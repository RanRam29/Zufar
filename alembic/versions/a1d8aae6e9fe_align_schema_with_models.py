"""align schema with models (NO-OP replacement to avoid destructive ops)

Revision ID: a1d8aae6e9fe
Revises: mrg_20250812_single_head
Create Date: 2025-08-14 11:09:50.834470
"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa

# revision identifiers, used by Alembic.
revision = "a1d8aae6e9fe"
down_revision = "mrg_20250812_single_head"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # NO-OP: replaces previous autogenerate that dropped unrelated tables.
    # All required user-table changes are handled by 8f353e75bde7.
    pass

def downgrade() -> None:
    # NO-OP
    pass
