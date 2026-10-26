"""Add moves for all types and backfill missing starter moves.

Revision ID: e35ac9204f61
Revises: c724ab18d902
"""
from alembic import op
import sqlalchemy as sa


revision = "e35ac9204f61"
down_revision = "c724ab18d902"
branch_labels = None
depends_on = None


# Frozen catalogue so this migration does not depend on future application code.
MOVE_CATALOGUE = [
    ("Tackle", "Normal", 40, True),
    ("Headbutt", "Normal", 70, False),
    ("Body Slam", "Normal", 85, False),
    ("Ember", "Fire", 40, True),
    ("Flame Burst", "Fire", 70, False),
    ("Flamethrower", "Fire", 90, False),
    ("Water Gun", "Water", 40, True),
    ("Bubble Beam", "Water", 65, False),
    ("Surf", "Water", 90, False),
    ("Thunder Shock", "Electric", 40, True),
    ("Spark", "Electric", 65, False),
    ("Thunderbolt", "Electric", 90, False),
    ("Vine Whip", "Grass", 45, True),
    ("Razor Leaf", "Grass", 55, False),
    ("Energy Ball", "Grass", 90, False),
    ("Powder Snow", "Ice", 40, True),
    ("Aurora Beam", "Ice", 65, False),
    ("Ice Beam", "Ice", 90, False),
    ("Mach Punch", "Fighting", 40, True),
    ("Brick Break", "Fighting", 75, False),
    ("Close Combat", "Fighting", 120, False),
    ("Poison Sting", "Poison", 15, True),
    ("Venoshock", "Poison", 65, False),
    ("Sludge Bomb", "Poison", 90, False),
    ("Mud-Slap", "Ground", 20, True),
    ("Bulldoze", "Ground", 60, False),
    ("Earthquake", "Ground", 100, False),
    ("Gust", "Flying", 40, True),
    ("Wing Attack", "Flying", 60, False),
    ("Air Slash", "Flying", 75, False),
    ("Confusion", "Psychic", 50, True),
    ("Psybeam", "Psychic", 65, False),
    ("Psychic", "Psychic", 90, False),
    ("Struggle Bug", "Bug", 50, True),
    ("Bug Bite", "Bug", 60, False),
    ("Bug Buzz", "Bug", 90, False),
    ("Rock Throw", "Rock", 50, True),
    ("Rock Tomb", "Rock", 60, False),
    ("Rock Slide", "Rock", 75, False),
    ("Lick", "Ghost", 30, True),
    ("Hex", "Ghost", 65, False),
    ("Shadow Ball", "Ghost", 80, False),
    ("Twister", "Dragon", 40, True),
    ("Dragon Breath", "Dragon", 60, False),
    ("Dragon Pulse", "Dragon", 85, False),
    ("Bite", "Dark", 60, True),
    ("Night Slash", "Dark", 70, False),
    ("Dark Pulse", "Dark", 80, False),
    ("Metal Claw", "Steel", 50, True),
    ("Mirror Shot", "Steel", 65, False),
    ("Flash Cannon", "Steel", 80, False),
    ("Fairy Wind", "Fairy", 40, True),
    ("Draining Kiss", "Fairy", 50, False),
    ("Moonblast", "Fairy", 95, False),
]

# These six records existed before this migration.
ORIGINAL_MOVES = {"Ember", "Flame Burst", "Water Gun", "Bubble Beam", "Vine Whip", "Razor Leaf"}


def upgrade() -> None:
    connection = op.get_bind()
    for name, pokemon_type, power, starter in MOVE_CATALOGUE:
        connection.execute(sa.text("""
            INSERT INTO moves (name, type, power)
            SELECT :name, :type, :power
            WHERE NOT EXISTS (SELECT 1 FROM moves WHERE name = :name)
        """), {"name": name, "type": pokemon_type, "power": power})
        if starter:
            connection.execute(sa.text("""
                INSERT INTO pokemon_moves (pokemon_id, move_id)
                SELECT pokemons.id, moves.id
                FROM pokemons JOIN moves ON moves.name = :name
                WHERE pokemons.type = :type
                ON CONFLICT (pokemon_id, move_id) DO NOTHING
            """), {"name": name, "type": pokemon_type})


def downgrade() -> None:
    connection = op.get_bind()
    for name, _, _, _ in MOVE_CATALOGUE:
        if name in ORIGINAL_MOVES:
            continue
        connection.execute(sa.text("""
            DELETE FROM pokemon_moves
            WHERE move_id IN (SELECT id FROM moves WHERE name = :name)
        """), {"name": name})
        connection.execute(sa.text("DELETE FROM moves WHERE name = :name"), {"name": name})
