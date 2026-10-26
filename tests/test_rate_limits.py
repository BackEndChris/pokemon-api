from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

import config
from main import app
from rate_limits import limiter, RateLimiter
from tests.test_security import account, client, login, register, pokemon, PASSWORD
from tests.test_uploads import upload


@pytest.fixture
def clock(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(limiter, "clock", lambda: now[0])
    monkeypatch.setattr(config, "RATE_WINDOW_SECONDS", 60)
    return now


def test_registration_limit_includes_invalid_requests_and_recovers(clock, monkeypatch):
    monkeypatch.setattr(config, "REGISTER_LIMIT", 2)
    for _ in range(2):
        assert client.post("/register", json={}).status_code == 422
    response = register()
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) == 60
    clock[0] += 30
    assert int(register().headers["retry-after"]) == 30
    clock[0] += 30
    assert register().status_code == 200


def test_login_account_limit_is_case_insensitive_and_source_scoped(account, clock, monkeypatch):
    monkeypatch.setattr(config, "LOGIN_ACCOUNT_LIMIT", 2)
    assert login("Ash", "wrong-password").status_code == 401
    assert login("ASH", "wrong-password").status_code == 401
    assert login().status_code == 429
    assert login("different").status_code == 401
    # Blocking one source cannot lock the account for another source.
    other = TestClient(app, client=("198.51.100.2", 5000))
    assert other.post("/login", json={"username": "ash", "password": PASSWORD}).status_code == 200
    clock[0] += 61
    assert login().status_code == 200


def test_login_source_limit_prevents_username_rotation_and_header_spoofing(clock, monkeypatch):
    monkeypatch.setattr(config, "LOGIN_SOURCE_LIMIT", 2)
    assert login("first").status_code == 401
    assert login("second").status_code == 401
    response = client.post("/login", headers={"X-Forwarded-For": "203.0.113.123"}, json={"username": "third", "password": PASSWORD})
    assert response.status_code == 429
    clock[0] += 61
    assert login("third").status_code == 401


def test_upload_rate_limit_recovers_without_waiting(account, clock, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_LIMIT", 2)
    row = pokemon(account).json()
    assert upload(account, row["id"]).status_code == 200
    assert upload(account, row["id"]).status_code == 200
    response = upload(account, row["id"])
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    clock[0] += 60
    assert upload(account, row["id"]).status_code == 200


def test_limiter_bounds_memory_and_reclaims_expired_keys(monkeypatch):
    now = [0.0]
    local = RateLimiter(clock=lambda: now[0], max_keys=2)
    local.check([("one", 10)])
    local.check([("two", 10)])
    with pytest.raises(HTTPException) as error:
        local.check([("three", 10)])
    assert error.value.status_code == 429
    assert len(local.buckets) == 2
    now[0] += config.RATE_WINDOW_SECONDS
    local.check([("three", 10)])
    assert len(local.buckets) == 1
