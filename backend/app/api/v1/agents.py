"""智能体管理API路由"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.config import Settings

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
    model_id: int = Query(None, description="关联的模型ID"),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建智能体接口
    
    Args:
        agent_in: 智能体创建信息
        model_id: 关联的模型ID（可选）
        db: 数据库会话
    
    Returns:
        创建成功的智能体信息
    """
    agent = create_agent(db=db, agent=agent_in, user_id=1, model_id=model_id)  # 使用固定用户ID 1
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
    settings = Settings()
    if agent.avatar:
        if agent.avatar.startswith(('http://', 'https://')):
            agent_dict['avatar_url'] = agent.avatar
        else:
            agent_dict['avatar_url'] = f"http://localhost:{settings.server_port}/logos/agents/{agent.avatar}"
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
    
    # 转换智能体列表，并手动添加avatar_url字段和分类信息
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        settings = Settings()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"http://localhost:{settings.server_port}/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        
        # 添加分类信息
        if agent.category:
            agent_dict['category'] = {
                'id': agent.category.id,
                'name': agent.category.name,
                'logo': agent.category.logo
            }
        # 确保包含category_id字段
        agent_dict['category_id'] = agent.category_id
        
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
        settings = Settings()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"http://localhost:{settings.server_port}/logos/agents/{agent.avatar}"
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
        settings = Settings()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"http://localhost:{settings.server_port}/logos/agents/{agent.avatar}"
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
    
    # 转换为响应模型，确保包含所有字段
    agent_dict = AgentResponse.from_orm(agent).dict()
    
    # 添加头像URL
    settings = Settings()
    if agent.avatar:
        if agent.avatar.startswith(('http://', 'https://')):
            agent_dict['avatar_url'] = agent.avatar
        else:
            agent_dict['avatar_url'] = f"http://localhost:{settings.server_port}/logos/agents/{agent.avatar}"
    else:
        agent_dict['avatar_url'] = None
    
    # 添加分类信息 - 确保包含category_id字段
    agent_dict['category_id'] = agent.category_id
    
    # 添加分类详细信息
    if agent.category:
        agent_dict['category'] = {
            'id': agent.category.id,
            'name': agent.category.name,
            'logo': agent.category.logo
        }
    
    return agent_dict


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


# 智能体技能相关接口
@router.post("/{agent_id}/skills/{skill_id}")
def bind_skill_to_agent_api(
    agent_id: int,
    skill_id: int,
    priority: int = Query(0, description="技能调用优先级"),
    config: dict = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    绑定技能到智能体
    
    Args:
        agent_id: 智能体ID
        skill_id: 技能ID
        priority: 技能调用优先级
        config: 技能调用配置
        db: 数据库会话
    
    Returns:
        绑定结果
    """
    from app.services.agent_skill_service import AgentSkillService
    try:
        AgentSkillService.bind_skill_to_agent(db, agent_id, skill_id, priority, config)
        return {"message": "技能绑定成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{agent_id}/skills/{skill_id}")
def unbind_skill_from_agent_api(
    agent_id: int,
    skill_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    解除智能体与技能的绑定
    
    Args:
        agent_id: 智能体ID
        skill_id: 技能ID
        db: 数据库会话
    
    Returns:
        解除绑定结果
    """
    from app.services.agent_skill_service import AgentSkillService
    success = AgentSkillService.unbind_skill_from_agent(db, agent_id, skill_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能绑定不存在"
        )
    return {"message": "技能解绑成功"}


@router.get("/{agent_id}/skills")
def get_agent_skills_api(
    agent_id: int,
    enabled_only: bool = Query(False, description="是否只返回启用的技能"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体绑定的所有技能
    
    Args:
        agent_id: 智能体ID
        enabled_only: 是否只返回启用的技能
        db: 数据库会话
    
    Returns:
        智能体技能列表
    """
    from app.services.agent_skill_service import AgentSkillService
    skills = AgentSkillService.get_agent_skills(db, agent_id, enabled_only)
    return {"skills": [{
        "skill_id": skill.skill_id,
        "priority": skill.priority,
        "enabled": skill.enabled,
        "config": skill.config
    } for skill in skills]}


@router.put("/{agent_id}/skills/{skill_id}/enable")
def enable_agent_skill_api(
    agent_id: int,
    skill_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    启用智能体的技能
    
    Args:
        agent_id: 智能体ID
        skill_id: 技能ID
        db: 数据库会话
    
    Returns:
        启用结果
    """
    from app.services.agent_skill_service import AgentSkillService
    success = AgentSkillService.enable_skill_for_agent(db, agent_id, skill_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能绑定不存在"
        )
    return {"message": "技能已启用"}


@router.put("/{agent_id}/skills/{skill_id}/disable")
def disable_agent_skill_api(
    agent_id: int,
    skill_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    禁用智能体的技能
    
    Args:
        agent_id: 智能体ID
        skill_id: 技能ID
        db: 数据库会话
    
    Returns:
        禁用结果
    """
    from app.services.agent_skill_service import AgentSkillService
    success = AgentSkillService.disable_skill_for_agent(db, agent_id, skill_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能绑定不存在"
        )
    return {"message": "技能已禁用"}


@router.post("/{agent_id}/skills/{skill_id}/execute")
def execute_agent_skill_api(
    agent_id: int,
    skill_id: int,
    input_params: dict = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    执行智能体的技能
    
    Args:
        agent_id: 智能体ID
        skill_id: 技能ID
        input_params: 技能输入参数
        db: 数据库会话
    
    Returns:
        技能执行结果
    """
    from app.services.agent_skill_service import AgentSkillService
    try:
        result = AgentSkillService.execute_skill_by_agent(db, agent_id, skill_id, input_params)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )