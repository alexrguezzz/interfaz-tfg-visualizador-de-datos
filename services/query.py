from __future__ import annotations

import requests


def run_query(endpoint: str, query: str) -> list[dict[str, str]]:
    response = requests.post(
        endpoint,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()

    rows: list[dict[str, str]] = []
    for binding in payload.get("results", {}).get("bindings", []):
        row: dict[str, str] = {}
        for key, value in binding.items():
            row[key] = value.get("value", "")
        rows.append(row)
    return rows
