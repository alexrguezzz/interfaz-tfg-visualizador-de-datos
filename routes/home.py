from __future__ import annotations


def register_home_routes(app, deps) -> None:
    render_page = deps["render_page"]
    get_search = deps["get_search"]
    get_filters = deps["get_filters"]
    onboarding_complete = deps["onboarding_complete"]
    get_filtered_matches = deps["get_filtered_matches"]
    filters_are_default = deps["filters_are_default"]
    run_query = deps["run_query"]
    prefixes = deps["PREFIXES"]
    match_scope_clauses = deps["match_scope_clauses"]
    safe_int = deps["safe_int"]
    format_match_datetime = deps["format_match_datetime"]
    no_data_panel = deps["no_data_panel"]

    @app.route("/")
    def home():
        q = get_search()
        filters = get_filters()

        if not onboarding_complete():
            return render_page(
                "home",
                title="Inicio",
                subtitle="Seleccion inicial de ligas y temporadas",
                cards=[],
                panels=[{"title": "Seleccion inicial", "kind": "text", "text": "Configura primero las ligas y temporadas que quieres cargar."}],
            )

        try:
            cards: list[dict[str, str]] = []

            filtered_matches = get_filtered_matches(filters, q)

            cards.append({"label": "Partidos jugados", "value": str(len(filtered_matches))})

            team_names: set[str] = set()
            for row in filtered_matches:
                if row.get("homeLabel"):
                    team_names.add(row["homeLabel"])
                if row.get("awayLabel"):
                    team_names.add(row["awayLabel"])
            cards.append({"label": "Equipos", "value": str(len(team_names))})

            if filters_are_default(filters):
                total_players = run_query(prefixes + "SELECT (COUNT(?p) AS ?v) WHERE { ?p a class:Player . }")
            else:
                total_players = run_query(
                    prefixes
                    + f"""
                    SELECT (COUNT(DISTINCT ?p) AS ?v)
                    WHERE {{
                      ?p a class:Player .
                      FILTER EXISTS {{
                                            ?m a class:Match ; prop:hasEvent ?event ; prop:matchDate ?date .
                        OPTIONAL {{ ?m prop:week ?week . }}
                                            ?event prop:correspondsToPlayer ?p .
                        {match_scope_clauses(filters, match_var='?m', date_var='?date', week_var='?week')}
                      }}
                    }}
                    """
                )
            player_count = safe_int(total_players[0].get("v", "0") if total_players else "0")
            cards.append({"label": "Jugadores", "value": str(player_count) if player_count > 0 else "Informacion no disponible"})

            total_goals = 0
            for row in filtered_matches:
                total_goals += safe_int(row.get("hs", "0")) + safe_int(row.get("as", "0"))
            cards.append({"label": "Goles", "value": str(total_goals)})

            cards_data = run_query(
                prefixes
                + """
                SELECT (SUM(?c) AS ?v)
                WHERE {
                  { SELECT (SUM(?y) AS ?c) WHERE { ?x prop:yellowCards ?y . } }
                  UNION
                  { SELECT (SUM(?r) AS ?c) WHERE { ?x prop:redCards ?r . } }
                }
                """
            )
            cards_total = safe_int(cards_data[0].get("v", "0") if cards_data else "0")
            cards.append({"label": "Tarjetas", "value": str(cards_total) if cards_total > 0 else "Informacion no disponible"})

            if filtered_matches:
                last = filtered_matches[-1]
                last_date = format_match_datetime(last.get("dateTime", ""), last.get("date", ""))
                last_match = (
                    f"{last_date} | "
                    f"{last.get('homeLabel', '-')} {last.get('hs', '-')} - {last.get('as', '-')} {last.get('awayLabel', '-')}"
                )
            else:
                last_match = "Informacion no disponible"
            cards.append({"label": "Ultimo partido", "value": last_match})

            panels = [
                {
                    "title": "Resumen",
                    "kind": "text",
                    "text": "KPIs conectados directamente a GraphDB. Los datos no disponibles se muestran de forma explicita.",
                }
            ]

            return render_page("home", title="Inicio", subtitle="Resumen global", cards=cards, panels=panels)
        except Exception as exc:
            return render_page(
                "home",
                title="Inicio",
                subtitle="Resumen global",
                cards=[],
                panels=no_data_panel(),
                error=f"Error de conexion con GraphDB: {exc}",
            )

