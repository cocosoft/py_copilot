"""智能体管理API路由"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.core.config import Settings
from app.models.user import User
from app.utils.cache_decorators import cache_result

from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse
from app.services.agent_service import (
    create_agent,
    get_agent,
    get_agents,
    update_agent,
    delete_agent,
    get_public_agents,
    get_recommended_agents,
    search_agents,
    test_agent,
    copy_agent,
    restore_agent,
    get_deleted_agents,
    export_agent,
    import_agent
)

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent_api(
    agent_in: AgentCreate,
    model_id: int = Query(None, description="关联的模型ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建智能体接口
    
    Args:
        agent_in: 智能体创建信息
        model_id: 关联的模型ID（可选）
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        创建成功的智能体信息
    """
    agent = create_agent(db=db, agent=agent_in, user_id=current_user.id, model_id=model_id)
    return agent


@router.get("/{agent_id}", response_model=dict)
def get_agent_api(
    agent_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    根据ID获取智能体接口
    
    Args:
        agent_id: 智能体ID
        request: FastAPI请求对象
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
    
    agent_dict = AgentResponse.from_orm(agent).dict()
    
    if agent.avatar:
        if agent.avatar.startswith(('http://', 'https://')):
            agent_dict['avatar_url'] = agent.avatar
        else:
            base_url = str(request.base_url).rstrip('/')
            agent_dict['avatar_url'] = f"{base_url}/logos/agents/{agent.avatar}"
    else:
        agent_dict['avatar_url'] = None
    
    return agent_dict


@router.get("/", response_model=dict)
@cache_result(ttl=300, cache_key_prefix="agents")
def get_agents_api(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = Query(None, description="分类ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体列表接口（缓存5分钟）
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        category_id: 分类ID（可选）
        current_user: 当前用户
        request: FastAPI请求对象
        db: 数据库会话
    
    Returns:
        智能体列表信息
    """
    agents, total = get_agents(db=db, skip=skip, limit=limit, user_id=current_user.id, category_id=category_id)
    
    base_url = str(request.base_url).rstrip('/')
    
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"{base_url}/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        
        if agent.category:
            agent_dict['category'] = {
                'id': agent.category.id,
                'name': agent.category.name,
                'logo': agent.category.logo
            }
        agent_dict['category_id'] = agent.category_id
        
        agent_responses.append(agent_dict)
    
    return {"agents": agent_responses, "total": total}


@router.get("/search", response_model=dict)
def search_agents_api(
    request: Request,
    keyword: str = Query(..., description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    搜索智能体接口
    
    Args:
        keyword: 搜索关键词
        category_id: 分类ID（可选）
        skip: 跳过数量
        limit: 限制数量
        current_user: 当前用户
        request: FastAPI请求对象
        db: 数据库会话
    
    Returns:
        智能体搜索结果
    """
    agents, total = search_agents(
        db=db,
        keyword=keyword,
        user_id=current_user.id,
        category_id=category_id,
        skip=skip,
        limit=limit
    )
    
    base_url = str(request.base_url).rstrip('/')
    
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"{base_url}/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        
        if agent.category:
            agent_dict['category'] = {
                'id': agent.category.id,
                'name': agent.category.name,
                'logo': agent.category.logo
            }
        agent_dict['category_id'] = agent.category_id
        
        agent_responses.append(agent_dict)
    
    return {"agents": agent_responses, "total": total}


@router.get("/public/list", response_model=dict)
def get_public_agents_api(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取公开智能体列表接口
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        request: FastAPI请求对象
        db: 数据库会话
    
    Returns:
        公开智能体列表信息
    """
    agents, total = get_public_agents(db=db, skip=skip, limit=limit)
    
    base_url = str(request.base_url).rstrip('/')
    
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"{base_url}/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        agent_responses.append(agent_dict)
    
    return {"agents": agent_responses, "total": total}


@router.get("/recommended/list", response_model=dict)
def get_recommended_agents_api(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取推荐智能体列表接口
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        request: FastAPI请求对象
        db: 数据库会话
    
    Returns:
        推荐智能体列表信息
    """
    agents, total = get_recommended_agents(db=db, skip=skip, limit=limit)
    
    base_url = str(request.base_url).rstrip('/')
    
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"{base_url}/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        agent_responses.append(agent_dict)
    
    return {"agents": agent_responses, "total": total}


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent_api(
    request: Request,
    agent_id: int,
    agent_in: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新智能体接口
    
    Args:
        agent_id: 智能体ID
        agent_in: 智能体更新信息
        current_user: 当前用户
        request: FastAPI请求对象
        db: 数据库会话
    
    Returns:
        更新后的智能体信息
    
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = update_agent(db=db, agent_id=agent_id, agent_update=agent_in, user_id=current_user.id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    agent_dict = AgentResponse.from_orm(agent).dict()
    
    base_url = str(request.base_url).rstrip('/')
    if agent.avatar:
        if agent.avatar.startswith(('http://', 'https://')):
            agent_dict['avatar_url'] = agent.avatar
        else:
            agent_dict['avatar_url'] = f"{base_url}/logos/agents/{agent.avatar}"
    else:
        agent_dict['avatar_url'] = None
    
    agent_dict['category_id'] = agent.category_id
    
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    删除智能体接口
    
    Args:
        agent_id: 智能体ID
        current_user: 当前用户
        db: 数据库会话
    
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    success = delete_agent(db=db, agent_id=agent_id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    return {"message": "智能体删除成功"}


@router.post("/{agent_id}/restore")
def restore_agent_api(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    恢复已删除的智能体接口
    
    Args:
        agent_id: 智能体ID
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        恢复结果
    
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    success = restore_agent(db=db, agent_id=agent_id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在或未删除"
        )
    return {"message": "智能体恢复成功"}


@router.get("/deleted/list", response_model=dict)
def get_deleted_agents_api(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取已删除智能体列表接口
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        current_user: 当前用户
        request: FastAPI请求对象
        db: 数据库会话
    
    Returns:
        已删除智能体列表信息
    """
    agents, total = get_deleted_agents(db=db, skip=skip, limit=limit, user_id=current_user.id)
    
    base_url = str(request.base_url).rstrip('/')
    
    agent_responses = []
    for agent in agents:
        agent_dict = AgentResponse.from_orm(agent).dict()
        if agent.avatar:
            if agent.avatar.startswith(('http://', 'https://')):
                agent_dict['avatar_url'] = agent.avatar
            else:
                agent_dict['avatar_url'] = f"{base_url}/logos/agents/{agent.avatar}"
        else:
            agent_dict['avatar_url'] = None
        
        if agent.category:
            agent_dict['category'] = {
                'id': agent.category.id,
                'name': agent.category.name,
                'logo': agent.category.logo
            }
        agent_dict['category_id'] = agent.category_id
        
        agent_responses.append(agent_dict)
    
    return {"agents": agent_responses, "total": total}


@router.post("/{agent_id}/test")
def test_agent_api(
    agent_id: int,
    test_message: str = Query("你好，请介绍一下你自己", description="测试消息"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    测试智能体接口
    
    Args:
        agent_id: 智能体ID
        test_message: 测试消息
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        测试结果
    
    Raises:
        HTTPException: 智能体不存在或测试失败时抛出
    """
    try:
        result = test_agent(db=db, agent_id=agent_id, user_id=current_user.id, test_message=test_message)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"测试失败: {result.get('error', '未知错误')}"
            )
        
        return {
            "success": True,
            "response": result.get("response"),
            "model_used": result.get("model_used"),
            "tokens_used": result.get("tokens_used")
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{agent_id}/copy")
def copy_agent_api(
    agent_id: int,
    new_name: str = Query(None, description="新智能体名称"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    复制智能体接口
    
    Args:
        agent_id: 智能体ID
        new_name: 新智能体名称（可选）
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        复制后的智能体信息
    
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    try:
        new_agent = copy_agent(db=db, agent_id=agent_id, user_id=current_user.id, new_name=new_name)
        
        agent_dict = AgentResponse.from_orm(new_agent).dict()
        
        return {
            "message": "智能体复制成功",
            "agent": agent_dict
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{agent_id}/export")
def export_agent_api(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """
    导出智能体配置接口
    
    Args:
        agent_id: 智能体ID
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        智能体配置JSON
    
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    try:
        export_data = export_agent(db=db, agent_id=agent_id, user_id=current_user.id)
        return JSONResponse(content=export_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/import")
def import_agent_api(
    import_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    导入智能体配置接口
    
    Args:
        import_data: 导入数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        导入后的智能体信息
    
    Raises:
        HTTPException: 数据格式错误时抛出
    """
    try:
        new_agent = import_agent(db=db, import_data=import_data, user_id=current_user.id)
        
        agent_dict = AgentResponse.from_orm(new_agent).dict()
        
        return {
            "message": "智能体导入成功",
            "agent": agent_dict
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


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