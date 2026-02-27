"""MCP 传输层基类

定义 MCP 传输层的通用接口。
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class BaseTransport(ABC):
    """MCP 传输层基类
    
    定义所有传输层必须实现的接口。
    
    Attributes:
        config: 传输层配置
        message_handler: 消息处理回调函数
        is_running: 是否正在运行
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化传输层
        
        Args:
            config: 传输层配置字典
        """
        self.config = config
        self.message_handler: Optional[Callable[[Dict[str, Any]], None]] = None
        self.is_running = False
        
    @abstractmethod
    async def start(self) -> bool:
        """启动传输层
        
        Returns:
            是否启动成功
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止传输层
        
        Returns:
            是否停止成功
        """
        pass
    
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息
        
        Args:
            message: 要发送的消息字典
            
        Returns:
            是否发送成功
        """
        pass
    
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """设置消息处理回调
        
        Args:
            handler: 消息处理回调函数
        """
        self.message_handler = handler
        logger.info(f"消息处理器已设置: {self.__class__.__name__}")
    
    def _handle_incoming_message(self, message: Dict[str, Any]) -> None:
        """处理接收到的消息
        
        内部方法，由子类在接收到消息时调用。
        
        Args:
            message: 接收到的消息
        """
        if self.message_handler:
            try:
                self.message_handler(message)
            except Exception as e:
                logger.error(f"消息处理失败: {e}", exc_info=True)
        else:
            logger.warning("未设置消息处理器，消息被丢弃")
    
    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """验证消息格式
        
        Args:
            message: 要验证的消息
            
        Returns:
            是否验证通过
        """
        # 检查必需字段
        if not isinstance(message, dict):
            logger.error("消息必须是字典类型")
            return False
        
        if 'jsonrpc' not in message:
            logger.error("消息缺少 jsonrpc 字段")
            return False
        
        if message['jsonrpc'] != '2.0':
            logger.error(f"不支持的 JSON-RPC 版本: {message['jsonrpc']}")
            return False
        
        # 检查是否有 id 或 method
        if 'id' not in message and 'method' not in message:
            logger.error("消息必须包含 id 或 method 字段")
            return False
        
        return True
    
    def _create_error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        """创建错误响应
        
        Args:
            request_id: 请求ID
            code: 错误代码
            message: 错误消息
            data: 附加数据
            
        Returns:
            错误响应字典
        """
        error = {
            'code': code,
            'message': message
        }
        if data is not None:
            error['data'] = data
        
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': error
        }
    
    def _create_success_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        """创建成功响应
        
        Args:
            request_id: 请求ID
            result: 响应结果
            
        Returns:
            成功响应字典
        """
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': result
        }
    
    def _parse_message(self, data: str) -> Optional[Dict[str, Any]]:
        """解析消息字符串
        
        Args:
            data: 消息字符串
            
        Returns:
            解析后的消息字典，解析失败返回 None
        """
        try:
            message = json.loads(data)
            if self._validate_message(message):
                return message
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"消息解析失败: {e}")
            return None
