def test_register_user_success(client):
    payload = {
        "email": "testuser@example.com",
        "password": "securepassword123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "user"  # All newly registered users get 'user' role
    assert "hashed_password" not in data


def test_register_duplicate_email_fails(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "full_name": "User One"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_login_success(client):
    # Register user
    reg_payload = {
        "email": "loginuser@example.com",
        "password": "loginpassword123",
        "full_name": "Login User"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login user
    login_payload = {
        "email": "loginuser@example.com",
        "password": "loginpassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@example.com"

def test_login_invalid_password_fails(client):
    reg_payload = {
        "email": "wrongpass@example.com",
        "password": "correctpassword"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpass@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_get_current_user_me_endpoint(client):
    reg_payload = {
        "email": "meuser@example.com",
        "password": "mepassword123",
        "full_name": "Me Profile"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "meuser@example.com", "password": "mepassword123"})
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == "meuser@example.com"
    assert data["full_name"] == "Me Profile"

def test_get_me_unauthorized_without_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code in (401, 403)
