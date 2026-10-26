import os
from test_safety import read_test_config, guard_test_connection

test_config = read_test_config()
os.environ.update({key: value for key, value in test_config.items() if value is not None})

import pytest
from sqlalchemy import text

from database import engine
from rate_limits import limiter


@pytest.fixture(autouse=True)
def clean_database():
    # Re-read the explicit file and check the actual connection immediately
    # before TRUNCATE. Never trust an inherited DATABASE_URL alone.
    approved = read_test_config()
    with engine.begin() as connection:
        guard_test_connection(connection, approved["DATABASE_URL"])
        connection.execute(
            text("""
                TRUNCATE TABLE pokemon_moves, pokemons, users
                RESTART IDENTITY CASCADE
            """)
        )

    yield


@pytest.fixture(autouse=True)
def isolated_limits_and_uploads(tmp_path, monkeypatch):
    import pokemon_routes
    limiter.reset()
    monkeypatch.setattr(pokemon_routes, "UPLOAD_DIR", tmp_path)
    yield
    limiter.reset()
