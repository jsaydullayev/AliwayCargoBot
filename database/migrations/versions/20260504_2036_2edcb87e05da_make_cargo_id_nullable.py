"""make_cargo_id_nullable

Revision ID: 2edcb87e05da
Revises: initial
Create Date: 2026-05-04 20:36:08.292443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2edcb87e05da'
down_revision: Union[str, None] = 'initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # cargo_id ni nullable qilish
    op.alter_column('clients', 'cargo_id',
               existing_type=sa.VARCHAR(length=5),
               nullable=True)


def downgrade() -> None:
    # cargo_id ni nullable=False qaytarish
    op.alter_column('clients', 'cargo_id',
               existing_type=sa.VARCHAR(length=5),
               nullable=False)
