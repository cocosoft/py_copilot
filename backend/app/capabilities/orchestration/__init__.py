"""
智能编排引擎模块

本模块提供Agent的智能编排能力，包括：
- 意图理解：识别用户意图和提取参数
- 任务规划：将意图分解为可执行的任务序列
- 编排执行：执行编排计划并管理任务依赖
- 上下文管理：维护对话和任务上下文
"""

from app.capabilities.orchestration.intent_understanding import (
    IntentUnderstanding,
    IntentResult,
    IntentType
)

from app.capabilities.orchestration.task_planner import (
    TaskPlanner,
    TaskPlan,
    TaskNode,
    DependencyType
)

from app.capabilities.orchestration.orchestrator import (
    Orchestrator,
    OrchestrationResult,
    OrchestrationStatus
)

from app.capabilities.orchestration.context_manager import (
    ContextManager,
    ConversationContext,
    TaskContext
)

__all__ = [
    # 意图理解
    'IntentUnderstanding',
    'IntentResult',
    'IntentType',
    # 任务规划
    'TaskPlanner',
    'TaskPlan',
    'TaskNode',
    'DependencyType',
    # 编排执行
    'Orchestrator',
    'OrchestrationResult',
    'OrchestrationStatus',
    # 上下文管理
    'ContextManager',
    'ConversationContext',
    'TaskContext',
]
