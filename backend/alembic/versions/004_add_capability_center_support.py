"""添加能力中心支持

Revision ID: 004_add_capability_center_support
Revises: 003_add_mcp_support
Create Date: 2026-02-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '004_add_capability_center_support'
down_revision = '003_add_mcp_support'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """检查列是否已存在"""
    conn = op.get_bind()
    insp = inspect(conn)
    columns = insp.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)


def table_exists(table_name):
    """检查表是否已存在"""
    conn = op.get_bind()
    insp = inspect(conn)
    return table_name in insp.get_table_names()


def index_exists(table_name, index_name):
    """检查索引是否已存在"""
    conn = op.get_bind()
    insp = inspect(conn)
    indexes = insp.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade() -> None:
    """升级数据库结构 - 添加能力中心支持"""
    
    # ==========================================
    # 1. 扩展 skills 表 - 添加官方能力标识
    # ==========================================
    if not column_exists('skills', 'is_official'):
        op.add_column('skills', sa.Column('is_official', sa.Boolean(), default=False))
    if not column_exists('skills', 'is_builtin'):
        op.add_column('skills', sa.Column('is_builtin', sa.Boolean(), default=False))
    if not column_exists('skills', 'official_badge'):
        op.add_column('skills', sa.Column('official_badge', sa.String(50), nullable=True))
    if not column_exists('skills', 'is_protected'):
        op.add_column('skills', sa.Column('is_protected', sa.Boolean(), default=False))
    if not column_exists('skills', 'allow_disable'):
        op.add_column('skills', sa.Column('allow_disable', sa.Boolean(), default=True))
    if not column_exists('skills', 'allow_edit'):
        op.add_column('skills', sa.Column('allow_edit', sa.Boolean(), default=True))
    if not column_exists('skills', 'min_app_version'):
        op.add_column('skills', sa.Column('min_app_version', sa.String(50), nullable=True))
    if not column_exists('skills', 'update_mode'):
        op.add_column('skills', sa.Column('update_mode', sa.String(20), default='manual'))
    
    # 创建索引
    if not index_exists('skills', 'idx_skills_official'):
        op.create_index('idx_skills_official', 'skills', ['is_official'])
    if not index_exists('skills', 'idx_skills_builtin'):
        op.create_index('idx_skills_builtin', 'skills', ['is_builtin'])
    if not index_exists('skills', 'idx_skills_protected'):
        op.create_index('idx_skills_protected', 'skills', ['is_protected'])
    
    # ==========================================
    # 2. 创建 tools 数据库表
    # ==========================================
    if not table_exists('tools'):
        op.create_table('tools',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('display_name', sa.String(200), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(50), default='general'),
            sa.Column('version', sa.String(50), default='1.0.0'),
            sa.Column('icon', sa.String(50), default='🔧'),
            sa.Column('tags', sa.JSON(), default=list),
            
            # 官方能力标识
            sa.Column('source', sa.String(50), default='user'),
            sa.Column('is_official', sa.Boolean(), default=False),
            sa.Column('is_builtin', sa.Boolean(), default=False),
            sa.Column('official_badge', sa.String(50), nullable=True),
            sa.Column('is_system', sa.Boolean(), default=False),
            sa.Column('is_protected', sa.Boolean(), default=False),
            sa.Column('allow_disable', sa.Boolean(), default=True),
            sa.Column('allow_edit', sa.Boolean(), default=True),
            
            # 版本管理
            sa.Column('min_app_version', sa.String(50), nullable=True),
            sa.Column('update_mode', sa.String(20), default='manual'),
            
            # 工具配置
            sa.Column('tool_type', sa.String(50), default='local'),  # local/mcp/official
            sa.Column('handler_module', sa.String(200), nullable=True),  # 处理模块路径
            sa.Column('handler_class', sa.String(100), nullable=True),   # 处理类名
            sa.Column('parameters_schema', sa.JSON(), nullable=True),
            sa.Column('config', sa.JSON(), default=dict),
            
            # MCP关联 (不使用外键约束，SQLite兼容)
            sa.Column('mcp_client_config_id', sa.Integer(), nullable=True),
            sa.Column('mcp_tool_name', sa.String(255), nullable=True),
            
            # 状态
            sa.Column('status', sa.String(20), default='disabled'),
            sa.Column('is_active', sa.Boolean(), default=True),
            
            # 元数据
            sa.Column('author', sa.String(200), nullable=True),
            sa.Column('documentation_url', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('usage_count', sa.Integer(), default=0),
            
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name', name='uq_tool_name')
        )
        
        # 创建tools表索引
        op.create_index('idx_tools_category', 'tools', ['category'])
        op.create_index('idx_tools_status', 'tools', ['status'])
        op.create_index('idx_tools_official', 'tools', ['is_official'])
        op.create_index('idx_tools_type', 'tools', ['tool_type'])
        op.create_index('idx_tools_mcp_client', 'tools', ['mcp_client_config_id'])
    
    # ==========================================
    # 3. 创建 agent_tool_associations 关联表
    # ==========================================
    if not table_exists('agent_tool_associations'):
        op.create_table('agent_tool_associations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('agent_id', sa.Integer(), nullable=True),
            sa.Column('tool_id', sa.Integer(), nullable=True),
            sa.Column('priority', sa.Integer(), default=0),
            sa.Column('enabled', sa.Boolean(), default=True),
            sa.Column('config', sa.JSON(), default=dict),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
            
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('agent_id', 'tool_id', name='uq_agent_tool')
        )
        
        op.create_index('idx_agent_tool_agent', 'agent_tool_associations', ['agent_id'])
        op.create_index('idx_agent_tool_tool', 'agent_tool_associations', ['tool_id'])
    
    # ==========================================
    # 4. 扩展 agents 表 - 支持智能体分类
    # ==========================================
    if not column_exists('agents', 'agent_type'):
        op.add_column('agents', sa.Column('agent_type', sa.String(50), default='single'))
    if not column_exists('agents', 'primary_capability_id'):
        op.add_column('agents', sa.Column('primary_capability_id', sa.Integer(), nullable=True))
    if not column_exists('agents', 'primary_capability_type'):
        op.add_column('agents', sa.Column('primary_capability_type', sa.String(50), nullable=True))
    if not column_exists('agents', 'capability_orchestration'):
        op.add_column('agents', sa.Column('capability_orchestration', sa.JSON(), default=dict))
    if not column_exists('agents', 'is_official'):
        op.add_column('agents', sa.Column('is_official', sa.Boolean(), default=False))
    if not column_exists('agents', 'is_template'):
        op.add_column('agents', sa.Column('is_template', sa.Boolean(), default=False))
    if not column_exists('agents', 'template_category'):
        op.add_column('agents', sa.Column('template_category', sa.String(50), nullable=True))
    
    # 创建索引
    if not index_exists('agents', 'idx_agents_type'):
        op.create_index('idx_agents_type', 'agents', ['agent_type'])
    if not index_exists('agents', 'idx_agents_official'):
        op.create_index('idx_agents_official', 'agents', ['is_official'])
    if not index_exists('agents', 'idx_agents_template'):
        op.create_index('idx_agents_template', 'agents', ['is_template'])
    
    # ==========================================
    # 5. 创建官方能力初始化数据
    # ==========================================
    _create_official_capabilities()


def downgrade() -> None:
    """降级数据库结构"""
    
    # 删除agents表新增字段
    if index_exists('agents', 'idx_agents_template'):
        op.drop_index('idx_agents_template', table_name='agents')
    if index_exists('agents', 'idx_agents_official'):
        op.drop_index('idx_agents_official', table_name='agents')
    if index_exists('agents', 'idx_agents_type'):
        op.drop_index('idx_agents_type', table_name='agents')
        
    if column_exists('agents', 'template_category'):
        op.drop_column('agents', 'template_category')
    if column_exists('agents', 'is_template'):
        op.drop_column('agents', 'is_template')
    if column_exists('agents', 'is_official'):
        op.drop_column('agents', 'is_official')
    if column_exists('agents', 'capability_orchestration'):
        op.drop_column('agents', 'capability_orchestration')
    if column_exists('agents', 'primary_capability_type'):
        op.drop_column('agents', 'primary_capability_type')
    if column_exists('agents', 'primary_capability_id'):
        op.drop_column('agents', 'primary_capability_id')
    if column_exists('agents', 'agent_type'):
        op.drop_column('agents', 'agent_type')
    
    # 删除关联表
    if table_exists('agent_tool_associations'):
        if index_exists('agent_tool_associations', 'idx_agent_tool_tool'):
            op.drop_index('idx_agent_tool_tool', table_name='agent_tool_associations')
        if index_exists('agent_tool_associations', 'idx_agent_tool_agent'):
            op.drop_index('idx_agent_tool_agent', table_name='agent_tool_associations')
        op.drop_table('agent_tool_associations')
    
    # 删除tools表
    if table_exists('tools'):
        if index_exists('tools', 'idx_tools_mcp_client'):
            op.drop_index('idx_tools_mcp_client', table_name='tools')
        if index_exists('tools', 'idx_tools_type'):
            op.drop_index('idx_tools_type', table_name='tools')
        if index_exists('tools', 'idx_tools_official'):
            op.drop_index('idx_tools_official', table_name='tools')
        if index_exists('tools', 'idx_tools_status'):
            op.drop_index('idx_tools_status', table_name='tools')
        if index_exists('tools', 'idx_tools_category'):
            op.drop_index('idx_tools_category', table_name='tools')
        op.drop_table('tools')
    
    # 删除skills表新增字段
    if index_exists('skills', 'idx_skills_protected'):
        op.drop_index('idx_skills_protected', table_name='skills')
    if index_exists('skills', 'idx_skills_builtin'):
        op.drop_index('idx_skills_builtin', table_name='skills')
    if index_exists('skills', 'idx_skills_official'):
        op.drop_index('idx_skills_official', table_name='skills')
        
    if column_exists('skills', 'update_mode'):
        op.drop_column('skills', 'update_mode')
    if column_exists('skills', 'min_app_version'):
        op.drop_column('skills', 'min_app_version')
    if column_exists('skills', 'allow_edit'):
        op.drop_column('skills', 'allow_edit')
    if column_exists('skills', 'allow_disable'):
        op.drop_column('skills', 'allow_disable')
    if column_exists('skills', 'is_protected'):
        op.drop_column('skills', 'is_protected')
    if column_exists('skills', 'official_badge'):
        op.drop_column('skills', 'official_badge')
    if column_exists('skills', 'is_builtin'):
        op.drop_column('skills', 'is_builtin')
    if column_exists('skills', 'is_official'):
        op.drop_column('skills', 'is_official')


def _create_official_capabilities() -> None:
    """创建官方能力初始化数据"""
    
    # 获取数据库连接
    conn = op.get_bind()
    
    # 检查是否已有数据
    result = conn.execute(sa.text("SELECT COUNT(*) FROM tools")).scalar()
    if result > 0:
        print("Tools表已有数据，跳过初始化")
        return
    
    # 官方工具初始化数据
    official_tools = [
        {
            'name': 'file_reader',
            'display_name': '文件读取工具',
            'description': '读取本地文件内容，支持多种格式（txt, md, pdf, docx等）',
            'category': 'file',
            'version': '1.0.0',
            'icon': '📄',
            'tags': '["文件操作", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': False,
            'tool_type': 'official',
            'handler_module': 'app.tools.official.file_reader',
            'handler_class': 'FileReaderTool',
            'status': 'active',
            'is_active': True,
            'author': 'System'
        },
        {
            'name': 'web_search',
            'display_name': '网络搜索工具',
            'description': '执行网络搜索，支持Google/Bing/Baidu等多个搜索引擎',
            'category': 'search',
            'version': '1.0.0',
            'icon': '🔍',
            'tags': '["搜索", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': True,
            'tool_type': 'official',
            'handler_module': 'app.tools.official.web_search',
            'handler_class': 'WebSearchTool',
            'status': 'active',
            'is_active': True,
            'author': 'System'
        },
        {
            'name': 'knowledge_retrieval',
            'display_name': '知识库检索工具',
            'description': '从知识库中检索相关信息，支持语义搜索和关键词搜索',
            'category': 'knowledge',
            'version': '1.0.0',
            'icon': '📚',
            'tags': '["知识库", "检索", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': True,
            'tool_type': 'official',
            'handler_module': 'app.tools.official.knowledge_retrieval',
            'handler_class': 'KnowledgeRetrievalTool',
            'status': 'active',
            'is_active': True,
            'author': 'System'
        },
        {
            'name': 'calculator',
            'display_name': '计算器工具',
            'description': '执行数学计算，支持复杂表达式',
            'category': 'math',
            'version': '1.0.0',
            'icon': '🧮',
            'tags': '["数学", "计算", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': False,
            'tool_type': 'official',
            'handler_module': 'app.tools.official.calculator',
            'handler_class': 'CalculatorTool',
            'status': 'active',
            'is_active': True,
            'author': 'System'
        },
        {
            'name': 'datetime_tool',
            'display_name': '时间日期工具',
            'description': '获取当前时间、日期计算、时区转换',
            'category': 'datetime',
            'version': '1.0.0',
            'icon': '📅',
            'tags': '["时间", "日期", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': False,
            'tool_type': 'official',
            'handler_module': 'app.tools.official.datetime_tool',
            'handler_class': 'DateTimeTool',
            'status': 'active',
            'is_active': True,
            'author': 'System'
        }
    ]
    
    # 插入官方工具数据
    for tool in official_tools:
        columns = ', '.join(tool.keys())
        placeholders = ', '.join([f':{k}' for k in tool.keys()])
        conn.execute(sa.text(f"INSERT INTO tools ({columns}) VALUES ({placeholders})"), tool)
    
    # 检查是否已有官方技能数据
    result = conn.execute(sa.text("SELECT COUNT(*) FROM skills WHERE is_official = 1")).scalar()
    if result > 0:
        print("Skills表已有官方数据，跳过初始化")
        return
    
    # 官方技能初始化数据
    official_skills = [
        {
            'name': 'code_review_assistant',
            'display_name': '代码审查助手',
            'description': '专业的代码审查技能，帮助发现代码问题和改进建议',
            'content': '你是一个专业的代码审查助手。请仔细审查用户提供的代码，从以下方面进行分析：\n1. 代码规范和风格\n2. 潜在的bug和安全问题\n3. 性能优化建议\n4. 可读性和可维护性\n5. 最佳实践遵循情况',
            'version': '1.0.0',
            'tags': '["代码", "审查", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': False,
            'status': 'active',
            'author': 'System'
        },
        {
            'name': 'translation_expert',
            'display_name': '翻译专家',
            'description': '专业的多语言翻译技能，支持多种语言之间的准确翻译',
            'content': '你是一个专业的翻译专家，擅长多种语言之间的准确翻译。请遵循以下原则：\n1. 保持原文的语气和风格\n2. 准确传达专业术语\n3. 确保译文通顺自然\n4. 保留原文的格式和结构',
            'version': '1.0.0',
            'tags': '["翻译", "语言", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': False,
            'status': 'active',
            'author': 'System'
        },
        {
            'name': 'writing_assistant',
            'display_name': '文案生成器',
            'description': '专业的文案创作技能，帮助生成各类文案内容',
            'content': '你是一个专业的文案创作助手。请根据用户需求生成高质量的文案内容，包括：\n1. 标题和开头吸引眼球\n2. 内容结构清晰\n3. 语言风格符合目标受众\n4. 适当使用修辞手法',
            'version': '1.0.0',
            'tags': '["写作", "文案", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': False,
            'status': 'active',
            'author': 'System'
        },
        {
            'name': 'document_summary',
            'display_name': '文档总结助手',
            'description': '专业的文档总结技能，帮助提取文档核心内容',
            'content': '你是一个专业的文档总结助手。请仔细阅读文档内容，提取核心信息：\n1. 识别文档的主要主题和目的\n2. 提取关键观点和结论\n3. 总结重要细节和数据\n4. 保持客观和准确',
            'version': '1.0.0',
            'tags': '["总结", "文档", "官方"]',
            'source': 'official',
            'is_official': True,
            'is_builtin': True,
            'official_badge': '🏛️',
            'is_system': False,
            'is_protected': True,
            'allow_disable': True,
            'allow_edit': False,
            'status': 'active',
            'author': 'System'
        }
    ]
    
    # 插入官方技能数据
    for skill in official_skills:
        columns = ', '.join(skill.keys())
        placeholders = ', '.join([f':{k}' for k in skill.keys()])
        conn.execute(sa.text(f"INSERT INTO skills ({columns}) VALUES ({placeholders})"), skill)
