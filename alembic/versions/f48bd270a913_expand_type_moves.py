"""Expand each type's move pool by five moves.

Revision ID: f48bd270a913
Revises: e35ac9204f61
"""
from alembic import op
import sqlalchemy as sa


revision = "f48bd270a913"
down_revision = "e35ac9204f61"
branch_labels = None
depends_on = None


# Frozen data: migrations must not import the application's changing catalogue.
NEW_MOVES = [
    ("Quick Attack", "Normal", 40),
    ("Swift", "Normal", 60),
    ("Slash", "Normal", 70),
    ("Hyper Voice", "Normal", 90),
    ("Hyper Beam", "Normal", 150),
    ("Incinerate", "Fire", 60),
    ("Fire Fang", "Fire", 65),
    ("Fire Punch", "Fire", 75),
    ("Heat Wave", "Fire", 95),
    ("Fire Blast", "Fire", 110),
    ("Aqua Jet", "Water", 40),
    ("Water Pulse", "Water", 60),
    ("Aqua Tail", "Water", 90),
    ("Liquidation", "Water", 85),
    ("Hydro Pump", "Water", 110),
    ("Nuzzle", "Electric", 20),
    ("Shock Wave", "Electric", 60),
    ("Thunder Punch", "Electric", 75),
    ("Discharge", "Electric", 80),
    ("Thunder", "Electric", 110),
    ("Absorb", "Grass", 20),
    ("Mega Drain", "Grass", 40),
    ("Giga Drain", "Grass", 75),
    ("Leaf Blade", "Grass", 90),
    ("Solar Beam", "Grass", 120),
    ("Ice Shard", "Ice", 40),
    ("Icy Wind", "Ice", 55),
    ("Ice Fang", "Ice", 65),
    ("Ice Punch", "Ice", 75),
    ("Blizzard", "Ice", 110),
    ("Low Sweep", "Fighting", 65),
    ("Force Palm", "Fighting", 60),
    ("Drain Punch", "Fighting", 75),
    ("Aura Sphere", "Fighting", 80),
    ("Focus Blast", "Fighting", 120),
    ("Smog", "Poison", 30),
    ("Acid", "Poison", 40),
    ("Poison Fang", "Poison", 50),
    ("Poison Jab", "Poison", 80),
    ("Gunk Shot", "Poison", 120),
    ("Mud Shot", "Ground", 55),
    ("Bone Club", "Ground", 65),
    ("Dig", "Ground", 80),
    ("Drill Run", "Ground", 80),
    ("Earth Power", "Ground", 90),
    ("Peck", "Flying", 35),
    ("Aerial Ace", "Flying", 60),
    ("Pluck", "Flying", 60),
    ("Drill Peck", "Flying", 80),
    ("Hurricane", "Flying", 110),
    ("Stored Power", "Psychic", 20),
    ("Psyshock", "Psychic", 80),
    ("Zen Headbutt", "Psychic", 80),
    ("Extrasensory", "Psychic", 80),
    ("Future Sight", "Psychic", 120),
    ("Fury Cutter", "Bug", 40),
    ("Pin Missile", "Bug", 25),
    ("Silver Wind", "Bug", 60),
    ("X-Scissor", "Bug", 80),
    ("Megahorn", "Bug", 120),
    ("Rollout", "Rock", 30),
    ("Rock Blast", "Rock", 25),
    ("Ancient Power", "Rock", 60),
    ("Power Gem", "Rock", 80),
    ("Stone Edge", "Rock", 100),
    ("Astonish", "Ghost", 30),
    ("Shadow Sneak", "Ghost", 40),
    ("Shadow Punch", "Ghost", 60),
    ("Ominous Wind", "Ghost", 60),
    ("Phantom Force", "Ghost", 90),
    ("Dragon Tail", "Dragon", 60),
    ("Dragon Claw", "Dragon", 80),
    ("Dragon Rush", "Dragon", 100),
    ("Outrage", "Dragon", 120),
    ("Draco Meteor", "Dragon", 130),
    ("Assurance", "Dark", 60),
    ("Feint Attack", "Dark", 60),
    ("Knock Off", "Dark", 65),
    ("Crunch", "Dark", 80),
    ("Foul Play", "Dark", 95),
    ("Bullet Punch", "Steel", 40),
    ("Smart Strike", "Steel", 70),
    ("Steel Wing", "Steel", 70),
    ("Iron Head", "Steel", 80),
    ("Iron Tail", "Steel", 100),
    ("Disarming Voice", "Fairy", 40),
    ("Dazzling Gleam", "Fairy", 80),
    ("Spirit Break", "Fairy", 75),
    ("Play Rough", "Fairy", 90),
    ("Alluring Voice", "Fairy", 80),
]


def upgrade() -> None:
    connection = op.get_bind()
    for name, pokemon_type, power in NEW_MOVES:
        connection.execute(sa.text("""
            INSERT INTO moves (name, type, power)
            SELECT :name, :type, :power
            WHERE NOT EXISTS (SELECT 1 FROM moves WHERE name = :name)
        """), {"name": name, "type": pokemon_type, "power": power})


def downgrade() -> None:
    connection = op.get_bind()
    for name, _, _ in NEW_MOVES:
        connection.execute(sa.text("""
            DELETE FROM pokemon_moves
            WHERE move_id IN (SELECT id FROM moves WHERE name = :name)
        """), {"name": name})
        connection.execute(sa.text("DELETE FROM moves WHERE name = :name"), {"name": name})
