from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "cf36412b4ea9"
down_revision = "cae03aeba4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event",
        sa.Column("required_attendees", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "event",
        sa.Column("is_locked_for_edit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    # להסיר server_default אחרי ההוספה (שומר על סכימה זהה למודלים)
    op.alter_column("event", "required_attendees", server_default=None)
    op.alter_column("event", "is_locked_for_edit", server_default=None)


def downgrade():
    op.drop_column("event", "is_locked_for_edit")
    op.drop_column("event", "required_attendees")
