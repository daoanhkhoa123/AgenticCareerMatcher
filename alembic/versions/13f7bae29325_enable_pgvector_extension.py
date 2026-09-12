"""enable pgvector extension

Revision ID: 13f7bae29325
Revises: 55a1ddb40723
Create Date: 2026-09-12 22:12:27.024039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13f7bae29325'
down_revision: Union[str, Sequence[str], None] = '55a1ddb40723'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector")
