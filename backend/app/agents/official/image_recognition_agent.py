"""
图像识别专家

识别和分析图片内容的智能体
"""

import logging
from typing import Any, Optional, List, Dict

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class ImageRecognitionAgent(BaseAgent):
    """图像识别专家"""

    DEFAULT_CONFIG = AgentConfig(
        name="图像识别专家",
        description="识别和分析图片内容的智能体",
        version="1.0.0",
        author="System",
        tags=["image", "recognition", "analysis", "vision"],
        priority=AgentPriority.NORMAL,
        required_capabilities=["image_recognition", "vision"],
        optional_capabilities=["object_detection", "ocr", "face_recognition"],
        metadata={
            "template_category": "image_recognition",
            "agent_type": "single",
            "is_official": True,
            "icon": "image_recognition_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """执行图像识别"""
        logger.info(f"图像识别专家执行")

        try:
            if isinstance(input_data, dict):
                image_url = input_data.get("image_url")
                question = input_data.get("question")
            else:
                image_url = str(input_data)
                question = None

            if not image_url:
                return AgentResult(success=False, error="图片URL不能为空")

            # 模拟图像识别
            result = await self._recognize_image(image_url, question)

            return AgentResult(
                success=True,
                output=result,
                metadata={"agent_name": self.name, "image_url": image_url}
            )

        except Exception as e:
            logger.error(f"图像识别失败: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def can_handle(self, input_data: Any) -> float:
        """判断是否能处理输入"""
        if isinstance(input_data, dict):
            if input_data.get("type") == "image_recognition":
                return 1.0
            if "image_url" in input_data or "image_file" in input_data:
                return 0.9

        if isinstance(input_data, str):
            keywords = ["识别图片", "分析图片", "图片里有什么", "这是什么", "image recognition"]
            if any(k in input_data.lower() for k in keywords):
                return 0.8

        return 0.2

    async def _recognize_image(self, image_url: str, question: Optional[str]) -> dict:
        """模拟图像识别"""
        return {
            "description": "这是一张示例图片，包含一些物体和场景。",
            "objects": ["object1", "object2"],
            "scene": "室内场景",
            "text_detected": False,
            "question_answer": question
        }
