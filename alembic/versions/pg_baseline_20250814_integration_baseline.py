"""PostgreSQL Baseline Integration (single migration, idempotent)

This migration consolidates schema into one file and is safe to run on an
existing PostgreSQL database. It creates/aligns the `user` and `event` tables
and enforces unique email. It will not error if objects already exist.

Notes:
- Designed for PostgreSQL. Uses NOW() and boolean defaults (true/false).
- Idempotent: checks existence before create/alter.

"""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "pg_baseline_20250814"
down_revision = None
branch_labels = None
depends_on = None


def _pg():
    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def _has_table(name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return insp.has_table(name)


def _col_names(table: str):
    insp = sa.inspect(op.get_bind())
    return {c["name"] for c in insp.get_columns(table)} if insp.has_table(table) else set()


def _unique_names(table: str):
    insp = sa.inspect(op.get_bind())
    return {uc.get("name") for uc in insp.get_unique_constraints(table)} if insp.has_table(table) else set()


def upgrade():
    assert _pg(), "This baseline is intended for PostgreSQL."

    # ---------------- USER TABLE ----------------
    if not _has_table("user"):
        op.create_table(
            "user",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=True),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_unique_constraint("uq_users_email", "user", ["email"])
    else:
        cols = _col_names("user")

        if "email" not in cols:
            op.add_column("user", sa.Column("email", sa.String(length=255), nullable=False))
        if "full_name" not in cols:
            op.add_column("user", sa.Column("full_name", sa.String(length=255), nullable=True))
        if "hashed_password" not in cols:
            op.add_column("user", sa.Column("hashed_password", sa.String(length=255), nullable=False))
        if "created_at" not in cols:
            op.add_column("user", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False))

        # Drop legacy index if present
        op.execute("""
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind='i' AND c.relname='ix_user_email'
          ) THEN
            DROP INDEX IF EXISTS ix_user_email;
          END IF;
        END $$;
        """)

        # Ensure unique(email)
        uqs = _unique_names("user")
        if "uq_users_email" not in uqs and "uq_user_email" not in uqs:
            BEGIN_TRY = True
            try:
                op.create_unique_constraint("uq_users_email", "user", ["email"])
            except Exception:
                op.create_unique_constraint("uq_user_email", "user", ["email"])

    # ---------------- EVENT TABLE ----------------
    if not _has_table("event"):
        op.create_table(
            "event",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("title", sa.String(length=255), nullable=False, server_default=sa.text("''")),
            sa.Column("date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("address", sa.String(length=255), nullable=True),
            sa.Column("required_attendees", sa.Integer(), nullable=False, server_default=sa.text("1")),
            sa.Column("is_locked_for_registration", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )
    else:
        ecols = _col_names("event")
        if "title" not in ecols:
            op.add_column("event", sa.Column("title", sa.String(length=255), nullable=False, server_default=sa.text("''")))
        if "date" not in ecols:
            op.add_column("event", sa.Column("date", sa.DateTime(timezone=True), nullable=True))
        if "address" not in ecols:
            op.add_column("event", sa.Column("address", sa.String(length=255), nullable=True))
        if "required_attendees" not in ecols:
            op.add_column("event", sa.Column("required_attendees", sa.Integer(), nullable=False, server_default=sa.text("1")))
        if "is_locked_for_registration" not in ecols:
            op.add_column("event", sa.Column("is_locked_for_registration", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        if "created_at" not in ecols:
            op.add_column("event", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False))


def downgrade():
    # Forward-only baseline
    pass
