"""
智能体知识库集成模块

实现智能体与知识库系统的无缝集成，提供知识检索、上下文增强等功能。
"""
import logging
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session

from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.services.knowledge.retrieval_service import RetrievalService, AdvancedRetrievalService
from app.agents.agent_models import Agent, AgentConfig
from app.memory.memory_models import Memory, MemoryType, MemoryPriority

logger = logging.getLogger(__name__)


class AgentKnowledgeIntegration:
    """智能体知识库集成类"""
    
    def __init__(self, db_session: Session):
        """初始化知识库集成
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.knowledge_service = KnowledgeService()
        self.retrieval_service = RetrievalService()
        self.advanced_retrieval = AdvancedRetrievalService()
    
    def search_knowledge_for_agent(self, 
                                  agent_id: int, 
                                  query: str, 
                                  knowledge_base_id: Optional[int] = None,
                                  limit: int = 5) -> List[Dict[str, Any]]:
        """为智能体搜索相关知识
        
        Args:
            agent_id: 智能体ID
            query: 搜索查询
            knowledge_base_id: 指定知识库ID（可选）
            limit: 返回结果数量限制
            
        Returns:
            相关知识文档列表
        """
        try:
            # 获取智能体配置
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                logger.warning(f"智能体 {agent_id} 不存在")
                return []
            
            # 如果未指定知识库，使用智能体关联的知识库
            if not knowledge_base_id and agent.config:
                config_data = agent.config.config_data if agent.config else {}
                default_kb = config_data.get('default_knowledge_base')
                if default_kb:
                    knowledge_base_id = default_kb
            
            # 执行搜索
            if knowledge_base_id:
                results = self.retrieval_service.search_documents(
                    query=query, 
                    limit=limit, 
                    knowledge_base_id=knowledge_base_id
                )
            else:
                results = self.retrieval_service.search_documents(
                    query=query, 
                    limit=limit
                )
            
            # 记录搜索日志
            logger.info(f"智能体 {agent_id} 搜索知识库，查询: {query}, 结果数: {len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"智能体知识库搜索失败: {e}")
            return []
    
    def get_contextual_knowledge(self, 
                                agent_id: int, 
                                conversation_context: str,
                                recent_messages: List[Dict[str, Any]] = None,
                                limit: int = 3) -> List[Dict[str, Any]]:
        """获取上下文相关知识
        
        Args:
            agent_id: 智能体ID
            conversation_context: 对话上下文
            recent_messages: 最近消息列表（可选）
            limit: 返回结果数量限制
            
        Returns:
            上下文相关知识列表
        """
        try:
            # 构建上下文查询
            context_query = self._build_context_query(conversation_context, recent_messages)
            
            # 使用高级检索服务
            results = self.advanced_retrieval.advanced_search(
                query=context_query,
                n_results=limit,
                sort_by="relevance"
            )
            
            # 过滤和排序结果
            filtered_results = self._filter_contextual_results(results, conversation_context)
            
            logger.info(f"智能体 {agent_id} 获取上下文知识，结果数: {len(filtered_results)}")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"获取上下文知识失败: {e}")
            return []
    
    def _build_context_query(self, 
                           conversation_context: str, 
                           recent_messages: List[Dict[str, Any]] = None) -> str:
        """构建上下文查询
        
        Args:
            conversation_context: 对话上下文
            recent_messages: 最近消息列表
            
        Returns:
            构建的查询字符串
        """
        # 基础上下文
        query_parts = [conversation_context]
        
        # 添加最近消息的关键词
        if recent_messages:
            for msg in recent_messages[-5:]:  # 最近5条消息
                content = msg.get('content', '')
                if len(content) > 10:  # 只处理有内容的消息
                    # 提取关键词（简化实现）
                    keywords = self._extract_keywords(content)
                    if keywords:
                        query_parts.extend(keywords)
        
        # 去重并组合
        unique_parts = list(set([part for part in query_parts if part.strip()]))
        return " ".join(unique_parts)
    
    def _extract_keywords(self, text: str, max_keywords: int = 3) -> List[str]:
        """提取关键词（简化实现）
        
        Args:
            text: 文本内容
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取（实际项目中可以使用NLP库）
        words = text.split()
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '这', '那', '和', '与', '或', '但', '就', '都', '也', '又', '还', '而', '且', '如果', '因为', '所以', '虽然', '但是', '然后', '接着', '最后', '首先', '其次', '然后', '最后'}
        
        keywords = []
        for word in words:
            if (len(word) > 1 and 
                word not in stop_words and 
                not word.isdigit() and
                word.isalnum()):
                keywords.append(word)
        
        return keywords[:max_keywords]
    
    def _filter_contextual_results(self, 
                                 results: List[Dict[str, Any]], 
                                 context: str) -> List[Dict[str, Any]]:
        """过滤上下文相关结果
        
        Args:
            results: 原始结果列表
            context: 对话上下文
            
        Returns:
            过滤后的结果列表
        """
        if not results:
            return []
        
        # 简单的相关性过滤（实际项目中可以使用更复杂的算法）
        filtered = []
        for result in results:
            content = result.get('content', '').lower()
            context_lower = context.lower()
            
            # 检查内容中是否包含上下文关键词
            context_words = set(context_lower.split())
            content_words = set(content.split())
            
            # 计算关键词重叠率
            overlap = len(context_words & content_words)
            if overlap > 0:
                # 添加相关性分数
                result['context_relevance'] = overlap / len(context_words)
                filtered.append(result)
        
        # 按上下文相关性排序
        filtered.sort(key=lambda x: x.get('context_relevance', 0), reverse=True)
        
        return filtered
    
    def enhance_agent_response(self, 
                              agent_id: int, 
                              original_response: str,
                              conversation_context: str) -> str:
        """使用知识库增强智能体响应
        
        Args:
            agent_id: 智能体ID
            original_response: 原始响应
            conversation_context: 对话上下文
            
        Returns:
            增强后的响应
        """
        try:
            # 搜索相关知识
            knowledge_results = self.get_contextual_knowledge(
                agent_id=agent_id,
                conversation_context=conversation_context,
                limit=2
            )
            
            if not knowledge_results:
                return original_response
            
            # 构建增强响应
            enhanced_response = self._build_enhanced_response(
                original_response, 
                knowledge_results
            )
            
            logger.info(f"智能体 {agent_id} 响应已使用知识库增强")
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"智能体响应增强失败: {e}")
            return original_response
    
    def _build_enhanced_response(self, 
                               original_response: str,
                               knowledge_results: List[Dict[str, Any]]) -> str:
        """构建增强响应
        
        Args:
            original_response: 原始响应
            knowledge_results: 相关知识结果
            
        Returns:
            增强后的响应
        """
        if not knowledge_results:
            return original_response
        
        # 提取相关知识片段
        knowledge_snippets = []
        for result in knowledge_results[:2]:  # 最多使用2个知识片段
            content = result.get('content', '')[:200]  # 限制长度
            if content:
                knowledge_snippets.append(content)
        
        if not knowledge_snippets:
            return original_response
        
        # 构建增强响应
        enhanced_parts = [original_response]
        
        # 添加知识引用
        if knowledge_snippets:
            enhanced_parts.append("\n\n基于相关知识：")
            for i, snippet in enumerate(knowledge_snippets, 1):
                enhanced_parts.append(f"{i}. {snippet}")
        
        return "".join(enhanced_parts)


class KnowledgeAwareAgentEngine:
    """知识感知的智能体引擎"""
    
    def __init__(self, db_session: Session):
        """初始化知识感知引擎
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.knowledge_integration = AgentKnowledgeIntegration(db_session)
    
    def process_message_with_knowledge(self, 
                                      agent_id: int, 
                                      message: str,
                                      conversation_context: str = "") -> str:
        """使用知识库处理消息
        
        Args:
            agent_id: 智能体ID
            message: 输入消息
            conversation_context: 对话上下文
            
        Returns:
            处理后的响应
        """
        try:
            # 1. 搜索相关知识
            knowledge_results = self.knowledge_integration.search_knowledge_for_agent(
                agent_id=agent_id,
                query=message,
                limit=3
            )
            
            # 2. 生成基础响应（这里简化实现，实际项目中应该调用智能体引擎）
            base_response = self._generate_base_response(message)
            
            # 3. 使用知识库增强响应
            if knowledge_results:
                enhanced_response = self.knowledge_integration.enhance_agent_response(
                    agent_id=agent_id,
                    original_response=base_response,
                    conversation_context=conversation_context or message
                )
                return enhanced_response
            else:
                return base_response
                
        except Exception as e:
            logger.error(f"知识感知消息处理失败: {e}")
            return "抱歉，我暂时无法处理这个问题。"
    
    def _generate_base_response(self, message: str) -> str:
        """生成基础响应（简化实现）
        
        Args:
            message: 输入消息
            
        Returns:
            基础响应
        """
        # 这里应该调用实际的智能体引擎
        # 简化实现：返回一个基础响应
        return f"我收到了您的消息：'{message}'。让我为您查找相关信息。"