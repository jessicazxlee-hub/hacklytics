def test_register_and_login_is_disabled(client):
    register_payload = {
        "email": "user@example.com",
        "password": "password123",
        "firebase_uid": "firebase-user-123",
        "neighborhood": "South Congress",
    }
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_payload = {"email": "user@example.com", "password": "password123"}
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 410
    assert (
        login_response.json()["detail"]
        == "Local login is disabled. Use Firebase authentication and send Firebase ID tokens to backend endpoints."
    )
