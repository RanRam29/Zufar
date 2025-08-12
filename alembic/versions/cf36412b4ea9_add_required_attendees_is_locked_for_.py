"""add required_attendees & is_locked_for_registration to event (idempotent)

Revision ID: cf36412b4ea9
Revises: cae03aeba4e5
Create Date: 2025-08-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "cf36412b4ea9"
down_revision = "cae03aeba4e5"
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

    # ודא שהטבלה event קיימת (בלוקאל/SQLite ייתכן שהיא עדיין לא נוצרה בענף הזה)
    if not _has_table(bind, "event"):
        op.create_table(
            "event",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("address", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # הוסף required_attendees רק אם חסר
    if not _has_column(bind, "event", "required_attendees"):
        op.add_column(
            "event",
            sa.Column("required_attendees", sa.Integer(), nullable=False, server_default="1"),
        )

    # הוסף is_locked_for_registration רק אם חסר
    if not _has_column(bind, "event", "is_locked_for_registration"):
        # ב-SQLite Boolean = INTEGER (0/1); ב-Postgres זה boolean – שניהם יעבדו
        op.add_column(
            "event",
            sa.Column("is_locked_for_registration", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        )


def downgrade():
    bind = op.get_bind()

    if _has_table(bind, "event") and _has_column(bind, "event", "is_locked_for_registration"):
        op.drop_column("event", "is_locked_for_registration")

    if _has_table(bind, "event") and _has_column(bind, "event", "required_attendees"):
        op.drop_column("event", "required_attendees")
