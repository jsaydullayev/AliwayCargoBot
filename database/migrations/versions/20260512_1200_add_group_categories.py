"""add group categories

Revision ID: add_grp_categories
Revises: add_cn_fields
Create Date: 2026-05-12

Yangi `group_categories` jadvali va `groups.category_id` FK ustuni.
Mavjud guruhlar default kategoriyalarga ko'chiriladi (data migration).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_grp_categories'
down_revision: Union[str, None] = 'add_cn_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. group_categories jadvalini yaratish
    op.create_table(
        'group_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('name_uz', sa.String(length=255), nullable=False),
        sa.Column('name_ru', sa.String(length=255), nullable=False),
        sa.Column('name_tr', sa.String(length=255), nullable=False),
        sa.Column('emoji', sa.String(length=10), nullable=False, server_default='📂'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    # 2. groups jadvaliga category_id ustunini qo'shish (nullable)
    op.add_column('groups', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_index('ix_groups_category_id', 'groups', ['category_id'])
    op.create_foreign_key(
        'fk_groups_category_id',
        'groups', 'group_categories',
        ['category_id'], ['id'],
        ondelete='SET NULL',
    )

    # 3. Data migration: mavjud guruhlardan default kategoriyalar yaratish
    # Har bir mavjud guruh nomidan kategoriya hosil qilamiz va
    # uning telegram_link'ini "Asosiy" guruh sifatida saqlab qolamiz.
    conn = op.get_bind()

    existing_groups = conn.execute(sa.text(
        "SELECT id, name_uz, name_ru, name_tr, emoji, sort_order FROM groups"
    )).fetchall()

    for grp in existing_groups:
        # Bir xil nomdagi kategoriya allaqachon bo'lmasligini tekshirish
        existing_cat = conn.execute(sa.text(
            "SELECT id FROM group_categories WHERE name_uz = :name"
        ), {"name": grp.name_uz}).fetchone()

        if existing_cat:
            cat_id = existing_cat.id
        else:
            result = conn.execute(sa.text("""
                INSERT INTO group_categories (name_uz, name_ru, name_tr, emoji, is_active, sort_order)
                VALUES (:name_uz, :name_ru, :name_tr, :emoji, TRUE, :sort_order)
                RETURNING id
            """), {
                "name_uz": grp.name_uz,
                "name_ru": grp.name_ru,
                "name_tr": grp.name_tr,
                "emoji": grp.emoji or "📂",
                "sort_order": grp.sort_order or 0,
            })
            cat_id = result.scalar()

        # Eski guruhni shu kategoriyaga biriktirish va nomini "Asosiy" ga o'zgartirish
        conn.execute(sa.text("""
            UPDATE groups
            SET category_id = :cat_id,
                name_uz = 'Asosiy',
                name_ru = 'Основной',
                name_tr = 'Ana'
            WHERE id = :grp_id
        """), {"cat_id": cat_id, "grp_id": grp.id})


def downgrade() -> None:
    # FK va ustunni olib tashlash
    op.drop_constraint('fk_groups_category_id', 'groups', type_='foreignkey')
    op.drop_index('ix_groups_category_id', table_name='groups')
    op.drop_column('groups', 'category_id')

    # Jadvalni o'chirish
    op.drop_table('group_categories')
