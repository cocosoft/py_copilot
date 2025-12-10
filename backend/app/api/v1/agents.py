"""智能体管理API路由"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db

from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse
from app.services.agent_service import (
    create_agent,
    get_agent,
    get_agents,
    update_agent,
    delete_agent,
    get_public_agents,
    get_recommended_agents
)

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent_api(
    agent_in: AgentCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    创建智能体接口
    
    Args:
        agent_in: 智能体创建信息
        db: 数据库会话
    
    Returns:
        创建成功的智能体信息
    """
    agent = create_agent(db=db, agent=agent_in, user_id=1)  # 使用固定用户ID 1
    return agent


@router.get("/{agent_id}", response_model=dict)
def get_agent_api(
    agent_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    根据ID获取智能体接口
    
    Args:
        agent_id: 智能体ID
        db: 数据库会话
    
    Returns:
        智能体信息
    
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    # 将Agent模型转换为字典
    agent_dict = AgentResponse.from_orm(agent).dict()
    
    # 手动添加avatar_url字段
    if agent.avatar:
        if agent.avatar.startswith(('http://', 'https://')):
            agent_dict['avatar_url'] = agent.avatar
        else:
            agent_dict['avatar_url'] = f"/logos/agents/{agent.avatar}"
    else:
        agent_dict['avatar_url'] = None
    
    return agent_dict


@router.get("/", response_model=dict)
def get_agents_api(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category_id: int = Query(None, ge=1),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体列表接口
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        category_id: 分类ID（可选）
        db: 数据库会话
    
    Returns:
        智能体列表信息
    """
    agents, total = get_agents(db=db, skip=skip, limit=limit, user_id=1, category_id=category_id)  # 使用固定用户ID 1
    
    # 转换智能体列表，并手动添加avatar_url字段
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        agent_responses.append(agent_dict)
    
    return {"agents": agent_responses, "total": total}


@router.get("/public/list", response_model=dict)
def get_public_agents_api(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取公开智能体列表接口
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
    
    Returns:
        公开智能体列表信息
    """
    agents, total = get_public_agents(db=db, skip=skip, limit=limit)
    
    # 转换智能体列表，并手动添加avatar_url字段
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        agent_responses.append(agent_dict)
    
    return {"agents": agent_responses, "total": total}


@router.get("/recommended/list", response_model=dict)
def get_recommended_agents_api(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取推荐智能体列表接口
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
    
    Returns:
        推荐智能体列表信息
    """
    agents, total = get_recommended_agents(db=db, skip=skip, limit=limit)
    
    # 转换智能体列表，并手动添加avatar_url字段
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        agent_responses.append(agent_dict)
    
    return {"agents": agent_responses, "total": total}


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent_api(
    agent_id: int,
    agent_in: AgentUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """
    更新智能体接口
    
    Args:
        agent_id: 智能体ID
        agent_in: 智能体更新信息
        db: 数据库会话
    
    Returns:
        更新后的智能体信息
    
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = update_agent(db=db, agent_id=agent_id, agent_update=agent_in, user_id=1)  # 使用固定用户ID 1
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    return agent


@router.delete("/{agent_id}")
def delete_agent_api(
    agent_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    删除智能体接口
    
    Args:
        agent_id: 智能体ID
        db: 数据库会话
    
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    success = delete_agent(db=db, agent_id=agent_id, user_id=1)  # 使用固定用户ID 1
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    return {"message": "智能体删除成功"}