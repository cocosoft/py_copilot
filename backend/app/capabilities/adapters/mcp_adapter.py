"""
MCP能力适配器

本模块将MCP服务适配为统一Capability接口
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityResult,
    ExecutionContext,
    ValidationResult,
    CapabilityType,
    CapabilityLevel
)
from app.capabilities.validators import InputValidator
from app.capabilities.utils import parse_tags
from app.mcp.schemas import MCPClientConfig, ConnectionStatus
from app.mcp.client.client import MCPClient
from app.mcp.client.connection_manager import MCPConnectionManager

logger = logging.getLogger(__name__)


class MCPCapability(BaseCapability):
    """
    MCP能力适配器

    将MCP服务适配为统一Capability接口。
    每个MCP工具对应一个MCPCapability实例。

    Attributes:
        mcp_config: MCP客户端配置
        tool_name: MCP工具名称
        tool_schema: MCP工具Schema
        _client: MCP客户端实例
    """

    def __init__(self,
                 mcp_config: MCPClientConfig,
                 tool_name: str,
                 tool_schema: Dict[str, Any]):
        """
        初始化MCP能力适配器

        Args:
            mcp_config: MCP客户端配置
            tool_name: MCP工具名称
            tool_schema: MCP工具Schema
        """
        # 构建元数据
        metadata = CapabilityMetadata(
            name=f"mcp_{mcp_config.name}_{tool_name}",
            display_name=tool_schema.get("display_name") or tool_name,
            description=tool_schema.get("description", ""),
            capability_type=CapabilityType.MCP,
            level=CapabilityLevel.ATOMIC,
            category="mcp",
            tags=["mcp", mcp_config.name] + parse_tags(tool_schema.get("tags", [])),
            input_schema=tool_schema.get("inputSchema", {"type": "object", "properties": {}}),
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "any"},
                    "content": {"type": "array"}
                }
            },
            timeout_seconds=mcp_config.timeout_seconds or 60,
            max_retries=2,
            version="1.0.0",
            author=f"mcp:{mcp_config.name}"
        )

        super().__init__(metadata)
        self.mcp_config = mcp_config
        self.tool_name = tool_name
        self.tool_schema = tool_schema
        self._client: Optional[MCPClient] = None

    async def initialize(self) -> bool:
        """
        初始化MCP适配器

        获取或创建MCP客户端连接

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 获取连接管理器
            manager = MCPConnectionManager()

            # 获取客户端
            self._client = manager.clients.get(self.mcp_config.id)

            if not self._client:
                # 创建新客户端
                self._client = MCPClient(self.mcp_config)
                manager.clients[self.mcp_config.id] = self._client

                # 连接
                if not await self._client.connect():
                    logger.error(f"MCP客户端连接失败: {self.mcp_config.name}")
                    return False

            self._is_initialized = True
            logger.info(f"MCP适配器 '{self.name}' 初始化完成")
            return True

        except Exception as e:
            logger.error(f"MCP适配器 '{self.name}' 初始化失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        # 注意：我们不关闭客户端，因为可能被其他能力共享使用
        self._client = None
        self._is_initialized = False
        logger.info(f"MCP适配器 '{self.name}' 资源已清理")

    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """
        执行MCP工具

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        try:
            # 检查客户端连接
            if not self._client or not self._client.is_connected:
                return CapabilityResult(
                    success=False,
                    error="MCP客户端未连接"
                )

            # 调用MCP工具
            logger.info(f"调用MCP工具: {self.mcp_config.name}/{self.tool_name}")

            result = await self._client.call_tool(
                name=self.tool_name,
                arguments=input_data
            )

            # 解析结果
            if result.get("isError"):
                return CapabilityResult(
                    success=False,
                    error=result.get("content", "MCP工具执行失败"),
                    metadata={
                        "mcp_config_id": self.mcp_config.id,
                        "mcp_config_name": self.mcp_config.name,
                        "tool_name": self.tool_name
                    }
                )

            # 提取内容
            content = result.get("content", [])
            output = None

            if content and len(content) > 0:
                # 尝试提取文本内容
                text_parts = []
                for item in content:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))

                if text_parts:
                    output = "\n".join(text_parts)
                else:
                    output = content

            return CapabilityResult(
                success=True,
                output=output,
                artifacts=[{"type": "mcp_result", "content": content}],
                metadata={
                    "mcp_config_id": self.mcp_config.id,
                    "mcp_config_name": self.mcp_config.name,
                    "tool_name": self.tool_name
                }
            )

        except Exception as e:
            logger.error(f"MCP工具执行异常: {self.name}, error={e}", exc_info=True)

            return CapabilityResult(
                success=False,
                error=f"MCP工具执行异常: {str(e)}",
                metadata={
                    "mcp_config_id": self.mcp_config.id,
                    "tool_name": self.tool_name,
                    "exception_type": type(e).__name__
                }
            )

    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """
        验证输入数据

        Args:
            input_data: 输入数据

        Returns:
            ValidationResult: 验证结果
        """
        input_schema = self.tool_schema.get("inputSchema", {})

        if not input_schema:
            return ValidationResult(valid=True)

        validator = InputValidator(input_schema)
        return validator.validate(input_data)

    def get_mcp_info(self) -> Dict[str, Any]:
        """
        获取MCP详细信息

        Returns:
            Dict: MCP信息
        """
        return {
            "mcp_config_id": self.mcp_config.id,
            "mcp_config_name": self.mcp_config.name,
            "tool_name": self.tool_name,
            "tool_schema": self.tool_schema,
            "is_connected": self._client.is_connected if self._client else False,
            "timeout_seconds": self.mcp_config.timeout_seconds
        }


class MCPRegistry:
    """
    MCP能力注册表

    管理所有MCP能力的注册、发现和生命周期。
    """

    def __init__(self):
        """初始化MCP注册表"""
        self._capabilities: Dict[str, MCPCapability] = {}
        self._connection_manager: Optional[MCPConnectionManager] = None

    async def initialize(self):
        """
        初始化注册表

        从所有MCP客户端加载工具并注册
        """
        logger.info("开始初始化MCP注册表...")

        try:
            # 获取连接管理器
            self._connection_manager = MCPConnectionManager()

            # 遍历所有客户端
            for config_id, client in self._connection_manager.clients.items():
                if client.is_connected:
                    await self._register_client_tools(config_id, client)

            logger.info(f"MCP注册表初始化完成，共注册 {len(self._capabilities)} 个MCP工具")

        except Exception as e:
            logger.error(f"MCP注册表初始化失败: {e}", exc_info=True)
            raise

    async def _register_client_tools(self, config_id: int, client: MCPClient):
        """
        注册客户端的所有工具

        Args:
            config_id: 配置ID
            client: MCP客户端
        """
        try:
            # 获取配置
            config = client.config

            # 获取工具列表
            tools = client.tools

            for tool in tools:
                tool_name = tool.get("name")
                if not tool_name:
                    continue

                # 创建适配器
                capability = MCPCapability(
                    mcp_config=config,
                    tool_name=tool_name,
                    tool_schema=tool
                )

                # 初始化
                await capability.initialize()

                # 注册
                self._capabilities[capability.name] = capability

                logger.debug(f"MCP工具已注册: {capability.name}")

        except Exception as e:
            logger.error(f"注册MCP客户端工具失败: config_id={config_id}, error={e}")

    async def refresh(self):
        """
        刷新注册表

        重新从所有MCP客户端加载工具
        """
        logger.info("刷新MCP注册表...")

        # 清理现有注册
        for capability in self._capabilities.values():
            await capability.cleanup()

        self._capabilities.clear()

        # 重新初始化
        await self.initialize()

    def get_capability(self, name: str) -> Optional[MCPCapability]:
        """
        获取MCP能力

        Args:
            name: 能力名称

        Returns:
            Optional[MCPCapability]: MCP能力适配器
        """
        return self._capabilities.get(name)

    def has_capability(self, name: str) -> bool:
        """
        检查是否存在指定能力

        Args:
            name: 能力名称

        Returns:
            bool: 是否存在
        """
        return name in self._capabilities

    def list_capabilities(self) -> List[str]:
        """
        列出所有已注册的MCP能力

        Returns:
            List[str]: 能力名称列表
        """
        return list(self._capabilities.keys())

    def get_all_capabilities(self) -> Dict[str, MCPCapability]:
        """
        获取所有已注册的MCP能力

        Returns:
            Dict[str, MCPCapability]: MCP能力字典
        """
        return self._capabilities.copy()

    def get_capabilities_by_config(self, config_name: str) -> List[MCPCapability]:
        """
        根据配置名称获取MCP能力

        Args:
            config_name: MCP配置名称

        Returns:
            List[MCPCapability]: MCP能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.mcp_config.name == config_name
        ]

    async def shutdown(self):
        """
        关闭注册表

        清理所有资源
        """
        logger.info("关闭MCP注册表...")

        for capability in self._capabilities.values():
            await capability.cleanup()

        self._capabilities.clear()

        logger.info("MCP注册表已关闭")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取注册表统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 按配置分组统计
        config_groups = {}
        for cap in self._capabilities.values():
            config_name = cap.mcp_config.name
            if config_name not in config_groups:
                config_groups[config_name] = []
            config_groups[config_name].append(cap.tool_name)

        return {
            "total_mcp_tools": len(self._capabilities),
            "config_count": len(config_groups),
            "configs": config_groups,
            "registered_names": list(self._capabilities.keys())
        }
