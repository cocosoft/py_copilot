"""系统参数管理API接口"""
from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.models.parameter_template import ParameterTemplate
from app.schemas.parameter_template import (
    ParameterTemplateResponse,
    ParameterTemplateCreate,
    ParameterTemplateUpdate
)
from app.services.parameter_management.system_parameter_manager import SystemParameterManager

# 创建模拟用户类用于测试
class MockUser:
    def __init__(self):
        self.id = 1
        self.is_active = True
        self.is_superuser = True

def get_mock_user():
    return MockUser()

router = APIRouter()
system_parameters_router = router


class SystemParameterListResponse(BaseModel):
    """系统参数列表响应Schema"""
    parameters: List[Dict[str, Any]]


class SystemParameterUpdateRequest(BaseModel):
    """系统参数更新请求Schema"""
    value: Any
    type: Optional[str] = "string"
    description: Optional[str] = ""


class BatchSystemParameterUpdateRequest(BaseModel):
    """批量系统参数更新请求Schema"""
    parameters: Dict[str, Dict[str, Any]]


@router.get("/system-parameters", response_model=SystemParameterListResponse)
def get_system_parameters(
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取当前激活的系统参数配置
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        系统参数配置列表
    """
    try:
        parameters = SystemParameterManager.get_system_parameters(db)
        return SystemParameterListResponse(parameters=parameters)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统参数失败: {str(e)}"
        )


@router.get("/system-parameters/templates", response_model=List[ParameterTemplateResponse])
def get_system_parameter_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取系统参数模板列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        系统参数模板列表
    """
    try:
        templates = SystemParameterManager.get_system_parameter_templates(db, skip=skip, limit=limit)
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统参数模板失败: {str(e)}"
        )


@router.get("/system-parameters/templates/active", response_model=ParameterTemplateResponse)
def get_active_system_parameter_template(
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取当前激活的系统参数模板
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        当前激活的系统参数模板
    """
    template = SystemParameterManager.get_active_system_parameter_template(db)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到激活的系统参数模板"
        )
    return template


@router.post("/system-parameters/templates", response_model=ParameterTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_system_parameter_template(
    template_data: ParameterTemplateCreate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    创建系统参数模板
    
    Args:
        template_data: 系统参数模板创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的系统参数模板
    """
    try:
        # 确保模板级别为system
        template_data.level = "system"
        template = SystemParameterManager.create_system_parameter_template(db, template_data)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建系统参数模板失败: {str(e)}"
        )


@router.put("/system-parameters/templates/{template_id}", response_model=ParameterTemplateResponse)
def update_system_parameter_template(
    template_id: int,
    template_data: ParameterTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新系统参数模板
    
    Args:
        template_id: 系统参数模板ID
        template_data: 系统参数模板更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的系统参数模板
    """
    try:
        template = SystemParameterManager.update_system_parameter_template(db, template_id, template_data)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新系统参数模板失败: {str(e)}"
        )


@router.put("/system-parameters/templates/{template_id}/activate", response_model=ParameterTemplateResponse)
def activate_system_parameter_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    激活系统参数模板
    
    Args:
        template_id: 系统参数模板ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        激活的系统参数模板
    """
    try:
        template = SystemParameterManager.activate_system_parameter_template(db, template_id)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"激活系统参数模板失败: {str(e)}"
        )


@router.put("/system-parameters/{param_name}")
def update_system_parameter(
    param_name: str,
    param_data: SystemParameterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新单个系统参数
    
    Args:
        param_name: 参数名称
        param_data: 参数更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的系统参数信息
    """
    try:
        template = SystemParameterManager.update_system_parameter(
            db=db,
            param_name=param_name,
            param_value=param_data.value,
            param_type=param_data.type,
            description=param_data.description
        )
        
        # 从更新后的模板中找到更新的参数
        updated_param = None
        for param in template.parameters:
            if param["name"] == param_name:
                updated_param = param
                break
        
        return {
            "success": True,
            "parameter": updated_param,
            "message": "系统参数更新成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新系统参数失败: {str(e)}"
        )


@router.delete("/system-parameters/{param_name}")
def delete_system_parameter(
    param_name: str,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    删除单个系统参数
    
    Args:
        param_name: 参数名称
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        删除结果
    """
    try:
        template = SystemParameterManager.delete_system_parameter(db, param_name)
        return {
            "success": True,
            "message": "系统参数删除成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除系统参数失败: {str(e)}"
        )


@router.put("/system-parameters", response_model=ParameterTemplateResponse)
def batch_update_system_parameters(
    batch_request: BatchSystemParameterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    批量更新系统参数
    
    Args:
        batch_request: 批量更新请求数据，包含多个参数的更新信息
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的系统参数模板
    """
    try:
        template = SystemParameterManager.batch_update_system_parameters(
            db=db,
            parameters=batch_request.parameters
        )
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新系统参数失败: {str(e)}"
        )
