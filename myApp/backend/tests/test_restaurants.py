def test_create_and_list_restaurants(client):
    payload = {
        "name": "Cafe Nova",
        "cuisine": "Cafe",
        "address": "100 Test Dr",
        "latitude": 30.3,
        "longitude": -97.7,
    }

    create_response = client.post("/api/v1/restaurants", json=payload)
    assert create_response.status_code == 201

    list_response = client.get("/api/v1/restaurants")
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Cafe Nova"
