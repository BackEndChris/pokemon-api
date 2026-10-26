"""Fail early with configuration errors that never print secret values."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


load_dotenv(Path(__file__).resolve().parent / ".env")


def required(name):
    value = os.getenv(name)
    if not value or not value.strip():
        raise RuntimeError(f"{name} must be configured")
    return value


def positive_int(name, default):
    try:
        value = int(os.getenv(name, str(default)))
        if value <= 0:
            raise ValueError()
        return value
    except ValueError:
        raise RuntimeError(f"{name} must be a positive integer") from None


SECRET_KEY = required("SECRET_KEY")
DATABASE_URL = required("DATABASE_URL")
try:
    database_url = make_url(DATABASE_URL)
    if database_url.get_backend_name() != "postgresql" or not database_url.database:
        raise ValueError()
except (ValueError, TypeError, ArgumentError):
    raise RuntimeError("DATABASE_URL must be a valid PostgreSQL database URL") from None

MAX_UPLOAD_BYTES = positive_int("MAX_UPLOAD_BYTES", 5 * 1024 * 1024)
MAX_IMAGE_PIXELS = positive_int("MAX_IMAGE_PIXELS", 20_000_000)
REGISTER_LIMIT = positive_int("REGISTER_LIMIT", 5)
LOGIN_SOURCE_LIMIT = positive_int("LOGIN_SOURCE_LIMIT", 30)
LOGIN_ACCOUNT_LIMIT = positive_int("LOGIN_ACCOUNT_LIMIT", 10)
UPLOAD_LIMIT = positive_int("UPLOAD_LIMIT", 10)
RATE_WINDOW_SECONDS = positive_int("RATE_WINDOW_SECONDS", 60)
