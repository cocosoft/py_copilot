from typing import List, Dict, Any, Optional
from app.services.knowledge.retrieval_service import AdvancedRetrievalService
from app.modules.memory.services.memory_service import MemoryService
from sqlalchemy.orm import Session


class KnowledgeRetrievalAgent:
    """
    知识库检索智能体
    负责执行智能知识库检索并优化检索结果
    """
    
    def __init__(self):
        self.retrieval_service = AdvancedRetrievalService()
    
    def retrieve(
        self, 
        query: str, 
        context: Dict[str, Any] = None,
        knowledge_base_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        执行知识库检索
        
        Args:
            query: 检索查询
            context: 上下文信息
            knowledge_base_id: 知识库ID（可选）
            tags: 标签过滤（可选）
            limit: 返回结果数量限制
            
        Returns:
            检索结果列表
        """
        # 增强查询（使用上下文）
        enhanced_query = self._enhance_query(query, context)
        
        # 执行混合搜索（关键词+向量）
        results = self.retrieval_service.hybrid_search(
            query=enhanced_query,
            n_results=limit,
            keyword_weight=0.3,
            vector_weight=0.7,
            knowledge_base_id=knowledge_base_id,
            tags=tags
        )
        
        # 优化检索结果
        optimized_results = self._optimize_results(results, context)
        
        return optimized_results
    
    async def retrieve_with_memory(
        self, 
        db: Session,
        user_id: int,
        query: str,
        context: Dict[str, Any] = None,
        knowledge_base_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        结合用户记忆的智能检索
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            query: 检索查询
            context: 上下文信息
            knowledge_base_id: 知识库ID（可选）
            tags: 标签过滤（可选）
            limit: 返回结果数量限制
            
        Returns:
            检索结果列表
        """
        # 获取用户相关记忆
        user_memories = await MemoryService.get_intelligent_context_memories(
            db=db,
            user_id=user_id,
            conversation_id=0,  # 临时值
            query=query,
            limit=3,
            use_semantic_search=True,
            use_recency_boost=True,
            use_importance_boost=True
        )
        
        # 构建包含记忆的上下文
        memory_context = context.copy() if context else {}
        memory_context["user_memories"] = [
            {
                "id": mem.id,
                "content": mem.content,
                "timestamp": mem.created_at.isoformat(),
                "memory_type": mem.memory_type,
                "memory_category": mem.memory_category
            }
            for mem in user_memories
        ]
        
        # 执行检索
        return self.retrieve(
            query=query,
            context=memory_context,
            knowledge_base_id=knowledge_base_id,
            tags=tags,
            limit=limit
        )
    
    def _enhance_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        使用上下文信息增强查询
        
        Args:
            query: 原始查询
            context: 上下文信息
            
        Returns:
            增强后的查询
        """
        if not context:
            return query
        
        enhanced_query = query
        
        # 添加对话历史到查询
        if "conversation_history" in context and context["conversation_history"]:
            recent_history = " ".join([
                item["content"] for item in context["conversation_history"][-3:]
            ])
            enhanced_query = f"{query} [对话历史: {recent_history}]"
        
        # 添加用户记忆到查询
        if "user_memories" in context and context["user_memories"]:
            user_context = " ".join([
                mem["content"] for mem in context["user_memories"]
            ])
            enhanced_query = f"{enhanced_query} [用户记忆: {user_context}]"
        
        return enhanced_query
    
    def _optimize_results(
        self, 
        results: List[Dict[str, Any]], 
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        优化检索结果
        
        Args:
            results: 原始检索结果
            context: 上下文信息
            
        Returns:
            优化后的结果
        """
        if not results:
            return []
        
        optimized_results = []
        
        for result in results:
            # 过滤低质量结果
            if result.get("score", 0) < 0.1:
                continue
            
            # 优化结果格式
            optimized_result = {
                "id": result["id"],
                "title": result["title"],
                "content": self._truncate_content(result["content"], max_length=500),
                "score": round(result.get("score", 0), 3),
                "knowledge_base_id": result.get("knowledge_base_id"),
                "file_type": result.get("file_type"),
                "created_at": result.get("created_at")
            }
            
            optimized_results.append(optimized_result)
        
        return optimized_results
    
    def _truncate_content(self, content: str, max_length: int = 500) -> str:
        """
        截断内容，保持完整性
        
        Args:
            content: 原始内容
            max_length: 最大长度 (不包括省略号)
            
        Returns:
            截断后的内容
        """
        if len(content) <= max_length:
            return content
        
        # 在句子边界截断
        truncated = content[:max_length]
        last_period = truncated.rfind(".")
        last_comma = truncated.rfind(",")
        last_space = truncated.rfind(" ")
        
        cut_position = max(last_period, last_comma, last_space)
        if cut_position == -1:
            cut_position = max_length
        
        # 确保最终长度不超过max_length + 3(省略号)
        final_content = truncated[:cut_position+1]
        if len(final_content) > max_length:
            final_content = truncated[:max_length]
        
        return final_content + "..."
