import uuid


def _unique_email() -> str:
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_register_creates_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": _unique_email(),
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "hashed_password" not in data  # пароль никогда не должен утекать в ответе


def test_register_duplicate_email_fails(client):
    email = _unique_email()
    payload = {
        "email": email,
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "password": "testpassword123",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post(
        "/auth/register",
        json={**payload, "username": f"other_{uuid.uuid4().hex[:8]}"},
    )
    assert second.status_code == 400


def test_login_with_correct_credentials(client):
    email = _unique_email()
    password = "correctpassword123"
    client.post(
        "/auth/register",
        json={"email": email, "username": f"user_{uuid.uuid4().hex[:8]}", "password": password},
    )

    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_fails(client):
    email = _unique_email()
    client.post(
        "/auth/register",
        json={
            "email": email,
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "correctpassword",
        },
    )

    response = client.post("/auth/login", json={"email": email, "password": "wrongpassword"})
    assert response.status_code == 401


def test_conversations_require_auth(client):
    response = client.get("/conversations/")
    assert response.status_code == 401