"""initial schema: user, event, participant

Revision ID: 0001_init
Revises: 
Create Date: 2025-08-12 08:30:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_init'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(length=256), nullable=False, unique=True),
        sa.Column('full_name', sa.String(length=256), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_user_email', 'user', ['email'], unique=True)

    op.create_table(
        'event',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=2000), nullable=False),
        sa.Column('address', sa.String(length=300), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False, server_default='IL'),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('required_attendees', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_locked_for_edit', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    op.create_table(
        'participant',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lng', sa.Float(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_participant_event_id', 'participant', ['event_id'])
    op.create_index('ix_participant_user_id', 'participant', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_participant_user_id', table_name='participant')
    op.drop_index('ix_participant_event_id', table_name='participant')
    op.drop_table('participant')
    op.drop_table('event')
    op.drop_index('ix_user_email', table_name='user')
    op.drop_table('user')
