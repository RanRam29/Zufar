"""add full_name column to user

Revision ID: a1b2c3d4fullnam3
Revises: cf36412b4ea9
Create Date: 2025-08-12

"""
from alembic import op
import sqlalchemy as sa

# מזהים
revision = "a1b2c3d4fullnam3"
down_revision = "cf36412b4ea9"  # עדכן אם ה-head הקודם אצלך שונה
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) הוספת העמודה כ-nullable כדי לא לשבור שורות קיימות
    op.add_column(
        "user",
        sa.Column("full_name", sa.String(length=256), nullable=True),
    )

    # 2) אתחול ערכים לשורות קיימות (לוקחים את החלק לפני ה-@ באימייל)
    op.execute('UPDATE "user" SET full_name = split_part(email, \'@\', 1) WHERE full_name IS NULL')

    # 3) נעילת העמודה כ-not null (תואם למודל)
    op.alter_column(
        "user",
        "full_name",
        existing_type=sa.String(length=256),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("user", "full_name")
