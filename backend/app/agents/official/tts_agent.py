"""
文字转语音 (TTS)

将文本转换为自然语音的智能体
"""

import logging
from typing import Any, Optional

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class TTSAgent(BaseAgent):
    """文字转语音"""

    DEFAULT_CONFIG = AgentConfig(
        name="文字转语音",
        description="将文本转换为自然语音的智能体",
        version="1.0.0",
        author="System",
        tags=["tts", "text-to-speech", "voice", "audio"],
        priority=AgentPriority.NORMAL,
        required_capabilities=["tts"],
        optional_capabilities=["voice_cloning", "emotion_control"],
        metadata={
            "template_category": "tts",
            "agent_type": "single",
            "is_official": True,
            "icon": "tts_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """执行文字转语音"""
        logger.info(f"文字转语音执行: {str(input_data)[:50]}...")

        try:
            if isinstance(input_data, dict):
                text = input_data.get("text", "")
                voice = input_data.get("voice", "default")
                language = input_data.get("language", "zh")
            else:
                text = str(input_data)
                voice = "default"
                language = "zh"

            if not text.strip():
                return AgentResult(success=False, error="转换文本不能为空")

            # 模拟TTS
            result = await self._text_to_speech(text, voice, language)

            return AgentResult(
                success=True,
                output=result,
                metadata={"agent_name": self.name, "text_length": len(text)}
            )

        except Exception as e:
            logger.error(f"文字转语音失败: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def can_handle(self, input_data: Any) -> float:
        """判断是否能处理输入"""
        if isinstance(input_data, dict):
            if input_data.get("type") == "tts":
                return 1.0
            if "text" in input_data and ("voice" in input_data or "speak" in input_data):
                return 0.9

        if isinstance(input_data, str):
            keywords = ["转成语音", "读出来", "朗读", "tts", "text to speech", "speak"]
            if any(k in input_data.lower() for k in keywords):
                return 0.85

        return 0.2

    async def _text_to_speech(self, text: str, voice: str, language: str) -> dict:
        """模拟文字转语音"""
        return {
            "audio_url": "https://example.com/tts_output.mp3",
            "text": text,
            "voice": voice,
            "language": language,
            "duration": len(text) * 0.3  # 估算时长
        }
