"""MCP 工具代理

将外部 MCP 工具集成到 Function Calling 系统中。
"""
from typing import Dict, Any, List
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter, ToolExecutionResult
from app.mcp.client.tool_proxy import tool_proxy_registry
import logging

logger = logging.getLogger(__name__)


class MCPTool(BaseTool):
    """MCP 工具代理类
    
    将外部 MCP 服务提供的工具代理为 Function Calling 工具。
    
    Attributes:
        proxy: MCP 工具代理实例
    """
    
    def __init__(self, tool_name: str):
        """初始化 MCP 工具
        
        Args:
            tool_name: MCP 工具名称
        """
        self.proxy = tool_proxy_registry.get_proxy(tool_name)
        if not self.proxy:
            raise ValueError(f"MCP 工具不存在: {tool_name}")
        
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """返回工具元数据"""
        return ToolMetadata(
            name=self.proxy.tool_name,
            display_name=self.proxy.tool_name,
            description=self.proxy.description,
            category="mcp",
            version="1.0.0",
            author="MCP Service",
            icon="🔗",
            tags=["MCP", "外部工具"]
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """返回工具参数定义"""
        parameters = []
        
        schema = self.proxy.input_schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for name, prop in properties.items():
            param = ToolParameter(
                name=name,
                type=prop.get("type", "string"),
                description=prop.get("description", ""),
                required=name in required,
                default=prop.get("default"),
                enum=prop.get("enum")
            )
            parameters.append(param)
        
        return parameters
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """执行 MCP 工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        import time
        
        start_time = time.time()
        
        try:
            logger.info(f"执行 MCP 工具: {self.proxy.tool_name}, 参数={kwargs}")
            
            # 执行工具调用
            result = await self.proxy.execute(**kwargs)
            
            execution_time = time.time() - start_time
            
            # 检查结果
            if isinstance(result, dict) and "error" in result:
                return ToolExecutionResult(
                    success=False,
                    error=result["error"],
                    execution_time=execution_time,
                    tool_name=self._metadata.name
                )
            
            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=self._metadata.name,
                metadata={
                    "source": "mcp",
                    "original_name": self.proxy.original_name
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"MCP 工具执行失败: {self.proxy.tool_name}, 错误: {e}")
            
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                tool_name=self._metadata.name
            )


class MCPToolManager:
    """MCP 工具管理器
    
    管理所有 MCP 工具的注册和发现。
    """
    
    def __init__(self):
        """初始化管理器"""
        self.tools: Dict[str, MCPTool] = {}
    
    def refresh_tools(self) -> int:
        """刷新 MCP 工具列表
        
        从工具代理注册表同步所有 MCP 工具。
        
        Returns:
            同步的工具数量
        """
        count = 0
        
        try:
            # 获取所有代理
            proxies = tool_proxy_registry.get_all_proxies()
            
            # 清理已不存在的工具
            removed = []
            for tool_name in self.tools:
                if tool_name not in proxies:
                    removed.append(tool_name)
            
            for tool_name in removed:
                del self.tools[tool_name]
                logger.info(f"移除 MCP 工具: {tool_name}")
            
            # 添加新工具
            for tool_name in proxies:
                if tool_name not in self.tools:
                    try:
                        tool = MCPTool(tool_name)
                        self.tools[tool_name] = tool
                        count += 1
                        logger.info(f"添加 MCP 工具: {tool_name}")
                    except Exception as e:
                        logger.error(f"创建 MCP 工具失败: {tool_name}, 错误: {e}")
            
            logger.info(f"MCP 工具刷新完成: 新增 {count} 个工具")
            
        except Exception as e:
            logger.error(f"刷新 MCP 工具失败: {e}", exc_info=True)
        
        return count
    
    def get_tool(self, tool_name: str) -> MCPTool:
        """获取 MCP 工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            MCP 工具实例
        """
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, MCPTool]:
        """获取所有 MCP 工具
        
        Returns:
            工具字典
        """
        return self.tools.copy()
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具定义
        
        Returns:
            工具定义列表
        """
        return [tool.get_tool_definition() for tool in self.tools.values()]


# 全局 MCP 工具管理器
mcp_tool_manager = MCPToolManager()
