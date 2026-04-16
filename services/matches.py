from __future__ import annotations

from datetime import datetime as dt_datetime

from services.utils import parse_datetime, safe_int


def get_filtered_matches(*, run_query, prefixes: str, match_scope_clauses, text_filter, filters: dict[str, object], q: str = "") -> list[dict[str, str]]:
    rows = run_query(
        prefixes
        + f"""
        SELECT ?matchUri ?date ?dateTime ?week ?homeLabel ?awayLabel ?hs ?as
        WHERE {{
            ?m a class:Match ;
                 prop:matchDate ?date ;
                 prop:hasTeamMatchParticipation ?homeP ;
                 prop:hasTeamMatchParticipation ?awayP .
            BIND(STR(?m) AS ?matchUri)
            OPTIONAL {{ ?m prop:matchDateTime ?dateTime . }}
            OPTIONAL {{ ?m prop:week ?week . }}
            OPTIONAL {{ ?m prop:homeScore ?hs . }}
            OPTIONAL {{ ?m prop:awayScore ?as . }}

            ?homeP prop:isHome true ; prop:correspondsToTeam ?home .
            ?awayP prop:isHome false ; prop:correspondsToTeam ?away .
            ?home rdfs:label ?homeLabel .
            ?away rdfs:label ?awayLabel .

            {match_scope_clauses(filters, match_var='?m', date_var='?date', week_var='?week')}
            {text_filter(q, '?homeLabel', '?awayLabel')}
        }}
        ORDER BY COALESCE(?dateTime, ?date) ?homeLabel ?awayLabel
        """
    )

    by_match_uri: dict[str, dict[str, str]] = {}
    for row in rows:
        match_uri = row.get("matchUri", "").strip()
        if not match_uri:
            continue
        if match_uri not in by_match_uri:
            by_match_uri[match_uri] = row
            continue

        current = by_match_uri[match_uri]
        if (not current.get("hs") and row.get("hs")) or (not current.get("as") and row.get("as")):
            by_match_uri[match_uri] = row

    rows = list(by_match_uri.values())

    def sort_key(row: dict[str, str]) -> tuple[dt_datetime, int, str, str]:
        match_dt = parse_datetime(row.get("dateTime", ""))
        if match_dt is None:
            match_dt = parse_datetime(row.get("date", "")) or dt_datetime.max

        return (
            match_dt,
            safe_int(row.get("week", "0")),
            row.get("homeLabel", ""),
            row.get("awayLabel", ""),
        )

    rows.sort(key=sort_key)
    return rows
