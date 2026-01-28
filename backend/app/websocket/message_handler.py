"""
WebSocket消息处理器

负责处理WebSocket消息的解析、验证、路由和处理。
"""
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, ValidationError

from .connection_manager import ConnectionManager, connection_manager
from .session_manager import SessionManager, SessionType, session_manager

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举"""
    HEARTBEAT = "heartbeat"
    CHAT_MESSAGE = "chat_message"
    SKILL_EXECUTION = "skill_execution"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    STATUS = "status"
    ERROR = "error"
    NOTIFICATION = "notification"
    SESSION_CREATE = "session_create"
    SESSION_JOIN = "session_join"
    SESSION_LEAVE = "session_leave"
    SESSION_CLOSE = "session_close"


class MessageSchema(BaseModel):
    """消息基础模型"""
    type: str
    id: Optional[str] = None
    timestamp: Optional[str] = None
    

class HeartbeatMessage(MessageSchema):
    """心跳消息模型"""
    type: str = MessageType.HEARTBEAT.value
    client_info: Optional[Dict[str, Any]] = None


class ChatMessage(MessageSchema):
    """聊天消息模型"""
    type: str = MessageType.CHAT_MESSAGE.value
    conversation_id: int
    user_id: int
    message: str
    enable_streaming: bool = True
    enable_memory_enhancement: bool = True


class SkillExecutionMessage(MessageSchema):
    """技能执行消息模型"""
    type: str = MessageType.SKILL_EXECUTION.value
    skill_id: str
    parameters: Dict[str, Any]
    user_id: int


class SubscribeMessage(MessageSchema):
    """订阅消息模型"""
    type: str = MessageType.SUBSCRIBE.value
    channels: list[str]


class UnsubscribeMessage(MessageSchema):
    """取消订阅消息模型"""
    type: str = MessageType.UNSUBSCRIBE.value
    channels: list[str]


class StatusMessage(MessageSchema):
    """状态消息模型"""
    type: str = MessageType.STATUS.value
    status: str
    details: Optional[Dict[str, Any]] = None


class ErrorMessage(MessageSchema):
    """错误消息模型"""
    type: str = MessageType.ERROR.value
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None


class NotificationMessage(MessageSchema):
    """通知消息模型"""
    type: str = MessageType.NOTIFICATION.value
    title: str
    message: str
    level: str = "info"  # info, warning, error, success
    metadata: Optional[Dict[str, Any]] = None


class SessionCreateMessage(MessageSchema):
    """会话创建消息模型"""
    type: str = MessageType.SESSION_CREATE.value
    user_id: int
    session_type: str = SessionType.CHAT.value
    metadata: Optional[Dict[str, Any]] = None


class SessionJoinMessage(MessageSchema):
    """会话加入消息模型"""
    type: str = MessageType.SESSION_JOIN.value
    session_id: str


class SessionLeaveMessage(MessageSchema):
    """会话离开消息模型"""
    type: str = MessageType.SESSION_LEAVE.value
    session_id: str


class SessionCloseMessage(MessageSchema):
    """会话关闭消息模型"""
    type: str = MessageType.SESSION_CLOSE.value
    session_id: str


class MessageHandler:
    """WebSocket消息处理器"""
    
    def __init__(self, connection_manager: ConnectionManager):
        """初始化消息处理器
        
        Args:
            connection_manager: 连接管理器实例
        """
        self.connection_manager = connection_manager
        self.message_handlers: Dict[str, Callable] = {
            MessageType.HEARTBEAT.value: self._handle_heartbeat,
            MessageType.CHAT_MESSAGE.value: self._handle_chat_message,
            MessageType.SKILL_EXECUTION.value: self._handle_skill_execution,
            MessageType.SUBSCRIBE.value: self._handle_subscribe,
            MessageType.UNSUBSCRIBE.value: self._handle_unsubscribe,
            MessageType.STATUS.value: self._handle_status,
            MessageType.SESSION_CREATE.value: self._handle_session_create,
            MessageType.SESSION_JOIN.value: self._handle_session_join,
            MessageType.SESSION_LEAVE.value: self._handle_session_leave,
            MessageType.SESSION_CLOSE.value: self._handle_session_close,
        }
        
    async def handle_message(self, connection_id: str, raw_message: str) -> bool:
        """处理WebSocket消息
        
        Args:
            connection_id: 连接ID
            raw_message: 原始消息字符串
            
        Returns:
            处理是否成功
        """
        try:
            # 解析消息
            message_data = json.loads(raw_message)
            
            # 验证消息格式
            if not isinstance(message_data, dict) or "type" not in message_data:
                await self._send_error(connection_id, "invalid_message_format", 
                                     "消息格式无效")
                return False
                
            message_type = message_data.get("type")
            
            # 查找对应的处理器
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                await handler(connection_id, message_data)
                return True
            else:
                await self._send_error(connection_id, "unknown_message_type", 
                                     f"未知的消息类型: {message_type}")
                return False
                
        except json.JSONDecodeError:
            await self._send_error(connection_id, "invalid_json", 
                                 "JSON格式无效")
            return False
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            await self._send_error(connection_id, "internal_error", 
                                 "内部服务器错误")
            return False
            
    async def _handle_heartbeat(self, connection_id: str, message_data: Dict[str, Any]):
        """处理心跳消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            heartbeat_msg = HeartbeatMessage(**message_data)
            
            # 更新连接心跳
            connection = self.connection_manager.active_connections.get(connection_id)
            if connection:
                connection.update_heartbeat()
                
                # 发送心跳响应
                await self.connection_manager.send_to_client(connection_id, {
                    "type": "heartbeat_response",
                    "id": heartbeat_msg.id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "ok"
                })
                
                logger.debug(f"心跳消息处理完成: {connection_id}")
                
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_heartbeat_message", 
                                 f"心跳消息格式无效: {e}")
            
    async def _handle_chat_message(self, connection_id: str, message_data: Dict[str, Any]):
        """处理聊天消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            chat_msg = ChatMessage(**message_data)
            
            # 获取连接信息
            connection = self.connection_manager.active_connections.get(connection_id)
            if not connection:
                await self._send_error(connection_id, "connection_not_found", 
                                     "连接不存在")
                return
                
            # 发送确认消息
            await self.connection_manager.send_to_client(connection_id, {
                "type": "chat_message_ack",
                "id": chat_msg.id,
                "timestamp": datetime.now().isoformat(),
                "status": "processing"
            })
            
            # 处理聊天消息（这里可以集成现有的聊天服务）
            # 暂时模拟处理
            await self._simulate_chat_processing(connection_id, chat_msg)
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_chat_message", 
                                 f"聊天消息格式无效: {e}")
            
    async def _handle_skill_execution(self, connection_id: str, message_data: Dict[str, Any]):
        """处理技能执行消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            skill_msg = SkillExecutionMessage(**message_data)
            
            # 获取连接信息
            connection = self.connection_manager.active_connections.get(connection_id)
            if not connection:
                await self._send_error(connection_id, "connection_not_found", 
                                     "连接不存在")
                return
                
            # 发送确认消息
            await self.connection_manager.send_to_client(connection_id, {
                "type": "skill_execution_ack",
                "id": skill_msg.id,
                "timestamp": datetime.now().isoformat(),
                "status": "processing"
            })
            
            # 处理技能执行（这里可以集成现有的技能服务）
            # 暂时模拟处理
            await self._simulate_skill_execution(connection_id, skill_msg)
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_skill_message", 
                                 f"技能执行消息格式无效: {e}")
            
    async def _handle_subscribe(self, connection_id: str, message_data: Dict[str, Any]):
        """处理订阅消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            subscribe_msg = SubscribeMessage(**message_data)
            
            # 获取连接信息
            connection = self.connection_manager.active_connections.get(connection_id)
            if not connection:
                await self._send_error(connection_id, "connection_not_found", 
                                     "连接不存在")
                return
                
            # 加入订阅组
            for channel in subscribe_msg.channels:
                await self.connection_manager.join_group(connection_id, channel)
                
            # 发送订阅确认
            await self.connection_manager.send_to_client(connection_id, {
                "type": "subscribe_ack",
                "id": subscribe_msg.id,
                "timestamp": datetime.now().isoformat(),
                "channels": subscribe_msg.channels,
                "status": "subscribed"
            })
            
            logger.info(f"客户端 {connection.client_id} 订阅了频道: {subscribe_msg.channels}")
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_subscribe_message", 
                                 f"订阅消息格式无效: {e}")
            
    async def _handle_unsubscribe(self, connection_id: str, message_data: Dict[str, Any]):
        """处理取消订阅消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            unsubscribe_msg = UnsubscribeMessage(**message_data)
            
            # 获取连接信息
            connection = self.connection_manager.active_connections.get(connection_id)
            if not connection:
                await self._send_error(connection_id, "connection_not_found", 
                                     "连接不存在")
                return
                
            # 退出订阅组
            for channel in unsubscribe_msg.channels:
                await self.connection_manager.leave_group(connection_id, channel)
                
            # 发送取消订阅确认
            await self.connection_manager.send_to_client(connection_id, {
                "type": "unsubscribe_ack",
                "id": unsubscribe_msg.id,
                "timestamp": datetime.now().isoformat(),
                "channels": unsubscribe_msg.channels,
                "status": "unsubscribed"
            })
            
            logger.info(f"客户端 {connection.client_id} 取消了频道订阅: {unsubscribe_msg.channels}")
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_unsubscribe_message", 
                                 f"取消订阅消息格式无效: {e}")
            
    async def _handle_status(self, connection_id: str, message_data: Dict[str, Any]):
        """处理状态消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            status_msg = StatusMessage(**message_data)
            
            # 获取连接信息
            connection = self.connection_manager.active_connections.get(connection_id)
            if not connection:
                await self._send_error(connection_id, "connection_not_found", 
                                     "连接不存在")
                return
                
            # 发送状态响应
            await self.connection_manager.send_to_client(connection_id, {
                "type": "status_response",
                "id": status_msg.id,
                "timestamp": datetime.now().isoformat(),
                "connection_stats": self.connection_manager.get_connection_stats(),
                "connection_details": connection.to_dict(),
                "session_stats": session_manager.get_session_stats()
            })
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_status_message", 
                                 f"状态消息格式无效: {e}")
            
    async def _handle_session_create(self, connection_id: str, message_data: Dict[str, Any]):
        """处理会话创建消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            session_create_msg = SessionCreateMessage(**message_data)
            
            # 获取连接信息
            connection = self.connection_manager.active_connections.get(connection_id)
            if not connection:
                await self._send_error(connection_id, "connection_not_found", 
                                     "连接不存在")
                return
                
            # 创建会话
            session_type = SessionType(session_create_msg.session_type)
            session = await session_manager.create_session(
                user_id=session_create_msg.user_id,
                session_type=session_type,
                metadata=session_create_msg.metadata
            )
            
            # 关联连接与会话
            await session_manager.associate_connection(session.session_id, connection_id)
            
            # 发送创建成功响应
            await self.connection_manager.send_to_client(connection_id, {
                "type": "session_create_response",
                "id": session_create_msg.id,
                "timestamp": datetime.now().isoformat(),
                "session_id": session.session_id,
                "status": "created"
            })
            
            logger.info(f"会话创建成功: {session.session_id}, 用户: {session_create_msg.user_id}")
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_session_create_message", 
                                 f"会话创建消息格式无效: {e}")
        except ValueError as e:
            await self._send_error(connection_id, "invalid_session_type", 
                                 f"无效的会话类型: {e}")
            
    async def _handle_session_join(self, connection_id: str, message_data: Dict[str, Any]):
        """处理会话加入消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            session_join_msg = SessionJoinMessage(**message_data)
            
            # 获取连接信息
            connection = self.connection_manager.active_connections.get(connection_id)
            if not connection:
                await self._send_error(connection_id, "connection_not_found", 
                                     "连接不存在")
                return
                
            # 关联连接与会话
            success = await session_manager.associate_connection(
                session_join_msg.session_id, 
                connection_id
            )
            
            if not success:
                await self._send_error(connection_id, "session_not_found", 
                                     f"会话不存在: {session_join_msg.session_id}")
                return
                
            # 发送加入成功响应
            await self.connection_manager.send_to_client(connection_id, {
                "type": "session_join_response",
                "id": session_join_msg.id,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_join_msg.session_id,
                "status": "joined"
            })
            
            logger.info(f"连接 {connection_id} 加入会话: {session_join_msg.session_id}")
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_session_join_message", 
                                 f"会话加入消息格式无效: {e}")
            
    async def _handle_session_leave(self, connection_id: str, message_data: Dict[str, Any]):
        """处理会话离开消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            session_leave_msg = SessionLeaveMessage(**message_data)
            
            # 解除连接与会话的关联
            await session_manager.disassociate_connection(connection_id)
            
            # 发送离开成功响应
            await self.connection_manager.send_to_client(connection_id, {
                "type": "session_leave_response",
                "id": session_leave_msg.id,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_leave_msg.session_id,
                "status": "left"
            })
            
            logger.info(f"连接 {connection_id} 离开会话: {session_leave_msg.session_id}")
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_session_leave_message", 
                                 f"会话离开消息格式无效: {e}")
            
    async def _handle_session_close(self, connection_id: str, message_data: Dict[str, Any]):
        """处理会话关闭消息
        
        Args:
            connection_id: 连接ID
            message_data: 消息数据
        """
        try:
            # 验证消息格式
            session_close_msg = SessionCloseMessage(**message_data)
            
            # 获取连接信息
            connection = self.connection_manager.active_connections.get(connection_id)
            if not connection:
                await self._send_error(connection_id, "connection_not_found", 
                                     "连接不存在")
                return
                
            # 关闭会话
            await session_manager.close_session(session_close_msg.session_id)
            
            # 发送关闭成功响应
            await self.connection_manager.send_to_client(connection_id, {
                "type": "session_close_response",
                "id": session_close_msg.id,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_close_msg.session_id,
                "status": "closed"
            })
            
            logger.info(f"会话已关闭: {session_close_msg.session_id}")
            
        except ValidationError as e:
            await self._send_error(connection_id, "invalid_session_close_message", 
                                 f"会话关闭消息格式无效: {e}")
            
    async def _simulate_chat_processing(self, connection_id: str, chat_msg: ChatMessage):
        """模拟聊天处理（临时实现）
        
        Args:
            connection_id: 连接ID
            chat_msg: 聊天消息
        """
        # 模拟处理延迟
        import asyncio
        await asyncio.sleep(0.1)
        
        # 发送处理结果
        await self.connection_manager.send_to_client(connection_id, {
            "type": "chat_message_result",
            "id": chat_msg.id,
            "timestamp": datetime.now().isoformat(),
            "response": f"已收到您的消息: {chat_msg.message}",
            "status": "completed"
        })
        
    async def _simulate_skill_execution(self, connection_id: str, skill_msg: SkillExecutionMessage):
        """模拟技能执行（临时实现）
        
        Args:
            connection_id: 连接ID
            skill_msg: 技能执行消息
        """
        # 模拟处理延迟
        import asyncio
        await asyncio.sleep(0.1)
        
        # 发送执行结果
        await self.connection_manager.send_to_client(connection_id, {
            "type": "skill_execution_result",
            "id": skill_msg.id,
            "timestamp": datetime.now().isoformat(),
            "skill_id": skill_msg.skill_id,
            "result": f"技能 {skill_msg.skill_id} 执行完成",
            "status": "completed"
        })
        
    async def _send_error(self, connection_id: str, error_code: str, error_message: str):
        """发送错误消息
        
        Args:
            connection_id: 连接ID
            error_code: 错误代码
            error_message: 错误消息
        """
        error_msg = ErrorMessage(
            type=MessageType.ERROR.value,
            error_code=error_code,
            error_message=error_message,
            timestamp=datetime.now().isoformat()
        )
        
        await self.connection_manager.send_to_client(connection_id, error_msg.dict())
        
    async def send_notification(self, connection_id: str, title: str, message: str, 
                              level: str = "info", metadata: Optional[Dict[str, Any]] = None):
        """发送通知消息
        
        Args:
            connection_id: 连接ID
            title: 通知标题
            message: 通知内容
            level: 通知级别
            metadata: 元数据
        """
        notification_msg = NotificationMessage(
            type=MessageType.NOTIFICATION.value,
            title=title,
            message=message,
            level=level,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )
        
        await self.connection_manager.send_to_client(connection_id, notification_msg.dict())
        
    async def broadcast_notification(self, title: str, message: str, 
                                   level: str = "info", metadata: Optional[Dict[str, Any]] = None):
        """广播通知消息
        
        Args:
            title: 通知标题
            message: 通知内容
            level: 通知级别
            metadata: 元数据
        """
        notification_msg = NotificationMessage(
            type=MessageType.NOTIFICATION.value,
            title=title,
            message=message,
            level=level,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )
        
        await self.connection_manager.broadcast(notification_msg.dict())


# 全局消息处理器实例
message_handler = MessageHandler(connection_manager)