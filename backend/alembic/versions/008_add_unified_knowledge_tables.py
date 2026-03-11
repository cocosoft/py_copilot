"""添加一体化知识管理表结构

Revision ID: 008
Revises: 007_add_hierarchical_knowledge_graph
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_unified_knowledge_tables'
down_revision = '007_add_hierarchical_knowledge_graph'
branch_labels = None
depends_on = None


def upgrade():
    """
    创建一体化知识管理所需的表结构
    
    包含以下表：
    - unified_knowledge_units: 统一知识单元表
    - knowledge_unit_associations: 知识单元关联表
    - processing_pipeline_runs: 处理流水线运行记录表
    - vector_metadata: 向量元数据表
    - knowledge_unit_versions: 知识单元版本表
    """
    
    # ==================== 1. 统一知识单元表 ====================
    op.create_table(
        'unified_knowledge_units',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('unit_id', sa.String(64), nullable=False, unique=True, comment='全局唯一单元ID'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='所属知识库ID'),
        sa.Column('document_id', sa.Integer(), nullable=True, comment='关联文档ID'),
        sa.Column('parent_unit_id', sa.String(64), nullable=True, comment='父单元ID'),
        
        # 单元类型和状态
        sa.Column('unit_type', sa.String(50), nullable=False, comment='单元类型: DOCUMENT/CHUNK/ENTITY/CONCEPT'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active', 
                  comment='状态: active/archived/deleted'),
        
        # 内容信息
        sa.Column('title', sa.String(500), nullable=True, comment='单元标题'),
        sa.Column('content', sa.Text(), nullable=True, comment='单元内容'),
        sa.Column('content_hash', sa.String(64), nullable=True, comment='内容哈希'),
        
        # 向量化信息
        sa.Column('vector_id', sa.String(64), nullable=True, comment='向量存储ID'),
        sa.Column('vector_status', sa.String(20), nullable=True, 
                  comment='向量化状态: pending/processing/completed/failed'),
        sa.Column('vector_version', sa.Integer(), nullable=False, server_default='1', comment='向量版本'),
        
        # 质量评估
        sa.Column('quality_score', sa.Float(), nullable=True, comment='质量分数 0-100'),
        sa.Column('quality_dimensions', sa.JSON(), nullable=True, comment='各维度质量评分'),
        
        # 元数据
        sa.Column('metadata', sa.JSON(), nullable=True, comment='扩展元数据'),
        sa.Column('position', sa.JSON(), nullable=True, comment='位置信息(起始/结束位置)'),
        sa.Column('hierarchy_path', sa.String(500), nullable=True, comment='层级路径'),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='0', comment='层级深度'),
        
        # 统计信息
        sa.Column('child_count', sa.Integer(), nullable=False, server_default='0', comment='子单元数量'),
        sa.Column('association_count', sa.Integer(), nullable=False, server_default='0', comment='关联数量'),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0', comment='访问次数'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('vectorized_at', sa.DateTime(), nullable=True, comment='向量化完成时间'),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True, comment='最后访问时间'),
        
        # 主键和外键约束
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_unit_id'], ['unified_knowledge_units.unit_id'], ondelete='SET NULL'),
    )
    
    # 创建索引
    op.create_index('idx_uku_unit_id', 'unified_knowledge_units', ['unit_id'], unique=True)
    op.create_index('idx_uku_kb_id', 'unified_knowledge_units', ['knowledge_base_id'])
    op.create_index('idx_uku_doc_id', 'unified_knowledge_units', ['document_id'])
    op.create_index('idx_uku_parent_id', 'unified_knowledge_units', ['parent_unit_id'])
    op.create_index('idx_uku_type', 'unified_knowledge_units', ['unit_type'])
    op.create_index('idx_uku_status', 'unified_knowledge_units', ['status'])
    op.create_index('idx_uku_vector_status', 'unified_knowledge_units', ['vector_status'])
    op.create_index('idx_uku_quality', 'unified_knowledge_units', ['quality_score'])
    op.create_index('idx_uku_created_at', 'unified_knowledge_units', ['created_at'])
    op.create_index('idx_uku_kb_type', 'unified_knowledge_units', ['knowledge_base_id', 'unit_type'])
    op.create_index('idx_uku_kb_status', 'unified_knowledge_units', ['knowledge_base_id', 'status'])
    
    # ==================== 2. 知识单元关联表 ====================
    op.create_table(
        'knowledge_unit_associations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('association_id', sa.String(64), nullable=False, unique=True, comment='全局唯一关联ID'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='所属知识库ID'),
        
        # 关联双方
        sa.Column('source_unit_id', sa.String(64), nullable=False, comment='源单元ID'),
        sa.Column('target_unit_id', sa.String(64), nullable=False, comment='目标单元ID'),
        
        # 关联属性
        sa.Column('association_type', sa.String(50), nullable=False, 
                  comment='关联类型: CONTAINS/REFERENCES/SIMILAR_TO/RELATED_TO/PART_OF/INSTANCE_OF/SUBCLASS_OF/MENTIONS'),
        sa.Column('strength', sa.Float(), nullable=False, server_default='1.0', comment='关联强度 0-1'),
        sa.Column('bidirectional', sa.Boolean(), nullable=False, server_default='false', comment='是否双向'),
        
        # 关联元数据
        sa.Column('metadata', sa.JSON(), nullable=True, comment='关联元数据'),
        sa.Column('evidence', sa.Text(), nullable=True, comment='关联证据/依据'),
        sa.Column('confidence', sa.Float(), nullable=True, comment='置信度 0-1'),
        
        # 状态
        sa.Column('status', sa.String(20), nullable=False, server_default='active', 
                  comment='状态: active/inactive/deleted'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # 主键和外键约束
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_unit_id'], ['unified_knowledge_units.unit_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_unit_id'], ['unified_knowledge_units.unit_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('source_unit_id', 'target_unit_id', 'association_type', name='unique_association')
    )
    
    # 创建索引
    op.create_index('idx_kua_association_id', 'knowledge_unit_associations', ['association_id'], unique=True)
    op.create_index('idx_kua_kb_id', 'knowledge_unit_associations', ['knowledge_base_id'])
    op.create_index('idx_kua_source', 'knowledge_unit_associations', ['source_unit_id'])
    op.create_index('idx_kua_target', 'knowledge_unit_associations', ['target_unit_id'])
    op.create_index('idx_kua_type', 'knowledge_unit_associations', ['association_type'])
    op.create_index('idx_kua_strength', 'knowledge_unit_associations', ['strength'])
    op.create_index('idx_kua_status', 'knowledge_unit_associations', ['status'])
    op.create_index('idx_kua_kb_type', 'knowledge_unit_associations', ['knowledge_base_id', 'association_type'])
    
    # ==================== 3. 处理流水线运行记录表 ====================
    op.create_table(
        'processing_pipeline_runs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('run_id', sa.String(64), nullable=False, unique=True, comment='运行ID'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='所属知识库ID'),
        
        # 处理配置
        sa.Column('pipeline_type', sa.String(50), nullable=False, 
                  comment='流水线类型: document_processing/vectorization/quality_check/migration'),
        sa.Column('trigger_type', sa.String(20), nullable=False, 
                  comment='触发类型: manual/scheduled/event'),
        sa.Column('triggered_by', sa.Integer(), nullable=True, comment='触发用户ID'),
        
        # 处理范围
        sa.Column('target_unit_ids', sa.JSON(), nullable=True, comment='目标单元ID列表'),
        sa.Column('target_document_ids', sa.JSON(), nullable=True, comment='目标文档ID列表'),
        
        # 处理配置
        sa.Column('config', sa.JSON(), nullable=True, comment='处理配置参数'),
        sa.Column('processing_mode', sa.String(20), nullable=True, 
                  comment='处理模式: standard/high_quality/fast'),
        
        # 状态
        sa.Column('status', sa.String(20), nullable=False, server_default='pending',
                  comment='状态: pending/running/paused/completed/failed/cancelled'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0', comment='进度 0-100'),
        
        # 统计信息
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0', comment='总项目数'),
        sa.Column('processed_items', sa.Integer(), nullable=False, server_default='0', comment='已处理数'),
        sa.Column('success_items', sa.Integer(), nullable=False, server_default='0', comment='成功数'),
        sa.Column('failed_items', sa.Integer(), nullable=False, server_default='0', comment='失败数'),
        sa.Column('skipped_items', sa.Integer(), nullable=False, server_default='0', comment='跳过数'),
        
        # 时间和性能
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('estimated_duration', sa.Integer(), nullable=True, comment='预估耗时(秒)'),
        sa.Column('actual_duration', sa.Integer(), nullable=True, comment='实际耗时(秒)'),
        
        # 错误信息
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('error_details', sa.JSON(), nullable=True, comment='错误详情'),
        
        # 结果
        sa.Column('result_summary', sa.JSON(), nullable=True, comment='结果摘要'),
        sa.Column('output_log', sa.Text(), nullable=True, comment='输出日志'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # 主键和外键约束
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
    )
    
    # 创建索引
    op.create_index('idx_ppr_run_id', 'processing_pipeline_runs', ['run_id'], unique=True)
    op.create_index('idx_ppr_kb_id', 'processing_pipeline_runs', ['knowledge_base_id'])
    op.create_index('idx_ppr_type', 'processing_pipeline_runs', ['pipeline_type'])
    op.create_index('idx_ppr_status', 'processing_pipeline_runs', ['status'])
    op.create_index('idx_ppr_triggered_by', 'processing_pipeline_runs', ['triggered_by'])
    op.create_index('idx_ppr_created_at', 'processing_pipeline_runs', ['created_at'])
    op.create_index('idx_ppr_kb_status', 'processing_pipeline_runs', ['knowledge_base_id', 'status'])
    
    # ==================== 4. 向量元数据表 ====================
    op.create_table(
        'vector_metadata',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('vector_id', sa.String(64), nullable=False, unique=True, comment='向量ID'),
        sa.Column('unit_id', sa.String(64), nullable=False, comment='关联单元ID'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='所属知识库ID'),
        
        # 向量信息
        sa.Column('embedding_model', sa.String(100), nullable=True, comment='嵌入模型'),
        sa.Column('vector_dimension', sa.Integer(), nullable=True, comment='向量维度'),
        sa.Column('vector_version', sa.Integer(), nullable=False, server_default='1', comment='向量版本'),
        
        # 存储信息
        sa.Column('storage_backend', sa.String(50), nullable=True, comment='存储后端: chromadb/faiss/milvus'),
        sa.Column('storage_collection', sa.String(100), nullable=True, comment='存储集合名称'),
        sa.Column('storage_metadata', sa.JSON(), nullable=True, comment='存储相关元数据'),
        
        # 状态
        sa.Column('status', sa.String(20), nullable=False, server_default='active',
                  comment='状态: active/archived/deleted'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # 主键和外键约束
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['unified_knowledge_units.unit_id'], ondelete='CASCADE'),
    )
    
    # 创建索引
    op.create_index('idx_vm_vector_id', 'vector_metadata', ['vector_id'], unique=True)
    op.create_index('idx_vm_unit_id', 'vector_metadata', ['unit_id'])
    op.create_index('idx_vm_kb_id', 'vector_metadata', ['knowledge_base_id'])
    op.create_index('idx_vm_model', 'vector_metadata', ['embedding_model'])
    op.create_index('idx_vm_status', 'vector_metadata', ['status'])
    op.create_index('idx_vm_kb_status', 'vector_metadata', ['knowledge_base_id', 'status'])
    
    # ==================== 5. 知识单元版本表 ====================
    op.create_table(
        'knowledge_unit_versions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('version_id', sa.String(64), nullable=False, unique=True, comment='版本ID'),
        sa.Column('unit_id', sa.String(64), nullable=False, comment='单元ID'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='所属知识库ID'),
        
        # 版本信息
        sa.Column('version_number', sa.Integer(), nullable=False, comment='版本号'),
        sa.Column('version_type', sa.String(20), nullable=False, 
                  comment='版本类型: major/minor/patch'),
        
        # 内容快照
        sa.Column('title', sa.String(500), nullable=True, comment='标题快照'),
        sa.Column('content', sa.Text(), nullable=True, comment='内容快照'),
        sa.Column('content_hash', sa.String(64), nullable=True, comment='内容哈希'),
        sa.Column('metadata_snapshot', sa.JSON(), nullable=True, comment='元数据快照'),
        
        # 变更信息
        sa.Column('change_summary', sa.Text(), nullable=True, comment='变更摘要'),
        sa.Column('change_type', sa.String(50), nullable=True, 
                  comment='变更类型: create/update/delete/merge/split'),
        sa.Column('changed_fields', sa.JSON(), nullable=True, comment='变更字段列表'),
        
        # 版本关系
        sa.Column('parent_version_id', sa.String(64), nullable=True, comment='父版本ID'),
        sa.Column('merged_from_versions', sa.JSON(), nullable=True, comment='合并来源版本'),
        
        # 创建信息
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建用户ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # 主键和外键约束
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['unified_knowledge_units.unit_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_version_id'], ['knowledge_unit_versions.version_id'], ondelete='SET NULL'),
        sa.UniqueConstraint('unit_id', 'version_number', name='unique_unit_version')
    )
    
    # 创建索引
    op.create_index('idx_kuv_version_id', 'knowledge_unit_versions', ['version_id'], unique=True)
    op.create_index('idx_kuv_unit_id', 'knowledge_unit_versions', ['unit_id'])
    op.create_index('idx_kuv_kb_id', 'knowledge_unit_versions', ['knowledge_base_id'])
    op.create_index('idx_kuv_version_number', 'knowledge_unit_versions', ['version_number'])
    op.create_index('idx_kuv_created_at', 'knowledge_unit_versions', ['created_at'])
    op.create_index('idx_kuv_unit_version', 'knowledge_unit_versions', ['unit_id', 'version_number'])


def downgrade():
    """
    回滚数据库迁移
    
    按相反顺序删除表
    """
    # 删除表（按依赖关系的相反顺序）
    op.drop_index('idx_kuv_unit_version', table_name='knowledge_unit_versions')
    op.drop_index('idx_kuv_created_at', table_name='knowledge_unit_versions')
    op.drop_index('idx_kuv_version_number', table_name='knowledge_unit_versions')
    op.drop_index('idx_kuv_kb_id', table_name='knowledge_unit_versions')
    op.drop_index('idx_kuv_unit_id', table_name='knowledge_unit_versions')
    op.drop_index('idx_kuv_version_id', table_name='knowledge_unit_versions')
    op.drop_table('knowledge_unit_versions')
    
    op.drop_index('idx_vm_kb_status', table_name='vector_metadata')
    op.drop_index('idx_vm_status', table_name='vector_metadata')
    op.drop_index('idx_vm_model', table_name='vector_metadata')
    op.drop_index('idx_vm_kb_id', table_name='vector_metadata')
    op.drop_index('idx_vm_unit_id', table_name='vector_metadata')
    op.drop_index('idx_vm_vector_id', table_name='vector_metadata')
    op.drop_table('vector_metadata')
    
    op.drop_index('idx_ppr_kb_status', table_name='processing_pipeline_runs')
    op.drop_index('idx_ppr_created_at', table_name='processing_pipeline_runs')
    op.drop_index('idx_ppr_triggered_by', table_name='processing_pipeline_runs')
    op.drop_index('idx_ppr_status', table_name='processing_pipeline_runs')
    op.drop_index('idx_ppr_type', table_name='processing_pipeline_runs')
    op.drop_index('idx_ppr_kb_id', table_name='processing_pipeline_runs')
    op.drop_index('idx_ppr_run_id', table_name='processing_pipeline_runs')
    op.drop_table('processing_pipeline_runs')
    
    op.drop_index('idx_kua_kb_type', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_status', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_strength', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_type', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_target', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_source', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_kb_id', table_name='knowledge_unit_associations')
    op.drop_index('idx_kua_association_id', table_name='knowledge_unit_associations')
    op.drop_table('knowledge_unit_associations')
    
    op.drop_index('idx_uku_kb_status', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_kb_type', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_created_at', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_quality', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_vector_status', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_status', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_type', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_parent_id', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_doc_id', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_kb_id', table_name='unified_knowledge_units')
    op.drop_index('idx_uku_unit_id', table_name='unified_knowledge_units')
    op.drop_table('unified_knowledge_units')
