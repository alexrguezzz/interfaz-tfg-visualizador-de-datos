from __future__ import annotations


def register_teams_routes(app, deps) -> None:
    render_page = deps["render_page"]
    get_search = deps["get_search"]
    get_filters = deps["get_filters"]
    onboarding_complete = deps["onboarding_complete"]
    run_query = deps["run_query"]
    prefixes = deps["PREFIXES"]
    match_scope_clauses = deps["match_scope_clauses"]
    text_filter = deps["text_filter"]
    build_elo_panel = deps["build_elo_panel"]
    no_data_panel = deps["no_data_panel"]

    @app.route("/teams")
    def teams():
        q = get_search()
        filters = get_filters()
        if not onboarding_complete():
            return render_page("teams", title="Equipos", subtitle="Seleccion inicial de ligas y temporadas", panels=no_data_panel())
        try:
            data = run_query(
                prefixes
                + f"""
                SELECT ?teamLabel
                       (COUNT(DISTINCT ?m) AS ?matches)
                         (SUM(?gfValue) AS ?gf)
                         (SUM(?gaValue) AS ?ga)
                WHERE {{
                  ?team a class:Team ; rdfs:label ?teamLabel .

                  OPTIONAL {{
                         ?m a class:Match ;
                             prop:matchDate ?date ;
                             prop:hasTeamMatchParticipation ?p .
                         OPTIONAL {{ ?m prop:week ?week . }}
                         OPTIONAL {{ ?m prop:homeScore ?homeScoreRaw . }}
                         OPTIONAL {{ ?m prop:awayScore ?awayScoreRaw . }}

                         ?p a class:TeamMatchParticipation ;
                            prop:correspondsToTeam ?team ;
                            prop:isHome ?isHome .

                         BIND(COALESCE(xsd:integer(?homeScoreRaw), 0) AS ?homeScore)
                         BIND(COALESCE(xsd:integer(?awayScoreRaw), 0) AS ?awayScore)
                         BIND(IF(?isHome = true, ?homeScore, ?awayScore) AS ?gfValue)
                         BIND(IF(?isHome = true, ?awayScore, ?homeScore) AS ?gaValue)

                         {match_scope_clauses(filters, match_var='?m', date_var='?date', week_var='?week')}
                  }}

                  {text_filter(q, '?teamLabel')}
                }}
                GROUP BY ?teamLabel
                HAVING(COUNT(DISTINCT ?m) > 0)
                ORDER BY DESC(?matches) DESC(?gf) ?teamLabel
                LIMIT 300
                """
            )

            rows = [[r["teamLabel"], r.get("matches", "0"), r.get("gf", "0"), r.get("ga", "0")] for r in data]
            elo_panel = build_elo_panel([r["teamLabel"] for r in data[:6]], years=5)
            panels = [elo_panel] if elo_panel else [{"title": "Tendencia Elo", "kind": "text", "text": "Informacion no disponible para los ultimos 5 aÃ±os."}]

            return render_page(
                "teams",
                title="Equipos",
                subtitle="Resumen por equipo y tendencia Elo (Ãºltimos 5 aÃ±os)",
                headers=["Equipo", "Partidos", "GF", "GA"],
                rows=rows,
                panels=no_data_panel() if not rows else panels,
            )
        except Exception as exc:
            return render_page("teams", title="Equipos", subtitle="Resumen por equipo", error=f"Error: {exc}", panels=no_data_panel())

