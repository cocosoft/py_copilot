"""
能力中心核心类型定义

本模块定义了能力中心的所有核心数据类型和枚举
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class CapabilityType(Enum):
    """
    能力类型枚举
    
    定义能力的三种基本类型
    """
    SKILL = "skill"      # 技能类型：复杂任务处理能力
    TOOL = "tool"        # 工具类型：原子操作能力
    MCP = "mcp"          # MCP类型：外部服务集成能力


class CapabilityLevel(Enum):
    """
    能力级别枚举
    
    定义能力的复杂程度层级
    """
    ATOMIC = "atomic"         # 原子能力：不可再分的基础能力
    COMPOSITE = "composite"   # 复合能力：组合多个原子能力
    WORKFLOW = "workflow"     # 工作流能力：包含复杂流程控制


class ExecutionStatus(Enum):
    """
    执行状态枚举
    
    定义能力执行的各种状态
    """
    PENDING = "pending"           # 等待执行
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 执行完成
    FAILED = "failed"             # 执行失败
    CANCELLED = "cancelled"       # 已取消
    TIMEOUT = "timeout"           # 执行超时
    RETRYING = "retrying"         # 重试中


@dataclass
class CapabilityMetadata:
    """
    能力元数据
    
    描述能力的基本信息和属性
    
    Attributes:
        name: 能力唯一标识名称
        display_name: 显示名称
        description: 能力描述
        capability_type: 能力类型
        level: 能力级别
        category: 能力分类
        tags: 能力标签列表
        input_schema: 输入参数JSON Schema
        output_schema: 输出结果JSON Schema
        dependencies: 依赖的其他能力名称列表
        timeout_seconds: 执行超时时间（秒）
        max_retries: 最大重试次数
        version: 能力版本
        author: 作者
        created_at: 创建时间
        updated_at: 更新时间
    """
    name: str
    display_name: str
    description: str = ""
    capability_type: CapabilityType = CapabilityType.SKILL
    level: CapabilityLevel = CapabilityLevel.ATOMIC
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 30
    max_retries: int = 3
    version: str = "1.0.0"
    author: str = "system"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ExecutionContext:
    """
    执行上下文
    
    传递执行时的上下文信息
    
    Attributes:
        user_id: 用户ID
        agent_id: 智能体ID
        conversation_id: 对话ID
        session_id: 会话ID
        context_data: 额外的上下文数据
        scene: 场景标识
    """
    user_id: Optional[int] = None
    agent_id: Optional[int] = None
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    scene: Optional[str] = None


@dataclass
class CapabilityResult:
    """
    能力执行结果
    
    封装能力执行的返回结果
    
    Attributes:
        success: 是否执行成功
        output: 执行输出
        error: 错误信息（失败时）
        artifacts: 生成的产物列表
        execution_time_ms: 执行耗时（毫秒）
        metadata: 额外元数据
    """
    success: bool
    output: Any = None
    error: Optional[str] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """
    验证结果
    
    输入数据验证的返回结果
    
    Attributes:
        valid: 是否验证通过
        error: 错误信息（验证失败时）
        errors: 详细错误列表
    """
    valid: bool
    error: Optional[str] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class CapabilityMatch:
    """
    能力匹配结果
    
    能力发现时的匹配信息
    
    Attributes:
        capability_name: 能力名称
        score: 匹配分数（0-1）
        match_type: 匹配类型（semantic/tag/history/scene）
        reason: 匹配理由说明
    """
    capability_name: str
    score: float
    match_type: str
    reason: str = ""


@dataclass
class TaskStep:
    """
    任务步骤
    
    任务规划中的单个步骤
    
    Attributes:
        id: 步骤唯一标识
        name: 步骤名称
        description: 步骤描述
        dependencies: 依赖的步骤ID列表
        estimated_time: 估计执行时间（秒）
        required_capabilities: 需要的能力列表
        input_requirements: 输入要求
        output_productions: 输出产物
        can_parallel: 是否可以并行执行
        candidate_capabilities: 候选能力列表
    """
    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_time: int = 30
    required_capabilities: List[str] = field(default_factory=list)
    input_requirements: List[str] = field(default_factory=list)
    output_productions: List[str] = field(default_factory=list)
    can_parallel: bool = False
    candidate_capabilities: List[CapabilityMatch] = field(default_factory=list)


@dataclass
class TaskPlan:
    """
    任务计划
    
    完整的任务执行计划
    
    Attributes:
        plan_id: 计划唯一标识
        original_input: 原始输入
        intent: 识别到的意图
        steps: 任务步骤列表
        estimated_total_time: 估计总执行时间（秒）
        complexity_level: 复杂度级别
    """
    plan_id: str
    original_input: str
    intent: Dict[str, Any]
    steps: List[TaskStep]
    estimated_total_time: int = 0
    complexity_level: str = "medium"


@dataclass
class ExecutionStep:
    """
    执行步骤
    
    记录实际执行时的步骤信息
    
    Attributes:
        step_id: 步骤ID
        capability_name: 执行的能力名称
        input_data: 输入数据
        output_data: 输出数据
        status: 执行状态
        start_time: 开始时间
        end_time: 结束时间
        error_message: 错误信息
        retry_count: 重试次数
    """
    step_id: str
    capability_name: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Any = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class OrchestrationResult:
    """
    编排结果
    
    智能编排的完整结果
    
    Attributes:
        success: 是否成功
        result: 最终结果
        execution_plan: 执行计划详情
        used_capabilities: 使用的能力列表
        execution_steps: 执行步骤详情
        execution_time_ms: 总执行时间（毫秒）
        error: 错误信息
    """
    success: bool
    result: Any = None
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    used_capabilities: List[str] = field(default_factory=list)
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    execution_time_ms: int = 0
    error: Optional[str] = None


@dataclass
class Intent:
    """
    意图
    
    用户意图的完整描述
    
    Attributes:
        category: 意图主分类
        sub_category: 意图子分类
        confidence: 置信度（0-1）
        entities: 提取的实体
        raw_text: 原始文本
        method: 识别方法
    """
    category: str
    sub_category: Optional[str] = None
    confidence: float = 0.0
    entities: List[Dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""
    method: str = ""


@dataclass
class ExecutionStats:
    """
    执行统计
    
    能力执行的统计数据
    
    Attributes:
        total_calls: 总调用次数
        successful_calls: 成功次数
        failed_calls: 失败次数
        total_execution_time_ms: 总执行时间（毫秒）
        average_execution_time_ms: 平均执行时间（毫秒）
        last_execution_time: 最后执行时间
        success_rate: 成功率
    """
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time_ms: int = 0
    average_execution_time_ms: float = 0.0
    last_execution_time: Optional[datetime] = None
    success_rate: float = 1.0


# 类型别名
CapabilityInput = Dict[str, Any]
CapabilityOutput = Any
ContextData = Dict[str, Any]
