"""Add special attack and special defense.

Revision ID: c724ab18d902
Revises: 83ddfa0aa6c1
"""
from alembic import op
import sqlalchemy as sa


revision = "c724ab18d902"
down_revision = "83ddfa0aa6c1"
branch_labels = None
depends_on = None


# Keep migration values independent of future changes to stats.py.
SPECIAL_BASES = {
    "Normal": (50, 55), "Fire": (80, 55), "Water": (65, 65),
    "Electric": (80, 50), "Grass": (70, 65), "Ice": (80, 65),
    "Fighting": (40, 50), "Poison": (65, 65), "Ground": (45, 50),
    "Flying": (55, 55), "Psychic": (75, 80), "Bug": (45, 50),
    "Rock": (40, 50), "Ghost": (80, 70), "Dragon": (70, 55),
    "Dark": (60, 50), "Steel": (40, 80), "Fairy": (75, 75),
}


def upgrade() -> None:
    op.add_column("pokemons", sa.Column("special_attack", sa.Integer(), nullable=True))
    op.add_column("pokemons", sa.Column("special_defense", sa.Integer(), nullable=True))

    pokemons = sa.table(
        "pokemons",
        sa.column("type", sa.Text()),
        sa.column("level", sa.Integer()),
        sa.column("special_attack", sa.Integer()),
        sa.column("special_defense", sa.Integer()),
    )
    op.execute(
        pokemons.update().values(
            special_attack=sa.case(
                {name: values[0] for name, values in SPECIAL_BASES.items()},
                value=pokemons.c.type,
                else_=60,
            ) + pokemons.c.level * 2,
            special_defense=sa.case(
                {name: values[1] for name, values in SPECIAL_BASES.items()},
                value=pokemons.c.type,
                else_=60,
            ) + pokemons.c.level * 2,
        )
    )
    op.alter_column("pokemons", "special_attack", nullable=False)
    op.alter_column("pokemons", "special_defense", nullable=False)


def downgrade() -> None:
    op.drop_column("pokemons", "special_defense")
    op.drop_column("pokemons", "special_attack")
