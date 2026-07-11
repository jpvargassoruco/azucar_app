"""add vitals tables and user height

Revision ID: 63157c8f
Revises: c70ac26199f7
Create Date: 2026-07-11 19:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63157c8f'
down_revision: Union[str, None] = 'c70ac26199f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add height column to users table
    op.add_column('users', sa.Column('height', sa.Integer(), nullable=True))

    # Create weights table
    op.create_table(
        'weights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weights_id'), 'weights', ['id'], unique=False)
    op.create_index(op.f('ix_weights_datetime'), 'weights', ['datetime'], unique=False)
    op.create_index(op.f('ix_weights_user_id'), 'weights', ['user_id'], unique=False)

    # Create blood_pressures table
    op.create_table(
        'blood_pressures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('systolic_mmhg', sa.Integer(), nullable=False),
        sa.Column('diastolic_mmhg', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blood_pressures_id'), 'blood_pressures', ['id'], unique=False)
    op.create_index(op.f('ix_blood_pressures_datetime'), 'blood_pressures', ['datetime'], unique=False)
    op.create_index(op.f('ix_blood_pressures_user_id'), 'blood_pressures', ['user_id'], unique=False)

    # Create hba1c_readings table
    op.create_table(
        'hba1c_readings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('value_percent', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hba1c_readings_id'), 'hba1c_readings', ['id'], unique=False)
    op.create_index(op.f('ix_hba1c_readings_datetime'), 'hba1c_readings', ['datetime'], unique=False)
    op.create_index(op.f('ix_hba1c_readings_user_id'), 'hba1c_readings', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop hba1c_readings table
    op.drop_index(op.f('ix_hba1c_readings_user_id'), table_name='hba1c_readings')
    op.drop_index(op.f('ix_hba1c_readings_datetime'), table_name='hba1c_readings')
    op.drop_index(op.f('ix_hba1c_readings_id'), table_name='hba1c_readings')
    op.drop_table('hba1c_readings')

    # Drop blood_pressures table
    op.drop_index(op.f('ix_blood_pressures_user_id'), table_name='blood_pressures')
    op.drop_index(op.f('ix_blood_pressures_datetime'), table_name='blood_pressures')
    op.drop_index(op.f('ix_blood_pressures_id'), table_name='blood_pressures')
    op.drop_table('blood_pressures')

    # Drop weights table
    op.drop_index(op.f('ix_weights_user_id'), table_name='weights')
    op.drop_index(op.f('ix_weights_datetime'), table_name='weights')
    op.drop_index(op.f('ix_weights_id'), table_name='weights')
    op.drop_table('weights')

    # Remove height column from users table
    op.drop_column('users', 'height')
