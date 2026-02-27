# 设置功能合并方案 V8（完整最终版 + 官方能力 + 智能体分类）

## 1. 方案概述

本方案整合V1-V7的所有内容，并新增：
1. **官方能力标注与保护**：应用内置的官方能力需要特殊标识和保护
2. **智能体分类体系**：单一功能智能体 vs 复合智能体

**核心目标**：
1. 删除冗余功能，简化系统
2. 建设统一的能力中心（含官方能力保护）
3. 重构智能体管理，支持单一/复合两种模式
4. 优化导航结构，提升用户体验

## 2. 功能删除与整合清单

### 2.1 需要删除的功能

| 功能 | 当前位置 | 删除原因 | 替代方案 |
|-----|---------|---------|---------|
| **搜索管理** | 设置内子页面 | 搜索本质是工具，不应独立管理 | 整合到能力中心的工具管理 |
| **独立工具页面** | `/tool` | 入口分散，与技能管理分离 | 整合到能力中心 |
| **MCP客户端配置** | MCP服务页面 | 与工具概念重叠 | 作为工具类型在能力中心管理 |
| **Agent的skills JSON字段** | agent表 | 缺乏关联和配置能力 | 迁移到关联表 |

### 2.2 需要整合的功能

| 功能 | 原位置 | 整合目标 | 整合方式 |
|-----|-------|---------|---------|
| **网络搜索** | 搜索管理 | 能力中心-工具 | 作为"网络搜索工具" |
| **知识库检索** | 知识库/搜索管理 | 能力中心-工具 | 作为"知识库检索工具" |
| **工具管理** | `/tool`页面 | 能力中心 | 统一入口管理 |
| **技能管理** | 设置子页面 | 能力中心 | 统一入口管理 |
| **MCP工具** | MCP服务页面 | 能力中心-工具 | 作为"MCP工具"类型 |
| **模型能力标签** | 模型管理 | 保持独立 | 与能力中心关联但不合并 |

### 2.3 保持独立的功能

| 功能 | 位置 | 保持独立原因 |
|-----|-----|-------------|
| **全局记忆** | 设置 | 属于数据层，非能力层 |
| **知识库管理** | 独立页面 | 知识管理是独立功能，检索只是其中一部分 |
| **MCP服务端** | 设置 | 服务暴露配置，与客户端工具不同 |
| **模型管理** | 设置 | 模型能力 ≠ 外部能力，概念不同 |
| **工作流编排** | 独立页面 | 能力编排层，与能力管理不同 |

## 3. 官方能力体系 ⭐ 新增

### 3.1 官方能力定义

**官方能力**是指应用内置的、由官方提供和维护的能力，具有以下特征：
- 🏛️ **官方标识**：带有官方徽章
- 🔒 **不可删除**：用户无法删除，只能启用/禁用
- 🔄 **自动更新**：随应用版本自动更新
- 📋 **标准实现**：经过严格测试的标准实现

### 3.2 官方能力分类

```
官方能力
├── 🛠️ 官方工具（Official Tools）
│   ├── 文件读取工具
│   ├── 代码执行工具
│   ├── 网络搜索工具 ⭐（原搜索管理）
│   ├── 知识库检索工具 ⭐（原知识库搜索）
│   ├── 计算器工具
│   └── 时间日期工具
│
├── 📝 官方技能（Official Skills）
│   ├── 代码审查助手
│   ├── 翻译专家
│   ├── 文案生成器
│   └── 文档总结助手
│
└── 🔌 官方MCP适配器（Official MCP Adapters）
    ├── 文件系统适配器
    └── 数据库适配器
```

### 3.3 官方能力数据结构

```python
class CapabilitySource(Enum):
    """能力来源枚举"""
    OFFICIAL = "official"      # 官方内置
    MARKETPLACE = "marketplace" # 市场安装
    USER_CREATED = "user"      # 用户创建
    MCP_REMOTE = "mcp"         # MCP远程


class Tool(Base):
    """工具模型 - 扩展官方标识"""
    __tablename__ = "tools"
    
    # 基础字段（已有）
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 新增：官方能力标识
    source = Column(String(50), default=CapabilitySource.USER_CREATED.value)
    is_official = Column(Boolean, default=False)  # 是否为官方能力
    is_builtin = Column(Boolean, default=False)   # 是否为内置（不可删除）
    official_badge = Column(String(50))           # 官方徽章标识
    
    # 保护机制
    is_system = Column(Boolean, default=False)    # 系统级，完全不可修改
    is_protected = Column(Boolean, default=False) # 受保护，可禁用不可删除
    allow_disable = Column(Boolean, default=True) # 允许禁用
    allow_edit = Column(Boolean, default=True)    # 允许编辑配置
    
    # 版本管理
    version = Column(String(50), default="1.0.0")
    min_app_version = Column(String(50))          # 最低应用版本要求
    update_mode = Column(String(20), default="manual")  # auto / manual
    
    # 元数据
    metadata = Column(JSON, default=dict)
    
    # 与Agent的关系
    agent_associations = relationship("AgentToolAssociation", back_populates="tool")


class Skill(Base):
    """技能模型 - 扩展官方标识"""
    __tablename__ = "skills"
    
    # 基础字段（已有）
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    
    # 新增：官方能力标识（同Tool）
    source = Column(String(50), default=CapabilitySource.USER_CREATED.value)
    is_official = Column(Boolean, default=False)
    is_builtin = Column(Boolean, default=False)
    official_badge = Column(String(50))
    
    is_system = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)
    allow_disable = Column(Boolean, default=True)
    allow_edit = Column(Boolean, default=True)
    
    version = Column(String(50), default="1.0.0")
    min_app_version = Column(String(50))
    update_mode = Column(String(20), default="manual")
    
    # 与Agent的关系
    agent_associations = relationship("AgentSkillAssociation", back_populates="skill")
```

### 3.4 官方能力UI标识

```
能力列表展示：
┌─────────────────────────────────────────────────────────────┐
│ 📄 文件读取工具                              [本地工具] 🏛️  │
│ 读取本地文件内容，支持多种格式                              │
│ 🏷️ 文件操作  🏷️ 官方                                       │
│ [配置] [禁用]                                              │  ← 官方能力：可配置、可禁用，不可删除
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🔍 网络搜索工具                              [本地工具] 🏛️  │
│ 执行网络搜索，支持Google/Bing/Baidu                       │
│ 🏷️ 搜索  🏷️ 官方                                           │
│ [配置] [禁用]                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📝 我的自定义Skill                           [提示词技能]   │
│ 我自己创建的提示词模板                                      │
│ 🏷️ 自定义                                                  │
│ [编辑] [测试] [删除]                                       │  ← 自定义能力：可编辑、可删除
└─────────────────────────────────────────────────────────────┘
```

### 3.5 官方能力保护规则

| 类型 | 删除 | 禁用 | 编辑配置 | 编辑代码 |
|-----|-----|-----|---------|---------|
| **系统级** (is_system=True) | ❌ 不可 | ❌ 不可 | ❌ 不可 | ❌ 不可 |
| **受保护** (is_protected=True) | ❌ 不可 | ✅ 可 | ✅ 可 | ❌ 不可 |
| **标准官方** (is_official=True) | ❌ 不可 | ✅ 可 | ✅ 可 | ⚠️ 警告 |
| **自定义** | ✅ 可 | ✅ 可 | ✅ 可 | ✅ 可 |

## 4. 智能体分类体系 ⭐ 新增

### 4.1 智能体类型定义

```
智能体分类
├── 🎯 单一功能智能体（Single-Purpose Agent）
│   ├── 定义：专注于单一任务，使用单一能力
│   ├── 特点：简单、快速、专业
│   ├── 示例：
│   │   ├── 💬 聊天助手（仅对话，无特殊能力）
│   │   ├── 🌐 翻译专家（仅翻译Skill）
│   │   ├── 🎨 图像生成器（仅图像生成Tool）
│   │   ├── 🔍 搜索助手（仅搜索Tool）
│   │   └── 📝 文案生成器（仅文案Skill）
│   └── 配置：1个主能力 + 基础对话能力
│
└── 🔧 复合智能体（Composite Agent）
    ├── 定义：具备多种能力，可完成复杂任务
    ├── 特点：灵活、强大、可编排
    ├── 示例：
    │   ├── 🤖 全能助手（翻译+搜索+代码+文案）
    │   ├── 👨‍💻 开发助手（代码审查+代码生成+文档查询）
    │   ├── 📊 数据分析助手（搜索+计算+可视化+报告生成）
    │   └── 🎓 学习助手（翻译+总结+记忆+知识库）
    └── 配置：多个能力 + 能力编排规则
```

### 4.2 智能体类型数据结构

```python
class AgentType(Enum):
    """智能体类型枚举"""
    SINGLE_PURPOSE = "single"      # 单一功能
    COMPOSITE = "composite"        # 复合功能
    WORKFLOW = "workflow"          # 工作流驱动（未来扩展）


class Agent(Base):
    """智能体模型 - V8版本（支持类型区分）"""
    __tablename__ = "agents"
    
    # 基础信息
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    avatar = Column(String(50))
    
    # 新增：智能体类型
    agent_type = Column(String(50), default=AgentType.SINGLE_PURPOSE.value)
    
    # 角色定义
    prompt = Column(Text, nullable=False)
    role_config = Column(JSON, default=dict)
    
    # 能力组合关系
    skill_associations = relationship("AgentSkillAssociation", back_populates="agent")
    tool_associations = relationship("AgentToolAssociation", back_populates="agent")
    mcp_associations = relationship("AgentMCPAssociation", back_populates="agent")
    
    # 单一功能智能体配置
    primary_capability_id = Column(Integer)           # 主能力ID
    primary_capability_type = Column(String(50))      # 主能力类型：skill/tool/mcp
    
    # 复合智能体配置
    capability_orchestration = Column(JSON, default=dict)
    # {
    #     "mode": "auto",           # auto / sequential / conditional
    #     "rules": [...],           # 能力调用规则
    #     "fallback_order": [...]   # 能力回退顺序
    # }
    
    # 模型配置
    default_model = Column(Integer, ForeignKey("models.id"))
    fallback_model = Column(Integer, ForeignKey("models.id"))
    model_parameters = Column(JSON, default=dict)
    
    # 上下文配置
    knowledge_base_ids = Column(JSON, default=list)
    memory_config = Column(JSON, default=dict)
    
    # 执行配置
    execution_config = Column(JSON, default=dict)
    
    # 官方智能体标识
    is_official = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)      # 是否为模板
    template_category = Column(String(50))            # 模板分类
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 4.3 单一功能智能体配置

```python
class SinglePurposeAgentConfig:
    """单一功能智能体配置示例"""
    
    # 示例：翻译专家
    TRANSLATION_EXPERT = {
        "name": "翻译专家",
        "agent_type": "single",
        "description": "专业的多语言翻译助手",
        "prompt": "你是一个专业的翻译专家，擅长多种语言之间的准确翻译...",
        "primary_capability": {
            "type": "skill",
            "id": "translation_skill",
            "name": "专业翻译"
        },
        "model_config": {
            "default_model": "gpt-4",
            "temperature": 0.3  # 翻译需要确定性
        },
        "execution_config": {
            "auto_trigger": True,      # 自动识别翻译需求
            "show_capability_indicator": True  # 显示能力指示器
        }
    }
    
    # 示例：图像生成器
    IMAGE_GENERATOR = {
        "name": "图像生成器",
        "agent_type": "single",
        "description": "根据描述生成图像",
        "prompt": "你是一个图像生成助手，可以根据用户的描述生成图像...",
        "primary_capability": {
            "type": "tool",
            "id": "image_generation_tool",
            "name": "图像生成"
        },
        "model_config": {
            "default_model": "dall-e-3"
        }
    }
```

### 4.4 复合智能体配置

```python
class CompositeAgentConfig:
    """复合智能体配置示例"""
    
    # 示例：全能助手
    UNIVERSAL_ASSISTANT = {
        "name": "全能助手",
        "agent_type": "composite",
        "description": "具备多种能力的通用助手",
        "prompt": "你是一个全能助手，可以根据用户需求调用不同的能力...",
        "capabilities": [
            {"type": "skill", "id": "translation_skill", "priority": 1},
            {"type": "tool", "id": "search_tool", "priority": 2},
            {"type": "skill", "id": "code_review_skill", "priority": 3},
            {"type": "skill", "id": "writing_skill", "priority": 4}
        ],
        "orchestration": {
            "mode": "auto",           # 自动选择能力
            "intent_mapping": {       # 意图映射
                "翻译": ["translation_skill"],
                "搜索": ["search_tool"],
                "代码": ["code_review_skill"],
                "写": ["writing_skill"]
            },
            "multi_capability": True,  # 支持多能力组合
            "context_sharing": True    # 能力间共享上下文
        }
    }
```

### 4.5 智能体创建向导（按类型区分）

```
创建智能体
├── 🎯 选择智能体类型
│   ├── ○ 单一功能智能体（简单、专注）
│   └── ○ 复合智能体（强大、灵活）
│
├── 步骤1: 基础信息（共用）
│   ├── 名称
│   ├── 头像
│   └── 描述
│
├── 🎯 单一功能路径
│   ├── 步骤2: 选择主能力
│   │   ├── 从能力中心选择1个能力
│   │   │   ├── 📝 翻译Skill
│   │   │   ├── 🔍 搜索Tool
│   │   │   ├── 🎨 图像生成Tool
│   │   │   └── ...
│   │   └── 预览能力效果
│   │
│   ├── 步骤3: 角色定义（简化）
│   │   ├── 系统提示词（可选预设模板）
│   │   └── 性格特征（可选）
│   │
│   └── 步骤4: 模型配置
│       └── 选择适合该能力的模型
│
└── 🔧 复合智能体路径
    ├── 步骤2: 能力组合
    │   ├── 从能力中心选择多个能力
    │   │   ├── ✅ 翻译Skill
    │   │   ├── ✅ 搜索Tool
    │   │   ├── ✅ 代码Skill
    │   │   └── ...
    │   ├── 设置能力优先级
    │   └── 配置能力编排规则
    │       ├── 自动模式（推荐）
    │       ├── 顺序模式
    │       └── 条件模式
    │
    ├── 步骤3: 角色定义（完整）
    │   ├── 系统提示词
    │   ├── 性格特征
    │   └── 能力协调策略
    │
    ├── 步骤4: 模型配置
    │   ├── 默认模型
    │   ├── 备用模型
    │   └── 参数调优
    │
    └── 步骤5: 上下文配置
        ├── 知识库关联
        └── 记忆策略
```

### 4.6 智能体市场分类

```
智能体市场
├── 🏛️ 官方智能体
│   ├── 单一功能
│   │   ├── 💬 基础聊天助手
│   │   ├── 🌐 翻译专家
│   │   ├── 📝 文案生成器
│   │   └── 🔍 搜索助手
│   └── 复合功能
│       ├── 🤖 全能助手
│       ├── 👨‍💻 开发助手
│       └── 📊 数据分析助手
│
├── 🌟 热门智能体
│   └── 社区最受欢迎的模板
│
├── 🎯 单一功能模板
│   ├── 按能力分类
│   │   ├── 翻译类
│   │   ├── 搜索类
│   │   ├── 生成类
│   │   └── ...
│   └── 按场景分类
│       ├── 办公场景
│       ├── 开发场景
│       └── 学习场景
│
└── 🔧 复合智能体模板
    ├── 按领域分类
    │   ├── 开发领域
    │   ├── 写作领域
    │   ├── 数据分析领域
    │   └── ...
    └── 按复杂度分类
        ├── 简单组合（2-3个能力）
        ├── 中等组合（4-6个能力）
        └── 复杂组合（7+个能力）
```

## 5. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              应用层                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    聊天      │  │   工作流     │  │   Agent      │  │   知识库     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────────────────────┤
│                           智能体层 (Agent Layer)                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        智能体市场                                     │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐                  │  │
│  │  │   🏛️ 官方智能体     │  │   🌟 社区智能体     │                  │  │
│  │  │   • 单一功能        │  │   • 单一功能        │                  │  │
│  │  │   • 复合功能        │  │   • 复合功能        │                  │  │
│  │  └─────────────────────┘  └─────────────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        我的智能体                                     │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐                  │  │
│  │  │   🎯 单一功能       │  │   🔧 复合智能体     │                  │  │
│  │  │   • 1个主能力       │  │   • 多能力组合      │                  │  │
│  │  │   • 简单配置        │  │   • 编排规则        │                  │  │
│  │  └─────────────────────┘  └─────────────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                           能力中心层 (Capability Hub)                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        能力市场                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │  │
│  │  │  Skill市场   │  │  Tool市场   │  │  MCP市场    │                  │  │
│  │  │  • 🏛️ 官方  │  │  • 🏛️ 官方  │  │  • 官方     │                  │  │
│  │  │  • 社区     │  │  • 社区     │  │  • 第三方   │                  │  │
│  │  │  • GitHub   │  │  • MCP      │  │  • 自定义   │                  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        我的能力                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │  │
│  │  │  🏛️ 官方Skill│  │  🏛️ 官方Tool │  │  我的MCP    │                  │  │
│  │  │  我的Skill   │  │  我的Tool    │  │             │                  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        开发中心                                       │  │
│  │  • 创建Skill  • 创建Tool  • 配置MCP                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                          基础设施层（已有）                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Skill发现    │  │ Skill解析    │  │ Skill执行    │  │ Tool注册     │    │
│  │ ✅ 已存在    │  │ ✅ 已存在    │  │ ✅ 已存在    │  │ ✅ 已存在    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ MCP客户端    │  │ 模型管理     │  │ 知识库       │  │ 全局记忆     │    │
│  │ ✅ 已存在    │  │ ✅ 已存在    │  │ ✅ 已存在    │  │ ✅ 已存在    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6. 导航结构重构

### 6.1 新导航结构

```
主导航
├── 💬 聊天
│   └── 可选择带能力的智能体
│
├── 🛠️ 能力中心 ⭐（整合所有能力）
│   ├── 我的能力
│   │   ├── 🏛️ 官方能力（不可删除）
│   │   │   ├── 官方Skill
│   │   │   └── 官方Tool
│   │   ├── 我的Skill（自定义）
│   │   ├── 我的Tool（自定义）
│   │   └── 我的MCP
│   ├── 能力市场
│   │   ├── Skill市场（官方+社区+GitHub）
│   │   ├── Tool市场（官方+社区+MCP）
│   │   └── MCP市场
│   └── 开发中心
│       ├── 创建Skill
│       ├── 创建Tool
│       └── 配置MCP
│
├── 🤖 智能体管理 ⭐（按类型分类）
│   ├── 我的智能体
│   │   ├── 🎯 单一功能（简单、专注）
│   │   └── 🔧 复合智能体（多能力）
│   ├── 创建智能体
│   │   ├── 🎯 创建单一功能智能体（3步向导）
│   │   └── 🔧 创建复合智能体（5步向导）
│   └── 智能体市场
│       ├── 🏛️ 官方智能体
│       ├── 🎯 单一功能模板
│       └── 🔧 复合智能体模板
│
├── 🔄 工作流
│   └── 可使用Skill节点、Tool节点、Agent节点
│
├── 🧠 知识库
│   ├── 知识库管理
│   └── 文档管理
│
└── ⚙️ 设置
    ├── 模型管理
    ├── 全局记忆
    ├── MCP服务端
    └── 系统设置
```

## 7. 数据模型设计

### 7.1 官方能力相关表

```python
# Tool和Skill模型扩展（见第3节）
# 主要新增字段：
# - is_official: 是否为官方
# - is_builtin: 是否为内置
# - is_system: 是否为系统级
# - is_protected: 是否受保护
# - allow_disable: 是否允许禁用
# - allow_edit: 是否允许编辑
```

### 7.2 智能体类型相关表

```python
# Agent模型扩展（见第4节）
# 主要新增字段：
# - agent_type: 智能体类型（single/composite）
# - primary_capability_id: 单一功能主能力ID
# - primary_capability_type: 单一功能主能力类型
# - capability_orchestration: 复合智能体编排配置
# - is_official: 是否为官方智能体
# - is_template: 是否为模板
# - template_category: 模板分类
```

### 7.3 完整的关联表

```python
# 1. 智能体-Skill关联（已有扩展）
class AgentSkillAssociation(Base):
    """智能体与Skill关联"""
    __tablename__ = "agent_skill_associations"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"))
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"))
    
    # 配置字段
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    trigger_mode = Column(String(20), default="auto")
    trigger_conditions = Column(JSON, default=dict)
    parameter_override = Column(JSON, default=dict)
    
    # 单一功能智能体标识
    is_primary = Column(Boolean, default=False)  # 是否为主能力
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 2. 智能体-Tool关联
class AgentToolAssociation(Base):
    """智能体与Tool关联"""
    __tablename__ = "agent_tool_associations"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"))
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"))
    
    enabled = Column(Boolean, default=True)
    execution_mode = Column(String(20), default="confirm")
    default_parameters = Column(JSON, default=dict)
    usage_limits = Column(JSON, default=dict)
    
    # 单一功能智能体标识
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 3. 智能体-MCP关联
class AgentMCPAssociation(Base):
    """智能体与MCP关联"""
    __tablename__ = "agent_mcp_associations"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"))
    mcp_config_id = Column(Integer, ForeignKey("mcp_server_configs.id", ondelete="CASCADE"))
    
    enabled = Column(Boolean, default=True)
    auto_connect = Column(Boolean, default=True)
    enabled_tools = Column(JSON, default=list)
    permissions = Column(JSON, default=dict)
    
    # 单一功能智能体标识
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## 8. 实施计划

### 8.1 第一阶段：数据迁移（1周）

1. **创建新表**
   - 扩展 `Tool` 模型（官方能力字段）
   - 扩展 `Skill` 模型（官方能力字段）
   - 扩展 `Agent` 模型（类型字段）
   - 创建关联表

2. **数据迁移**
   - 标记现有官方能力
   - 迁移 `Agent.skills` JSON字段
   - 设置默认智能体类型

### 8.2 第二阶段：能力中心（2周）

1. **官方能力标识**
   - 后端：官方能力保护逻辑
   - 前端：官方徽章展示
   - 权限：删除/编辑控制

2. **能力中心页面**
   - 我的能力（区分官方/自定义）
   - 能力市场
   - 开发中心

### 8.3 第三阶段：智能体分类（2周）

1. **后端开发**
   - 智能体类型逻辑
   - 单一/复合配置处理
   - 能力编排引擎

2. **前端开发**
   - 智能体列表分类展示
   - 单一功能创建向导（3步）
   - 复合智能体创建向导（5步）

### 8.4 第四阶段：删除旧功能（1周）

1. 删除旧页面
2. 清理代码
3. 删除废弃字段

### 8.5 第五阶段：工作流整合（1周）

1. 工作流节点
2. Agent节点支持

## 9. 总结

### 9.1 V8新增内容

| 需求 | 实现方案 |
|-----|---------|
| **官方能力标注** | `is_official` + `is_protected` + 官方徽章 + 保护规则 |
| **单一功能智能体** | `agent_type=single` + `primary_capability` + 3步向导 |
| **复合智能体** | `agent_type=composite` + `capability_orchestration` + 5步向导 |

### 9.2 完整功能清单

**能力中心**：
- ✅ 官方能力（🏛️ 标识，不可删除）
- ✅ 自定义能力（可编辑、可删除）
- ✅ 能力市场（多源整合）
- ✅ 开发中心

**智能体管理**：
- ✅ 单一功能智能体（简单、专注）
- ✅ 复合智能体（多能力编排）
- ✅ 官方智能体模板
- ✅ 社区智能体模板

**已删除/整合**：
- ❌ 搜索管理 → 整合到工具
- ❌ 独立工具页面 → 整合到能力中心
- ❌ MCP客户端配置 → 整合到工具

### 9.3 实施周期

**总计：7周**
- 第1周：数据迁移
- 第2-3周：能力中心（含官方能力）
- 第4-5周：智能体分类（单一/复合）
- 第6周：删除旧功能
- 第7周：工作流整合
