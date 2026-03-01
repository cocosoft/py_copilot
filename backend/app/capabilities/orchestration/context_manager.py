"""
上下文管理器

本模块提供对话上下文和任务上下文的管理功能
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """
    消息

    Attributes:
        role: 角色 (user/assistant/system)
        content: 内容
        timestamp: 时间戳
        metadata: 元数据
    """
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """
    对话上下文

    Attributes:
        conversation_id: 对话ID
        user_id: 用户ID
        messages: 消息列表
        created_at: 创建时间
        last_activity: 最后活动时间
        metadata: 元数据
        summary: 对话摘要
    """
    conversation_id: str
    user_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        添加消息

        Args:
            role: 角色
            content: 内容
            metadata: 元数据
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.last_activity = datetime.now()

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """
        获取最近的消息

        Args:
            count: 消息数量

        Returns:
            List[Message]: 消息列表
        """
        return self.messages[-count:] if len(self.messages) > count else self.messages

    def get_messages_by_role(self, role: str) -> List[Message]:
        """
        获取指定角色的消息

        Args:
            role: 角色

        Returns:
            List[Message]: 消息列表
        """
        return [m for m in self.messages if m.role == role]

    def clear_messages(self):
        """清空消息"""
        self.messages.clear()
        self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "summary": self.summary,
            "metadata": self.metadata
        }


@dataclass
class TaskContext:
    """
    任务上下文

    Attributes:
        task_id: 任务ID
        plan_id: 计划ID
        parent_task_id: 父任务ID
        input_data: 输入数据
        output_data: 输出数据
        intermediate_results: 中间结果
        started_at: 开始时间
        completed_at: 完成时间
        status: 状态
    """
    task_id: str
    plan_id: str
    parent_task_id: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Any = None
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"

    def set_input(self, key: str, value: Any):
        """设置输入"""
        self.input_data[key] = value

    def get_input(self, key: str, default: Any = None) -> Any:
        """获取输入"""
        return self.input_data.get(key, default)

    def set_output(self, output: Any):
        """设置输出"""
        self.output_data = output
        self.completed_at = datetime.now()
        self.status = "completed"

    def add_intermediate_result(self, key: str, value: Any):
        """添加中间结果"""
        self.intermediate_results[key] = value

    def get_intermediate_result(self, key: str, default: Any = None) -> Any:
        """获取中间结果"""
        return self.intermediate_results.get(key, default)


class ContextManager:
    """
    上下文管理器

    负责管理对话上下文和任务上下文。
    支持上下文的创建、存储、检索和清理。

    Attributes:
        _conversations: 对话上下文存储
        _tasks: 任务上下文存储
        _max_history: 最大历史消息数
        _context_ttl: 上下文存活时间（秒）
    """

    def __init__(self,
                 max_history: int = 100,
                 context_ttl: int = 3600):
        """
        初始化上下文管理器

        Args:
            max_history: 最大历史消息数
            context_ttl: 上下文存活时间（秒）
        """
        self._conversations: Dict[str, ConversationContext] = {}
        self._tasks: Dict[str, TaskContext] = {}
        self._max_history = max_history
        self._context_ttl = context_ttl

        logger.info(f"上下文管理器已创建，最大历史: {max_history}, TTL: {context_ttl}s")

    def create_conversation(self,
                           conversation_id: str,
                           user_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> ConversationContext:
        """
        创建对话上下文

        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            metadata: 元数据

        Returns:
            ConversationContext: 对话上下文
        """
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata or {}
        )

        self._conversations[conversation_id] = context

        logger.debug(f"创建对话上下文: {conversation_id}")

        return context

    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        获取对话上下文

        Args:
            conversation_id: 对话ID

        Returns:
            Optional[ConversationContext]: 对话上下文
        """
        context = self._conversations.get(conversation_id)

        if context:
            # 检查是否过期
            if self._is_expired(context.last_activity):
                logger.info(f"对话上下文已过期: {conversation_id}")
                self.delete_conversation(conversation_id)
                return None

        return context

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话上下文

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 是否成功删除
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.debug(f"删除对话上下文: {conversation_id}")
            return True
        return False

    def add_message(self,
                   conversation_id: str,
                   role: str,
                   content: str,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加消息到对话

        Args:
            conversation_id: 对话ID
            role: 角色
            content: 内容
            metadata: 元数据

        Returns:
            bool: 是否成功添加
        """
        context = self.get_conversation(conversation_id)

        if not context:
            # 自动创建对话上下文
            context = self.create_conversation(conversation_id)

        context.add_message(role, content, metadata)

        # 限制历史消息数
        if len(context.messages) > self._max_history:
            context.messages = context.messages[-self._max_history:]

        return True

    def get_conversation_history(self,
                                conversation_id: str,
                                count: int = 10) -> List[Dict[str, Any]]:
        """
        获取对话历史

        Args:
            conversation_id: 对话ID
            count: 消息数量

        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        context = self.get_conversation(conversation_id)

        if not context:
            return []

        messages = context.get_recent_messages(count)

        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "metadata": m.metadata
            }
            for m in messages
        ]

    def create_task_context(self,
                           task_id: str,
                           plan_id: str,
                           parent_task_id: Optional[str] = None) -> TaskContext:
        """
        创建任务上下文

        Args:
            task_id: 任务ID
            plan_id: 计划ID
            parent_task_id: 父任务ID

        Returns:
            TaskContext: 任务上下文
        """
        context = TaskContext(
            task_id=task_id,
            plan_id=plan_id,
            parent_task_id=parent_task_id,
            started_at=datetime.now()
        )

        self._tasks[task_id] = context

        logger.debug(f"创建任务上下文: {task_id}")

        return context

    def get_task_context(self, task_id: str) -> Optional[TaskContext]:
        """
        获取任务上下文

        Args:
            task_id: 任务ID

        Returns:
            Optional[TaskContext]: 任务上下文
        """
        return self._tasks.get(task_id)

    def delete_task_context(self, task_id: str) -> bool:
        """
        删除任务上下文

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功删除
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.debug(f"删除任务上下文: {task_id}")
            return True
        return False

    def get_tasks_by_plan(self, plan_id: str) -> List[TaskContext]:
        """
        获取计划的所有任务上下文

        Args:
            plan_id: 计划ID

        Returns:
            List[TaskContext]: 任务上下文列表
        """
        return [ctx for ctx in self._tasks.values() if ctx.plan_id == plan_id]

    def _is_expired(self, last_activity: datetime) -> bool:
        """检查是否过期"""
        return (datetime.now() - last_activity).total_seconds() > self._context_ttl

    def cleanup_expired(self):
        """清理过期的上下文"""
        expired_conversations = []
        for conv_id, context in self._conversations.items():
            if self._is_expired(context.last_activity):
                expired_conversations.append(conv_id)

        for conv_id in expired_conversations:
            self.delete_conversation(conv_id)

        expired_tasks = []
        for task_id, context in self._tasks.items():
            if context.completed_at and self._is_expired(context.completed_at):
                expired_tasks.append(task_id)

        for task_id in expired_tasks:
            self.delete_task_context(task_id)

        logger.info(f"清理完成: 删除 {len(expired_conversations)} 个对话, {len(expired_tasks)} 个任务")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "conversations": {
                "total": len(self._conversations),
                "active": sum(
                    1 for c in self._conversations.values()
                    if not self._is_expired(c.last_activity)
                )
            },
            "tasks": {
                "total": len(self._tasks),
                "pending": sum(1 for t in self._tasks.values() if t.status == "pending"),
                "completed": sum(1 for t in self._tasks.values() if t.status == "completed"),
            },
            "max_history": self._max_history,
            "context_ttl": self._context_ttl
        }

    def generate_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """
        生成对话摘要

        Args:
            conversation_id: 对话ID

        Returns:
            Optional[str]: 摘要
        """
        context = self.get_conversation(conversation_id)

        if not context or len(context.messages) < 2:
            return None

        # 简化实现：提取关键信息
        user_messages = context.get_messages_by_role("user")
        assistant_messages = context.get_messages_by_role("assistant")

        summary_parts = []

        if user_messages:
            first_user = user_messages[0].content[:50]
            summary_parts.append(f"用户首次询问: {first_user}...")

        if assistant_messages:
            summary_parts.append(f"共 {len(assistant_messages)} 轮对话")

        summary = "; ".join(summary_parts)
        context.summary = summary

        return summary

    def export_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        导出对话

        Args:
            conversation_id: 对话ID

        Returns:
            Optional[Dict[str, Any]]: 导出的对话数据
        """
        context = self.get_conversation(conversation_id)

        if not context:
            return None

        return {
            "conversation_id": context.conversation_id,
            "user_id": context.user_id,
            "created_at": context.created_at.isoformat(),
            "last_activity": context.last_activity.isoformat(),
            "summary": context.summary,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in context.messages
            ],
            "metadata": context.metadata
        }

    def import_conversation(self, data: Dict[str, Any]) -> ConversationContext:
        """
        导入对话

        Args:
            data: 对话数据

        Returns:
            ConversationContext: 对话上下文
        """
        conversation_id = data["conversation_id"]

        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=data.get("user_id"),
            summary=data.get("summary"),
            metadata=data.get("metadata", {})
        )

        # 解析时间
        if "created_at" in data:
            context.created_at = datetime.fromisoformat(data["created_at"])
        if "last_activity" in data:
            context.last_activity = datetime.fromisoformat(data["last_activity"])

        # 导入消息
        for msg_data in data.get("messages", []):
            message = Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"])
            )
            context.messages.append(message)

        self._conversations[conversation_id] = context

        logger.info(f"导入对话: {conversation_id}")

        return context
