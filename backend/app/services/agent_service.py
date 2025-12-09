"""智能体服务层"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


def create_agent(db: Session, agent: AgentCreate, user_id: int) -> Agent:
    """创建智能体"""
    db_agent = Agent(**agent.dict(), user_id=user_id)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def get_agent(db: Session, agent_id: int) -> Optional[Agent]:
    """根据ID获取智能体"""
    return db.query(Agent).filter(Agent.id == agent_id).first()


def get_agents(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> tuple[List[Agent], int]:
    """获取智能体列表"""
    query = db.query(Agent)
    if user_id is not None:
        query = query.filter(Agent.user_id == user_id)
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    return agents, total


def update_agent(db: Session, agent_id: int, agent_update: AgentUpdate, user_id: int) -> Optional[Agent]:
    """更新智能体"""
    db_agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id).first()
    if not db_agent:
        return None
    
    update_data = agent_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)
    
    db.commit()
    db.refresh(db_agent)
    return db_agent


def delete_agent(db: Session, agent_id: int, user_id: int) -> bool:
    """删除智能体"""
    db_agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id).first()
    if not db_agent:
        return False
    
    db.delete(db_agent)
    db.commit()
    return True


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