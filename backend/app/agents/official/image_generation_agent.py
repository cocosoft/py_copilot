"""
图片生成器

根据描述生成图片的AI智能体
"""

import logging
from typing import Any, Optional

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class ImageGenerationAgent(BaseAgent):
    """图片生成器"""

    DEFAULT_CONFIG = AgentConfig(
        name="图片生成器",
        description="根据描述生成图片的AI智能体",
        version="1.0.0",
        author="System",
        tags=["image", "generation", "ai", "art"],
        priority=AgentPriority.NORMAL,
        required_capabilities=["image_generation"],
        optional_capabilities=["style_transfer", "image_editing"],
        metadata={
            "template_category": "image_generation",
            "agent_type": "single",
            "is_official": True,
            "icon": "image_generation_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """执行图片生成"""
        logger.info(f"图片生成器执行: {str(input_data)[:50]}...")

        try:
            if isinstance(input_data, dict):
                prompt = input_data.get("prompt", "")
                style = input_data.get("style", "default")
                size = input_data.get("size", "1024x1024")
            else:
                prompt = str(input_data)
                style = "default"
                size = "1024x1024"

            if not prompt.strip():
                return AgentResult(success=False, error="图片描述不能为空")

            # 模拟图片生成
            result = await self._generate_image(prompt, style, size)

            return AgentResult(
                success=True,
                output=result,
                metadata={"agent_name": self.name, "prompt": prompt}
            )

        except Exception as e:
            logger.error(f"图片生成失败: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def can_handle(self, input_data: Any) -> float:
        """判断是否能处理输入"""
        if isinstance(input_data, dict):
            if input_data.get("type") == "image_generation":
                return 1.0
            if "prompt" in input_data and ("image" in input_data or "generate" in input_data):
                return 0.9

        if isinstance(input_data, str):
            keywords = ["生成图片", "画一张", "画个", "生成图像", "image generation", "draw"]
            if any(k in input_data.lower() for k in keywords):
                return 0.85

        return 0.2

    async def _generate_image(self, prompt: str, style: str, size: str) -> dict:
        """模拟图片生成"""
        return {
            "image_url": "https://example.com/generated_image.png",
            "prompt": prompt,
            "style": style,
            "size": size,
            "status": "completed"
        }
