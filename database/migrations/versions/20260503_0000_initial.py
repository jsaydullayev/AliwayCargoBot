"""Initial migration - Create all tables

Revision ID: initial
Revises:
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create CargoStatus enum type
    cargo_status_enum = postgresql.ENUM(
        'pending', 'in_transit', 'arrived', 'ready', 'delivered',
        name='cargo_status', create_type=True
    )

    # Create clients table
    op.create_table(
        'clients',
        sa.Column('id', postgresql.BIGINT(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', postgresql.BIGINT(), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('cargo_id', sa.String(length=5), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('language', sa.String(length=5), nullable=False, server_default='uz'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.BIGINT(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id'),
        sa.UniqueConstraint('phone_number'),
        sa.UniqueConstraint('cargo_id'),
    )
    op.create_index('ix_clients_id', 'clients', ['id'])
    op.create_index('ix_clients_phone_number', 'clients', ['phone_number'])
    op.create_index('ix_clients_cargo_id', 'clients', ['cargo_id'])
    op.create_index('ix_clients_telegram_id', 'clients', ['telegram_id'])

    # Create shipments table
    op.create_table(
        'shipments',
        sa.Column('id', postgresql.BIGINT(), autoincrement=True, nullable=False),
        sa.Column('client_id', postgresql.BIGINT(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('weight_kg', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('cargo_weight_kg', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=5), nullable=True),
        sa.Column('photo_file_id', sa.Text(), nullable=True),
        sa.Column('status', cargo_status_enum, nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.BIGINT(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_shipments_id', 'shipments', ['id'])
    op.create_index('ix_shipments_client_id', 'shipments', ['client_id'])
    op.create_index('ix_shipments_status', 'shipments', ['status'])
    op.create_index('ix_shipments_created_at', 'shipments', ['created_at'])

    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name_uz', sa.String(length=255), nullable=False),
        sa.Column('name_ru', sa.String(length=255), nullable=False),
        sa.Column('name_tr', sa.String(length=255), nullable=False),
        sa.Column('telegram_link', sa.Text(), nullable=False),
        sa.Column('emoji', sa.String(length=10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create company_info table
    op.create_table(
        'company_info',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('address_uz', sa.Text(), nullable=False),
        sa.Column('address_ru', sa.Text(), nullable=False),
        sa.Column('address_tr', sa.Text(), nullable=False),
        sa.Column('phone_numbers', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('telegram_account', sa.String(length=255), nullable=False),
        sa.Column('working_hours', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('company_info')
    op.drop_table('groups')
    op.drop_table('shipments')
    op.drop_table('clients')

    # Drop CargoStatus enum
    op.execute('DROP TYPE IF EXISTS cargo_status')
