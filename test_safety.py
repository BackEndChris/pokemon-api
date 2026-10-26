"""Explicit test configuration and guards for destructive database fixtures."""
from pathlib import Path
import re

from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from sqlalchemy import text
from sqlalchemy.exc import ArgumentError


ROOT = Path(__file__).resolve().parent


def read_test_config(path=ROOT / ".env.test", normal_path=ROOT / ".env"):
    if not Path(path).is_file():
        raise RuntimeError("Testing requires an explicit .env.test file")
    values = dotenv_values(path, interpolate=False)
    if any(not values.get(key) or not values[key].strip() for key in ("DATABASE_URL", "SECRET_KEY")):
        raise RuntimeError(".env.test must explicitly set DATABASE_URL and SECRET_KEY")
    try:
        url = make_url(values["DATABASE_URL"])
        if url.get_backend_name() != "postgresql" or not re.fullmatch(r"[a-zA-Z0-9_]+_test", url.database or ""):
            raise ValueError()
        normal = dotenv_values(normal_path, interpolate=False).get("DATABASE_URL")
        if normal and make_url(normal).database == url.database:
            raise ValueError()
    except (ValueError, TypeError, ArgumentError):
        raise RuntimeError("Test database must be PostgreSQL, end in _test, and differ from the application database") from None
    return values


def guard_test_connection(connection, expected_url):
    expected = make_url(expected_url)
    if connection.engine.url != expected or not (expected.database or "").endswith("_test"):
        raise RuntimeError("Refusing destructive operations on an unapproved database connection")
    if connection.execute(text("SELECT current_database()")).scalar_one() != expected.database:
        raise RuntimeError("Connected database does not match the approved test database")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Verify the dedicated test database before use")
    parser.add_argument("--migrate", action="store_true", help="Apply Alembic migrations only after safety verification")
    arguments = parser.parse_args()
    values = read_test_config()
    os.environ.update({key: value for key, value in values.items() if value is not None})
    from database import engine

    with engine.connect() as connection:
        guard_test_connection(connection, values["DATABASE_URL"])
    print("Verified explicit configuration and dedicated test database identity.")
    if arguments.migrate:
        from alembic import command
        from alembic.config import Config

        command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
