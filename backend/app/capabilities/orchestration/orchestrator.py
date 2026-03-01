"""
编排执行器

本模块负责任务计划的执行和协调
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

from app.capabilities.center.unified_center import UnifiedCapabilityCenter
from app.capabilities.center.execution_service import ExecutionService, ExecutionMode
from app.capabilities.orchestration.task_planner import TaskPlan, TaskNode, TaskStatus
from app.capabilities.types import CapabilityResult, ExecutionContext

logger = logging.getLogger(__name__)


class OrchestrationStatus(Enum):
    """编排状态"""
    IDLE = "idle"               # 空闲
    RUNNING = "running"         # 执行中
    PAUSED = "paused"          # 暂停
    COMPLETED = "completed"     # 完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 取消


@dataclass
class OrchestrationResult:
    """
    编排执行结果

    Attributes:
        success: 是否成功
        plan_id: 计划ID
        status: 最终状态
        task_results: 任务结果
        total_execution_time_ms: 总执行时间
        error: 错误信息
        output: 最终输出
    """
    success: bool
    plan_id: str
    status: OrchestrationStatus
    task_results: Dict[str, CapabilityResult] = field(default_factory=dict)
    total_execution_time_ms: int = 0
    error: Optional[str] = None
    output: Any = None


class Orchestrator:
    """
    编排执行器

    负责任务计划的执行、协调和监控。
    支持顺序执行、并行执行、错误处理和状态管理。

    Attributes:
        _center: 统一能力中心
        _execution_service: 执行服务
        _current_plan: 当前执行的计划
        _status: 编排器状态
        _event_handlers: 事件处理器
        _max_parallel: 最大并行数
    """

    def __init__(self,
                 center: UnifiedCapabilityCenter,
                 max_parallel: int = 5):
        """
        初始化编排执行器

        Args:
            center: 统一能力中心
            max_parallel: 最大并行任务数
        """
        self._center = center
        self._execution_service = ExecutionService(center, max_parallel=max_parallel)
        self._current_plan: Optional[TaskPlan] = None
        self._status = OrchestrationStatus.IDLE
        self._event_handlers: Dict[str, List[Callable]] = {
            'task_started': [],
            'task_completed': [],
            'task_failed': [],
            'plan_completed': [],
            'plan_failed': [],
        }
        self._max_parallel = max_parallel
        self._cancelled = False

        logger.info(f"编排执行器已创建，最大并行数: {max_parallel}")

    async def execute(self,
                     plan: TaskPlan,
                     context: Optional[ExecutionContext] = None) -> OrchestrationResult:
        """
        执行任务计划

        Args:
            plan: 任务计划
            context: 执行上下文

        Returns:
            OrchestrationResult: 执行结果
        """
        if self._status == OrchestrationStatus.RUNNING:
            return OrchestrationResult(
                success=False,
                plan_id=plan.id,
                status=OrchestrationStatus.FAILED,
                error="编排器正在执行其他计划"
            )

        self._current_plan = plan
        self._status = OrchestrationStatus.RUNNING
        self._cancelled = False
        plan.status = TaskStatus.RUNNING
        plan.started_at = datetime.now()

        logger.info(f"开始执行任务计划: {plan.id}, 任务数: {len(plan.tasks)}")

        start_time = datetime.now()
        task_results: Dict[str, CapabilityResult] = {}

        try:
            # 按并行组执行
            for group_idx, task_group in enumerate(plan.parallel_groups):
                if self._cancelled:
                    logger.info("计划执行已取消")
                    break

                logger.debug(f"执行并行组 {group_idx+1}/{len(plan.parallel_groups)}: {task_group}")

                # 执行当前组的所有任务
                group_results = await self._execute_task_group(
                    plan, task_group, context, task_results
                )
                task_results.update(group_results)

                # 检查是否有失败
                if any(not r.success for r in group_results.values()):
                    # 检查是否应该停止
                    if not await self._should_continue_on_failure(plan, group_results):
                        logger.warning("任务失败，停止执行")
                        break

            # 计算执行时间
            end_time = datetime.now()
            total_time = int((end_time - start_time).total_seconds() * 1000)

            # 确定最终状态
            if self._cancelled:
                final_status = OrchestrationStatus.CANCELLED
                success = False
            elif plan.has_failed():
                final_status = OrchestrationStatus.FAILED
                success = False
            elif plan.is_completed():
                final_status = OrchestrationStatus.COMPLETED
                success = True
            else:
                final_status = OrchestrationStatus.FAILED
                success = False

            plan.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            plan.completed_at = end_time
            self._status = final_status

            # 获取最终输出
            final_output = self._get_final_output(plan, task_results)

            result = OrchestrationResult(
                success=success,
                plan_id=plan.id,
                status=final_status,
                task_results=task_results,
                total_execution_time_ms=total_time,
                output=final_output
            )

            # 触发事件
            if success:
                self._emit_event('plan_completed', {'plan': plan, 'result': result})
            else:
                self._emit_event('plan_failed', {'plan': plan, 'result': result})

            logger.info(f"任务计划执行完成: {plan.id}, 状态: {final_status.value}")

            return result

        except Exception as e:
            logger.error(f"执行计划时出错: {e}", exc_info=True)
            self._status = OrchestrationStatus.FAILED
            plan.status = TaskStatus.FAILED

            return OrchestrationResult(
                success=False,
                plan_id=plan.id,
                status=OrchestrationStatus.FAILED,
                task_results=task_results,
                error=str(e)
            )

        finally:
            self._current_plan = None
            if self._status == OrchestrationStatus.RUNNING:
                self._status = OrchestrationStatus.IDLE

    async def _execute_task_group(self,
                                  plan: TaskPlan,
                                  task_ids: List[str],
                                  context: Optional[ExecutionContext],
                                  previous_results: Dict[str, CapabilityResult]) -> Dict[str, CapabilityResult]:
        """
        执行一组任务

        Args:
            plan: 任务计划
            task_ids: 任务ID列表
            context: 执行上下文
            previous_results: 之前任务的结果

        Returns:
            Dict[str, CapabilityResult]: 任务结果
        """
        results = {}

        # 准备任务执行
        tasks_to_run = []
        for task_id in task_ids:
            task = plan.tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                # 准备参数（合并依赖任务的输出）
                parameters = self._prepare_task_parameters(task, previous_results)
                tasks_to_run.append((task, parameters))

        if not tasks_to_run:
            return results

        # 并行执行
        async def execute_single(task: TaskNode, parameters: Dict[str, Any]) -> tuple:
            result = await self._execute_single_task(task, parameters, context)
            return task.id, result

        # 使用 gather 并行执行
        coroutines = [execute_single(task, params) for task, params in tasks_to_run]
        group_results = await asyncio.gather(*coroutines, return_exceptions=True)

        for item in group_results:
            if isinstance(item, Exception):
                logger.error(f"任务执行异常: {item}")
            else:
                task_id, result = item
                results[task_id] = result

        return results

    async def _execute_single_task(self,
                                   task: TaskNode,
                                   parameters: Dict[str, Any],
                                   context: Optional[ExecutionContext]) -> CapabilityResult:
        """
        执行单个任务

        Args:
            task: 任务节点
            parameters: 任务参数
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        self._emit_event('task_started', {'task': task})

        try:
            logger.debug(f"执行任务: {task.name}")

            # 使用执行服务执行任务
            result = await self._execution_service.execute_single(
                capability_name=task.capability_name,
                input_data=parameters,
                context=context,
                timeout=60  # 默认60秒超时
            )

            task.execution_time_ms = result.execution_time_ms or 0

            if result.success:
                task.status = TaskStatus.COMPLETED
                task.output = result.output
                self._emit_event('task_completed', {'task': task, 'result': result})
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error
                task.retry_count += 1

                # 尝试重试
                if task.can_retry():
                    logger.info(f"任务失败，尝试重试: {task.name} (第{task.retry_count}次)")
                    await asyncio.sleep(1)  # 简单延迟
                    return await self._execute_single_task(task, parameters, context)

                self._emit_event('task_failed', {'task': task, 'result': result})

            return result

        except Exception as e:
            logger.error(f"执行任务时出错: {task.name}, error={e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.retry_count += 1

            self._emit_event('task_failed', {'task': task, 'error': str(e)})

            return CapabilityResult(success=False, error=str(e))

    def _prepare_task_parameters(self,
                                 task: TaskNode,
                                 previous_results: Dict[str, CapabilityResult]) -> Dict[str, Any]:
        """
        准备任务参数

        Args:
            task: 任务节点
            previous_results: 之前任务的结果

        Returns:
            Dict[str, Any]: 合并后的参数
        """
        parameters = task.parameters.copy()

        # 从依赖任务的输出中提取参数
        for dep_id, dep_type in task.dependencies:
            if dep_id in previous_results:
                dep_result = previous_results[dep_id]
                if dep_result.success and dep_result.output:
                    # 将依赖任务的输出作为参数
                    param_name = f"output_from_{dep_id}"
                    parameters[param_name] = dep_result.output

        return parameters

    async def _should_continue_on_failure(self,
                                         plan: TaskPlan,
                                         group_results: Dict[str, CapabilityResult]) -> bool:
        """
        检查失败时是否应该继续

        Args:
            plan: 任务计划
            group_results: 当前组的结果

        Returns:
            bool: 是否继续
        """
        # 简化实现：如果有失败就停止
        # 实际应用中可以根据任务的重要性和依赖关系决定
        return False

    def _get_final_output(self,
                         plan: TaskPlan,
                         task_results: Dict[str, CapabilityResult]) -> Any:
        """
        获取最终输出

        Args:
            plan: 任务计划
            task_results: 任务结果

        Returns:
            Any: 最终输出
        """
        # 返回最后一个完成的任务的输出
        for task_id in reversed(list(plan.tasks.keys())):
            if task_id in task_results:
                result = task_results[task_id]
                if result.success:
                    return result.output

        return None

    def on(self, event: str, handler: Callable):
        """
        注册事件处理器

        Args:
            event: 事件名称
            handler: 处理函数
        """
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)

    def off(self, event: str, handler: Callable):
        """
        注销事件处理器

        Args:
            event: 事件名称
            handler: 处理函数
        """
        if event in self._event_handlers:
            if handler in self._event_handlers[event]:
                self._event_handlers[event].remove(handler)

    def _emit_event(self, event: str, data: Dict[str, Any]):
        """
        触发事件

        Args:
            event: 事件名称
            data: 事件数据
        """
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {event}, error={e}")

    def pause(self):
        """暂停执行"""
        if self._status == OrchestrationStatus.RUNNING:
            self._status = OrchestrationStatus.PAUSED
            logger.info("编排执行已暂停")

    def resume(self):
        """恢复执行"""
        if self._status == OrchestrationStatus.PAUSED:
            self._status = OrchestrationStatus.RUNNING
            logger.info("编排执行已恢复")

    def cancel(self):
        """取消执行"""
        self._cancelled = True
        self._status = OrchestrationStatus.CANCELLED
        logger.info("编排执行已取消")

    def get_status(self) -> OrchestrationStatus:
        """获取当前状态"""
        return self._status

    def get_progress(self) -> Optional[Dict[str, Any]]:
        """获取执行进度"""
        if self._current_plan:
            return self._current_plan.get_progress()
        return None

    def get_current_plan(self) -> Optional[TaskPlan]:
        """获取当前计划"""
        return self._current_plan
