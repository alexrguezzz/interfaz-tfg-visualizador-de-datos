from __future__ import annotations

from flask import request


def register_compare_routes(app, deps) -> None:
    render_page = deps["render_page"]
    get_search = deps["get_search"]
    get_filters = deps["get_filters"]
    onboarding_complete = deps["onboarding_complete"]
    filters_are_default = deps["filters_are_default"]
    match_scope_clauses = deps["match_scope_clauses"]
    onboarding_match_clauses = deps["onboarding_match_clauses"]
    run_query = deps["run_query"]
    prefixes = deps["PREFIXES"]
    sparql_string = deps["sparql_string"]
    filter_clauses = deps["filter_clauses"]
    no_data_panel = deps["no_data_panel"]

    def get_team_options(filters: dict[str, object]) -> list[str]:
        team_scope = ""
        if not filters_are_default(filters):
            team_scope = (
                "FILTER EXISTS { "
                "?m a class:Match ; prop:matchDate ?date ; prop:hasTeamMatchParticipation ?part . "
                "OPTIONAL { ?m prop:week ?week . } "
                "?part prop:correspondsToTeam ?team . "
                + match_scope_clauses(filters, match_var="?m", date_var="?date", week_var="?week")
                + " }"
            )

        if onboarding_complete() and not team_scope:
            team_scope = onboarding_match_clauses(match_var="?m")

        rows = run_query(
            prefixes
            + f"""
            SELECT ?label
            WHERE {{
              ?team a class:Team ; rdfs:label ?label .
              {team_scope}
            }}
            ORDER BY ?label
            LIMIT 300
            """
        )
        return [r["label"] for r in rows if r.get("label")]

    @app.route("/compare")
    def compare():
        q = get_search()
        filters = get_filters()
        team_a = request.args.get("team_a", "").strip()
        team_b = request.args.get("team_b", "").strip()

        if not onboarding_complete():
            return render_page(
                "compare",
                title="Comparador",
                subtitle="Seleccion inicial de ligas y temporadas",
                compare_form=True,
                compare_cards=[],
                team_options=[],
                team_a=team_a,
                team_b=team_b,
                panels=no_data_panel(),
            )

        try:
            team_options = get_team_options(filters)
            compare_cards: list[dict[str, str]] = []

            for team_label in [team_a, team_b]:
                if not team_label:
                    continue
                summary = run_query(
                    prefixes
                    + f"""
                    SELECT (COUNT(?p) AS ?matches) (SUM(?pts) AS ?points)
                    WHERE {{
                      ?team a class:Team ; rdfs:label {sparql_string(team_label)} .
                                        OPTIONAL {{
                                            ?m a class:Match ; prop:matchDate ?date ; prop:hasTeamMatchParticipation ?p .
                                            OPTIONAL {{ ?m prop:week ?week . }}
                                            ?p a class:TeamMatchParticipation ; prop:correspondsToTeam ?team .
                                            {match_scope_clauses(filters, match_var='?m', date_var='?date', week_var='?week')}
                                        }}
                                        OPTIONAL {{
                                            ?tcs a class:TeamCompetitionSeason ;
                                                     prop:correspondsToTeam ?team ;
                                                     prop:points ?pts ;
                                                     prop:belongsToCompetition ?cmp ;
                                                     prop:belongsToSeason ?ssn .
                                            ?cmp rdfs:label ?competitionLabel .
                                            ?ssn rdfs:label ?seasonLabel .
                                            {filter_clauses(filters, competition_label='?competitionLabel', season_label='?seasonLabel')}
                                        }}
                    }}
                    """
                )
                row = summary[0] if summary else {}
                compare_cards.append(
                    {
                        "label": team_label,
                        "value": f"{row.get('matches', '0')} partidos",
                        "extra": f"{row.get('points', '0')} puntos acumulados",
                    }
                )

            return render_page(
                "compare",
                title="Comparador",
                subtitle="Comparacion basica entre equipos",
                compare_form=True,
                team_options=team_options,
                team_a=team_a,
                team_b=team_b,
                compare_cards=compare_cards,
                panels=no_data_panel() if not compare_cards else [],
            )
        except Exception as exc:
            return render_page(
                "compare",
                title="Comparador",
                subtitle="Comparacion basica entre equipos",
                compare_form=True,
                team_options=[],
                team_a=team_a,
                team_b=team_b,
                compare_cards=[],
                panels=no_data_panel(),
                error=f"Error: {exc}",
            )

