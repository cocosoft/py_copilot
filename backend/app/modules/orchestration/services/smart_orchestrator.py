"""智能体编排系统核心服务"""
from typing import Dict, Any, Optional
from app.modules.orchestration.services.context_manager import ContextManager
from app.modules.orchestration.services.intent_recognizer import IntentRecognizer
from app.modules.orchestration.services.agent_selector import AgentSelector
from app.modules.orchestration.services.capability_matcher import CapabilityMatcher
from app.modules.orchestration.services.skill_composer import SkillComposer
from app.modules.workflow.services.workflow_service import WorkflowService
from app.services.llm_service import LLMService
from app.core.database import get_db
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class SmartOrchestrator:
    """智能体编排系统核心类"""
    
    def __init__(self, 
                 context_manager: Optional[ContextManager] = None, 
                 intent_recognizer: Optional[IntentRecognizer] = None, 
                 llm_service: Optional[LLMService] = None,
                 agent_selector: Optional[AgentSelector] = None,
                 capability_matcher: Optional[CapabilityMatcher] = None,
                 skill_composer: Optional[SkillComposer] = None):
        self.context_manager = context_manager or ContextManager()
        self.intent_recognizer = intent_recognizer or IntentRecognizer()
        self.llm_service = llm_service or LLMService()
        self.agent_selector = agent_selector or AgentSelector()
        self.capability_matcher = capability_matcher or CapabilityMatcher()
        self.skill_composer = skill_composer or SkillComposer()
        
    async def orchestrate(self, user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心编排逻辑
        
        Args:
            user_input: 用户输入文本
            user_context: 用户上下文信息，包含user_id、conversation_id等
            
        Returns:
            编排执行结果
        """
        try:
            logger.info(f"开始智能编排流程，用户输入: {user_input[:100]}...")
            
            # 1. 意图识别
            intent_result = await self._intent_recognition(user_input, user_context)
            intent_type = intent_result["type"]
            logger.info(f"意图识别结果: {intent_type}")
            
            # 2. 上下文增强
            enhanced_context = await self.context_manager.enhance_context(
                user_input, 
                user_context, 
                intent_result
            )
            logger.debug(f"增强上下文: {enhanced_context}")
            
            # 3. 路由决策
            route = await self._route_decision(intent_type, enhanced_context)
            logger.info(f"路由决策结果: {route}")
            
            # 4. 执行对应的处理流程
            if route == "knowledge_query":
                result = await self._execute_knowledge_query(user_input, enhanced_context)
            elif route == "workflow_generation":
                result = await self._execute_workflow_generation(user_input, enhanced_context)
            elif route == "sentiment_analysis":
                result = await self._execute_sentiment_analysis(user_input, enhanced_context)
            elif route == "entity_extraction":
                result = await self._execute_entity_extraction(user_input, enhanced_context)
            else:
                # 默认使用LLM直接回答
                result = await self._execute_direct_llm(user_input, enhanced_context)
            
            logger.info(f"智能编排流程完成")
            return {
                "success": True,
                "result": result,
                "intent": intent_type,
                "route": route
            }
            
        except Exception as e:
            logger.error(f"智能编排流程失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "智能编排流程执行失败"
            }
    
    async def _intent_recognition(self, user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        意图识别
        
        Args:
            user_input: 用户输入文本
            user_context: 用户上下文信息
            
        Returns:
            意图识别结果
        """
        return await self.intent_recognizer.recognize_intent(user_input, user_context)
    
    async def _route_decision(self, intent_type: str, context: Dict[str, Any]) -> str:
        """
        路由决策
        
        Args:
            intent_type: 意图类型
            context: 上下文信息
            
        Returns:
            路由路径
        """
        # 基于意图类型进行路由决策
        route_mapping = {
            "knowledge_query": "knowledge_query",
            "workflow_generation": "workflow_generation",
            "sentiment_analysis": "sentiment_analysis",
            "entity_extraction": "entity_extraction",
            "relationship_analysis": "knowledge_query",
            "condition_judgment": "workflow_generation",
            "data_processing": "workflow_generation"
        }
        
        return route_mapping.get(intent_type, "direct_llm")
    
    async def _execute_knowledge_query(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行知识查询
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息
            
        Returns:
            查询结果
        """
        # 这里应该调用知识库检索服务
        logger.info(f"执行知识查询: {user_input}")
        
        # 模拟知识库查询结果
        return {
            "type": "knowledge_query",
            "content": f"知识库查询结果: {user_input}"
        }
    
    async def _execute_workflow_generation(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工作流生成
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息
            
        Returns:
            工作流生成结果
        """
        logger.info(f"执行工作流生成: {user_input}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 创建工作流服务实例
        workflow_service = WorkflowService(db)
        
        # 使用WorkflowAutoComposer生成工作流
        user_id = context.get("user_id", 1)
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        # 生成工作流
        workflow = await workflow_service.create_workflow_from_description(user_input, user_id)
        
        return {
            "type": "workflow_generation",
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "nodes_count": len(workflow.definition.get("nodes", [])),
            "edges_count": len(workflow.definition.get("edges", []))
        }
    
    async def _execute_sentiment_analysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行情感分析
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息
            
        Returns:
            情感分析结果
        """
        logger.info(f"执行情感分析: {user_input}")
        
        # 调用LLM进行情感分析
        messages = [
            {"role": "system", "content": "请分析以下文本的情感倾向，返回正面、负面或中性，并给出置信度。"},
            {"role": "user", "content": user_input}
        ]
        
        result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
        
        return {
            "type": "sentiment_analysis",
            "content": result["generated_text"]
        }
    
    async def _execute_entity_extraction(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行实体提取
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息
            
        Returns:
            实体提取结果
        """
        logger.info(f"执行实体提取: {user_input}")
        
        # 调用LLM进行实体提取
        messages = [
            {"role": "system", "content": "请从以下文本中提取实体，包括人物、地点、组织等，并分类列出。"},
            {"role": "user", "content": user_input}
        ]
        
        result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
        
        return {
            "type": "entity_extraction",
            "content": result["generated_text"]
        }
    
    async def _execute_direct_llm(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        直接调用LLM回答
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息
            
        Returns:
            LLM回答结果
        """
        logger.info(f"直接调用LLM回答: {user_input}")
        
        # 直接调用LLM回答
        messages = [
            {"role": "system", "content": "请直接回答用户的问题。"},
            {"role": "user", "content": user_input}
        ]
        
        result = await self.llm_service.chat_completion(messages, model_name="gpt-3.5-turbo")
        
        return {
            "type": "direct_llm",
            "content": result["generated_text"]
        }
