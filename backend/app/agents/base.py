"""
Agent基础类

本模块定义Agent的基础类和接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.capabilities.types import CapabilityMetadata, CapabilityResult

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent状态"""
    IDLE = "idle"           # 空闲
    RUNNING = "running"     # 运行中
    PAUSED = "paused"       # 暂停
    ERROR = "error"         # 错误
    STOPPED = "stopped"     # 已停止


class AgentPriority(Enum):
    """Agent优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentConfig:
    """
    Agent配置

    Attributes:
        name: Agent名称
        description: Agent描述
        version: 版本号
        author: 作者
        tags: 标签列表
        priority: 优先级
        max_retries: 最大重试次数
        timeout: 超时时间（秒）
        required_capabilities: 必需的能力列表
        optional_capabilities: 可选的能力列表
        metadata: 额外元数据
    """
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    priority: AgentPriority = AgentPriority.NORMAL
    max_retries: int = 3
    timeout: float = 30.0
    required_capabilities: List[str] = field(default_factory=list)
    optional_capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "priority": self.priority.value,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "required_capabilities": self.required_capabilities,
            "optional_capabilities": self.optional_capabilities,
            "metadata": self.metadata
        }


@dataclass
class AgentResult:
    """
    Agent执行结果

    Attributes:
        success: 是否成功
        output: 输出内容
        error: 错误信息
        execution_time_ms: 执行时间（毫秒）
        metadata: 元数据
    """
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata
        }


@dataclass
class AgentContext:
    """
    Agent执行上下文

    Attributes:
        session_id: 会话ID
        user_id: 用户ID
        conversation_id: 对话ID
        parameters: 执行参数
        history: 执行历史
        metadata: 元数据
    """
    session_id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Agent基础类

    所有Agent的基类，定义了Agent的基本接口和通用功能。

    Attributes:
        config: Agent配置
        _status: 当前状态
        _capabilities: 能力列表
        _event_handlers: 事件处理器
    """

    def __init__(self, config: AgentConfig):
        """
        初始化Agent

        Args:
            config: Agent配置
        """
        self.config = config
        self._status = AgentStatus.IDLE
        self._capabilities: List[CapabilityMetadata] = []
        self._event_handlers: Dict[str, List[Callable]] = {
            'started': [],
            'completed': [],
            'failed': [],
            'paused': [],
            'resumed': [],
        }

        logger.info(f"Agent '{config.name}' 已创建")

    @property
    def name(self) -> str:
        """获取Agent名称"""
        return self.config.name

    @property
    def status(self) -> AgentStatus:
        """获取当前状态"""
        return self._status

    @abstractmethod
    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """
        执行Agent

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            AgentResult: 执行结果
        """
        pass

    @abstractmethod
    def can_handle(self, input_data: Any) -> float:
        """
        判断是否能处理输入

        Args:
            input_data: 输入数据

        Returns:
            float: 置信度（0-1）
        """
        pass

    def validate_capabilities(self, available_capabilities: List[str]) -> bool:
        """
        验证必需能力是否可用

        Args:
            available_capabilities: 可用的能力列表

        Returns:
            bool: 是否满足要求
        """
        missing = set(self.config.required_capabilities) - set(available_capabilities)
        if missing:
            logger.warning(f"Agent '{self.name}' 缺少必需能力: {missing}")
            return False
        return True

    def on(self, event: str, handler: Callable):
        """
        注册事件处理器

        Args:
            event: 事件类型
            handler: 处理器函数
        """
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)

    def off(self, event: str, handler: Callable):
        """
        注销事件处理器

        Args:
            event: 事件类型
            handler: 处理器函数
        """
        if event in self._event_handlers and handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)

    def _emit_event(self, event: str, data: Dict[str, Any]):
        """
        触发事件

        Args:
            event: 事件类型
            data: 事件数据
        """
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"事件处理器错误: {e}")

    async def run(self,
                 input_data: Any,
                 context: Optional[AgentContext] = None) -> AgentResult:
        """
        运行Agent（带状态管理和错误处理）

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            AgentResult: 执行结果
        """
        import time

        if self._status == AgentStatus.RUNNING:
            return AgentResult(
                success=False,
                error="Agent正在执行中"
            )

        self._status = AgentStatus.RUNNING
        self._emit_event('started', {'input': input_data, 'context': context})

        start_time = time.time()

        try:
            # 执行Agent
            result = await self.execute(input_data, context)

            # 计算执行时间
            execution_time_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time_ms

            # 更新状态
            self._status = AgentStatus.IDLE if result.success else AgentStatus.ERROR

            # 触发事件
            if result.success:
                self._emit_event('completed', {'result': result})
            else:
                self._emit_event('failed', {'error': result.error})

            return result

        except Exception as e:
            logger.error(f"Agent '{self.name}' 执行失败: {e}", exc_info=True)

            self._status = AgentStatus.ERROR
            self._emit_event('failed', {'error': str(e)})

            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

    def pause(self) -> bool:
        """
        暂停Agent

        Returns:
            bool: 是否成功
        """
        if self._status == AgentStatus.RUNNING:
            self._status = AgentStatus.PAUSED
            self._emit_event('paused', {})
            return True
        return False

    def resume(self) -> bool:
        """
        恢复Agent

        Returns:
            bool: 是否成功
        """
        if self._status == AgentStatus.PAUSED:
            self._status = AgentStatus.RUNNING
            self._emit_event('resumed', {})
            return True
        return False

    def stop(self) -> bool:
        """
        停止Agent

        Returns:
            bool: 是否成功
        """
        if self._status in [AgentStatus.RUNNING, AgentStatus.PAUSED]:
            self._status = AgentStatus.STOPPED
            return True
        return False

    def get_info(self) -> Dict[str, Any]:
        """
        获取Agent信息

        Returns:
            Dict[str, Any]: Agent信息
        """
        return {
            "name": self.name,
            "description": self.config.description,
            "version": self.config.version,
            "author": self.config.author,
            "status": self._status.value,
            "tags": self.config.tags,
            "priority": self.config.priority.value,
            "capabilities": {
                "required": self.config.required_capabilities,
                "optional": self.config.optional_capabilities
            },
            "config": self.config.to_dict()
        }
