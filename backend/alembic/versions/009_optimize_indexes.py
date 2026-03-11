"""优化数据库索引

Revision ID: 009
Revises: 008_add_unified_knowledge_tables
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_optimize_indexes'
down_revision = '008_add_unified_knowledge_tables'
branch_labels = None
depends_on = None


def upgrade():
    """
    优化数据库索引
    
    1. 为常用查询添加复合索引
    2. 优化全文搜索索引
    3. 添加部分索引（针对特定状态）
    4. 优化外键索引
    """
    
    # ==================== 1. 优化 unified_knowledge_units 表索引 ====================
    
    # 添加复合索引：知识库+类型+状态（常用过滤组合）
    op.create_index(
        'idx_uku_kb_type_status',
        'unified_knowledge_units',
        ['knowledge_base_id', 'unit_type', 'status']
    )
    
    # 添加复合索引：知识库+质量分数（用于质量筛选）
    op.create_index(
        'idx_uku_kb_quality',
        'unified_knowledge_units',
        ['knowledge_base_id', 'quality_score']
    )
    
    # 添加复合索引：知识库+向量化状态（用于向量化任务）
    op.create_index(
        'idx_uku_kb_vector_status',
        'unified_knowledge_units',
        ['knowledge_base_id', 'vector_status']
    )
    
    # 添加复合索引：父单元ID+排序（用于层级查询）
    op.create_index(
        'idx_uku_parent_created',
        'unified_knowledge_units',
        ['parent_unit_id', 'created_at']
    )
    
    # 添加部分索引：活跃的单元（减少索引大小）
    op.execute("""
        CREATE INDEX idx_uku_active ON unified_knowledge_units (knowledge_base_id, unit_type)
        WHERE status = 'active'
    """)
    
    # ==================== 2. 优化 knowledge_unit_associations 表索引 ====================
    
    # 添加复合索引：知识库+类型+强度（用于关联筛选）
    op.create_index(
        'idx_kua_kb_type_strength',
        'knowledge_unit_associations',
        ['knowledge_base_id', 'association_type', 'strength']
    )
    
    # 添加复合索引：源单元+类型（用于出边查询）
    op.create_index(
        'idx_kua_source_type',
        'knowledge_unit_associations',
        ['source_unit_id', 'association_type']
    )
    
    # 添加复合索引：目标单元+类型（用于入边查询）
    op.create_index(
        'idx_kua_target_type',
        'knowledge_unit_associations',
        ['target_unit_id', 'association_type']
    )
    
    # 添加部分索引：活跃的关联
    op.execute("""
        CREATE INDEX idx_kua_active ON knowledge_unit_associations (source_unit_id, target_unit_id)
        WHERE status = 'active'
    """)
    
    # ==================== 3. 优化 processing_pipeline_runs 表索引 ====================
    
    # 添加复合索引：知识库+类型+状态（用于流水线查询）
    op.create_index(
        'idx_ppr_kb_type_status',
        'processing_pipeline_runs',
        ['knowledge_base_id', 'pipeline_type', 'status']
    )
    
    # 添加复合索引：知识库+创建时间（用于历史查询）
    op.create_index(
        'idx_ppr_kb_created',
        'processing_pipeline_runs',
        ['knowledge_base_id', 'created_at']
    )
    
    # 添加复合索引：状态+进度（用于监控面板）
    op.create_index(
        'idx_ppr_status_progress',
        'processing_pipeline_runs',
        ['status', 'progress']
    )
    
    # 添加部分索引：进行中的任务
    op.execute("""
        CREATE INDEX idx_ppr_running ON processing_pipeline_runs (knowledge_base_id, started_at)
        WHERE status IN ('pending', 'running', 'paused')
    """)
    
    # ==================== 4. 优化 vector_metadata 表索引 ====================
    
    # 添加复合索引：知识库+模型+状态
    op.create_index(
        'idx_vm_kb_model_status',
        'vector_metadata',
        ['knowledge_base_id', 'embedding_model', 'status']
    )
    
    # 添加复合索引：单元ID+版本（用于版本查询）
    op.create_index(
        'idx_vm_unit_version',
        'vector_metadata',
        ['unit_id', 'vector_version']
    )
    
    # ==================== 5. 优化 knowledge_unit_versions 表索引 ====================
    
    # 添加复合索引：单元ID+创建时间（用于版本历史）
    op.create_index(
        'idx_kuv_unit_created',
        'knowledge_unit_versions',
        ['unit_id', 'created_at']
    )
    
    # 添加复合索引：知识库+变更类型
    op.create_index(
        'idx_kuv_kb_change_type',
        'knowledge_unit_versions',
        ['knowledge_base_id', 'change_type']
    )
    
    # ==================== 6. 优化现有表索引 ====================
    
    # 为 knowledge_documents 表添加复合索引
    op.create_index(
        'idx_kd_kb_status',
        'knowledge_documents',
        ['knowledge_base_id', 'status']
    )
    
    op.create_index(
        'idx_kd_kb_created',
        'knowledge_documents',
        ['knowledge_base_id', 'created_at']
    )
    
    # 为 knowledge_bases 表添加索引
    op.create_index(
        'idx_kb_status',
        'knowledge_bases',
        ['status']
    )
    
    # ==================== 7. 删除冗余索引（如果有）====================
    # 注意：在实际环境中应该先分析再删除，这里仅作为示例
    # op.drop_index('idx_redundant_index', table_name='some_table')


def downgrade():
    """
    回滚索引优化
    """
    # 删除 unified_knowledge_units 表的优化索引
    op.drop_index('idx_uku_kb_type_status', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_kb_quality', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_kb_vector_status', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_parent_created', table_name='unified_knowledge_units')
    op.execute("DROP INDEX IF EXISTS idx_uku_active")
    
    # 删除 knowledge_unit_associations 表的优化索引
    op.drop_index('idx_kua_kb_type_strength', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_source_type', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_target_type', table_name='knowledge_unit_associations')
    op.execute("DROP INDEX IF EXISTS idx_kua_active")
    
    # 删除 processing_pipeline_runs 表的优化索引
    op.drop_index('idx_ppr_kb_type_status', table_name='processing_pipeline_runs')
    op.drop_index('idx_ppr_kb_created', table_name='processing_pipeline_runs')
    op.drop_index('idx_ppr_status_progress', table_name='processing_pipeline_runs')
    op.execute("DROP INDEX IF EXISTS idx_ppr_running")
    
    # 删除 vector_metadata 表的优化索引
    op.drop_index('idx_vm_kb_model_status', table_name='vector_metadata')
    op.drop_index('idx_vm_unit_version', table_name='vector_metadata')
    
    # 删除 knowledge_unit_versions 表的优化索引
    op.drop_index('idx_kuv_unit_created', table_name='knowledge_unit_versions')
    op.drop_index('idx_kuv_kb_change_type', table_name='knowledge_unit_versions')
    
    # 删除现有表的优化索引
    op.drop_index('idx_kd_kb_status', table_name='knowledge_documents')
    op.drop_index('idx_kd_kb_created', table_name='knowledge_documents')
    op.drop_index('idx_kb_status', table_name='knowledge_bases')
