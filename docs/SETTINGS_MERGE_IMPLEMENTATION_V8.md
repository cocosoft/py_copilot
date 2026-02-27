# 设置功能合并实施方案 V8（可执行版）

## 文档信息

- **版本**: V8.0
- **日期**: 2026-02-27
- **状态**: 可执行
- **依赖文档**: SETTINGS_MERGE_PROPOSAL_V8.md

---

## 1. 实施概述

### 1.1 实施目标

基于 SETTINGS_MERGE_PROPOSAL_V8.md 方案，执行以下核心任务：

1. **数据库迁移**: 扩展现有模型支持官方能力和智能体分类
2. **功能整合**: 将搜索管理、工具页面整合到能力中心
3. **API开发**: 实现能力中心相关接口
4. **前端适配**: 更新UI支持新的能力中心

### 1.2 技术栈确认

- **后端**: Python 3.11 + FastAPI + SQLAlchemy + Alembic
- **数据库**: SQLite (当前) / PostgreSQL (生产)
- **前端**: Vue.js (基于现有项目结构推断)
- **迁移工具**: Alembic

### 1.3 实施阶段

```
阶段1: 数据库迁移 (预计2-3天)
阶段2: 后端API开发 (预计3-4天)
阶段3: 前端适配 (预计3-4天)
阶段4: 功能迁移与测试 (预计2-3天)
阶段5: 废弃功能清理 (预计1天)
```

---

## 2. 阶段1: 数据库迁移

### 2.1 创建Alembic迁移脚本

**文件路径**: `backend/alembic/versions/004_add_capability_center_support.py`

```python
"""添加能力中心支持

Revision ID: 004_add_capability_center_support
Revises: 003_add_mcp_support
Create Date: 2026-02-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_capability_center_support'
down_revision = '003_add_mcp_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 添加能力中心支持"""
    
    # ==========================================
    # 1. 扩展 skills 表 - 添加官方能力标识
    # ==========================================
    op.add_column('skills', sa.Column('is_official', sa.Boolean(), default=False))
    op.add_column('skills', sa.Column('is_builtin', sa.Boolean(), default=False))
    op.add_column('skills', sa.Column('official_badge', sa.String(50), nullable=True))
    op.add_column('skills', sa.Column('is_protected', sa.Boolean(), default=False))
    op.add_column('skills', sa.Column('allow_disable', sa.Boolean(), default=True))
    op.add_column('skills', sa.Column('allow_edit', sa.Boolean(), default=True))
    op.add_column('skills', sa.Column('min_app_version', sa.String(50), nullable=True))
    op.add_column('skills', sa.Column('update_mode', sa.String(20), default='manual'))
    
    # 创建索引
    op.create_index('idx_skills_official', 'skills', ['is_official'])
    op.create_index('idx_skills_builtin', 'skills', ['is_builtin'])
    op.create_index('idx_skills_protected', 'skills', ['is_protected'])
    
    # ==========================================
    # 2. 创建 tools 数据库表
    # ==========================================
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
        
        # MCP关联
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
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_tools_mcp_client',
        'tools', 'mcp_client_configs',
        ['mcp_client_config_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # ==========================================
    # 3. 创建 agent_tool_associations 关联表
    # ==========================================
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
        sa.UniqueConstraint('agent_id', 'tool_id', name='uq_agent_tool'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='SET NULL')
    )
    
    op.create_index('idx_agent_tool_agent', 'agent_tool_associations', ['agent_id'])
    op.create_index('idx_agent_tool_tool', 'agent_tool_associations', ['tool_id'])
    
    # ==========================================
    # 4. 扩展 agents 表 - 支持智能体分类
    # ==========================================
    op.add_column('agents', sa.Column('agent_type', sa.String(50), default='single'))
    op.add_column('agents', sa.Column('primary_capability_id', sa.Integer(), nullable=True))
    op.add_column('agents', sa.Column('primary_capability_type', sa.String(50), nullable=True))
    op.add_column('agents', sa.Column('capability_orchestration', sa.JSON(), default=dict))
    op.add_column('agents', sa.Column('is_official', sa.Boolean(), default=False))
    op.add_column('agents', sa.Column('is_template', sa.Boolean(), default=False))
    op.add_column('agents', sa.Column('template_category', sa.String(50), nullable=True))
    
    # 创建索引
    op.create_index('idx_agents_type', 'agents', ['agent_type'])
    op.create_index('idx_agents_official', 'agents', ['is_official'])
    op.create_index('idx_agents_template', 'agents', ['is_template'])
    
    # ==========================================
    # 5. 创建官方能力初始化数据
    # ==========================================
    _create_official_capabilities()


def downgrade() -> None:
    """降级数据库结构"""
    
    # 删除agents表新增字段
    op.drop_index('idx_agents_template', table_name='agents')
    op.drop_index('idx_agents_official', table_name='agents')
    op.drop_index('idx_agents_type', table_name='agents')
    op.drop_column('agents', 'template_category')
    op.drop_column('agents', 'is_template')
    op.drop_column('agents', 'is_official')
    op.drop_column('agents', 'capability_orchestration')
    op.drop_column('agents', 'primary_capability_type')
    op.drop_column('agents', 'primary_capability_id')
    op.drop_column('agents', 'agent_type')
    
    # 删除关联表
    op.drop_index('idx_agent_tool_tool', table_name='agent_tool_associations')
    op.drop_index('idx_agent_tool_agent', table_name='agent_tool_associations')
    op.drop_table('agent_tool_associations')
    
    # 删除tools表
    op.drop_index('idx_tools_mcp_client', table_name='tools')
    op.drop_index('idx_tools_type', table_name='tools')
    op.drop_index('idx_tools_official', table_name='tools')
    op.drop_index('idx_tools_status', table_name='tools')
    op.drop_index('idx_tools_category', table_name='tools')
    op.drop_table('tools')
    
    # 删除skills表新增字段
    op.drop_index('idx_skills_protected', table_name='skills')
    op.drop_index('idx_skills_builtin', table_name='skills')
    op.drop_index('idx_skills_official', table_name='skills')
    op.drop_column('skills', 'update_mode')
    op.drop_column('skills', 'min_app_version')
    op.drop_column('skills', 'allow_edit')
    op.drop_column('skills', 'allow_disable')
    op.drop_column('skills', 'is_protected')
    op.drop_column('skills', 'official_badge')
    op.drop_column('skills', 'is_builtin')
    op.drop_column('skills', 'is_official')


def _create_official_capabilities() -> None:
    """创建官方能力初始化数据"""
    
    # 获取数据库连接
    conn = op.get_bind()
    
    # 官方工具初始化数据
    official_tools = [
        {
            'name': 'file_reader',
            'display_name': '文件读取工具',
            'description': '读取本地文件内容，支持多种格式（txt, md, pdf, docx等）',
            'category': 'file',
            'version': '1.0.0',
            'icon': '📄',
            'tags': ['文件操作', '官方'],
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
            'tags': ['搜索', '官方'],
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
            'tags': ['知识库', '检索', '官方'],
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
            'tags': ['数学', '计算', '官方'],
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
            'tags': ['时间', '日期', '官方'],
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
    
    # 官方技能初始化数据
    official_skills = [
        {
            'name': 'code_review_assistant',
            'display_name': '代码审查助手',
            'description': '专业的代码审查技能，帮助发现代码问题和改进建议',
            'content': '你是一个专业的代码审查助手。请仔细审查用户提供的代码，从以下方面进行分析：\n1. 代码规范和风格\n2. 潜在的bug和安全问题\n3. 性能优化建议\n4. 可读性和可维护性\n5. 最佳实践遵循情况',
            'version': '1.0.0',
            'tags': ['代码', '审查', '官方'],
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
            'tags': ['翻译', '语言', '官方'],
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
            'tags': ['写作', '文案', '官方'],
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
            'tags': ['总结', '文档', '官方'],
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
```

### 2.2 执行迁移命令

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
venv\Scripts\activate

# 执行数据库迁移
alembic upgrade head

# 验证迁移结果
alembic current
```

### 2.3 验证迁移

```python
# 验证脚本: backend/scripts/verify_migration.py
"""验证数据库迁移结果"""

from app.core.database import SessionLocal
from app.models.skill import Skill
from app.models.tool import Tool
from app.models.agent import Agent

def verify_migration():
    db = SessionLocal()
    try:
        # 验证skills表扩展
        official_skills = db.query(Skill).filter(Skill.is_official == True).all()
        print(f"✓ 官方技能数量: {len(official_skills)}")
        
        # 验证tools表创建
        tools_count = db.query(Tool).count()
        print(f"✓ 工具总数: {tools_count}")
        
        official_tools = db.query(Tool).filter(Tool.is_official == True).all()
        print(f"✓ 官方工具数量: {len(official_tools)}")
        
        # 验证agents表扩展
        agents_with_type = db.query(Agent).filter(Agent.agent_type.isnot(None)).count()
        print(f"✓ 已分类智能体数量: {agents_with_type}")
        
        print("\n✅ 数据库迁移验证通过")
        return True
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    verify_migration()
```

---

## 3. 阶段2: 后端API开发

### 3.1 更新数据模型

**文件**: `backend/app/models/tool.py` (新建)

```python
"""工具数据库模型"""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Tool(Base):
    """工具数据库模型 - 支持官方能力和用户自定义"""
    
    __tablename__ = "tools"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200))
    description = Column(Text)
    category = Column(String(50), default="general", index=True)
    version = Column(String(50), default="1.0.0")
    icon = Column(String(50), default="🔧")
    tags = Column(JSON, default=list)
    
    # 官方能力标识
    source = Column(String(50), default="user")  # official/marketplace/user/mcp
    is_official = Column(Boolean, default=False, index=True)
    is_builtin = Column(Boolean, default=False)
    official_badge = Column(String(50))
    is_system = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)
    allow_disable = Column(Boolean, default=True)
    allow_edit = Column(Boolean, default=True)
    
    # 版本管理
    min_app_version = Column(String(50))
    update_mode = Column(String(20), default="manual")
    
    # 工具配置
    tool_type = Column(String(50), default="local")  # local/mcp/official
    handler_module = Column(String(200))
    handler_class = Column(String(100))
    parameters_schema = Column(JSON)
    config = Column(JSON, default=dict)
    
    # MCP关联
    mcp_client_config_id = Column(Integer, ForeignKey("mcp_client_configs.id", ondelete="SET NULL"))
    mcp_tool_name = Column(String(255))
    
    # 状态
    status = Column(String(20), default="disabled", index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # 元数据
    author = Column(String(200))
    documentation_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    
    # 关系
    agent_associations = relationship("AgentToolAssociation", back_populates="tool")
    mcp_client = relationship("MCPClientConfigModel", backref="tools")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', official={self.is_official})>"


class AgentToolAssociation(Base):
    """智能体与工具关联表"""
    
    __tablename__ = "agent_tool_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"))
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="SET NULL"))
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    agent = relationship("Agent", backref="tool_associations")
    tool = relationship("Tool", back_populates="agent_associations")
    
    __table_args__ = (
        # 确保一个智能体不会重复关联同一个工具
        {'sqlite_autoincrement': True},
    )
```

**文件**: `backend/app/models/__init__.py` 更新

```python
# 添加Tool模型导入
from app.models.tool import Tool, AgentToolAssociation
```

### 3.2 创建能力中心API

**文件**: `backend/app/api/v1/capability_center.py` (新建)

```python
"""能力中心API - 统一管理能力（工具、技能、MCP）"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.tool import Tool
from app.models.skill import Skill
from app.models.agent import Agent
from app.models.mcp import MCPClientConfigModel
from app.api.deps import get_current_user

router = APIRouter(prefix="/capability-center", tags=["能力中心"])


# ==================== 请求/响应模型 ====================

class CapabilityListItem(BaseModel):
    """能力列表项"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    type: str  # tool/skill/mcp
    category: str
    icon: str
    tags: List[str]
    is_official: bool
    is_builtin: bool
    official_badge: Optional[str]
    is_protected: bool
    allow_disable: bool
    allow_edit: bool
    status: str
    is_active: bool
    author: Optional[str]
    version: str
    usage_count: int
    
    class Config:
        from_attributes = True


class CapabilityFilterRequest(BaseModel):
    """能力筛选请求"""
    type: Optional[str] = None  # tool/skill/mcp/all
    category: Optional[str] = None
    source: Optional[str] = None  # official/marketplace/user
    status: Optional[str] = None
    search: Optional[str] = None
    tags: Optional[List[str]] = None


class CapabilityToggleRequest(BaseModel):
    """能力启用/禁用请求"""
    enabled: bool


class CapabilityConfigUpdateRequest(BaseModel):
    """能力配置更新请求"""
    config: Dict[str, Any]


class AgentCapabilityAssignment(BaseModel):
    """智能体能力分配"""
    agent_id: int
    capability_id: int
    capability_type: str  # tool/skill
    priority: int = 0
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


# ==================== API端点 ====================

@router.get("/capabilities", response_model=Dict[str, Any])
async def list_capabilities(
    type: Optional[str] = Query(None, description="类型筛选: tool/skill/mcp/all"),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None, description="来源: official/marketplace/user"),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="标签，逗号分隔"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取能力列表（统一查询工具、技能、MCP）
    
    支持筛选、搜索、分页
    """
    try:
        results = []
        
        # 解析标签
        tag_list = tags.split(",") if tags else []
        
        # 查询工具
        if type in (None, "all", "tool"):
            tool_query = db.query(Tool)
            
            if source:
                tool_query = tool_query.filter(Tool.source == source)
            if category:
                tool_query = tool_query.filter(Tool.category == category)
            if status:
                tool_query = tool_query.filter(Tool.status == status)
            if search:
                tool_query = tool_query.filter(
                    (Tool.name.ilike(f"%{search}%")) |
                    (Tool.display_name.ilike(f"%{search}%")) |
                    (Tool.description.ilike(f"%{search}%"))
                )
            
            tools = tool_query.all()
            for tool in tools:
                results.append(CapabilityListItem(
                    id=tool.id,
                    name=tool.name,
                    display_name=tool.display_name or tool.name,
                    description=tool.description,
                    type="tool",
                    category=tool.category,
                    icon=tool.icon,
                    tags=tool.tags or [],
                    is_official=tool.is_official,
                    is_builtin=tool.is_builtin,
                    official_badge=tool.official_badge,
                    is_protected=tool.is_protected,
                    allow_disable=tool.allow_disable,
                    allow_edit=tool.allow_edit,
                    status=tool.status,
                    is_active=tool.is_active,
                    author=tool.author,
                    version=tool.version,
                    usage_count=tool.usage_count
                ))
        
        # 查询技能
        if type in (None, "all", "skill"):
            skill_query = db.query(Skill)
            
            if source:
                skill_query = skill_query.filter(Skill.source == source)
            if status:
                skill_query = skill_query.filter(Skill.status == status)
            if search:
                skill_query = skill_query.filter(
                    (Skill.name.ilike(f"%{search}%")) |
                    (Skill.display_name.ilike(f"%{search}%")) |
                    (Skill.description.ilike(f"%{search}%"))
                )
            
            skills = skill_query.all()
            for skill in skills:
                results.append(CapabilityListItem(
                    id=skill.id,
                    name=skill.name,
                    display_name=skill.display_name or skill.name,
                    description=skill.description,
                    type="skill",
                    category="skill",
                    icon=skill.icon or "📝",
                    tags=skill.tags or [],
                    is_official=skill.is_official or False,
                    is_builtin=skill.is_builtin or False,
                    official_badge=skill.official_badge,
                    is_protected=skill.is_protected or False,
                    allow_disable=skill.allow_disable if hasattr(skill, 'allow_disable') else True,
                    allow_edit=skill.allow_edit if hasattr(skill, 'allow_edit') else True,
                    status=skill.status,
                    is_active=skill.status == "active",
                    author=skill.author,
                    version=skill.version,
                    usage_count=skill.usage_count or 0
                ))
        
        # 分页
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = results[start:end]
        
        return {
            "success": True,
            "data": {
                "items": [item.model_dump() for item in paginated_results],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取能力列表失败: {str(e)}"
        )


@router.get("/capabilities/categories")
async def get_capability_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取能力分类列表"""
    try:
        # 工具分类
        tool_categories = db.query(Tool.category).distinct().all()
        
        categories = {
            "tool": [cat[0] for cat in tool_categories if cat[0]],
            "skill": ["skill"],
            "all": list(set([cat[0] for cat in tool_categories if cat[0]] + ["skill"]))
        }
        
        return {
            "success": True,
            "data": categories
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类失败: {str(e)}"
        )


@router.post("/capabilities/{capability_type}/{capability_id}/toggle")
async def toggle_capability(
    capability_type: str,
    capability_id: int,
    request: CapabilityToggleRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    启用/禁用能力
    
    - capability_type: tool/skill
    - 官方能力(is_protected=True)可以禁用但不能删除
    """
    try:
        if capability_type == "tool":
            item = db.query(Tool).filter(Tool.id == capability_id).first()
        elif capability_type == "skill":
            item = db.query(Skill).filter(Skill.id == capability_id).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的能力类型: {capability_type}"
            )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="能力不存在"
            )
        
        # 检查是否允许禁用
        if hasattr(item, 'allow_disable') and not item.allow_disable:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="该能力不允许禁用"
            )
        
        # 更新状态
        if capability_type == "tool":
            item.status = "active" if request.enabled else "disabled"
            item.is_active = request.enabled
        else:
            item.status = "active" if request.enabled else "disabled"
        
        db.commit()
        
        return {
            "success": True,
            "message": f"已{'启用' if request.enabled else '禁用'}该能力",
            "data": {
                "id": capability_id,
                "type": capability_type,
                "enabled": request.enabled
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"操作失败: {str(e)}"
        )


@router.delete("/capabilities/{capability_type}/{capability_id}")
async def delete_capability(
    capability_type: str,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    删除能力
    
    - 官方能力(is_protected=True)不能删除
    - 系统级能力(is_system=True)不能删除
    """
    try:
        if capability_type == "tool":
            item = db.query(Tool).filter(Tool.id == capability_id).first()
        elif capability_type == "skill":
            item = db.query(Skill).filter(Skill.id == capability_id).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的能力类型: {capability_type}"
            )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="能力不存在"
            )
        
        # 检查是否可以删除
        if hasattr(item, 'is_system') and item.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="系统级能力不能删除"
            )
        
        if hasattr(item, 'is_protected') and item.is_protected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="受保护的能力不能删除，只能禁用"
            )
        
        if hasattr(item, 'is_official') and item.is_official:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="官方能力不能删除，只能禁用"
            )
        
        db.delete(item)
        db.commit()
        
        return {
            "success": True,
            "message": "能力已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.get("/agents/{agent_id}/capabilities")
async def get_agent_capabilities(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取智能体的能力分配"""
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="智能体不存在"
            )
        
        # 获取技能关联
        skills = []
        for assoc in agent.skill_associations:
            if assoc.skill:
                skills.append({
                    "id": assoc.skill.id,
                    "type": "skill",
                    "name": assoc.skill.name,
                    "display_name": assoc.skill.display_name,
                    "priority": assoc.priority,
                    "enabled": assoc.enabled,
                    "config": assoc.config
                })
        
        # 获取工具关联
        tools = []
        for assoc in agent.tool_associations:
            if assoc.tool:
                tools.append({
                    "id": assoc.tool.id,
                    "type": "tool",
                    "name": assoc.tool.name,
                    "display_name": assoc.tool.display_name,
                    "priority": assoc.priority,
                    "enabled": assoc.enabled,
                    "config": assoc.config
                })
        
        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "agent_type": agent.agent_type,
                "primary_capability_id": agent.primary_capability_id,
                "primary_capability_type": agent.primary_capability_type,
                "skills": skills,
                "tools": tools
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.post("/agents/{agent_id}/capabilities/assign")
async def assign_capability_to_agent(
    agent_id: int,
    assignment: AgentCapabilityAssignment,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """为智能体分配能力"""
    try:
        # 验证智能体
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="智能体不存在"
            )
        
        # 验证能力
        if assignment.capability_type == "skill":
            capability = db.query(Skill).filter(Skill.id == assignment.capability_id).first()
            if not capability:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="技能不存在"
                )
            
            # 检查是否已关联
            from app.models.agent_skill_association import AgentSkillAssociation
            existing = db.query(AgentSkillAssociation).filter(
                AgentSkillAssociation.agent_id == agent_id,
                AgentSkillAssociation.skill_id == assignment.capability_id
            ).first()
            
            if existing:
                # 更新现有关联
                existing.priority = assignment.priority
                existing.enabled = assignment.enabled
                existing.config = assignment.config
            else:
                # 创建新关联
                new_assoc = AgentSkillAssociation(
                    agent_id=agent_id,
                    skill_id=assignment.capability_id,
                    priority=assignment.priority,
                    enabled=assignment.enabled,
                    config=assignment.config
                )
                db.add(new_assoc)
                
        elif assignment.capability_type == "tool":
            capability = db.query(Tool).filter(Tool.id == assignment.capability_id).first()
            if not capability:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="工具不存在"
                )
            
            # 检查是否已关联
            existing = db.query(AgentToolAssociation).filter(
                AgentToolAssociation.agent_id == agent_id,
                AgentToolAssociation.tool_id == assignment.capability_id
            ).first()
            
            if existing:
                existing.priority = assignment.priority
                existing.enabled = assignment.enabled
                existing.config = assignment.config
            else:
                new_assoc = AgentToolAssociation(
                    agent_id=agent_id,
                    tool_id=assignment.capability_id,
                    priority=assignment.priority,
                    enabled=assignment.enabled,
                    config=assignment.config
                )
                db.add(new_assoc)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的能力类型: {assignment.capability_type}"
            )
        
        # 更新智能体主能力（如果是单一功能智能体）
        if agent.agent_type == "single":
            agent.primary_capability_id = assignment.capability_id
            agent.primary_capability_type = assignment.capability_type
        
        db.commit()
        
        return {
            "success": True,
            "message": "能力分配成功",
            "data": {
                "agent_id": agent_id,
                "capability_id": assignment.capability_id,
                "capability_type": assignment.capability_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配失败: {str(e)}"
        )


@router.post("/agents/{agent_id}/capabilities/remove")
async def remove_capability_from_agent(
    agent_id: int,
    capability_type: str,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """从智能体移除能力"""
    try:
        if capability_type == "skill":
            from app.models.agent_skill_association import AgentSkillAssociation
            assoc = db.query(AgentSkillAssociation).filter(
                AgentSkillAssociation.agent_id == agent_id,
                AgentSkillAssociation.skill_id == capability_id
            ).first()
        elif capability_type == "tool":
            assoc = db.query(AgentToolAssociation).filter(
                AgentToolAssociation.agent_id == agent_id,
                AgentToolAssociation.tool_id == capability_id
            ).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的能力类型: {capability_type}"
            )
        
        if not assoc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联不存在"
            )
        
        db.delete(assoc)
        db.commit()
        
        return {
            "success": True,
            "message": "能力已移除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除失败: {str(e)}"
        )
```

### 3.3 更新智能体API支持分类

**文件**: `backend/app/api/v1/agents.py` 更新

```python
# 在现有agents.py中添加以下端点

from pydantic import BaseModel, Field
from typing import Literal


class AgentCreateRequest(BaseModel):
    """创建智能体请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    avatar: Optional[str] = None
    prompt: str = Field(..., min_length=1)
    agent_type: Literal["single", "composite"] = "single"
    default_model: Optional[int] = None
    # 单一功能智能体配置
    primary_capability_id: Optional[int] = None
    primary_capability_type: Optional[Literal["skill", "tool"]] = None
    # 复合智能体配置
    capabilities: Optional[List[Dict[str, Any]]] = None  # [{"type": "skill", "id": 1, "priority": 0}]


class AgentUpdateRequest(BaseModel):
    """更新智能体请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    avatar: Optional[str] = None
    prompt: Optional[str] = None
    agent_type: Optional[Literal["single", "composite"]] = None
    default_model: Optional[int] = None
    primary_capability_id: Optional[int] = None
    primary_capability_type: Optional[Literal["skill", "tool"]] = None
    capability_orchestration: Optional[Dict[str, Any]] = None


@router.post("", response_model=Dict[str, Any])
async def create_agent(
    request: AgentCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    创建智能体（支持单一功能和复合类型）
    """
    try:
        # 创建智能体
        agent = Agent(
            name=request.name,
            description=request.description,
            avatar=request.avatar,
            prompt=request.prompt,
            agent_type=request.agent_type,
            default_model=request.default_model,
            user_id=current_user.id,
            is_public=False,
            is_recommended=False
        )
        
        # 单一功能智能体配置
        if request.agent_type == "single":
            if request.primary_capability_id and request.primary_capability_type:
                agent.primary_capability_id = request.primary_capability_id
                agent.primary_capability_type = request.primary_capability_type
                
                # 自动创建关联
                if request.primary_capability_type == "skill":
                    from app.models.agent_skill_association import AgentSkillAssociation
                    assoc = AgentSkillAssociation(
                        agent=agent,
                        skill_id=request.primary_capability_id,
                        priority=0,
                        enabled=True
                    )
                    db.add(assoc)
                elif request.primary_capability_type == "tool":
                    assoc = AgentToolAssociation(
                        agent=agent,
                        tool_id=request.primary_capability_id,
                        priority=0,
                        enabled=True
                    )
                    db.add(assoc)
        
        # 复合智能体配置
        elif request.agent_type == "composite" and request.capabilities:
            for cap in request.capabilities:
                cap_type = cap.get("type")
                cap_id = cap.get("id")
                priority = cap.get("priority", 0)
                
                if cap_type == "skill":
                    from app.models.agent_skill_association import AgentSkillAssociation
                    assoc = AgentSkillAssociation(
                        agent=agent,
                        skill_id=cap_id,
                        priority=priority,
                        enabled=True
                    )
                    db.add(assoc)
                elif cap_type == "tool":
                    assoc = AgentToolAssociation(
                        agent=agent,
                        tool_id=cap_id,
                        priority=priority,
                        enabled=True
                    )
                    db.add(assoc)
            
            # 设置能力编排配置
            agent.capability_orchestration = {
                "mode": "auto",
                "rules": [],
                "fallback_order": [cap.get("id") for cap in request.capabilities]
            }
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        return {
            "success": True,
            "message": "智能体创建成功",
            "data": {
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.get("/templates", response_model=Dict[str, Any])
async def get_agent_templates(
    agent_type: Optional[str] = Query(None, description="single/composite"),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取智能体模板列表
    
    返回官方提供的单一功能和复合智能体模板
    """
    try:
        query = db.query(Agent).filter(Agent.is_template == True)
        
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        if category:
            query = query.filter(Agent.template_category == category)
        
        templates = query.all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "agent_type": t.agent_type,
                    "avatar": t.avatar,
                    "template_category": t.template_category,
                    "primary_capability_type": t.primary_capability_type
                }
                for t in templates
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板失败: {str(e)}"
        )
```

### 3.4 注册API路由

**文件**: `backend/app/api/v1/__init__.py` 更新

```python
from fastapi import APIRouter

from app.api.v1 import auth, agents, skills, tools, mcp, capability_center

api_router = APIRouter()

# 现有路由...
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(agents.router, prefix="/agents", tags=["智能体"])
api_router.include_router(skills.router, prefix="/skills", tags=["技能"])
api_router.include_router(tools.router, prefix="/tools", tags=["工具"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["MCP"])

# 新增能力中心路由
api_router.include_router(
    capability_center.router, 
    prefix="/capability-center", 
    tags=["能力中心"]
)
```

---

## 4. 阶段3: 前端适配（React版本）

### 4.1 创建能力中心页面组件

**文件**: `frontend/src/components/CapabilityCenter/CapabilityCenter.jsx`

```jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useCapabilityStore } from '../../stores/capabilityStore';
import { Input } from '../UI/Input';
import { Select } from '../UI/Select';
import { Button } from '../UI/Button';
import { Loading } from '../UI/Loading';
import { CapabilityCard } from './CapabilityCard';
import { Pagination } from '../UI/Pagination';
import './CapabilityCenter.css';

/**
 * 能力中心组件
 * 统一管理工具、技能和MCP能力
 */
const CapabilityCenter = () => {
  // 本地状态
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterSource, setFilterSource] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // 全局状态
  const {
    capabilities,
    total,
    loading,
    fetchCapabilities,
    toggleCapability,
    deleteCapability
  } = useCapabilityStore();

  // 获取能力列表
  const loadCapabilities = useCallback(() => {
    fetchCapabilities({
      type: filterType,
      source: filterSource,
      status: filterStatus,
      search: searchQuery,
      page: currentPage,
      page_size: pageSize
    });
  }, [filterType, filterSource, filterStatus, searchQuery, currentPage, pageSize, fetchCapabilities]);

  // 监听筛选变化
  useEffect(() => {
    setCurrentPage(1);
    loadCapabilities();
  }, [filterType, filterSource, filterStatus, searchQuery]);

  // 监听分页变化
  useEffect(() => {
    loadCapabilities();
  }, [currentPage, pageSize, loadCapabilities]);

  // 处理启用/禁用
  const handleToggle = useCallback(async (item) => {
    await toggleCapability(item.type, item.id, !item.is_active);
    loadCapabilities();
  }, [toggleCapability, loadCapabilities]);

  // 处理删除
  const handleDelete = useCallback(async (item) => {
    if (window.confirm(`确定要删除能力 "${item.display_name}" 吗？`)) {
      await deleteCapability(item.type, item.id);
      loadCapabilities();
    }
  }, [deleteCapability, loadCapabilities]);

  // 类型选项
  const typeOptions = [
    { value: 'all', label: '全部' },
    { value: 'tool', label: '工具' },
    { value: 'skill', label: '技能' }
  ];

  // 来源选项
  const sourceOptions = [
    { value: '', label: '全部来源' },
    { value: 'official', label: '官方' },
    { value: 'user', label: '用户创建' },
    { value: 'marketplace', label: '市场安装' }
  ];

  // 状态选项
  const statusOptions = [
    { value: '', label: '全部状态' },
    { value: 'active', label: '已启用' },
    { value: 'disabled', label: '已禁用' }
  ];

  if (loading && capabilities.length === 0) {
    return <Loading fullScreen />;
  }

  return (
    <div className="capability-center">
      <div className="page-header">
        <h1>能力中心</h1>
        <p className="subtitle">统一管理工具、技能和MCP能力</p>
      </div>

      {/* 筛选栏 */}
      <div className="filter-bar">
        <Input
          type="text"
          placeholder="搜索能力..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />

        <Select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          options={typeOptions}
          className="filter-select"
        />

        <Select
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value)}
          options={sourceOptions}
          className="filter-select"
        />

        <Select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          options={statusOptions}
          className="filter-select"
        />
      </div>

      {/* 能力列表 */}
      <div className="capability-list">
        {capabilities.map((item) => (
          <CapabilityCard
            key={`${item.type}-${item.id}`}
            capability={item}
            onToggle={() => handleToggle(item)}
            onDelete={() => handleDelete(item)}
          />
        ))}
      </div>

      {/* 分页 */}
      <div className="pagination-container">
        <Pagination
          current={currentPage}
          pageSize={pageSize}
          total={total}
          pageSizeOptions={[20, 50, 100]}
          onChange={setCurrentPage}
          onPageSizeChange={setPageSize}
        />
      </div>
    </div>
  );
};

export default CapabilityCenter;
```

**样式文件**: `frontend/src/components/CapabilityCenter/CapabilityCenter.css`

```css
.capability-center {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #333;
}

.subtitle {
  color: #666;
  margin: 0;
  font-size: 14px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  width: 250px;
}

.filter-select {
  width: 150px;
}

.capability-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
```
      
### 4.2 创建能力卡片组件

**文件**: `frontend/src/components/CapabilityCenter/CapabilityCard.jsx`

```jsx
import React, { memo } from 'react';
import { Card } from '../UI/Card';
import { Button } from '../UI/Button';
import { Badge } from '../UI/Badge';
import './CapabilityCard.css';

/**
 * 能力卡片组件
 * 展示单个能力的详细信息和操作按钮
 */
const CapabilityCard = memo(({
  capability,
  onToggle,
  onConfig,
  onDelete
}) => {
  // 获取类型标签
  const getTypeLabel = (type) => {
    const map = {
      tool: '工具',
      skill: '技能',
      mcp: 'MCP'
    };
    return map[type] || type;
  };

  // 处理开关切换
  const handleToggle = () => {
    if (capability.allow_disable) {
      onToggle?.(capability);
    }
  };

  return (
    <Card
      className={`capability-card ${capability.is_official ? 'is-official' : ''}`}
      hoverable
    >
      <div className="card-header">
        <div className="icon-wrapper">
          <span className="icon">{capability.icon}</span>
          {capability.official_badge && (
            <span className="official-badge">{capability.official_badge}</span>
          )}
        </div>

        <div className="title-wrapper">
          <h3 className="title">
            {capability.display_name}
            {capability.is_official && (
              <Badge variant="warning" size="small">官方</Badge>
            )}
          </h3>
          <span className="type-tag">{getTypeLabel(capability.type)}</span>
        </div>

        {/* 启用/禁用开关 */}
        <label className="switch-wrapper">
          <input
            type="checkbox"
            checked={capability.is_active}
            disabled={!capability.allow_disable}
            onChange={handleToggle}
          />
          <span className="switch-slider"></span>
        </label>
      </div>

      <p className="description">{capability.description}</p>

      <div className="tags">
        {capability.tags?.map((tag) => (
          <Badge key={tag} variant="default" size="small">
            {tag}
          </Badge>
        ))}
      </div>

      <div className="card-footer">
        <span className="meta">
          <span className="version">v{capability.version}</span>
          {capability.author && (
            <span className="author">by {capability.author}</span>
          )}
        </span>

        <div className="actions">
          {capability.allow_edit && (
            <Button
              variant="ghost"
              size="small"
              onClick={() => onConfig?.(capability)}
            >
              配置
            </Button>
          )}

          {!capability.is_protected && !capability.is_official && (
            <Button
              variant="danger"
              size="small"
              onClick={() => onDelete?.(capability)}
            >
              删除
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
});

export default CapabilityCard;
```

**样式文件**: `frontend/src/components/CapabilityCenter/CapabilityCard.css`

```css
.capability-card {
  height: 100%;
  transition: all 0.3s ease;
}

.capability-card.is-official {
  border: 2px solid #e6a23c;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.icon-wrapper {
  position: relative;
  font-size: 32px;
  line-height: 1;
}

.official-badge {
  position: absolute;
  bottom: -4px;
  right: -4px;
  font-size: 14px;
}

.title-wrapper {
  flex: 1;
  min-width: 0;
}

.title {
  margin: 0 0 4px;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-tag {
  font-size: 12px;
  color: #999;
}

.description {
  color: #666;
  font-size: 13px;
  line-height: 1.5;
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.meta {
  font-size: 12px;
  color: #999;
}

.meta .version {
  margin-right: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

/* 开关样式 */
.switch-wrapper {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch-wrapper input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 24px;
}

.switch-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .switch-slider {
  background-color: #1890ff;
}

input:checked + .switch-slider:before {
  transform: translateX(20px);
}

input:disabled + .switch-slider {
  opacity: 0.6;
  cursor: not-allowed;
}
```
      
      <el-switch
        v-model="isEnabled"
        :disabled="!capability.allow_disable"
        @change="$emit('toggle', capability)"
      />
    </div>
    
    <p class="description">{{ capability.description }}</p>
    
    <div class="tags">
      <el-tag 
        v-for="tag in capability.tags" 
        :key="tag"
        size="small"
        effect="plain"
      >
        {{ tag }}
      </el-tag>
    </div>
    
    <div class="card-footer">
      <span class="meta">
        <span class="version">v{{ capability.version }}</span>
        <span v-if="capability.author" class="author">by {{ capability.author }}</span>
      </span>
      
      <div class="actions">
        <el-button 
          v-if="capability.allow_edit"
          type="primary"
          link
          size="small"
          @click="$emit('config', capability)"
        >
          配置
        </el-button>
        
        <el-button
          v-if="!capability.is_protected && !capability.is_official"
          type="danger"
          link
          size="small"
          @click="$emit('delete', capability)"
        >
          删除
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  capability: any
}>()

const emit = defineEmits(['toggle', 'config', 'delete'])

const isEnabled = computed({
  get: () => props.capability.is_active,
  set: () => {} // 由父组件处理
})

const typeLabel = computed(() => {
  const map: Record<string, string> = {
    tool: '工具',
    skill: '技能',
    mcp: 'MCP'
  }
  return map[props.capability.type] || props.capability.type
})
</script>

<style scoped>
.capability-card {
  height: 100%;
  transition: all 0.3s;
}

.capability-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

### 4.3 创建Zustand状态管理Store

**文件**: `frontend/src/stores/capabilityStore.js`

```javascript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { capabilityApi } from '../utils/api/capabilityApi';

/**
 * 能力中心状态管理
 * 使用Zustand管理能力列表、筛选状态和操作
 */
export const useCapabilityStore = create(
  devtools(
    (set, get) => ({
      // 状态
      capabilities: [],
      total: 0,
      loading: false,
      error: null,
      categories: [],

      // 筛选状态
      filters: {
        type: 'all',
        source: '',
        status: '',
        search: ''
      },

      // 分页状态
      pagination: {
        page: 1,
        pageSize: 20
      },

      /**
       * 获取能力列表
       */
      fetchCapabilities: async (params = {}) => {
        const { filters, pagination } = get();
        
        set({ loading: true, error: null });
        
        try {
          const response = await capabilityApi.list({
            ...filters,
            ...pagination,
            ...params
          });
          
          if (response.success) {
            set({
              capabilities: response.data.items,
              total: response.data.total,
              loading: false
            });
          } else {
            set({ 
              error: response.message || '获取能力列表失败', 
              loading: false 
            });
          }
        } catch (error) {
          set({ 
            error: error.message || '获取能力列表失败', 
            loading: false 
          });
        }
      },

      /**
       * 更新筛选条件
       */
      setFilters: (newFilters) => {
        set((state) => ({
          filters: { ...state.filters, ...newFilters },
          pagination: { ...state.pagination, page: 1 } // 重置到第一页
        }));
        get().fetchCapabilities();
      },

      /**
       * 更新分页
       */
      setPagination: (newPagination) => {
        set((state) => ({
          pagination: { ...state.pagination, ...newPagination }
        }));
        get().fetchCapabilities();
      },

      /**
       * 启用/禁用能力
       */
      toggleCapability: async (type, id, enabled) => {
        try {
          const response = await capabilityApi.toggle(type, id, enabled);
          if (response.success) {
            // 更新本地状态
            set((state) => ({
              capabilities: state.capabilities.map((item) =>
                item.id === id && item.type === type
                  ? { ...item, is_active: enabled, status: enabled ? 'active' : 'disabled' }
                  : item
              )
            }));
            return true;
          }
          return false;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },

      /**
       * 删除能力
       */
      deleteCapability: async (type, id) => {
        try {
          const response = await capabilityApi.delete(type, id);
          if (response.success) {
            // 从列表中移除
            set((state) => ({
              capabilities: state.capabilities.filter(
                (item) => !(item.id === id && item.type === type)
              ),
              total: state.total - 1
            }));
            return true;
          }
          return false;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },

      /**
       * 获取能力分类
       */
      fetchCategories: async () => {
        try {
          const response = await capabilityApi.getCategories();
          if (response.success) {
            set({ categories: response.data });
          }
        } catch (error) {
          console.error('获取分类失败:', error);
        }
      },

      /**
       * 清除错误
       */
      clearError: () => set({ error: null })
    }),
    { name: 'capabilityStore' }
  )
);
```

### 4.4 创建能力中心API客户端

**文件**: `frontend/src/api/capability.ts`

```typescript
import request from '@/utils/request'

export const capabilityApi = {
  /**
   * 获取能力列表
   */
  list(params: {
    type?: string
    source?: string
    status?: string
    search?: string
    page?: number
    page_size?: number
  }) {
    return request.get('/capability-center/capabilities', { params })
  },

  /**
   * 获取能力分类
   */
  getCategories() {
    return request.get('/capability-center/capabilities/categories')
  },

  /**
   * 启用/禁用能力
   */
  toggle(type: string, id: number, enabled: boolean) {
    return request.post(`/capability-center/capabilities/${type}/${id}/toggle`, {
      enabled
    })
  },

  /**
   * 删除能力
   */
  delete(type: string, id: number) {
    return request.delete(`/capability-center/capabilities/${type}/${id}`)
  },

  /**
   * 获取智能体的能力分配
   */
  getAgentCapabilities(agentId: number) {
    return request.get(`/capability-center/agents/${agentId}/capabilities`)
  },

  /**
   * 为智能体分配能力
   */
  assignCapability(agentId: number, data: {
    agent_id: number
    capability_id: number
    capability_type: string
    priority?: number
    enabled?: boolean
    config?: Record<string, any>
  }) {
    return request.post(`/capability-center/agents/${agentId}/capabilities/assign`, data)
  },

  /**
   * 从智能体移除能力
   */
  removeCapability(agentId: number, type: string, capabilityId: number) {
    return request.post(`/capability-center/agents/${agentId}/capabilities/remove`, null, {
      params: { capability_type: type, capability_id: capabilityId }
    })
  }
}
```

### 4.5 更新路由配置

**文件**: `frontend/src/router/index.jsx` 更新

```jsx
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Loading } from '../components/UI/Loading';

// 懒加载能力中心组件
const CapabilityCenter = lazy(() => 
  import('../components/CapabilityCenter/CapabilityCenter')
);

// 路由配置
export const routes = [
  // 现有路由...
  
  {
    path: '/capability-center',
    element: (
      <Suspense fallback={<Loading fullScreen />}>
        <CapabilityCenter />
      </Suspense>
    ),
    meta: {
      title: '能力中心',
      icon: 'Tools',
      requiresAuth: true
    }
  },
  
  // 重定向旧路由
  {
    path: '/settings/search',
    element: <Navigate to="/capability-center?type=tool&category=search" replace />
  },
  {
    path: '/tool',
    element: <Navigate to="/capability-center?type=tool" replace />
  },
  {
    path: '/settings/skills',
    element: <Navigate to="/capability-center?type=skill" replace />
  }
];

const router = createBrowserRouter(routes);

export default router;
```

### 4.6 创建能力中心入口文件

**文件**: `frontend/src/components/CapabilityCenter/index.js`

```javascript
export { default as CapabilityCenter } from './CapabilityCenter';
export { default as CapabilityCard } from './CapabilityCard';
export { useCapabilityStore } from '../../stores/capabilityStore';
```

### 4.7 更新侧边栏导航

在项目的侧边栏组件中添加能力中心入口：

```jsx
// 在 Sidebar.jsx 或类似的导航组件中添加
{
  path: '/capability-center',
  name: '能力中心',
  icon: '🔧', // 或使用项目中的图标组件
  description: '统一管理工具、技能和MCP能力'
}
```

---

## 5. 阶段4: 功能迁移与测试

### 5.1 MCP客户端工具迁移脚本

**文件**: `backend/scripts/migrate_mcp_to_tools.py`

```python
"""将MCP客户端配置迁移到工具表"""

import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.mcp import MCPClientConfigModel, MCPToolMappingModel
from app.models.tool import Tool


def migrate_mcp_to_tools():
    """将MCP工具映射迁移到统一工具表"""
    db = SessionLocal()
    
    try:
        # 获取所有MCP客户端配置
        clients = db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.enabled == True
        ).all()
        
        migrated_count = 0
        
        for client in clients:
            # 获取该客户端的工具映射
            mappings = db.query(MCPToolMappingModel).filter(
                MCPToolMappingModel.client_config_id == client.id
            ).all()
            
            for mapping in mappings:
                # 检查是否已存在
                existing = db.query(Tool).filter(
                    Tool.mcp_client_config_id == client.id,
                    Tool.mcp_tool_name == mapping.original_name
                ).first()
                
                if existing:
                    print(f"  跳过已存在: {mapping.local_name}")
                    continue
                
                # 创建工具记录
                tool = Tool(
                    name=mapping.local_name,
                    display_name=mapping.local_name.replace('_', ' ').title(),
                    description=mapping.description or f"MCP工具: {mapping.original_name}",
                    category='mcp',
                    tool_type='mcp',
                    mcp_client_config_id=client.id,
                    mcp_tool_name=mapping.original_name,
                    parameters_schema=mapping.input_schema,
                    source='mcp',
                    is_official=False,
                    status='active' if mapping.enabled else 'disabled',
                    is_active=mapping.enabled,
                    author=f"MCP:{client.name}"
                )
                
                db.add(tool)
                migrated_count += 1
                print(f"  迁移: {mapping.original_name} -> {mapping.local_name}")
        
        db.commit()
        print(f"\n✅ 迁移完成，共迁移 {migrated_count} 个MCP工具")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_mcp_to_tools()
```

### 5.2 搜索设置迁移脚本

**文件**: `backend/scripts/migrate_search_settings.py`

```python
"""将搜索设置迁移到工具配置"""

import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.search_settings import SearchSettings
from app.models.tool import Tool


def migrate_search_settings():
    """将搜索设置迁移到网络搜索工具配置"""
    db = SessionLocal()
    
    try:
        # 获取搜索设置
        settings = db.query(SearchSettings).first()
        
        if not settings:
            print("未找到搜索设置，跳过迁移")
            return
        
        # 查找网络搜索工具
        search_tool = db.query(Tool).filter(Tool.name == 'web_search').first()
        
        if not search_tool:
            print("未找到网络搜索工具，跳过迁移")
            return
        
        # 迁移配置
        config = {
            'default_engine': settings.default_engine,
            'engines': settings.engines_config,
            'max_results': settings.max_results,
            'timeout': settings.timeout,
            'safe_search': settings.safe_search
        }
        
        search_tool.config = config
        search_tool.status = 'active' if settings.enabled else 'disabled'
        search_tool.is_active = settings.enabled
        
        db.commit()
        print("✅ 搜索设置已迁移到网络搜索工具")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_search_settings()
```

### 5.3 智能体技能字段迁移

**文件**: `backend/scripts/migrate_agent_skills.py`

```python
"""将Agent的skills JSON字段迁移到关联表"""

import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.agent import Agent
from app.models.skill import Skill
from app.models.agent_skill_association import AgentSkillAssociation


def migrate_agent_skills():
    """迁移智能体的技能字段到关联表"""
    db = SessionLocal()
    
    try:
        # 获取所有有skills字段的智能体
        agents = db.query(Agent).filter(
            Agent.skills.isnot(None)
        ).all()
        
        migrated_count = 0
        
        for agent in agents:
            if not agent.skills:
                continue
            
            skill_ids = agent.skills
            if isinstance(skill_ids, str):
                import json
                try:
                    skill_ids = json.loads(skill_ids)
                except:
                    continue
            
            for idx, skill_id in enumerate(skill_ids):
                # 验证技能存在
                skill = db.query(Skill).filter(Skill.id == skill_id).first()
                if not skill:
                    print(f"  跳过不存在的技能ID: {skill_id}")
                    continue
                
                # 检查是否已关联
                existing = db.query(AgentSkillAssociation).filter(
                    AgentSkillAssociation.agent_id == agent.id,
                    AgentSkillAssociation.skill_id == skill_id
                ).first()
                
                if existing:
                    continue
                
                # 创建关联
                assoc = AgentSkillAssociation(
                    agent_id=agent.id,
                    skill_id=skill_id,
                    priority=idx,
                    enabled=True,
                    config={}
                )
                db.add(assoc)
                migrated_count += 1
            
            print(f"  智能体 {agent.name}(ID:{agent.id}): 迁移 {len(skill_ids)} 个技能")
        
        db.commit()
        print(f"\n✅ 迁移完成，共创建 {migrated_count} 个关联")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_agent_skills()
```

### 5.4 执行所有迁移脚本

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
venv\Scripts\activate

# 执行迁移脚本
python scripts/migrate_mcp_to_tools.py
python scripts/migrate_search_settings.py
python scripts/migrate_agent_skills.py
```

### 5.5 功能测试清单

**文件**: `backend/tests/test_capability_center.py`

```python
"""能力中心功能测试"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCapabilityCenter:
    """能力中心测试类"""
    
    def test_list_capabilities(self, auth_headers):
        """测试获取能力列表"""
        response = client.get(
            "/api/v1/capability-center/capabilities",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
    
    def test_list_capabilities_with_filter(self, auth_headers):
        """测试带筛选的能力列表"""
        response = client.get(
            "/api/v1/capability-center/capabilities?type=tool&source=official",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 验证返回的都是官方工具
        for item in data["data"]["items"]:
            assert item["is_official"] is True
    
    def test_toggle_capability(self, auth_headers):
        """测试启用/禁用能力"""
        # 先获取一个能力
        response = client.get(
            "/api/v1/capability-center/capabilities?type=tool",
            headers=auth_headers
        )
        items = response.json()["data"]["items"]
        if not items:
            pytest.skip("没有可测试的工具")
        
        tool = items[0]
        
        # 切换状态
        response = client.post(
            f"/api/v1/capability-center/capabilities/tool/{tool['id']}/toggle",
            json={"enabled": not tool["is_active"]},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_cannot_delete_official_capability(self, auth_headers):
        """测试不能删除官方能力"""
        # 获取官方工具
        response = client.get(
            "/api/v1/capability-center/capabilities?type=tool&source=official",
            headers=auth_headers
        )
        items = response.json()["data"]["items"]
        if not items:
            pytest.skip("没有官方工具")
        
        tool = items[0]
        
        # 尝试删除
        response = client.delete(
            f"/api/v1/capability-center/capabilities/tool/{tool['id']}",
            headers=auth_headers
        )
        assert response.status_code == 403
    
    def test_get_agent_capabilities(self, auth_headers, test_agent):
        """测试获取智能体能力"""
        response = client.get(
            f"/api/v1/capability-center/agents/{test_agent.id}/capabilities",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "skills" in data["data"]
        assert "tools" in data["data"]
    
    def test_assign_capability_to_agent(self, auth_headers, test_agent, test_skill):
        """测试为智能体分配能力"""
        response = client.post(
            f"/api/v1/capability-center/agents/{test_agent.id}/capabilities/assign",
            json={
                "agent_id": test_agent.id,
                "capability_id": test_skill.id,
                "capability_type": "skill",
                "priority": 1,
                "enabled": True,
                "config": {}
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
```

---

## 6. 阶段5: 废弃功能清理

### 6.1 废弃API标记

**文件**: `backend/app/api/v1/search_management.py` 更新

```python
"""搜索管理API（已废弃，请使用能力中心）"""

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.get("/settings/search")
async def get_search_settings_deprecated():
    """
    ⚠️ 已废弃
    
    该接口已废弃，请使用 `/capability-center/capabilities?type=tool&category=search`
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="该接口已废弃，请使用能力中心API: /capability-center/capabilities?type=tool&category=search"
    )
```

### 6.2 前端路由重定向

**文件**: `frontend/src/router/index.ts` 添加重定向

```typescript
// 在路由配置中添加
const routes = [
  // ... 其他路由
  
  // 废弃路由重定向
  {
    path: '/settings/search',
    redirect: () => {
      console.warn('路由 /settings/search 已废弃，请使用 /capability-center')
      return '/capability-center?type=tool&category=search'
    }
  },
  {
    path: '/tool',
    redirect: () => {
      console.warn('路由 /tool 已废弃，请使用 /capability-center')
      return '/capability-center?type=tool'
    }
  },
  {
    path: '/settings/skills',
    redirect: () => {
      console.warn('路由 /settings/skills 已废弃，请使用 /capability-center')
      return '/capability-center?type=skill'
    }
  }
]
```

### 6.3 清理计划

| 阶段 | 时间 | 操作 |
|-----|------|------|
| 阶段1 | 实施后 | 保留旧API，返回410状态码和重定向信息 |
| 阶段2 | 1个月后 | 前端移除旧页面，仅保留重定向 |
| 阶段3 | 3个月后 | 后端移除废弃API，清理相关代码 |
| 阶段4 | 6个月后 | 删除数据库中废弃字段（如agents.skills JSON字段） |

---

## 7. 实施检查清单

### 7.1 数据库迁移检查

- [ ] 执行 Alembic 迁移脚本
- [ ] 验证 `tools` 表创建成功
- [ ] 验证 `skills` 表字段扩展
- [ ] 验证 `agents` 表字段扩展
- [ ] 验证 `agent_tool_associations` 关联表创建
- [ ] 验证官方能力初始化数据插入

### 7.2 后端API检查

- [ ] 能力中心API可正常访问
- [ ] 智能体API支持类型字段
- [ ] 工具API正常工作
- [ ] 技能API正常工作
- [ ] MCP集成正常

### 7.3 前端检查

- [ ] 能力中心页面可正常访问
- [ ] 能力列表展示正常
- [ ] 筛选功能正常
- [ ] 启用/禁用功能正常
- [ ] 官方能力标识显示正确
- [ ] 旧路由重定向正常

### 7.4 数据迁移检查

- [ ] MCP工具迁移完成
- [ ] 搜索设置迁移完成
- [ ] 智能体技能关联迁移完成
- [ ] 数据完整性验证通过

---

## 8. 回滚方案

### 8.1 数据库回滚

```bash
# 回滚到上一个版本
alembic downgrade 003_add_mcp_support
```

### 8.2 代码回滚

```bash
# 使用git回滚
git stash
git checkout <previous-commit>
```

### 8.3 数据恢复

如果有备份，可以从备份恢复：

```bash
# SQLite备份恢复
copy backup\app.db backend\app.db
```

---

## 9. 附录

### 9.1 官方能力清单

| 类型 | 名称 | 显示名称 | 状态 |
|-----|------|---------|------|
| 工具 | file_reader | 文件读取工具 | 内置，可禁用 |
| 工具 | web_search | 网络搜索工具 | 内置，可配置 |
| 工具 | knowledge_retrieval | 知识库检索工具 | 内置，可配置 |
| 工具 | calculator | 计算器工具 | 内置，可禁用 |
| 工具 | datetime_tool | 时间日期工具 | 内置，可禁用 |
| 技能 | code_review_assistant | 代码审查助手 | 内置，可禁用 |
| 技能 | translation_expert | 翻译专家 | 内置，可禁用 |
| 技能 | writing_assistant | 文案生成器 | 内置，可禁用 |
| 技能 | document_summary | 文档总结助手 | 内置，可禁用 |

### 9.2 数据库变更摘要

**新增表**:
- `tools` - 工具表
- `agent_tool_associations` - 智能体工具关联表

**扩展表**:
- `skills` - 添加官方能力标识字段
- `agents` - 添加智能体类型和主能力字段

### 9.3 API变更摘要

**新增API**:
- `GET /capability-center/capabilities` - 能力列表
- `POST /capability-center/capabilities/{type}/{id}/toggle` - 启用/禁用
- `DELETE /capability-center/capabilities/{type}/{id}` - 删除
- `GET /capability-center/agents/{id}/capabilities` - 智能体能力
- `POST /capability-center/agents/{id}/capabilities/assign` - 分配能力
- `POST /capability-center/agents/{id}/capabilities/remove` - 移除能力

**废弃API**:
- `GET /settings/search` - 使用能力中心替代
- `/tool/*` - 使用能力中心替代

---

**文档结束**