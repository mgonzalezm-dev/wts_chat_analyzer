"""empty message

Revision ID: eca27cab5082
Revises: 27f8d890cde7
Create Date: 2025-07-18 22:59:37.443863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eca27cab5082'
down_revision: Union[str, None] = '27f8d890cde7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration is now handled by the initial_migration.py file
    # which creates all tables from the SQLAlchemy models
    pass


def downgrade() -> None:
    # This migration is now handled by the initial_migration.py file
    pass
