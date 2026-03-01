"""
任务规划引擎

本模块提供任务规划和分解功能
"""

import logging
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

from app.capabilities.orchestration.intent_understanding import IntentResult, IntentType
from app.capabilities.center.unified_center import UnifiedCapabilityCenter

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """依赖类型"""
    SEQUENTIAL = "sequential"   # 顺序依赖（前一个完成才能执行）
    DATA = "data"              # 数据依赖（需要前一个的输出）
    CONDITION = "condition"    # 条件依赖
    RESOURCE = "resource"      # 资源依赖


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"         # 待执行
    RUNNING = "running"         # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 失败
    SKIPPED = "skipped"        # 已跳过
    CANCELLED = "cancelled"    # 已取消


@dataclass
class TaskNode:
    """
    任务节点

    Attributes:
        id: 任务ID
        name: 任务名称
        capability_name: 能力名称
        parameters: 任务参数
        dependencies: 依赖列表 [(task_id, dependency_type)]
        status: 任务状态
        output: 任务输出
        error: 错误信息
        execution_time_ms: 执行时间
        retry_count: 重试次数
        max_retries: 最大重试次数
        condition: 执行条件（用于条件任务）
    """
    id: str
    name: str
    capability_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[tuple] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    retry_count: int = 0
    max_retries: int = 3
    condition: Optional[Callable] = None

    def is_ready(self) -> bool:
        """检查任务是否准备好执行"""
        if self.status != TaskStatus.PENDING:
            return False

        # 检查条件
        if self.condition and not self.condition():
            return False

        return True

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries


@dataclass
class TaskPlan:
    """
    任务计划

    Attributes:
        id: 计划ID
        intent_result: 意图结果
        tasks: 任务节点列表
        created_at: 创建时间
        started_at: 开始时间
        completed_at: 完成时间
        status: 计划状态
        parallel_groups: 可并行执行的任务组
    """
    id: str
    intent_result: IntentResult
    tasks: Dict[str, TaskNode] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    parallel_groups: List[List[str]] = field(default_factory=list)

    def get_ready_tasks(self) -> List[TaskNode]:
        """获取准备好的任务"""
        ready = []
        for task in self.tasks.values():
            if task.is_ready():
                # 检查依赖是否完成
                deps_satisfied = all(
                    self.tasks.get(dep_id, TaskNode("", "", "")).status == TaskStatus.COMPLETED
                    for dep_id, _ in task.dependencies
                )
                if deps_satisfied:
                    ready.append(task)
        return ready

    def get_task_by_id(self, task_id: str) -> Optional[TaskNode]:
        """根据ID获取任务"""
        return self.tasks.get(task_id)

    def is_completed(self) -> bool:
        """检查计划是否完成"""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED, TaskStatus.CANCELLED]
            for task in self.tasks.values()
        )

    def has_failed(self) -> bool:
        """检查是否有失败任务"""
        return any(task.status == TaskStatus.FAILED for task in self.tasks.values())

    def get_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "percentage": (completed / total * 100) if total > 0 else 0
        }


class TaskPlanner:
    """
    任务规划器

    负责将意图结果转换为可执行的任务计划。
    支持任务分解、依赖分析和并行优化。

    Attributes:
        _center: 统一能力中心
        _plan_id_counter: 计划ID计数器
    """

    def __init__(self, center: UnifiedCapabilityCenter):
        """
        初始化任务规划器

        Args:
            center: 统一能力中心
        """
        self._center = center
        self._plan_id_counter = 0

        logger.info("任务规划器已创建")

    async def create_plan(self, intent_result: IntentResult) -> TaskPlan:
        """
        创建任务计划

        Args:
            intent_result: 意图理解结果

        Returns:
            TaskPlan: 任务计划
        """
        self._plan_id_counter += 1
        plan_id = f"plan_{self._plan_id_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        logger.info(f"创建任务计划: {plan_id}, 意图类型: {intent_result.intent_type.value}")

        plan = TaskPlan(
            id=plan_id,
            intent_result=intent_result
        )

        # 根据意图类型生成任务
        if intent_result.intent_type == IntentType.SINGLE:
            await self._plan_single_task(plan, intent_result)
        elif intent_result.intent_type == IntentType.SEQUENTIAL:
            await self._plan_sequential_tasks(plan, intent_result)
        elif intent_result.intent_type == IntentType.PARALLEL:
            await self._plan_parallel_tasks(plan, intent_result)
        elif intent_result.intent_type == IntentType.CONDITIONAL:
            await self._plan_conditional_tasks(plan, intent_result)
        elif intent_result.intent_type == IntentType.QUERY:
            await self._plan_query_task(plan, intent_result)
        else:
            # 默认处理
            await self._plan_single_task(plan, intent_result)

        # 分析并行组
        plan.parallel_groups = self._analyze_parallel_groups(plan)

        logger.info(f"任务计划创建完成: {plan_id}, 任务数: {len(plan.tasks)}")

        return plan

    async def _plan_single_task(self, plan: TaskPlan, intent_result: IntentResult):
        """规划单任务"""
        if not intent_result.capabilities:
            logger.warning("没有匹配的能力")
            return

        capability_name = intent_result.capabilities[0]

        task = TaskNode(
            id=f"task_{plan.id}_1",
            name=f"执行 {capability_name}",
            capability_name=capability_name,
            parameters=intent_result.parameters.copy()
        )

        plan.tasks[task.id] = task

    async def _plan_sequential_tasks(self, plan: TaskPlan, intent_result: IntentResult):
        """规划顺序任务"""
        capabilities = intent_result.capabilities

        prev_task_id = None
        for i, capability_name in enumerate(capabilities):
            task = TaskNode(
                id=f"task_{plan.id}_{i+1}",
                name=f"步骤 {i+1}: {capability_name}",
                capability_name=capability_name,
                parameters=intent_result.parameters.copy()
            )

            # 添加顺序依赖
            if prev_task_id:
                task.dependencies.append((prev_task_id, DependencyType.SEQUENTIAL))

            plan.tasks[task.id] = task
            prev_task_id = task.id

    async def _plan_parallel_tasks(self, plan: TaskPlan, intent_result: IntentResult):
        """规划并行任务"""
        capabilities = intent_result.capabilities

        for i, capability_name in enumerate(capabilities):
            task = TaskNode(
                id=f"task_{plan.id}_{i+1}",
                name=f"并行任务 {i+1}: {capability_name}",
                capability_name=capability_name,
                parameters=intent_result.parameters.copy()
            )

            plan.tasks[task.id] = task

    async def _plan_conditional_tasks(self, plan: TaskPlan, intent_result: IntentResult):
        """规划条件任务"""
        # 简化实现：创建条件任务和默认任务
        if len(intent_result.capabilities) >= 2:
            # 条件为真时执行的任务
            true_task = TaskNode(
                id=f"task_{plan.id}_true",
                name=f"条件为真: {intent_result.capabilities[0]}",
                capability_name=intent_result.capabilities[0],
                parameters=intent_result.parameters.copy()
            )

            # 条件为假时执行的任务
            false_task = TaskNode(
                id=f"task_{plan.id}_false",
                name=f"条件为假: {intent_result.capabilities[1]}",
                capability_name=intent_result.capabilities[1],
                parameters=intent_result.parameters.copy()
            )

            plan.tasks[true_task.id] = true_task
            plan.tasks[false_task.id] = false_task
        else:
            await self._plan_single_task(plan, intent_result)

    async def _plan_query_task(self, plan: TaskPlan, intent_result: IntentResult):
        """规划查询任务"""
        # 查询任务通常是单任务
        await self._plan_single_task(plan, intent_result)

    def _analyze_parallel_groups(self, plan: TaskPlan) -> List[List[str]]:
        """
        分析可并行执行的任务组

        Args:
            plan: 任务计划

        Returns:
            List[List[str]]: 并行任务组（每组内的任务可以并行执行）
        """
        if not plan.tasks:
            return []

        groups = []
        remaining = set(plan.tasks.keys())
        completed = set()

        while remaining:
            # 找出当前可以执行的任务（依赖已完成）
            current_group = []
            for task_id in list(remaining):
                task = plan.tasks[task_id]
                deps_satisfied = all(
                    dep_id in completed
                    for dep_id, _ in task.dependencies
                )
                if deps_satisfied:
                    current_group.append(task_id)

            if not current_group:
                # 有循环依赖或无法执行的任务
                logger.warning(f"无法继续分析并行组，剩余任务: {remaining}")
                break

            groups.append(current_group)
            completed.update(current_group)
            remaining -= set(current_group)

        return groups

    def optimize_plan(self, plan: TaskPlan) -> TaskPlan:
        """
        优化任务计划

        Args:
            plan: 原始计划

        Returns:
            TaskPlan: 优化后的计划
        """
        logger.info(f"优化任务计划: {plan.id}")

        # 1. 合并可以合并的任务
        plan = self._merge_tasks(plan)

        # 2. 重新分析并行组
        plan.parallel_groups = self._analyze_parallel_groups(plan)

        # 3. 检查能力可用性
        plan = self._validate_capabilities(plan)

        return plan

    def _merge_tasks(self, plan: TaskPlan) -> TaskPlan:
        """合并可合并的任务"""
        # 简化实现：检查连续相同能力的任务
        # 实际应用中可能需要更复杂的逻辑
        return plan

    def _validate_capabilities(self, plan: TaskPlan) -> TaskPlan:
        """验证能力可用性"""
        for task in plan.tasks.values():
            if not self._center.has_capability(task.capability_name):
                logger.warning(f"能力不可用: {task.capability_name}")
                task.status = TaskStatus.FAILED
                task.error = f"能力不可用: {task.capability_name}"

        return plan

    def add_task(self,
                 plan: TaskPlan,
                 name: str,
                 capability_name: str,
                 parameters: Optional[Dict[str, Any]] = None,
                 dependencies: Optional[List[tuple]] = None) -> TaskNode:
        """
        向计划中添加任务

        Args:
            plan: 任务计划
            name: 任务名称
            capability_name: 能力名称
            parameters: 任务参数
            dependencies: 依赖列表

        Returns:
            TaskNode: 创建的任务节点
        """
        task_id = f"task_{plan.id}_{len(plan.tasks)+1}"

        task = TaskNode(
            id=task_id,
            name=name,
            capability_name=capability_name,
            parameters=parameters or {},
            dependencies=dependencies or []
        )

        plan.tasks[task_id] = task

        # 重新分析并行组
        plan.parallel_groups = self._analyze_parallel_groups(plan)

        return task

    def remove_task(self, plan: TaskPlan, task_id: str) -> bool:
        """
        从计划中移除任务

        Args:
            plan: 任务计划
            task_id: 任务ID

        Returns:
            bool: 是否成功移除
        """
        if task_id not in plan.tasks:
            return False

        # 检查是否有其他任务依赖此任务
        for task in plan.tasks.values():
            for dep_id, _ in task.dependencies:
                if dep_id == task_id:
                    logger.warning(f"无法移除任务 {task_id}，有其他任务依赖它")
                    return False

        del plan.tasks[task_id]

        # 重新分析并行组
        plan.parallel_groups = self._analyze_parallel_groups(plan)

        return True

    def get_plan_summary(self, plan: TaskPlan) -> Dict[str, Any]:
        """
        获取计划摘要

        Args:
            plan: 任务计划

        Returns:
            Dict[str, Any]: 计划摘要
        """
        return {
            "plan_id": plan.id,
            "intent_type": plan.intent_result.intent_type.value,
            "total_tasks": len(plan.tasks),
            "parallel_groups": len(plan.parallel_groups),
            "estimated_parallel_steps": len(plan.parallel_groups),
            "capabilities": list(set(
                task.capability_name for task in plan.tasks.values()
            )),
            "created_at": plan.created_at.isoformat(),
            "status": plan.status.value
        }
