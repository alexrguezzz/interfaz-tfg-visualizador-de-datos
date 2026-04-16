from __future__ import annotations

import os

SECRET_KEY = os.getenv("SECRET_KEY", "datagol-development-secret")
GRAPHDB_ENDPOINT = os.getenv(
    "GRAPHDB_ENDPOINT",
    "http://localhost:7200/repositories/TFG_SoccerData",
)
BRAND_LOGO_PATH = "images/brand/datagol-logo.png"

PREFIXES = """
PREFIX class: <http://example.org/TFG_SoccerData/class/>
PREFIX prop: <http://example.org/TFG_SoccerData/property/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

SECTIONS = [
    {"key": "home", "label": "Inicio", "path": "home"},
    {"key": "competition", "label": "Competicion", "path": "competition"},
    {"key": "matches", "label": "Partidos", "path": "matches"},
    {"key": "teams", "label": "Equipos", "path": "teams"},
    {"key": "players", "label": "Jugadores", "path": "players"},
    {"key": "compare", "label": "Comparador", "path": "compare"},
]

ONBOARDING_LEAGUES = [
    {"label": "La Liga", "slug": "la-liga", "logo": "images/leagues/la-liga.svg", "fallback": "LL"},
    {"label": "Premier League", "slug": "premier-league", "logo": "images/leagues/premier-league.svg", "fallback": "PL"},
    {"label": "Bundesliga", "slug": "bundesliga", "logo": "images/leagues/bundesliga.svg", "fallback": "B"},
    {"label": "Ligue 1", "slug": "ligue-1", "logo": "images/leagues/ligue-1.svg", "fallback": "L1"},
    {"label": "Serie A", "slug": "serie-a", "logo": "images/leagues/serie-a.svg", "fallback": "SA"},
]

ONBOARDING_SEASONS = [
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
]

ONBOARDING_LEAGUE_LABELS = [item["label"] for item in ONBOARDING_LEAGUES]
