"""update plantype enum

Revision ID: 8a34b21e876d
Revises: 7f12e50d965e
Create Date: 2025-12-15 15:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a34b21e876d'
down_revision: Union[str, None] = '7f12e50d965e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new values to the enum
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE plantype ADD VALUE IF NOT EXISTS 'starter'")
        op.execute("ALTER TYPE plantype ADD VALUE IF NOT EXISTS 'pro'")
        op.execute("ALTER TYPE plantype ADD VALUE IF NOT EXISTS 'enterprise'")


def downgrade() -> None:
    pass
