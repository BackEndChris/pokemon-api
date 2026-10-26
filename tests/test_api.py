from fastapi.testclient import TestClient
from main import app
import pytest

from stats import TYPE_BASE_STATS
from moves import TYPE_MOVES
from database import engine
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
from pokemon_routes import save_pokemon_moves

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
    assert "special_attack" in data
    assert "special_defense" in data
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


@pytest.fixture
def auth_headers():
    client.post("/register", json={
        "username": "statsuser", "email": "stats@example.com", "password": "test123"
    })
    response = client.post("/login", json={"username": "statsuser", "password": "test123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.parametrize("pokemon_type", TYPE_BASE_STATS)
def test_create_and_read_all_types(auth_headers, pokemon_type, monkeypatch):
    monkeypatch.setattr("moves.random", lambda: 0.0)
    response = client.post("/pokemon", headers=auth_headers, json={
        "name": "Example", "type": pokemon_type, "level": 100
    })
    assert response.status_code == 200
    data = response.json()

    for stat, base in TYPE_BASE_STATS[pokemon_type].items():
        expected = base + 100 * (3 if stat == "hp" else 2)
        assert expected - 4 <= data[stat] <= expected + 4

    detail = client.get(f"/pokemon/{data['id']}").json()
    learned = detail.pop("moves")
    assert {move["name"] for move in learned} == {move["name"] for move in TYPE_MOVES[pokemon_type]}
    with engine.connect() as connection:
        stored_types = connection.execute(text("""
            SELECT DISTINCT moves.type FROM moves
            JOIN pokemon_moves ON moves.id = pokemon_moves.move_id
            WHERE pokemon_moves.pokemon_id = :id
        """), {"id": data["id"]}).scalars().all()
        assert stored_types == [pokemon_type]
    assert detail == data
    assert client.get("/pokemon").json() == [data]
    assert client.get("/my-pokemon", headers=auth_headers).json() == [data]


def test_update_preserves_variation_and_disallows_type_changes(auth_headers):
    original = client.post("/pokemon", headers=auth_headers, json={
        "name": "Example", "type": "Psychic", "level": 10
    }).json()
    url = f"/pokemon/{original['id']}"

    for level in (10, 15, 15, 20):
        response = client.put(url, headers=auth_headers, json={
            "name": "Renamed", "type": "Psychic", "level": level
        })
        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == "Renamed"
        assert updated["level"] == level
        for stat in TYPE_BASE_STATS["Psychic"]:
            growth = 3 if stat == "hp" else 2
            assert updated[stat] == original[stat] + (level - 10) * growth

    response = client.put(url, headers=auth_headers, json={
        "name": "Changed", "type": "Psychic", "level": 19
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Pokemon level cannot be lowered"
    detail = client.get(url).json()
    detail.pop("moves")
    assert detail == updated

    response = client.put(url, headers=auth_headers, json={
        "name": "Changed", "type": "Fighting", "level": 20
    })
    assert response.status_code == 400
    detail = client.get(url).json()
    detail.pop("moves")
    assert detail == updated

    response = client.delete(url, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["pokemon"] == updated


def test_unknown_type_is_rejected(auth_headers):
    response = client.post("/pokemon", headers=auth_headers, json={
        "name": "Example", "type": "Unknown", "level": 10
    })
    assert response.status_code == 422


def test_moves_are_persisted_and_only_roll_on_level_gains(auth_headers, monkeypatch):
    monkeypatch.setattr("moves.random", lambda: 0.99)
    original = client.post("/pokemon", headers=auth_headers, json={
        "name": "Example", "type": "Fire", "level": 10
    }).json()
    url = f"/pokemon/{original['id']}"
    assert [move["name"] for move in client.get(url).json()["moves"]] == ["Ember"]

    monkeypatch.setattr("moves.random", lambda: 0.0)
    # Neither reads nor a rename at the same level grant another attempt.
    response = client.put(url, headers=auth_headers, json={
        "name": "Renamed", "type": "Fire", "level": 10
    })
    assert response.status_code == 200
    assert [move["name"] for move in client.get(url).json()["moves"]] == ["Ember"]

    for level in (11, 25, 30, 100):
        response = client.put(url, headers=auth_headers, json={
            "name": "Renamed", "type": "Fire", "level": level
        })
        assert response.status_code == 200
        expected = {move["name"] for move in TYPE_MOVES["Fire"] if move["min_level"] <= level}
        assert {move["name"] for move in client.get(url).json()["moves"]} == expected

    with engine.connect() as connection:
        count = connection.execute(text("""
            SELECT count(*) FROM pokemon_moves WHERE pokemon_id = :id
        """), {"id": original["id"]}).scalar_one()
        assert count == 8


def test_creation_at_high_level_processes_learning_history(auth_headers, monkeypatch):
    monkeypatch.setattr("moves.random", lambda: 0.0)
    response = client.post("/pokemon", headers=auth_headers, json={
        "name": "Example", "type": "Electric", "level": 25
    })
    assert response.status_code == 200
    detail = client.get(f"/pokemon/{response.json()['id']}").json()
    assert {move["name"] for move in detail["moves"]} == {
        move["name"] for move in TYPE_MOVES["Electric"] if move["min_level"] <= 25
    }


def test_saving_a_move_from_another_type_is_rejected(auth_headers):
    response = client.post("/pokemon", headers=auth_headers, json={
        "name": "Example", "type": "Water", "level": 1
    })
    assert response.status_code == 200
    pokemon_id = response.json()["id"]
    with engine.begin() as connection:
        with pytest.raises(NoResultFound):
            save_pokemon_moves(connection, pokemon_id, ["Ember"])
    learned = client.get(f"/pokemon/{pokemon_id}").json()["moves"]
    assert [move["name"] for move in learned] == ["Water Gun"]
