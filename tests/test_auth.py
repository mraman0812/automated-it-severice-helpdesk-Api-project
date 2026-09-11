def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "New Person",
            "email": "newperson@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newperson@example.com"
    assert data["name"] == "New Person"


def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testemployee@example.com",
            "password": "TestPass123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "testemployee@example.com"


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testemployee@example.com",
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"


def test_get_me_authenticated(client, employee_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "testemployee@example.com"


def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
