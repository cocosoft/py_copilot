"""
Tool能力适配器

本模块将现有Tool系统适配为统一Capability接口
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
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
from app.models.tool import Tool, ToolExecutionLog
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class ToolCapability(BaseCapability):
    """
    Tool能力适配器

    将现有Tool系统适配为统一Capability接口。

    支持三种Tool类型：
    1. local: 本地工具，直接调用处理函数
    2. mcp: MCP工具，通过MCP客户端调用
    3. official: 官方工具，使用内置实现

    Attributes:
        tool: 原始Tool模型实例
        _handler: 本地处理函数（仅local类型）
    """

    # 本地工具处理函数注册表
    _local_handlers: Dict[str, Callable] = {}

    def __init__(self, tool: Tool):
        """
        初始化Tool能力适配器

        Args:
            tool: Tool模型实例
        """
        # 处理tags
        tags = parse_tags(tool.tags)

        # 构建元数据
        metadata = CapabilityMetadata(
            name=tool.name,
            display_name=tool.display_name or tool.name,
            description=tool.description or "",
            capability_type=CapabilityType.TOOL,
            level=CapabilityLevel.ATOMIC,
            category=tool.category or "general",
            tags=tags,
            input_schema=self._build_input_schema(tool),
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "any"},
                    "metadata": {"type": "object"}
                }
            },
            timeout_seconds=30,  # Tool默认30秒超时
            max_retries=2,
            version=tool.version or "1.0.0",
            author=tool.author or "system"
        )

        super().__init__(metadata)
        self.tool = tool
        self._handler: Optional[Callable] = None

    def _build_input_schema(self, tool: Tool) -> Dict[str, Any]:
        """
        构建输入Schema

        Args:
            tool: Tool模型

        Returns:
            Dict[str, Any]: 输入Schema
        """
        if not tool.parameters_schema:
            return {
                "type": "object",
                "properties": {}
            }

        # Tool的parameters_schema已经是标准格式
        return tool.parameters_schema

    @classmethod
    def register_local_handler(cls, tool_name: str, handler: Callable):
        """
        注册本地工具处理函数

        Args:
            tool_name: 工具名称
            handler: 处理函数
        """
        cls._local_handlers[tool_name] = handler
        logger.info(f"注册本地工具处理器: {tool_name}")

    async def _do_execute(self,
                         input_data: Dict[str, Any],
                         context: ExecutionContext) -> CapabilityResult:
        """
        执行Tool

        根据Tool类型选择执行方式

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        execution_log = None

        try:
            # 创建执行日志
            execution_log = await self._create_execution_log(input_data, context)

            # 根据类型执行
            if self.tool.tool_type == "mcp":
                result = await self._execute_mcp(input_data, context)
            elif self.tool.tool_type == "official":
                result = await self._execute_official(input_data, context)
            else:  # local
                result = await self._execute_local(input_data, context)

            # 更新执行日志
            await self._update_execution_log(
                execution_log,
                success=result.success,
                output=str(result.output) if result.output else "",
                error=result.error
            )

            # 添加执行日志ID到metadata
            result.metadata["execution_log_id"] = execution_log.id

            return result

        except Exception as e:
            logger.error(f"Tool执行异常: {self.tool.name}, error={e}", exc_info=True)

            if execution_log:
                await self._update_execution_log(
                    execution_log,
                    success=False,
                    error=str(e)
                )

            return CapabilityResult(
                success=False,
                error=f"Tool执行异常: {str(e)}",
                metadata={
                    "tool_id": self.tool.id,
                    "tool_name": self.tool.name,
                    "tool_type": self.tool.tool_type
                }
            )

    async def _execute_local(self,
                            input_data: Dict[str, Any],
                            context: ExecutionContext) -> CapabilityResult:
        """
        执行本地Tool

        通过handler_module和handler_class动态加载处理类

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        # 方法1: 使用注册的处理函数
        if self.tool.name in self._local_handlers:
            handler = self._local_handlers[self.tool.name]
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(input_data, context)
                else:
                    result = handler(input_data, context)

                return CapabilityResult(
                    success=True,
                    output=result
                )
            except Exception as e:
                return CapabilityResult(
                    success=False,
                    error=f"本地工具执行失败: {str(e)}"
                )

        # 方法2: 动态加载处理类
        if self.tool.handler_module and self.tool.handler_class:
            try:
                # 动态导入模块
                module = __import__(
                    self.tool.handler_module,
                    fromlist=[self.tool.handler_class]
                )
                handler_class = getattr(module, self.tool.handler_class)
                handler = handler_class()

                # 调用处理方法
                if hasattr(handler, 'execute'):
                    if asyncio.iscoroutinefunction(handler.execute):
                        result = await handler.execute(input_data, context)
                    else:
                        result = handler.execute(input_data, context)

                    return CapabilityResult(
                        success=True,
                        output=result
                    )
                else:
                    return CapabilityResult(
                        success=False,
                        error=f"处理器类缺少execute方法"
                    )

            except Exception as e:
                return CapabilityResult(
                    success=False,
                    error=f"加载Tool处理器失败: {str(e)}"
                )

        return CapabilityResult(
            success=False,
            error=f"Tool '{self.tool.name}' 没有配置处理器"
        )

    async def _execute_mcp(self,
                          input_data: Dict[str, Any],
                          context: ExecutionContext) -> CapabilityResult:
        """
        通过MCP执行Tool

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        try:
            # 导入MCP连接管理器
            from app.mcp.client.connection_manager import MCPConnectionManager

            # 获取MCP客户端
            client = await MCPConnectionManager.get_client(
                self.tool.mcp_client_config_id
            )

            if not client:
                return CapabilityResult(
                    success=False,
                    error=f"MCP客户端未连接: config_id={self.tool.mcp_client_config_id}"
                )

            # 调用MCP工具
            logger.info(f"调用MCP工具: {self.tool.mcp_tool_name}")

            result = await client.call_tool(
                tool_name=self.tool.mcp_tool_name,
                params=input_data
            )

            return CapabilityResult(
                success=True,
                output=result,
                metadata={
                    "mcp_client_id": self.tool.mcp_client_config_id,
                    "mcp_tool_name": self.tool.mcp_tool_name
                }
            )

        except Exception as e:
            return CapabilityResult(
                success=False,
                error=f"MCP调用失败: {str(e)}"
            )

    async def _execute_official(self,
                               input_data: Dict[str, Any],
                               context: ExecutionContext) -> CapabilityResult:
        """
        执行官方Tool

        使用内置的官方工具实现

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            CapabilityResult: 执行结果
        """
        # 导入工具集成服务
        from app.services.tool_integration_service import ToolIntegrationService

        try:
            # 获取工具服务实例
            tool_service = ToolIntegrationService()

            # 执行工具
            result = tool_service.execute_tool(
                tool_name=self.tool.name,
                parameters=input_data
            )

            return CapabilityResult(
                success=result.success,
                output=result.result,
                error=result.error_message,
                metadata={
                    "execution_time": result.execution_time,
                    "tool_name": result.tool_name
                }
            )

        except Exception as e:
            return CapabilityResult(
                success=False,
                error=f"官方工具执行失败: {str(e)}"
            )

    async def _create_execution_log(self,
                                   input_data: Dict[str, Any],
                                   context: ExecutionContext) -> ToolExecutionLog:
        """创建执行日志"""
        db = SessionLocal()
        try:
            log = ToolExecutionLog(
                tool_id=self.tool.id,
                agent_id=context.agent_id,
                conversation_id=context.conversation_id,
                user_id=context.user_id,
                input_params=input_data,
                status="pending"
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        finally:
            db.close()

    async def _update_execution_log(self,
                                   log: ToolExecutionLog,
                                   success: bool,
                                   output: str = "",
                                   error: str = ""):
        """更新执行日志"""
        db = SessionLocal()
        try:
            log.status = "success" if success else "failed"
            log.output_result = output
            log.error_message = error
            db.commit()
        finally:
            db.close()

    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证输入"""
        if not self.metadata.input_schema:
            return ValidationResult(valid=True)

        validator = InputValidator(self.metadata.input_schema)
        return validator.validate(input_data)

    def get_tool_info(self) -> Dict[str, Any]:
        """
        获取Tool详细信息

        Returns:
            Dict: Tool信息
        """
        return {
            "id": self.tool.id,
            "name": self.tool.name,
            "display_name": self.tool.display_name,
            "description": self.tool.description,
            "tool_type": self.tool.tool_type,
            "category": self.tool.category,
            "version": self.tool.version,
            "status": self.tool.status,
            "is_official": self.tool.is_official,
            "is_builtin": self.tool.is_builtin,
            "author": self.tool.author,
            "tags": self.tool.tags,
            "usage_count": self.tool.usage_count,
            "last_used_at": self.tool.last_used_at.isoformat() if self.tool.last_used_at else None
        }


# 导入asyncio用于检查协程函数
import asyncio
