from __future__ import annotations

from flask import session

from config import ONBOARDING_LEAGUE_LABELS, ONBOARDING_LEAGUES, ONBOARDING_SEASONS
from services.utils import sparql_string


def normalize_selection_value(value: str) -> str:
    text = str(value or "").strip().replace("_", " ").replace("-", " ").lower()
    return " ".join(text.split())


def ensure_onboarding_boot_token(app_boot_token: str) -> None:
    current_token = str(session.get("onboarding_boot_token", ""))
    if current_token == app_boot_token:
        return

    session["onboarding_boot_token"] = app_boot_token
    session.pop("onboarding_competitions", None)
    session.pop("onboarding_seasons", None)


def get_onboarding_state(app_boot_token: str) -> dict[str, list[str]]:
    ensure_onboarding_boot_token(app_boot_token)
    competitions = [value for value in session.get("onboarding_competitions", []) if value in ONBOARDING_LEAGUE_LABELS]
    seasons = [value for value in session.get("onboarding_seasons", []) if value in ONBOARDING_SEASONS]
    return {"competitions": competitions, "seasons": seasons}


def onboarding_complete(app_boot_token: str) -> bool:
    state = get_onboarding_state(app_boot_token)
    return bool(state["competitions"]) and bool(state["seasons"])


def selection_filter_clause(field_expr: str, selected_values: list[str]) -> str:
    if not selected_values:
        return ""

    checks = [
        f'CONTAINS(LCASE(REPLACE(REPLACE(STR({field_expr}), "_", " "), "-", " ")), {sparql_string(normalize_selection_value(value))})'
        for value in selected_values
    ]
    return "FILTER(" + " || ".join(checks) + ")"


def normalized_label_match_clause(field_expr: str, value: str) -> str:
    normalized_value = normalize_selection_value(value)
    if not normalized_value:
        return ""
    return (
        'CONTAINS('
        f'LCASE(REPLACE(REPLACE(STR({field_expr}), "_", " "), "-", " ")), '
        f'{sparql_string(normalized_value)}'
        ')'
    )


def onboarding_label_clauses(
    app_boot_token: str,
    *,
    competition_label: str | None = None,
    season_label: str | None = None,
) -> str:
    state = get_onboarding_state(app_boot_token)
    clauses: list[str] = []

    if competition_label and state["competitions"]:
        clauses.append(selection_filter_clause(competition_label, state["competitions"]))

    if season_label and state["seasons"]:
        clauses.append(selection_filter_clause(season_label, state["seasons"]))

    return "\n          ".join(clauses)


def onboarding_match_clauses(
    app_boot_token: str,
    match_var: str = "?m",
    *,
    date_var: str = "?date",
    week_var: str = "?week",
) -> str:
    del date_var, week_var
    state = get_onboarding_state(app_boot_token)
    clauses: list[str] = []

    if state["competitions"]:
        competition_checks = [
            f'CONTAINS(LCASE(REPLACE(REPLACE(STR(?_baseCompetitionLabel), "_", " "), "-", " ")), {sparql_string(normalize_selection_value(value))})'
            for value in state["competitions"]
        ]
        clauses.append(
            f"""
            FILTER(EXISTS {{
                {match_var} prop:belongsToCompetition ?_baseCompetition .
                ?_baseCompetition rdfs:label ?_baseCompetitionLabel .
                FILTER({" || ".join(competition_checks)})
            }})
            """
        )

    if state["seasons"]:
        season_checks = [
            f'CONTAINS(LCASE(REPLACE(REPLACE(STR(?_baseSeasonLabel), "_", " "), "-", " ")), {sparql_string(normalize_selection_value(value))})'
            for value in state["seasons"]
        ]
        clauses.append(
            f"""
            FILTER(EXISTS {{
                {match_var} prop:belongsToSeason ?_baseSeason .
                ?_baseSeason rdfs:label ?_baseSeasonLabel .
                FILTER({" || ".join(season_checks)})
            }})
            """
        )

    return "\n              ".join(clauses)


def onboarding_choices(app_boot_token: str) -> dict[str, list[dict[str, str]] | list[str] | bool]:
    state = get_onboarding_state(app_boot_token)
    competition_choices = state["competitions"] or ONBOARDING_LEAGUE_LABELS
    season_choices = state["seasons"] or ONBOARDING_SEASONS
    return {
        "leagues": ONBOARDING_LEAGUES,
        "seasons": ONBOARDING_SEASONS,
        "competition_options": competition_choices,
        "season_options": season_choices,
        "selected_competitions": state["competitions"],
        "selected_seasons": state["seasons"],
        "complete": onboarding_complete(app_boot_token),
    }
