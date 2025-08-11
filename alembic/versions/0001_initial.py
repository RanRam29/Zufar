
"""create base tables"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('user',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(length=256), nullable=False, unique=True),
        sa.Column('full_name', sa.String(length=256), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
    )
    op.create_index('ix_user_email', 'user', ['email'], unique=True)

    op.create_table('event',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=2000), nullable=False),
        sa.Column('address', sa.String(length=300), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('required_attendees', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_locked_for_edit', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    op.create_table('participant',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), index=True, nullable=True),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lng', sa.Float(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('participant')
    op.drop_index('ix_user_email', table_name='user')
    op.drop_table('user')
    op.drop_table('event')
