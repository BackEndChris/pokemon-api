import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text

from database import engine
from moves import TYPE_MOVES


def test_special_stats_migration_backfills_existing_pokemon():
    path = Path(__file__).resolve().parents[1] / "alembic/versions/c724ab18d902_add_special_stats.py"
    spec = importlib.util.spec_from_file_location("special_stats_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            # A temporary table shadows the real table on this connection only.
            connection.execute(text("""
                CREATE TEMPORARY TABLE pokemons (
                    type TEXT, level INTEGER, hp INTEGER
                ) ON COMMIT DROP
            """))
            connection.execute(text("""
                INSERT INTO pokemons (type, level, hp)
                VALUES ('Fire', 20, 105), ('Water', 1, 58), ('Grass', 10, 90)
            """))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                rows = connection.execute(text("""
                    SELECT type, hp, special_attack, special_defense
                    FROM pokemons ORDER BY type
                """)).fetchall()
                assert [tuple(row) for row in rows] == [
                    ("Fire", 105, 120, 95),
                    ("Grass", 90, 90, 85),
                    ("Water", 58, 67, 67),
                ]
                assert connection.execute(text("""
                    SELECT count(*) FROM pg_attribute
                    WHERE attrelid = 'pg_temp.pokemons'::regclass
                    AND attname IN ('special_attack', 'special_defense')
                    AND attnotnull
                """)).scalar_one() == 2

                migration.downgrade()
                assert connection.execute(text("SELECT hp FROM pokemons ORDER BY type")).scalars().all() == [105, 90, 58]
        finally:
            transaction.rollback()


def test_move_migration_seeds_catalogue_and_preserves_existing_assignments():
    path = Path(__file__).resolve().parents[1] / "alembic/versions/e35ac9204f61_add_type_moves.py"
    spec = importlib.util.spec_from_file_location("type_moves_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("""
                CREATE TEMPORARY TABLE pokemons (id INTEGER PRIMARY KEY, type TEXT)
                ON COMMIT DROP
            """))
            connection.execute(text("""
                CREATE TEMPORARY TABLE moves (
                    id SERIAL PRIMARY KEY, name TEXT, type TEXT, power INTEGER
                ) ON COMMIT DROP
            """))
            connection.execute(text("""
                CREATE TEMPORARY TABLE pokemon_moves (
                    pokemon_id INTEGER REFERENCES pokemons(id),
                    move_id INTEGER REFERENCES moves(id),
                    PRIMARY KEY (pokemon_id, move_id)
                ) ON COMMIT DROP
            """))
            connection.execute(text("INSERT INTO pokemons VALUES (1, 'Fire'), (2, 'Psychic')"))
            connection.execute(text("""
                INSERT INTO moves (name, type, power)
                VALUES ('Ember', 'Fire', 41), ('Flame Burst', 'Fire', 70)
            """))
            connection.execute(text("""
                INSERT INTO pokemon_moves
                SELECT 1, id FROM moves WHERE name = 'Flame Burst'
            """))

            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                migration.upgrade()  # Repeated seeding must not duplicate records.
                rows = connection.execute(text("SELECT name, type, power FROM moves")).fetchall()
                expected = {
                    (move["name"], pokemon_type, 41 if move["name"] == "Ember" else move["power"])
                    for pokemon_type, moves in TYPE_MOVES.items() for move in moves[:3]
                }
                assert len(rows) == 54
                assert {tuple(row) for row in rows} == expected
                learned = connection.execute(text("""
                    SELECT pokemon_id, name FROM pokemon_moves
                    JOIN moves ON moves.id = pokemon_moves.move_id
                    ORDER BY pokemon_id, name
                """)).fetchall()
                assert [tuple(row) for row in learned] == [
                    (1, "Ember"), (1, "Flame Burst"), (2, "Confusion")
                ]

                expansion_path = path.with_name("f48bd270a913_expand_type_moves.py")
                expansion_spec = importlib.util.spec_from_file_location("expanded_moves_migration", expansion_path)
                expansion = importlib.util.module_from_spec(expansion_spec)
                expansion_spec.loader.exec_module(expansion)
                expansion.upgrade()
                expansion.upgrade()
                expanded = connection.execute(text("SELECT name, type, power FROM moves")).fetchall()
                expected = {
                    (move["name"], pokemon_type, 41 if move["name"] == "Ember" else move["power"])
                    for pokemon_type, moves in TYPE_MOVES.items() for move in moves
                }
                assert len(expanded) == 144
                assert {tuple(row) for row in expanded} == expected
                assert connection.execute(text("SELECT count(*) FROM pokemon_moves")).scalar_one() == 3
                connection.execute(text("""
                    INSERT INTO pokemon_moves SELECT 1, id FROM moves WHERE name = 'Quick Attack'
                """))
                expansion.downgrade()
                assert connection.execute(text("SELECT count(*) FROM moves")).scalar_one() == 54
                assert connection.execute(text("SELECT count(*) FROM pokemon_moves")).scalar_one() == 3

                migration.downgrade()
                assert set(connection.execute(text("SELECT name FROM moves")).scalars()) == migration.ORIGINAL_MOVES
        finally:
            transaction.rollback()
