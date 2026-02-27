"""MCP Tools 处理器

处理 MCP 协议中的工具相关请求。
"""

import logging
from typing import Dict, Any, List, Optional, Callable
import asyncio

from .base import BaseHandler

logger = logging.getLogger(__name__)


class ToolsHandler(BaseHandler):
    """工具处理器
    
    处理 tools/list 和 tools/call 请求。
    
    Attributes:
        tools: 工具注册表
        adapters: 工具适配器列表
    """
    
    def __init__(self):
        """初始化工具处理器"""
        super().__init__("tools")
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.adapters: List[Any] = []
        self.capabilities = {
            "listChanged": True
        }
        
    def _get_supported_methods(self) -> List[str]:
        """获取支持的方法列表
        
        Returns:
            方法名列表
        """
        return [
            "tools/list",
            "tools/call"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取处理器能力
        
        Returns:
            能力描述字典
        """
        return self.capabilities
    
    def register_adapter(self, adapter: Any) -> None:
        """注册工具适配器
        
        Args:
            adapter: 工具适配器实例
        """
        self.adapters.append(adapter)
        logger.info(f"注册工具适配器: {adapter.__class__.__name__}")
    
    async def refresh_tools(self) -> None:
        """刷新工具列表
        
        从所有适配器收集工具信息。
        """
        self.tools = {}
        
        for adapter in self.adapters:
            try:
                adapter_tools = await adapter.get_tools()
                for tool in adapter_tools:
                    tool_name = tool.get('name')
                    if tool_name:
                        self.tools[tool_name] = {
                            **tool,
                            '_adapter': adapter
                        }
            except Exception as e:
                logger.error(f"从适配器获取工具失败: {e}", exc_info=True)
        
        logger.info(f"工具列表已刷新，共 {len(self.tools)} 个工具")
    
    async def handle(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具请求
        
        Args:
            method: 请求方法名
            params: 请求参数
            
        Returns:
            处理结果
        """
        try:
            if method == "tools/list":
                return await self._handle_list(params)
            elif method == "tools/call":
                return await self._handle_call(params)
            else:
                return self._create_error(
                    -32601,
                    f"Method not found: {method}"
                )
        except Exception as e:
            logger.error(f"处理工具请求失败: {e}", exc_info=True)
            return self._create_error(
                -32603,
                f"Internal error: {str(e)}"
            )
    
    async def _handle_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 tools/list 请求
        
        返回所有可用工具列表。
        
        Args:
            params: 请求参数（可包含 cursor 用于分页）
            
        Returns:
            工具列表
        """
        # 确保工具列表是最新的
        await self.refresh_tools()
        
        # 构建工具列表
        tools_list = []
        for name, tool in self.tools.items():
            tools_list.append({
                "name": name,
                "description": tool.get("description", ""),
                "inputSchema": tool.get("inputSchema", {})
            })
        
        result = {
            "tools": tools_list
        }
        
        # 如果有更多数据，添加 nextCursor
        # 这里简化处理，不分页
        
        return result
    
    async def _handle_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 tools/call 请求
        
        执行指定的工具调用。
        
        Args:
            params: 请求参数，包含 name 和 arguments
            
        Returns:
            工具调用结果
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return self._create_error(
                -32602,
                "Invalid params: missing 'name'"
            )
        
        # 查找工具
        tool = self.tools.get(tool_name)
        if not tool:
            return self._create_error(
                -32602,
                f"Tool not found: {tool_name}"
            )
        
        # 获取适配器
        adapter = tool.get('_adapter')
        if not adapter:
            return self._create_error(
                -32603,
                f"Tool adapter not found: {tool_name}"
            )
        
        try:
            # 执行工具调用
            result = await adapter.execute_tool(tool_name, arguments)
            
            # 格式化结果
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result) if not isinstance(result, str) else result
                    }
                ],
                "isError": False
            }
        except Exception as e:
            logger.error(f"工具调用失败 {tool_name}: {e}", exc_info=True)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称
        
        Returns:
            工具名称列表
        """
        return list(self.tools.keys())
