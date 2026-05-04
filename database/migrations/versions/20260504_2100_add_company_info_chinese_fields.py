"""add company_info chinese fields

Revision ID: add_cn_fields
Revises: 2edcb87e05da
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_cn_fields'
down_revision: Union[str, None] = '2edcb87e05da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add address_cn column to company_info
    op.add_column('company_info', sa.Column('address_cn', sa.Text(), nullable=True))

    # Add phone_numbers_cn column to company_info
    op.add_column('company_info', sa.Column('phone_numbers_cn', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    # Remove phone_numbers_cn column
    op.drop_column('company_info', 'phone_numbers_cn')

    # Remove address_cn column
    op.drop_column('company_info', 'address_cn')
