"""safe add full_name to user and address to event

Revision ID: XXXX_safe_add_cols
Revises: 2c131f530702
Create Date: 2025-08-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# מזהים של Alembic
revision = 'XXXX_safe_add_cols'
down_revision = '2c131f530702'
branch_labels = None
depends_on = None


def _has_table(bind, table_name: str) -> bool:
    insp = sa.inspect(bind)
    return table_name in insp.get_table_names()


def _has_column(bind, table_name: str, column_name: str) -> bool:
    insp = sa.inspect(bind)
    try:
        cols = [c["name"] for c in insp.get_columns(table_name)]
    except Exception:
        return False
    return column_name in cols


def upgrade():
    bind = op.get_bind()

    # user.full_name
    if _has_table(bind, "user") and not _has_column(bind, "user", "full_name"):
        op.add_column(
            "user",
            sa.Column("full_name", sa.String(length=200), nullable=True),
        )

    # event.address
    if _has_table(bind, "event") and not _has_column(bind, "event", "address"):
        op.add_column(
            "event",
            sa.Column("address", sa.String(length=300), nullable=True),
        )


def downgrade():
    bind = op.get_bind()

    # הורדה בטוחה – רק אם קיים
    if _has_table(bind, "event") and _has_column(bind, "event", "address"):
        op.drop_column("event", "address")

    if _has_table(bind, "user") and _has_column(bind, "user", "full_name"):
        op.drop_column("user", "full_name")
