"""PostgreSQL Baseline Integration (single migration, idempotent, plural + compat views)

- Normalizes physical tables to plural: users, events.
- Guarantees required columns on users; UC on users.email.
- Provides compatibility views "user" and "event" with updatable RULES so code that uses
  singular names continues to work transparently.
- PostgreSQL only.

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

    # ---------- Normalize physical table names to plural ----------
    if _has_table("user") and not _has_table("users"):
        op.execute('ALTER TABLE public."user" RENAME TO users')
    if _has_table("event") and not _has_table("events"):
        op.execute('ALTER TABLE public."event" RENAME TO events')

    # ---------- USERS (physical table) ----------
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
            op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=False, server_default=sa.text("''")))
            op.alter_column("users", "hashed_password", server_default=None)
        if "created_at" not in ucols:
            op.add_column("users", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))

        # Drop legacy single-table index if exists
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
            BEGIN_TRY = True  # noqa: F841
            try:
                op.create_unique_constraint("uq_users_email", "users", ["email"])
            except Exception:
                op.create_unique_constraint("uq_user_email", "users", ["email"])

    # ---------- EVENTS (physical table) ----------
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

    # ---------- Compatibility views (singular names) ----------
    # Create VIEW "user" -> users (only if there is no conflicting TABLE named "user")
    op.execute("""
    DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='user'
      ) THEN
        IF NOT EXISTS (
          SELECT 1
          FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
          WHERE c.relkind='v' AND c.relname='user'
        ) THEN
          EXECUTE 'CREATE VIEW public."user" AS SELECT id, email, full_name, hashed_password, created_at FROM public.users';
        END IF;

        -- Updatable rules to route writes to the base table
        EXECUTE 'CREATE OR REPLACE RULE user_insert AS ON INSERT TO public."user"
                 DO INSTEAD INSERT INTO public.users(email, full_name, hashed_password, created_at)
                 VALUES (NEW.email, NEW.full_name, NEW.hashed_password, COALESCE(NEW.created_at, NOW()))
                 RETURNING *';

        EXECUTE 'CREATE OR REPLACE RULE user_update AS ON UPDATE TO public."user"
                 DO INSTEAD UPDATE public.users
                 SET email = NEW.email,
                     full_name = NEW.full_name,
                     hashed_password = NEW.hashed_password,
                     created_at = COALESCE(NEW.created_at, users.created_at)
                 WHERE users.id = OLD.id
                 RETURNING *';

        EXECUTE 'CREATE OR REPLACE RULE user_delete AS ON DELETE TO public."user"
                 DO INSTEAD DELETE FROM public.users WHERE users.id = OLD.id RETURNING *';
      END IF;
    END $$;
    """)

    # Create VIEW event -> events
    op.execute("""
    DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='event'
      ) THEN
        IF NOT EXISTS (
          SELECT 1
          FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
          WHERE c.relkind='v' AND c.relname='event'
        ) THEN
          EXECUTE 'CREATE VIEW public."event" AS
                   SELECT id, title, description, address, country_code, lat, lng,
                          start_time, end_time, required_attendees,
                          is_locked_for_edit, is_locked_for_registration, created_at
                   FROM public.events';
        END IF;

        EXECUTE 'CREATE OR REPLACE RULE event_insert AS ON INSERT TO public."event"
                 DO INSTEAD INSERT INTO public.events
                 (title, description, address, country_code, lat, lng, start_time, end_time,
                  required_attendees, is_locked_for_edit, is_locked_for_registration, created_at)
                 VALUES (COALESCE(NEW.title, ''''),
                         COALESCE(NEW.description, ''''),
                         COALESCE(NEW.address, ''''),
                         COALESCE(NEW.country_code, ''''),
                         COALESCE(NEW.lat, 0),
                         COALESCE(NEW.lng, 0),
                         COALESCE(NEW.start_time, NOW()),
                         COALESCE(NEW.end_time, NOW()),
                         COALESCE(NEW.required_attendees, 1),
                         COALESCE(NEW.is_locked_for_edit, false),
                         COALESCE(NEW.is_locked_for_registration, false),
                         COALESCE(NEW.created_at, NOW()))
                 RETURNING *';

        EXECUTE 'CREATE OR REPLACE RULE event_update AS ON UPDATE TO public."event"
                 DO INSTEAD UPDATE public.events
                 SET title = COALESCE(NEW.title, events.title),
                     description = COALESCE(NEW.description, events.description),
                     address = COALESCE(NEW.address, events.address),
                     country_code = COALESCE(NEW.country_code, events.country_code),
                     lat = COALESCE(NEW.lat, events.lat),
                     lng = COALESCE(NEW.lng, events.lng),
                     start_time = COALESCE(NEW.start_time, events.start_time),
                     end_time = COALESCE(NEW.end_time, events.end_time),
                     required_attendees = COALESCE(NEW.required_attendees, events.required_attendees),
                     is_locked_for_edit = COALESCE(NEW.is_locked_for_edit, events.is_locked_for_edit),
                     is_locked_for_registration = COALESCE(NEW.is_locked_for_registration, events.is_locked_for_registration),
                     created_at = COALESCE(NEW.created_at, events.created_at)
                 WHERE events.id = OLD.id
                 RETURNING *';

        EXECUTE 'CREATE OR REPLACE RULE event_delete AS ON DELETE TO public."event"
                 DO INSTEAD DELETE FROM public.events WHERE events.id = OLD.id RETURNING *';
      END IF;
    END $$;
    """)


def downgrade():
    # Forward-only baseline
    pass
