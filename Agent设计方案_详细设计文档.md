# Agent设计方案 - 详细设计文档

## 目录

1. [统一能力抽象层设计](#一统一能力抽象层设计)
2. [统一能力中心设计](#二统一能力中心设计)
3. [智能编排引擎设计](#三智能编排引擎设计)
4. [11个官方能力封装](#四11个官方能力封装)
5. [能力编排执行流程](#五能力编排执行流程)
6. [数据库模型设计](#六数据库模型设计)
7. [API接口设计](#七api接口设计)

---

## 一、统一能力抽象层设计

### 1.1 核心类图

```
┌─────────────────────────────────────────────────────────────────┐
│                      能力抽象层类图                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    <<abstract>>                         │   │
│  │                  BaseCapability                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ - metadata: CapabilityMetadata                          │   │
│  │ - execution_stats: Dict                                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ + execute(input, context): CapabilityResult             │   │
│  │ + validate_input(input): ValidationResult               │   │
│  │ + get_capabilities(): List[str]                         │   │
│  │ + update_stats(time, success): void                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              △                                  │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│              ▼               ▼               ▼                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ SkillCapability │ │ ToolCapability  │ │  MCPCapability  │   │
│  ├─────────────────┤ ├─────────────────┤ ├─────────────────┤   │
│  │ - skill: Skill  │ │ - tool: Tool    │ │ - client_config │   │
│  │ - engine        │ │ - handler       │ │ - tool_mapping  │   │
│  ├─────────────────┤ ├─────────────────┤ ├─────────────────┤   │
│  │ + execute()     │ │ + execute()     │ │ + execute()     │   │
│  │ + _execute_*()  │ │ + _execute_*()  │ │ + _call_mcp()   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 详细代码实现

#### 1.2.1 基础类型定义

```python
# app/capabilities/types.py

from enum import Enum, auto
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


class CapabilityType(Enum):
    """
    能力类型枚举
    
    定义三种基本能力类型
    """
    SKILL = "skill"      # 高阶技能，包含完整业务逻辑
    TOOL = "tool"        # 原子工具，单一功能
    MCP = "mcp"          # MCP连接器，外部服务


class CapabilityLevel(Enum):
    """
    能力级别枚举
    
    定义能力的复杂程度
    """
    ATOMIC = "atomic"           # 原子能力，不可再分
    COMPOSITE = "composite"     # 复合能力，由多个原子能力组成
    WORKFLOW = "workflow"       # 工作流能力，包含完整流程


class ExecutionMode(Enum):
    """
    执行模式枚举
    
    定义多步骤能力的执行方式
    """
    SEQUENTIAL = "sequential"   # 顺序执行
    PARALLEL = "parallel"       # 并行执行
    CONDITIONAL = "conditional" # 条件执行


@dataclass
class CapabilityMetadata:
    """
    能力元数据
    
    描述能力的基本信息和约束
    """
    # 基本信息
    name: str                                   # 唯一标识名
    display_name: str                           # 显示名称
    description: str                            # 描述
    
    # 分类信息
    capability_type: CapabilityType             # 能力类型
    level: CapabilityLevel                      # 能力级别
    category: str                               # 分类
    tags: List[str] = field(default_factory=list)  # 标签
    
    # 接口定义
    input_schema: Dict[str, Any] = field(default_factory=dict)   # 输入参数模式
    output_schema: Dict[str, Any] = field(default_factory=dict)  # 输出结果模式
    
    # 依赖关系
    dependencies: List[str] = field(default_factory=list)        # 依赖的其他能力
    required_resources: List[str] = field(default_factory=list)  # 所需资源
    
    # 执行配置
    timeout_seconds: int = 30                   # 超时时间
    max_retries: int = 3                        # 最大重试次数
    retry_delay_seconds: int = 1                # 重试间隔
    
    # 权限控制
    required_permissions: List[str] = field(default_factory=list)  # 所需权限
    
    # 版本信息
    version: str = "1.0.0"                      # 版本号
    author: str = ""                            # 作者
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "capability_type": self.capability_type.value,
            "level": self.level.value,
            "category": self.category,
            "tags": self.tags,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "dependencies": self.dependencies,
            "required_resources": self.required_resources,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "version": self.version,
            "author": self.author
        }


@dataclass
class ValidationResult:
    """
    输入验证结果
    """
    valid: bool                                 # 是否有效
    error: Optional[str] = None                 # 错误信息
    warnings: List[str] = field(default_factory=list)  # 警告信息
    normalized_input: Optional[Dict[str, Any]] = None  # 规范化后的输入


@dataclass
class CapabilityResult:
    """
    能力执行结果
    """
    success: bool                               # 是否成功
    output: Any = None                          # 输出数据
    error: Optional[str] = None                 # 错误信息
    artifacts: List[Dict[str, Any]] = field(default_factory=list)  # 生成的产物
    execution_time_ms: int = 0                  # 执行时间（毫秒）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "artifacts": self.artifacts,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata
        }


@dataclass
class ExecutionContext:
    """
    执行上下文
    
    传递执行过程中的上下文信息
    """
    # 身份标识
    user_id: Optional[int] = None
    agent_id: Optional[int] = None
    conversation_id: Optional[int] = None
    session_id: Optional[str] = None
    
    # 执行追踪
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_execution_id: Optional[str] = None
    
    # 上下文数据
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    # 历史记录
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 记忆服务
    memory_service: Optional[Any] = None
    
    # 场景信息
    scene: Optional[str] = None
    intent: Optional[Dict[str, Any]] = None
    
    def get(self, key: str, default=None):
        """获取上下文数据"""
        return self.context_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置上下文数据"""
        self.context_data[key] = value
    
    def create_child_context(self) -> 'ExecutionContext':
        """创建子上下文"""
        return ExecutionContext(
            user_id=self.user_id,
            agent_id=self.agent_id,
            conversation_id=self.conversation_id,
            session_id=self.session_id,
            parent_execution_id=self.execution_id,
            memory_service=self.memory_service,
            scene=self.scene
        )
```

#### 1.2.2 基础能力抽象类

```python
# app/capabilities/base_capability.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import uuid

from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    CapabilityType,
    CapabilityLevel
)


class BaseCapability(ABC):
    """
    能力统一抽象基类
    
    这是整个能力中心的核心抽象，所有具体能力都必须继承此类。
    提供统一的能力接口、执行监控、统计收集等功能。
    
    Attributes:
        metadata: 能力元数据，描述能力的基本信息
        execution_stats: 执行统计数据
        _capability_id: 能力唯一标识
    
    Example:
        ```python
        class MyCapability(BaseCapability):
            def __init__(self):
                metadata = CapabilityMetadata(
                    name="my_capability",
                    display_name="我的能力",
                    description="这是一个示例能力",
                    capability_type=CapabilityType.TOOL,
                    level=CapabilityLevel.ATOMIC,
                    category="example"
                )
                super().__init__(metadata)
            
            async def execute(self, input_data, context):
                # 实现能力逻辑
                return CapabilityResult(success=True, output="result")
        ```
    """
    
    def __init__(self, metadata: CapabilityMetadata):
        """
        初始化能力
        
        Args:
            metadata: 能力元数据
        """
        self.metadata = metadata
        self._capability_id = str(uuid.uuid4())
        
        # 执行统计
        self._execution_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_execution_time_ms": 0,
            "average_execution_time_ms": 0.0,
            "last_execution_time": None,
            "success_rate": 1.0
        }
        
        # 执行历史（保留最近100条）
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history_size = 100
    
    @property
    def capability_id(self) -> str:
        """获取能力唯一标识"""
        return self._capability_id
    
    @property
    def name(self) -> str:
        """获取能力名称"""
        return self.metadata.name
    
    @property
    def execution_stats(self) -> Dict[str, Any]:
        """获取执行统计（返回副本）"""
        return self._execution_stats.copy()
    
    async def execute(self,
                     input_data: Dict[str, Any],
                     context: ExecutionContext) -> CapabilityResult:
        """
        执行能力（模板方法模式）
        
        提供统一的执行流程：
        1. 输入验证
        2. 前置处理
        3. 实际执行
        4. 后置处理
        5. 统计更新
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        start_time = time.time()
        execution_record = {
            "execution_id": str(uuid.uuid4()),
            "start_time": datetime.now(),
            "input_data": input_data,
            "context": {
                "user_id": context.user_id,
                "conversation_id": context.conversation_id,
                "scene": context.scene
            }
        }
        
        try:
            # 1. 输入验证
            validation = await self.validate_input(input_data)
            if not validation.valid:
                return CapabilityResult(
                    success=False,
                    error=f"输入验证失败: {validation.error}",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # 使用规范化后的输入
            if validation.normalized_input:
                input_data = validation.normalized_input
            
            # 2. 前置处理
            await self._before_execute(input_data, context)
            
            # 3. 实际执行（由子类实现）
            result = await self._do_execute(input_data, context)
            
            # 4. 后置处理
            await self._after_execute(result, context)
            
            # 5. 更新统计
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._update_stats(execution_time_ms, result.success)
            
            # 更新执行记录
            execution_record.update({
                "end_time": datetime.now(),
                "success": result.success,
                "execution_time_ms": execution_time_ms
            })
            self._add_execution_history(execution_record)
            
            # 设置执行时间
            result.execution_time_ms = execution_time_ms
            
            return result
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._update_stats(execution_time_ms, False)
            
            execution_record.update({
                "end_time": datetime.now(),
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms
            })
            self._add_execution_history(execution_record)
            
            return CapabilityResult(
                success=False,
                error=f"能力执行异常: {str(e)}",
                execution_time_ms=execution_time_ms,
                metadata={"exception_type": type(e).__name__}
            )
    
    @abstractmethod
    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """
        实际执行能力（子类必须实现）
        
        Args:
            input_data: 输入数据
            context: 执行上下文
            
        Returns:
            CapabilityResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """
        验证输入数据（子类必须实现）
        
        Args:
            input_data: 输入数据
            
        Returns:
            ValidationResult: 验证结果
        """
        pass
    
    async def _before_execute(self,
                             input_data: Dict[str, Any],
                             context: ExecutionContext):
        """
        执行前钩子（可选重写）
        
        Args:
            input_data: 输入数据
            context: 执行上下文
        """
        pass
    
    async def _after_execute(self,
                            result: CapabilityResult,
                            context: ExecutionContext):
        """
        执行后钩子（可选重写）
        
        Args:
            result: 执行结果
            context: 执行上下文
        """
        pass
    
    def _update_stats(self, execution_time_ms: int, success: bool):
        """
        更新执行统计
        
        Args:
            execution_time_ms: 执行时间（毫秒）
            success: 是否成功
        """
        stats = self._execution_stats
        stats["total_calls"] += 1
        stats["total_execution_time_ms"] += execution_time_ms
        
        if success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
        
        # 计算平均值
        stats["average_execution_time_ms"] = (
            stats["total_execution_time_ms"] / stats["total_calls"]
        )
        
        # 计算成功率
        stats["success_rate"] = (
            stats["successful_calls"] / stats["total_calls"]
        )
        
        stats["last_execution_time"] = datetime.now()
    
    def _add_execution_history(self, record: Dict[str, Any]):
        """
        添加执行历史
        
        Args:
            record: 执行记录
        """
        self._execution_history.append(record)
        
        # 限制历史记录大小
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Args:
            limit: 返回记录数
            
        Returns:
            List[Dict]: 执行历史
        """
        return self._execution_history[-limit:]
    
    async def get_capabilities(self) -> List[str]:
        """
        获取子能力列表
        
        用于复合能力，返回包含的子能力名称
        
        Returns:
            List[str]: 子能力名称列表
        """
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示
        
        Returns:
            Dict: 能力的字典表示
        """
        return {
            "capability_id": self._capability_id,
            "metadata": self.metadata.to_dict(),
            "execution_stats": self.execution_stats,
            "history_count": len(self._execution_history)
        }
```

#### 1.2.3 输入验证基类

```python
# app/capabilities/validators.py

from typing import Dict, Any, List, Optional
from app.capabilities.types import ValidationResult


class InputValidator:
    """
    输入验证器基类
    
    提供基于JSON Schema的输入验证
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        初始化验证器
        
        Args:
            schema: JSON Schema定义
        """
        self.schema = schema
    
    def validate(self, input_data: Dict[str, Any]) -> ValidationResult:
        """
        验证输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        normalized = {}
        
        # 验证必填字段
        required = self.schema.get("required", [])
        for field in required:
            if field not in input_data:
                errors.append(f"缺少必填字段: {field}")
            else:
                normalized[field] = input_data[field]
        
        # 验证字段类型
        properties = self.schema.get("properties", {})
        for field, value in input_data.items():
            if field in properties:
                field_schema = properties[field]
                field_type = field_schema.get("type")
                
                # 类型验证
                if field_type and not self._check_type(value, field_type):
                    errors.append(f"字段 '{field}' 类型错误，期望 {field_type}")
                    continue
                
                # 范围验证
                if field_type == "string":
                    min_length = field_schema.get("minLength")
                    max_length = field_schema.get("maxLength")
                    if min_length and len(value) < min_length:
                        errors.append(f"字段 '{field}' 长度不能小于 {min_length}")
                    if max_length and len(value) > max_length:
                        errors.append(f"字段 '{field}' 长度不能大于 {max_length}")
                
                elif field_type == "number" or field_type == "integer":
                    minimum = field_schema.get("minimum")
                    maximum = field_schema.get("maximum")
                    if minimum is not None and value < minimum:
                        errors.append(f"字段 '{field}' 不能小于 {minimum}")
                    if maximum is not None and value > maximum:
                        errors.append(f"字段 '{field}' 不能大于 {maximum}")
                
                # 枚举验证
                enum_values = field_schema.get("enum")
                if enum_values and value not in enum_values:
                    errors.append(f"字段 '{field}' 必须是以下值之一: {enum_values}")
                
                normalized[field] = value
            else:
                # 未定义的字段，作为警告
                warnings.append(f"未知字段: {field}")
                normalized[field] = value
        
        # 应用默认值
        for field, field_schema in properties.items():
            if field not in normalized and "default" in field_schema:
                normalized[field] = field_schema["default"]
        
        if errors:
            return ValidationResult(
                valid=False,
                error="; ".join(errors),
                warnings=warnings
            )
        
        return ValidationResult(
            valid=True,
            warnings=warnings,
            normalized_input=normalized
        )
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        检查类型
        
        Args:
            value: 值
            expected_type: 期望类型
            
        Returns:
            bool: 类型是否匹配
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected = type_mapping.get(expected_type)
        if expected is None:
            return True
        
        return isinstance(value, expected)
```

---

## 二、统一能力中心设计

### 2.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    统一能力中心架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              UnifiedCapabilityCenter                    │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐              │   │
│  │  │  CapabilityStore│  │CapabilityIndex  │              │   │
│  │  │  (能力存储)      │  │  (能力索引)     │              │   │
│  │  │                 │  │                 │              │   │
│  │  │ • Skill封装     │  │ • 语义索引       │              │   │
│  │  │ • Tool封装      │  │ • 标签索引       │              │   │
│  │  │ • MCP封装       │  │ • 场景索引       │              │   │
│  │  │ • 官方能力      │  │ • 使用频率索引   │              │   │
│  │  └─────────────────┘  └─────────────────┘              │   │
│  │                                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐              │   │
│  │  │DiscoveryService │  │ ExecutionEngine │              │   │
│  │  │  (发现服务)      │  │  (执行引擎)     │              │   │
│  │  │                 │  │                 │              │   │
│  │  │ • 语义匹配       │  │ • 执行调度       │              │   │
│  │  │ • 标签匹配       │  │ • 超时控制       │              │   │
│  │  │ • 历史匹配       │  │ • 重试机制       │              │   │
│  │  │ • 场景匹配       │  │ • 并发控制       │              │   │
│  │  └─────────────────┘  └─────────────────┘              │   │
│  │                                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐              │   │
│  │  │ MonitorService  │  │ LearningEngine  │              │   │
│  │  │  (监控服务)      │  │  (学习引擎)     │              │   │
│  │  │                 │  │                 │              │   │
│  │  │ • 性能监控       │  │ • 使用模式学习   │              │   │
│  │  │ • 错误追踪       │  │ • 推荐优化       │              │   │
│  │  │ • 统计分析       │  │ • 自动调优       │              │   │
│  │  └─────────────────┘  └─────────────────┘              │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 详细代码实现

#### 2.2.1 能力中心核心类

```python
# app/capabilities/unified_capability_center.py

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from sqlalchemy.orm import Session

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    CapabilityType
)
from app.capabilities.discovery import CapabilityDiscoveryService
from app.capabilities.index import CapabilityIndex
from app.capabilities.execution import CapabilityExecutionEngine
from app.capabilities.monitor import CapabilityMonitorService

from app.models.skill import Skill
from app.models.tool import Tool
from app.models.agent import Agent
from app.mcp.models import MCPClientConfigModel, MCPToolMappingModel

logger = logging.getLogger(__name__)


@dataclass
class CapabilityMatch:
    """
    能力匹配结果
    """
    name: str
    match_score: float
    match_type: str  # semantic/tag/history/scene
    metadata: CapabilityMetadata
    confidence: float
    reason: str


class UnifiedCapabilityCenter:
    """
    统一能力中心
    
    统一管理Skill、Tool、MCP三层能力，提供统一的能力发现、执行、监控接口。
    
    核心职责：
    1. 能力注册与存储
    2. 能力发现与匹配
    3. 能力执行与调度
    4. 能力监控与统计
    5. 能力学习与优化
    
    Example:
        ```python
        # 初始化
        center = UnifiedCapabilityCenter(db)
        await center.initialize()
        
        # 发现能力
        matches = await center.discover_capabilities(
            query="搜索最新新闻",
            context=execution_context
        )
        
        # 执行能力
        result = await center.execute_capability(
            capability_name="web_search",
            input_data={"query": "AI最新进展"},
            context=execution_context
        )
        ```
    """
    
    def __init__(self, db: Session):
        """
        初始化能力中心
        
        Args:
            db: 数据库会话
        """
        self.db = db
        
        # 能力存储
        self._capabilities: Dict[str, BaseCapability] = {}
        
        # 服务组件
        self._index = CapabilityIndex()
        self._discovery = CapabilityDiscoveryService(self)
        self._execution_engine = CapabilityExecutionEngine()
        self._monitor = CapabilityMonitorService()
        
        # 统计信息
        self._stats = {
            "total_capabilities": 0,
            "skill_count": 0,
            "tool_count": 0,
            "mcp_count": 0,
            "total_executions": 0,
            "initialized_at": None
        }
        
        self._initialized = False
    
    async def initialize(self):
        """
        初始化能力中心
        
        加载所有能力并构建索引
        """
        if self._initialized:
            logger.warning("能力中心已经初始化")
            return
        
        logger.info("开始初始化统一能力中心...")
        
        try:
            # 1. 加载所有Skill
            await self._load_skills()
            
            # 2. 加载所有Tool
            await self._load_tools()
            
            # 3. 加载所有MCP能力
            await self._load_mcp_capabilities()
            
            # 4. 加载11个官方能力
            await self._load_official_capabilities()
            
            # 5. 构建索引
            await self._build_index()
            
            # 6. 更新统计
            self._update_stats()
            
            self._stats["initialized_at"] = datetime.now()
            self._initialized = True
            
            logger.info(
                f"能力中心初始化完成: "
                f"总能力数={self._stats['total_capabilities']}, "
                f"Skill={self._stats['skill_count']}, "
                f"Tool={self._stats['tool_count']}, "
                f"MCP={self._stats['mcp_count']}"
            )
            
        except Exception as e:
            logger.error(f"能力中心初始化失败: {e}", exc_info=True)
            raise
    
    async def _load_skills(self):
        """
        加载技能
        
        从数据库加载所有激活的技能并封装为Capability
        """
        from app.capabilities.adapters.skill_adapter import SkillCapability
        
        skills = self.db.query(Skill).filter(
            Skill.status == "active"
        ).all()
        
        logger.info(f"加载 {len(skills)} 个Skill...")
        
        for skill in skills:
            try:
                capability = SkillCapability(skill)
                self._register_capability(capability)
                self._stats["skill_count"] += 1
            except Exception as e:
                logger.error(f"加载Skill失败 {skill.name}: {e}")
    
    async def _load_tools(self):
        """
        加载工具
        
        从数据库加载所有激活的工具并封装为Capability
        """
        from app.capabilities.adapters.tool_adapter import ToolCapability
        
        tools = self.db.query(Tool).filter(
            Tool.is_active == True
        ).all()
        
        logger.info(f"加载 {len(tools)} 个Tool...")
        
        for tool in tools:
            try:
                capability = ToolCapability(tool)
                self._register_capability(capability)
                self._stats["tool_count"] += 1
            except Exception as e:
                logger.error(f"加载Tool失败 {tool.name}: {e}")
    
    async def _load_mcp_capabilities(self):
        """
        加载MCP能力
        
        从数据库加载所有MCP配置和工具映射
        """
        from app.capabilities.adapters.mcp_adapter import MCPCapability
        
        mcp_configs = self.db.query(MCPClientConfigModel).filter(
            MCPClientConfigModel.enabled == True
        ).all()
        
        logger.info(f"加载 {len(mcp_configs)} 个MCP配置...")
        
        for config in mcp_configs:
            tool_mappings = self.db.query(MCPToolMappingModel).filter(
                MCPToolMappingModel.client_config_id == config.id,
                MCPToolMappingModel.enabled == True
            ).all()
            
            for mapping in tool_mappings:
                try:
                    capability = MCPCapability(config, mapping)
                    self._register_capability(capability)
                    self._stats["mcp_count"] += 1
                except Exception as e:
                    logger.error(f"加载MCP能力失败 {mapping.local_name}: {e}")
    
    async def _load_official_capabilities(self):
        """
        加载11个官方能力
        
        将11个官方智能体封装为能力
        """
        from app.capabilities.official import OfficialCapabilitiesRegistry
        
        registry = OfficialCapabilitiesRegistry()
        registry.register_all()
        
        logger.info(f"加载 {len(registry.capabilities)} 个官方能力...")
        
        for name, capability in registry.capabilities.items():
            self._register_capability(capability)
    
    def _register_capability(self, capability: BaseCapability):
        """
        注册能力
        
        Args:
            capability: 能力实例
        """
        name = capability.metadata.name
        
        if name in self._capabilities:
            logger.warning(f"能力 '{name}' 已存在，将被覆盖")
        
        self._capabilities[name] = capability
        logger.debug(f"注册能力: {name}")
    
    async def _build_index(self):
        """
        构建能力索引
        
        构建多种索引以支持快速发现
        """
        logger.info("构建能力索引...")
        
        for name, capability in self._capabilities.items():
            metadata = capability.metadata
            
            # 添加到语义索引
            await self._index.add_semantic(
                name=name,
                description=metadata.description,
                tags=metadata.tags
            )
            
            # 添加到标签索引
            await self._index.add_tags(name, metadata.tags)
            
            # 添加到分类索引
            await self._index.add_category(name, metadata.category)
            
            # 添加到类型索引
            await self._index.add_type(name, metadata.capability_type)
    
    def _update_stats(self):
        """更新统计信息"""
        self._stats["total_capabilities"] = len(self._capabilities)
    
    # ==================== 公共API ====================
    
    async def discover_capabilities(self,
                                   query: str,
                                   context: ExecutionContext,
                                   top_k: int = 5,
                                   min_score: float = 0.3) -> List[CapabilityMatch]:
        """
        发现相关能力
        
        基于查询和上下文，发现最相关的能力
        
        Args:
            query: 查询文本
            context: 执行上下文
            top_k: 返回的最大结果数
            min_score: 最小匹配分数
            
        Returns:
            List[CapabilityMatch]: 匹配的能力列表
        """
        if not self._initialized:
            raise RuntimeError("能力中心未初始化")
        
        logger.debug(f"发现能力: query='{query}', user_id={context.user_id}")
        
        all_matches = []
        
        # 1. 语义匹配
        semantic_matches = await self._discovery.semantic_search(
            query=query,
            min_score=min_score
        )
        all_matches.extend(semantic_matches)
        
        # 2. 标签匹配
        tag_matches = await self._discovery.tag_search(query)
        all_matches.extend(tag_matches)
        
        # 3. 历史使用匹配
        if context.user_id:
            history_matches = await self._discovery.history_search(
                user_id=context.user_id,
                query=query
            )
            all_matches.extend(history_matches)
        
        # 4. 场景匹配
        if context.scene:
            scene_matches = await self._discovery.scene_search(
                scene=context.scene
            )
            all_matches.extend(scene_matches)
        
        # 5. 去重和排序
        unique_matches = self._deduplicate_and_rank(all_matches)
        
        # 6. 添加上下文信息
        for match in unique_matches[:top_k]:
            capability = self._capabilities.get(match.name)
            if capability:
                match.metadata = capability.metadata
        
        return unique_matches[:top_k]
    
    async def execute_capability(self,
                                capability_name: str,
                                input_data: Dict[str, Any],
                                context: ExecutionContext,
                                timeout: Optional[int] = None) -> CapabilityResult:
        """
        执行指定能力
        
        提供统一的能力执行接口，包含超时控制、重试机制等
        
        Args:
            capability_name: 能力名称
            input_data: 输入数据
            context: 执行上下文
            timeout: 超时时间（秒），默认使用能力配置
            
        Returns:
            CapabilityResult: 执行结果
        """
        if not self._initialized:
            raise RuntimeError("能力中心未初始化")
        
        capability = self._capabilities.get(capability_name)
        if not capability:
            return CapabilityResult(
                success=False,
                error=f"能力 '{capability_name}' 不存在"
            )
        
        # 使用配置的超时时间
        if timeout is None:
            timeout = capability.metadata.timeout_seconds
        
        logger.debug(f"执行能力: {capability_name}, timeout={timeout}s")
        
        try:
            # 执行并设置超时
            result = await asyncio.wait_for(
                capability.execute(input_data, context),
                timeout=timeout
            )
            
            # 记录执行
            self._stats["total_executions"] += 1
            await self._monitor.record_execution(
                capability_name=capability_name,
                result=result,
                context=context
            )
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"能力执行超时: {capability_name}")
            return CapabilityResult(
                success=False,
                error=f"能力执行超时（{timeout}秒）"
            )
        except Exception as e:
            logger.error(f"能力执行异常: {capability_name}, error={e}")
            return CapabilityResult(
                success=False,
                error=f"执行异常: {str(e)}"
            )
    
    async def execute_capabilities_parallel(self,
                                           capabilities: List[Tuple[str, Dict[str, Any]]],
                                           context: ExecutionContext,
                                           timeout: Optional[int] = None) -> Dict[str, CapabilityResult]:
        """
        并行执行多个能力
        
        Args:
            capabilities: 能力列表，每个元素为 (capability_name, input_data)
            context: 执行上下文
            timeout: 超时时间
            
        Returns:
            Dict[str, CapabilityResult]: 执行结果字典
        """
        tasks = []
        names = []
        
        for name, input_data in capabilities:
            task = self.execute_capability(name, input_data, context, timeout)
            tasks.append(task)
            names.append(name)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            name: result if not isinstance(result, Exception) else CapabilityResult(
                success=False,
                error=str(result)
            )
            for name, result in zip(names, results)
        }
    
    def get_capability(self, name: str) -> Optional[BaseCapability]:
        """
        获取能力实例
        
        Args:
            name: 能力名称
            
        Returns:
            Optional[BaseCapability]: 能力实例
        """
        return self._capabilities.get(name)
    
    def get_capability_metadata(self, name: str) -> Optional[CapabilityMetadata]:
        """
        获取能力元数据
        
        Args:
            name: 能力名称
            
        Returns:
            Optional[CapabilityMetadata]: 能力元数据
        """
        capability = self._capabilities.get(name)
        return capability.metadata if capability else None
    
    def list_capabilities(self,
                         category: Optional[str] = None,
                         capability_type: Optional[CapabilityType] = None,
                         tags: Optional[List[str]] = None) -> List[CapabilityMetadata]:
        """
        列出能力
        
        Args:
            category: 分类筛选
            capability_type: 类型筛选
            tags: 标签筛选
            
        Returns:
            List[CapabilityMetadata]: 能力元数据列表
        """
        results = []
        
        for name, capability in self._capabilities.items():
            metadata = capability.metadata
            
            # 分类筛选
            if category and metadata.category != category:
                continue
            
            # 类型筛选
            if capability_type and metadata.capability_type != capability_type:
                continue
            
            # 标签筛选
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            results.append(metadata)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self._stats.copy()
    
    def _deduplicate_and_rank(self, matches: List[CapabilityMatch]) -> List[CapabilityMatch]:
        """
        去重并排序匹配结果
        
        Args:
            matches: 匹配结果列表
            
        Returns:
            List[CapabilityMatch]: 处理后的列表
        """
        # 按名称去重，保留最高分数
        unique = {}
        for match in matches:
            if match.name not in unique or unique[match.name].match_score < match.match_score:
                unique[match.name] = match
        
        # 按分数排序
        sorted_matches = sorted(
            unique.values(),
            key=lambda m: m.match_score,
            reverse=True
        )
        
        return sorted_matches
