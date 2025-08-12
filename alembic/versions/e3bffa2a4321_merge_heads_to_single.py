"""merge heads to single

Revision ID: e3bffa2a4321
Revises: 0001_init, 4f6d2a1b7ac9
Create Date: 2025-08-12 13:56:28.378762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3bffa2a4321'
down_revision = ('0001_init', '4f6d2a1b7ac9')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
