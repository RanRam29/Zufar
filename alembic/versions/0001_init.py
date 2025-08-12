"""initial schema: user, event, participant (idempotent)

Revision ID: 0001_init
Revises:
Create Date: 2025-08-12 08:30:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(bind, name: str) -> bool:
    insp = sa.inspect(bind)
    return insp.has_table(name)


def upgrade():
    bind = op.get_bind()

    # --- USER (singular) ---
    if not _has_table(bind, "user"):
        op.create_table(
            "user",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=256), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_user_email", "user", ["email"], unique=True)

    # --- EVENT ---
    if not _has_table(bind, "event"):
        op.create_table(
            "event",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("title", sa.String(length=200), nullable=False, server_default=""),
            sa.Column("description", sa.String(length=2000), nullable=False, server_default=""),
            sa.Column("address", sa.String(length=300), nullable=False, server_default=""),
            sa.Column("country_code", sa.String(length=2), nullable=False, server_default="IL"),
            sa.Column("lat", sa.Float, nullable=False, server_default="0"),
            sa.Column("lng", sa.Float, nullable=False, server_default="0"),
            sa.Column("start_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("end_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("required_attendees", sa.Integer, nullable=False, server_default="1"),
            sa.Column("is_locked_for_edit", sa.Boolean, nullable=False, server_default=sa.text("false")),
        )

    # --- PARTICIPANT ---
    if not _has_table(bind, "participant"):
        op.create_table(
            "participant",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, nullable=False),
            sa.Column("event_id", sa.Integer, nullable=False),
            sa.Column("status", sa.String(length=50), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_participant_user_id", "participant", ["user_id"], unique=False)
        op.create_index("ix_participant_event_id", "participant", ["event_id"], unique=False)


def downgrade():
    # No destructive drops to avoid data loss.
    pass
