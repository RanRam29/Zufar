"""align user table schema (hashed_password, types, unique email)

Revision ID: a1d8_user_align_20250814
Revises: mrg_20250812_single_head
Create Date: 2025-08-14

- Adds column: hashed_password (String(255), NOT NULL)
- Drops column: password_hash (legacy)
- Shrinks varchar length to 255 for email/full_name
- Makes full_name nullable
- Ensures unique(email) via uq_users_email
- (Optional) re-creates ix_user_id if models define index=True on id
"""

from alembic import op
import sqlalchemy as sa

# --- identifiers ---
revision = 'a1d8_user_align_20250814'
down_revision = 'mrg_20250812_single_head'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # batch_alter_table מאפשר תאימות גם ל-SQLite (יבנה טבלה זמנית ויעתיק נתונים)
    with op.batch_alter_table('user', schema=None) as batch:
        # הוספת hashed_password אם לא קיים
        batch.add_column(sa.Column('hashed_password', sa.String(length=255), nullable=False))

        # מחיקת password_hash אם קיים (שם ישן)
        # (אם לא קיים – Alembic יתפוס חריגה; לכן נעשה try/except רך ע"י DDL ישיר בהמשך, אבל batch.drop_column מספיק לרוב)
        try:
            batch.drop_column('password_hash')
        except Exception:
            pass

        # שינוי סוגים/nullable
        batch.alter_column(
            'email',
            existing_type=sa.VARCHAR(length=256),
            type_=sa.String(length=255),
            existing_nullable=False
        )
        batch.alter_column(
            'full_name',
            existing_type=sa.VARCHAR(length=256),
            type_=sa.String(length=255),
            existing_nullable=True,   # לאפשר NULL
            nullable=True
        )

        # unique(email) – שם איגון מותאם למודל (__table_args__)
        # אם כבר קיים unique דומה – הקריאה תיכשל; לכן ננסה להסיר קודם, ואז ליצור.
        try:
            batch.drop_constraint('ix_user_email', type_='unique')
        except Exception:
            pass
        try:
            batch.create_unique_constraint('uq_users_email', ['email'])
        except Exception:
            pass

        # אינדקס על id (אם במודל יש index=True בנוסף ל-PK)
        try:
            batch.create_index('ix_user_id', ['id'], unique=False)
        except Exception:
            pass


def downgrade() -> None:
    # פעולה הפוכה – השאר רק אם באמת תצטרך רוורס (בפרוד לרוב לא משתמשים ב-downgrade)
    with op.batch_alter_table('user', schema=None) as batch:
        try:
            batch.drop_index('ix_user_id')
        except Exception:
            pass
        try:
            batch.drop_constraint('uq_users_email', type_='unique')
        except Exception:
            pass

        batch.alter_column(
            'full_name',
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=256),
            existing_nullable=True,
        )
        batch.alter_column(
            'email',
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=256),
            existing_nullable=False
        )

        # החזרת העמודה הישנה אם ממש חייבים תאימות לאחור
        try:
            batch.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))
        except Exception:
            pass

        try:
            batch.drop_column('hashed_password')
        except Exception:
            pass
