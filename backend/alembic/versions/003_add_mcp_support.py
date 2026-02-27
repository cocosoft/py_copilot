"""添加 MCP 支持相关数据表

Revision ID: 003_add_mcp_support
Revises: 002_add_file_upload_support
Create Date: 2026-02-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_mcp_support'
down_revision = '002_add_file_upload_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 添加 MCP 支持"""
    
    # 创建 MCP 服务端配置表
    op.create_table('mcp_server_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transport', sa.String(50), default='sse'),
        sa.Column('host', sa.String(255), default='127.0.0.1'),
        sa.Column('port', sa.Integer(), default=8008),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('auth_type', sa.String(50), default='none'),
        sa.Column('auth_config', sa.JSON(), nullable=True),
        sa.Column('exposed_modules', sa.JSON(), default=list),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mcp_server_user_id', 'mcp_server_configs', ['user_id'])
    op.create_index('idx_mcp_server_enabled', 'mcp_server_configs', ['enabled'])
    
    # 创建 MCP 客户端连接配置表
    op.create_table('mcp_client_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transport', sa.String(50), default='sse'),
        sa.Column('connection_url', sa.String(500), nullable=True),
        sa.Column('command', sa.String(500), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('auto_connect', sa.Boolean(), default=True),
        sa.Column('auth_config', sa.JSON(), nullable=True),
        sa.Column('tool_whitelist', sa.JSON(), nullable=True),
        sa.Column('tool_blacklist', sa.JSON(), nullable=True),
        sa.Column('last_connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), default='disconnected'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mcp_client_user_id', 'mcp_client_configs', ['user_id'])
    op.create_index('idx_mcp_client_status', 'mcp_client_configs', ['status'])
    op.create_index('idx_mcp_client_enabled', 'mcp_client_configs', ['enabled'])
    
    # 创建 MCP 工具映射表（缓存外部工具信息）
    op.create_table('mcp_tool_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_config_id', sa.Integer(), nullable=False),
        sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('local_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('input_schema', sa.JSON(), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('cached_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_config_id'], ['mcp_client_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_config_id', 'original_name', name='uq_client_tool_name')
    )
    op.create_index('idx_mcp_tool_mapping_client_id', 'mcp_tool_mappings', ['client_config_id'])
    op.create_index('idx_mcp_tool_mapping_enabled', 'mcp_tool_mappings', ['enabled'])
    
    # 创建 MCP 调用日志表
    op.create_table('mcp_call_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('direction', sa.String(20), nullable=False),
        sa.Column('connection_name', sa.String(255), nullable=True),
        sa.Column('tool_name', sa.String(255), nullable=True),
        sa.Column('request_data', sa.JSON(), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mcp_log_user_id', 'mcp_call_logs', ['user_id'])
    op.create_index('idx_mcp_log_direction', 'mcp_call_logs', ['direction'])
    op.create_index('idx_mcp_log_status', 'mcp_call_logs', ['status'])
    op.create_index('idx_mcp_log_created_at', 'mcp_call_logs', ['created_at'])
    
    print("数据库升级完成：已添加 MCP 支持相关数据表")


def downgrade() -> None:
    """降级数据库结构 - 删除 MCP 相关表"""
    
    # 删除 MCP 调用日志表
    op.drop_index('idx_mcp_log_created_at', table_name='mcp_call_logs')
    op.drop_index('idx_mcp_log_status', table_name='mcp_call_logs')
    op.drop_index('idx_mcp_log_direction', table_name='mcp_call_logs')
    op.drop_index('idx_mcp_log_user_id', table_name='mcp_call_logs')
    op.drop_table('mcp_call_logs')
    
    # 删除 MCP 工具映射表
    op.drop_index('idx_mcp_tool_mapping_enabled', table_name='mcp_tool_mappings')
    op.drop_index('idx_mcp_tool_mapping_client_id', table_name='mcp_tool_mappings')
    op.drop_table('mcp_tool_mappings')
    
    # 删除 MCP 客户端连接配置表
    op.drop_index('idx_mcp_client_enabled', table_name='mcp_client_configs')
    op.drop_index('idx_mcp_client_status', table_name='mcp_client_configs')
    op.drop_index('idx_mcp_client_user_id', table_name='mcp_client_configs')
    op.drop_table('mcp_client_configs')
    
    # 删除 MCP 服务端配置表
    op.drop_index('idx_mcp_server_enabled', table_name='mcp_server_configs')
    op.drop_index('idx_mcp_server_user_id', table_name='mcp_server_configs')
    op.drop_table('mcp_server_configs')
    
    print("数据库降级完成：已删除 MCP 相关数据表")
