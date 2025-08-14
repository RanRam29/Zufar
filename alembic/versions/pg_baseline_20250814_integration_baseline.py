"""PostgreSQL Baseline Integration (single migration, idempotent, pluralized)

Consolidates schema into one safe migration.
- Normalizes table names to plural: "user"->users, "event"->events
- USERS: ensures email/full_name/hashed_password/created_at + UNIQUE(email)
- EVENTS: ensures core columns; adds missing ones safely
- PostgreSQL-only; uses NOW() and boolean defaults

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

    # ---------- Normalize table names to plural ----------
    if _has_table("user") and not _has_table("users"):
        op.execute('ALTER TABLE "user" RENAME TO users')
    if _has_table("event") and not _has_table("events"):
        op.execute("ALTER TABLE event RENAME TO events")

    # ---------- USERS TABLE ----------
    if not _has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=True),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_unique_constraint("uq_users_email", "users", ["email"])
    else:
        ucols = _col_names("users")

        if "email" not in ucols:
            op.add_column("users", sa.Column("email", sa.String(length=255), nullable=False))
        if "full_name" not in ucols:
            op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
        if "hashed_password" not in ucols:
            # add NOT NULL with temporary default to satisfy existing rows
            op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=False, server_default=sa.text("''")))
            op.alter_column("users", "hashed_password", server_default=None)
        if "created_at" not in ucols:
            op.add_column("users", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))

        # Drop legacy single-table index name if it exists (harmless if missing)
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
        uqs = _unique_names("users")
        if "uq_users_email" not in uqs and "uq_user_email" not in uqs:
            BEGIN_TRY = True  # noqa: F841 (just to hint try-block intent)
            try:
                op.create_unique_constraint("uq_users_email", "users", ["email"])
            except Exception:
                op.create_unique_constraint("uq_user_email", "users", ["email"])

    # ---------- EVENTS TABLE ----------
    # We support a richer schema (title/description/address/country_code/lat/lng/start_time/end_time/required_attendees/is_locked_for_edit/is_locked_for_registration/created_at).
    if not _has_table("events"):
        op.create_table(
            "events",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("title", sa.String(length=255), nullable=False, server_default=sa.text("''")),
            sa.Column("description", sa.String(length=255), nullable=False, server_default=sa.text("''")),
            sa.Column("address", sa.String(length=255), nullable=False, server_default=sa.text("''")),
            sa.Column("country_code", sa.String(length=8), nullable=False, server_default=sa.text("''")),
            sa.Column("lat", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("lng", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("start_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("end_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("required_attendees", sa.Integer(), nullable=False, server_default=sa.text("1")),
            sa.Column("is_locked_for_edit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_locked_for_registration", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )
    else:
        ecols = _col_names("events")

        def _add_col_if_missing(name, col):
            if name not in ecols:
                op.add_column("events", col)

        _add_col_if_missing("title", sa.Column("title", sa.String(length=255), nullable=False, server_default=sa.text("''")))
        _add_col_if_missing("description", sa.Column("description", sa.String(length=255), nullable=False, server_default=sa.text("''")))
        _add_col_if_missing("address", sa.Column("address", sa.String(length=255), nullable=False, server_default=sa.text("''")))
        _add_col_if_missing("country_code", sa.Column("country_code", sa.String(length=8), nullable=False, server_default=sa.text("''")))
        _add_col_if_missing("lat", sa.Column("lat", sa.Float(), nullable=False, server_default=sa.text("0")))
        _add_col_if_missing("lng", sa.Column("lng", sa.Float(), nullable=False, server_default=sa.text("0")))
        _add_col_if_missing("start_time", sa.Column("start_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))
        _add_col_if_missing("end_time", sa.Column("end_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))
        _add_col_if_missing("required_attendees", sa.Column("required_attendees", sa.Integer(), nullable=False, server_default=sa.text("1")))
        _add_col_if_missing("is_locked_for_edit", sa.Column("is_locked_for_edit", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_col_if_missing("is_locked_for_registration", sa.Column("is_locked_for_registration", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_col_if_missing("created_at", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))


def downgrade():
    # Forward-only baseline
    pass
