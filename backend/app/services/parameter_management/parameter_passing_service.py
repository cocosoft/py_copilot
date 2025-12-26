"""参数传递服务 - 桥接参数管理系统与LLM服务"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.services.parameter_management.agent_parameter_manager import AgentParameterManager
from app.services.parameter_management.parameter_manager import ParameterManager


class ParameterPassingService:
    """参数传递服务，负责将参数从管理系统传递到LLM服务调用"""
    
    @staticmethod
    def get_llm_parameters(
        db: Session,
        agent_id: Optional[int] = None,
        model_id: Optional[int] = None,
        include_model_params: bool = True
    ) -> Dict[str, Any]:
        """
        获取LLM调用所需的完整参数
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID（可选）
            model_id: 模型ID（可选，用于回退查询）
            include_model_params: 是否包含模型参数
            
        Returns:
            合并后的LLM调用参数字典
        """
        params = {}
        
        if agent_id:
            agent_params = AgentParameterManager.get_effective_parameters(db, agent_id)
            params.update(agent_params)
        
        if include_model_params and model_id and not agent_id:
            model_params = ParameterManager.get_model_parameters(db, model_id)
            for param in model_params:
                if param["parameter_name"] not in params:
                    params[param["parameter_name"]] = param["parameter_value"]
        
        return params
    
    @staticmethod
    def get_llm_kwargs(
        db: Session,
        agent_id: Optional[int] = None,
        model_id: Optional[int] = None,
        **overrides
    ) -> Dict[str, Any]:
        """
        获取LLM方法调用的kwargs
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            model_id: 模型ID
            **overrides: 覆盖参数
            
        Returns:
            可直接传递给LLM方法的kwargs字典
        """
        params = ParameterPassingService.get_llm_parameters(db, agent_id, model_id)
        
        kwargs = {
            "model_name": params.get("model_name"),
            "max_tokens": int(params.get("max_tokens", 1000)) if params.get("max_tokens") else 1000,
            "temperature": float(params.get("temperature", 0.7)) if params.get("temperature") else 0.7,
            "top_p": float(params.get("top_p", 1.0)) if params.get("top_p") else 1.0,
            "frequency_penalty": float(params.get("frequency_penalty", 0.0)) if params.get("frequency_penalty") else 0.0,
            "presence_penalty": float(params.get("presence_penalty", 0.0)) if params.get("presence_penalty") else 0.0,
        }
        
        kwargs.update({k: v for k, v in overrides.items() if v is not None})
        
        return kwargs
    
    @staticmethod
    def get_chat_completion_kwargs(
        db: Session,
        agent_id: Optional[int] = None,
        model_id: Optional[int] = None,
        **overrides
    ) -> Dict[str, Any]:
        """
        获取chat_completion方法的kwargs
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            model_id: 模型ID
            **overrides: 覆盖参数
            
        Returns:
            可直接传递给chat_completion的kwargs
        """
        base_kwargs = ParameterPassingService.get_llm_kwargs(db, agent_id, model_id, **overrides)
        
        chat_kwargs = {
            "model_name": base_kwargs.get("model_name"),
            "max_tokens": base_kwargs.get("max_tokens"),
            "temperature": base_kwargs.get("temperature"),
            "top_p": base_kwargs.get("top_p"),
            "frequency_penalty": base_kwargs.get("frequency_penalty"),
            "presence_penalty": base_kwargs.get("presence_penalty"),
            "db": db,
        }
        
        return {k: v for k, v in chat_kwargs.items() if v is not None}
    
    @staticmethod
    def get_text_completion_kwargs(
        db: Session,
        agent_id: Optional[int] = None,
        model_id: Optional[int] = None,
        **overrides
    ) -> Dict[str, Any]:
        """
        获取text_completion方法的kwargs
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            model_id: 模型ID
            **overrides: 覆盖参数
            
        Returns:
            可直接传递给text_completion的kwargs
        """
        base_kwargs = ParameterPassingService.get_llm_kwargs(db, agent_id, model_id, **overrides)
        
        text_kwargs = {
            "model_name": base_kwargs.get("model_name"),
            "max_tokens": base_kwargs.get("max_tokens"),
            "temperature": base_kwargs.get("temperature"),
            "top_p": base_kwargs.get("top_p"),
            "frequency_penalty": base_kwargs.get("frequency_penalty"),
            "presence_penalty": base_kwargs.get("presence_penalty"),
        }
        
        return {k: v for k, v in text_kwargs.items() if v is not None}
    
    @staticmethod
    def resolve_model_id(db: Session, agent_id: Optional[int] = None, model_id: Optional[int] = None) -> Optional[int]:
        """
        解析最终的模型ID
        
        优先级：
        1. 直接指定的model_id
        2. Agent参数中的model_name对应的model_id
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            model_id: 直接指定的模型ID
            
        Returns:
            解析后的模型ID
        """
        if model_id:
            return model_id
        
        if agent_id:
            agent_params = AgentParameterManager.get_parameters_dict(db, agent_id)
            if agent_params.get("model_name"):
                from app.models.supplier_db import ModelDB
                model = db.query(ModelDB).filter(
                    ModelDB.model_id == agent_params["model_name"]
                ).first()
                if model:
                    return model.id
        
        return None
