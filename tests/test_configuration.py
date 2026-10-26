import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest
from sqlalchemy.engine import make_url

from test_safety import read_test_config, guard_test_connection

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("contents", [None, "", "SECRET_KEY=test", "DATABASE_URL=postgresql://localhost/example_test", "DATABASE_URL=postgresql://localhost/pokemon_api\nSECRET_KEY=test", "DATABASE_URL=not-a-url\nSECRET_KEY=test", "DATABASE_URL=sqlite:///example_test\nSECRET_KEY=test"])
def test_missing_or_unsafe_test_configuration_cannot_fall_back(tmp_path, monkeypatch, contents):
    path = tmp_path / ".env.test"
    if contents is not None:
        path.write_text(contents)
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/pokemon_api")
    monkeypatch.setenv("SECRET_KEY", "inherited-value")
    with pytest.raises(RuntimeError):
        read_test_config(path, tmp_path / ".env")


def test_same_database_is_rejected_even_with_different_credentials(tmp_path):
    test = tmp_path / ".env.test"
    normal = tmp_path / ".env"
    test.write_text("DATABASE_URL=postgresql://testuser@localhost/shared_test\nSECRET_KEY=test")
    normal.write_text("DATABASE_URL=postgresql://appuser@localhost/shared_test")
    with pytest.raises(RuntimeError):
        read_test_config(test, normal)


def test_guard_refuses_wrong_engine_before_any_query():
    connection = Mock()
    connection.engine.url = make_url("postgresql://localhost/pokemon_api")
    with pytest.raises(RuntimeError):
        guard_test_connection(connection, "postgresql://localhost/pokemon_api_test")
    connection.execute.assert_not_called()


def test_guard_checks_actual_database_identity():
    connection = Mock()
    url = "postgresql://localhost/pokemon_api_test"
    connection.engine.url = make_url(url)
    connection.execute.return_value.scalar_one.return_value = "pokemon_api"
    with pytest.raises(RuntimeError):
        guard_test_connection(connection, url)
    assert connection.execute.call_count == 1


@pytest.mark.parametrize("name,value", [("SECRET_KEY", ""), ("SECRET_KEY", "  "), ("DATABASE_URL", ""), ("DATABASE_URL", "private-secret-invalid-url"), ("UPLOAD_LIMIT", "0"), ("RATE_WINDOW_SECONDS", "invalid")])
def test_configuration_fails_early_without_secret_values(name, value):
    env = {**os.environ, name: value}
    result = subprocess.run([sys.executable, "-c", "import config"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert name in result.stderr
    assert "private-secret-invalid-url" not in result.stderr


def test_chunked_authentication_body_is_bounded():
    from tests.test_security import client
    response = client.post("/login", content=iter([b"x" * 9000, b"y" * 9000]), headers={"Content-Type": "application/json"})
    assert response.status_code == 413
