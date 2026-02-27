"""工具适配器

将现有工具系统适配到 MCP 协议。
"""

import logging
from typing import Dict, Any, List
import asyncio

from .base import BaseAdapter

logger = logging.getLogger(__name__)


class ToolAdapter(BaseAdapter):
    """工具适配器
    
    将 ToolRegistry 中的工具适配为 MCP 工具。
    
    Attributes:
        tool_registry: 工具注册表实例
    """
    
    def __init__(self, tool_registry=None):
        """初始化工具适配器
        
        Args:
            tool_registry: 工具注册表实例，如果为 None 则延迟加载
        """
        super().__init__("tool_adapter")
        self._tool_registry = tool_registry
        self._tools_cache = None
        
    @property
    def tool_registry(self):
        """获取工具注册表（延迟加载）"""
        if self._tool_registry is None:
            try:
                from app.modules.function_calling.tool_registry import ToolRegistry
                self._tool_registry = ToolRegistry()
            except Exception as e:
                logger.error(f"加载 ToolRegistry 失败: {e}")
                self._tool_registry = None
        return self._tool_registry
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表
        
        从 ToolRegistry 获取所有可用工具。
        
        Returns:
            MCP 格式的工具列表
        """
        tools = []
        
        try:
            if self.tool_registry:
                # 获取所有工具
                all_tools = self.tool_registry.get_all_tools()
                
                for tool_name, tool_info in all_tools.items():
                    # 转换参数格式
                    input_schema = self._convert_parameters_to_schema(
                        tool_info.get('parameters', [])
                    )
                    
                    tools.append({
                        'name': tool_name,
                        'description': tool_info.get('description', f'执行 {tool_name} 工具'),
                        'inputSchema': input_schema
                    })
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}", exc_info=True)
        
        return tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具
        
        调用 ToolRegistry 执行指定工具。
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            if not self.tool_registry:
                raise RuntimeError("ToolRegistry 未初始化")
            
            # 执行工具
            result = await self.tool_registry.execute_tool(tool_name, arguments)
            
            return result
        except Exception as e:
            logger.error(f"执行工具失败 {tool_name}: {e}", exc_info=True)
            raise
    
    def _convert_parameters_to_schema(self, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """转换参数格式为 JSON Schema
        
        Args:
            parameters: 工具参数列表
            
        Returns:
            JSON Schema 格式
        """
        properties = {}
        required = []
        
        for param in parameters:
            param_name = param.get('name')
            if not param_name:
                continue
            
            param_type = param.get('type', 'string')
            param_description = param.get('description', '')
            param_required = param.get('required', False)
            
            # 类型映射
            schema_type = self._map_type_to_json_schema(param_type)
            
            properties[param_name] = {
                'type': schema_type,
                'description': param_description
            }
            
            if param_required:
                required.append(param_name)
        
        return {
            'type': 'object',
            'properties': properties,
            'required': required
        }
    
    def _map_type_to_json_schema(self, param_type: str) -> str:
        """将参数类型映射为 JSON Schema 类型
        
        Args:
            param_type: 参数类型
            
        Returns:
            JSON Schema 类型
        """
        type_mapping = {
            'string': 'string',
            'str': 'string',
            'integer': 'integer',
            'int': 'integer',
            'number': 'number',
            'float': 'number',
            'boolean': 'boolean',
            'bool': 'boolean',
            'array': 'array',
            'list': 'array',
            'object': 'object',
            'dict': 'object'
        }
        
        return type_mapping.get(param_type.lower(), 'string')
