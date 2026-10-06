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


def test_estimate_from_description_returns_estimate(client, auth_headers):
    headers = auth_headers()

    response = client.post(
        "/meals/estimate-from-description",
        json={"description": "a bowl of oatmeal with banana and peanut butter"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["calories"] > 0
    assert 0 <= body["confidence"] <= 1


def test_estimate_from_description_rejects_empty_description(client, auth_headers):
    headers = auth_headers()

    response = client.post("/meals/estimate-from-description", json={"description": "   "}, headers=headers)

    assert response.status_code == 400


def test_estimate_from_description_requires_auth(client):
    response = client.post("/meals/estimate-from-description", json={"description": "an apple"})

    assert response.status_code == 403


def test_estimate_from_description_rejects_oversized_description(client, auth_headers):
    headers = auth_headers()

    response = client.post("/meals/estimate-from-description", json={"description": "a" * 501}, headers=headers)

    assert response.status_code == 422


def test_barcode_lookup_rejects_non_numeric_barcode(client, auth_headers):
    headers = auth_headers()

    response = client.get("/meals/foods/barcode/..%2F..%2Fadmin", headers=headers)

    assert response.status_code in (404, 422)
    assert client.get("/meals/foods/barcode/abc123", headers=headers).status_code == 422


class _FakeOffResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _stub_open_food_facts(monkeypatch, payload, status_code=200):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url):
            return _FakeOffResponse(payload, status_code)

    monkeypatch.setattr("app.meals.router.httpx.AsyncClient", FakeClient)


def _off_product(**overrides):
    nutriments = {
        "energy-kcal_100g": 250,
        "proteins_100g": 8,
        "carbohydrates_100g": 40,
        "fat_100g": 6,
        "sodium_100g": 0.4,
    }
    nutriments.update(overrides.pop("nutriments", {}))
    return {"status": 1, "product": {"product_name": "Oat bar", "nutriments": nutriments, **overrides}}


def test_barcode_lookup_caches_a_valid_open_food_facts_product(client, auth_headers, monkeypatch):
    _stub_open_food_facts(monkeypatch, _off_product())

    response = client.get("/meals/foods/barcode/5000112637922", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Oat bar"
    assert body["calories_per_serving"] == 250
    assert body["sodium_mg"] == 400


def test_barcode_lookup_rejects_implausible_open_food_facts_values(client, auth_headers, monkeypatch):
    headers = auth_headers()
    bad_nutriments = [
        {"energy-kcal_100g": -5},
        {"energy-kcal_100g": 1_000_000},
        {"energy-kcal_100g": "lots"},
        {"energy-kcal_100g": float("nan")},
        {"proteins_100g": 400},
        {"sodium_100g": 5000},
        {"proteins_100g": 60, "carbohydrates_100g": 60, "fat_100g": 60},
    ]
    for index, nutriments in enumerate(bad_nutriments):
        _stub_open_food_facts(monkeypatch, _off_product(nutriments=nutriments))
        barcode = f"500011263{index:04d}"
        assert client.get(f"/meals/foods/barcode/{barcode}", headers=headers).status_code == 404, nutriments


def test_barcode_lookup_rejects_bad_names_and_shapes(client, auth_headers, monkeypatch):
    headers = auth_headers()
    payloads = [
        _off_product(product_name="x" * 121),
        _off_product(product_name="bad\x00name"),
        _off_product(product_name=["not", "a", "string"]),
        {"status": 1, "product": "oops"},
        {"status": 1, "product": {"product_name": "No nutriments"}},
        ["not", "a", "dict"],
    ]
    for index, payload in enumerate(payloads):
        _stub_open_food_facts(monkeypatch, payload)
        barcode = f"600011263{index:04d}"
        assert client.get(f"/meals/foods/barcode/{barcode}", headers=headers).status_code == 404, payload


def test_barcode_lookup_treats_non_json_as_unavailable(client, auth_headers, monkeypatch):
    _stub_open_food_facts(monkeypatch, ValueError("not json"))

    response = client.get("/meals/foods/barcode/70001126370001", headers=auth_headers())

    assert response.status_code == 502


def test_estimate_from_description_is_rate_limited(client, auth_headers):
    headers = auth_headers()

    codes = [
        client.post("/meals/estimate-from-description", json={"description": "an apple"}, headers=headers).status_code
        for _ in range(31)
    ]

    assert codes[-1] == 429
    assert 429 not in codes[:-1]
