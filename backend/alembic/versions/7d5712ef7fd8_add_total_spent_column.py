"""add_total_spent_column

Revision ID: 7d5712ef7fd8
Revises: dc3f914b9e6a
Create Date: 2025-09-16 21:39:48.025748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d5712ef7fd8'
down_revision = 'dc3f914b9e6a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add total_spent column to users table
    op.add_column('users', sa.Column('total_spent', sa.DECIMAL(precision=10, scale=2), nullable=False, server_default='0.00'))


def downgrade() -> None:
    # Remove total_spent column from users table
    op.drop_column('users', 'total_spent')
