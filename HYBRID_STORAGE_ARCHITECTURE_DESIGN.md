# 混合存储架构设计方案

## 1. 架构概述

本方案旨在设计一个混合存储架构，结合数据库的结构化管理能力和文件系统的透明性、可移植性优势，为 Py Copilot 提供更高效、可靠的存储解决方案。

### 1.1 核心设计理念

- **分离关注点**：数据库负责索引和元数据管理，文件系统负责原始内容存储
- **数据一致性**：通过事件监听机制确保数据库与文件系统的同步
- **可扩展性**：支持多模态内容存储和检索
- **用户可控性**：纯文本文件格式，用户可直接查看和编辑

### 1.2 技术架构图

```
┌─────────────────────────────────────────────────────────┐
│                   混合存储架构                           │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  应用层     │────│  服务层     │────│  存储层     │ │
│  │  (API)      │    │  (Services) │    │             │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│                                           │           │
│                                           ▼           │
│  ┌─────────────────────────────────────────────────┐   │
│  │                 存储适配器                       │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  ┌─────────────┐    ┌────────────────────────┐  │   │
│  │  │  数据库     │    │  文件系统              │  │   │
│  │  │  (SQLite)   │    │  (Markdown + 多媒体)   │  │   │
│  │  └─────────────┘    └────────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 2. 存储职责划分

### 2.1 数据库职责

| 模块 | 职责 | 存储内容 |
|------|------|----------|
| 记忆系统 | 存储记忆索引、元数据、关系映射 | 记忆ID、类型、优先级、访问统计、标签、向量索引 |
| 知识库系统 | 存储文档索引、元数据、标签 | 文档ID、标题、摘要、标签、创建时间、更新时间 |
| 智能体系统 | 存储智能体配置索引、状态 | 智能体ID、名称、类型、状态、配置引用 |
| 工作流系统 | 存储工作流定义索引、状态 | 工作流ID、名称、状态、节点关系 |
| 平台集成 | 存储平台配置索引、状态 | 平台ID、类型、配置引用、状态 |

### 2.2 文件系统职责

| 模块 | 职责 | 存储内容 |
|------|------|----------|
| 记忆系统 | 存储记忆原始内容 | 长期记忆（Markdown）、短期记忆（按日期组织的Markdown） |
| 知识库系统 | 存储知识文档原始内容 | 知识文档（Markdown）、多媒体附件 |
| 智能体系统 | 存储智能体详细配置 | 智能体配置（YAML）、能力定义 |
| 工作流系统 | 存储工作流详细定义 | 工作流定义（YAML）、节点配置 |
| 平台集成 | 存储平台详细配置 | 平台配置（YAML）、认证信息 |

## 3. 目录结构设计

### 3.1 基础目录结构

```
backend/data/
├── memory/               # 记忆存储
│   ├── long_term/        # 长期记忆
│   │   ├── agent_1/      # 智能体ID
│   │   │   ├── memory.md # 长期记忆内容
│   │   │   └── assets/   # 关联的多媒体文件
│   │   └── ...
│   └── short_term/       # 短期记忆
│       ├── 20260101/     # 日期目录
│       │   ├── agent_1.md# 智能体当日记忆
│       │   └── agent_2.md
│       └── ...
├── knowledge/            # 知识库
│   ├── docs/             # 文档存储
│   │   ├── doc_001.md    # 知识文档
│   │   ├── doc_002.md
│   │   └── ...
│   └── assets/           # 知识库多媒体资源
├── config/               # 配置文件
│   ├── agents/           # 智能体配置
│   │   ├── agent_1.yaml  # 智能体配置
│   │   └── ...
│   ├── workflows/        # 工作流配置
│   │   ├── workflow_1.yaml
│   │   └── ...
│   └── platforms/        # 平台配置
│       ├── feishu.yaml
│       ├── telegram.yaml
│       └── ...
└── vector_index/         # 向量索引
    └── memory_vectors.db # SQLite 向量数据库
```

### 3.2 目录命名规范

- **智能体目录**：`agent_{agent_id}`，其中 `agent_id` 为智能体的唯一标识符
- **日期目录**：`YYYYMMDD` 格式，如 `20260101`
- **文档文件**：`doc_{doc_id}.md`，其中 `doc_id` 为文档的唯一标识符
- **配置文件**：`{name}.yaml`，其中 `name` 为配置项的名称

## 4. 数据模型设计

### 4.1 记忆系统数据模型

#### 4.1.1 数据库表结构

**`memories` 表**
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `memory_id` | `TEXT` | `PRIMARY KEY` | 记忆ID |
| `agent_id` | `TEXT` | `NOT NULL` | 智能体ID |
| `user_id` | `TEXT` | `NOT NULL` | 用户ID |
| `memory_type` | `TEXT` | `NOT NULL` | 记忆类型 |
| `priority` | `TEXT` | `NOT NULL` | 优先级 |
| `access_count` | `INTEGER` | `DEFAULT 0` | 访问次数 |
| `last_accessed` | `DATETIME` | `NOT NULL` | 最后访问时间 |
| `created_at` | `DATETIME` | `NOT NULL` | 创建时间 |
| `expires_at` | `DATETIME` | | 过期时间 |
| `file_path` | `TEXT` | `NOT NULL` | 文件系统路径 |
| `tags` | `TEXT` | | 标签（JSON格式） |
| `vector_id` | `INTEGER` | | 向量索引ID |

**`memory_vectors` 表**
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 向量ID |
| `memory_id` | `TEXT` | `REFERENCES memories(memory_id)` | 记忆ID |
| `vector` | `BLOB` | `NOT NULL` | 向量数据 |
| `created_at` | `DATETIME` | `NOT NULL` | 创建时间 |

#### 4.1.2 文件结构

**长期记忆文件** (`backend/data/memory/long_term/agent_{agent_id}/memory.md`)

```markdown
# 长期记忆

## 基本信息
- **智能体ID**: {agent_id}
- **创建时间**: {created_at}
- **最后更新**: {last_updated}

## 用户偏好
- 偏好类型: {preference_type}
- 详细内容: {preference_content}

## 重要事实
- 事实描述: {fact_description}
- 相关上下文: {context}

## 项目上下文
- 项目名称: {project_name}
- 项目状态: {project_status}
- 相关信息: {related_info}

## 对话记录
- 对话时间: {conversation_time}
- 对话内容: {conversation_content}

## 其他信息
- 标签: {tags}
- 优先级: {priority}
```

**短期记忆文件** (`backend/data/memory/short_term/{YYYYMMDD}/agent_{agent_id}.md`)

```markdown
# 短期记忆 - {YYYYMMDD}

## 智能体信息
- **智能体ID**: {agent_id}
- **日期**: {date}

## 记忆条目

### {timestamp}
- **类型**: {memory_type}
- **内容**: {content}
- **标签**: {tags}
- **优先级**: {priority}

### {timestamp}
- **类型**: {memory_type}
- **内容**: {content}
- **标签**: {tags}
- **优先级**: {priority}
```

### 4.2 知识库系统数据模型

#### 4.2.1 数据库表结构

**`knowledge_documents` 表**
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `doc_id` | `TEXT` | `PRIMARY KEY` | 文档ID |
| `title` | `TEXT` | `NOT NULL` | 文档标题 |
| `summary` | `TEXT` | | 文档摘要 |
| `file_path` | `TEXT` | `NOT NULL` | 文件系统路径 |
| `created_at` | `DATETIME` | `NOT NULL` | 创建时间 |
| `updated_at` | `DATETIME` | `NOT NULL` | 更新时间 |
| `tags` | `TEXT` | | 标签（JSON格式） |
| `vector_id` | `INTEGER` | | 向量索引ID |

**`knowledge_vectors` 表**
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 向量ID |
| `doc_id` | `TEXT` | `REFERENCES knowledge_documents(doc_id)` | 文档ID |
| `vector` | `BLOB` | `NOT NULL` | 向量数据 |
| `created_at` | `DATETIME` | `NOT NULL` | 创建时间 |

#### 4.2.2 文件结构

**知识文档文件** (`backend/data/knowledge/docs/doc_{doc_id}.md`)

```markdown
# {title}

## 摘要
{summary}

## 内容
{content}

## 标签
{tags}

## 元数据
- **创建时间**: {created_at}
- **最后更新**: {updated_at}
- **文档ID**: {doc_id}
```

### 4.3 智能体系统数据模型

#### 4.3.1 数据库表结构

**`agents` 表** (现有表结构扩展)
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `agent_id` | `TEXT` | `PRIMARY KEY` | 智能体ID |
| `name` | `TEXT` | `NOT NULL` | 智能体名称 |
| `type` | `TEXT` | `NOT NULL` | 智能体类型 |
| `status` | `TEXT` | `NOT NULL` | 状态 |
| `config_path` | `TEXT` | | 配置文件路径 |
| `created_at` | `DATETIME` | `NOT NULL` | 创建时间 |
| `updated_at` | `DATETIME` | `NOT NULL` | 更新时间 |

#### 4.3.2 文件结构

**智能体配置文件** (`backend/data/config/agents/{agent_id}.yaml`)

```yaml
# 智能体配置
agent_id: {agent_id}
name: {name}
type: {type}
status: {status}

# 基本配置
configuration:
  description: {description}
  capabilities: {capabilities}
  parameters: {parameters}

# 记忆配置
memory:
  long_term_memory: true
  short_term_memory: true
  memory_limit: {memory_limit}

# 模型配置
model:
  default_model: {default_model}
  fallback_model: {fallback_model}
  parameters: {parameters}

# 工具配置
tools:
  - tool_id: {tool_id}
    name: {tool_name}
    configuration: {configuration}

# 元数据
metadata:
  created_at: {created_at}
  updated_at: {updated_at}
  version: {version}
```

### 4.4 工作流系统数据模型

#### 4.4.1 数据库表结构

**`workflows` 表** (现有表结构扩展)
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `workflow_id` | `TEXT` | `PRIMARY KEY` | 工作流ID |
| `name` | `TEXT` | `NOT NULL` | 工作流名称 |
| `description` | `TEXT` | | 工作流描述 |
| `status` | `TEXT` | `NOT NULL` | 状态 |
| `config_path` | `TEXT` | | 配置文件路径 |
| `created_at` | `DATETIME` | `NOT NULL` | 创建时间 |
| `updated_at` | `DATETIME` | `NOT NULL` | 更新时间 |

#### 4.4.2 文件结构

**工作流配置文件** (`backend/data/config/workflows/{workflow_id}.yaml`)

```yaml
# 工作流配置
workflow_id: {workflow_id}
name: {name}
description: {description}
status: {status}

# 节点配置
nodes:
  - node_id: {node_id}
    name: {node_name}
    type: {node_type}
    configuration: {configuration}
    next_nodes: {next_nodes}

# 触发器配置
triggers:
  - trigger_id: {trigger_id}
    type: {trigger_type}
    configuration: {configuration}

# 元数据
metadata:
  created_at: {created_at}
  updated_at: {updated_at}
  version: {version}
```

### 4.5 平台集成数据模型

#### 4.5.1 数据库表结构

**`platforms` 表** (新建)
| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `platform_id` | `TEXT` | `PRIMARY KEY` | 平台ID |
| `name` | `TEXT` | `NOT NULL` | 平台名称 |
| `type` | `TEXT` | `NOT NULL` | 平台类型 |
| `status` | `TEXT` | `NOT NULL` | 状态 |
| `config_path` | `TEXT` | | 配置文件路径 |
| `created_at` | `DATETIME` | `NOT NULL` | 创建时间 |
| `updated_at` | `DATETIME` | `NOT NULL` | 更新时间 |

#### 4.5.2 文件结构

**平台配置文件** (`backend/data/config/platforms/{platform_type}.yaml`)

```yaml
# 平台配置
platform_id: {platform_id}
name: {name}
type: {platform_type}
status: {status}

# 认证配置
auth:
  {auth_config}

# 消息配置
messaging:
  {messaging_config}

# 事件配置
events:
  {events_config}

# 元数据
metadata:
  created_at: {created_at}
  updated_at: {updated_at}
  version: {version}
```

## 5. 实现细节

### 5.1 存储适配器设计

#### 5.1.1 核心组件

- **HybridStorageService**：混合存储服务，提供统一的存储接口
- **FileStorageAdapter**：文件存储适配器，处理文件系统操作
- **DatabaseStorageAdapter**：数据库存储适配器，处理数据库操作
- **SynchronizationService**：同步服务，确保数据库与文件系统的一致性

#### 5.1.2 类图

```
┌───────────────────────┐
│  HybridStorageService │
├───────────────────────┤
│ + save_memory()       │
│ + load_memory()       │
│ + save_knowledge()    │
│ + load_knowledge()    │
│ + save_config()       │
│ + load_config()       │
└───────────────────────┘
        │
        ├─────────────────┐
        ▼                 ▼
┌────────────────┐   ┌───────────────────┐
│ FileStorageAdapter │ │ DatabaseStorageAdapter │
├────────────────┘   └───────────────────┘
│ + write_file()    │   │ + save_metadata()     │
│ + read_file()     │   │ + load_metadata()     │
│ + delete_file()   │   │ + update_metadata()   │
│ + list_files()    │   │ + delete_metadata()   │
└──────────────────┘   └──────────────────────┘
        │                     │
        └─────────────────────┘
                  │
                  ▼
        ┌───────────────────────┐
        │ SynchronizationService │
        ├───────────────────────┤
        │ + sync_file_to_db()   │
        │ + sync_db_to_file()   │
        │ + validate_consistency() │
        └───────────────────────┘
```

### 5.2 目录结构实现

#### 5.2.1 初始化脚本

```python
"""
目录结构初始化脚本
"""
import os
from pathlib import Path

def initialize_directory_structure(base_path: str = "backend/data"):
    """初始化目录结构
    
    Args:
        base_path: 基础路径
    """
    base_dir = Path(base_path)
    
    # 创建基础目录
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建记忆存储目录
    memory_dir = base_dir / "memory"
    memory_dir.mkdir(exist_ok=True)
    
    # 创建长期记忆目录
    long_term_dir = memory_dir / "long_term"
    long_term_dir.mkdir(exist_ok=True)
    
    # 创建短期记忆目录
    short_term_dir = memory_dir / "short_term"
    short_term_dir.mkdir(exist_ok=True)
    
    # 创建知识库目录
    knowledge_dir = base_dir / "knowledge"
    knowledge_dir.mkdir(exist_ok=True)
    
    # 创建文档目录
    docs_dir = knowledge_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # 创建知识库资源目录
    assets_dir = knowledge_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    # 创建配置目录
    config_dir = base_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # 创建智能体配置目录
    agents_dir = config_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    
    # 创建工作流配置目录
    workflows_dir = config_dir / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    
    # 创建平台配置目录
    platforms_dir = config_dir / "platforms"
    platforms_dir.mkdir(exist_ok=True)
    
    # 创建向量索引目录
    vector_index_dir = base_dir / "vector_index"
    vector_index_dir.mkdir(exist_ok=True)
    
    print(f"目录结构已初始化: {base_path}")

if __name__ == "__main__":
    initialize_directory_structure()
```

### 5.3 数据同步机制

#### 5.3.1 事件监听实现

```python
"""
数据同步机制
"""
from sqlalchemy import event
from sqlalchemy.orm import Session
from pathlib import Path
import json

class SynchronizationService:
    """同步服务，确保数据库与文件系统的一致性"""
    
    def __init__(self, base_path: str = "backend/data"):
        """初始化同步服务
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
    
    def sync_file_to_db(self, file_path: str, db_session: Session, entity_type: str):
        """将文件内容同步到数据库
        
        Args:
            file_path: 文件路径
            db_session: 数据库会话
            entity_type: 实体类型 (memory/knowledge/agent/workflow/platform)
        """
        # 读取文件内容
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        content = file_path.read_text(encoding="utf-8")
        
        # 根据实体类型执行不同的同步逻辑
        if entity_type == "memory":
            self._sync_memory_file_to_db(file_path, content, db_session)
        elif entity_type == "knowledge":
            self._sync_knowledge_file_to_db(file_path, content, db_session)
        elif entity_type == "agent":
            self._sync_agent_file_to_db(file_path, content, db_session)
        elif entity_type == "workflow":
            self._sync_workflow_file_to_db(file_path, content, db_session)
        elif entity_type == "platform":
            self._sync_platform_file_to_db(file_path, content, db_session)
    
    def sync_db_to_file(self, entity_id: str, db_session: Session, entity_type: str):
        """将数据库内容同步到文件
        
        Args:
            entity_id: 实体ID
            db_session: 数据库会话
            entity_type: 实体类型
        """
        # 根据实体类型执行不同的同步逻辑
        if entity_type == "memory":
            self._sync_memory_db_to_file(entity_id, db_session)
        elif entity_type == "knowledge":
            self._sync_knowledge_db_to_file(entity_id, db_session)
        elif entity_type == "agent":
            self._sync_agent_db_to_file(entity_id, db_session)
        elif entity_type == "workflow":
            self._sync_workflow_db_to_file(entity_id, db_session)
        elif entity_type == "platform":
            self._sync_platform_db_to_file(entity_id, db_session)
    
    def validate_consistency(self, entity_id: str, entity_type: str, db_session: Session) -> bool:
        """验证数据库与文件系统的一致性
        
        Args:
            entity_id: 实体ID
            entity_type: 实体类型
            db_session: 数据库会话
            
        Returns:
            是否一致
        """
        # 实现一致性验证逻辑
        # 比较数据库中的元数据与文件系统中的内容
        pass
    
    def _sync_memory_file_to_db(self, file_path: Path, content: str, db_session: Session):
        """同步记忆文件到数据库"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_knowledge_file_to_db(self, file_path: Path, content: str, db_session: Session):
        """同步知识文件到数据库"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_agent_file_to_db(self, file_path: Path, content: str, db_session: Session):
        """同步智能体配置文件到数据库"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_workflow_file_to_db(self, file_path: Path, content: str, db_session: Session):
        """同步工作流配置文件到数据库"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_platform_file_to_db(self, file_path: Path, content: str, db_session: Session):
        """同步平台配置文件到数据库"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_memory_db_to_file(self, memory_id: str, db_session: Session):
        """同步记忆数据库到文件"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_knowledge_db_to_file(self, doc_id: str, db_session: Session):
        """同步知识数据库到文件"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_agent_db_to_file(self, agent_id: str, db_session: Session):
        """同步智能体数据库到文件"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_workflow_db_to_file(self, workflow_id: str, db_session: Session):
        """同步工作流数据库到文件"""
        # 实现具体的同步逻辑
        pass
    
    def _sync_platform_db_to_file(self, platform_id: str, db_session: Session):
        """同步平台数据库到文件"""
        # 实现具体的同步逻辑
        pass

# 注册事件监听器
def register_sync_listeners():
    """注册数据库事件监听器"""
    # 实现事件监听器注册
    pass
```

### 5.4 与现有系统的集成

#### 5.4.1 记忆系统集成

```python
"""
记忆系统与混合存储架构的集成
"""
from app.memory.memory_models import MemoryManager, MemoryItem
from app.services.hybrid_storage import HybridStorageService

class HybridMemoryManager:
    """混合存储记忆管理器"""
    
    def __init__(self):
        """初始化混合记忆管理器"""
        self.legacy_manager = MemoryManager()
        self.hybrid_storage = HybridStorageService()
    
    def store_memory(self, memory: MemoryItem) -> bool:
        """存储记忆
        
        Args:
            memory: 记忆项
            
        Returns:
            是否成功
        """
        # 1. 保存到文件系统
        file_path = self.hybrid_storage.save_memory(
            agent_id=memory.agent_id,
            content=memory.content,
            memory_type="long_term" if memory.priority in ["high", "critical"] else "short_term"
        )
        
        # 2. 更新记忆项的文件路径
        memory.metadata["file_path"] = file_path
        
        # 3. 保存到数据库
        return self.legacy_manager.store_memory(memory)
    
    def get_memory(self, memory_id: str) -> MemoryItem:
        """获取记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            记忆项
        """
        # 1. 从数据库获取记忆
        memory = self.legacy_manager.get_memory(memory_id)
        
        # 2. 如果有文件路径，从文件系统加载最新内容
        if memory and memory.metadata.get("file_path"):
            file_content = self.hybrid_storage.load_memory(
                agent_id=memory.agent_id,
                file_path=memory.metadata["file_path"]
            )
            if file_content:
                memory.content = file_content
        
        return memory
    
    def search_memories(self, *args, **kwargs) -> list:
        """搜索记忆"""
        # 使用现有的搜索方法
        memories = self.legacy_manager.search_memories(*args, **kwargs)
        
        # 加载文件内容
        for memory in memories:
            if memory.metadata.get("file_path"):
                file_content = self.hybrid_storage.load_memory(
                    agent_id=memory.agent_id,
                    file_path=memory.metadata["file_path"]
                )
                if file_content:
                    memory.content = file_content
        
        return memories
```

#### 5.4.2 知识库系统集成

```python
"""
知识库系统与混合存储架构的集成
"""
from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.services.hybrid_storage import HybridStorageService

class HybridKnowledgeService:
    """混合存储知识服务"""
    
    def __init__(self):
        """初始化混合知识服务"""
        self.legacy_service = KnowledgeService()
        self.hybrid_storage = HybridStorageService()
    
    def create_document(self, title: str, content: str, tags: list = None) -> str:
        """创建文档
        
        Args:
            title: 文档标题
            content: 文档内容
            tags: 标签列表
            
        Returns:
            文档ID
        """
        # 1. 创建文档（现有逻辑）
        doc_id = self.legacy_service.create_document(title, content, tags)
        
        # 2. 保存到文件系统
        self.hybrid_storage.save_knowledge(
            doc_id=doc_id,
            title=title,
            content=content,
            tags=tags
        )
        
        return doc_id
    
    def get_document(self, doc_id: str) -> dict:
        """获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档内容
        """
        # 1. 从数据库获取文档元数据
        document = self.legacy_service.get_document(doc_id)
        
        # 2. 从文件系统加载最新内容
        file_content = self.hybrid_storage.load_knowledge(doc_id)
        if file_content:
            document["content"] = file_content
        
        return document
    
    def update_document(self, doc_id: str, title: str = None, content: str = None, tags: list = None) -> bool:
        """更新文档
        
        Args:
            doc_id: 文档ID
            title: 文档标题
            content: 文档内容
            tags: 标签列表
            
        Returns:
            是否成功
        """
        # 1. 更新数据库
        success = self.legacy_service.update_document(doc_id, title, content, tags)
        
        # 2. 更新文件系统
        if success:
            document = self.legacy_service.get_document(doc_id)
            self.hybrid_storage.save_knowledge(
                doc_id=doc_id,
                title=document["title"],
                content=content or document["content"],
                tags=tags or document["tags"]
            )
        
        return success
```

## 6. 性能优化策略

### 6.1 文件 I/O 优化

- **异步文件操作**：使用 `asyncio` + `aiofiles` 实现异步文件读写
- **内存缓存**：使用 `lru_cache` 缓存频繁访问的文件内容
- **批量操作**：批量读取和写入文件，减少 I/O 次数
- **压缩存储**：对大型文件使用压缩存储，减少磁盘空间占用

### 6.2 数据库优化

- **索引优化**：为常用查询字段创建索引
- **批量插入**：使用批量插入减少数据库操作次数
- **事务管理**：合理使用事务，确保数据一致性
- **连接池**：使用连接池管理数据库连接，减少连接开销

### 6.3 向量计算优化

- **增量索引**：支持向量索引的增量更新，避免全量重建
- **缓存机制**：缓存高频查询的向量结果
- **批处理**：批量处理向量计算，提高计算效率
- **轻量级模型**：使用轻量级的嵌入模型，减少计算开销

## 7. 部署与迁移策略

### 7.1 部署步骤

1. **初始化目录结构**：运行目录初始化脚本
2. **配置存储服务**：更新配置文件，指定存储路径
3. **注册事件监听器**：确保数据库与文件系统的同步
4. **启动服务**：启动应用服务

### 7.2 数据迁移策略

1. **备份现有数据**：备份现有的数据库和文件
2. **数据导出**：将现有记忆和知识库导出为 Markdown 文件
3. **数据导入**：将导出的文件导入到新的存储架构中
4. **验证迁移**：验证迁移后的数据完整性
5. **切换服务**：切换到新的存储架构

### 7.3 回退策略

1. **保留旧系统**：在迁移过程中保留旧的存储系统
2. **双写模式**：在验证期间同时写入新旧系统
3. **快速回退**：如果出现问题，快速切换回旧系统

## 8. 测试计划

### 8.1 单元测试

- **存储适配器测试**：测试文件和数据库操作
- **同步服务测试**：测试数据库与文件系统的同步
- **集成测试**：测试与现有系统的集成

### 8.2 性能测试

- **文件 I/O 性能**：测试文件读写速度
- **数据库性能**：测试数据库操作速度
- **同步性能**：测试同步操作的开销
- **检索性能**：测试记忆和知识库的检索速度

### 8.3 可靠性测试

- **数据一致性测试**：测试数据库与文件系统的一致性
- **故障恢复测试**：测试系统在故障后的恢复能力
- **并发测试**：测试多用户并发操作的稳定性

## 9. 结论

混合存储架构通过结合数据库和文件系统的优势，为 Py Copilot 提供了更高效、可靠、用户友好的存储解决方案。该架构不仅保留了现有系统的功能完整性，还提升了数据的透明度、可移植性和可扩展性。

通过分阶段实施该方案，Py Copilot 将逐步实现存储架构的现代化，为用户提供更好的使用体验，同时为未来的功能扩展奠定坚实的基础。