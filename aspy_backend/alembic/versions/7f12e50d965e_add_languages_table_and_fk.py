"""add languages table and fk

Revision ID: 7f12e50d965e
Revises: 6e01e49d854c
Create Date: 2025-12-15 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f12e50d965e'
down_revision: Union[str, None] = '6e01e49d854c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create languages table
    op.create_table('languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('slug', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_languages_id'), 'languages', ['id'], unique=False)
    op.create_index(op.f('ix_languages_name'), 'languages', ['name'], unique=True)
    op.create_index(op.f('ix_languages_slug'), 'languages', ['slug'], unique=True)

    # 2. Add language_id to code_executions
    op.add_column('code_executions', sa.Column('language_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'code_executions', 'languages', ['language_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'code_executions', type_='foreignkey')
    op.drop_column('code_executions', 'language_id')
    op.drop_index(op.f('ix_languages_slug'), table_name='languages')
    op.drop_index(op.f('ix_languages_name'), table_name='languages')
    op.drop_index(op.f('ix_languages_id'), table_name='languages')
    op.drop_table('languages')
