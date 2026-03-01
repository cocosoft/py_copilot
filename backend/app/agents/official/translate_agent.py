"""
翻译专家

专业的多语言翻译智能体，支持各种语言之间的互译
"""

import logging
import re
from typing import Any, Optional, Dict, List

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class TranslateAgent(BaseAgent):
    """
    翻译专家

    专业的多语言翻译智能体，特点：
    - 支持多种语言互译
    - 保持原文语气和风格
    - 专业术语翻译
    - 自动检测语言

    Attributes:
        config: Agent配置
    """

    DEFAULT_CONFIG = AgentConfig(
        name="翻译专家",
        description="专业的多语言翻译智能体，支持各种语言之间的互译",
        version="1.0.0",
        author="System",
        tags=["translate", "translation", "language", "multilingual"],
        priority=AgentPriority.NORMAL,
        required_capabilities=["llm", "translation"],
        optional_capabilities=["language_detection", "terminology"],
        metadata={
            "template_category": "translation",
            "agent_type": "single",
            "is_official": True,
            "icon": "translate_agent.svg",
            "supported_languages": [
                "zh", "en", "ja", "ko", "fr", "de", "es", "ru", "ar"
            ]
        }
    )

    # 语言代码映射
    LANGUAGE_NAMES = {
        "zh": "中文",
        "en": "英语",
        "ja": "日语",
        "ko": "韩语",
        "fr": "法语",
        "de": "德语",
        "es": "西班牙语",
        "ru": "俄语",
        "ar": "阿拉伯语"
    }

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        初始化翻译专家

        Args:
            config: Agent配置，如果为None使用默认配置
        """
        super().__init__(config or self.DEFAULT_CONFIG)
        self._system_prompt = (
            "你是一位专业的翻译专家。"
            "请将用户提供的文本准确翻译成目标语言，保持原文的语气和风格。"
            "对于专业术语，请提供适当的翻译。"
            "如果用户没有指定目标语言，请询问用户需要翻译成哪种语言。"
        )

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """
        执行翻译

        Args:
            input_data: 输入数据（包含文本和翻译参数）
            context: 执行上下文

        Returns:
            AgentResult: 执行结果
        """
        logger.info(f"翻译专家执行: {str(input_data)[:50]}...")

        try:
            # 解析输入
            if isinstance(input_data, str):
                text = input_data
                source_lang = None
                target_lang = "zh"  # 默认翻译成中文
            elif isinstance(input_data, dict):
                text = input_data.get("text", "")
                source_lang = input_data.get("source_lang")
                target_lang = input_data.get("target_lang", "zh")
            else:
                text = str(input_data)
                source_lang = None
                target_lang = "zh"

            if not text.strip():
                return AgentResult(
                    success=False,
                    error="翻译文本不能为空"
                )

            # 自动检测源语言（简化版）
            if not source_lang:
                source_lang = self._detect_language(text)

            # 执行翻译
            translation = await self._translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang
            )

            return AgentResult(
                success=True,
                output={
                    "original_text": text,
                    "translated_text": translation,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "source_lang_name": self.LANGUAGE_NAMES.get(source_lang, source_lang),
                    "target_lang_name": self.LANGUAGE_NAMES.get(target_lang, target_lang)
                },
                metadata={
                    "agent_name": self.name,
                    "text_length": len(text),
                    "translation_length": len(translation)
                }
            )

        except Exception as e:
            logger.error(f"翻译专家执行失败: {e}", exc_info=True)
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
        if isinstance(input_data, dict):
            if input_data.get("type") == "translation":
                return 1.0
            if input_data.get("agent_type") == "translation":
                return 1.0
            if "text" in input_data and ("target_lang" in input_data or "source_lang" in input_data):
                return 0.9

        if isinstance(input_data, str):
            # 检查是否包含翻译相关关键词
            keywords = ["翻译", "translate", "翻成", "译成", "翻译成"]
            input_lower = input_data.lower()
            for keyword in keywords:
                if keyword in input_lower:
                    return 0.85

        return 0.2

    def _detect_language(self, text: str) -> str:
        """
        检测文本语言（简化版）

        Args:
            text: 文本内容

        Returns:
            str: 语言代码
        """
        # 简单的语言检测逻辑
        if re.search(r'[\u4e00-\u9fff]', text):
            return "zh"
        elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return "ja"
        elif re.search(r'[\uac00-\ud7af]', text):
            return "ko"
        elif re.search(r'[\u0600-\u06ff]', text):
            return "ar"
        elif re.search(r'[а-яА-Я]', text):
            return "ru"
        else:
            return "en"  # 默认为英语

    async def _translate(self,
                        text: str,
                        source_lang: str,
                        target_lang: str) -> str:
        """
        执行翻译

        Args:
            text: 原文
            source_lang: 源语言
            target_lang: 目标语言

        Returns:
            str: 译文
        """
        # 这里应该调用实际的翻译服务或LLM
        # 目前返回模拟响应

        if source_lang == target_lang:
            return text

        source_name = self.LANGUAGE_NAMES.get(source_lang, source_lang)
        target_name = self.LANGUAGE_NAMES.get(target_lang, target_lang)

        return f"[模拟翻译] 从{source_name}翻译成{target_name}: {text[:50]}..."
