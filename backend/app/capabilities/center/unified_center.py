"""
统一能力中心

本模块提供统一的能力管理入口，整合所有能力类型
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    CapabilityType,
    CapabilityMatch
)
from app.capabilities.adapters.skill_registry import SkillRegistry
from app.capabilities.adapters.tool_registry import ToolRegistry
from app.capabilities.adapters.mcp_adapter import MCPRegistry

logger = logging.getLogger(__name__)


class CenterStatus(Enum):
    """能力中心状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class CenterStats:
    """能力中心统计信息"""
    total_capabilities: int = 0
    skill_count: int = 0
    tool_count: int = 0
    mcp_count: int = 0
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_execution_time_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class UnifiedCapabilityCenter:
    """
    统一能力中心

    整合Skill、Tool、MCP三种能力类型，提供统一的管理接口。
    是能力编排系统的核心组件。

    Attributes:
        _skill_registry: Skill注册表
        _tool_registry: Tool注册表
        _mcp_registry: MCP注册表
        _status: 中心状态
        _stats: 统计信息
        _event_handlers: 事件处理器
    """

    def __init__(self, db: Session):
        """
        初始化统一能力中心

        Args:
            db: 数据库会话
        """
        self._db = db
        self._skill_registry: Optional[SkillRegistry] = None
        self._tool_registry: Optional[ToolRegistry] = None
        self._mcp_registry: Optional[MCPRegistry] = None
        self._status = CenterStatus.INITIALIZING
        self._stats = CenterStats()
        self._event_handlers: Dict[str, List[Callable]] = {
            'capability_registered': [],
            'capability_executed': [],
            'capability_failed': [],
            'center_error': []
        }

        logger.info("统一能力中心实例已创建")

    async def initialize(self) -> bool:
        """
        初始化能力中心

        初始化所有注册表并加载能力

        Returns:
            bool: 初始化是否成功
        """
        logger.info("开始初始化统一能力中心...")

        try:
            # 初始化Skill注册表
            self._skill_registry = SkillRegistry(self._db)
            await self._skill_registry.initialize()
            logger.info(f"Skill注册表初始化完成: {len(self._skill_registry.list_capabilities())} 个")

            # 初始化Tool注册表
            self._tool_registry = ToolRegistry(self._db)
            await self._tool_registry.initialize()
            logger.info(f"Tool注册表初始化完成: {len(self._tool_registry.list_capabilities())} 个")

            # 初始化MCP注册表
            self._mcp_registry = MCPRegistry()
            await self._mcp_registry.initialize()
            logger.info(f"MCP注册表初始化完成: {len(self._mcp_registry.list_capabilities())} 个")

            # 更新统计信息
            self._update_stats()

            self._status = CenterStatus.READY
            logger.info("统一能力中心初始化完成")

            return True

        except Exception as e:
            self._status = CenterStatus.ERROR
            logger.error(f"统一能力中心初始化失败: {e}", exc_info=True)
            self._emit_event('center_error', {'error': str(e)})
            return False

    async def shutdown(self):
        """
        关闭能力中心

        清理所有资源
        """
        logger.info("开始关闭统一能力中心...")

        try:
            if self._skill_registry:
                await self._skill_registry.shutdown()

            if self._tool_registry:
                await self._tool_registry.shutdown()

            if self._mcp_registry:
                await self._mcp_registry.shutdown()

            self._status = CenterStatus.SHUTDOWN
            logger.info("统一能力中心已关闭")

        except Exception as e:
            logger.error(f"关闭能力中心时出错: {e}", exc_info=True)

    def get_capability(self, name: str) -> Optional[BaseCapability]:
        """
        获取能力

        按名称从所有注册表中查找能力

        Args:
            name: 能力名称

        Returns:
            Optional[BaseCapability]: 能力实例，不存在返回None
        """
        # 按优先级查找: Skill -> Tool -> MCP
        if self._skill_registry and self._skill_registry.has_capability(name):
            return self._skill_registry.get_capability(name)

        if self._tool_registry and self._tool_registry.has_capability(name):
            return self._tool_registry.get_capability(name)

        if self._mcp_registry and self._mcp_registry.has_capability(name):
            return self._mcp_registry.get_capability(name)

        return None

    def has_capability(self, name: str) -> bool:
        """
        检查能力是否存在

        Args:
            name: 能力名称

        Returns:
            bool: 是否存在
        """
        return self.get_capability(name) is not None

    def list_capabilities(self) -> List[str]:
        """
        列出所有能力名称

        Returns:
            List[str]: 能力名称列表
        """
        names = set()

        if self._skill_registry:
            names.update(self._skill_registry.list_capabilities())

        if self._tool_registry:
            names.update(self._tool_registry.list_capabilities())

        if self._mcp_registry:
            names.update(self._mcp_registry.list_capabilities())

        return sorted(list(names))

    def get_capabilities_by_type(self, capability_type: CapabilityType) -> List[BaseCapability]:
        """
        按类型获取能力

        Args:
            capability_type: 能力类型

        Returns:
            List[BaseCapability]: 能力列表
        """
        if capability_type == CapabilityType.SKILL and self._skill_registry:
            return list(self._skill_registry.get_all_capabilities().values())

        if capability_type == CapabilityType.TOOL and self._tool_registry:
            return list(self._tool_registry.get_all_capabilities().values())

        if capability_type == CapabilityType.MCP and self._mcp_registry:
            return list(self._mcp_registry.get_all_capabilities().values())

        return []

    def get_all_capabilities(self) -> Dict[str, BaseCapability]:
        """
        获取所有能力

        Returns:
            Dict[str, BaseCapability]: 能力字典
        """
        capabilities = {}

        if self._skill_registry:
            capabilities.update(self._skill_registry.get_all_capabilities())

        if self._tool_registry:
            capabilities.update(self._tool_registry.get_all_capabilities())

        if self._mcp_registry:
            capabilities.update(self._mcp_registry.get_all_capabilities())

        return capabilities

    def get_capability_metadata(self, name: str) -> Optional[CapabilityMetadata]:
        """
        获取能力元数据

        Args:
            name: 能力名称

        Returns:
            Optional[CapabilityMetadata]: 元数据，不存在返回None
        """
        capability = self.get_capability(name)
        return capability.metadata if capability else None

    async def execute_capability(self,
                                 name: str,
                                 input_data: Dict[str, Any],
                                 context: Optional[ExecutionContext] = None) -> CapabilityResult:
        """
        执行能力

        Args:
            name: 能力名称
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        if not context:
            context = ExecutionContext()

        capability = self.get_capability(name)

        if not capability:
            logger.error(f"能力不存在: {name}")
            return CapabilityResult(
                success=False,
                error=f"能力不存在: {name}"
            )

        try:
            logger.info(f"执行能力: {name}")

            result = await capability.execute(input_data, context)

            # 更新统计
            self._stats.total_executions += 1
            if result.success:
                self._stats.success_count += 1
                self._emit_event('capability_executed', {
                    'name': name,
                    'success': True,
                    'execution_time': result.execution_time_ms
                })
            else:
                self._stats.failure_count += 1
                self._emit_event('capability_failed', {
                    'name': name,
                    'error': result.error
                })

            return result

        except Exception as e:
            logger.error(f"执行能力异常: {name}, error={e}", exc_info=True)
            self._stats.failure_count += 1
            self._emit_event('capability_failed', {
                'name': name,
                'error': str(e)
            })

            return CapabilityResult(
                success=False,
                error=f"执行异常: {str(e)}"
            )

    async def refresh(self):
        """
        刷新能力中心

        重新加载所有能力
        """
        logger.info("刷新统一能力中心...")

        if self._skill_registry:
            await self._skill_registry.refresh()

        if self._tool_registry:
            await self._tool_registry.refresh()

        if self._mcp_registry:
            await self._mcp_registry.refresh()

        self._update_stats()

        logger.info("统一能力中心刷新完成")

    def get_stats(self) -> CenterStats:
        """
        获取统计信息

        Returns:
            CenterStats: 统计信息
        """
        self._update_stats()
        return self._stats

    def _update_stats(self):
        """更新统计信息"""
        self._stats.skill_count = len(self._skill_registry.list_capabilities()) if self._skill_registry else 0
        self._stats.tool_count = len(self._tool_registry.list_capabilities()) if self._tool_registry else 0
        self._stats.mcp_count = len(self._mcp_registry.list_capabilities()) if self._mcp_registry else 0
        self._stats.total_capabilities = (
            self._stats.skill_count +
            self._stats.tool_count +
            self._stats.mcp_count
        )
        self._stats.last_updated = datetime.now()

    def get_status(self) -> CenterStatus:
        """
        获取中心状态

        Returns:
            CenterStatus: 状态
        """
        return self._status

    def is_ready(self) -> bool:
        """
        检查是否就绪

        Returns:
            bool: 是否就绪
        """
        return self._status == CenterStatus.READY

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

    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        return {
            "status": self._status.value,
            "is_ready": self.is_ready(),
            "skill_registry": {
                "initialized": self._skill_registry is not None,
                "count": self._stats.skill_count
            },
            "tool_registry": {
                "initialized": self._tool_registry is not None,
                "count": self._stats.tool_count
            },
            "mcp_registry": {
                "initialized": self._mcp_registry is not None,
                "count": self._stats.mcp_count
            },
            "total_capabilities": self._stats.total_capabilities,
            "total_executions": self._stats.total_executions,
            "success_rate": (
                self._stats.success_count / self._stats.total_executions * 100
                if self._stats.total_executions > 0 else 0
            )
        }
