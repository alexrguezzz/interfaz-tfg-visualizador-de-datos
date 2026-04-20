from __future__ import annotations

from flask import request


def register_matches_routes(app, deps) -> None:
    render_page = deps["render_page"]
    get_search = deps["get_search"]
    get_filters = deps["get_filters"]
    onboarding_complete = deps["onboarding_complete"]
    get_filtered_matches = deps["get_filtered_matches"]
    format_match_datetime = deps["format_match_datetime"]
    build_url = deps["build_url"]
    no_data_panel = deps["no_data_panel"]
    run_query = deps["run_query"]
    prefixes = deps["PREFIXES"]
    sparql_iri = deps["sparql_iri"]
    safe_bool = deps["safe_bool"]
    build_match_pitch_panel = deps["build_match_pitch_panel"]

    @app.route("/matches")
    def matches():
        q = get_search()
        filters = get_filters()
        if not onboarding_complete():
            return render_page("matches", title="Partidos", subtitle="Seleccion inicial de ligas y temporadas", panels=no_data_panel())
        try:
            data = get_filtered_matches(filters, q)

            rows = [
                [
                    format_match_datetime(r.get("dateTime", ""), r.get("date", "")),
                    r.get("week", "-"),
                    r.get("homeLabel", "-"),
                    r.get("awayLabel", "-"),
                    f"{r.get('hs', '-')} - {r.get('as', '-')}",
                    {
                        "text": "Ver partido",
                        "href": build_url("match_detail", filters, q, {"match_uri": r.get("matchUri", "")}),
                    },
                ]
                for r in data
            ]

            return render_page(
                "matches",
                title="Partidos",
                subtitle="Partidos filtrados",
                headers=["Fecha y hora", "Jornada", "Local", "Visitante", "Marcador", "Detalle"],
                rows=rows,
                panels=no_data_panel() if not rows else [],
            )
        except Exception as exc:
            return render_page("matches", title="Partidos", subtitle="Partidos filtrados", error=f"Error: {exc}", panels=no_data_panel())

    @app.route("/match")
    def match_detail():
        match_uri = request.args.get("match_uri", "").strip()

        if not onboarding_complete():
            return render_page(
                "matches",
                title="Detalle de partido",
                current_view="match_detail",
                subtitle="Seleccion inicial de ligas y temporadas",
                panels=no_data_panel(),
            )

        if not match_uri:
            return render_page(
                "matches",
                title="Detalle de partido",
                current_view="match_detail",
                subtitle="Vista de detalle",
                panels=no_data_panel(),
                error="No se ha indicado el partido.",
            )

        try:
            details = run_query(
                prefixes
                + f"""
                            SELECT ?date ?dateTime ?week ?homeLabel ?awayLabel ?hs ?as ?venue ?attendance
                WHERE {{
                  BIND({sparql_iri(match_uri)} AS ?m)
                  ?m a class:Match ;
                     prop:matchDate ?date ;
                     prop:hasTeamMatchParticipation ?homeP ;
                     prop:hasTeamMatchParticipation ?awayP .
                                OPTIONAL {{ ?m prop:matchDateTime ?dateTime . }}
                  OPTIONAL {{ ?m prop:week ?week . }}
                  OPTIONAL {{ ?m prop:homeScore ?hs . }}
                  OPTIONAL {{ ?m prop:awayScore ?as . }}
                  OPTIONAL {{ ?m prop:venue ?venue . }}
                  OPTIONAL {{ ?m prop:attendance ?attendance . }}

                  ?homeP prop:isHome true ; prop:correspondsToTeam ?home .
                  ?awayP prop:isHome false ; prop:correspondsToTeam ?away .
                  ?home rdfs:label ?homeLabel .
                  ?away rdfs:label ?awayLabel .
                }}
                LIMIT 1
                """
            )

            if not details:
                return render_page(
                    "matches",
                    title="Detalle de partido",
                    current_view="match_detail",
                    subtitle="Vista de detalle",
                    panels=no_data_panel(),
                    error="No se han encontrado datos para el partido seleccionado.",
                )

            row = details[0]
            row_date = format_match_datetime(row.get("dateTime", ""), row.get("date", ""))
            cards = [
                {"label": "Jornada", "value": row.get("week", "-")},
                {"label": "Fecha", "value": row_date},
                {"label": "Local", "value": row.get("homeLabel", "-")},
                {"label": "Visitante", "value": row.get("awayLabel", "-")},
                {"label": "Marcador", "value": f"{row.get('hs', '-')} - {row.get('as', '-')}"},
                {"label": "Asistencia", "value": row.get("attendance", "Informacion no disponible")},
            ]

            events_rows = run_query(
                prefixes
                + f"""
                SELECT ?event ?teamLabel ?playerLabel ?type ?outcomeType ?isShot ?x ?y ?endX ?endY
                WHERE {{
                  BIND({sparql_iri(match_uri)} AS ?m)
                  ?m a class:Match ; prop:hasEvent ?event .
                  ?event prop:correspondsToTeam ?team ;
                         prop:xCoord ?x ;
                         prop:yCoord ?y .
                  ?team rdfs:label ?teamLabel .

                  OPTIONAL {{ ?event prop:correspondsToPlayer ?player . ?player rdfs:label ?playerLabel . }}
                  OPTIONAL {{ ?event prop:eventType ?type . }}
                  OPTIONAL {{ ?event prop:outcomeType ?outcomeType . }}
                  OPTIONAL {{ ?event prop:isShot ?isShot . }}
                  OPTIONAL {{ ?event prop:endX ?endX . }}
                  OPTIONAL {{ ?event prop:endY ?endY . }}
                }}
                ORDER BY ?event
                """
            )

            events_payload: list[dict[str, object]] = []
            for item in events_rows:
                try:
                    x_val = float(item.get("x", ""))
                    y_val = float(item.get("y", ""))
                except Exception:
                    continue

                events_payload.append(
                    {
                        "team": item.get("teamLabel", ""),
                        "player": item.get("playerLabel", ""),
                        "type": item.get("type", ""),
                        "outcome_type": item.get("outcomeType", ""),
                        "is_shot": safe_bool(item.get("isShot", "")),
                        "x": x_val,
                        "y": y_val,
                        "end_x": float(item["endX"]) if item.get("endX", "") not in {"", None} else None,
                        "end_y": float(item["endY"]) if item.get("endY", "") not in {"", None} else None,
                    }
                )

            panels = [build_match_pitch_panel(events_payload)]

            return render_page(
                "matches",
                title="Detalle de partido",
                current_view="match_detail",
                subtitle=row.get("venue", "Partido seleccionado"),
                cards=cards,
                panels=panels,
            )
        except Exception as exc:
            return render_page(
                "matches",
                title="Detalle de partido",
                current_view="match_detail",
                subtitle="Vista de detalle",
                panels=no_data_panel(),
                error=f"Error al cargar detalle del partido: {exc}",
            )
