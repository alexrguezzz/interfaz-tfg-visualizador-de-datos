from __future__ import annotations


def register_competition_routes(app, deps) -> None:
    render_page = deps["render_page"]
    get_search = deps["get_search"]
    get_filters = deps["get_filters"]
    onboarding_complete = deps["onboarding_complete"]
    run_query = deps["run_query"]
    prefixes = deps["PREFIXES"]
    onboarding_label_clauses = deps["onboarding_label_clauses"]
    filter_clauses = deps["filter_clauses"]
    text_filter = deps["text_filter"]
    no_data_panel = deps["no_data_panel"]

    @app.route("/competition")
    def competition():
        q = get_search()
        filters = get_filters()
        if not onboarding_complete():
            return render_page("competition", title="Competicion", subtitle="Seleccion inicial de ligas y temporadas", panels=no_data_panel())
        try:
            data = run_query(
                prefixes
                + f"""
                SELECT ?competitionLabel ?seasonLabel ?position ?teamLabel ?pts ?mp ?w ?d ?l ?gf ?ga ?gd
                WHERE {{
                  ?tcs a class:TeamCompetitionSeason ;
                       prop:belongsToCompetition ?competition ;
                       prop:belongsToSeason ?season ;
                       prop:correspondsToTeam ?team .
                  ?competition rdfs:label ?competitionLabel .
                  ?season rdfs:label ?seasonLabel .
                  ?team rdfs:label ?teamLabel .

                  OPTIONAL {{ ?tcs prop:position ?position . }}
                  OPTIONAL {{ ?tcs prop:points ?pts . }}
                  OPTIONAL {{ ?tcs prop:matchesPlayed ?mp . }}
                  OPTIONAL {{ ?tcs prop:wins ?w . }}
                  OPTIONAL {{ ?tcs prop:draws ?d . }}
                  OPTIONAL {{ ?tcs prop:losses ?l . }}
                  OPTIONAL {{ ?tcs prop:goalsFor ?gf . }}
                  OPTIONAL {{ ?tcs prop:goalsAgainst ?ga . }}
                  OPTIONAL {{ ?tcs prop:goalDifference ?gd . }}

                  BIND(COALESCE(xsd:integer(?position), 999) AS ?positionSort)
                  BIND(COALESCE(xsd:integer(?pts), 0) AS ?pointsSort)

                                {onboarding_label_clauses(competition_label='?competitionLabel', season_label='?seasonLabel')}
                  {filter_clauses(filters, competition_label='?competitionLabel', season_label='?seasonLabel')}
                  {text_filter(q, '?competitionLabel', '?seasonLabel', '?teamLabel')}
                }}
                ORDER BY ?competitionLabel DESC(?seasonLabel) ?positionSort DESC(?pointsSort) ?teamLabel
                LIMIT 600
                """
            )
            rows = [
                [
                    r.get("competitionLabel", "-"),
                    r.get("seasonLabel", "-"),
                    r.get("position", "-"),
                    r.get("teamLabel", "-"),
                    r.get("pts", "0"),
                    r.get("mp", "0"),
                    r.get("w", "0"),
                    r.get("d", "0"),
                    r.get("l", "0"),
                    r.get("gf", "0"),
                    r.get("ga", "0"),
                    r.get("gd", "0"),
                ]
                for r in data
            ]
            panels = no_data_panel() if not rows else []
            return render_page(
                "competition",
                title="Competicion",
                subtitle="Clasificacion por temporada completa (sin filtro de jornadas ni fechas)",
                headers=["Competicion", "Temporada", "Pos", "Equipo", "Pts", "PJ", "G", "E", "P", "GF", "GA", "DG"],
                rows=rows,
                panels=panels,
            )
        except Exception as exc:
            return render_page("competition", title="Competicion", subtitle="Competiciones y temporadas", error=f"Error: {exc}", panels=no_data_panel())

