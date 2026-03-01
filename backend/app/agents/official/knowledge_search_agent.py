"""
知识库搜索

在知识库中搜索和检索信息的智能体
"""

import logging
from typing import Any, Optional, List, Dict

from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext, AgentPriority

logger = logging.getLogger(__name__)


class KnowledgeSearchAgent(BaseAgent):
    """知识库搜索"""

    DEFAULT_CONFIG = AgentConfig(
        name="知识库搜索",
        description="在知识库中搜索和检索信息的智能体",
        version="1.0.0",
        author="System",
        tags=["knowledge", "search", "retrieval", "rag"],
        priority=AgentPriority.HIGH,
        required_capabilities=["knowledge_base", "search", "llm"],
        optional_capabilities=["embedding", "rerank"],
        metadata={
            "template_category": "search",
            "agent_type": "single",
            "is_official": True,
            "icon": "knowledge_search_agent.svg"
        }
    )

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    async def execute(self,
                     input_data: Any,
                     context: Optional[AgentContext] = None) -> AgentResult:
        """执行知识库搜索"""
        logger.info(f"知识库搜索执行: {str(input_data)[:50]}...")

        try:
            if isinstance(input_data, dict):
                query = input_data.get("query", "")
                knowledge_base_id = input_data.get("knowledge_base_id")
                top_k = input_data.get("top_k", 5)
            else:
                query = str(input_data)
                knowledge_base_id = None
                top_k = 5

            if not query.strip():
                return AgentResult(success=False, error="查询内容不能为空")

            # 模拟知识库搜索
            results = await self._search_knowledge(query, knowledge_base_id, top_k)

            return AgentResult(
                success=True,
                output={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "knowledge_base_id": knowledge_base_id
                },
                metadata={"agent_name": self.name, "query": query}
            )

        except Exception as e:
            logger.error(f"知识库搜索失败: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def can_handle(self, input_data: Any) -> float:
        """判断是否能处理输入"""
        if isinstance(input_data, dict):
            if input_data.get("type") == "knowledge_search":
                return 1.0
            if "knowledge_base_id" in input_data:
                return 0.9
            if "query" in input_data:
                return 0.7

        if isinstance(input_data, str):
            keywords = ["知识库", "搜索", "查询", "检索", "rag", "knowledge"]
            if any(k in input_data.lower() for k in keywords):
                return 0.75

        return 0.3

    async def _search_knowledge(self, query: str, kb_id: Optional[str], top_k: int) -> List[Dict]:
        """模拟知识库搜索"""
        return [
            {
                "content": f"关于'{query}'的知识库内容示例",
                "source": "knowledge_base",
                "score": 0.92,
                "metadata": {"page": 1, "document": "example.pdf"}
            }
        ]
