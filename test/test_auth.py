def test_register_user(client):
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass"
    })
    assert response.status_code == 201
    data = response.get_json()
    
    assert "user" in data
    assert "id" in data["user"]
    assert data["user"]["username"] == "testuser"


def test_login_user(client):
    # first register
    client.post("/api/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "securepass"
    })

    # then login
    response = client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "securepass"
    }, follow_redirects=False)

    print("Status:", response.status_code)
    print("Headers:", response.headers)
    print("Body:", response.get_data(as_text=True))

    print(response.status_code)
    print(response.location)

    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
