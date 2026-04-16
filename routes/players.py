from __future__ import annotations


def register_players_routes(app, deps) -> None:
    render_page = deps["render_page"]
    get_search = deps["get_search"]
    get_filters = deps["get_filters"]
    onboarding_complete = deps["onboarding_complete"]
    filters_are_default = deps["filters_are_default"]
    match_scope_clauses = deps["match_scope_clauses"]
    run_query = deps["run_query"]
    prefixes = deps["PREFIXES"]
    text_filter = deps["text_filter"]
    no_data_panel = deps["no_data_panel"]

    @app.route("/players")
    def players():
        q = get_search()
        filters = get_filters()
        if not onboarding_complete():
            return render_page("players", title="Jugadores", subtitle="Seleccion inicial de ligas y temporadas", panels=no_data_panel())
        player_scope = ""
        if not filters_are_default(filters):
            player_scope = (
                "FILTER EXISTS { "
                "?m a class:Match ; prop:hasEvent ?event ; prop:matchDate ?date . "
                "OPTIONAL { ?m prop:week ?week . } "
                "?event prop:correspondsToPlayer ?p . "
                + match_scope_clauses(filters, match_var="?m", date_var="?date", week_var="?week")
                + " }"
            )

        try:
            data = run_query(
                prefixes
                + f"""
                SELECT ?label
                WHERE {{
                  ?p a class:Player ; rdfs:label ?label .
                  {player_scope}
                  {text_filter(q, '?label')}
                }}
                ORDER BY ?label
                """
            )
            if not data:
                return render_page(
                    "players",
                    title="Jugadores",
                    subtitle="Estado de datos",
                    panels=no_data_panel(),
                )

            rows = [[r["label"]] for r in data]
            return render_page(
                "players",
                title="Jugadores",
                subtitle="Listado de jugadores",
                headers=["Jugador"],
                rows=rows,
            )
        except Exception:
            return render_page(
                "players",
                title="Jugadores",
                subtitle="Estado de datos",
                panels=no_data_panel(),
            )

