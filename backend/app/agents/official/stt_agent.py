"""
语音转文字 (STT)

将语音准确转换为文本的智能体
"""

import logging
from typing import Any, Optional

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class STTAgent(BaseAgent):
    """语音转文字"""

    DEFAULT_CONFIG = AgentConfig(
        name="语音转文字",
        description="将语音准确转换为文本的智能体",
        version="1.0.0",
        author="System",
        tags=["stt", "speech-to-text", "transcription", "audio"],
        priority=AgentPriority.NORMAL,
        required_capabilities=["speech_recognition"],
        optional_capabilities=["speaker_diarization", "punctuation"],
        metadata={
            "template_category": "stt",
            "agent_type": "single",
            "is_official": True,
            "icon": "stt_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """执行语音转文字"""
        logger.info(f"语音转文字执行")

        try:
            if isinstance(input_data, dict):
                audio_url = input_data.get("audio_url")
                language = input_data.get("language", "auto")
                add_punctuation = input_data.get("add_punctuation", True)
            else:
                audio_url = str(input_data)
                language = "auto"
                add_punctuation = True

            if not audio_url:
                return AgentResult(success=False, error="音频URL不能为空")

            # 模拟STT
            result = await self._speech_to_text(audio_url, language, add_punctuation)

            return AgentResult(
                success=True,
                output=result,
                metadata={"agent_name": self.name, "audio_url": audio_url}
            )

        except Exception as e:
            logger.error(f"语音转文字失败: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def can_handle(self, input_data: Any) -> float:
        """判断是否能处理输入"""
        if isinstance(input_data, dict):
            if input_data.get("type") == "stt":
                return 1.0
            if input_data.get("type") == "speech_to_text":
                return 1.0
            if "audio_url" in input_data and "transcribe" in str(input_data):
                return 0.9

        if isinstance(input_data, str):
            keywords = ["转文字", "转文本", "stt", "speech to text", "transcribe", "转录"]
            if any(k in input_data.lower() for k in keywords):
                return 0.85

        return 0.2

    async def _speech_to_text(self, audio_url: str, language: str, add_punctuation: bool) -> dict:
        """模拟语音转文字"""
        return {
            "text": "这是语音转文字的模拟结果。实际实现需要集成STT服务。",
            "language": language,
            "confidence": 0.95,
            "duration": 15.5,
            "word_count": 20,
            "add_punctuation": add_punctuation
        }
