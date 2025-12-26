"""智能体参数管理API路由"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.agent_parameter import (
    AgentParameterCreate,
    AgentParameterUpdate,
    AgentParameterResponse,
    AgentParameterListResponse,
    AgentParametersBulkCreate,
    AgentParameterEffectiveResponse,
    AgentParametersWithSourceResponse,
    AgentParametersValidationResponse
)
from app.services.agent_service import get_agent
from app.services.parameter_management.agent_parameter_manager import AgentParameterManager
from app.models.agent_parameter import AgentParameter

router = APIRouter()


@router.get("/{agent_id}/parameters", response_model=AgentParameterListResponse)
def get_agent_parameters(
    agent_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    parameter_group: Optional[str] = Query(None, description="参数分组筛选"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体的所有参数
    
    Args:
        agent_id: 智能体ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        parameter_group: 参数分组筛选
        db: 数据库会话
        
    Returns:
        智能体参数列表
        
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    query = db.query(AgentParameterManager.__class__).filter(
        AgentParameterManager.__tablename__ == "agent_parameters"
    )
    
    params = db.query(AgentParameter).filter(
        AgentParameter.agent_id == agent_id
    )
    
    if parameter_group:
        params = params.filter(AgentParameter.parameter_group == parameter_group)
    
    params = params.offset(skip).limit(limit).all()
    total = db.query(AgentParameter).filter(
        AgentParameter.agent_id == agent_id
    ).count()
    
    return AgentParameterListResponse(
        parameters=params,
        total=total
    )


@router.get("/{agent_id}/parameters/effective", response_model=AgentParameterEffectiveResponse)
def get_effective_parameters(
    agent_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体的有效参数（包含继承自模型的参数）
    
    Args:
        agent_id: 智能体ID
        db: 数据库会话
        
    Returns:
        智能体有效参数（包含继承的模型参数）
        
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    effective_params = AgentParameterManager.get_effective_parameters(db, agent_id)
    
    return AgentParameterEffectiveResponse(
        agent_id=agent_id,
        parameters=effective_params,
        inherited_from_model=agent.model_id is not None,
        model_id=agent.model_id
    )


@router.get("/{agent_id}/parameters/effective-with-source", response_model=AgentParametersWithSourceResponse)
def get_parameters_with_source(
    agent_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体的有效参数（包含来源信息）
    
    Args:
        agent_id: 智能体ID
        db: 数据库会话
        
    Returns:
        智能体参数列表（包含来源信息）
        
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    params_with_source = AgentParameterManager.get_effective_parameters_with_source(db, agent_id)
    
    return AgentParametersWithSourceResponse(
        agent_id=agent_id,
        parameters=params_with_source
    )


@router.post("/{agent_id}/parameters", response_model=AgentParameterResponse, status_code=status.HTTP_201_CREATED)
def create_agent_parameter(
    agent_id: int,
    param_in: AgentParameterCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    创建智能体参数
    
    Args:
        agent_id: 智能体ID
        param_in: 参数创建数据
        db: 数据库会话
        
    Returns:
        创建的智能体参数
        
    Raises:
        HTTPException: 智能体不存在或参数值类型不匹配时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    try:
        param = AgentParameterManager.create_parameter(
            db=db,
            agent_id=agent_id,
            parameter_name=param_in.parameter_name,
            parameter_value=param_in.parameter_value,
            parameter_type=param_in.parameter_type,
            description=param_in.description,
            parameter_group=param_in.parameter_group
        )
        return param
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{agent_id}/parameters/bulk", response_model=List[AgentParameterResponse], status_code=status.HTTP_201_CREATED)
def create_agent_parameters_bulk(
    agent_id: int,
    params_in: AgentParametersBulkCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    批量创建智能体参数
    
    Args:
        agent_id: 智能体ID
        params_in: 批量参数创建数据
        db: 数据库会话
        
    Returns:
        创建的智能体参数列表
        
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    created_params = AgentParameterManager.create_parameters_bulk(
        db=db,
        agent_id=agent_id,
        parameters=params_in.parameters,
        parameter_group=params_in.parameter_group
    )
    
    return created_params


@router.get("/{agent_id}/parameters/{parameter_name}", response_model=AgentParameterResponse)
def get_agent_parameter(
    agent_id: int,
    parameter_name: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体的特定参数
    
    Args:
        agent_id: 智能体ID
        parameter_name: 参数名称
        db: 数据库会话
        
    Returns:
        智能体参数
        
    Raises:
        HTTPException: 智能体或参数不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    param = AgentParameterManager.get_parameter(db, agent_id, parameter_name)
    if not param:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"参数 '{parameter_name}' 不存在"
        )
    
    return param


@router.put("/{agent_id}/parameters/{parameter_name}", response_model=AgentParameterResponse)
def update_agent_parameter(
    agent_id: int,
    parameter_name: str,
    param_in: AgentParameterUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """
    更新智能体参数
    
    Args:
        agent_id: 智能体ID
        parameter_name: 参数名称
        param_in: 参数更新数据
        db: 数据库会话
        
    Returns:
        更新后的智能体参数
        
    Raises:
        HTTPException: 智能体或参数不存在或参数值类型不匹配时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    try:
        param = AgentParameterManager.update_parameter(
            db=db,
            agent_id=agent_id,
            parameter_name=parameter_name,
            parameter_value=param_in.parameter_value,
            parameter_type=param_in.parameter_type,
            description=param_in.description,
            parameter_group=param_in.parameter_group
        )
        
        if not param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"参数 '{parameter_name}' 不存在"
            )
        
        return param
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{agent_id}/parameters/{parameter_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_parameter(
    agent_id: int,
    parameter_name: str,
    db: Session = Depends(get_db)
):
    """
    删除智能体参数
    
    Args:
        agent_id: 智能体ID
        parameter_name: 参数名称
        db: 数据库会话
        
    Returns:
        无内容
        
    Raises:
        HTTPException: 智能体或参数不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    success = AgentParameterManager.delete_parameter(db, agent_id, parameter_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"参数 '{parameter_name}' 不存在"
        )


@router.delete("/{agent_id}/parameters", response_model=Dict[str, int])
def delete_all_agent_parameters(
    agent_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    删除智能体的所有参数
    
    Args:
        agent_id: 智能体ID
        db: 数据库会话
        
    Returns:
        删除的参数数量
        
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    deleted_count = AgentParameterManager.delete_all_parameters(db, agent_id)
    
    return {"deleted_count": deleted_count}


@router.post("/{agent_id}/parameters/validate", response_model=AgentParametersValidationResponse)
def validate_agent_parameters(
    agent_id: int,
    parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    校验智能体参数的有效性
    
    Args:
        agent_id: 智能体ID
        parameters: 要校验的参数（默认校验所有参数）
        db: 数据库会话
        
    Returns:
        校验结果
        
    Raises:
        HTTPException: 智能体不存在时抛出
    """
    agent = get_agent(db=db, agent_id=agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    errors = AgentParameterManager.validate_parameters(db, agent_id, parameters)
    
    return AgentParametersValidationResponse(
        valid=len(errors) == 0,
        errors=errors
    )
