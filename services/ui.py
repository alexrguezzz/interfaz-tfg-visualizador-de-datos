from __future__ import annotations

from datetime import date, timedelta
from html import escape
import json

from flask import render_template, request

from services.utils import safe_int


def current_page_url() -> str:
    full_path = request.full_path or request.path
    return full_path[:-1] if full_path.endswith("?") else full_path


def no_data_panel() -> list[dict[str, object]]:
    return [{"title": "Estado", "kind": "text", "text": "Informacion no disponible"}]


def compact_elo_points(points: list[tuple[date, float]], max_points: int = 60) -> list[tuple[date, float]]:
    if len(points) <= max_points:
        return points
    if max_points <= 1:
        return [points[-1]]

    step = (len(points) - 1) / float(max_points - 1)
    sampled: list[tuple[date, float]] = []
    used_indices: set[int] = set()

    for idx in range(max_points - 1):
        source_idx = int(round(idx * step))
        if source_idx in used_indices:
            continue
        sampled.append(points[source_idx])
        used_indices.add(source_idx)

    sampled.append(points[-1])
    return sampled


def build_elo_panel(*, run_query, prefixes: str, sparql_string, team_labels: list[str], years: int = 5) -> dict[str, object] | None:
    selected_teams = [label for label in dict.fromkeys(team_labels) if label][:6]
    if not selected_teams:
        return None

    date_limit = (date.today() - timedelta(days=365 * years)).isoformat()
    values_clause = " ".join(sparql_string(label) for label in selected_teams)

    elo_rows = run_query(
        prefixes
        + f"""
        SELECT ?teamLabel ?d ?elo
        WHERE {{
          VALUES ?teamLabel {{ {values_clause} }}
          ?team a class:Team ; rdfs:label ?teamLabel .
          ?record a class:EloRecord ;
                  prop:correspondsToTeam ?team ;
                  prop:elo ?elo .
          OPTIONAL {{ ?record prop:dateFrom ?dateFrom . }}
          OPTIONAL {{ ?record prop:dateTo ?dateTo . }}
          BIND(COALESCE(?dateFrom, ?dateTo) AS ?d)
          FILTER(BOUND(?d))
          FILTER(xsd:date(?d) >= "{date_limit}"^^xsd:date)
        }}
        ORDER BY ?teamLabel ?d
        """
    )

    grouped: dict[str, list[tuple[date, float]]] = {team: [] for team in selected_teams}
    for row in elo_rows:
        team = row.get("teamLabel", "")
        raw_date = row.get("d", "")
        if team not in grouped or len(raw_date) < 10:
            continue
        try:
            point_date = date.fromisoformat(raw_date[:10])
            elo_value = float(row.get("elo", "0"))
        except Exception:
            continue
        grouped[team].append((point_date, elo_value))

    series: dict[str, list[tuple[date, float]]] = {}
    for team, points in grouped.items():
        if len(points) >= 2:
            series[team] = compact_elo_points(points, max_points=60)

    if not series:
        return None

    all_dates = [point_date for points in series.values() for point_date, _ in points]
    all_elos = [value for points in series.values() for _, value in points]

    min_date = min(all_dates)
    max_date = max(all_dates)
    min_elo = min(all_elos)
    max_elo = max(all_elos)

    min_ord = min_date.toordinal()
    max_ord = max_date.toordinal()
    if min_ord == max_ord:
        max_ord = min_ord + 1

    if min_elo == max_elo:
        min_elo -= 20.0
        max_elo += 20.0
    else:
        pad = max((max_elo - min_elo) * 0.08, 15.0)
        min_elo -= pad
        max_elo += pad

    width, height = 980, 360
    margin_left, margin_right, margin_top, margin_bottom = 58, 18, 18, 48
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    def x_coord(point_date: date) -> float:
        ratio = (point_date.toordinal() - min_ord) / float(max_ord - min_ord)
        return margin_left + ratio * plot_w

    def y_coord(value: float) -> float:
        ratio = (value - min_elo) / float(max_elo - min_elo)
        return margin_top + (1.0 - ratio) * plot_h

    palette = ["#0a66c2", "#0d9488", "#ef4444", "#f59e0b", "#7c3aed", "#2563eb"]
    svg_parts: list[str] = [
        f'<svg class="elo-svg" viewBox="0 0 {width} {height}" role="img" aria-label="Evolucion Elo ultimos {years} anos">',
        f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="transparent"/>',
    ]

    for idx in range(6):
        y = margin_top + (plot_h * idx / 5.0)
        y_value = max_elo - ((max_elo - min_elo) * idx / 5.0)
        svg_parts.append(
            f'<line x1="{margin_left}" y1="{y:.2f}" x2="{width - margin_right}" y2="{y:.2f}" stroke="rgba(80,101,132,0.24)" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{margin_left - 8}" y="{y + 4:.2f}" text-anchor="end" font-size="11" fill="currentColor">{int(round(y_value))}</text>'
        )

    for idx in range(6):
        tick_ord = int(round(min_ord + ((max_ord - min_ord) * idx / 5.0)))
        tick_date = date.fromordinal(tick_ord)
        x = margin_left + (plot_w * idx / 5.0)
        svg_parts.append(
            f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{height - margin_bottom}" stroke="rgba(80,101,132,0.18)" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x:.2f}" y="{height - margin_bottom + 18}" text-anchor="middle" font-size="11" fill="currentColor">{tick_date.strftime("%Y")}</text>'
        )

    legend_items: list[str] = []
    for idx, team in enumerate(series.keys()):
        color = palette[idx % len(palette)]
        points_str = " ".join(f"{x_coord(d):.2f},{y_coord(v):.2f}" for d, v in series[team])
        last_date, last_elo = series[team][-1]
        svg_parts.append(
            f'<polyline points="{points_str}" fill="none" stroke="{color}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        svg_parts.append(
            f'<circle cx="{x_coord(last_date):.2f}" cy="{y_coord(last_elo):.2f}" r="3.2" fill="{color}"/>'
        )
        legend_items.append(
            f'<span class="elo-item"><span class="elo-swatch" style="background:{color};"></span>{escape(team)}</span>'
        )

    svg_parts.append("</svg>")
    chart_html = (
        '<div class="elo-chart">'
        + "".join(svg_parts)
        + f'<div class="elo-legend">{"".join(legend_items)}</div>'
        + "</div>"
    )

    return {
        "title": f"Tendencia Elo (ultimos {years} anos)",
        "kind": "html",
        "html": chart_html,
    }


def build_match_pitch_panel(events: list[dict[str, object]]) -> dict[str, object]:
    events_json = json.dumps(events, ensure_ascii=True).replace("</", "<\\/")
    pitch_html = f"""
    <div class="pitch-widget" data-pitch-widget>
        <div class="pitch-toolbar">
            <label class="pitch-field">
                <span>Equipo</span>
                <select data-pitch-team>
                    <option value="all">Todos</option>
                </select>
            </label>
            <label class="pitch-field">
                <span>Jugador</span>
                <select data-pitch-player>
                    <option value="all">Todos</option>
                </select>
            </label>
            <label class="pitch-field">
                <span>Tipo</span>
                <select data-pitch-kind>
                    <option value="all">Todos</option>
                    <option value="pass">Pase</option>
                    <option value="shot">Tiro</option>
                </select>
            </label>
        </div>
        <div class="pitch-wrap">
            <svg class="pitch-svg" viewBox="0 0 1000 620" role="img" aria-label="Eventos del partido"></svg>
        </div>
        <p class="pitch-summary" data-pitch-summary></p>
        <script type="application/json" data-pitch-data>{events_json}</script>
    </div>
    """
    return {
        "title": "Campo de futbol - eventos",
        "kind": "html",
        "html": pitch_html,
    }


def render_page_factory(
    *,
    brand_logo_path: str,
    build_nav,
    get_search,
    get_filters,
    onboarding_choices,
    available_weeks,
):
    def render_page(
        current: str,
        *,
        title: str,
        current_view: str | None = None,
        subtitle: str = "",
        cards: list[dict[str, str]] | None = None,
        headers: list[str] | None = None,
        rows: list[list[str]] | None = None,
        panels: list[dict[str, object]] | None = None,
        compare_form: bool = False,
        team_options: list[str] | None = None,
        team_a: str = "",
        team_b: str = "",
        compare_cards: list[dict[str, str]] | None = None,
        error: str = "",
    ):
        q = get_search()
        filters = get_filters()
        onboarding = onboarding_choices()

        return render_template(
            "page.html",
            page_title=title,
            app_name="DataGol",
            brand_logo_path=brand_logo_path,
            current_section=current,
            current_view=current_view or current,
            title=title,
            subtitle=subtitle,
            q=q,
            nav_items=build_nav(current, filters, q),
            filter_state=filters,
            onboarding=onboarding,
            onboarding_required=not onboarding["complete"],
            current_page_url=current_page_url(),
            competition_options=["all", *onboarding["competition_options"]],
            season_options=["all", *onboarding["season_options"]],
            jornadas_options=available_weeks(),
            cards=cards or [],
            headers=headers or [],
            rows=rows or [],
            panels=panels or [],
            compare_form=compare_form,
            team_options=team_options or [],
            team_a=team_a,
            team_b=team_b,
            compare_cards=compare_cards or [],
            error=error,
        )

    return render_page
