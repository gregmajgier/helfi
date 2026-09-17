def test_register_then_login_returns_tokens(client):
    register = client.post(
        "/auth/register", json={"email": "user@example.com", "password": "password123"}
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password123"}
    )

    assert login.status_code == 200
    body = login.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_register_duplicate_email_is_rejected(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})

    response = client.post(
        "/auth/register", json={"email": "dup@example.com", "password": "password123"}
    )

    assert response.status_code == 409
    assert response.json() == {"error": {"code": "409", "message": "email already registered"}}


def test_register_with_short_password_is_rejected(client):
    response = client.post(
        "/auth/register", json={"email": "shortpw@example.com", "password": "short12"}
    )

    assert response.status_code == 422


def test_login_with_wrong_password_is_rejected(client):
    client.post("/auth/register", json={"email": "user2@example.com", "password": "password123"})

    response = client.post(
        "/auth/login", json={"email": "user2@example.com", "password": "wrong"}
    )

    assert response.status_code == 401


def test_refresh_returns_new_token_pair(client):
    client.post("/auth/register", json={"email": "user3@example.com", "password": "password123"})
    login = client.post(
        "/auth/login", json={"email": "user3@example.com", "password": "password123"}
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_me_returns_current_user(client, auth_headers):
    headers = auth_headers(email="user4@example.com")

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "user4@example.com"


def test_me_without_token_is_rejected(client):
    response = client.get("/auth/me")

    assert response.status_code == 403


def test_oauth_login_creates_user_on_first_sign_in(client):
    response = client.post("/auth/oauth/google", json={"id_token": "newuser@example.com"})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_oauth_login_reuses_existing_user(client):
    first = client.post("/auth/oauth/google", json={"id_token": "same@example.com"})
    second = client.post("/auth/oauth/google", json={"id_token": "same@example.com"})

    me1 = client.get("/auth/me", headers={"Authorization": f"Bearer {first.json()['access_token']}"})
    me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {second.json()['access_token']}"})

    assert me1.json()["id"] == me2.json()["id"]


def test_oauth_login_rejects_invalid_token(client):
    response = client.post("/auth/oauth/google", json={"id_token": "invalid"})

    assert response.status_code == 401


def test_oauth_login_rejects_unknown_provider(client):
    response = client.post("/auth/oauth/facebook", json={"id_token": "someone@example.com"})

    assert response.status_code == 400


def test_login_with_password_for_oauth_only_user_is_rejected_not_crashed(client):
    client.post("/auth/oauth/google", json={"id_token": "oauthonly@example.com"})

    response = client.post(
        "/auth/login", json={"email": "oauthonly@example.com", "password": "anything"}
    )

    assert response.status_code == 401
