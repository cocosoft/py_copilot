"""工具集成适配器 - 将现有工具适配为Function Calling格式"""
from typing import Dict, Any, List, Optional
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter, ToolExecutionResult
from app.services.tool_integration_service import (
    ToolIntegrationService,
    ToolCategory,
    ToolParameter as LegacyToolParameter,
    ToolDefinition as LegacyToolDefinition
)
import logging
import time

logger = logging.getLogger(__name__)


class AdaptedTool(BaseTool):
    """适配后的工具类"""

    def __init__(self, legacy_tool: LegacyToolDefinition, legacy_service: ToolIntegrationService):
        """初始化适配工具"""
        self._legacy_tool = legacy_tool
        self._legacy_service = legacy_service
        super().__init__()

    def _get_metadata(self) -> ToolMetadata:
        """获取工具元数据"""
        return ToolMetadata(
            name=self._legacy_tool.name,
            display_name=self._legacy_tool.display_name,
            description=self._legacy_tool.description,
            category=self._legacy_tool.category.value,
            version="1.0.0",
            author="System",
            icon=self._legacy_tool.icon,
            tags=[],
            is_active=self._legacy_tool.is_active
        )

    def _get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name=param.name,
                type=param.type,
                description=param.description,
                required=param.required,
                default=param.default
            )
            for param in self._legacy_tool.parameters
        ]

    async def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """执行工具

        Args:
            parameters: 工具参数字典

        Returns:
            执行结果
        """
        start_time = time.time()

        try:
            # 调用遗留工具执行
            legacy_result = self._legacy_service.execute_tool(
                tool_name=self._legacy_tool.name,
                parameters=parameters or {}
            )

            execution_time = time.time() - start_time

            return ToolExecutionResult(
                success=legacy_result.success,
                result=legacy_result.result,
                error=legacy_result.error_message,
                execution_time=execution_time,
                tool_name=self._legacy_tool.name
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"执行适配工具失败: {self._legacy_tool.name}, 错误: {str(e)}")

            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                tool_name=self._legacy_tool.name
            )


class ToolIntegrationAdapter:
    """工具集成适配器，将现有工具系统适配为Function Calling格式"""

    def __init__(self, tool_integration_service: Optional[ToolIntegrationService] = None):
        """
        初始化适配器

        Args:
            tool_integration_service: 工具集成服务实例
        """
        self.tool_integration_service = tool_integration_service or ToolIntegrationService()
        self._adapted_tools: Dict[str, BaseTool] = {}

    def adapt_all_tools(self) -> List[BaseTool]:
        """
        适配所有现有工具

        Returns:
            适配后的工具列表
        """
        adapted_tools = []

        # 获取所有工具
        legacy_tools = self.tool_integration_service.list_tools()

        for legacy_tool in legacy_tools:
            try:
                adapted_tool = self._adapt_tool(legacy_tool)
                if adapted_tool:
                    adapted_tools.append(adapted_tool)
                    self._adapted_tools[legacy_tool.name] = adapted_tool
                    logger.info(f"成功适配工具: {legacy_tool.name}")
            except Exception as e:
                logger.error(f"适配工具失败: {legacy_tool.name}, 错误: {str(e)}")

        return adapted_tools

    def _adapt_tool(self, legacy_tool: LegacyToolDefinition) -> Optional[BaseTool]:
        """
        适配单个工具

        Args:
            legacy_tool: 遗留工具定义

        Returns:
            适配后的工具
        """
        return AdaptedTool(legacy_tool, self.tool_integration_service)

    def get_adapted_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取适配后的工具

        Args:
            tool_name: 工具名称

        Returns:
            适配后的工具，不存在则返回None
        """
        return self._adapted_tools.get(tool_name)
