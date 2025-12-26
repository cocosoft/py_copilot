# 参数管理优化建议

## 任务跟踪

| 阶段 | 任务 | 状态 | 完成日期 |
|------|------|------|----------|
| **Phase 1** | 数据库层 | | |
| 1.1 | 创建 agent_parameters 表 | ✅ 已完成 | 2025-01-25 |
| 1.2 | 简化 ParameterTemplate 模型 | ✅ 已完成 | 2025-01-25 |
| **Phase 2** | 服务层 | | |
| 2.1 | 实现 AgentParameterManager | ✅ 已完成 | 2025-01-25 |
| 2.2 | 从参数管理移除能力相关内容 | ✅ 已完成 | 2025-01-25 |
| 2.3 | 实现参数继承链服务 | ✅ 已完成 | 2025-01-25 |
| 2.4 | 实现 ParameterPassingService | ✅ 已完成 | 2025-01-25 |
| **Phase 3** | API层 | | |
| 3.1 | 实现智能体参数 API 端点 | ✅ 已完成 | 2025-01-25 |
| **Phase 4** | LLM服务集成 | | |
| 4.1 | 更新 LLM 服务以使用数据库参数 | ✅ 已完成 | 2025-01-26 |
| **Phase 5** | 测试与验证 | | |
| 5.1 | 单元测试 | ✅ 已完成 | 2025-01-26 |
| 5.2 | 集成测试 | ✅ 已完成 | 2025-01-26 |

> 注：✅ 已完成 ⏳ 待进行 🔄 进行中

## 一、现状分析

### 1.1 当前系统架构

经过对代码库的全面分析，现有参数管理系统包含以下层级：

1. **系统级参数** (`SystemParameterManager`)
   - 通过 `ParameterTemplate` 实现
   - 支持系统级别的参数模板管理
   - 存储在 `parameter_templates` 表

2. **模型类型级参数** (`ModelCategory`)
   - `default_parameters` 字段存储 JSON 格式默认参数
   - 关联到 `model_categories` 表

3. **模型级参数** (`ModelParameter`)
   - 存储在 `model_parameters` 表
   - 支持 `parameter_source` 区分来源（model_type/model）
   - 支持 `is_override` 标识覆盖状态

4. **模型能力** (`ModelCapability`)
   - 独立于参数管理的系统
   - 存储在 `model_capabilities` 表
   - 通过 `model_capability_associations` 关联到模型

5. **智能体参数**
   - **当前未实现任何参数管理**
   - `Agent` 模型仅有 `prompt` 字段

### 1.2 发现的问题

1. **系统级参数与模型参数分离**
   - 造成职责不清，配置分散
   - 用户需要在多个位置配置相似参数

2. **智能体参数完全缺失**
   - 作为核心使用层，缺少参数配置能力
   - 无法为不同智能体设置不同参数

3. **模型能力定位模糊**
   - 能力是"发现的"属性，不是"配置的"参数
   - 当前与参数管理混在一起，造成混乱

4. **层级过多且冗余**
   - 系统级 + 类型级 + 模型级 = 三层
   - 实际使用中，用户只关心最终参数值

5. **参数模板与默认参数重复**
   - `ParameterTemplate` 和 `default_parameters` 功能重复

### 1.3 实际应用情况分析

#### 1.3.1 LLM服务层存在硬编码参数

在 `llm_service.py:41-48` 中发现：

```python
return self.text_completion(
    prompt=prompt,
    model_name=kwargs.get("model_name"),
    max_tokens=kwargs.get("max_tokens", 1000),  # 硬编码
    temperature=kwargs.get("temperature", 0.7)   # 硬编码
)
```

这意味着：
- 参数管理系统与实际LLM调用完全脱节
- 无论参数管理配置如何，实际调用都使用默认值
- 用户无法通过参数管理系统控制实际的模型行为

#### 1.3.2 Agent模型缺乏参数配置能力

当前的Agent模型（`agent.py:12-35`）只包含：

```python
class Agent(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    avatar = Column(String(50))
    prompt = Column(Text, nullable=False)  # 只能配置提示词
    knowledge_base = Column(String(100))
    # ... 没有任何参数配置字段
```

这导致：
- Agent无法独立配置模型参数
- Agent与模型参数管理没有关联
- 用户体验层缺少参数控制能力

#### 1.3.3 参数传递链路断裂

```
参数管理 → ModelParameter → ModelDB
    ↓
Agent（无参数配置）→ AgentScheduler → LLM服务
    ↓
硬编码参数覆盖（temperature=0.7, max_tokens=1000）
```

当前系统中，参数管理系统的配置无法传递到实际的LLM调用，造成配置失效。

---

## 二、优化建议

### 2.1 设计原则

**核心原则：简化层级，职责分离**

1. **只管理"可配置的"内容**
   - 参数 = 需要用户配置的数值
   - 能力 = 模型固有的属性（不应在参数系统中管理）

2. **保留必要的继承层级**
   - 避免完全扁平化，保留类型到模型的继承
   - 减少不必要的复杂度

3. **统一智能体和模型的参数管理**
   - 智能体是最重要的使用入口
   - 应该支持完整的参数配置能力

### 2.2 推荐的四层参数架构

```
┌─────────────────────────────────────────────────────────────┐
│                    参数配置优先级（从高到低）                   │
├─────────────────────────────────────────────────────────────┤
│  1. 智能体级参数 (Agent Parameters)                          │
│      - 智能体独有的运行参数                                   │
│      - 优先级最高，覆盖所有下层                               │
├─────────────────────────────────────────────────────────────┤
│  2. 模型级参数 (Model Parameters)                            │
│      - 具体模型的特定参数                                     │
│      - 可以覆盖模型类型的默认配置                             │
├─────────────────────────────────────────────────────────────┤
│  3. 模型类型级参数 (Model Type Parameters)                   │
│      - 同一类型模型的默认参数                                 │
│      - 如所有 Chat 模型共享 temperature=0.7                  │
├─────────────────────────────────────────────────────────────┤
│  4. 系统级参数 (System Parameters)                           │
│      - 全局默认参数                                           │
│      - 所有模型的兜底配置                                     │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 关键决策：模型能力是否纳入参数管理？

**建议：不纳入参数管理系统**

#### 理由：

1. **本质区别**
   - **参数 (Parameters)**：可配置的输入值，用户可以修改
   - **能力 (Capabilities)**：模型固有的能力，是发现的属性

2. **配置方式不同**
   - 参数需要值（如 temperature=0.7）
   - 能力是布尔或强度（如 supports_vision=true）

3. **管理目标不同**
   - 参数管理：简化配置，减少重复
   - 能力管理：发现和展示模型的能力边界

4. **当前实现已经分离**
   - `ModelCapability` 是独立的系统
   - 建议保持分离，但可以增强关联显示

#### 建议做法：

```
┌──────────────────┐     ┌──────────────────┐
│   参数管理系统    │     │   能力管理系统    │
│  (Parameter)     │     │  (Capability)    │
├──────────────────┤     ├──────────────────┤
│ - System Params  │     │ - ModelCapability│
│ - Type Params    │     │ - Capability     │
│ - Model Params   │     │   Association    │
│ - Agent Params   │     │ - Strength       │
└──────────────────┘     │   Assessment     │
                         └──────────────────┘
                                │
                                ▼
                    显示在模型详情页，但不混在一起
```

---

## 三、具体实施建议

### 3.1 保留的层级

| 层级 | 存储位置 | 职责 | 优先级 |
|------|----------|------|--------|
| 系统级 | `parameter_templates` (level=system) | 全局默认配置 | 最低 |
| 模型类型级 | `model_categories.default_parameters` | 类型默认配置 | 第三 |
| 模型级 | `model_parameters` | 模型特定配置 | 第二 |
| **新增：智能体级** | `agent_parameters` (新建表) | 智能体运行配置 | 最高 |

### 3.2 移除/简化的内容

| 内容 | 当前状态 | 建议 | 原因 |
|------|----------|------|------|
| ParameterTemplate 多级模板 | 存在 | 简化为仅系统级 | 功能重复 |
| ModelParameter.parameter_source | 存在 | 保留 | 用于继承追溯 |
| ModelParameter.is_override | 存在 | 保留 | 用于覆盖标识 |
| AgentParameter.is_override | 新增 | **移除** | Agent参数本身就是最高优先级，无需额外标识 |
| ModelCapability 关联参数 | 存在 | 移除 | 能力不应是参数 |

### 3.3 新增：智能体参数表

```python
class AgentParameter(Base):
    """智能体参数表"""
    __tablename__ = "agent_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    parameter_value = Column(Text, nullable=False)
    parameter_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    parameter_group = Column(String(50), nullable=True)  # 参数分组，用于前端展示
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    agent = relationship("Agent", back_populates="parameters")
    
    __table_args__ = (
        UniqueConstraint('agent_id', 'parameter_name', name='uq_agent_parameter_name'),
    )
```

### 3.4 Agent 与 Model 的关联方式

**设计决策：Agent 通过参数关联 Model，而非直接外键关联**

```python
class Agent(Base):
    """智能体表模型 - 更新后"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    avatar = Column(String(50))
    prompt = Column(Text, nullable=False)
    knowledge_base = Column(String(100))
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="agents")
    
    is_public = Column(Boolean, default=False)
    is_recommended = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    category_id = Column(Integer, ForeignKey("agent_categories.id"), nullable=True)
    category = relationship("AgentCategory", back_populates="agents")
    
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    
    # Agent参数关系
    parameters = relationship("AgentParameter", back_populates="agent", cascade="all, delete-orphan")
```

**关联方式说明：**

| 关联方式 | 优点 | 缺点 |
|----------|------|------|
| **参数关联（选用）** | 灵活性高，支持动态切换模型 | 查询时需要额外解析 |
| 直接外键关联 | 查询简单，性能高 | 灵活性低，切换模型需修改记录 |

**参数关联实现：**

Agent 通过 `model_name` 参数关联到具体的 Model：

```python
# AgentParameter 示例
{
    "parameter_name": "model_name",
    "parameter_value": "gpt-4",
    "parameter_type": "string",
    "description": "指定智能体使用的模型名称",
    "parameter_group": "model_selection"
}
```

### 3.5 参数分组设计

#### 3.5.1 参数分组定义

```python
PARAMETER_GROUPS = {
    "model_selection": {
        "name": "模型选择",
        "description": "选择智能体使用的底层模型",
        "order": 1,
        "parameters": ["model_name"]
    },
    "generation": {
        "name": "生成参数",
        "description": "控制文本生成的质量和风格",
        "order": 2,
        "parameters": ["temperature", "top_p", "max_tokens", "presence_penalty", "frequency_penalty"]
    },
    "safety": {
        "name": "安全参数",
        "description": "控制内容过滤和安全级别",
        "order": 3,
        "parameters": ["response_mime_type"]
    },
    "advanced": {
        "name": "高级参数",
        "description": "专家级参数调整",
        "order": 4,
        "parameters": ["logprobs", "top_logprobs"]
    }
}
```

#### 3.5.2 各分组详细说明

| 分组 | 参数名 | 类型 | 默认值 | 有效范围 | 帮助信息 |
|------|--------|------|--------|----------|----------|
| **模型选择** | model_name | string | - | 有效模型名称列表 | 选择要使用的AI模型，不同模型有不同的能力和定价 |
| **生成参数** | temperature | float | 0.7 | 0.0-2.0 | 控制输出的随机性，值越高越有创意，值越低越确定性 |
| **生成参数** | top_p | float | 1.0 | 0.0-1.0 | 核采样概率阈值，越低越保守 |
| **生成参数** | max_tokens | int | 1000 | 1-4096 | 单次生成的最大token数量，影响回复长度 |
| **生成参数** | presence_penalty | float | 0.0 | -2.0-2.0 | 惩罚重复词汇，正值鼓励新词汇 |
| **生成参数** | frequency_penalty | float | 0.0 | -2.0-2.0 | 惩罚频繁词汇，正值降低重复率 |
| **安全参数** | response_mime_type | string | "text" | "text", "json_object" | 响应格式，json_object强制输出JSON |
| **高级参数** | logprobs | bool | false | true/false | 是否返回对数概率信息 |
| **高级参数** | top_logprobs | int | 0 | 0-20 | 每个位置返回的最可能token数量 |

### 3.6 参数校验规则

```python
PARAMETER_VALIDATION_RULES = {
    "temperature": {
        "type": "float",
        "min": 0.0,
        "max": 2.0,
        "step": 0.1,
        "default": 0.7
    },
    "top_p": {
        "type": "float",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01,
        "default": 1.0
    },
    "max_tokens": {
        "type": "int",
        "min": 1,
        "max": 4096,
        "step": 1,
        "default": 1000
    },
    "presence_penalty": {
        "type": "float",
        "min": -2.0,
        "max": 2.0,
        "step": 0.1,
        "default": 0.0
    },
    "frequency_penalty": {
        "type": "float",
        "min": -2.0,
        "max": 2.0,
        "step": 0.1,
        "default": 0.0
    },
    "response_mime_type": {
        "type": "enum",
        "values": ["text", "json_object"],
        "default": "text"
    },
    "model_name": {
        "type": "string",
        "required": True,
        "default": None
    }
}

class ParameterValidationError(Exception):
    """参数校验异常"""
    def __init__(self, parameter_name: str, message: str, value: Any):
        self.parameter_name = parameter_name
        self.message = message
        self.value = value
        super().__init__(f"参数校验失败 [{parameter_name}]: {message}")

def validate_parameter(parameter_name: str, value: Any) -> Any:
    """
    校验单个参数值，如果无效则抛出异常
    
    Args:
        parameter_name: 参数名称
        value: 参数值
        
    Returns:
        校验后的值（可能进行了类型转换）
        
    Raises:
        ParameterValidationError: 参数值无效
    """
    if parameter_name not in PARAMETER_VALIDATION_RULES:
        raise ParameterValidationError(
            parameter_name,
            f"未知参数: {parameter_name}",
            value
        )
    
    rule = PARAMETER_VALIDATION_RULES[parameter_name]
    
    # 类型转换
    if rule["type"] == "float":
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ParameterValidationError(
                parameter_name,
                f"需要浮点数，实际收到: {type(value).__name__}",
                value
            )
    elif rule["type"] == "int":
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ParameterValidationError(
                parameter_name,
                f"需要整数，实际收到: {type(value).__name__}",
                value
            )
    elif rule["type"] == "bool":
        if isinstance(value, str):
            value = value.lower() in ("true", "1", "yes")
        else:
            value = bool(value)
    
    # 枚举值校验
    if rule["type"] == "enum":
        if value not in rule["values"]:
            raise ParameterValidationError(
                parameter_name,
                f"有效值: {rule['values']}，实际收到: {value}",
                value
            )
        return value
    
    # 范围校验
    if "min" in rule and value < rule["min"]:
        raise ParameterValidationError(
            parameter_name,
            f"最小值为 {rule['min']}，实际收到: {value}",
            value
        )
    
    if "max" in rule and value > rule["max"]:
        raise ParameterValidationError(
            parameter_name,
            f"最大值为 {rule['max']}，实际收到: {value}",
            value
        )
    
    # 必需值校验
    if rule.get("required") and value is None:
        raise ParameterValidationError(
            parameter_name,
            "此参数为必需参数",
            value
        )
    
    return value
```

### 3.7 参数获取流程

```python
def get_final_parameters(
    db: Session,
    agent_id: int = None,
    model_id: int = None
) -> Dict[str, Any]:
    """
    获取最终生效的参数配置
    优先级：Agent > Model > ModelType > System
    所有参数值都从数据库动态读取
    
    Args:
        db: 数据库会话
        agent_id: 智能体ID（可选）
        model_id: 模型ID（可选，用于回退查询）
        
    Returns:
        合并后的完整参数配置字典
        
    Raises:
        ParameterValidationError: 参数值无效时抛出
    """
    params = {}
    
    # 1. 获取系统级参数（兜底）- 从数据库读取
    system_params = _get_system_defaults_from_db(db)
    params.update(system_params)
    
    resolved_model_id = model_id
    
    # 2. 如果有Agent，尝试从Agent参数中获取model_name
    if agent_id:
        agent_model_name = _get_agent_model_name(db, agent_id)
        if agent_model_name:
            # 通过model_name查询对应的model_id
            model = db.query(ModelDB).filter(
                ModelDB.name == agent_model_name
            ).first()
            if model:
                resolved_model_id = model.id
    
    # 3. 获取模型类型参数（覆盖系统级）- 从数据库读取
    if resolved_model_id:
        model = db.query(ModelDB).filter(ModelDB.id == resolved_model_id).first()
        if model and model.model_type_id:
            type_params = ModelCategoryManager.get_type_default_parameters(
                db, model.model_type_id
            )
            params.update(type_params)
        
        # 4. 获取模型参数（覆盖类型级）- 从数据库读取
        model_params = db.query(ModelParameter).filter(
            ModelParameter.model_id == resolved_model_id
        ).all()
        for param in model_params:
            validated_value = validate_parameter(
                param.parameter_name,
                param.parameter_value
            )
            params[param.parameter_name] = validated_value
        
        # 5. 获取智能体参数（最高优先级）- 从数据库读取
        if agent_id:
            agent_params = db.query(AgentParameter).filter(
                AgentParameter.agent_id == agent_id
            ).all()
            for param in agent_params:
                # 跳过model_name，它已经在步骤2中处理
                if param.parameter_name == "model_name":
                    continue
                validated_value = validate_parameter(
                    param.parameter_name,
                    param.parameter_value
                )
                params[param.parameter_name] = validated_value
    
    return params


def _get_system_defaults_from_db(db: Session) -> Dict[str, Any]:
    """
    从数据库获取系统级默认参数
    优先级：parameter_templates > 硬编码兜底
    """
    # 尝试从数据库获取
    templates = db.query(ParameterTemplate).filter(
        ParameterTemplate.level == "system",
        ParameterTemplate.is_active == True
    ).all()
    
    system_defaults = {}
    for template in templates:
        try:
            value = template.get_value()
            validated_value = validate_parameter(template.name, value)
            system_defaults[template.name] = validated_value
        except ParameterValidationError:
            # 忽略无效的系统参数
            continue
    
    # 如果数据库中没有配置，使用硬编码兜底
    if not system_defaults:
        system_defaults = {
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 1000,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "response_mime_type": "text",
        }
    
    return system_defaults


def _get_agent_model_name(db: Session, agent_id: int) -> Optional[str]:
    """
    从Agent参数中获取model_name
    """
    model_param = db.query(AgentParameter).filter(
        AgentParameter.agent_id == agent_id,
        AgentParameter.parameter_name == "model_name"
    ).first()
    
    return model_param.parameter_value if model_param else None
```

---

## 三、数据库迁移方案

### 3.1 迁移概述

由于应用尚未发布，无需考虑现有用户数据的迁移问题，采用全新部署策略。

**迁移策略**：全新创建，不涉及历史数据迁移

### 3.2 迁移脚本

```python
# migration_001_create_agent_parameters.py
"""创建智能体参数表"""

def upgrade(db_session):
    db_session.execute("""
        CREATE TABLE IF NOT EXISTS agent_parameters (
            id SERIAL PRIMARY KEY,
            agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            parameter_name VARCHAR(100) NOT NULL,
            parameter_value TEXT NOT NULL,
            parameter_type VARCHAR(50) NOT NULL,
            description TEXT,
            parameter_group VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_agent_parameter_name UNIQUE (agent_id, parameter_name)
        )
    """)
    db_session.execute("CREATE INDEX IF NOT EXISTS idx_agent_parameters_agent_id ON agent_parameters(agent_id)")
    db_session.commit()


def downgrade(db_session):
    db_session.execute("DROP TABLE IF EXISTS agent_parameters")
    db_session.commit()
```

### 3.3 迁移执行顺序

| 顺序 | 操作 | 说明 |
|------|------|------|
| 1 | 创建 agent_parameters 表 | 新增表，无依赖 |
| 2 | 添加 Agent.parameters 关系 | ORM 关系字段，无数据变更 |
| 3 | 初始化系统默认参数 | 可选，可通过管理界面配置 |
| 4 | 验证表结构 | 确保所有约束生效 |

---

## 四、API 兼容性声明

### 4.1 兼容性策略

**允许破坏性变更**：本次优化允许 API 端点进行破坏性变更，理由如下：
- 应用尚未正式发布，无外部集成方依赖
- 可借此机会清理不合理的 API 设计
- 统一参数获取逻辑，简化客户端使用

### 4.2 变更的 API 端点

| 端点 | 变更类型 | 说明 |
|------|----------|------|
| 新增 | GET /api/v1/agents/{id}/parameters | 获取智能体参数列表 |
| 新增 | GET /api/v1/agents/{id}/parameters/effective | 获取合并后的有效参数 |
| 新增 | POST /api/v1/agents/{id}/parameters | 设置智能体参数 |
| 新增 | DELETE /api/v1/agents/{id}/parameters/{name} | 删除智能体参数 |
| 变更 | GET /api/v1/models/{id}/parameters | 返回格式调整为统一结构 |

### 4.3 响应格式统一

```json
{
  "status": "success",
  "data": { ... },
  "message": null
}

{
  "status": "error",
  "data": null,
  "message": "错误描述",
  "errors": [ ... ]
}
```

---

## 五、测试计划

### 5.1 测试范围

| 测试类型 | 覆盖范围 | 优先级 |
|----------|----------|--------|
| 单元测试 | 参数校验、参数合并、类型转换 | P0 |
| 集成测试 | API 端点、数据库操作 | P0 |
| 功能测试 | 完整参数传递链路 | P1 |
| 异常测试 | 边界条件、错误处理 | P1 |

### 5.2 单元测试用例

```python
# tests/unit/test_parameter_validation.py

import pytest
from backend.app.services.parameter_management.validator import (
    validate_parameter,
    PARAMETER_VALIDATION_RULES,
    ParameterValidationError
)


class TestValidateParameter:
    """参数校验单元测试"""

    def test_temperature_valid_values(self):
        assert validate_parameter("temperature", 0.0) == 0.0
        assert validate_parameter("temperature", 0.7) == 0.7
        assert validate_parameter("temperature", 2.0) == 2.0

    def test_temperature_invalid_max(self):
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_parameter("temperature", 2.5)
        assert "最大值为 2.0" in str(exc_info.value)

    def test_temperature_string_conversion(self):
        assert validate_parameter("temperature", "0.8") == 0.8

    def test_max_tokens_valid_values(self):
        assert validate_parameter("max_tokens", 1) == 1
        assert validate_parameter("max_tokens", 4096) == 4096

    def test_response_mime_type_enum(self):
        assert validate_parameter("response_mime_type", "text") == "text"
        assert validate_parameter("response_mime_type", "json_object") == "json_object"

    def test_response_mime_type_invalid(self):
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_parameter("response_mime_type", "xml")
        assert "有效值" in str(exc_info.value)


class TestParameterMerge:
    """参数合并单元测试"""

    def test_agent_overrides_model(self):
        pass

    def test_model_overrides_type(self):
        pass

    def test_type_overrides_system(self):
        pass

    def test_missing_agent_returns_defaults(self):
        pass
```

### 5.3 集成测试用例

```python
# tests/integration/test_agent_parameters.py

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import get_db, TestingSessionLocal


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


class TestAgentParametersAPI:
    """智能体参数 API 集成测试"""

    def test_set_agent_parameter(self, client):
        response = client.post(
            "/api/v1/agents/1/parameters/temperature",
            json={
                "value": 0.8,
                "type": "float",
                "description": "控制随机性"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_agent_parameters(self, client):
        response = client.get("/api/v1/agents/1/parameters")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_get_effective_parameters(self, client):
        response = client.get("/api/v1/agents/1/parameters/effective")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["temperature"] == 0.8

    def test_delete_agent_parameter(self, client):
        response = client.delete("/api/v1/agents/1/parameters/temperature")
        assert response.status_code == 200

    def test_invalid_parameter_value(self, client):
        response = client.post(
            "/api/v1/agents/1/parameters/temperature",
            json={"value": 5.0, "type": "float"}
        )
        assert response.status_code == 400
```

### 5.4 测试执行

```bash
pytest tests/ -v
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest --cov=backend.app.services.parameter_management --cov-report=html
```

---

## 六、系统初始化数据

### 6.1 系统级默认参数

首次部署时，系统默认参数从硬编码值初始化：

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| temperature | 0.7 | 默认随机性 |
| top_p | 1.0 | 默认核采样 |
| max_tokens | 1000 | 默认最大 token 数 |
| presence_penalty | 0.0 | 默认存在惩罚 |
| frequency_penalty | 0.0 | 默认频率惩罚 |
| response_mime_type | "text" | 默认响应格式 |

### 6.2 初始化脚本

```python
# scripts/init_system_parameters.py

from sqlalchemy.orm import Session
from backend.app.models.parameter_template import ParameterTemplate


def init_system_parameters(db: Session):
    system_params = [
        {"name": "temperature", "value": "0.7", "type": "float"},
        {"name": "top_p", "value": "1.0", "type": "float"},
        {"name": "max_tokens", "value": "1000", "type": "int"},
        {"name": "presence_penalty", "value": "0.0", "type": "float"},
        {"name": "frequency_penalty", "value": "0.0", "type": "float"},
        {"name": "response_mime_type", "value": "text", "type": "string"},
    ]

    for param in system_params:
        existing = db.query(ParameterTemplate).filter(
            ParameterTemplate.name == param["name"],
            ParameterTemplate.level == "system"
        ).first()
        if not existing:
            template = ParameterTemplate(
                name=param["name"],
                value=param["value"],
                type=param["type"],
                level="system",
                is_active=True,
                description=f"系统默认{param['name']}"
            )
            db.add(template)

    db.commit()
    print(f"已初始化 {len(system_params)} 个系统默认参数")


if __name__ == "__main__":
    from backend.app.core.database import SessionLocal
    db = SessionLocal()
    try:
        init_system_parameters(db)
    finally:
        db.close()
```

### 6.3 初始化执行

```bash
python -m scripts.init_system_parameters
```

---

## 七、优化实施建议

### 4.1 方案一：快速修复方案（低风险）

**目标**：在最小改动范围内实现参数传递

**核心改动**：
1. 更新 `llm_service.py`，支持从数据库动态读取参数
2. 确保 AgentScheduler 在调用LLM时传递参数
3. 添加 Agent → Model → Parameter 的映射查询逻辑

**具体实现**：

```python
# 在 agent_model_scheduler.py 或新的参数传递服务中
class ParameterPassingService:
    @staticmethod
    def get_agent_model_parameters(db: Session, agent_id: int) -> Dict[str, Any]:
        """
        获取智能体的完整参数配置
        
        优先级：
        1. Agent直接配置的参数（最高优先级）
        2. Agent关联模型的参数
        3. 模型继承的类型默认参数
        4. 系统默认参数（兜底）
        
        Returns:
            包含temperature、max_tokens等的字典
        """
        return get_final_parameters(db, agent_id=agent_id)
    
    @staticmethod
    def get_model_id_for_agent(db: Session, agent_id: int) -> Optional[int]:
        """
        根据Agent配置的model_name获取对应的model_id
        """
        agent_model_name = _get_agent_model_name(db, agent_id)
        if not agent_model_name:
            return None
        
        model = db.query(ModelDB).filter(
            ModelDB.name == agent_model_name
        ).first()
        
        return model.id if model else None
```

**优点**：
- 改动最小，风险低
- 立即解决参数无法传递的问题

**缺点**：
- Agent仍无法独立配置全部参数
- 需要通过参数方式建立Agent与Model的关联

---

### 4.2 方案二：完整实现方案（推荐）

**目标**：建立完整的四层参数体系，实现参数的可追溯和可管理

#### 4.2.1 Phase 1：数据库层

```python
# 新增文件: backend/app/models/agent_parameter.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class AgentParameter(Base):
    """智能体参数表"""
    __tablename__ = "agent_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    parameter_value = Column(Text, nullable=False)
    parameter_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    parameter_group = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    agent = relationship("Agent", back_populates="parameters")
    
    __table_args__ = (
        UniqueConstraint('agent_id', 'parameter_name', name='uq_agent_parameter_name'),
    )
```

**数据库迁移脚本：**

```sql
-- 创建 agent_parameters 表
CREATE TABLE IF NOT EXISTS agent_parameters (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    parameter_name VARCHAR(100) NOT NULL,
    parameter_value TEXT NOT NULL,
    parameter_type VARCHAR(50) NOT NULL,
    description TEXT,
    parameter_group VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_agent_parameter_name UNIQUE (agent_id, parameter_name)
);

CREATE INDEX IF NOT EXISTS idx_agent_parameters_agent_id ON agent_parameters(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_parameters_name ON agent_parameters(parameter_name);

-- 添加 model_id 外键到 agents 表（可选，用于缓存加速查询）
ALTER TABLE agents ADD COLUMN IF NOT EXISTS model_id INTEGER REFERENCES model_dbs(id);
CREATE INDEX IF NOT EXISTS idx_agents_model_id ON agents(model_id);
```

#### 4.2.2 Phase 2：服务层

```python
# 新增文件: backend/app/services/parameter_management/agent_parameter_manager.py
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.agent import Agent
from backend.app.models.agent_parameter import AgentParameter
from backend.app.models.model_db import ModelDB
from backend.app.models.model_category import ModelCategory
from backend.app.models.model_parameter import ModelParameter
from backend.app.models.parameter_template import ParameterTemplate
from backend.app.services.parameter_management.parameter_validator import (
    validate_parameter,
    ParameterValidationError
)

class AgentParameterManager:
    
    @staticmethod
    def get_agent_effective_parameters(db: Session, agent_id: int) -> Dict[str, Any]:
        """
        获取智能体的有效参数配置（包含继承链）
        优先级：Agent参数 > Model参数 > ModelType参数 > System参数
        
        Returns:
            完整参数配置字典
            
        Raises:
            ParameterValidationError: 参数值无效时抛出
        """
        return get_final_parameters(db, agent_id=agent_id)
    
    @staticmethod
    def set_agent_parameter(
        db: Session,
        agent_id: int,
        parameter_name: str,
        parameter_value: Any,
        parameter_type: str = None,
        description: str = None,
        parameter_group: str = None
    ) -> AgentParameter:
        """
        设置智能体的单个参数
        
        Args:
            agent_id: 智能体ID
            parameter_name: 参数名
            parameter_value: 参数值
            parameter_type: 参数类型（可选，自动推断）
            description: 参数描述（可选）
            parameter_group: 参数分组（可选）
            
        Returns:
            创建或更新的AgentParameter对象
            
        Raises:
            ParameterValidationError: 参数值校验失败
        """
        # 自动推断参数类型
        if parameter_type is None:
            parameter_type = _infer_parameter_type(parameter_value)
        
        # 校验参数值
        validated_value = validate_parameter(parameter_name, parameter_value)
        
        # 转换为字符串存储
        value_str = str(validated_value)
        
        # 查找现有参数
        existing = db.query(AgentParameter).filter(
            AgentParameter.agent_id == agent_id,
            AgentParameter.parameter_name == parameter_name
        ).first()
        
        if existing:
            # 更新现有参数
            existing.parameter_value = value_str
            existing.parameter_type = parameter_type
            if description:
                existing.description = description
            if parameter_group:
                existing.parameter_group = parameter_group
            param = existing
        else:
            # 创建新参数
            param = AgentParameter(
                agent_id=agent_id,
                parameter_name=parameter_name,
                parameter_value=value_str,
                parameter_type=parameter_type,
                description=description,
                parameter_group=parameter_group
            )
            db.add(param)
        
        db.commit()
        db.refresh(param)
        
        return param
    
    @staticmethod
    def delete_agent_parameter(db: Session, agent_id: int, parameter_name: str) -> bool:
        """
        删除智能体的单个参数
        
        Returns:
            是否删除成功
        """
        result = db.query(AgentParameter).filter(
            AgentParameter.agent_id == agent_id,
            AgentParameter.parameter_name == parameter_name
        ).delete()
        
        db.commit()
        return result > 0
    
    @staticmethod
    def get_agent_parameters_by_group(db: Session, agent_id: int) -> Dict[str, list]:
        """
        按分组获取智能体的所有参数
        
        Returns:
            按分组组织的参数字典
        """
        params = db.query(AgentParameter).filter(
            AgentParameter.agent_id == agent_id
        ).all()
        
        grouped = {}
        for param in params:
            group = param.parameter_group or "default"
            if group not in grouped:
                grouped[group] = []
            grouped[group].append({
                "id": param.id,
                "parameter_name": param.parameter_name,
                "parameter_value": param.parameter_value,
                "parameter_type": param.parameter_type,
                "description": param.description
            })
        
        return grouped
    
    @staticmethod
    def get_agent_model_name(db: Session, agent_id: int) -> Optional[str]:
        """
        获取智能体配置的模型名称
        """
        return _get_agent_model_name(db, agent_id)


def _infer_parameter_type(value: Any) -> str:
    """
    自动推断参数类型
    """
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        # 尝试解析为JSON数组或对象
        if value.startswith("[") or value.startswith("{"):
            return "json"
        return "string"
    return "string"
```

#### 4.2.3 Phase 3：LLM服务集成

```python
# 更新 llm_service.py
from backend.app.services.parameter_management.agent_parameter_manager import AgentParameterManager

class LLMService:
    def generate_text_for_agent(self, agent_id: int, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        为智能体生成文本，自动使用智能体的参数配置
        所有参数从数据库动态读取
        """
        from backend.app.core.database import SessionLocal
        db = SessionLocal()
        try:
            # 获取智能体的完整参数配置
            agent_params = AgentParameterManager.get_agent_effective_parameters(db, agent_id)
            
            # 构建最终参数
            final_params = {
                'temperature': agent_params.get('temperature', 0.7),
                'max_tokens': agent_params.get('max_tokens', 1000),
                'top_p': agent_params.get('top_p', 1.0),
                'presence_penalty': agent_params.get('presence_penalty', 0.0),
                'frequency_penalty': agent_params.get('frequency_penalty', 0.0),
            }
            
            # 从agent参数中获取model_name
            model_name = agent_params.get('model_name')
            if model_name:
                final_params['model_name'] = model_name
            
            # 允许kwargs覆盖
            final_params.update(kwargs)
            
            return self.text_completion(prompt=prompt, **final_params)
        finally:
            db.close()
    
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        生成文本响应 - 保留原有接口用于直接调用
        """
        try:
            return self.text_completion(
                prompt=prompt,
                model_name=kwargs.get("model_name"),
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                top_p=kwargs.get("top_p", 1.0),
                presence_penalty=kwargs.get("presence_penalty", 0.0),
                frequency_penalty=kwargs.get("frequency_penalty", 0.0),
            )
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return {
                "error": str(e),
                "model": kwargs.get("model_name", "default"),
                "success": False
            }
```

#### 4.2.4 Phase 4：API层

```python
# 新增路由: backend/app/api/v1/agent_parameter.py
from pydantic import BaseModel, Field
from typing import Optional, Any

class ParameterSetRequest(BaseModel):
    """参数设置请求"""
    value: Any = Field(..., description="参数值")
    type: Optional[str] = Field(None, description="参数类型")
    description: Optional[str] = Field(None, description="参数说明")
    group: Optional[str] = Field(None, description="参数分组")

class ParameterDeleteRequest(BaseModel):
    """参数删除请求"""
    parameter_name: str = Field(..., description="要删除的参数名")

router = APIRouter(prefix="/agents/{agent_id}/parameters", tags=["智能体参数管理"])

@router.get("/")
def get_agent_parameters(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """
    获取智能体的所有参数（按分组展示）
    """
    grouped_params = AgentParameterManager.get_agent_parameters_by_group(db, agent_id)
    return {
        "agent_id": agent_id,
        "parameters": grouped_params
    }

@router.get("/effective")
def get_effective_parameters(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """
    获取智能体的有效参数配置（合并继承链后）
    """
    params = AgentParameterManager.get_agent_effective_parameters(db, agent_id)
    return {
        "agent_id": agent_id,
        "parameters": params
    }

@router.post("/{parameter_name}")
def set_agent_parameter(
    agent_id: int,
    parameter_name: str,
    request: ParameterSetRequest,
    db: Session = Depends(get_db)
):
    """
    设置智能体的单个参数
    
    行为：
    - 如果参数已存在，则更新
    - 如果参数不存在，则创建
    - 参数值会被校验，无效值会报错
    """
    try:
        param = AgentParameterManager.set_agent_parameter(
            db=db,
            agent_id=agent_id,
            parameter_name=parameter_name,
            parameter_value=request.value,
            parameter_type=request.type,
            description=request.description,
            parameter_group=request.group
        )
        return {
            "status": "success",
            "message": f"参数 {parameter_name} 设置成功",
            "data": {
                "parameter_name": parameter_name,
                "parameter_value": param.parameter_value,
                "parameter_type": param.parameter_type
            }
        }
    except ParameterValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"参数校验失败: {e.message}",
                "parameter": e.parameter_name,
                "invalid_value": e.value
            }
        )

@router.delete("/{parameter_name}")
def delete_agent_parameter(
    agent_id: int,
    parameter_name: str,
    db: Session = Depends(get_db)
):
    """
    删除智能体的单个参数
    """
    success = AgentParameterManager.delete_agent_parameter(db, agent_id, parameter_name)
    if success:
        return {
            "status": "success",
            "message": f"参数 {parameter_name} 已删除"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": f"参数 {parameter_name} 不存在"
            }
        )
```

#### 4.2.5 Phase 5：前端集成规范

```javascript
// 前端参数分组配置
const PARAMETER_GROUPS = {
  model_selection: {
    title: '模型选择',
    description: '选择智能体使用的底层模型',
    icon: '🤖',
    order: 1
  },
  generation: {
    title: '生成参数',
    description: '控制文本生成的质量和风格',
    icon: '✍️',
    order: 2
  },
  safety: {
    title: '安全参数',
    description: '控制内容过滤和安全级别',
    icon: '🛡️',
    order: 3
  },
  advanced: {
    title: '高级参数',
    description: '专家级参数调整，请谨慎修改',
    icon: '⚙️',
    order: 4
  }
};

// 前端参数配置
const PARAMETER_CONFIG = {
  temperature: {
    group: 'generation',
    label: 'Temperature',
    type: 'slider',
    min: 0,
    max: 2,
    step: 0.1,
    default: 0.7,
    help: '控制输出的随机性。较高的值会使输出更随机和创意，较低的值使输出更集中和确定性。',
    helpLink: 'https://platform.openai.com/docs/api-reference/chat/create#chat-create-temperature'
  },
  top_p: {
    group: 'generation',
    label: 'Top P',
    type: 'slider',
    min: 0,
    max: 1,
    step: 0.01,
    default: 1,
    help: '核采样概率阈值。模型只考虑概率质量最高的部分 token。较低的值会使输出更保守。',
    helpLink: 'https://platform.openai.com/docs/api-reference/chat/create#chat-create-top_p'
  },
  max_tokens: {
    group: 'generation',
    label: '最大 Token 数',
    type: 'number',
    min: 1,
    max: 4096,
    step: 1,
    default: 1000,
    help: '生成文本的最大 token 数量。较高的值允许生成更长的回复，但也会消耗更多配额。',
    helpLink: 'https://platform.openai.com/docs/api-reference/chat/create#chat-create-max_tokens'
  },
  presence_penalty: {
    group: 'generation',
    label: 'Presence Penalty',
    type: 'slider',
    min: -2,
    max: 2,
    step: 0.1,
    default: 0,
    help: '对已出现在生成文本中的 token 进行惩罚。正值会鼓励模型生成新内容。',
    helpLink: 'https://platform.openai.com/docs/api-reference/chat/create#chat-create-presence_penalty'
  },
  frequency_penalty: {
    group: 'generation',
    label: 'Frequency Penalty',
    type: 'slider',
    min: -2,
    max: 2,
    step: 0.1,
    default: 0,
    help: '根据 token 在生成文本中的频率进行惩罚。正值会降低重复 token 的概率。',
    helpLink: 'https://platform.openai.com/docs/api-reference/chat/create#chat-create-frequency_penalty'
  },
  model_name: {
    group: 'model_selection',
    label: '选择模型',
    type: 'select',
    options: [
      { value: 'gpt-4', label: 'GPT-4' },
      { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
    ],
    default: 'gpt-3.5-turbo',
    help: '选择要使用的 AI 模型。不同模型有不同的能力和定价。'
  }
};
```

---

### 4.3 迁移方案（完整版）

#### 4.3.1 阶段一：修复参数传递（1天）

1. **创建 ParameterPassingService**
   - 实现 Agent → Model → Parameter 的查询逻辑
   - 在 AgentScheduler 中集成参数传递

2. **更新 LLM 服务**
   - 确保参数能够从调用方传递到实际 LLM 调用
   - 移除硬编码参数，使用传递的参数

#### 4.3.2 阶段二：添加智能体参数（2天）

1. **创建 agent_parameters 表**
   - 执行数据库迁移脚本
   - 更新 Agent 模型关系

2. **创建 AgentParameterManager**
   - 实现参数CRUD操作
   - 实现参数校验逻辑
   - 实现参数获取和继承逻辑

3. **更新 API 接口**
   - 实现完整的RESTful API
   - 添加参数校验错误处理

4. **更新前端界面**
   - 实现参数分组展示
   - 添加参数帮助信息
   - 实现参数编辑功能

#### 4.3.3 阶段三：清理和简化（0.5天）

1. **移除 ParameterTemplate 的多级支持**
   - 只保留系统级参数
   - 迁移现有数据到新结构

2. **清理 ModelParameter 字段**
   - 移除未使用的字段

#### 4.3.4 阶段四：分离能力展示（0.5天）

1. **从参数管理中移除能力相关内容**
2. **在模型详情页独立展示能力**

---

## 五、实施优先级建议

### 5.1 优先级排序

| 优先级 | 任务 | 原因 |
|--------|------|------|
| **P0** | 修复参数传递链路 | 当前配置完全不生效，用户体验极差 |
| **P1** | 新增智能体参数管理 | 用户刚需，Agent 级别参数完全缺失 |
| **P1** | 实现参数校验机制 | 保证数据有效性，防止非法值导致错误 |
| **P1** | 简化 ParameterTemplate | 功能重复，需要清理 |
| **P2** | 分离能力展示 | 减少混淆，但不是阻塞问题 |
| **P3** | 清理旧代码 | 保持兼容，低优先级 |

### 5.2 风险评估

| 改动 | 风险 | 缓解措施 |
|------|------|----------|
| 添加AgentParameter表 | 低 | 新增表，不影响现有功能 |
| 修改Agent模型添加model_id | 低 | 字段可选，不强制迁移 |
| 修改LLM服务集成参数 | 中 | 需要测试确保兼容 |
| 实现参数校验 | 低 | 非法值会报错，不影响现有功能 |
| 移除硬编码参数 | 低 | 通过默认值保证兼容 |

---

## 六、实施效果评估

### 6.1 预期改进指标

| 指标 | 优化前 | 优化后 | 提升幅度 |
|------|--------|--------|----------|
| 参数配置生效率 | 0% | 100% | +100% |
| 智能体参数配置能力 | 无 | 完整 | 新增 |
| 配置入口统一性 | 分散 | 统一 | 显著提升 |
| 职责清晰度 | 模糊 | 明确 | 大幅改善 |
| 参数值合法性校验 | 无 | 有 | 新增 |

### 6.2 用户体验改善

1. **参数配置立即生效**
   - 用户配置的 temperature、max_tokens 等参数能够真正影响模型行为
   - 不再出现"配置了但没效果"的问题

2. **智能体参数完整支持**
   - 可以为不同智能体设置不同的参数
   - 支持参数继承，减少重复配置
   - 参数通过数据库动态读取，无需重启服务

3. **配置界面更清晰**
   - 能力展示与参数管理分离
   - 参数分组展示，层次分明
   - 每个参数都有详细的帮助信息

4. **参数值安全可控**
   - 严格的参数校验，无效值会被拒绝
   - 清晰的错误提示，帮助用户修正

### 6.3 技术债务清理

1. **移除冗余代码**
   - 简化 ParameterTemplate 多级模板
   - 清理重复的参数管理逻辑

2. **架构更清晰**
   - 四层参数体系职责明确
   - 参数传递链路完整可追溯
   - 参数关联方式灵活（通过参数名关联）

### 6.4 风险与缓解

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 迁移过程中服务中断 | 低 | 采用平滑迁移方案，新旧系统并行 |
| 历史参数数据丢失 | 低 | 迁移前完整备份，提供回滚脚本 |
| 现有集成失效 | 中 | 保持 API 兼容，提供迁移脚本 |
| 参数校验过于严格影响用户 | 低 | 提供清晰的错误提示和默认值 |

---

## 七、参数校验规则汇总

### 7.1 参数定义表

| 参数名 | 分组 | 类型 | 默认值 | 最小值 | 最大值 | 帮助信息 |
|--------|------|------|--------|--------|--------|----------|
| model_name | 模型选择 | string | - | - | - | 选择要使用的AI模型 |
| temperature | 生成参数 | float | 0.7 | 0.0 | 2.0 | 控制输出的随机性，值越高越有创意 |
| top_p | 生成参数 | float | 1.0 | 0.0 | 1.0 | 核采样概率阈值，越低越保守 |
| max_tokens | 生成参数 | int | 1000 | 1 | 4096 | 单次生成的最大token数量 |
| presence_penalty | 生成参数 | float | 0.0 | -2.0 | 2.0 | 惩罚重复词汇，正值鼓励新词汇 |
| frequency_penalty | 生成参数 | float | 0.0 | -2.0 | 2.0 | 惩罚频繁词汇，正值降低重复率 |
| response_mime_type | 安全参数 | enum | text | - | - | 响应格式，json_object强制输出JSON |
| logprobs | 高级参数 | bool | false | - | - | 是否返回对数概率信息 |
| top_logprobs | 高级参数 | int | 0 | 0 | 20 | 每个位置返回的最可能token数量 |

### 7.2 错误处理

```python
# 错误响应示例
{
  "status": "error",
  "message": "参数校验失败",
  "errors": [
    {
      "parameter": "temperature",
      "message": "最大值为 2.0，实际收到: 2.5",
      "invalid_value": 2.5
    }
  ]
}
```

---

## 八、API 接口规格

### 8.1 接口列表

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | /agents/{id}/parameters | 获取所有参数（分组） | - | 分组参数列表 |
| GET | /agents/{id}/parameters/effective | 获取有效参数（合并后） | - | 完整参数字典 |
| POST | /agents/{id}/parameters/{name} | 设置参数 | ParameterSetRequest | 参数信息 |
| DELETE | /agents/{id}/parameters/{name} | 删除参数 | - | 操作结果 |

### 8.2 完整请求示例

```json
// POST /agents/1/parameters/temperature
{
  "value": 0.8,
  "type": "float",
  "description": "控制输出的随机性",
  "group": "generation"
}
```

### 8.3 完整响应示例

```json
// GET /agents/1/parameters
{
  "status": "success",
  "data": {
    "agent_id": 1,
    "parameters": {
      "model_selection": [
        {
          "id": 1,
          "parameter_name": "model_name",
          "parameter_value": "gpt-4",
          "parameter_type": "string",
          "description": "选择要使用的模型"
        }
      ],
      "generation": [
        {
          "id": 2,
          "parameter_name": "temperature",
          "parameter_value": "0.8",
          "parameter_type": "float",
          "description": "控制输出的随机性"
        },
        {
          "id": 3,
          "parameter_name": "max_tokens",
          "parameter_value": "2000",
          "parameter_type": "int",
          "description": "最大Token数"
        }
      ]
    }
  }
}
```

---

## 九、实施进度跟踪

### 9.1 进度总览

| 任务 | 状态 | 完成日期 | 备注 |
|------|------|----------|------|
| 创建 AgentParameter 数据库模型 | ✅ 已完成 | 2024-12-25 | 已创建 agent_parameter.py |
| 更新 Agent 模型关联关系 | ✅ 已完成 | 2024-12-25 | 已添加 parameters 关系 |
| 更新模型初始化文件导出 | ✅ 已完成 | 2024-12-25 | 已添加 AgentParameter 导出 |
| 创建 AgentParameterManager 服务类 | ✅ 已完成 | 2024-12-25 | 已创建 agent_parameter_manager.py |
| 实现参数校验逻辑 | ✅ 已完成 | 2024-12-25 | 已集成到 AgentParameterManager |
| 实现参数获取和继承逻辑 | ✅ 已完成 | 2024-12-25 | 已集成到 AgentParameterManager |
| 集成参数传递到 LLM 服务 | ⏳ 进行中 | - | 待实现 |
| 创建智能体参数 API 端点 | ⏳ 待执行 | - | 待实现 |
| 创建系统参数初始化脚本 | ⏳ 待执行 | - | 待实现 |
| 编写单元测试和集成测试 | ⏳ 待执行 | - | 待实现 |

### 9.2 已完成文件清单

- `backend/app/models/agent_parameter.py` - 智能体参数数据库模型
- `backend/app/models/agent.py` - 更新 Agent 模型添加关联关系
- `backend/app/models/__init__.py` - 更新模型导出
- `backend/app/services/parameter_management/agent_parameter_manager.py` - 智能体参数管理服务
