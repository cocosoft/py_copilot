"""
视频分析专家

分析视频内容和提取信息的智能体
"""

import logging
from typing import Any, Optional, List, Dict

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class VideoAnalysisAgent(BaseAgent):
    """视频分析专家"""

    DEFAULT_CONFIG = AgentConfig(
        name="视频分析专家",
        description="分析视频内容和提取信息的智能体",
        version="1.0.0",
        author="System",
        tags=["video", "analysis", "extraction", "vision"],
        priority=AgentPriority.NORMAL,
        required_capabilities=["video_analysis", "vision"],
        optional_capabilities=["scene_detection", "object_tracking", "ocr"],
        metadata={
            "template_category": "video_analysis",
            "agent_type": "single",
            "is_official": True,
            "icon": "video_analysis_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """执行视频分析"""
        logger.info(f"视频分析专家执行")

        try:
            if isinstance(input_data, dict):
                video_url = input_data.get("video_url")
                analysis_type = input_data.get("analysis_type", "summary")
            else:
                video_url = str(input_data)
                analysis_type = "summary"

            if not video_url:
                return AgentResult(success=False, error="视频URL不能为空")

            # 模拟视频分析
            result = await self._analyze_video(video_url, analysis_type)

            return AgentResult(
                success=True,
                output=result,
                metadata={"agent_name": self.name, "video_url": video_url}
            )

        except Exception as e:
            logger.error(f"视频分析失败: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def can_handle(self, input_data: Any) -> float:
        """判断是否能处理输入"""
        if isinstance(input_data, dict):
            if input_data.get("type") == "video_analysis":
                return 1.0
            if "video_url" in input_data or "video_file" in input_data:
                return 0.9

        if isinstance(input_data, str):
            keywords = ["分析视频", "视频内容", "视频摘要", "video analysis"]
            if any(k in input_data.lower() for k in keywords):
                return 0.8

        return 0.2

    async def _analyze_video(self, video_url: str, analysis_type: str) -> dict:
        """模拟视频分析"""
        return {
            "summary": "这是一个示例视频的摘要描述。",
            "duration": 120,
            "scenes": ["scene1", "scene2", "scene3"],
            "key_frames": ["frame1.jpg", "frame2.jpg"],
            "transcript": "视频中的语音转录文本...",
            "analysis_type": analysis_type
        }
