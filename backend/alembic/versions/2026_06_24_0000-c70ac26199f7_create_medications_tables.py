"""create medications tables

Revision ID: c70ac26199f7
Revises: 00a34ea76c46
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c70ac26199f7'
down_revision: Union[str, None] = '00a34ea76c46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'medications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('dosage', sa.String(length=50), nullable=True),
        sa.Column('times', sa.JSON(), nullable=False),
        sa.Column('days_of_week', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medications_id'), 'medications', ['id'], unique=False)
    op.create_index(op.f('ix_medications_user_id'), 'medications', ['user_id'], unique=False)

    op.create_table(
        'medication_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('scheduled_time', sa.String(length=5), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('marked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('medication_id', 'date', 'scheduled_time', name='uq_medication_date_time')
    )
    op.create_index(op.f('ix_medication_logs_id'), 'medication_logs', ['id'], unique=False)
    op.create_index(op.f('ix_medication_logs_medication_id'), 'medication_logs', ['medication_id'], unique=False)
    op.create_index(op.f('ix_medication_logs_user_id'), 'medication_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_medication_logs_user_id'), table_name='medication_logs')
    op.drop_index(op.f('ix_medication_logs_medication_id'), table_name='medication_logs')
    op.drop_index(op.f('ix_medication_logs_id'), table_name='medication_logs')
    op.drop_table('medication_logs')
    op.drop_index(op.f('ix_medications_user_id'), table_name='medications')
    op.drop_index(op.f('ix_medications_id'), table_name='medications')
    op.drop_table('medications')
