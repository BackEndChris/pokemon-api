"""initial schema

Revision ID: 83ddfa0aa6c1
Revises: 
Create Date: 2026-09-08 22:33:59.451550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83ddfa0aa6c1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
    )

    op.create_table(
        "pokemons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("hp", sa.Integer()),
        sa.Column("attack", sa.Integer()),
        sa.Column("defense", sa.Integer()),
        sa.Column("speed", sa.Integer()),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("image_url", sa.Text()),
    )

    op.create_table(
        "moves",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("power", sa.Integer(), nullable=False),
    )

    op.create_table(
        "pokemon_moves",
        sa.Column(
            "pokemon_id",
            sa.Integer(),
            sa.ForeignKey("pokemons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "move_id",
            sa.Integer(),
            sa.ForeignKey("moves.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("pokemon_id", "move_id"),
    )


def downgrade() -> None:
    op.drop_table("pokemon_moves")
    op.drop_table("moves")
    op.drop_table("pokemons")
    op.drop_table("users")
