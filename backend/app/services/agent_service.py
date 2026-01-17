"""智能体服务层"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.agent import Agent
from app.models.agent_category import AgentCategory
from app.models.supplier_db import ModelDB
from app.schemas.agent import AgentCreate, AgentUpdate
from app.services.parameter_management.agent_parameter_manager import AgentParameterManager


def create_agent(db: Session, agent: AgentCreate, user_id: int, model_id: int = None) -> Agent:
    """创建智能体，支持关联模型并自动继承模型能力和参数"""
    # 创建智能体基本信息
    agent_dict = agent.dict()
    if model_id:
        agent_dict['model_id'] = model_id
    
    db_agent = Agent(**agent_dict, user_id=user_id)
    db.add(db_agent)
    db.flush()  # 刷新以获取agent_id
    
    # 自动继承模型能力和参数
    if model_id:
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if model:
            # 继承模型能力
            # 注意：这里需要根据实际的模型能力获取方式进行调整
            # 假设模型能力存储在model.capabilities字段中
            if hasattr(model, 'capabilities') and model.capabilities:
                db_agent.capabilities = model.capabilities
            
            # 继承模型参数
            # 注意：这里需要根据实际的模型参数获取方式进行调整
            # 假设模型参数存储在model.parameters字段中
            if hasattr(model, 'parameters') and model.parameters:
                for param in model.parameters:
                    AgentParameterManager.create_parameter(
                        db=db,
                        agent_id=db_agent.id,
                        parameter_name=param.get("parameter_name"),
                        parameter_value=param.get("parameter_value"),
                        parameter_type=param.get("parameter_type"),
                        description=param.get("description"),
                        parameter_group=param.get("parameter_group"),
                        source="model",
                        inherited=True,
                        inherited_from=f"model_{model_id}"
                    )
    
    db.commit()
    db.refresh(db_agent)
    return db_agent


def get_agent(db: Session, agent_id: int) -> Optional[Agent]:
    """根据ID获取智能体"""
    return db.query(Agent).filter(Agent.id == agent_id).first()


def get_agents(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None, category_id: Optional[int] = None) -> tuple[List[Agent], int]:
    """获取智能体列表"""
    query = db.query(Agent).options(joinedload(Agent.category))  # 使用joinedload预加载分类信息
    if user_id is not None:
        query = query.filter(Agent.user_id == user_id)
    if category_id is not None:
        query = query.filter(Agent.category_id == category_id)
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    return agents, total


def update_agent(db: Session, agent_id: int, agent_update: AgentUpdate, user_id: int) -> Optional[Agent]:
    """更新智能体"""
    db_agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id).first()
    if not db_agent:
        return None
    
    # 获取更新数据，只包含实际设置的字段（排除未设置的字段）
    update_data = agent_update.dict(exclude_unset=True)
    
    # 只更新实际提供的字段，避免将必填字段设置为None
    for key, value in update_data.items():
        setattr(db_agent, key, value)
    
    db.commit()
    db.refresh(db_agent)
    return db_agent


def delete_agent(db: Session, agent_id: int, user_id: int) -> bool:
    """删除智能体"""
    # 使用更安全的方式删除，避免加载关联关系
    try:
        # 首先检查智能体是否存在
        agent_exists = db.query(Agent.id).filter(Agent.id == agent_id, Agent.user_id == user_id).first()
        if not agent_exists:
            return False
        
        # 直接执行删除操作，避免加载关联对象
        db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"删除智能体时出错: {e}")
        return False


def get_public_agents(db: Session, skip: int = 0, limit: int = 100) -> tuple[List[Agent], int]:
    """获取公开智能体列表"""
    query = db.query(Agent).filter(Agent.is_public == True)
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    return agents, total


def get_recommended_agents(db: Session, skip: int = 0, limit: int = 100) -> tuple[List[Agent], int]:
    """获取推荐智能体列表"""
    query = db.query(Agent).filter(Agent.is_recommended == True)
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    return agents, total