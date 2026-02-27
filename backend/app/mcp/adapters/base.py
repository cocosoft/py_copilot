"""MCP 适配器基类

定义 MCP 适配器的通用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """MCP 适配器基类
    
    所有 MCP 适配器必须继承此类。
    
    Attributes:
        name: 适配器名称
    """
    
    def __init__(self, name: str):
        """初始化适配器
        
        Args:
            name: 适配器名称
        """
        self.name = name
        
    @abstractmethod
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表
        
        Returns:
            工具列表，每个工具包含 name, description, inputSchema
        """
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        pass
    
    async def get_resources(self) -> List[Dict[str, Any]]:
        """获取资源列表
        
        Returns:
            资源列表，每个资源包含 uri, name, description, mimeType
        """
        return []
    
    async def read_resource(self, uri: str) -> Any:
        """读取资源
        
        Args:
            uri: 资源 URI
            
        Returns:
            资源内容
        """
        raise NotImplementedError(f"Adapter {self.name} does not support resources")
    
    async def get_prompts(self) -> List[Dict[str, Any]]:
        """获取提示模板列表
        
        Returns:
            提示模板列表，每个模板包含 name, description, arguments
        """
        return []
    
    async def get_prompt_content(self, name: str, arguments: Dict[str, Any]) -> str:
        """获取提示模板内容
        
        Args:
            name: 模板名称
            arguments: 模板参数
            
        Returns:
            提示模板内容
        """
        raise NotImplementedError(f"Adapter {self.name} does not support prompts")
