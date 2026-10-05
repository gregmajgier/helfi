RULE_PAYLOAD = {"name": "Evening wind-down", "apps_or_categories": ["social", "games"], "daily_limit_minutes": 30}


def test_create_and_list_rule(client, auth_headers):
    headers = auth_headers()

    create = client.post("/screentime/rules", json=RULE_PAYLOAD, headers=headers)
    assert create.status_code == 201
    assert create.json()["enabled"] is True

    listing = client.get("/screentime/rules", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_rule_without_categories_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {**RULE_PAYLOAD, "apps_or_categories": []}

    response = client.post("/screentime/rules", json=payload, headers=headers)

    assert response.status_code == 422


def test_rule_with_non_positive_daily_limit_is_rejected(client, auth_headers):
    headers = auth_headers()

    zero = client.post("/screentime/rules", json={**RULE_PAYLOAD, "daily_limit_minutes": 0}, headers=headers)
    negative = client.post("/screentime/rules", json={**RULE_PAYLOAD, "daily_limit_minutes": -5}, headers=headers)

    assert zero.status_code == 422
    assert negative.status_code == 422


def test_rule_with_blank_name_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {**RULE_PAYLOAD, "name": "   "}

    response = client.post("/screentime/rules", json=payload, headers=headers)

    assert response.status_code == 422


def test_update_and_delete_own_rule(client, auth_headers):
    headers = auth_headers()
    rule_id = client.post("/screentime/rules", json=RULE_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/screentime/rules/{rule_id}", json={"enabled": False}, headers=headers)
    assert update.status_code == 200
    assert update.json()["enabled"] is False

    delete = client.delete(f"/screentime/rules/{rule_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/screentime/rules", headers=headers)
    assert listing.json() == []


def test_user_cannot_read_or_modify_another_users_rule(client, auth_headers):
    headers_a = auth_headers(email="rule-owner@example.com")
    headers_b = auth_headers(email="rule-intruder@example.com")
    rule_id = client.post("/screentime/rules", json=RULE_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/screentime/rules/{rule_id}", json={"enabled": False}, headers=headers_b)
    assert update.status_code == 404

    delete = client.delete(f"/screentime/rules/{rule_id}", headers=headers_b)
    assert delete.status_code == 404

    listing = client.get("/screentime/rules", headers=headers_b)
    assert listing.json() == []


def test_screentime_rules_require_auth(client):
    response = client.get("/screentime/rules")

    assert response.status_code == 403


# --- usage sync ---

from datetime import date, timedelta  # noqa: E402


def _day(offset: int = 0) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def test_usage_upsert_is_idempotent_and_overwrites(client, auth_headers):
    headers = auth_headers()
    day = _day(-1)

    first = client.put(f"/screentime/usage/{day}", json={"total_minutes": 200, "dumb_minutes": 90}, headers=headers)
    second = client.put(f"/screentime/usage/{day}", json={"total_minutes": 240, "dumb_minutes": 100}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    listing = client.get(f"/screentime/usage?start={day}&end={day}", headers=headers).json()
    assert len(listing) == 1
    assert listing[0]["date"] == day
    assert listing[0]["total_minutes"] == 240
    assert listing[0]["dumb_minutes"] == 100


def test_usage_list_returns_sorted_range_only(client, auth_headers):
    headers = auth_headers()
    for offset in (-3, -1, -2, -10):
        client.put(f"/screentime/usage/{_day(offset)}", json={"total_minutes": 60, "dumb_minutes": 30}, headers=headers)

    listing = client.get(f"/screentime/usage?start={_day(-3)}&end={_day(-1)}", headers=headers).json()

    assert [r["date"] for r in listing] == [_day(-3), _day(-2), _day(-1)]


def test_usage_is_isolated_per_user(client, auth_headers):
    alice = auth_headers("alice@example.com")
    bob = auth_headers("bob@example.com")
    day = _day(-1)
    client.put(f"/screentime/usage/{day}", json={"total_minutes": 100, "dumb_minutes": 50}, headers=alice)

    assert client.get(f"/screentime/usage?start={day}&end={day}", headers=bob).json() == []
    client.put(f"/screentime/usage/{day}", json={"total_minutes": 10, "dumb_minutes": 5}, headers=bob)
    alice_rows = client.get(f"/screentime/usage?start={day}&end={day}", headers=alice).json()
    assert alice_rows[0]["total_minutes"] == 100


def test_usage_requires_auth(client):
    assert client.get(f"/screentime/usage?start={_day(-1)}&end={_day()}").status_code in (401, 403)
    body = {"total_minutes": 1, "dumb_minutes": 1}
    assert client.put(f"/screentime/usage/{_day()}", json=body).status_code in (401, 403)


def test_usage_rejects_invalid_minutes(client, auth_headers):
    headers = auth_headers()
    url = f"/screentime/usage/{_day(-1)}"

    for payload in (
        {"total_minutes": -1, "dumb_minutes": 0},
        {"total_minutes": 1441, "dumb_minutes": 0},
        {"total_minutes": 60, "dumb_minutes": 61},
        {"total_minutes": 60},
        {"total_minutes": "abc", "dumb_minutes": 1},
    ):
        assert client.put(url, json=payload, headers=headers).status_code == 422, payload


def test_usage_rejects_bad_dates(client, auth_headers):
    headers = auth_headers()
    body = {"total_minutes": 60, "dumb_minutes": 30}

    assert client.put("/screentime/usage/not-a-date", json=body, headers=headers).status_code == 422
    assert client.put(f"/screentime/usage/{_day(5)}", json=body, headers=headers).status_code == 400
    assert client.put(f"/screentime/usage/{_day(-401)}", json=body, headers=headers).status_code == 400
    assert client.put(f"/screentime/usage/{_day(-400)}", json=body, headers=headers).status_code == 200


def test_usage_range_validation(client, auth_headers):
    headers = auth_headers()

    reversed_range = client.get(f"/screentime/usage?start={_day(0)}&end={_day(-1)}", headers=headers)
    too_long = client.get(f"/screentime/usage?start={_day(-366)}&end={_day(0)}", headers=headers)
    max_ok = client.get(f"/screentime/usage?start={_day(-365)}&end={_day(0)}", headers=headers)
    missing = client.get("/screentime/usage", headers=headers)

    assert reversed_range.status_code == 400
    assert too_long.status_code == 400
    assert max_ok.status_code == 200
    assert missing.status_code == 422


def test_usage_put_is_rate_limited_per_user(client, auth_headers):
    headers = auth_headers()
    other = auth_headers("other@example.com")
    url = f"/screentime/usage/{_day(-1)}"
    body = {"total_minutes": 60, "dumb_minutes": 30}

    codes = [client.put(url, json=body, headers=headers).status_code for _ in range(61)]

    assert codes[:60] == [200] * 60
    assert codes[60] == 429
    assert client.put(url, json=body, headers=other).status_code == 200
