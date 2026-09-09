from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Pokemon API is running"
    }

def test_register():
    response = client.post(
        "/register",
        json={
            "username": "testuser_pytest",
            "email": "testuser_pytest@example.com",
            "password": "test123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "testuser_pytest"
    assert data["email"] == "testuser_pytest@example.com"
    assert "id" in data

def test_login():
    client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "test123"
        }
    )

    response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "test123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_pokemon():
    client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "test123"
        }
    )

    login_response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "test123"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/pokemon",
        json={
            "name": "Dracuno",
            "type": "Fire",
            "level": 20
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Dracuno"
    assert data["type"] == "Fire"
    assert data["level"] == 20
    assert data["owner_id"] == 1

    assert "hp" in data
    assert "attack" in data
    assert "defense" in data
    assert "speed" in data

def test_create_pokemon_without_token():
    response = client.post(
        "/pokemon",
        json={
            "name": "Dracuno",
            "type": "Fire",
            "level": 20
        }
    )

    assert response.status_code == 401