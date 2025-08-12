"""safe add full_name to user and address to event

Revision ID: cae03aeba4e5
Revises: 2c131f530702
Create Date: 2025-08-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# Alembic identifiers
revision = "cae03aeba4e5"
down_revision = "2c131f530702"
branch_labels = None
depends_on = None


def upgrade():
    # user.full_name (לא רצה לשבור רשומות קיימות -> מוסיפים עם ברירת מחדל ריקה ואז מסירים ברירת מחדל)
    op.add_column(
        "user",
        sa.Column("full_name", sa.String(length=256), nullable=False, server_default="")
    )
    op.alter_column("user", "full_name", server_default=None)

    # event.address (אותו הטריק)
    op.add_column(
        "event",
        sa.Column("address", sa.String(length=300), nullable=False, server_default="")
    )
    op.alter_column("event", "address", server_default=None)


def downgrade():
    op.drop_column("event", "address")
    op.drop_column("user", "full_name")
