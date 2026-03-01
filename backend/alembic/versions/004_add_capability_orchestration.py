"""添加能力编排支持相关数据表

Revision ID: 004_add_capability_orchestration
Revises: 003_add_mcp_support
Create Date: 2026-03-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_capability_orchestration'
down_revision = '003_add_mcp_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 添加能力编排支持"""
    
    # 创建能力编排日志表
    op.create_table('capability_orchestration_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.String(100), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('intent_type', sa.String(100), nullable=True),
        sa.Column('intent_confidence', sa.Float(), nullable=True),
        sa.Column('complexity_level', sa.String(50), nullable=True),
        sa.Column('execution_plan', sa.JSON(), default=dict),
        sa.Column('used_capabilities', sa.JSON(), default=list),
        sa.Column('execution_steps', sa.JSON(), default=list),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('execution_id')
    )
    
    # 创建索引
    op.create_index('idx_orchestration_execution_id', 'capability_orchestration_logs', ['execution_id'])
    op.create_index('idx_orchestration_user', 'capability_orchestration_logs', ['user_id', 'created_at'])
    op.create_index('idx_orchestration_agent', 'capability_orchestration_logs', ['agent_id', 'created_at'])
    op.create_index('idx_orchestration_intent', 'capability_orchestration_logs', ['intent_type', 'success'])
    
    # 创建能力执行日志表
    op.create_table('capability_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('orchestration_id', sa.Integer(), nullable=True),
        sa.Column('capability_name', sa.String(100), nullable=False),
        sa.Column('capability_type', sa.String(50), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['orchestration_id'], ['capability_orchestration_logs.id'], ondelete='SET NULL')
    )
    
    # 创建索引
    op.create_index('idx_execution_capability', 'capability_execution_logs', ['capability_name', 'created_at'])
    op.create_index('idx_execution_orchestration', 'capability_execution_logs', ['orchestration_id', 'created_at'])
    op.create_index('idx_execution_success', 'capability_execution_logs', ['capability_name', 'success'])
    
    # 创建能力使用统计表
    op.create_table('capability_usage_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('capability_name', sa.String(100), nullable=False),
        sa.Column('total_calls', sa.Integer(), default=0),
        sa.Column('successful_calls', sa.Integer(), default=0),
        sa.Column('failed_calls', sa.Integer(), default=0),
        sa.Column('total_execution_time_ms', sa.BigInteger(), default=0),
        sa.Column('average_execution_time_ms', sa.Float(), default=0.0),
        sa.Column('success_rate', sa.Float(), default=1.0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('capability_name')
    )
    
    # 创建索引
    op.create_index('idx_stats_capability', 'capability_usage_stats', ['capability_name'])
    
    # 创建能力依赖关系表
    op.create_table('capability_dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('capability_name', sa.String(100), nullable=False),
        sa.Column('depends_on', sa.String(100), nullable=False),
        sa.Column('dependency_type', sa.String(50), default='required'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('capability_name', 'depends_on', name='idx_dependency_unique')
    )
    
    # 创建索引
    op.create_index('idx_dependency_capability', 'capability_dependencies', ['capability_name'])
    op.create_index('idx_dependency_depends_on', 'capability_dependencies', ['depends_on'])
    
    # 创建能力结果缓存表
    op.create_table('capability_cache_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False),
        sa.Column('capability_name', sa.String(100), nullable=False),
        sa.Column('input_hash', sa.String(64), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hit_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )
    
    # 创建索引
    op.create_index('idx_cache_capability', 'capability_cache_entries', ['capability_name', 'created_at'])
    op.create_index('idx_cache_expires', 'capability_cache_entries', ['expires_at'])
    
    # 创建能力索引表
    op.create_table('capability_index_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('capability_name', sa.String(100), nullable=False),
        sa.Column('name_index', sa.Text(), nullable=True),
        sa.Column('description_index', sa.Text(), nullable=True),
        sa.Column('tags_index', sa.Text(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('capability_name')
    )
    
    # 创建编排配置表
    op.create_table('orchestration_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(100), nullable=False),
        sa.Column('config_value', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key')
    )
    
    # 插入默认配置
    op.bulk_insert('orchestration_configs', [
        {
            'config_key': 'max_parallel_executions',
            'config_value': 5,
            'description': '最大并行执行数'
        },
        {
            'config_key': 'default_timeout_seconds',
            'config_value': 30,
            'description': '默认超时时间（秒）'
        },
        {
            'config_key': 'max_retries',
            'config_value': 3,
            'description': '最大重试次数'
        },
        {
            'config_key': 'cache_ttl_seconds',
            'config_value': 300,
            'description': '缓存过期时间（秒）'
        }
    ])


def downgrade() -> None:
    """降级数据库结构 - 删除能力编排相关表"""
    
    # 删除表（按依赖顺序）
    op.drop_table('orchestration_configs')
    op.drop_table('capability_index_entries')
    op.drop_table('capability_cache_entries')
    op.drop_table('capability_dependencies')
    op.drop_table('capability_usage_stats')
    op.drop_table('capability_execution_logs')
    op.drop_table('capability_orchestration_logs')
