"""
语音识别助手

将语音转换为文本的智能体，支持多种语言和方言
"""

import logging
from typing import Any, Optional

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class SpeechRecognitionAgent(BaseAgent):
    """语音识别助手"""

    DEFAULT_CONFIG = AgentConfig(
        name="语音识别助手",
        description="将语音转换为文本的智能体，支持多种语言和方言",
        version="1.0.0",
        author="System",
        tags=["speech", "recognition", "asr", "audio"],
        priority=AgentPriority.NORMAL,
        required_capabilities=["speech_recognition"],
        optional_capabilities=["language_detection", "emotion_recognition"],
        metadata={
            "template_category": "speech",
            "agent_type": "single",
            "is_official": True,
            "icon": "speech_recognition_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """执行语音识别"""
        logger.info(f"语音识别助手执行")

        try:
            if isinstance(input_data, dict):
                audio_url = input_data.get("audio_url")
                language = input_data.get("language", "auto")
            else:
                audio_url = str(input_data)
                language = "auto"

            if not audio_url:
                return AgentResult(success=False, error="音频URL不能为空")

            # 模拟语音识别
            result = await self._recognize_speech(audio_url, language)

            return AgentResult(
                success=True,
                output=result,
                metadata={"agent_name": self.name, "audio_url": audio_url}
            )

        except Exception as e:
            logger.error(f"语音识别失败: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def can_handle(self, input_data: Any) -> float:
        """判断是否能处理输入"""
        if isinstance(input_data, dict):
            if input_data.get("type") == "speech_recognition":
                return 1.0
            if "audio_url" in input_data or "audio_file" in input_data:
                return 0.9

        if isinstance(input_data, str):
            keywords = ["语音识别", "语音转文字", "转录", "transcribe"]
            if any(k in input_data.lower() for k in keywords):
                return 0.8

        return 0.2

    async def _recognize_speech(self, audio_url: str, language: str) -> dict:
        """模拟语音识别"""
        return {
            "text": "这是语音识别的模拟结果。实际实现需要集成ASR服务。",
            "language": language,
            "confidence": 0.95,
            "duration": 10.5,
            "word_count": 15
        }
