"""
WebSocket连接管理器

负责管理所有WebSocket连接的生命周期，包括连接跟踪、心跳检测、
连接状态监控和连接池管理。
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from uuid import uuid4
from enum import Enum

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """连接状态枚举"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    IDLE = "idle"
    ACTIVE = "active"


class ClientType(Enum):
    """客户端类型枚举"""
    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    CLI = "cli"
    API = "api"


class WebSocketConnection:
    """WebSocket连接封装类"""
    
    def __init__(self, websocket: WebSocket, client_id: str, client_type: ClientType = ClientType.WEB):
        """初始化连接
        
        Args:
            websocket: WebSocket连接对象
            client_id: 客户端ID
            client_type: 客户端类型
        """
        self.websocket = websocket
        self.client_id = client_id
        self.client_type = client_type
        self.connection_id = str(uuid4())
        self.status = ConnectionStatus.CONNECTED
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.last_heartbeat = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self.subscriptions: Set[str] = set()
        self.message_count = 0
        self.error_count = 0
        
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息到客户端
        
        Args:
            message: 消息内容
            
        Returns:
            发送是否成功
        """
        try:
            await self.websocket.send_text(json.dumps(message))
            self.last_activity = datetime.now()
            self.message_count += 1
            return True
        except Exception as e:
            logger.error(f"发送消息到客户端 {self.client_id} 失败: {e}")
            self.error_count += 1
            return False
            
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """接收客户端消息
        
        Returns:
            消息内容，如果连接断开返回None
        """
        try:
            data = await self.websocket.receive_text()
            self.last_activity = datetime.now()
            return json.loads(data)
        except Exception as e:
            logger.error(f"接收客户端 {self.client_id} 消息失败: {e}")
            return None
            
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
        
    def is_alive(self, timeout_seconds: int = 30) -> bool:
        """检查连接是否存活
        
        Args:
            timeout_seconds: 超时时间（秒）
            
        Returns:
            连接是否存活
        """
        return (datetime.now() - self.last_heartbeat).total_seconds() < timeout_seconds
        
    def is_active(self, timeout_seconds: int = 300) -> bool:
        """检查连接是否活跃
        
        Args:
            timeout_seconds: 超时时间（秒）
            
        Returns:
            连接是否活跃
        """
        return (datetime.now() - self.last_activity).total_seconds() < timeout_seconds
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "connection_id": self.connection_id,
            "client_id": self.client_id,
            "client_type": self.client_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "subscriptions": list(self.subscriptions),
            "metadata": self.metadata
        }


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        """初始化连接管理器"""
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.connection_groups: Dict[str, Set[str]] = {}  # 组名 -> 连接ID集合
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.cleanup_interval = 60    # 清理间隔（秒）
        self.max_connections = 1000   # 最大连接数
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def connect(self, websocket: WebSocket, client_id: str, 
                     client_type: ClientType = ClientType.WEB, 
                     metadata: Optional[Dict[str, Any]] = None) -> WebSocketConnection:
        """接受新连接
        
        Args:
            websocket: WebSocket连接对象
            client_id: 客户端ID
            client_type: 客户端类型
            metadata: 连接元数据
            
        Returns:
            WebSocket连接对象
        """
        # 检查连接数限制
        if len(self.active_connections) >= self.max_connections:
            raise Exception("连接数已达上限")
            
        # 接受WebSocket连接
        await websocket.accept()
        
        # 创建连接对象
        connection = WebSocketConnection(websocket, client_id, client_type)
        if metadata:
            connection.metadata.update(metadata)
            
        # 添加到活跃连接
        self.active_connections[connection.connection_id] = connection
        
        logger.info(f"客户端 {client_id} 连接成功，连接ID: {connection.connection_id}")
        
        # 发送连接确认消息
        await connection.send_message({
            "type": "connection_established",
            "connection_id": connection.connection_id,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return connection
        
    async def disconnect(self, connection_id: str, close_code: int = 1000):
        """断开连接
        
        Args:
            connection_id: 连接ID
            close_code: 关闭代码
        """
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            connection.status = ConnectionStatus.DISCONNECTED
            
            # 从所有组中移除
            for group_name in list(connection.subscriptions):
                await self.leave_group(connection_id, group_name)
                
            # 从活跃连接中移除
            del self.active_connections[connection_id]
            
            logger.info(f"客户端 {connection.client_id} 断开连接")
            
    async def send_to_client(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """发送消息到指定客户端
        
        Args:
            connection_id: 连接ID
            message: 消息内容
            
        Returns:
            发送是否成功
        """
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            return await connection.send_message(message)
        return False
        
    async def broadcast(self, message: Dict[str, Any], 
                       exclude_connections: Optional[Set[str]] = None) -> int:
        """广播消息到所有客户端
        
        Args:
            message: 消息内容
            exclude_connections: 排除的连接ID集合
            
        Returns:
            成功发送的消息数量
        """
        if exclude_connections is None:
            exclude_connections = set()
            
        success_count = 0
        for connection_id, connection in self.active_connections.items():
            if connection_id not in exclude_connections:
                if await connection.send_message(message):
                    success_count += 1
                    
        return success_count
        
    async def send_to_group(self, group_name: str, message: Dict[str, Any]) -> int:
        """发送消息到指定组
        
        Args:
            group_name: 组名
            message: 消息内容
            
        Returns:
            成功发送的消息数量
        """
        if group_name not in self.connection_groups:
            return 0
            
        success_count = 0
        for connection_id in self.connection_groups[group_name]:
            if connection_id in self.active_connections:
                if await self.send_to_client(connection_id, message):
                    success_count += 1
                    
        return success_count
        
    async def join_group(self, connection_id: str, group_name: str):
        """将连接加入组
        
        Args:
            connection_id: 连接ID
            group_name: 组名
        """
        if connection_id not in self.active_connections:
            return
            
        if group_name not in self.connection_groups:
            self.connection_groups[group_name] = set()
            
        self.connection_groups[group_name].add(connection_id)
        self.active_connections[connection_id].subscriptions.add(group_name)
        
    async def leave_group(self, connection_id: str, group_name: str):
        """将连接移出组
        
        Args:
            connection_id: 连接ID
            group_name: 组名
        """
        if group_name in self.connection_groups:
            self.connection_groups[group_name].discard(connection_id)
            
        if connection_id in self.active_connections:
            self.active_connections[connection_id].subscriptions.discard(group_name)
            
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息
        
        Returns:
            统计信息
        """
        total_connections = len(self.active_connections)
        active_connections = sum(1 for conn in self.active_connections.values() 
                               if conn.is_active())
        
        client_type_stats = {}
        for conn in self.active_connections.values():
            client_type = conn.client_type.value
            client_type_stats[client_type] = client_type_stats.get(client_type, 0) + 1
            
        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "client_type_stats": client_type_stats,
            "group_count": len(self.connection_groups),
            "max_connections": self.max_connections
        }
        
    def get_connection_details(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """获取连接详情
        
        Args:
            connection_id: 连接ID
            
        Returns:
            连接详情，如果不存在返回None
        """
        if connection_id in self.active_connections:
            return self.active_connections[connection_id].to_dict()
        return None
        
    async def start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
    async def stop_cleanup_task(self):
        """停止清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_inactive_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务错误: {e}")
                
    async def _cleanup_inactive_connections(self):
        """清理非活跃连接"""
        inactive_connections = []
        now = datetime.now()
        
        for connection_id, connection in self.active_connections.items():
            # 检查心跳超时（60秒）
            if (now - connection.last_heartbeat).total_seconds() > 60:
                inactive_connections.append(connection_id)
                
        # 断开非活跃连接
        for connection_id in inactive_connections:
            logger.info(f"清理非活跃连接: {connection_id}")
            await self.disconnect(connection_id, 1001)  # 1001: Going Away


# 全局连接管理器实例
connection_manager = ConnectionManager()