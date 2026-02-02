"""
平台适配器基类

定义平台适配器的接口和通用功能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Message:
    """消息类"""
    
    def __init__(self, message_id: str, platform: str, user_id: str, content: str, 
                 timestamp: datetime = None, metadata: Dict[str, Any] = None):
        """初始化消息
        
        Args:
            message_id: 消息ID
            platform: 平台名称
            user_id: 用户ID
            content: 消息内容
            timestamp: 时间戳
            metadata: 元数据
        """
        self.message_id = message_id
        self.platform = platform
        self.user_id = user_id
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            消息字典
        """
        return {
            "message_id": self.message_id,
            "platform": self.platform,
            "user_id": self.user_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化平台适配器
        
        Args:
            platform_name: 平台名称
            config: 平台配置
        """
        self.platform_name = platform_name
        self.config = config
        self.is_connected = False
        logger.info(f"初始化平台适配器: {platform_name}")
    
    @abstractmethod
    def connect(self) -> bool:
        """连接到平台
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开与平台的连接
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def send_message(self, user_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """发送消息
        
        Args:
            user_id: 用户ID
            content: 消息内容
            metadata: 元数据
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def receive_messages(self) -> List[Message]:
        """接收消息
        
        Returns:
            消息列表
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        pass
    
    @abstractmethod
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息
        """
        pass
    
    def get_platform_name(self) -> str:
        """获取平台名称
        
        Returns:
            平台名称
        """
        return self.platform_name
    
    def get_connection_status(self) -> bool:
        """获取连接状态
        
        Returns:
            连接状态
        """
        return self.is_connected
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 新配置
        """
        self.config = config
        logger.info(f"平台配置已更新: {self.platform_name}")
    
    def handle_error(self, error: Exception, context: str):
        """处理错误
        
        Args:
            error: 错误对象
            context: 上下文信息
        """
        logger.error(f"平台 {self.platform_name} 错误 ({context}): {str(error)}")
