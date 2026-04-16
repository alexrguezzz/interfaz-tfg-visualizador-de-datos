from __future__ import annotations

from flask import redirect, request, session, url_for


def register_selection_routes(app, deps) -> None:
    ensure_onboarding_boot_token = deps["ensure_onboarding_boot_token"]
    onboarding_league_labels = deps["ONBOARDING_LEAGUE_LABELS"]
    onboarding_seasons = deps["ONBOARDING_SEASONS"]

    @app.route("/selection", methods=["POST"])
    def save_selection():
        ensure_onboarding_boot_token()
        competitions = [value for value in request.form.getlist("competitions") if value in onboarding_league_labels]
        seasons = [value for value in request.form.getlist("seasons") if value in onboarding_seasons]

        if competitions and seasons:
            session["onboarding_competitions"] = competitions
            session["onboarding_seasons"] = seasons

        return redirect(request.form.get("next", url_for("home")))

