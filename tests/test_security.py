from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from auth import SECRET_KEY, create_access_token
from auth_routes import pwd_context
from database import engine
from main import app

client = TestClient(app)
PASSWORD = "valid-password"


def register(username="ash", email="ash@example.com", password=PASSWORD):
    return client.post("/register", json={"username": username, "email": email, "password": password})


def login(username="ash", password=PASSWORD):
    return client.post("/login", json={"username": username, "password": password})


@pytest.fixture
def account():
    response = register()
    assert response.status_code == 200
    return {"Authorization": f"Bearer {create_access_token(response.json()['id'])}"}


def pokemon(headers, name="Pikachu", **changes):
    data = {"name": name, "type": "Electric", "level": 1, **changes}
    return client.post("/pokemon", headers=headers, json=data)


@pytest.mark.parametrize("name", ["", "   ", "123", "１２３", "²", "a" * 51])
def test_invalid_pokemon_names(account, name):
    assert pokemon(account, name).status_code == 422


@pytest.mark.parametrize("name", ["Pikachu123", "Porygon2", "Mr. Mime", "a" * 50])
def test_valid_names_are_trimmed(account, name):
    response = pokemon(account, f"  {name}  ")
    assert response.status_code == 200
    assert response.json()["name"] == name
    response = client.put(f"/pokemon/{response.json()['id']}", headers=account, json={"name": "  Porygon2  ", "type": "Electric", "level": 1})
    assert response.json()["name"] == "Porygon2"


@pytest.mark.parametrize("email", ["invalid", "a@", "@example.com", "a b@example.com"])
def test_invalid_email(email):
    assert register(email=email).status_code == 422


@pytest.mark.parametrize("username", ["", "   ", "ab", "a" * 33, "ash ketchum", "ash@home", "éclair", ".ash"])
def test_invalid_usernames(username):
    assert register(username=username).status_code == 422


def test_case_insensitive_registration_login_and_database_uniqueness():
    assert register("  Ash  ").json()["username"] == "ash"
    assert login("ASH").status_code == 200
    assert register("aSh", "other@example.com").status_code == 409
    assert register("other", "ash@example.com").status_code == 409
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO users (username, email, password_hash)
                VALUES ('ASH', 'different@example.com', 'hash')
            """))
    assert login("Ash").status_code == 200


@pytest.mark.parametrize("password", ["", "short", " " * 8, "a" * 73, "é" * 37, "😀" * 19, "valid\x00password"])
def test_invalid_passwords_are_never_echoed(password):
    response = register(password=password)
    assert response.status_code == 422
    assert all("input" not in error and "ctx" not in error for error in response.json()["detail"])


@pytest.mark.parametrize("password", ["a" * 8, "a" * 72, "é" * 36, "😀" * 18, "  password  "])
def test_password_boundaries_and_no_silent_changes(password):
    assert register(password=password).status_code == 200
    assert login(password=password).status_code == 200
    if password.startswith(" "):
        assert login(password=password.strip()).status_code == 401
    with engine.connect() as connection:
        stored = connection.execute(text("SELECT password_hash FROM users")).scalar_one()
        assert stored != password
        assert pwd_context.verify(password, stored)


def test_legacy_short_password_and_mixed_case_username_remain_usable():
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO users (username, email, password_hash)
            VALUES (:username, :email, :hash)
        """), {"username": "LegacyAsh", "email": "legacy@example.com", "hash": pwd_context.hash("old")})
    assert login("LEGACYASH", "old").status_code == 200


def test_wrong_credentials_use_same_generic_response():
    register()
    wrong = login(password="incorrect")
    missing = login("unknown")
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json() == missing.json() == {"detail": "Invalid username or password"}
    assert login(password="é" * 37).status_code == 422


@pytest.mark.parametrize("header", [None, "", "Basic abc", "Bearer", "Bearer garbage", "Bearer a.b.c"])
def test_missing_or_malformed_authorization(header):
    headers = {} if header is None else {"Authorization": header}
    response = client.get("/my-pokemon", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("subject", [None, "abc", "1.0", "-1", "0", "1" * 100, "2147483648", 1, [], {}, True])
def test_invalid_token_subjects(subject):
    token = jwt.encode({"sub": subject, "exp": datetime.now(timezone.utc) + timedelta(minutes=1)}, SECRET_KEY, algorithm="HS256")
    response = client.get("/my-pokemon", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


@pytest.mark.parametrize("claims,key", [
    ({"sub": "1"}, SECRET_KEY),
    ({"sub": "1", "exp": 0}, SECRET_KEY),
    ({"sub": "1", "exp": []}, SECRET_KEY),
    ({"sub": "1", "exp": 9999999999}, "wrong-key"),
])
def test_expired_missing_expiry_or_invalid_signature(claims, key):
    token = jwt.encode(claims, key, algorithm="HS256")
    assert client.get("/my-pokemon", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_deleted_user_token_is_rejected(account):
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM users"))
    assert client.get("/my-pokemon", headers=account).status_code == 401


def test_nonexistent_resources_and_ownership(account):
    assert client.get("/pokemon/99999").status_code == 404
    assert client.delete("/pokemon/99999", headers=account).status_code == 404
    row = pokemon(account).json()
    other = register("misty", "misty@example.com").json()
    other_headers = {"Authorization": f"Bearer {create_access_token(other['id'])}"}
    path = f"/pokemon/{row['id']}"
    assert client.put(path, headers=other_headers, json={"name": "Changed", "type": "Electric", "level": 10}).status_code == 404
    assert client.delete(path, headers=other_headers).status_code == 404
    assert client.get(path).json()["name"] == "Pikachu"
    assert client.get("/my-pokemon", headers=other_headers).json() == []


def test_paginated_lists_are_bounded_ordered_and_owner_scoped(account):
    own_ids = [pokemon(account, f"Pikachu{index}").json()["id"] for index in range(4)]
    other = register("misty", "misty@example.com").json()
    pokemon({"Authorization": f"Bearer {create_access_token(other['id'])}"}, "Squirtle")
    assert [row["id"] for row in client.get("/pokemon?limit=2&offset=1").json()] == own_ids[1:3]
    assert [row["id"] for row in client.get("/my-pokemon?limit=2&offset=2", headers=account).json()] == own_ids[2:]
    assert client.get("/pokemon?offset=999").json() == []
    for query in ("limit=0", "limit=101", "offset=-1", "offset=100001", "limit=abc"):
        assert client.get(f"/pokemon?{query}").status_code == 422
        assert client.get(f"/my-pokemon?{query}", headers=account).status_code == 422


def test_missing_move_records_rollback_creation(account):
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM moves WHERE name = 'Thunder Shock'"))
    try:
        response = pokemon(account)
        assert response.status_code == 503
        assert client.get("/pokemon").json() == []
    finally:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO moves (name,type,power) VALUES ('Thunder Shock','Electric',40)"))


def test_duplicate_move_records_are_safe_server_failures(account):
    with engine.begin() as connection:
        move_id = connection.execute(text("INSERT INTO moves (name,type,power) VALUES ('Thunder Shock','Electric',40) RETURNING id")).scalar_one()
    try:
        assert pokemon(account).status_code == 503
        assert client.get("/pokemon").json() == []
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM moves WHERE id=:id"), {"id": move_id})


def test_missing_move_rolls_back_level_stats_and_assignments(account, monkeypatch):
    original = pokemon(account).json()
    monkeypatch.setattr("moves.random", lambda: 0.0)
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM moves WHERE name='Nuzzle'"))
    try:
        response = client.put(f"/pokemon/{original['id']}", headers=account, json={"name": "Changed", "type": "Electric", "level": 5})
        assert response.status_code == 503
        detail = client.get(f"/pokemon/{original['id']}").json()
        assert detail.pop("moves") == [{"name": "Thunder Shock", "power": 40}]
        assert detail == original
    finally:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO moves (name,type,power) VALUES ('Nuzzle','Electric',20)"))


def test_database_failure_response_and_logs_are_safe(monkeypatch, caplog):
    def fail():
        raise OperationalError("secret SQL", {"password": "private-value"}, Exception("private-credential"))

    monkeypatch.setattr(engine, "connect", fail)
    response = client.get("/pokemon")
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]
    assert "OperationalError" in caplog.text
    assert "private-credential" not in response.text + caplog.text
    assert "private-value" not in response.text + caplog.text


def test_programming_errors_remain_server_errors(monkeypatch, caplog):
    def fail():
        raise RuntimeError("private-internal-detail")

    monkeypatch.setattr(engine, "connect", fail)
    response = TestClient(app, raise_server_exceptions=False).get("/pokemon")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "private-internal-detail" not in response.text + caplog.text
