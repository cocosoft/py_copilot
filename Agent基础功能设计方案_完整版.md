# Agent基础功能设计方案（完整版）

结合能力中心（工具/技能/MCP）的深度优化方案

---

## 一、现有能力中心架构分析

### 1.1 三层能力体系

```
┌─────────────────────────────────────────────────────────────────┐
│                     现有能力中心架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    第一层：技能层 (Skill)                 │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  特点：                                          │   │   │
│  │  │  • 高阶业务能力封装                               │   │   │
│  │  │  • 包含完整业务逻辑和流程                         │   │   │
│  │  │  • 支持版本管理和依赖关系                         │   │   │
│  │  │  • 可生成Artifacts（文档/代码/图表等）             │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │  示例：PPT生成技能、数据分析技能、文档翻译技能          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    第二层：工具层 (Tool)                  │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  特点：                                          │   │   │
│  │  │  • 原子化功能封装                                 │   │   │
│  │  │  • 单一职责，可复用                               │   │   │
│  │  │  • 支持本地/MCP/官方三种类型                      │   │   │
│  │  │  • 参数化配置                                     │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │  示例：Web搜索工具、文件读取工具、邮件发送工具          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    第三层：MCP层                          │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  特点：                                          │   │   │
│  │  │  • 外部服务连接器                                 │   │   │
│  │  │  • 标准化协议（Model Context Protocol）           │   │   │
│  │  │  • 支持SSE/stdio传输                              │   │   │
│  │  │  • 动态工具发现                                   │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │  示例：GitHub MCP、Slack MCP、数据库 MCP               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 数据模型关系

```
┌─────────────────────────────────────────────────────────────────┐
│                     能力中心数据模型                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐   │
│  │    Skill    │◄─────►│    Agent    │◄─────►│    Tool     │   │
│  │   (技能)    │       │   (智能体)   │       │   (工具)    │   │
│  └──────┬──────┘       └──────┬──────┘       └──────┬──────┘   │
│         │                     │                     │          │
│         │              ┌──────┴──────┐              │          │
│         │              │             │              │          │
│         ▼              ▼             ▼              ▼          │
│  ┌─────────────┐  ┌──────────┐ ┌──────────┐  ┌─────────────┐  │
│  │SkillExecution│  │AgentSkill│ │AgentTool │  │ToolExecution│  │
│  │Log(执行日志) │  │Association│ │Association│ │Log(执行日志) │  │
│  └─────────────┘  └──────────┘ └──────────┘  └─────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                          MCP层                          │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │  │
│  │  │MCPClientConfig│   │MCPServerConfig│   │MCPToolMapping│ │  │
│  │  │ (客户端配置) │    │ (服务端配置) │    │ (工具映射)  │ │  │
│  │  └─────────────┘    └─────────────┘    └─────────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 现有执行流程

```python
# 现有执行流程（agent_execution_engine.py）

用户输入
    │
    ▼
┌─────────────────┐
│  加载Agent配置   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  调用LLM模型    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 分析模型响应     │
│ (识别技能/工具调用)│
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│执行技能 │ │执行工具 │
└────────┘ └────────┘
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│ 生成最终响应     │
└─────────────────┘
```

---

## 二、核心问题分析

### 2.1 现有架构的不足

```
┌─────────────────────────────────────────────────────────────────┐
│                    现有架构问题分析                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ 问题1：能力调用不够智能                                      │
│     - LLM决定调用哪些技能/工具，但缺乏智能编排                    │
│     - 多个技能/工具之间无法自动协调                               │
│     - 缺乏基于上下文的动态能力选择                                │
│                                                                 │
│  ❌ 问题2：三层能力割裂                                          │
│     - Skill、Tool、MCP各自独立管理                                │
│     - 缺乏统一的能力发现和调度层                                  │
│     - 能力之间的依赖关系难以表达                                  │
│                                                                 │
│  ❌ 问题3：11个官方智能体与能力中心脱节                          │
│     - 官方智能体是独立的Agent实例                                │
│     - 没有充分利用能力中心的Skill/Tool/MCP                       │
│     - 能力无法跨智能体复用                                        │
│                                                                 │
│  ❌ 问题4：缺乏能力编排层                                        │
│     - 复杂任务需要手动编排多个能力                                │
│     - 没有自动化的任务分解和能力组合                              │
│     - 缺乏能力执行的计划和优化                                    │
│                                                                 │
│  ❌ 问题5：记忆与能力执行分离                                     │
│     - 能力执行过程中无法有效利用记忆                              │
│     - 能力执行结果没有有效沉淀到记忆                              │
│     - 缺乏基于记忆的能力推荐                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、优化设计方案

### 3.1 整体架构优化

```
┌─────────────────────────────────────────────────────────────────┐
│                 优化后的统一Agent架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    用户交互层                              │   │
│  │         (Web / 移动端 / API / 语音)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              统一智能体入口 (UnifiedAgent)                 │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  • 统一对话接口                                  │   │   │
│  │  │  • 上下文管理                                    │   │   │
│  │  │  • 用户画像管理                                  │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              智能编排引擎 (OrchestrationEngine)            │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  意图理解层                                       │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 意图分类器  │ │ 实体提取器  │ │ 场景识别器  │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  ├─────────────────────────────────────────────────┤   │   │
│  │  │  任务规划层                                       │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 任务分解器  │ │ 依赖分析器  │ │ 执行优化器  │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  ├─────────────────────────────────────────────────┤   │   │
│  │  │  能力调度层                                       │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │ 能力发现器  │ │ 能力匹配器  │ │ 能力编排器  │ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              统一能力中心 (UnifiedCapabilityCenter)        │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │                                                   │   │   │
│  │  │   ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │   │   │
│  │  │   │   Skill     │  │    Tool     │  │   MCP   │ │   │   │
│  │  │   │   (技能)    │  │   (工具)    │  │ (连接器)│ │   │   │
│  │  │   │             │  │             │  │         │ │   │   │
│  │  │   │ • PPT生成   │  │ • Web搜索   │  │ • GitHub│ │   │   │
│  │  │   │ • 数据分析  │  │ • 文件读取  │  │ • Slack │ │   │   │
│  │  │   │ • 代码生成  │  │ • 邮件发送  │  │ • DB    │ │   │   │
│  │  │   │ • 文档翻译  │  │ • API调用   │  │ • ...   │ │   │   │
│  │  │   └─────────────┘  └─────────────┘  └─────────┘ │   │   │
│  │  │                                                   │   │   │
│  │  │   统一抽象：Capability (能力单元)                  │   │   │
│  │  │   • 统一接口封装                                  │   │   │
│  │  │   • 统一参数模式                                  │   │   │
│  │  │   • 统一执行流程                                  │   │   │
│  │  │   • 统一监控日志                                  │   │   │
│  │  │                                                   │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              基础设施层                                    │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │   │
│  │  │ 记忆系统    │ │ 学习引擎    │ │ 监控分析    │       │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心创新点：能力统一抽象

```python
# app/capabilities/base_capability.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

class CapabilityType(Enum):
    """能力类型枚举"""
    SKILL = "skill"      # 高阶技能
    TOOL = "tool"        # 原子工具
    MCP = "mcp"          # MCP连接器
    AGENT = "agent"      # 子智能体

class CapabilityLevel(Enum):
    """能力级别枚举"""
    ATOMIC = "atomic"           # 原子能力，不可再分
    COMPOSITE = "composite"     # 复合能力，由多个原子能力组成
    WORKFLOW = "workflow"       # 工作流能力，包含完整流程

class CapabilityMetadata:
    """能力元数据"""
    def __init__(self,
                 name: str,
                 display_name: str,
                 description: str,
                 capability_type: CapabilityType,
                 level: CapabilityLevel,
                 category: str,
                 tags: List[str] = None,
                 input_schema: Dict = None,
                 output_schema: Dict = None,
                 dependencies: List[str] = None,
                 required_resources: List[str] = None):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.capability_type = capability_type
        self.level = level
        self.category = category
        self.tags = tags or []
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}
        self.dependencies = dependencies or []
        self.required_resources = required_resources or []

class BaseCapability(ABC):
    """
    能力统一抽象基类
    
    将Skill、Tool、MCP统一抽象为Capability，提供一致的调用接口
    """
    
    def __init__(self, metadata: CapabilityMetadata):
        self.metadata = metadata
        self.execution_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "average_execution_time": 0.0
        }
    
    @abstractmethod
    async def execute(self, 
                     input_data: Dict[str, Any],
                     context: ExecutionContext) -> CapabilityResult:
        """
        执行能力
        
        Args:
            input_data: 输入数据，必须符合input_schema
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证输入数据"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """获取子能力列表（用于复合能力）"""
        return []
    
    def update_stats(self, execution_time: float, success: bool):
        """更新执行统计"""
        self.execution_stats["total_calls"] += 1
        if success:
            self.execution_stats["successful_calls"] += 1
        else:
            self.execution_stats["failed_calls"] += 1
        
        # 更新平均执行时间
        total = self.execution_stats["total_calls"]
        avg = self.execution_stats["average_execution_time"]
        self.execution_stats["average_execution_time"] = (
            (avg * (total - 1) + execution_time) / total
        )
```

### 3.3 三层能力统一封装

```python
# app/capabilities/skill_capability.py

class SkillCapability(BaseCapability):
    """
    技能能力封装
    
    将现有Skill系统封装为统一Capability接口
    """
    
    def __init__(self, skill: Skill):
        metadata = CapabilityMetadata(
            name=skill.name,
            display_name=skill.display_name or skill.name,
            description=skill.description,
            capability_type=CapabilityType.SKILL,
            level=CapabilityLevel.WORKFLOW,
            category="skill",
            tags=skill.tags,
            input_schema=skill.parameters_schema,
            dependencies=[dep.dependency_skill_id for dep in skill.dependencies]
        )
        super().__init__(metadata)
        self.skill = skill
        self.execution_engine = SkillExecutionEngine()
    
    async def execute(self, 
                     input_data: Dict[str, Any],
                     context: ExecutionContext) -> CapabilityResult:
        """执行技能"""
        try:
            # 调用现有技能执行引擎
            result = await self.execution_engine.execute(
                skill_id=self.skill.id,
                params=input_data,
                context=context
            )
            
            return CapabilityResult(
                success=result["status"] == "success",
                output=result.get("output"),
                artifacts=result.get("artifacts", []),
                execution_time=result.get("execution_time_ms", 0),
                metadata={
                    "skill_id": self.skill.id,
                    "skill_name": self.skill.name
                }
            )
        except Exception as e:
            return CapabilityResult(
                success=False,
                error=str(e),
                metadata={"skill_id": self.skill.id}
            )


# app/capabilities/tool_capability.py

class ToolCapability(BaseCapability):
    """
    工具能力封装
    
    将现有Tool系统封装为统一Capability接口
    """
    
    def __init__(self, tool: Tool):
        metadata = CapabilityMetadata(
            name=tool.name,
            display_name=tool.display_name or tool.name,
            description=tool.description,
            capability_type=CapabilityType.TOOL,
            level=CapabilityLevel.ATOMIC,
            category=tool.category,
            tags=tool.tags,
            input_schema=tool.parameters_schema
        )
        super().__init__(metadata)
        self.tool = tool
    
    async def execute(self,
                     input_data: Dict[str, Any],
                     context: ExecutionContext) -> CapabilityResult:
        """执行工具"""
        try:
            # 根据工具类型选择执行方式
            if self.tool.tool_type == "local":
                result = await self._execute_local(input_data, context)
            elif self.tool.tool_type == "mcp":
                result = await self._execute_mcp(input_data, context)
            else:
                result = await self._execute_official(input_data, context)
            
            return result
        except Exception as e:
            return CapabilityResult(
                success=False,
                error=str(e)
            )
    
    async def _execute_mcp(self, 
                          input_data: Dict[str, Any],
                          context: ExecutionContext) -> CapabilityResult:
        """通过MCP执行工具"""
        # 获取MCP客户端
        mcp_client = await MCPConnectionManager.get_client(
            self.tool.mcp_client_config_id
        )
        
        # 调用MCP工具
        result = await mcp_client.call_tool(
            tool_name=self.tool.mcp_tool_name,
            params=input_data
        )
        
        return CapabilityResult(
            success=True,
            output=result
        )


# app/capabilities/mcp_capability.py

class MCPCapability(BaseCapability):
    """
    MCP能力封装
    
    将MCP服务封装为统一Capability接口
    """
    
    def __init__(self, 
                 client_config: MCPClientConfigModel,
                 tool_mapping: MCPToolMappingModel):
        metadata = CapabilityMetadata(
            name=tool_mapping.local_name,
            display_name=tool_mapping.local_name,
            description=tool_mapping.description,
            capability_type=CapabilityType.MCP,
            level=CapabilityLevel.ATOMIC,
            category="mcp",
            input_schema=tool_mapping.input_schema
        )
        super().__init__(metadata)
        self.client_config = client_config
        self.tool_mapping = tool_mapping
        self._client: Optional[MCPClient] = None
    
    async def execute(self,
                     input_data: Dict[str, Any],
                     context: ExecutionContext) -> CapabilityResult:
        """执行MCP能力"""
        try:
            # 确保客户端连接
            if not self._client or not self._client.is_connected:
                self._client = MCPClient(self.client_config)
                await self._client.connect()
            
            # 调用MCP工具
            result = await self._client.call_tool(
                tool_name=self.tool_mapping.original_name,
                params=input_data
            )
            
            return CapabilityResult(
                success=True,
                output=result
            )
        except Exception as e:
            return CapabilityResult(
                success=False,
                error=str(e)
            )
```

### 3.4 统一能力中心

```python
# app/capabilities/unified_capability_center.py

class UnifiedCapabilityCenter:
    """
    统一能力中心
    
    统一管理Skill、Tool、MCP三层能力
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.capabilities: Dict[str, BaseCapability] = {}
        self.capability_index = CapabilityIndex()
        self.discovery_service = CapabilityDiscoveryService()
        
    async def initialize(self):
        """初始化能力中心"""
        # 1. 加载所有Skill
        await self._load_skills()
        
        # 2. 加载所有Tool
        await self._load_tools()
        
        # 3. 加载所有MCP能力
        await self._load_mcp_capabilities()
        
        # 4. 构建能力索引
        await self._build_index()
    
    async def _load_skills(self):
        """加载技能"""
        skills = self.db.query(Skill).filter(
            Skill.status == "active"
        ).all()
        
        for skill in skills:
            capability = SkillCapability(skill)
            self.capabilities[skill.name] = capability
    
    async def _load_tools(self):
        """加载工具"""
        tools = self.db.query(Tool).filter(
            Tool.is_active == True
        ).all()
        
        for tool in tools:
            capability = ToolCapability(tool)
            self.capabilities[tool.name] = capability
    
    async def _load_mcp_capabilities(self):
        """加载MCP能力"""
        mcp_configs = self.db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.enabled == True
        ).all()
        
        for config in mcp_configs:
            tool_mappings = self.db.query(MCPToolMappingModel).filter(
                MCPToolMappingModel.client_config_id == config.id,
                MCPToolMappingModel.enabled == True
            ).all()
            
            for mapping in tool_mappings:
                capability = MCPCapability(config, mapping)
                self.capabilities[mapping.local_name] = capability
    
    async def discover_capabilities(self, 
                                   query: str,
                                   context: ExecutionContext) -> List[CapabilityMatch]:
        """
        发现相关能力
        
        基于查询和上下文，发现最相关的能力
        """
        matches = []
        
        # 1. 语义匹配
        semantic_matches = await self.capability_index.semantic_search(query)
        matches.extend(semantic_matches)
        
        # 2. 标签匹配
        tag_matches = await self.capability_index.tag_search(query)
        matches.extend(tag_matches)
        
        # 3. 历史使用匹配
        history_matches = await self._match_by_history(query, context.user_id)
        matches.extend(history_matches)
        
        # 4. 场景匹配
        scene_matches = await self._match_by_scene(context.scene)
        matches.extend(scene_matches)
        
        # 5. 去重和排序
        unique_matches = self._deduplicate_and_rank(matches)
        
        return unique_matches
    
    async def execute_capability(self,
                                capability_name: str,
                                input_data: Dict[str, Any],
                                context: ExecutionContext) -> CapabilityResult:
        """
        执行指定能力
        
        提供统一的能力执行接口
        """
        capability = self.capabilities.get(capability_name)
        if not capability:
            return CapabilityResult(
                success=False,
                error=f"能力 '{capability_name}' 不存在"
            )
        
        # 验证输入
        validation = await capability.validate_input(input_data)
        if not validation.valid:
            return CapabilityResult(
                success=False,
                error=f"输入验证失败: {validation.error}"
            )
        
        # 执行能力
        start_time = time.time()
        try:
            result = await capability.execute(input_data, context)
            execution_time = time.time() - start_time
            
            # 更新统计
            capability.update_stats(execution_time, result.success)
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            capability.update_stats(execution_time, False)
            
            return CapabilityResult(
                success=False,
                error=str(e)
            )
    
    def get_capability_metadata(self, capability_name: str) -> Optional[CapabilityMetadata]:
        """获取能力元数据"""
        capability = self.capabilities.get(capability_name)
        if capability:
            return capability.metadata
        return None
    
    def list_capabilities(self, 
                         category: Optional[str] = None,
                         capability_type: Optional[CapabilityType] = None) -> List[CapabilityMetadata]:
        """列出所有能力"""
        results = []
        for name, capability in self.capabilities.items():
            if category and capability.metadata.category != category:
                continue
            if capability_type and capability.metadata.capability_type != capability_type:
                continue
            results.append(capability.metadata)
        return results
```

### 3.5 智能编排引擎

```python
# app/orchestration/intelligent_orchestrator.py

class IntelligentOrchestrator:
    """
    智能编排引擎
    
    基于意图自动编排多个能力完成复杂任务
    """
    
    def __init__(self, 
                 capability_center: UnifiedCapabilityCenter,
                 memory_service: MemoryService):
        self.capability_center = capability_center
        self.memory_service = memory_service
        self.task_planner = TaskPlanner()
        self.execution_engine = ExecutionEngine()
    
    async def orchestrate(self,
                         user_input: str,
                         context: ExecutionContext) -> OrchestrationResult:
        """
        智能编排主方法
        
        完整流程：
        1. 意图理解
        2. 任务规划
        3. 能力发现
        4. 能力编排
        5. 执行监控
        6. 结果融合
        """
        # 1. 意图理解
        intent = await self._understand_intent(user_input, context)
        
        # 2. 检索相关记忆
        memories = await self.memory_service.recall(
            user_id=context.user_id,
            query=user_input,
            context=intent
        )
        
        # 3. 任务规划
        task_plan = await self.task_planner.plan(
            intent=intent,
            memories=memories,
            context=context
        )
        
        # 4. 为每个任务步骤发现能力
        for step in task_plan.steps:
            capabilities = await self.capability_center.discover_capabilities(
                query=step.description,
                context=context
            )
            step.candidate_capabilities = capabilities
        
        # 5. 能力编排
        execution_plan = await self._compose_capabilities(task_plan)
        
        # 6. 执行计划
        execution_result = await self.execution_engine.execute(
            plan=execution_plan,
            context=context
        )
        
        # 7. 结果融合
        final_result = await self._fuse_results(
            execution_result,
            intent
        )
        
        # 8. 存储记忆
        await self.memory_service.remember(
            user_id=context.user_id,
            interaction=InteractionRecord(
                input=user_input,
                output=final_result,
                plan=task_plan,
                execution=execution_result
            )
        )
        
        return OrchestrationResult(
            success=execution_result.success,
            result=final_result,
            execution_plan=execution_plan,
            used_capabilities=execution_result.used_capabilities
        )
    
    async def _compose_capabilities(self, task_plan: TaskPlan) -> ExecutionPlan:
        """
        能力编排
        
        决定如何组合多个能力完成任务
        """
        execution_steps = []
        
        for task_step in task_plan.steps:
            # 选择最佳能力
            best_capability = await self._select_best_capability(
                task_step.candidate_capabilities,
                task_step
            )
            
            # 构建执行步骤
            execution_step = ExecutionStep(
                step_id=task_step.id,
                capability_name=best_capability.name,
                input_mapping=await self._build_input_mapping(
                    task_step, 
                    execution_steps
                ),
                output_mapping=task_step.expected_output,
                retry_policy=RetryPolicy(max_retries=3),
                fallback_capabilities=[
                    c.name for c in task_step.candidate_capabilities[1:3]
                ]
            )
            
            execution_steps.append(execution_step)
        
        return ExecutionPlan(
            steps=execution_steps,
            execution_mode=task_plan.execution_mode,  # sequential/parallel/conditional
            rollback_policy=RollbackPolicy()
        )
    
    async def _select_best_capability(self,
                                     candidates: List[CapabilityMatch],
                                     task_step: TaskStep) -> CapabilityMatch:
        """
        选择最佳能力
        
        综合考虑：
        - 匹配分数
        - 历史成功率
        - 执行时间
        - 资源消耗
        """
        scored_candidates = []
        
        for candidate in candidates:
            score = candidate.match_score
            
            # 获取能力统计
            capability = self.capability_center.capabilities.get(candidate.name)
            if capability:
                stats = capability.execution_stats
                
                # 成功率权重
                if stats["total_calls"] > 0:
                    success_rate = stats["successful_calls"] / stats["total_calls"]
                    score += success_rate * 0.2
                
                # 执行时间权重（越短越好）
                if stats["average_execution_time"] > 0:
                    time_score = 1.0 / (1.0 + stats["average_execution_time"] / 1000)
                    score += time_score * 0.1
            
            scored_candidates.append((candidate, score))
        
        # 排序并返回最佳
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[0][0] if scored_candidates else None
```

### 3.6 11个官方智能体的能力化改造

```python
# app/capabilities/official_capabilities.py

"""
11个官方智能体的能力化封装

将原有的11个官方智能体改造为可复用的能力单元
"""

class ChatCapability(BaseCapability):
    """
    聊天对话能力（原聊天助手）
    """
    
    def __init__(self):
        super().__init__(CapabilityMetadata(
            name="chat",
            display_name="聊天对话",
            description="通用对话能力，支持日常聊天、问答、建议",
            capability_type=CapabilityType.SKILL,
            level=CapabilityLevel.COMPOSITE,
            category="conversation",
            tags=["对话", "聊天", "问答"]
        ))
        self.llm_service = LLMService()
    
    async def execute(self, input_data: Dict, context: ExecutionContext) -> CapabilityResult:
        message = input_data.get("message")
        history = input_data.get("history", [])
        
        response = await self.llm_service.chat(
            message=message,
            history=history,
            system_prompt="你是一个友好、专业的AI助手。"
        )
        
        return CapabilityResult(
            success=True,
            output=response
        )


class TranslationCapability(BaseCapability):
    """
    翻译能力（原翻译专家）
    """
    
    def __init__(self):
        super().__init__(CapabilityMetadata(
            name="translation",
            display_name="多语言翻译",
            description="专业的多语言翻译能力",
            capability_type=CapabilityType.SKILL,
            level=CapabilityLevel.ATOMIC,
            category="language",
            tags=["翻译", "语言", "文本处理"],
            input_schema={
                "text": {"type": "string", "required": True},
                "target_language": {"type": "string", "required": True},
                "source_language": {"type": "string", "required": False}
            }
        ))
    
    async def execute(self, input_data: Dict, context: ExecutionContext) -> CapabilityResult:
        text = input_data.get("text")
        target_lang = input_data.get("target_language")
        source_lang = input_data.get("source_language", "auto")
        
        # 调用翻译服务
        translation = await self._translate(text, target_lang, source_lang)
        
        return CapabilityResult(
            success=True,
            output=translation
        )


class KnowledgeSearchCapability(BaseCapability):
    """
    知识搜索能力（原知识库搜索）
    """
    
    def __init__(self):
        super().__init__(CapabilityMetadata(
            name="knowledge_search",
            display_name="知识库搜索",
            description="在知识库中搜索和检索信息",
            capability_type=CapabilityType.SKILL,
            level=CapabilityLevel.COMPOSITE,
            category="search",
            tags=["搜索", "知识", "检索"],
            input_schema={
                "query": {"type": "string", "required": True},
                "knowledge_base_id": {"type": "integer", "required": False},
                "limit": {"type": "integer", "default": 5}
            }
        ))
        self.retrieval_service = RetrievalService()
    
    async def execute(self, input_data: Dict, context: ExecutionContext) -> CapabilityResult:
        query = input_data.get("query")
        kb_id = input_data.get("knowledge_base_id")
        limit = input_data.get("limit", 5)
        
        results = await self.retrieval_service.search(
            query=query,
            knowledge_base_id=kb_id,
            limit=limit
        )
        
        # 生成回答
        answer = await self._synthesize_answer(results, query)
        
        return CapabilityResult(
            success=True,
            output=answer,
            metadata={"sources": [r.source for r in results]}
        )


class WebSearchCapability(BaseCapability):
    """
    Web搜索能力（原Web搜索助手）
    """
    
    def __init__(self):
        super().__init__(CapabilityMetadata(
            name="web_search",
            display_name="Web搜索",
            description="使用网络搜索获取最新信息",
            capability_type=CapabilityType.TOOL,
            level=CapabilityLevel.ATOMIC,
            category="search",
            tags=["搜索", "网络", "实时"]
        ))
    
    async def execute(self, input_data: Dict, context: ExecutionContext) -> CapabilityResult:
        query = input_data.get("query")
        
        # 调用Web搜索工具
        search_results = await self._web_search(query)
        
        return CapabilityResult(
            success=True,
            output=search_results
        )


class ImageGenerationCapability(BaseCapability):
    """
    图片生成能力（原图片生成器）
    """
    
    def __init__(self):
        super().__init__(CapabilityMetadata(
            name="image_generation",
            display_name="图片生成",
            description="根据描述生成图片",
            capability_type=CapabilityType.TOOL,
            level=CapabilityLevel.ATOMIC,
            category="multimedia",
            tags=["图片", "生成", "AI绘图"]
        ))
    
    async def execute(self, input_data: Dict, context: ExecutionContext) -> CapabilityResult:
        prompt = input_data.get("prompt")
        
        # 调用图像生成服务
        image_url = await self._generate_image(prompt)
        
        return CapabilityResult(
            success=True,
            output=image_url,
            artifacts=[{
                "type": "image",
                "url": image_url
            }]
        )


# 其他能力类似封装...
# - ImageRecognitionCapability (图像识别专家)
# - VideoGenerationCapability (视频生成器)
# - VideoAnalysisCapability (视频分析专家)
# - SpeechRecognitionCapability (语音识别助手)
# - TTSCapability (文字转语音)
# - STTCapability (语音转文字)


class OfficialCapabilitiesRegistry:
    """
    官方能力注册表
    
    管理所有11个官方能力的注册和发现
    """
    
    def __init__(self):
        self.capabilities = {}
    
    def register_all(self):
        """注册所有官方能力"""
        official_capabilities = [
            ChatCapability(),
            TranslationCapability(),
            KnowledgeSearchCapability(),
            WebSearchCapability(),
            ImageGenerationCapability(),
            # ... 其他能力
        ]
        
        for capability in official_capabilities:
            self.capabilities[capability.metadata.name] = capability
    
    def get_capability(self, name: str) -> Optional[BaseCapability]:
        """获取指定能力"""
        return self.capabilities.get(name)
    
    def list_all(self) -> List[BaseCapability]:
        """列出所有官方能力"""
        return list(self.capabilities.values())
```

---

## 四、与现有系统的集成

### 4.1 集成架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    与现有系统的集成方案                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  新架构组件                          现有系统组件                │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌───────────────────┐             ┌───────────────────┐       │
│  │ UnifiedAgent      │◄───────────►│ Agent模型         │       │
│  │ (统一智能体入口)   │             │ (现有Agent表)      │       │
│  └───────────────────┘             └───────────────────┘       │
│           │                                                        │
│           ▼                                                        │
│  ┌───────────────────┐             ┌───────────────────┐       │
│  │ UnifiedCapability │◄───────────►│ Skill模型         │       │
│  │ Center            │◄───────────►│ Tool模型          │       │
│  │ (统一能力中心)     │◄───────────►│ MCP配置           │       │
│  └───────────────────┘             └───────────────────┘       │
│           │                                                        │
│           ▼                                                        │
│  ┌───────────────────┐             ┌───────────────────┐       │
│  │ IntelligentOrche- │◄───────────►│ AgentExecution    │       │
│  │ strator           │◄───────────►│ Engine            │       │
│  │ (智能编排引擎)     │◄───────────►│ SkillExecution    │       │
│  │                   │             │ Engine            │       │
│  └───────────────────┘             └───────────────────┘       │
│           │                                                        │
│           ▼                                                        │
│  ┌───────────────────┐             ┌───────────────────┐       │
│  │ MemoryService     │◄───────────►│ GlobalMemory      │       │
│  │ (记忆服务)         │◄───────────►│ (现有记忆表)       │       │
│  └───────────────────┘             └───────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 数据库迁移方案

```python
# alembic/versions/xxx_unified_capability_support.py

"""
统一能力中心支持的数据库迁移
"""

def upgrade():
    # 1. 扩展现有Agent表
    op.add_column('agents', sa.Column('unified_mode', sa.Boolean(), default=False))
    op.add_column('agents', sa.Column('orchestration_config', sa.JSON(), nullable=True))
    
    # 2. 创建能力编排日志表
    op.create_table(
        'capability_orchestration_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.id')),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('input_text', sa.Text()),
        sa.Column('intent_type', sa.String(100)),
        sa.Column('execution_plan', sa.JSON()),
        sa.Column('used_capabilities', sa.JSON()),
        sa.Column('execution_time_ms', sa.Integer()),
        sa.Column('success', sa.Boolean()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )
    
    # 3. 创建能力依赖关系表
    op.create_table(
        'capability_dependencies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_capability', sa.String(100)),
        sa.Column('target_capability', sa.String(100)),
        sa.Column('dependency_type', sa.String(50)),  # hard/soft
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )
    
    # 4. 扩展现有技能表
    op.add_column('skills', sa.Column('capability_name', sa.String(100), nullable=True))
    op.add_column('skills', sa.Column('unified_interface', sa.Boolean(), default=False))
    
    # 5. 扩展现有工具表
    op.add_column('tools', sa.Column('capability_name', sa.String(100), nullable=True))
    op.add_column('tools', sa.Column('unified_interface', sa.Boolean(), default=False))
```

---

## 五、实施路线图

### 阶段一：基础能力封装（4周）

```
Week 1: 能力抽象框架
├── 创建BaseCapability抽象基类
├── 定义CapabilityMetadata标准
└── 实现能力执行上下文

Week 2: Skill能力封装
├── 实现SkillCapability封装器
├── 迁移现有Skill到统一接口
└── 测试Skill能力调用

Week 3: Tool能力封装
├── 实现ToolCapability封装器
├── 迁移现有Tool到统一接口
└── 测试Tool能力调用

Week 4: MCP能力封装
├── 实现MCPCapability封装器
├── 集成MCP客户端
└── 测试MCP能力调用
```

### 阶段二：统一能力中心（3周）

```
Week 5: 能力中心核心
├── 实现UnifiedCapabilityCenter
├── 实现能力发现服务
└── 实现能力索引

Week 6: 能力编排
├── 实现CapabilityComposer
├── 实现依赖分析
└── 实现执行计划生成

Week 7: 11个官方能力
├── 封装11个官方智能体为能力
├── 注册到能力中心
└── 测试能力调用
```

### 阶段三：智能编排引擎（3周）

```
Week 8: 意图理解
├── 增强意图识别
├── 实现多意图检测
└── 实现实体提取

Week 9: 任务规划
├── 实现TaskPlanner
├── 实现任务分解
└── 实现依赖分析

Week 10: 编排执行
├── 实现IntelligentOrchestrator
├── 实现能力选择算法
└── 实现结果融合
```

### 阶段四：集成测试（2周）

```
Week 11: 集成测试
├── 端到端测试
├── 性能测试
└── 兼容性测试

Week 12: 优化上线
├── 性能优化
├── 文档完善
└── 灰度发布
```

---

## 六、预期效果

### 6.1 架构优化效果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 能力复用率 | 30% | 85% | **183%** |
| 任务编排复杂度 | 高（手动） | 低（自动） | **智能化** |
| 新能力接入时间 | 3天 | 2小时 | **91%** |
| 跨能力协作 | 不支持 | 原生支持 | **质变** |

### 6.2 用户体验提升

```
优化前：
用户："帮我搜索AI最新进展，然后生成一份PPT"
系统：请切换到"Web搜索助手"... 搜索完成...
      请切换到"PPT生成技能"... 生成完成...
      （上下文丢失，需要重复说明需求）

优化后：
用户："帮我搜索AI最新进展，然后生成一份PPT"
系统：正在搜索AI最新进展... 找到10篇相关文章
      正在分析内容并生成PPT大纲...
      正在生成PPT... 完成！
      （自动调用web_search + knowledge_search + ppt_generation技能）
```

---

## 七、总结

本方案通过引入**统一能力抽象**，将现有的三层能力体系（Skill/Tool/MCP）和11个官方智能体整合为一个统一的能力中心：

### 核心创新

1. **统一能力抽象** - Skill/Tool/MCP统一封装为Capability
2. **智能编排引擎** - 自动发现、选择、编排能力
3. **能力复用** - 11个官方智能体改造为可复用能力
4. **无缝集成** - 与现有系统完全兼容

### 技术亮点

- 保留现有所有功能和能力
- 通过封装层实现统一接口
- 智能编排实现复杂任务自动化
- 持续学习优化能力选择

通过本方案的实施，可以将现有的割裂的能力体系整合为一个真正统一、智能、可扩展的Agent系统。
