"""添加分层知识图谱支持

Revision ID: 007
Revises: 006_add_file_hash_to_knowledge_documents
Create Date: 2026-03-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_hierarchical_knowledge_graph'
down_revision = '006_add_file_hash_to_knowledge_documents'
branch_labels = None
depends_on = None


def upgrade():
    # 创建全局实体表
    op.create_table(
        'global_entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('global_name', sa.String(200), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('all_aliases', sa.JSON(), nullable=True),
        sa.Column('kb_count', sa.Integer(), default=0),
        sa.Column('document_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_global_entities_type', 'global_entities', ['entity_type'])
    
    # 创建知识库级实体表
    op.create_table(
        'kb_entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False),
        sa.Column('canonical_name', sa.String(200), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('document_count', sa.Integer(), default=0),
        sa.Column('occurrence_count', sa.Integer(), default=0),
        sa.Column('global_entity_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id']),
        sa.ForeignKeyConstraint(['global_entity_id'], ['global_entities.id'])
    )
    op.create_index('idx_kb_entities_kb', 'kb_entities', ['knowledge_base_id'])
    op.create_index('idx_kb_entities_type', 'kb_entities', ['entity_type'])
    op.create_index('idx_kb_entities_global', 'kb_entities', ['global_entity_id'])
    
    # 创建知识库级关系表
    op.create_table(
        'kb_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False),
        sa.Column('source_kb_entity_id', sa.Integer(), nullable=False),
        sa.Column('target_kb_entity_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('aggregated_count', sa.Integer(), default=0),
        sa.Column('source_relationships', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id']),
        sa.ForeignKeyConstraint(['source_kb_entity_id'], ['kb_entities.id']),
        sa.ForeignKeyConstraint(['target_kb_entity_id'], ['kb_entities.id'])
    )
    op.create_index('idx_kb_relations_kb', 'kb_relationships', ['knowledge_base_id'])
    op.create_index('idx_kb_relations_source', 'kb_relationships', ['source_kb_entity_id'])
    op.create_index('idx_kb_relations_target', 'kb_relationships', ['target_kb_entity_id'])
    
    # 创建全局级关系表
    op.create_table(
        'global_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_global_entity_id', sa.Integer(), nullable=False),
        sa.Column('target_global_entity_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('aggregated_count', sa.Integer(), default=0),
        sa.Column('source_kbs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_global_entity_id'], ['global_entities.id']),
        sa.ForeignKeyConstraint(['target_global_entity_id'], ['global_entities.id'])
    )
    op.create_index('idx_global_relations_source', 'global_relationships', ['source_global_entity_id'])
    op.create_index('idx_global_relations_target', 'global_relationships', ['target_global_entity_id'])
    
    # 修改 document_entities 表，添加层级关联
    op.add_column('document_entities', sa.Column('kb_entity_id', sa.Integer(), nullable=True))
    op.add_column('document_entities', sa.Column('global_entity_id', sa.Integer(), nullable=True))
    op.create_index('idx_doc_entities_kb', 'document_entities', ['kb_entity_id'])
    op.create_index('idx_doc_entities_global', 'document_entities', ['global_entity_id'])
    op.create_foreign_key('fk_doc_entities_kb', 'document_entities', 'kb_entities', ['kb_entity_id'], ['id'])
    op.create_foreign_key('fk_doc_entities_global', 'document_entities', 'global_entities', ['global_entity_id'], ['id'])


def downgrade():
    # 删除外键
    op.drop_constraint('fk_doc_entities_kb', 'document_entities', type_='foreignkey')
    op.drop_constraint('fk_doc_entities_global', 'document_entities', type_='foreignkey')
    
    # 删除索引
    op.drop_index('idx_doc_entities_kb', table_name='document_entities')
    op.drop_index('idx_doc_entities_global', table_name='document_entities')
    
    # 删除列
    op.drop_column('document_entities', 'kb_entity_id')
    op.drop_column('document_entities', 'global_entity_id')
    
    # 删除表
    op.drop_index('idx_global_relations_source', table_name='global_relationships')
    op.drop_index('idx_global_relations_target', table_name='global_relationships')
    op.drop_table('global_relationships')
    
    op.drop_index('idx_kb_relations_kb', table_name='kb_relationships')
    op.drop_index('idx_kb_relations_source', table_name='kb_relationships')
    op.drop_index('idx_kb_relations_target', table_name='kb_relationships')
    op.drop_table('kb_relationships')
    
    op.drop_index('idx_kb_entities_kb', table_name='kb_entities')
    op.drop_index('idx_kb_entities_type', table_name='kb_entities')
    op.drop_index('idx_kb_entities_global', table_name='kb_entities')
    op.drop_table('kb_entities')
    
    op.drop_index('idx_global_entities_type', table_name='global_entities')
    op.drop_table('global_entities')
