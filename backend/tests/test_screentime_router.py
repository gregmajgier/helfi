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
