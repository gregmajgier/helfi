MOOD_PAYLOAD = {"logged_at": "2026-10-01T08:00:00Z", "mood_score": 4, "tags": ["calm"], "note": "good day"}


def test_create_and_list_mood_entry(client, auth_headers):
    headers = auth_headers()

    create = client.post("/mood/entries", json=MOOD_PAYLOAD, headers=headers)
    assert create.status_code == 201
    assert create.json()["mood_score"] == 4

    listing = client.get("/mood/entries", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_mood_entry_score_out_of_range_is_rejected(client, auth_headers):
    headers = auth_headers()

    too_low = client.post("/mood/entries", json={**MOOD_PAYLOAD, "mood_score": 0}, headers=headers)
    too_high = client.post("/mood/entries", json={**MOOD_PAYLOAD, "mood_score": 6}, headers=headers)

    assert too_low.status_code == 422
    assert too_high.status_code == 422


def test_update_and_delete_own_mood_entry(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/mood/entries", json=MOOD_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/mood/entries/{entry_id}", json={"mood_score": 2}, headers=headers)
    assert update.status_code == 200
    assert update.json()["mood_score"] == 2

    delete = client.delete(f"/mood/entries/{entry_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/mood/entries", headers=headers)
    assert listing.json() == []


def test_user_cannot_read_or_modify_another_users_mood_entry(client, auth_headers):
    headers_a = auth_headers(email="mood-owner@example.com")
    headers_b = auth_headers(email="mood-intruder@example.com")
    entry_id = client.post("/mood/entries", json=MOOD_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/mood/entries/{entry_id}", json={"mood_score": 1}, headers=headers_b)
    assert update.status_code == 404

    delete = client.delete(f"/mood/entries/{entry_id}", headers=headers_b)
    assert delete.status_code == 404


def test_mood_entries_require_auth(client):
    response = client.get("/mood/entries")

    assert response.status_code == 403


JOURNAL_PAYLOAD = {"written_at": "2026-10-01T08:00:00Z", "prompt": "How was today?", "body": "It was fine."}


def test_create_and_list_journal_entry(client, auth_headers):
    headers = auth_headers()

    create = client.post("/mood/journal", json=JOURNAL_PAYLOAD, headers=headers)
    assert create.status_code == 201

    listing = client.get("/mood/journal", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_journal_entry_with_empty_body_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {**JOURNAL_PAYLOAD, "body": "   "}

    response = client.post("/mood/journal", json=payload, headers=headers)

    assert response.status_code == 422


def test_update_and_delete_own_journal_entry(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/mood/journal", json=JOURNAL_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/mood/journal/{entry_id}", json={"body": "Changed my mind."}, headers=headers)
    assert update.status_code == 200
    assert update.json()["body"] == "Changed my mind."

    delete = client.delete(f"/mood/journal/{entry_id}", headers=headers)
    assert delete.status_code == 204


def test_user_cannot_read_or_modify_another_users_journal_entry(client, auth_headers):
    headers_a = auth_headers(email="journal-owner@example.com")
    headers_b = auth_headers(email="journal-intruder@example.com")
    entry_id = client.post("/mood/journal", json=JOURNAL_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/mood/journal/{entry_id}", json={"body": "nope"}, headers=headers_b)
    assert update.status_code == 404


def test_get_todays_prompt_returns_consistent_result(client, auth_headers):
    headers = auth_headers()

    first = client.get("/mood/prompts", headers=headers)
    second = client.get("/mood/prompts", headers=headers)

    assert first.status_code == 200
    assert first.json()["prompt"]
    assert first.json()["prompt"] == second.json()["prompt"]
