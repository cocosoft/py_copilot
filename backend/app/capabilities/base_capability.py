"""
能力抽象基类

本模块定义了所有能力的抽象基类，提供统一的能力接口
"""

import uuid
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    ExecutionStats,
    ExecutionStatus
)
from app.capabilities.exceptions import (
    CapabilityExecutionException,
    ValidationException,
    TimeoutException,
    RetryExhaustedException
)

logger = logging.getLogger(__name__)


class BaseCapability(ABC):
    """
    能力抽象基类

    所有具体能力必须继承此类，提供统一的能力接口、执行监控、统计收集等功能。

    使用模板方法模式，子类只需实现 _do_execute 方法即可。

    Attributes:
        metadata: 能力元数据
        _capability_id: 能力实例唯一标识
        _execution_stats: 执行统计数据
        _is_initialized: 是否已初始化
    """

    def __init__(self, metadata: CapabilityMetadata):
        """
        初始化能力

        Args:
            metadata: 能力元数据
        """
        self.metadata = metadata
        self._capability_id = str(uuid.uuid4())
        self._execution_stats = ExecutionStats()
        self._is_initialized = False

    @property
    def capability_id(self) -> str:
        """获取能力实例ID"""
        return self._capability_id

    @property
    def name(self) -> str:
        """获取能力名称"""
        return self.metadata.name

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return self.metadata.display_name

    @property
    def execution_stats(self) -> ExecutionStats:
        """获取执行统计"""
        return self._execution_stats

    async def initialize(self) -> bool:
        """
        初始化能力

        子类可以重写此方法进行自定义初始化

        Returns:
            bool: 初始化是否成功
        """
        self._is_initialized = True
        logger.info(f"能力 '{self.name}' 初始化完成")
        return True

    async def cleanup(self):
        """
        清理资源

        子类可以重写此方法进行资源清理
        """
        self._is_initialized = False
        logger.info(f"能力 '{self.name}' 资源已清理")

    async def execute(self,
                     input_data: Dict[str, Any],
                     context: ExecutionContext) -> CapabilityResult:
        """
        执行能力（模板方法）

        完整的执行流程：
        1. 检查初始化状态
        2. 验证输入数据
        3. 前置处理
        4. 执行（带重试和超时）
        5. 后置处理
        6. 更新统计

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        start_time = time.time()

        try:
            # 1. 检查初始化状态
            if not self._is_initialized:
                await self.initialize()

            # 2. 验证输入数据
            validation = await self.validate_input(input_data)
            if not validation.valid:
                raise ValidationException(validation.errors)

            # 3. 前置处理
            processed_input = await self._pre_process(input_data, context)

            # 4. 执行（带重试）
            result = await self._execute_with_retry(processed_input, context)

            # 5. 后置处理
            final_result = await self._post_process(result, context)

            # 6. 更新统计
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._update_stats(True, execution_time_ms)

            logger.info(f"能力 '{self.name}' 执行成功，耗时 {execution_time_ms}ms")

            return final_result

        except ValidationException:
            raise

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._update_stats(False, execution_time_ms)

            error_msg = f"能力 '{self.name}' 执行异常: {str(e)}"
            logger.error(error_msg, exc_info=True)

            raise CapabilityExecutionException(self.name, str(e))

    async def _execute_with_retry(self,
                                  input_data: Dict[str, Any],
                                  context: ExecutionContext) -> CapabilityResult:
        """
        带重试的执行

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果

        Raises:
            RetryExhaustedException: 重试耗尽仍失败
        """
        max_retries = self.metadata.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # 设置超时
                import asyncio
                result = await asyncio.wait_for(
                    self._do_execute(input_data, context),
                    timeout=self.metadata.timeout_seconds
                )
                return result

            except asyncio.TimeoutError:
                last_error = f"执行超时（{self.metadata.timeout_seconds}秒）"
                logger.warning(f"能力 '{self.name}' 第 {attempt + 1} 次尝试超时")

                if attempt < max_retries:
                    await asyncio.sleep(1 * (attempt + 1))  # 线性退避

            except Exception as e:
                last_error = str(e)
                logger.warning(f"能力 '{self.name}' 第 {attempt + 1} 次尝试失败: {e}")

                if attempt < max_retries:
                    await asyncio.sleep(1 * (attempt + 1))

        # 重试耗尽
        raise RetryExhaustedException(self.name, max_retries, last_error)

    @abstractmethod
    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """
        实际执行逻辑（子类必须实现）

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        pass

    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """
        验证输入数据

        子类可以重写此方法进行自定义验证

        Args:
            input_data: 输入数据

        Returns:
            ValidationResult: 验证结果
        """
        # 基础验证：检查必填字段
        if not self.metadata.input_schema:
            return ValidationResult(valid=True)

        required_fields = self.metadata.input_schema.get("required", [])
        errors = []

        for field in required_fields:
            if field not in input_data:
                errors.append(f"缺少必填字段: {field}")

        if errors:
            return ValidationResult(valid=False, errors=errors)

        return ValidationResult(valid=True)

    async def _pre_process(self,
                          input_data: Dict[str, Any],
                          context: ExecutionContext) -> Dict[str, Any]:
        """
        前置处理

        子类可以重写此方法进行输入预处理

        Args:
            input_data: 原始输入数据
            context: 执行上下文

        Returns:
            Dict[str, Any]: 处理后的输入数据
        """
        return input_data

    async def _post_process(self,
                           result: CapabilityResult,
                           context: ExecutionContext) -> CapabilityResult:
        """
        后置处理

        子类可以重写此方法进行结果后处理

        Args:
            result: 执行结果
            context: 执行上下文

        Returns:
            CapabilityResult: 处理后的结果
        """
        return result

    def _update_stats(self, success: bool, execution_time_ms: int):
        """
        更新执行统计

        Args:
            success: 是否成功
            execution_time_ms: 执行时间（毫秒）
        """
        stats = self._execution_stats
        stats.total_calls += 1
        stats.total_execution_time_ms += execution_time_ms
        stats.last_execution_time = datetime.now()

        if success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1

        # 计算平均时间和成功率
        stats.average_execution_time_ms = (
            stats.total_execution_time_ms / stats.total_calls
        )
        stats.success_rate = stats.successful_calls / stats.total_calls

    def get_capabilities(self) -> List[str]:
        """
        获取子能力列表

        复合能力可以重写此方法返回依赖的能力

        Returns:
            List[str]: 子能力名称列表
        """
        return self.metadata.dependencies

    def get_info(self) -> Dict[str, Any]:
        """
        获取能力信息

        Returns:
            Dict[str, Any]: 能力信息字典
        """
        return {
            "capability_id": self._capability_id,
            "name": self.metadata.name,
            "display_name": self.metadata.display_name,
            "description": self.metadata.description,
            "type": self.metadata.capability_type.value,
            "level": self.metadata.level.value,
            "category": self.metadata.category,
            "tags": self.metadata.tags,
            "version": self.metadata.version,
            "author": self.metadata.author,
            "timeout_seconds": self.metadata.timeout_seconds,
            "max_retries": self.metadata.max_retries,
            "dependencies": self.metadata.dependencies,
            "stats": {
                "total_calls": self._execution_stats.total_calls,
                "success_rate": round(self._execution_stats.success_rate, 4),
                "average_execution_time_ms": round(self._execution_stats.average_execution_time_ms, 2)
            }
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', type={self.metadata.capability_type.value})>"

    def __str__(self) -> str:
        return f"{self.display_name} ({self.name})"
