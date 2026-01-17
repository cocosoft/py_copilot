"""智能体能力服务层"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.agent import Agent
from app.models.supplier_db import ModelDB
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.services.parameter_management.agent_parameter_manager import AgentParameterManager


class AgentCapabilityService:
    """智能体能力服务类，负责智能体对模型能力的动态承接"""
    
    @staticmethod
    def get_agent_model_capabilities(db: Session, agent_id: int) -> List[Dict[str, Any]]:
        """获取智能体关联模型的所有能力"""
        # 获取智能体信息，加载关联的模型
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent or not agent.model_id:
            return []
        
        # 获取模型信息，加载关联的能力
        model = db.query(ModelDB).options(
            joinedload(ModelDB.capabilities)
        ).filter(ModelDB.id == agent.model_id).first()
        
        if not model:
            return []
        
        # 转换能力信息为字典格式
        capabilities = []
        for capability in model.capabilities:
            capabilities.append({
                "id": capability.id,
                "name": capability.name,
                "display_name": capability.display_name,
                "description": capability.description,
                "capability_dimension": capability.capability_dimension,
                "capability_subdimension": capability.capability_subdimension,
                "base_strength": capability.base_strength,
                "max_strength": capability.max_strength,
                "input_types": capability.input_types,
                "output_types": capability.output_types
            })
        
        return capabilities
    
    @staticmethod
    def get_agent_capabilities(db: Session, agent_id: int) -> List[Dict[str, Any]]:
        """获取智能体的所有能力（包括继承的模型能力和自定义能力）"""
        # 获取智能体信息
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return []
        
        capabilities = []
        
        # 获取继承的模型能力
        model_capabilities = AgentCapabilityService.get_agent_model_capabilities(db, agent_id)
        capabilities.extend(model_capabilities)
        
        # 添加智能体自定义能力
        if agent.capabilities and isinstance(agent.capabilities, list):
            for custom_cap in agent.capabilities:
                # 确保不重复添加能力
                if not any(cap["name"] == custom_cap.get("name") for cap in capabilities):
                    capabilities.append(custom_cap)
        
        return capabilities
    
    @staticmethod
    def update_agent_capabilities(db: Session, agent_id: int, capabilities: List[Dict[str, Any]]) -> Agent:
        """更新智能体的自定义能力"""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"智能体不存在，ID: {agent_id}")
        
        agent.capabilities = capabilities
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        return agent
    
    @staticmethod
    def get_capability_details(db: Session, capability_id: int) -> Optional[Dict[str, Any]]:
        """获取能力的详细信息"""
        capability = db.query(ModelCapability).filter(ModelCapability.id == capability_id).first()
        if not capability:
            return None
        
        return {
            "id": capability.id,
            "name": capability.name,
            "display_name": capability.display_name,
            "description": capability.description,
            "capability_dimension": capability.capability_dimension,
            "capability_subdimension": capability.capability_subdimension,
            "base_strength": capability.base_strength,
            "max_strength": capability.max_strength,
            "input_types": capability.input_types,
            "output_types": capability.output_types,
            "assessment_metrics": capability.assessment_metrics,
            "benchmark_datasets": capability.benchmark_datasets
        }
    
    @staticmethod
    def inherit_model_capabilities(db: Session, agent_id: int, model_id: int) -> Agent:
        """让智能体继承模型的能力"""
        # 获取智能体信息
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"智能体不存在，ID: {agent_id}")
        
        # 获取模型信息
        model = db.query(ModelDB).options(
            joinedload(ModelDB.capabilities)
        ).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型不存在，ID: {model_id}")
        
        # 继承模型能力
        inherited_capabilities = []
        for capability in model.capabilities:
            inherited_capabilities.append({
                "id": capability.id,
                "name": capability.name,
                "display_name": capability.display_name,
                "source": "model",
                "model_id": model_id,
                "inherited": True
            })
        
        # 如果智能体已有自定义能力，合并它们
        if agent.capabilities and isinstance(agent.capabilities, list):
            # 过滤掉重复的能力（基于名称）
            capability_names = {cap["name"] for cap in inherited_capabilities}
            for custom_cap in agent.capabilities:
                if custom_cap.get("name") not in capability_names:
                    inherited_capabilities.append(custom_cap)
        
        # 更新智能体能力
        agent.capabilities = inherited_capabilities
        agent.model_id = model_id
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        # 同时继承模型的参数
        AgentCapabilityService.inherit_model_parameters(db, agent_id, model_id)
        
        return agent
    
    @staticmethod
    def inherit_model_parameters(db: Session, agent_id: int, model_id: int) -> None:
        """让智能体继承模型的参数"""
        # 获取模型信息
        model = db.query(ModelDB).options(
            joinedload(ModelDB.parameters)
        ).filter(ModelDB.id == model_id).first()
        if not model:
            return
        
        # 继承模型参数
        for model_param in model.parameters:
            # 检查参数是否已存在
            existing_param = AgentParameterManager.get_parameter(
                db=db,
                agent_id=agent_id,
                parameter_name=model_param.parameter_name
            )
            
            if not existing_param:
                # 创建新参数，标记为继承自模型
                AgentParameterManager.create_parameter(
                    db=db,
                    agent_id=agent_id,
                    parameter_name=model_param.parameter_name,
                    parameter_value=model_param.parameter_value,
                    parameter_type=model_param.parameter_type,
                    description=model_param.description,
                    parameter_group=model_param.parameter_group,
                    source="model",
                    inherited=True,
                    inherited_from=f"model_{model_id}"
                )
    
    @staticmethod
    def update_agent_capability_strength(db: Session, agent_id: int, capability_name: str, strength: int) -> Agent:
        """更新智能体特定能力的强度（如果支持）"""
        # 获取智能体信息
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent or not agent.capabilities:
            raise ValueError(f"智能体不存在或无能力设置，ID: {agent_id}")
        
        # 更新能力强度
        updated = False
        for cap in agent.capabilities:
            if cap.get("name") == capability_name and isinstance(cap, dict):
                # 检查强度是否在有效范围内
                if strength < 1 or strength > cap.get("max_strength", 5):
                    raise ValueError(f"能力强度必须在1到{cap.get('max_strength', 5)}之间")
                
                cap["base_strength"] = strength
                updated = True
                break
        
        if not updated:
            raise ValueError(f"智能体没有该能力: {capability_name}")
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        return agent
    
    @staticmethod
    def check_agent_capability(db: Session, agent_id: int, capability_name: str) -> bool:
        """检查智能体是否具备特定能力"""
        capabilities = AgentCapabilityService.get_agent_capabilities(db, agent_id)
        return any(cap["name"] == capability_name for cap in capabilities)
    
    @staticmethod
    def get_agent_capability_by_name(db: Session, agent_id: int, capability_name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取智能体的特定能力"""
        capabilities = AgentCapabilityService.get_agent_capabilities(db, agent_id)
        for cap in capabilities:
            if cap["name"] == capability_name:
                return cap
        return None
