"""参数管理API接口

提供参数列表查询功能，支持按级别过滤
"""
from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.models.parameter_template import ParameterTemplate
from app.core.permission_dependencies import get_current_active_user

router = APIRouter()


class ParameterItem(BaseModel):
    """参数项Schema"""
    id: int
    name: str
    description: Optional[str] = None
    key: str
    value: Any
    type: str = "string"
    level: str
    supplier_id: Optional[int] = None
    model_id: Optional[int] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True


class ParameterListResponse(BaseModel):
    """参数列表响应Schema"""
    parameters: List[ParameterItem]
    total: int


@router.get("", response_model=ParameterListResponse)
async def get_parameters(
    level: Optional[str] = Query(None, description="参数级别: model_type, model, agent"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    model_id: Optional[int] = Query(None, description="模型ID"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """
    获取参数列表
    
    根据级别、供应商ID和模型ID过滤参数
    
    Args:
        level: 参数级别 (model_type, model, agent)
        supplier_id: 供应商ID
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        参数列表
    """
    try:
        # 查询参数模板
        query = db.query(ParameterTemplate)
        
        # 根据级别过滤
        if level:
            # 将前端级别映射到场景
            scene_mapping = {
                'model_type': 'chat',
                'model': 'model',
                'agent': 'agent'
            }
            scene = scene_mapping.get(level, level)
            query = query.filter(ParameterTemplate.scene == scene)
        
        # 只返回激活的模板
        query = query.filter(ParameterTemplate.is_active == True)
        
        # 获取模板列表
        templates = query.all()
        
        # 将模板转换为参数列表格式
        parameters = []
        for template in templates:
            if template.parameters and isinstance(template.parameters, dict):
                for key, value in template.parameters.items():
                    param = ParameterItem(
                        id=template.id,
                        name=template.name,
                        description=template.description,
                        key=key,
                        value=value,
                        type=type(value).__name__ if value else "string",
                        level=level or "model_type",
                        supplier_id=supplier_id,
                        model_id=model_id,
                        is_active=template.is_active
                    )
                    parameters.append(param)
        
        return ParameterListResponse(
            parameters=parameters,
            total=len(parameters)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取参数列表失败: {str(e)}"
        )


@router.get("/{parameter_id}", response_model=ParameterItem)
async def get_parameter(
    parameter_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """
    获取单个参数详情
    
    Args:
        parameter_id: 参数ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        参数详情
    """
    try:
        template = db.query(ParameterTemplate).filter(
            ParameterTemplate.id == parameter_id,
            ParameterTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="参数不存在"
            )
        
        # 返回第一个参数作为示例
        first_key = list(template.parameters.keys())[0] if template.parameters else ""
        first_value = template.parameters.get(first_key) if template.parameters else None
        
        return ParameterItem(
            id=template.id,
            name=template.name,
            description=template.description,
            key=first_key,
            value=first_value,
            type=type(first_value).__name__ if first_value else "string",
            level="model_type",
            is_active=template.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取参数详情失败: {str(e)}"
        )
