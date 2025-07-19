"""add whatsapp analyzer tables

Revision ID: 27f8d890cde7
Revises: 001
Create Date: 2025-07-18 22:46:16.861218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27f8d890cde7'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration is now handled by the initial_migration.py file
    # which creates all tables from the SQLAlchemy models
    pass


def downgrade() -> None:
    # This migration is now handled by the initial_migration.py file
    pass
