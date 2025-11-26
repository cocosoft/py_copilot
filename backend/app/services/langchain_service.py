"""LangChain服务模块"""
from typing import Dict, Any, List, Optional
from langchain.chains import LLMChain, SequentialChain, TransformChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
import logging

from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class LangChainService:
    """LangChain服务类，用于构建和管理LangChain的链和代理"""
    
    def __init__(self):
        """初始化LangChain服务"""
        self.chains = {}
        self.default_llm = llm_service.get_llm()
    
    def create_llm_chain(
        self,
        prompt_template: str,
        chain_id: Optional[str] = None,
        input_variables: Optional[List[str]] = None,
        **kwargs
    ) -> LLMChain:
        """创建LLM链"""
        try:
            # 解析输入变量（如果没有提供）
            if not input_variables:
                # 简单的变量提取（假设格式为 {variable}）
                import re
                input_variables = re.findall(r'\{(\w+)\}', prompt_template)
            
            prompt = PromptTemplate(
                input_variables=input_variables,
                template=prompt_template
            )
            
            llm = llm_service.get_llm(kwargs.get("model_name"), kwargs.get("provider"))
            
            chain = LLMChain(
                llm=llm,
                prompt=prompt,
                verbose=settings.debug
            )
            
            # 缓存链
            if chain_id:
                self.chains[chain_id] = chain
            
            return chain
            
        except Exception as e:
            logger.error(f"Error creating LLM chain: {str(e)}")
            raise
    
    def create_conversation_chain(
        self,
        system_message: str = "你是一个有帮助的AI助手",
        chain_id: Optional[str] = None,
        use_summary: bool = False,
        **kwargs
    ) -> LLMChain:
        """创建对话链"""
        try:
            llm = llm_service.get_llm(kwargs.get("model_name"), kwargs.get("provider"))
            
            # 创建记忆组件
            if use_summary:
                memory = ConversationSummaryMemory(llm=llm)
            else:
                memory = ConversationBufferMemory()
            
            # 创建提示模板
            template = f"{system_message}\n\n{{chat_history}}\n\nHuman: {{input}}\n\nAI: "
            prompt = PromptTemplate(
                input_variables=["chat_history", "input"],
                template=template
            )
            
            chain = LLMChain(
                llm=llm,
                prompt=prompt,
                memory=memory,
                verbose=settings.debug
            )
            
            # 缓存链
            if chain_id:
                self.chains[chain_id] = chain
            
            return chain
            
        except Exception as e:
            logger.error(f"Error creating conversation chain: {str(e)}")
            raise
    
    def create_sequential_chain(
        self,
        chains: List[LLMChain],
        input_variables: List[str],
        output_variables: List[str],
        chain_id: Optional[str] = None
    ) -> SequentialChain:
        """创建顺序链"""
        try:
            sequential_chain = SequentialChain(
                chains=chains,
                input_variables=input_variables,
                output_variables=output_variables,
                verbose=settings.debug
            )
            
            # 缓存链
            if chain_id:
                self.chains[chain_id] = sequential_chain
            
            return sequential_chain
            
        except Exception as e:
            logger.error(f"Error creating sequential chain: {str(e)}")
            raise
    
    def create_transform_chain(
        self,
        input_variables: List[str],
        output_variables: List[str],
        transform_func,
        chain_id: Optional[str] = None
    ) -> TransformChain:
        """创建转换链"""
        try:
            transform_chain = TransformChain(
                input_variables=input_variables,
                output_variables=output_variables,
                transform=transform_func
            )
            
            # 缓存链
            if chain_id:
                self.chains[chain_id] = transform_chain
            
            return transform_chain
            
        except Exception as e:
            logger.error(f"Error creating transform chain: {str(e)}")
            raise
    
    def create_agent(
        self,
        tools: List[Tool],
        agent_type: AgentType = AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        chain_id: Optional[str] = None,
        **kwargs
    ):  # 返回类型取决于agent_type
        """创建代理"""
        try:
            llm = llm_service.get_llm(kwargs.get("model_name"), kwargs.get("provider"))
            
            agent = initialize_agent(
                tools=tools,
                llm=llm,
                agent=agent_type,
                verbose=settings.debug
            )
            
            # 缓存代理
            if chain_id:
                self.chains[chain_id] = agent
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    def get_chain(self, chain_id: str) -> Any:
        """获取缓存的链或代理"""
        if chain_id not in self.chains:
            raise KeyError(f"Chain with ID '{chain_id}' not found")
        
        return self.chains[chain_id]
    
    def run_chain(self, chain_id: str, **inputs) -> Dict[str, Any]:
        """运行缓存的链"""
        try:
            chain = self.get_chain(chain_id)
            result = chain.run(**inputs)
            
            return {
                "result": result,
                "chain_id": chain_id,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error running chain {chain_id}: {str(e)}")
            return {
                "error": str(e),
                "chain_id": chain_id,
                "success": False
            }


# 创建全局LangChain服务实例
langchain_service = LangChainService()