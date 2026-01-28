"""
会话管理增强模块

负责管理WebSocket连接与会话的关联关系，实现会话状态监控和连接管理。
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from uuid import uuid4
from enum import Enum

from app.websocket.connection_manager import ConnectionManager, ConnectionStatus, connection_manager

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    CLOSED = "closed"


class SessionType(Enum):
    """会话类型枚举"""
    CHAT = "chat"
    SKILL = "skill"
    FILE = "file"
    VOICE = "voice"
    SYSTEM = "system"


class Session:
    """会话类，管理会话状态和关联的连接"""
    
    def __init__(self, session_id: str, user_id: int, session_type: SessionType = SessionType.CHAT):
        """初始化会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            session_type: 会话类型
        """
        self.session_id = session_id
        self.user_id = user_id
        self.session_type = session_type
        self.status = SessionStatus.ACTIVE
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.associated_connections: Set[str] = set()  # 关联的连接ID集合
        self.metadata: Dict[str, Any] = {
            "title": f"{session_type.value.capitalize()} Session",
            "description": "",
            "tags": []
        }
        self.message_count = 0
        self.error_count = 0
        
    def add_connection(self, connection_id: str):
        """添加关联连接
        
        Args:
            connection_id: 连接ID
        """
        self.associated_connections.add(connection_id)
        self.last_activity = datetime.now()
        
    def remove_connection(self, connection_id: str):
        """移除关联连接
        
        Args:
            connection_id: 连接ID
        """
        self.associated_connections.discard(connection_id)
        
    def has_connections(self) -> bool:
        """检查会话是否有活跃连接
        
        Returns:
            是否有活跃连接
        """
        return len(self.associated_connections) > 0
        
    def get_active_connections(self) -> List[str]:
        """获取活跃连接列表
        
        Returns:
            活跃连接ID列表
        """
        active_connections = []
        for conn_id in self.associated_connections:
            conn = connection_manager.get_connection_details(conn_id)
            if conn and conn.get("status") == ConnectionStatus.CONNECTED.value:
                active_connections.append(conn_id)
        return active_connections
        
    def update_activity(self):
        """更新会话活动时间"""
        self.last_activity = datetime.now()
        
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否活跃
        
        Args:
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            会话是否活跃
        """
        return (datetime.now() - self.last_activity).total_seconds() < timeout_minutes * 60
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "session_type": self.session_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "connection_count": len(self.associated_connections),
            "active_connection_count": len(self.get_active_connections()),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "metadata": self.metadata
        }


class SessionManager:
    """会话管理器，管理所有会话和连接映射"""
    
    def __init__(self):
        """初始化会话管理器"""
        self.sessions: Dict[str, Session] = {}  # session_id -> Session
        self.user_sessions: Dict[int, Set[str]] = {}  # user_id -> session_id集合
        self.connection_sessions: Dict[str, str] = {}  # connection_id -> session_id
        self.cleanup_interval = 300  # 清理间隔（秒）
        self.session_timeout = 1800  # 会话超时时间（秒）
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def create_session(self, user_id: int, session_type: SessionType = SessionType.CHAT, 
                           metadata: Optional[Dict[str, Any]] = None) -> Session:
        """创建新会话
        
        Args:
            user_id: 用户ID
            session_type: 会话类型
            metadata: 会话元数据
            
        Returns:
            创建的会话对象
        """
        session_id = str(uuid4())
        session = Session(session_id, user_id, session_type)
        
        if metadata:
            session.metadata.update(metadata)
            
        # 添加到会话管理
        self.sessions[session_id] = session
        
        # 添加到用户会话映射
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        logger.info(f"创建新会话: {session_id}, 用户: {user_id}, 类型: {session_type.value}")
        
        return session
        
    async def associate_connection(self, session_id: str, connection_id: str) -> bool:
        """关联连接与会话
        
        Args:
            session_id: 会话ID
            connection_id: 连接ID
            
        Returns:
            关联是否成功
        """
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return False
            
        if connection_id not in connection_manager.active_connections:
            logger.warning(f"连接不存在: {connection_id}")
            return False
            
        session = self.sessions[session_id]
        session.add_connection(connection_id)
        self.connection_sessions[connection_id] = session_id
        
        logger.info(f"连接 {connection_id} 关联到会话 {session_id}")
        return True
        
    async def disassociate_connection(self, connection_id: str):
        """解除连接与会话的关联
        
        Args:
            connection_id: 连接ID
        """
        if connection_id in self.connection_sessions:
            session_id = self.connection_sessions[connection_id]
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.remove_connection(connection_id)
                
            del self.connection_sessions[connection_id]
            
            logger.info(f"连接 {connection_id} 从会话解除关联")
            
    async def get_session_by_connection(self, connection_id: str) -> Optional[Session]:
        """根据连接ID获取会话
        
        Args:
            connection_id: 连接ID
            
        Returns:
            会话对象，如果不存在返回None
        """
        if connection_id in self.connection_sessions:
            session_id = self.connection_sessions[connection_id]
            return self.sessions.get(session_id)
        return None
        
    async def get_user_sessions(self, user_id: int) -> List[Session]:
        """获取用户的所有会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户会话列表
        """
        if user_id not in self.user_sessions:
            return []
            
        sessions = []
        for session_id in self.user_sessions[user_id]:
            if session_id in self.sessions:
                sessions.append(self.sessions[session_id])
                
        return sessions
        
    async def get_active_sessions(self, user_id: Optional[int] = None) -> List[Session]:
        """获取活跃会话
        
        Args:
            user_id: 用户ID，如果为None则获取所有活跃会话
            
        Returns:
            活跃会话列表
        """
        active_sessions = []
        
        if user_id:
            sessions = await self.get_user_sessions(user_id)
        else:
            sessions = list(self.sessions.values())
            
        for session in sessions:
            if session.status == SessionStatus.ACTIVE and session.is_active():
                active_sessions.append(session)
                
        return active_sessions
        
    async def close_session(self, session_id: str):
        """关闭会话
        
        Args:
            session_id: 会话ID
        """
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        session.status = SessionStatus.CLOSED
        
        # 解除所有关联连接
        for connection_id in list(session.associated_connections):
            await self.disassociate_connection(connection_id)
            
        # 从用户会话映射中移除
        if session.user_id in self.user_sessions:
            self.user_sessions[session.user_id].discard(session_id)
            
        logger.info(f"会话已关闭: {session_id}")
        
    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> int:
        """发送消息到会话的所有连接
        
        Args:
            session_id: 会话ID
            message: 消息内容
            
        Returns:
            成功发送的消息数量
        """
        if session_id not in self.sessions:
            return 0
            
        session = self.sessions[session_id]
        success_count = 0
        
        for connection_id in session.get_active_connections():
            if await connection_manager.send_to_client(connection_id, message):
                success_count += 1
                
        return success_count
        
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息
        
        Returns:
            会话统计信息
        """
        total_sessions = len(self.sessions)
        active_sessions = len([s for s in self.sessions.values() 
                             if s.status == SessionStatus.ACTIVE and s.is_active()])
        
        session_type_stats = {}
        for session in self.sessions.values():
            session_type = session.session_type.value
            session_type_stats[session_type] = session_type_stats.get(session_type, 0) + 1
            
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "session_type_stats": session_type_stats,
            "user_count": len(self.user_sessions),
            "connection_mappings": len(self.connection_sessions)
        }
        
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
                await self._cleanup_inactive_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"会话清理任务错误: {e}")
                
    async def _cleanup_inactive_sessions(self):
        """清理非活跃会话"""
        inactive_sessions = []
        now = datetime.now()
        
        for session_id, session in self.sessions.items():
            # 检查会话超时（30分钟）
            if (now - session.last_activity).total_seconds() > self.session_timeout:
                inactive_sessions.append(session_id)
                
        # 关闭非活跃会话
        for session_id in inactive_sessions:
            logger.info(f"清理非活跃会话: {session_id}")
            await self.close_session(session_id)


# 全局会话管理器实例
session_manager = SessionManager()