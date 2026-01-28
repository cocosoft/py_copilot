"""
消息路由引擎

负责实时消息的路由、广播和队列管理，支持多种消息分发策略。
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Callable, Awaitable
from enum import Enum
from uuid import uuid4

from .connection_manager import ConnectionManager, connection_manager
from .session_manager import SessionManager, session_manager

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """消息路由策略枚举"""
    BROADCAST = "broadcast"  # 广播到所有连接
    SESSION = "session"      # 路由到指定会话
    GROUP = "group"          # 路由到指定组
    USER = "user"            # 路由到指定用户
    DIRECT = "direct"        # 直接路由到指定连接


class MessagePriority(Enum):
    """消息优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageQueueItem:
    """消息队列项"""
    
    def __init__(self, message: Dict[str, Any], routing_strategy: RoutingStrategy, 
                 target: Optional[str] = None, priority: MessagePriority = MessagePriority.NORMAL):
        """初始化消息队列项
        
        Args:
            message: 消息内容
            routing_strategy: 路由策略
            target: 目标标识（会话ID、组名、用户ID等）
            priority: 消息优先级
        """
        self.message_id = str(uuid4())
        self.message = message
        self.routing_strategy = routing_strategy
        self.target = target
        self.priority = priority
        self.created_at = datetime.now()
        self.attempts = 0
        self.max_attempts = 3
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message_id": self.message_id,
            "message": self.message,
            "routing_strategy": self.routing_strategy.value,
            "target": self.target,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "attempts": self.attempts
        }


class MessageRouter:
    """消息路由引擎"""
    
    def __init__(self):
        """初始化消息路由引擎"""
        self.connection_manager = connection_manager
        self.session_manager = session_manager
        self.message_queue: List[MessageQueueItem] = []
        self.is_processing = False
        self.processing_interval = 0.1  # 处理间隔（秒）
        self.max_queue_size = 10000     # 最大队列大小
        self._processing_task: Optional[asyncio.Task] = None
        
    async def route_message(self, message: Dict[str, Any], routing_strategy: RoutingStrategy,
                          target: Optional[str] = None, priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """路由消息
        
        Args:
            message: 消息内容
            routing_strategy: 路由策略
            target: 目标标识
            priority: 消息优先级
            
        Returns:
            消息ID
        """
        # 检查队列大小
        if len(self.message_queue) >= self.max_queue_size:
            raise Exception("消息队列已满")
            
        # 创建消息队列项
        queue_item = MessageQueueItem(message, routing_strategy, target, priority)
        
        # 根据优先级插入队列
        await self._insert_to_queue(queue_item)
        
        # 启动处理任务（如果未启动）
        await self.start_processing()
        
        logger.info(f"消息已路由到队列: {queue_item.message_id}, 策略: {routing_strategy.value}")
        
        return queue_item.message_id
        
    async def _insert_to_queue(self, queue_item: MessageQueueItem):
        """将消息插入队列（按优先级排序）
        
        Args:
            queue_item: 消息队列项
        """
        priority_order = {
            MessagePriority.URGENT: 0,
            MessagePriority.HIGH: 1,
            MessagePriority.NORMAL: 2,
            MessagePriority.LOW: 3
        }
        
        # 找到插入位置
        insert_index = 0
        for i, item in enumerate(self.message_queue):
            if priority_order[item.priority] <= priority_order[queue_item.priority]:
                insert_index = i + 1
            else:
                break
                
        self.message_queue.insert(insert_index, queue_item)
        
    async def start_processing(self):
        """启动消息处理任务"""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._processing_loop())
            
    async def stop_processing(self):
        """停止消息处理任务"""
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
                
    async def _processing_loop(self):
        """消息处理循环"""
        while True:
            try:
                await asyncio.sleep(self.processing_interval)
                await self._process_queue()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"消息处理循环错误: {e}")
                
    async def _process_queue(self):
        """处理消息队列"""
        if not self.message_queue or self.is_processing:
            return
            
        self.is_processing = True
        
        try:
            # 处理队列中的消息（限制每次处理数量）
            processed_count = 0
            max_batch_size = 100
            
            while self.message_queue and processed_count < max_batch_size:
                queue_item = self.message_queue.pop(0)
                await self._process_message(queue_item)
                processed_count += 1
                
            if processed_count > 0:
                logger.debug(f"处理了 {processed_count} 条消息")
                
        except Exception as e:
            logger.error(f"处理消息队列错误: {e}")
        finally:
            self.is_processing = False
            
    async def _process_message(self, queue_item: MessageQueueItem):
        """处理单个消息
        
        Args:
            queue_item: 消息队列项
        """
        try:
            # 根据路由策略分发消息
            success_count = 0
            
            if queue_item.routing_strategy == RoutingStrategy.BROADCAST:
                success_count = await self._broadcast_message(queue_item.message)
                
            elif queue_item.routing_strategy == RoutingStrategy.SESSION:
                if queue_item.target:
                    success_count = await self._route_to_session(queue_item.target, queue_item.message)
                
            elif queue_item.routing_strategy == RoutingStrategy.GROUP:
                if queue_item.target:
                    success_count = await self._route_to_group(queue_item.target, queue_item.message)
                    
            elif queue_item.routing_strategy == RoutingStrategy.USER:
                if queue_item.target:
                    success_count = await self._route_to_user(int(queue_item.target), queue_item.message)
                    
            elif queue_item.routing_strategy == RoutingStrategy.DIRECT:
                if queue_item.target:
                    success = await self.connection_manager.send_to_client(queue_item.target, queue_item.message)
                    success_count = 1 if success else 0
                    
            logger.info(f"消息 {queue_item.message_id} 分发完成，成功发送: {success_count}")
            
        except Exception as e:
            logger.error(f"处理消息 {queue_item.message_id} 错误: {e}")
            
            # 重试逻辑
            queue_item.attempts += 1
            if queue_item.attempts < queue_item.max_attempts:
                await self._insert_to_queue(queue_item)
            else:
                logger.error(f"消息 {queue_item.message_id} 重试次数已达上限")
                
    async def _broadcast_message(self, message: Dict[str, Any]) -> int:
        """广播消息到所有连接
        
        Args:
            message: 消息内容
            
        Returns:
            成功发送的消息数量
        """
        return await self.connection_manager.broadcast(message)
        
    async def _route_to_session(self, session_id: str, message: Dict[str, Any]) -> int:
        """路由消息到指定会话
        
        Args:
            session_id: 会话ID
            message: 消息内容
            
        Returns:
            成功发送的消息数量
        """
        return await self.session_manager.send_to_session(session_id, message)
        
    async def _route_to_group(self, group_name: str, message: Dict[str, Any]) -> int:
        """路由消息到指定组
        
        Args:
            group_name: 组名
            message: 消息内容
            
        Returns:
            成功发送的消息数量
        """
        return await self.connection_manager.send_to_group(group_name, message)
        
    async def _route_to_user(self, user_id: int, message: Dict[str, Any]) -> int:
        """路由消息到指定用户的所有会话
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            成功发送的消息数量
        """
        success_count = 0
        user_sessions = await self.session_manager.get_user_sessions(user_id)
        
        for session in user_sessions:
            count = await self.session_manager.send_to_session(session.session_id, message)
            success_count += count
            
        return success_count
        
    async def broadcast_to_all(self, message: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """广播消息到所有连接（便捷方法）
        
        Args:
            message: 消息内容
            priority: 消息优先级
            
        Returns:
            消息ID
        """
        return await self.route_message(message, RoutingStrategy.BROADCAST, priority=priority)
        
    async def send_to_session(self, session_id: str, message: Dict[str, Any], 
                            priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """发送消息到指定会话（便捷方法）
        
        Args:
            session_id: 会话ID
            message: 消息内容
            priority: 消息优先级
            
        Returns:
            消息ID
        """
        return await self.route_message(message, RoutingStrategy.SESSION, session_id, priority)
        
    async def send_to_group(self, group_name: str, message: Dict[str, Any], 
                          priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """发送消息到指定组（便捷方法）
        
        Args:
            group_name: 组名
            message: 消息内容
            priority: 消息优先级
            
        Returns:
            消息ID
        """
        return await self.route_message(message, RoutingStrategy.GROUP, group_name, priority)
        
    async def send_to_user(self, user_id: int, message: Dict[str, Any], 
                         priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """发送消息到指定用户（便捷方法）
        
        Args:
            user_id: 用户ID
            message: 消息内容
            priority: 消息优先级
            
        Returns:
            消息ID
        """
        return await self.route_message(message, RoutingStrategy.USER, str(user_id), priority)
        
    async def send_direct(self, connection_id: str, message: Dict[str, Any], 
                        priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """直接发送消息到指定连接（便捷方法）
        
        Args:
            connection_id: 连接ID
            message: 消息内容
            priority: 消息优先级
            
        Returns:
            消息ID
        """
        return await self.route_message(message, RoutingStrategy.DIRECT, connection_id, priority)
        
    def get_queue_stats(self) -> Dict[str, Any]:
        """获取消息队列统计信息
        
        Returns:
            队列统计信息
        """
        priority_stats = {}
        for item in self.message_queue:
            priority = item.priority.value
            priority_stats[priority] = priority_stats.get(priority, 0) + 1
            
        return {
            "queue_size": len(self.message_queue),
            "max_queue_size": self.max_queue_size,
            "priority_stats": priority_stats,
            "is_processing": self.is_processing
        }


# 全局消息路由引擎实例
message_router = MessageRouter()