from __future__ import annotations

from threading import Timer
import secrets
import webbrowser

from flask import Flask

from config import (
    BRAND_LOGO_PATH,
    GRAPHDB_ENDPOINT,
    ONBOARDING_LEAGUE_LABELS,
    ONBOARDING_SEASONS,
    PREFIXES,
    SECRET_KEY,
)
from routes.compare import register_compare_routes
from routes.competition import register_competition_routes
from routes.home import register_home_routes
from routes.matches import register_matches_routes
from routes.players import register_players_routes
from routes.selection import register_selection_routes
from routes.teams import register_teams_routes
from services.filters import (
    build_nav,
    build_url,
    filter_clauses,
    filters_are_default,
    get_filters,
    get_search,
    match_scope_clauses as build_match_scope_clauses,
    text_filter,
)
from services.matches import get_filtered_matches as fetch_filtered_matches
from services.onboarding import (
    ensure_onboarding_boot_token as ensure_onboarding,
    onboarding_choices as build_onboarding_choices,
    onboarding_complete as is_onboarding_complete,
    onboarding_label_clauses as build_onboarding_label_clauses,
    onboarding_match_clauses as build_onboarding_match_clauses,
)
from services.query import run_query as execute_query
from services.ui import (
    build_elo_panel as create_elo_panel,
    build_match_pitch_panel,
    no_data_panel,
    render_page_factory,
)
from services.utils import format_match_datetime, safe_bool, safe_int, sparql_iri, sparql_string

app = Flask(__name__)
app.secret_key = SECRET_KEY
APP_BOOT_TOKEN = secrets.token_hex(16)


def run_query(query: str) -> list[dict[str, str]]:
    return execute_query(GRAPHDB_ENDPOINT, query)


def ensure_onboarding_boot_token() -> None:
    ensure_onboarding(APP_BOOT_TOKEN)


def onboarding_complete() -> bool:
    return is_onboarding_complete(APP_BOOT_TOKEN)


def onboarding_choices() -> dict[str, object]:
    return build_onboarding_choices(APP_BOOT_TOKEN)


def onboarding_label_clauses(*, competition_label: str | None = None, season_label: str | None = None) -> str:
    return build_onboarding_label_clauses(
        APP_BOOT_TOKEN,
        competition_label=competition_label,
        season_label=season_label,
    )


def onboarding_match_clauses(match_var: str = "?m", *, date_var: str = "?date", week_var: str = "?week") -> str:
    return build_onboarding_match_clauses(
        APP_BOOT_TOKEN,
        match_var=match_var,
        date_var=date_var,
        week_var=week_var,
    )


def match_scope_clauses(
    filters: dict[str, object],
    *,
    match_var: str = "?m",
    date_var: str = "?date",
    week_var: str = "?week",
) -> str:
    return build_match_scope_clauses(
        filters,
        onboarding_match_clauses=onboarding_match_clauses,
        match_var=match_var,
        date_var=date_var,
        week_var=week_var,
    )


def available_weeks() -> list[str]:
    rows = run_query(
        PREFIXES
        + f"""
        SELECT DISTINCT ?week
        WHERE {{
          ?match a class:Match ; prop:week ?week .
          {onboarding_match_clauses(match_var='?match')}
        }}
        ORDER BY xsd:integer(?week)
        """
    )
    weeks: list[int] = []
    for row in rows:
        value = safe_int(row.get("week", "0"))
        if value > 0:
            weeks.append(value)
    return [str(week) for week in sorted(set(weeks))]


def get_filtered_matches(filters: dict[str, object], q: str = "") -> list[dict[str, str]]:
    return fetch_filtered_matches(
        run_query=run_query,
        prefixes=PREFIXES,
        match_scope_clauses=match_scope_clauses,
        text_filter=text_filter,
        filters=filters,
        q=q,
    )


def build_elo_panel(team_labels: list[str], years: int = 5) -> dict[str, object] | None:
    return create_elo_panel(
        run_query=run_query,
        prefixes=PREFIXES,
        sparql_string=sparql_string,
        team_labels=team_labels,
        years=years,
    )


render_page = render_page_factory(
    brand_logo_path=BRAND_LOGO_PATH,
    build_nav=build_nav,
    get_search=get_search,
    get_filters=get_filters,
    onboarding_choices=onboarding_choices,
    available_weeks=available_weeks,
)


register_selection_routes(
    app,
    {
        "ensure_onboarding_boot_token": ensure_onboarding_boot_token,
        "ONBOARDING_LEAGUE_LABELS": ONBOARDING_LEAGUE_LABELS,
        "ONBOARDING_SEASONS": ONBOARDING_SEASONS,
    },
)

shared_route_deps = {
    "render_page": render_page,
    "get_search": get_search,
    "get_filters": get_filters,
    "onboarding_complete": onboarding_complete,
    "run_query": run_query,
    "PREFIXES": PREFIXES,
    "no_data_panel": no_data_panel,
}

register_home_routes(
    app,
    {
        **shared_route_deps,
        "get_filtered_matches": get_filtered_matches,
        "filters_are_default": filters_are_default,
        "match_scope_clauses": match_scope_clauses,
        "safe_int": safe_int,
        "format_match_datetime": format_match_datetime,
    },
)

register_competition_routes(
    app,
    {
        **shared_route_deps,
        "onboarding_label_clauses": onboarding_label_clauses,
        "filter_clauses": filter_clauses,
        "text_filter": text_filter,
    },
)

register_matches_routes(
    app,
    {
        **shared_route_deps,
        "get_filtered_matches": get_filtered_matches,
        "format_match_datetime": format_match_datetime,
        "build_url": build_url,
        "sparql_iri": sparql_iri,
        "safe_bool": safe_bool,
        "build_match_pitch_panel": build_match_pitch_panel,
    },
)

register_teams_routes(
    app,
    {
        **shared_route_deps,
        "match_scope_clauses": match_scope_clauses,
        "text_filter": text_filter,
        "build_elo_panel": build_elo_panel,
    },
)

register_players_routes(
    app,
    {
        **shared_route_deps,
        "filters_are_default": filters_are_default,
        "match_scope_clauses": match_scope_clauses,
        "text_filter": text_filter,
    },
)

register_compare_routes(
    app,
    {
        **shared_route_deps,
        "filters_are_default": filters_are_default,
        "match_scope_clauses": match_scope_clauses,
        "onboarding_match_clauses": onboarding_match_clauses,
        "sparql_string": sparql_string,
        "filter_clauses": filter_clauses,
    },
)


if __name__ == "__main__":
    Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
