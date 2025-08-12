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

def upgrade():
    # no-op: superseded by 4f6d2a1b7ac9 (which also adds created_at)
    pass

def downgrade():
    pass

