def test_search_foods_matches_partial_case_insensitive_name(client, auth_headers):
    headers = auth_headers()

    response = client.get("/meals/foods/search", params={"q": "CHICK"}, headers=headers)

    assert response.status_code == 200
    names = [f["name"] for f in response.json()]
    assert any("Chicken" in name for name in names)


def test_search_foods_requires_auth(client):
    response = client.get("/meals/foods/search", params={"q": "chicken"})

    assert response.status_code == 401
