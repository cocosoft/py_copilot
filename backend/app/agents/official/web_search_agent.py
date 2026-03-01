"""
Web搜索助手

使用网络搜索获取最新信息的智能体
"""

import logging
from typing import Any, Optional, List, Dict

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class WebSearchAgent(BaseAgent):
    """Web搜索助手"""

    DEFAULT_CONFIG = AgentConfig(
        name="Web搜索助手",
        description="使用网络搜索获取最新信息的智能体",
        version="1.0.0",
        author="System",
        tags=["web", "search", "internet", "browser"],
        priority=AgentPriority.HIGH,
        required_capabilities=["web_search", "llm"],
        optional_capabilities=["web_browsing", "content_extraction"],
        metadata={
            "template_category": "web_search",
            "agent_type": "single",
            "is_official": True,
            "icon": "web_search_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """执行Web搜索"""
        logger.info(f"Web搜索助手执行: {str(input_data)[:50]}...")

        try:
            if isinstance(input_data, dict):
                query = input_data.get("query", "")
                num_results = input_data.get("num_results", 5)
            else:
                query = str(input_data)
                num_results = 5

            if not query.strip():
                return AgentResult(success=False, error="搜索关键词不能为空")

            # 模拟Web搜索
            results = await self._web_search(query, num_results)

            return AgentResult(
                success=True,
                output={
                    "query": query,
                    "results": results,
                    "total_results": len(results)
                },
                metadata={"agent_name": self.name, "query": query}
            )

        except Exception as e:
            logger.error(f"Web搜索失败: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def can_handle(self, input_data: Any) -> float:
        """判断是否能处理输入"""
        if isinstance(input_data, dict):
            if input_data.get("type") == "web_search":
                return 1.0
            if "search" in input_data and "web" in str(input_data.get("source", "")):
                return 0.9

        if isinstance(input_data, str):
            keywords = ["搜索", "查一下", "网上", "web", "search", "google", "百度"]
            if any(k in input_data.lower() for k in keywords):
                return 0.8

        return 0.3

    async def _web_search(self, query: str, num_results: int) -> List[Dict]:
        """模拟Web搜索"""
        return [
            {
                "title": f"关于'{query}'的搜索结果",
                "url": "https://example.com/search",
                "snippet": f"这是关于'{query}'的搜索摘要内容...",
                "source": "web"
            }
        ]
