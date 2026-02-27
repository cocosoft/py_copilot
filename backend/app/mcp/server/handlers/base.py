"""MCP 处理器基类

定义 MCP 处理器的通用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """MCP 处理器基类
    
    所有 MCP 处理器必须继承此类。
    
    Attributes:
        name: 处理器名称
        capabilities: 处理器能力
    """
    
    def __init__(self, name: str):
        """初始化处理器
        
        Args:
            name: 处理器名称
        """
        self.name = name
        self.capabilities: Dict[str, Any] = {}
        
    @abstractmethod
    async def handle(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求
        
        Args:
            method: 请求方法名
            params: 请求参数
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取处理器能力
        
        Returns:
            能力描述字典
        """
        pass
    
    def supports_method(self, method: str) -> bool:
        """检查是否支持指定方法
        
        Args:
            method: 方法名
            
        Returns:
            是否支持
        """
        return method in self._get_supported_methods()
    
    @abstractmethod
    def _get_supported_methods(self) -> List[str]:
        """获取支持的方法列表
        
        Returns:
            方法名列表
        """
        pass
    
    def _create_error(self, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        """创建错误响应
        
        Args:
            code: 错误代码
            message: 错误消息
            data: 附加数据
            
        Returns:
            错误字典
        """
        error = {
            'code': code,
            'message': message
        }
        if data is not None:
            error['data'] = data
        return error
    
    def _create_success_result(self, data: Any) -> Dict[str, Any]:
        """创建成功结果
        
        Args:
            data: 结果数据
            
        Returns:
            结果字典
        """
        return {
            'success': True,
            'data': data
        }
