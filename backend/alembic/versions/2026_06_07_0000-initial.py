"""initial

Revision ID: 2026_06_07_0000
Revises: 
Create Date: 2026-06-07 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2026_06_07_0000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. glucose_readings table
    op.create_table(
        'glucose_readings',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('value_mgdl', sa.Integer(), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_glucose_readings_id'), 'glucose_readings', ['id'], unique=False)
    op.create_index(op.f('ix_glucose_readings_user_id'), 'glucose_readings', ['user_id'], unique=False)
    op.create_index(op.f('ix_glucose_readings_datetime'), 'glucose_readings', ['datetime'], unique=False)

    # 3. fasting_sessions table
    op.create_table(
        'fasting_sessions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('protocol', sa.String(length=50), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_fasting_sessions_id'), 'fasting_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_fasting_sessions_user_id'), 'fasting_sessions', ['user_id'], unique=False)

    # 4. habit_logs table
    op.create_table(
        'habit_logs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('habit_key', sa.String(length=50), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'date', 'habit_key', name='uq_user_date_habit')
    )
    op.create_index(op.f('ix_habit_logs_id'), 'habit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_habit_logs_user_id'), 'habit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_habit_logs_date'), 'habit_logs', ['date'], unique=False)

    # 5. alarms table
    op.create_table(
        'alarms',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('config_time', sa.String(length=5), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_alarms_id'), 'alarms', ['id'], unique=False)
    op.create_index(op.f('ix_alarms_user_id'), 'alarms', ['user_id'], unique=False)

    # 6. meal_entries table
    op.create_table(
        'meal_entries',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('photo_path', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('ai_analysis', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_meal_entries_id'), 'meal_entries', ['id'], unique=False)
    op.create_index(op.f('ix_meal_entries_user_id'), 'meal_entries', ['user_id'], unique=False)
    op.create_index(op.f('ix_meal_entries_datetime'), 'meal_entries', ['datetime'], unique=False)

    # 7. push_subscriptions table
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('p256dh', sa.String(length=255), nullable=False),
        sa.Column('auth', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_push_subscriptions_id'), 'push_subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_push_subscriptions_user_id'), 'push_subscriptions', ['user_id'], unique=False)
    op.create_index(op.f('ix_push_subscriptions_endpoint'), 'push_subscriptions', ['endpoint'], unique=True)

def downgrade() -> None:
    op.drop_table('push_subscriptions')
    op.drop_table('meal_entries')
    op.drop_table('alarms')
    op.drop_table('habit_logs')
    op.drop_table('fasting_sessions')
    op.drop_table('glucose_readings')
    op.drop_table('users')
