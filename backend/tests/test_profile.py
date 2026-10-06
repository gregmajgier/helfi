from datetime import date, datetime, timedelta, timezone

from app.profile.calc import (
    bmr,
    compute_targets,
    daily_delta,
    trend_kg_per_week,
    water_goal_ml,
)

def _today() -> date:
    # The server's notion of today is UTC.
    return datetime.now(timezone.utc).date()


YEAR = _today().year

PROFILE = {
    "sex": "male",
    "birth_year": YEAR - 30,
    "height_cm": 180,
    "weight_kg": 80,
    "activity_level": "moderate",
    "goal": "lose",
    "goal_weight_kg": 74,
    "weekly_change_kg": 0.5,
}


def test_bmr_mifflin_st_jeor_male_and_female():
    assert bmr("male", 80, 180, 30) == 1780
    assert bmr("female", 60, 165, 28) == 600 + 1031.25 - 140 - 161


def test_daily_delta_signs():
    assert daily_delta("lose", 0.5) == -550
    assert daily_delta("build", 0.25) == 275
    assert daily_delta("maintain", 0.5) == 0


def test_targets_for_weight_loss():
    targets = compute_targets(PROFILE, YEAR)
    assert targets["bmr"] == 1780
    assert targets["tdee"] == 2759
    assert targets["calories"] == 2209
    # 30/40/30 default split for losing weight.
    assert targets["protein_g"] == round(2209 * 0.30 / 4)
    assert targets["carbs_g"] == round(2209 * 0.40 / 4)
    assert targets["fat_g"] == round(2209 * 0.30 / 9)
    assert targets["warnings"] == []


def test_calorie_floor_applies_with_warning():
    small = {**PROFILE, "sex": "female", "weight_kg": 50, "height_cm": 150, "activity_level": "sedentary", "weekly_change_kg": 1}
    targets = compute_targets(small, YEAR)
    assert targets["calories"] == 1200
    assert targets["warnings"]


def test_calorie_override_bypasses_floor_and_split_is_respected():
    custom = {
        **PROFILE,
        "calorie_override": 1800,
        "macro_split": {"protein_pct": 40, "carbs_pct": 30, "fat_pct": 30},
    }
    targets = compute_targets(custom, YEAR)
    assert targets["calories"] == 1800
    assert targets["protein_g"] == 180


def test_water_goal_rounds_and_clamps():
    assert water_goal_ml(80) == 2800
    assert water_goal_ml(40) == 1500
    assert water_goal_ml(200) == 4000


def test_trend_needs_enough_spread_and_points():
    assert trend_kg_per_week([(0, 80), (-2, 80.2)]) is None
    assert trend_kg_per_week([(-1, 80), (0, 80), (-2, 80.2)]) is None  # < 7 days spread
    slope = trend_kg_per_week([(-14, 82), (-7, 81), (0, 80)])
    assert slope == -1.0


def test_profile_requires_setup_first(client, auth_headers):
    headers = auth_headers()
    assert client.get("/profile", headers=headers).status_code == 404
    assert client.get("/profile/targets", headers=headers).status_code == 404


def test_put_get_and_targets(client, auth_headers):
    headers = auth_headers()
    saved = client.put("/profile", json=PROFILE, headers=headers)
    assert saved.status_code == 200
    assert client.get("/profile", headers=headers).json()["height_cm"] == 180
    assert client.get("/profile/targets", headers=headers).json()["calories"] == 2209
    # First save seeds the weight log.
    assert len(client.get("/profile/weight", headers=headers).json()) == 1


def test_profile_is_per_user(client, auth_headers):
    a = auth_headers(email="pa@example.com")
    b = auth_headers(email="pb@example.com")
    client.put("/profile", json=PROFILE, headers=a)
    assert client.get("/profile", headers=b).status_code == 404


def test_profile_validation(client, auth_headers):
    headers = auth_headers()
    assert client.put("/profile", json={**PROFILE, "weekly_change_kg": 2}, headers=headers).status_code == 422
    assert client.put("/profile", json={**PROFILE, "birth_year": YEAR - 5}, headers=headers).status_code == 422
    assert client.put("/profile", json={**PROFILE, "macro_split": {"protein_pct": 30, "carbs_pct": 30, "fat_pct": 30}}, headers=headers).status_code == 422


def test_weight_log_replaces_same_day_and_syncs_profile(client, auth_headers):
    headers = auth_headers()
    client.put("/profile", json=PROFILE, headers=headers)
    today = _today().isoformat()

    client.post("/profile/weight", json={"day": today, "weight_kg": 79.4}, headers=headers)
    client.post("/profile/weight", json={"day": today, "weight_kg": 79.0}, headers=headers)

    weights = client.get("/profile/weight", headers=headers).json()
    assert [w["weight_kg"] for w in weights] == [79.0]
    assert client.get("/profile", headers=headers).json()["weight_kg"] == 79.0

    assert client.delete(f"/profile/weight/{weights[0]['id']}", headers=headers).status_code == 204


def test_weight_cannot_be_logged_far_in_the_future(client, auth_headers):
    headers = auth_headers()
    future = (_today() + timedelta(days=10)).isoformat()
    assert client.post("/profile/weight", json={"day": future, "weight_kg": 70}, headers=headers).status_code == 400


def test_forecast_uses_planned_rate_and_trend(client, auth_headers):
    headers = auth_headers()
    client.put("/profile", json=PROFILE, headers=headers)
    today = _today()
    for offset, kg in [(14, 82.0), (7, 81.0), (0, 80.0)]:
        client.post("/profile/weight", json={"day": (today - timedelta(days=offset)).isoformat(), "weight_kg": kg}, headers=headers)

    forecast = client.get("/profile/forecast", headers=headers).json()

    assert forecast["current_kg"] == 80.0
    assert forecast["trend_kg_per_week"] == -1.0
    # 6 kg to go at 0.5 kg/week is 12 weeks; at the observed 1 kg/week it is 6.
    assert forecast["planned_eta"] == (today + timedelta(days=84)).isoformat()
    assert forecast["trend_eta"] == (today + timedelta(days=42)).isoformat()
    assert forecast["reached"] is False


def test_forecast_reached(client, auth_headers):
    headers = auth_headers()
    client.put("/profile", json={**PROFILE, "weight_kg": 73, "goal_weight_kg": 74}, headers=headers)
    assert client.get("/profile/forecast", headers=headers).json()["reached"] is True
