"""
Tool注册表

本模块管理所有Tool能力的注册和发现
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.capabilities.adapters.tool_adapter import ToolCapability
from app.models.tool import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Tool注册表

    管理所有Tool能力的注册、发现和生命周期。
    提供Tool到Capability的统一访问接口。

    Attributes:
        _capabilities: 已注册的Tool能力字典
        _db: 数据库会话
    """

    def __init__(self, db: Session):
        """
        初始化Tool注册表

        Args:
            db: 数据库会话
        """
        self._capabilities: Dict[str, ToolCapability] = {}
        self._db = db

    async def initialize(self):
        """
        初始化注册表

        从数据库加载所有启用的Tool并注册
        """
        logger.info("开始初始化Tool注册表...")

        try:
            # 加载所有启用的Tool
            tools = self._db.query(Tool).filter(
                Tool.status == "enabled",
                Tool.is_active == True
            ).all()

            for tool in tools:
                await self.register_tool(tool)

            logger.info(f"Tool注册表初始化完成，共注册 {len(self._capabilities)} 个Tool")

        except Exception as e:
            logger.error(f"Tool注册表初始化失败: {e}", exc_info=True)
            raise

    async def register_tool(self, tool: Tool) -> ToolCapability:
        """
        注册单个Tool

        Args:
            tool: Tool模型实例

        Returns:
            ToolCapability: 创建的Tool能力适配器
        """
        try:
            # 创建适配器
            capability = ToolCapability(tool)

            # 初始化
            await capability.initialize()

            # 注册
            self._capabilities[tool.name] = capability

            logger.debug(f"Tool已注册: {tool.name} (type={tool.tool_type})")

            return capability

        except Exception as e:
            logger.error(f"注册Tool失败: {tool.name}, error={e}")
            raise

    async def unregister_tool(self, tool_name: str):
        """
        注销Tool

        Args:
            tool_name: Tool名称
        """
        if tool_name in self._capabilities:
            capability = self._capabilities[tool_name]
            await capability.cleanup()
            del self._capabilities[tool_name]

            logger.debug(f"Tool已注销: {tool_name}")

    def get_capability(self, tool_name: str) -> Optional[ToolCapability]:
        """
        获取Tool能力

        Args:
            tool_name: Tool名称

        Returns:
            Optional[ToolCapability]: Tool能力适配器，不存在返回None
        """
        return self._capabilities.get(tool_name)

    def has_capability(self, tool_name: str) -> bool:
        """
        检查是否存在指定Tool

        Args:
            tool_name: Tool名称

        Returns:
            bool: 是否存在
        """
        return tool_name in self._capabilities

    def list_capabilities(self) -> List[str]:
        """
        列出所有已注册的Tool名称

        Returns:
            List[str]: Tool名称列表
        """
        return list(self._capabilities.keys())

    def get_all_capabilities(self) -> Dict[str, ToolCapability]:
        """
        获取所有已注册的Tool能力

        Returns:
            Dict[str, ToolCapability]: Tool能力字典
        """
        return self._capabilities.copy()

    def get_capabilities_by_type(self, tool_type: str) -> List[ToolCapability]:
        """
        根据类型获取Tool能力

        Args:
            tool_type: Tool类型 (local/mcp/official)

        Returns:
            List[ToolCapability]: Tool能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.tool.tool_type == tool_type
        ]

    def get_capabilities_by_category(self, category: str) -> List[ToolCapability]:
        """
        根据分类获取Tool能力

        Args:
            category: 分类

        Returns:
            List[ToolCapability]: Tool能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.tool.category == category
        ]

    def get_official_capabilities(self) -> List[ToolCapability]:
        """
        获取所有官方Tool能力

        Returns:
            List[ToolCapability]: 官方Tool能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.tool.is_official
        ]

    def get_local_capabilities(self) -> List[ToolCapability]:
        """
        获取所有本地Tool能力

        Returns:
            List[ToolCapability]: 本地Tool能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.tool.tool_type == "local"
        ]

    def get_mcp_capabilities(self) -> List[ToolCapability]:
        """
        获取所有MCP Tool能力

        Returns:
            List[ToolCapability]: MCP Tool能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.tool.tool_type == "mcp"
        ]

    async def refresh(self):
        """
        刷新注册表

        重新从数据库加载所有Tool
        """
        logger.info("刷新Tool注册表...")

        # 清理现有注册
        for capability in self._capabilities.values():
            await capability.cleanup()

        self._capabilities.clear()

        # 重新初始化
        await self.initialize()

    async def shutdown(self):
        """
        关闭注册表

        清理所有资源
        """
        logger.info("关闭Tool注册表...")

        for capability in self._capabilities.values():
            await capability.cleanup()

        self._capabilities.clear()

        logger.info("Tool注册表已关闭")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取注册表统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total = len(self._capabilities)
        local = sum(1 for cap in self._capabilities.values() if cap.tool.tool_type == "local")
        mcp = sum(1 for cap in self._capabilities.values() if cap.tool.tool_type == "mcp")
        official = sum(1 for cap in self._capabilities.values() if cap.tool.tool_type == "official")

        return {
            "total_tools": total,
            "local_tools": local,
            "mcp_tools": mcp,
            "official_tools": official,
            "registered_names": list(self._capabilities.keys())
        }
