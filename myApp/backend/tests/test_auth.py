def test_register_and_login(client):
    register_payload = {
        "email": "user@example.com",
        "password": "password123",
        "full_name": "Test User",
    }
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_payload = {"email": "user@example.com", "password": "password123"}
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
