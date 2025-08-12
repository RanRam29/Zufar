"""Add full_name and created_at to user (safe, idempotent)

Revision ID: 4f6d2a1b7ac9
Revises: cf36412b4ea9
Create Date: 2025-08-12 08:17:12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "4f6d2a1b7ac9"
down_revision = "cf36412b4ea9"
branch_labels = None
depends_on = None

def _has_table(conn, table_name: str) -> bool:
    insp = sa.inspect(conn)
    return insp.has_table(table_name)

def _has_column(conn, table_name: str, column_name: str) -> bool:
    insp = sa.inspect(conn)
    if not insp.has_table(table_name):
        return False
    cols = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in cols

def upgrade() -> None:
    conn = op.get_bind()
    if _has_table(conn, "user") and not _has_column(conn, "user", "full_name"):
        op.add_column("user", sa.Column("full_name", sa.String(length=256), nullable=True))
        # backfill existing rows to avoid nulls
        op.execute('UPDATE "user" SET full_name = email WHERE full_name IS NULL')
        op.alter_column("user", "full_name", nullable=False)

    if _has_table(conn, "user") and not _has_column(conn, "user", "created_at"):
        # use Postgres-friendly server default
        op.add_column("user", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))

def downgrade() -> None:
    conn = op.get_bind()
    if _has_table(conn, "user") and _has_column(conn, "user", "created_at"):
        op.drop_column("user", "created_at")
    if _has_table(conn, "user") and _has_column(conn, "user", "full_name"):
        op.drop_column("user", "full_name")
