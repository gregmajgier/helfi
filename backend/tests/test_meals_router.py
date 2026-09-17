def test_search_foods_matches_partial_case_insensitive_name(client, auth_headers):
    headers = auth_headers()

    response = client.get("/meals/foods/search", params={"q": "CHICK"}, headers=headers)

    assert response.status_code == 200
    names = [f["name"] for f in response.json()]
    assert any("Chicken" in name for name in names)


def test_search_foods_requires_auth(client):
    response = client.get("/meals/foods/search", params={"q": "chicken"})

    assert response.status_code == 403


ENTRY_PAYLOAD = {
    "meal_slot": "breakfast",
    "source": "quick_add",
    "logged_at": "2026-09-16T08:00:00Z",
    "calories": 300,
    "protein_g": 20,
    "carbs_g": 30,
    "fat_g": 10,
}


def test_create_and_list_entry_for_day(client, auth_headers):
    headers = auth_headers()

    create = client.post("/meals/entries", json=ENTRY_PAYLOAD, headers=headers)
    assert create.status_code == 201

    listing = client.get("/meals/entries", params={"day": "2026-09-16"}, headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["calories"] == 300


def test_update_and_delete_own_entry(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/meals/entries", json=ENTRY_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/meals/entries/{entry_id}", json={"calories": 450}, headers=headers)
    assert update.status_code == 200
    assert update.json()["calories"] == 450

    delete = client.delete(f"/meals/entries/{entry_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/meals/entries", params={"day": "2026-09-16"}, headers=headers)
    assert listing.json() == []


def test_user_cannot_read_or_modify_another_users_entry(client, auth_headers):
    headers_a = auth_headers(email="owner@example.com")
    headers_b = auth_headers(email="intruder@example.com")
    entry_id = client.post("/meals/entries", json=ENTRY_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/meals/entries/{entry_id}", json={"calories": 999}, headers=headers_b)
    assert update.status_code == 404

    delete = client.delete(f"/meals/entries/{entry_id}", headers=headers_b)
    assert delete.status_code == 404


def test_list_entries_excludes_other_users_entries(client, auth_headers):
    headers_a = auth_headers(email="owner2@example.com")
    headers_b = auth_headers(email="intruder2@example.com")
    client.post("/meals/entries", json=ENTRY_PAYLOAD, headers=headers_a)

    listing = client.get("/meals/entries", params={"day": "2026-09-16"}, headers=headers_b)

    assert listing.status_code == 200
    assert listing.json() == []


def test_photo_estimate_returns_estimate(client, auth_headers):
    headers = auth_headers()
    files = {"photo": ("meal.jpg", b"fake-image-bytes", "image/jpeg")}

    response = client.post("/meals/photo-estimate", headers=headers, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["calories"] > 0
    assert 0 <= body["confidence"] <= 1


def test_photo_estimate_rejects_unsupported_file_type(client, auth_headers):
    headers = auth_headers()
    files = {"photo": ("notes.txt", b"not an image", "text/plain")}

    response = client.post("/meals/photo-estimate", headers=headers, files=files)

    assert response.status_code == 400


def test_photo_estimate_rejects_oversized_photo(client, auth_headers):
    headers = auth_headers()
    oversized_bytes = b"x" * (10 * 1024 * 1024 + 1)
    files = {"photo": ("meal.jpg", oversized_bytes, "image/jpeg")}

    response = client.post("/meals/photo-estimate", headers=headers, files=files)

    assert response.status_code == 400
