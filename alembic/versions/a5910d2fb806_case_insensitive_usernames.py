"""Enforce case-insensitive username uniqueness without merging accounts.

Revision ID: a5910d2fb806
Revises: f48bd270a913
"""
from alembic import op
import sqlalchemy as sa

revision = "a5910d2fb806"
down_revision = "f48bd270a913"
branch_labels = None
depends_on = None


def upgrade():
    # Hold writes until the conflict check and unique index are both complete.
    op.execute("LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE")
    conflict = op.get_bind().execute(sa.text("""
        SELECT 1 FROM users GROUP BY lower(username) HAVING count(*) > 1 LIMIT 1
    """)).first()
    if conflict:
        raise RuntimeError(
            "Case-insensitive username conflicts exist. Resolve account names explicitly "
            "before retrying this migration; no accounts were deleted or merged."
        )
    op.create_index("users_username_lower_unique", "users", [sa.text("lower(username)")], unique=True)


def downgrade():
    op.drop_index("users_username_lower_unique", table_name="users")
