
"""safe add full_name to user and address to event (idempotent)

Revision ID: cae03aeba4e5
Revises: 2c131f530702
Create Date: 2025-08-12 08:40:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "cae03aeba4e5"
down_revision = "2c131f530702"
branch_labels = None
depends_on = None


def _has_table(bind, name: str) -> bool:
    insp = sa.inspect(bind)
    return insp.has_table(name)


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    if not insp.has_table(table):
        return False
    cols = {c["name"] for c in insp.get_columns(table)}
    return column in cols


def upgrade():
    bind = op.get_bind()

    # Add full_name to "user" table iff missing (quote reserved name)
    if _has_table(bind, "user") and not _has_column(bind, "user", "full_name"):
        op.add_column(
            "user",
            sa.Column("full_name", sa.String(length=256), nullable=False, server_default=""),
        )

    # Add address to "event" table iff missing
    if _has_table(bind, "event") and not _has_column(bind, "event", "address"):
        op.add_column(
            "event",
            sa.Column("address", sa.String(length=255), nullable=True),
        )


def downgrade():
    bind = op.get_bind()

    if _has_table(bind, "event") and _has_column(bind, "event", "address"):
        op.drop_column("event", "address")

    if _has_table(bind, "user") and _has_column(bind, "user", "full_name"):
        op.drop_column("user", "full_name")
