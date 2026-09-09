import os
from dotenv import load_dotenv

load_dotenv(".env.test", override=True)

import pytest
from sqlalchemy import text

from database import engine


@pytest.fixture(autouse=True)
def clean_database():
    with engine.begin() as connection:
        connection.execute(
            text("""
                TRUNCATE TABLE pokemon_moves, pokemons, users
                RESTART IDENTITY CASCADE
            """)
        )

    yield