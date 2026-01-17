from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import json

from app.modules.memory.services.memory_service import MemoryService
from app.schemas.memory import MemoryCreate
from app.core.database import get_db
from app.services.llm_service import LLMService
from app.services.knowledge.semantic_search_service import SemanticSearchService

logger = logging.getLogger(__name__)


class ContextManager:
    """
    上下文管理器类
    负责增强和更新用户上下文信息
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.semantic_search_service = SemanticSearchService()
        self.topic_tracking = {}
        self.max_history_length = 10
        self.topic_analysis_interval = 5  # 每5轮对话分析一次主题
        self.context_compression_threshold = 1500  # 上下文压缩阈值（字符数）
        self.context_prediction_enabled = True  # 启用上下文预测
        self.context_relevance_threshold = 0.3  # 上下文相关性阈值
    
    async def enhance_context(
        self, 
        user_input: str,
        user_context: Dict[str, Any],
        intent_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        增强上下文信息
        
        Args:
            user_input: 用户输入文本
            user_context: 基础用户上下文信息
            intent_result: 意图识别结果（可选）
            
        Returns:
            增强后的上下文信息
        """
        # 复制基础上下文
        enhanced_context = user_context.copy()
        
        # 添加意图信息
        if intent_result:
            enhanced_context["intent"] = intent_result
        
        # 添加时间信息
        enhanced_context["timestamp"] = datetime.now().isoformat()
        
        # 添加用户历史对话
        if "conversation_id" in user_context and "user_id" in user_context:
            try:
                # 获取数据库会话
                db: Session = next(get_db())
                
                # 获取当前对话的历史记录
                conversation_key = f"{user_context['user_id']}_{user_context['conversation_id']}"
                conversation_count = enhanced_context.get("interaction_count", 0) + 1
                enhanced_context["interaction_count"] = conversation_count
                
                # 使用更智能的方式获取对话历史
                recent_memories = await MemoryService.get_intelligent_context_memories(
                    db=db,
                    user_id=user_context["user_id"],
                    conversation_id=user_context["conversation_id"],
                    query=user_input,
                    limit=self.max_history_length,
                    use_semantic_search=True,  # 启用语义搜索
                    use_recency_boost=True,
                    use_importance_boost=True
                )
                
                # 添加对话历史到上下文
                conversation_history = [
                    {
                        "id": mem.id,
                        "content": mem.content,
                        "timestamp": mem.created_at.isoformat(),
                        "memory_type": mem.memory_type,
                        "memory_category": mem.memory_category,
                        "importance_score": mem.importance_score,
                        "relevance_score": mem.relevance_score
                    }
                    for mem in recent_memories
                ]
                enhanced_context["conversation_history"] = conversation_history
                
                # 添加当前输入到上下文
                enhanced_context["current_input"] = user_input
                
                # 分析对话主题（每5轮分析一次）
                if conversation_count % self.topic_analysis_interval == 0:
                    current_topic = await self._analyze_conversation_topic(conversation_key, conversation_history)
                    enhanced_context["current_topic"] = current_topic
                elif conversation_key in self.topic_tracking:
                    enhanced_context["current_topic"] = self.topic_tracking[conversation_key]
                
                # 从用户输入中提取实体
                entities = await self._extract_entities(user_input)
                if entities:
                    enhanced_context["extracted_entities"] = entities
                
                # 生成上下文摘要
                context_summary = await self._generate_context_summary(conversation_history, user_input)
                enhanced_context["context_summary"] = context_summary
                
                # 添加知识库相关信息
                if entities:
                    knowledge_references = await self._get_relevant_knowledge(
                        db=db,
                        user_input=user_input,
                        entities=entities,
                        user_id=user_context["user_id"]
                    )
                    if knowledge_references:
                        enhanced_context["knowledge_references"] = knowledge_references
                
                # 分析上下文关联
                context_correlation = await self._analyze_context_correlation(
                    user_context["user_id"],
                    conversation_history,
                    user_input
                )
                enhanced_context["context_correlation"] = context_correlation
                
                # 预测下一个上下文
                if self.context_prediction_enabled and conversation_count > 3:
                    next_context_prediction = await self._predict_next_context(
                        user_context["user_id"],
                        conversation_history,
                        user_input
                    )
                    enhanced_context["next_context_prediction"] = next_context_prediction
                
                # 压缩上下文（如果超过阈值）
                if len(str(enhanced_context)) > self.context_compression_threshold:
                    compressed_context = await self._compress_context(enhanced_context)
                    enhanced_context["compressed_context"] = compressed_context
                        
            except Exception as e:
                # 如果获取历史对话失败，记录错误但不中断流程
                logger.error(f"获取对话历史失败: {str(e)}")
                enhanced_context["conversation_history"] = []
        
        return enhanced_context
    
    async def _analyze_conversation_topic(self, conversation_key: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析对话主题
        
        Args:
            conversation_key: 对话键
            conversation_history: 对话历史
            
        Returns:
            对话主题分析结果
        """
        try:
            # 提取对话历史中的内容
            history_text = "\n".join([item["content"] for item in conversation_history])
            
            # 使用LLM分析主题
            messages = [
                {
                    "role": "system", 
                    "content": "请分析以下对话的主题，返回一个简洁的主题名称和主要讨论点。使用JSON格式返回，包含'topic'和'key_points'字段。"
                },
                {"role": "user", "content": history_text[:2000]}  # 限制输入长度
            ]
            
            result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
            
            # 解析结果
            topic_analysis = json.loads(result["generated_text"])
            
            # 保存主题到追踪字典
            self.topic_tracking[conversation_key] = topic_analysis
            
            logger.info(f"对话主题分析结果: {topic_analysis['topic']}")
            return topic_analysis
            
        except Exception as e:
            logger.error(f"分析对话主题失败: {str(e)}")
            return {"topic": "未知主题", "key_points": []}
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取实体
        
        Args:
            text: 输入文本
            
        Returns:
            提取的实体列表
        """
        try:
            # 使用LLM提取实体
            messages = [
                {
                    "role": "system", 
                    "content": "请从以下文本中提取实体，包括人物、地点、组织、事件等。使用JSON格式返回，每个实体包含'name'和'type'字段。"
                },
                {"role": "user", "content": text}
            ]
            
            result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
            
            # 解析结果
            entities = json.loads(result["generated_text"])
            
            logger.info(f"从文本中提取到实体: {[entity['name'] for entity in entities]}")
            return entities
            
        except Exception as e:
            logger.error(f"提取实体失败: {str(e)}")
            return []
    
    async def _generate_context_summary(self, conversation_history: List[Dict[str, Any]], current_input: str) -> str:
        """
        生成上下文摘要
        
        Args:
            conversation_history: 对话历史
            current_input: 当前用户输入
            
        Returns:
            上下文摘要
        """
        try:
            # 提取对话历史中的内容
            history_text = "\n".join([item["content"] for item in conversation_history])
            
            # 使用LLM生成摘要
            messages = [
                {
                    "role": "system", 
                    "content": "请为以下对话历史和当前输入生成一个简洁的上下文摘要，用于辅助AI理解当前对话场景。"
                },
                {
                    "role": "user", 
                    "content": f"对话历史:\n{history_text}\n\n当前输入:\n{current_input}"
                }
            ]
            
            result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
            
            return result["generated_text"]
            
        except Exception as e:
            logger.error(f"生成上下文摘要失败: {str(e)}")
            return ""
    
    async def _get_relevant_knowledge(self, db: Session, user_input: str, entities: List[Dict[str, Any]], user_id: int) -> List[Dict[str, Any]]:
        """
        获取与用户输入相关的知识库信息
        
        Args:
            db: 数据库会话
            user_input: 用户输入
            entities: 提取的实体列表
            user_id: 用户ID
            
        Returns:
            相关知识库信息列表
        """
        try:
            # 首先使用用户输入进行语义搜索
            search_results = await self.semantic_search_service.search_documents(
                db=db,
                query=user_input,
                user_id=user_id,
                limit=5
            )
            
            # 如果有实体，也使用实体进行搜索
            if entities:
                entity_names = [entity["name"] for entity in entities[:3]]  # 只使用前3个实体
                for entity_name in entity_names:
                    entity_results = await self.semantic_search_service.search_documents(
                        db=db,
                        query=entity_name,
                        user_id=user_id,
                        limit=3
                    )
                    search_results.extend(entity_results)
            
            # 去重
            unique_results = []
            seen_ids = set()
            for result in search_results:
                if "id" in result and result["id"] not in seen_ids:
                    seen_ids.add(result["id"])
                    unique_results.append(result)
            
            logger.info(f"获取到 {len(unique_results)} 条相关知识库信息")
            return unique_results[:5]  # 最多返回5条结果
            
        except Exception as e:
            logger.error(f"获取相关知识库信息失败: {str(e)}")
            return []
    
    async def update_context(
        self, 
        conversation_id: int,
        user_id: int,
        user_input: str,
        response: str,
        intent_type: Optional[str] = None
    ) -> None:
        """
        更新上下文信息，将新的对话内容保存到记忆中
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            user_input: 用户输入文本
            response: 系统响应文本
            intent_type: 意图类型（可选）
        """
        try:
            # 获取数据库会话
            db: Session = next(get_db())
            
            # 创建用户输入记忆
            input_memory = MemoryCreate(
                session_id="",
                memory_type="SHORT_TERM",
                memory_category="USER_INPUT",
                title=f"用户输入: {user_input[:30]}...",
                content=user_input,
                summary=f"用户输入: {user_input[:100]}...",
                importance_score=0.3,
                relevance_score=0.5,
                tags=["user_input"] if not intent_type else ["user_input", intent_type],
                source_info={
                    "source_type": "USER_INPUT",
                    "conversation_id": conversation_id
                },
                source_type="USER_INPUT"
            )
            
            # 保存用户输入记忆
            MemoryService.create_memory(db, input_memory, user_id)
            
            # 创建系统响应记忆
            response_memory = MemoryCreate(
                session_id="",
                memory_type="SHORT_TERM",
                memory_category="SYSTEM_RESPONSE",
                title=f"系统响应: {response[:30]}...",
                content=response,
                summary=f"系统响应: {response[:100]}...",
                importance_score=0.3,
                relevance_score=0.5,
                tags=["system_response"] if not intent_type else ["system_response", intent_type],
                source_info={
                    "source_type": "SYSTEM_RESPONSE",
                    "conversation_id": conversation_id
                },
                source_type="SYSTEM_RESPONSE"
            )
            
            # 保存系统响应记忆
            MemoryService.create_memory(db, response_memory, user_id)
            
        except Exception as e:
            # 如果保存记忆失败，记录错误但不中断流程
            logger.error(f"保存对话记忆失败: {str(e)}")
            
    async def clear_context(self, conversation_id: int, user_id: int) -> None:
        """
        清除特定对话的上下文信息
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
        """
        try:
            # 获取数据库会话
            db: Session = next(get_db())
            
            # 从主题跟踪中移除该对话
            if conversation_id in self.topic_tracking:
                del self.topic_tracking[conversation_id]
                logger.info(f"已从主题跟踪中移除对话ID {conversation_id} 的上下文")
            
            # 这里可以添加更多的上下文清除逻辑，例如：
            # 1. 如果有缓存的上下文，可以清除缓存
            # 2. 如果有临时存储的上下文数据，可以清除
            # 3. 如果需要标记记忆为不再相关，可以在这里实现
            
            # 记录清除操作
            logger.info(f"已清除用户ID {user_id} 对话ID {conversation_id} 的上下文信息")
            
        except Exception as e:
            # 如果清除上下文失败，记录错误但不中断流程
            logger.error(f"清除上下文失败: {str(e)}")
    
    async def _analyze_context_correlation(self, user_id: int, conversation_history: List[Dict[str, Any]], current_input: str) -> Dict[str, Any]:
        """
        分析上下文关联
        
        Args:
            user_id: 用户ID
            conversation_history: 对话历史
            current_input: 当前用户输入
            
        Returns:
            上下文关联分析结果
        """
        try:
            # 如果对话历史为空，直接返回默认结果
            if not conversation_history:
                return {
                    "topics": [],
                    "relevance_score": 0.0,
                    "is_topic_change": True,
                    "key_connections": []
                }
            
            # 提取对话历史中的内容，只使用最近5轮对话
            recent_history = conversation_history[-5:]
            history_text = "\n".join([item["content"] for item in recent_history])
            
            # 使用改进的提示词分析上下文关联
            messages = [
                {
                    "role": "system", 
                    "content": "请分析以下对话历史和当前输入之间的关联，返回详细的关联分析结果。\n\n要求：\n1. 输出必须是严格的JSON格式\n2. 包含以下字段：\n   - topics: 列表，包含对话涉及的主要主题\n   - relevance_score: 数字，0-1之间，表示当前输入与对话历史的相关度\n   - is_topic_change: 布尔值，是否为新主题\n   - key_connections: 列表，包含当前输入与历史对话的关键连接点\n   - continuity_score: 数字，0-1之间，表示对话的连续性\n\n示例输出：\n{\"topics\": [\"机器学习\", \"深度学习\"], \"relevance_score\": 0.85, \"is_topic_change\": false, \"key_connections\": [\"都讨论了神经网络\", \"都涉及模型训练\"]}"
                },
                {
                    "role": "user", 
                    "content": f"对话历史:\n{history_text}\n\n当前输入:\n{current_input}"
                }
            ]
            
            result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
            
            # 解析结果，添加错误处理
            try:
                correlation = json.loads(result["generated_text"])
            except json.JSONDecodeError:
                logger.warning(f"上下文关联分析结果解析失败，使用默认格式: {result['generated_text']}")
                # 提取关键信息，生成默认格式
                return {
                    "topics": [],
                    "relevance_score": 0.5,
                    "is_topic_change": False,
                    "key_connections": [],
                    "continuity_score": 0.5
                }
            
            # 确保返回结果包含所有必要字段
            if "topics" not in correlation:
                correlation["topics"] = []
            if "relevance_score" not in correlation:
                correlation["relevance_score"] = 0.5
            if "is_topic_change" not in correlation:
                correlation["is_topic_change"] = correlation["relevance_score"] < 0.4
            if "key_connections" not in correlation:
                correlation["key_connections"] = []
            if "continuity_score" not in correlation:
                correlation["continuity_score"] = correlation["relevance_score"]
            
            logger.info(f"上下文关联分析结果: 相关度 {correlation.get('relevance_score', 0.0)}, 主题变化 {correlation.get('is_topic_change', False)}")
            return correlation
            
        except Exception as e:
            logger.error(f"分析上下文关联失败: {str(e)}")
            # 返回更完整的默认结果
            return {
                "topics": [],
                "relevance_score": 0.5,
                "is_topic_change": False,
                "key_connections": [],
                "continuity_score": 0.5
            }
    
    async def _predict_next_context(self, user_id: int, conversation_history: List[Dict[str, Any]], current_input: str) -> Dict[str, Any]:
        """
        预测下一个上下文
        
        Args:
            user_id: 用户ID
            conversation_history: 对话历史
            current_input: 当前用户输入
            
        Returns:
            下一个上下文预测结果
        """
        try:
            # 如果没有对话历史，返回空预测
            if not conversation_history:
                return {
                    "predicted_topics": [],
                    "example_questions": [],
                    "predicted_intents": [],
                    "confidence_scores": [],
                    "knowledge_suggestions": [],
                    "prediction_timestamp": datetime.now().isoformat()
                }
            
            # 提取对话历史中的内容，只使用最近8轮对话
            recent_history = conversation_history[-8:]
            history_text = "\n".join([item["content"] for item in recent_history])
            
            # 使用改进的提示词预测下一个上下文
            messages = [
                {
                    "role": "system", 
                    "content": "请基于以下对话历史和当前输入，预测用户可能的下一个问题或需求。返回详细的预测结果。\n\n要求：\n1. 输出必须是严格的JSON格式\n2. 包含以下字段：\n   - predicted_topics: 列表，包含用户可能讨论的下一个主题\n   - example_questions: 列表，包含用户可能提出的具体问题示例\n   - predicted_intents: 列表，包含用户可能的意图\n   - confidence_scores: 列表，0-1之间的数字，表示每个预测的置信度\n   - knowledge_suggestions: 列表，包含可能需要的知识库建议\n\n示例输出：\n{\"predicted_topics\": [\"机器学习\", \"深度学习\"], \"example_questions\": [\"什么是神经网络？\", \"如何训练模型？\"], \"predicted_intents\": [\"获取信息\", \"请求解释\"], \"confidence_scores\": [0.8, 0.7], \"knowledge_suggestions\": [\"神经网络基础\", \"模型训练方法\"]}"
                },
                {
                    "role": "user", 
                    "content": f"对话历史:\n{history_text}\n\n当前输入:\n{current_input}"
                }
            ]
            
            result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
            
            # 解析结果，添加错误处理
            try:
                prediction = json.loads(result["generated_text"])
            except json.JSONDecodeError:
                logger.warning(f"上下文预测结果解析失败，使用默认格式: {result['generated_text']}")
                # 生成默认格式的预测结果
                return {
                    "predicted_topics": [],
                    "example_questions": [],
                    "predicted_intents": [],
                    "confidence_scores": [],
                    "knowledge_suggestions": [],
                    "prediction_timestamp": datetime.now().isoformat()
                }
            
            # 确保返回结果包含所有必要字段
            if "predicted_topics" not in prediction:
                prediction["predicted_topics"] = []
            if "example_questions" not in prediction:
                prediction["example_questions"] = []
            if "predicted_intents" not in prediction:
                prediction["predicted_intents"] = []
            if "confidence_scores" not in prediction:
                # 为每个预测的主题生成默认置信度
                prediction["confidence_scores"] = [0.5] * len(prediction["predicted_topics"])
            if "knowledge_suggestions" not in prediction:
                prediction["knowledge_suggestions"] = []
            
            # 添加时间戳
            prediction["prediction_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"上下文预测结果: 预测主题 {prediction.get('predicted_topics', [])}, 示例问题 {len(prediction.get('example_questions', []))}个")
            return prediction
            
        except Exception as e:
            logger.error(f"预测下一个上下文失败: {str(e)}")
            # 返回更完整的默认结果
            return {
                "predicted_topics": [],
                "example_questions": [],
                "predicted_intents": [],
                "confidence_scores": [],
                "knowledge_suggestions": [],
                "prediction_timestamp": datetime.now().isoformat()
            }
    
    async def _compress_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        压缩上下文
        
        Args:
            context: 需要压缩的上下文
            
        Returns:
            压缩后的上下文
        """
        try:
            # 创建压缩后的上下文副本
            compressed = context.copy()
            
            # 简化对话历史
            if "conversation_history" in compressed:
                # 只保留最近3轮对话，并且只保留核心信息
                simplified_history = []
                for item in compressed["conversation_history"][-3:]:
                    simplified = {
                        "content": item["content"][:200] + "..." if len(item["content"]) > 200 else item["content"],
                        "timestamp": item["timestamp"],
                        "memory_type": item["memory_type"]
                    }
                    simplified_history.append(simplified)
                compressed["conversation_history"] = simplified_history
            
            # 简化知识库引用
            if "knowledge_references" in compressed:
                # 只保留前2条知识库引用
                compressed["knowledge_references"] = compressed["knowledge_references"][:2]
            
            # 生成智能摘要
            try:
                # 提取关键信息用于生成摘要
                key_info = {
                    "current_input": compressed.get("current_input", ""),
                    "conversation_history": compressed.get("conversation_history", []),
                    "current_topic": compressed.get("current_topic", {}).get("topic", "")
                }
                
                # 使用LLM生成智能摘要
                messages = [
                    {
                        "role": "system", 
                        "content": "请为以下对话上下文生成一个简洁的摘要，突出当前的对话主题和用户的主要需求。摘要长度不超过150个字符。"
                    },
                    {
                        "role": "user", 
                        "content": str(key_info)
                    }
                ]
                
                summary_result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
                compressed["smart_summary"] = summary_result["generated_text"]
            except Exception as summary_e:
                logger.warning(f"生成智能摘要失败，使用默认摘要: {str(summary_e)}")
                # 如果生成摘要失败，使用更简单的方式生成摘要
                current_input = compressed.get("current_input", "").strip()
                if current_input:
                    compressed["smart_summary"] = f"用户当前输入: {current_input[:100]}{'...' if len(current_input) > 100 else ''}"
                else:
                    compressed["smart_summary"] = "上下文压缩: 对话历史简化"
            
            logger.info("上下文压缩完成")
            return compressed
            
        except Exception as e:
            logger.error(f"压缩上下文失败: {str(e)}")
            return context  # 如果压缩失败，返回原始上下文
