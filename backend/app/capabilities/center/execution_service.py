"""
能力执行服务

本模块提供能力执行的高级功能，包括批量执行、管道执行、条件执行等
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityResult,
    ExecutionContext,
    ExecutionStep,
    TaskPlan,
    TaskStep
)
from app.capabilities.center.unified_center import UnifiedCapabilityCenter

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    PIPELINE = "pipeline"      # 管道执行
    CONDITIONAL = "conditional"  # 条件执行


@dataclass
class ExecutionRequest:
    """执行请求"""
    capability_name: str
    input_data: Dict[str, Any]
    condition: Optional[Callable] = None
    timeout: Optional[int] = None


@dataclass
class BatchExecutionResult:
    """批量执行结果"""
    results: List[CapabilityResult] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    total_execution_time_ms: int = 0
    errors: List[str] = field(default_factory=list)


class ExecutionService:
    """
    能力执行服务

    提供高级执行功能：
    - 批量执行
    - 管道执行
    - 条件执行
    - 执行计划执行
    - 执行监控

    Attributes:
        _center: 统一能力中心
        _max_parallel: 最大并行数
        _default_timeout: 默认超时
    """

    def __init__(self,
                 center: UnifiedCapabilityCenter,
                 max_parallel: int = 5,
                 default_timeout: int = 60):
        """
        初始化执行服务

        Args:
            center: 统一能力中心
            max_parallel: 最大并行执行数
            default_timeout: 默认超时（秒）
        """
        self._center = center
        self._max_parallel = max_parallel
        self._default_timeout = default_timeout

        logger.info(f"执行服务已创建 (max_parallel={max_parallel})")

    async def execute_single(self,
                            capability_name: str,
                            input_data: Dict[str, Any],
                            context: Optional[ExecutionContext] = None,
                            timeout: Optional[int] = None) -> CapabilityResult:
        """
        执行单个能力

        Args:
            capability_name: 能力名称
            input_data: 输入数据
            context: 执行上下文
            timeout: 超时时间（秒）

        Returns:
            CapabilityResult: 执行结果
        """
        if not context:
            context = ExecutionContext()

        timeout = timeout or self._default_timeout

        try:
            # 使用asyncio.wait_for添加超时控制
            result = await asyncio.wait_for(
                self._center.execute_capability(capability_name, input_data, context),
                timeout=timeout
            )
            return result

        except asyncio.TimeoutError:
            logger.error(f"能力执行超时: {capability_name}")
            return CapabilityResult(
                success=False,
                error=f"执行超时（{timeout}秒）"
            )

        except Exception as e:
            logger.error(f"能力执行异常: {capability_name}, error={e}")
            return CapabilityResult(
                success=False,
                error=f"执行异常: {str(e)}"
            )

    async def execute_batch(self,
                           requests: List[ExecutionRequest],
                           mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
                           context: Optional[ExecutionContext] = None) -> BatchExecutionResult:
        """
        批量执行能力

        Args:
            requests: 执行请求列表
            mode: 执行模式
            context: 执行上下文

        Returns:
            BatchExecutionResult: 批量执行结果
        """
        if not context:
            context = ExecutionContext()

        start_time = datetime.now()
        result = BatchExecutionResult()

        if mode == ExecutionMode.SEQUENTIAL:
            # 顺序执行
            for request in requests:
                if request.condition and not request.condition():
                    continue

                capability_result = await self.execute_single(
                    request.capability_name,
                    request.input_data,
                    context,
                    request.timeout
                )

                result.results.append(capability_result)

                if capability_result.success:
                    result.success_count += 1
                else:
                    result.failure_count += 1
                    if capability_result.error:
                        result.errors.append(capability_result.error)

        elif mode == ExecutionMode.PARALLEL:
            # 并行执行
            semaphore = asyncio.Semaphore(self._max_parallel)

            async def execute_with_limit(request: ExecutionRequest) -> CapabilityResult:
                async with semaphore:
                    if request.condition and not request.condition():
                        return CapabilityResult(success=True, output="条件不满足，跳过执行")

                    return await self.execute_single(
                        request.capability_name,
                        request.input_data,
                        context,
                        request.timeout
                    )

            # 并发执行所有请求
            tasks = [execute_with_limit(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for capability_result in results:
                if isinstance(capability_result, Exception):
                    result.results.append(CapabilityResult(
                        success=False,
                        error=str(capability_result)
                    ))
                    result.failure_count += 1
                    result.errors.append(str(capability_result))
                else:
                    result.results.append(capability_result)
                    if capability_result.success:
                        result.success_count += 1
                    else:
                        result.failure_count += 1
                        if capability_result.error:
                            result.errors.append(capability_result.error)

        result.total_execution_time_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000
        )

        return result

    async def execute_pipeline(self,
                              steps: List[ExecutionRequest],
                              initial_input: Dict[str, Any],
                              context: Optional[ExecutionContext] = None,
                              stop_on_error: bool = True) -> List[CapabilityResult]:
        """
        管道执行

        前一个步骤的输出作为后一个步骤的输入

        Args:
            steps: 执行步骤
            initial_input: 初始输入
            context: 执行上下文
            stop_on_error: 出错时是否停止

        Returns:
            List[CapabilityResult]: 执行结果列表
        """
        if not context:
            context = ExecutionContext()

        results = []
        current_input = initial_input.copy()

        for i, step in enumerate(steps):
            logger.info(f"执行管道步骤 {i+1}/{len(steps)}: {step.capability_name}")

            # 合并当前输入和步骤输入
            step_input = {**current_input, **step.input_data}

            result = await self.execute_single(
                step.capability_name,
                step_input,
                context,
                step.timeout
            )

            results.append(result)

            if not result.success:
                logger.error(f"管道步骤 {i+1} 失败: {result.error}")
                if stop_on_error:
                    break
            else:
                # 更新当前输入（如果输出是字典）
                if isinstance(result.output, dict):
                    current_input.update(result.output)
                elif result.output:
                    current_input['previous_output'] = result.output

        return results

    async def execute_conditional(self,
                                  condition: Callable[[], bool],
                                  true_request: ExecutionRequest,
                                  false_request: Optional[ExecutionRequest] = None,
                                  context: Optional[ExecutionContext] = None) -> CapabilityResult:
        """
        条件执行

        Args:
            condition: 条件函数
            true_request: 条件为真时执行的请求
            false_request: 条件为假时执行的请求
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        if not context:
            context = ExecutionContext()

        try:
            if condition():
                logger.info(f"条件为真，执行: {true_request.capability_name}")
                return await self.execute_single(
                    true_request.capability_name,
                    true_request.input_data,
                    context,
                    true_request.timeout
                )
            elif false_request:
                logger.info(f"条件为假，执行: {false_request.capability_name}")
                return await self.execute_single(
                    false_request.capability_name,
                    false_request.input_data,
                    context,
                    false_request.timeout
                )
            else:
                return CapabilityResult(
                    success=True,
                    output="条件为假，无执行请求"
                )

        except Exception as e:
            logger.error(f"条件执行异常: {e}")
            return CapabilityResult(
                success=False,
                error=f"条件执行异常: {str(e)}"
            )

    async def execute_plan(self,
                          plan: TaskPlan,
                          context: Optional[ExecutionContext] = None) -> Dict[str, CapabilityResult]:
        """
        执行任务计划

        Args:
            plan: 任务计划
            context: 执行上下文

        Returns:
            Dict[str, CapabilityResult]: 步骤执行结果
        """
        if not context:
            context = ExecutionContext()

        results = {}
        step_outputs = {}

        for step in plan.steps:
            logger.info(f"执行计划步骤: {step.name} ({step.capability_name})")

            # 准备输入（支持引用其他步骤的输出）
            step_input = step.input_data.copy()

            # 替换引用
            for key, value in step_input.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    ref_path = value[2:-1]  # 去掉 ${ 和 }
                    parts = ref_path.split(".")

                    if len(parts) >= 2:
                        ref_step = parts[0]
                        ref_field = parts[1]

                        if ref_step in step_outputs:
                            step_input[key] = step_outputs[ref_step].get(ref_field)

            # 执行步骤
            result = await self.execute_single(
                step.capability_name,
                step_input,
                context
            )

            results[step.id] = result

            if result.success:
                if isinstance(result.output, dict):
                    step_outputs[step.id] = result.output
                else:
                    step_outputs[step.id] = {"output": result.output}
            else:
                logger.error(f"步骤 {step.name} 失败: {result.error}")
                # 根据错误处理策略决定是否继续
                if plan.error_handling == "stop":
                    break

        return results

    async def execute_with_retry(self,
                                capability_name: str,
                                input_data: Dict[str, Any],
                                max_retries: int = 3,
                                retry_delay: float = 1.0,
                                context: Optional[ExecutionContext] = None) -> CapabilityResult:
        """
        带重试的执行

        Args:
            capability_name: 能力名称
            input_data: 输入数据
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        if not context:
            context = ExecutionContext()

        last_error = None

        for attempt in range(max_retries + 1):
            result = await self.execute_single(
                capability_name,
                input_data,
                context
            )

            if result.success:
                if attempt > 0:
                    logger.info(f"能力 {capability_name} 在第 {attempt + 1} 次尝试后成功")
                return result

            last_error = result.error

            if attempt < max_retries:
                logger.warning(
                    f"能力 {capability_name} 执行失败（尝试 {attempt + 1}/{max_retries + 1}），"
                    f"{retry_delay}秒后重试..."
                )
                await asyncio.sleep(retry_delay)

        return CapabilityResult(
            success=False,
            error=f"重试{max_retries}次后仍然失败: {last_error}"
        )

    def set_max_parallel(self, max_parallel: int):
        """
        设置最大并行数

        Args:
            max_parallel: 最大并行数
        """
        self._max_parallel = max_parallel
        logger.info(f"最大并行数已设置为: {max_parallel}")

    def set_default_timeout(self, timeout: int):
        """
        设置默认超时

        Args:
            timeout: 超时时间（秒）
        """
        self._default_timeout = timeout
        logger.info(f"默认超时已设置为: {timeout}秒")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "max_parallel": self._max_parallel,
            "default_timeout": self._default_timeout,
            "center_status": self._center.get_status().value
        }
