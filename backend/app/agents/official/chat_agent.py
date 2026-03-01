"""
聊天助手

通用对话智能体，可以进行日常聊天、回答问题、提供建议等
"""

import logging
from typing import Any, Optional

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class ChatAgent(BaseAgent):
    """
    聊天助手

    通用对话智能体，特点：
    - 日常聊天对话
    - 回答问题
    - 提供建议
    - 友好专业的交流

    Attributes:
        config: Agent配置
    """

    DEFAULT_CONFIG = AgentConfig(
        name="聊天助手",
        description="通用对话智能体，可以进行日常聊天、回答问题、提供建议等",
        version="1.0.0",
        author="System",
        tags=["chat", "conversation", "general", "assistant"],
        priority=AgentPriority.NORMAL,
        required_capabilities=["llm", "conversation"],
        optional_capabilities=["memory", "context_awareness"],
        metadata={
            "template_category": "chat",
            "agent_type": "single",
            "is_official": True,
            "icon": "chat_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        初始化聊天助手

        Args:
            config: Agent配置，如果为None使用默认配置
        """
        super().__init__(config or self.DEFAULT_CONFIG)
        self._system_prompt = (
            "你是一个友好、专业的AI助手。"
            "请用简洁、清晰的语言回答用户的问题。"
            "如果用户的问题不够明确，请主动询问以获取更多信息。"
        )

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """
        执行聊天助手

        Args:
            input_data: 输入数据（用户消息）
            context: 执行上下文

        Returns:
            AgentResult: 执行结果
        """
        logger.info(f"聊天助手执行: {str(input_data)[:50]}...")

        try:
            # 解析输入
            if isinstance(input_data, str):
                user_message = input_data
            elif isinstance(input_data, dict):
                user_message = input_data.get("message", "")
            else:
                user_message = str(input_data)

            if not user_message.strip():
                return AgentResult(
                    success=False,
                    error="输入消息不能为空"
                )

            # 构建对话上下文
            conversation_history = []
            if context and context.history:
                conversation_history = context.history

            # 模拟LLM调用（实际应该调用LLM服务）
            response = await self._generate_response(
                user_message,
                conversation_history
            )

            return AgentResult(
                success=True,
                output={
                    "message": response,
                    "role": "assistant",
                    "type": "chat"
                },
                metadata={
                    "agent_name": self.name,
                    "input_length": len(user_message),
                    "response_length": len(response)
                }
            )

        except Exception as e:
            logger.error(f"聊天助手执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                error=str(e)
            )

    def can_handle(self, input_data: Any) -> float:
        """
        判断是否能处理输入

        Args:
            input_data: 输入数据

        Returns:
            float: 置信度（0-1）
        """
        # 聊天助手是通用智能体，可以处理大多数文本输入
        if isinstance(input_data, str):
            return 0.6  # 基础置信度

        if isinstance(input_data, dict):
            # 如果明确指定了聊天类型
            if input_data.get("type") == "chat":
                return 0.95
            if input_data.get("agent_type") == "chat":
                return 0.95
            if "message" in input_data:
                return 0.7

        return 0.5

    async def _generate_response(self,
                                user_message: str,
                                conversation_history: list) -> str:
        """
        生成回复

        Args:
            user_message: 用户消息
            conversation_history: 对话历史

        Returns:
            str: 生成的回复
        """
        # 这里应该调用实际的LLM服务
        # 目前返回模拟响应

        greetings = ["你好", "您好", "hello", "hi"]
        user_lower = user_message.lower()

        # 简单的关键词匹配
        if any(g in user_lower for g in greetings):
            return f"你好！我是{self.name}，很高兴为您服务。有什么我可以帮助您的吗？"

        if "?" in user_message or "？" in user_message:
            return f"关于您的问题：'{user_message}'，我需要更多信息来给出准确的回答。"

        return f"收到您的消息：'{user_message}'。作为{self.name}，我会尽力帮助您。"
