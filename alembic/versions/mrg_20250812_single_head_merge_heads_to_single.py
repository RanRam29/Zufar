"""merge heads to single

Revision ID: mrg_20250812_single_head
Revises: a1b2c3d4fullnam3, e3bffa2a4321
Create Date: 2025-08-12 11:02:02

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "mrg_20250812_single_head"
down_revision = ("a1b2c3d4fullnam3", "e3bffa2a4321")
branch_labels = None
depends_on = None


def upgrade():
    # no-op: structural merge only
    pass


def downgrade():
    # no-op
    pass
