"""添加 file_hash 列到 knowledge_documents 表

Revision ID: 006_add_file_hash_to_knowledge_documents
Revises: 005_add_task_execution_fields
Create Date: 2026-03-04 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_file_hash_to_knowledge_documents'
down_revision = '004_add_capability_orchestration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""

    # 在 knowledge_documents 表中添加 file_hash 字段
    op.add_column('knowledge_documents',
        sa.Column('file_hash', sa.String(64), nullable=True, index=True)
    )

    print("数据库升级完成：已添加 file_hash 字段到 knowledge_documents 表")


def downgrade() -> None:
    """降级数据库结构"""

    # 删除 file_hash 字段
    op.drop_column('knowledge_documents', 'file_hash')

    print("数据库降级完成：已删除 file_hash 字段")
