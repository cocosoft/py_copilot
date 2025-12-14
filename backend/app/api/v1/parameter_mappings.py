"""参数映射API接口"""
from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.models.parameter_normalization import ParameterNormalizationRule
from app.schemas.parameter_normalization import (
    ParameterNormalizationRuleCreate,
    ParameterNormalizationRuleUpdate,
    ParameterNormalizationRuleResponse,
    ParameterNormalizationRuleListResponse
)
from app.services.parameter_management.parameter_normalizer import ParameterNormalizer

# 创建模拟用户类用于测试
class MockUser:
    def __init__(self):
        self.id = 1
        self.is_active = True
        self.is_superuser = True

def get_mock_user():
    return MockUser()

router = APIRouter()
parameter_mappings_router = router


@router.get("/parameter-mappings", response_model=ParameterNormalizationRuleListResponse)
def get_parameter_mappings(
    skip: int = 0,
    limit: int = 100,
    supplier_id: Optional[int] = None,
    model_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取参数映射规则列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        supplier_id: 筛选特定供应商的规则
        model_type: 筛选特定模型类型的规则
        is_active: 筛选激活/未激活的规则
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        参数映射规则列表
    """
    query = db.query(ParameterNormalizationRule)
    
    # 应用筛选条件
    if supplier_id is not None:
        query = query.filter(ParameterNormalizationRule.supplier_id == supplier_id)
    if model_type:
        query = query.filter(ParameterNormalizationRule.model_type == model_type)
    if is_active is not None:
        query = query.filter(ParameterNormalizationRule.is_active == is_active)
    
    rules = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return ParameterNormalizationRuleListResponse(
        rules=rules,
        total=total
    )


@router.post("/parameter-mappings", response_model=ParameterNormalizationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_parameter_mapping(
    mapping_data: ParameterNormalizationRuleCreate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    创建参数映射规则
    
    Args:
        mapping_data: 映射规则创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的映射规则信息
    """
    try:
        db_mapping = ParameterNormalizationRule(**mapping_data.model_dump())
        db.add(db_mapping)
        db.commit()
        db.refresh(db_mapping)
        return db_mapping
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建参数映射规则失败，请检查输入数据"
        )


@router.get("/parameter-mappings/{mapping_id}", response_model=ParameterNormalizationRuleResponse)
def get_parameter_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取单个参数映射规则
    
    Args:
        mapping_id: 映射规则ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        参数映射规则信息
    """
    mapping = db.query(ParameterNormalizationRule).filter(ParameterNormalizationRule.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数映射规则不存在"
        )
    return mapping


@router.put("/parameter-mappings/{mapping_id}", response_model=ParameterNormalizationRuleResponse)
def update_parameter_mapping(
    mapping_id: int,
    mapping_data: ParameterNormalizationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新参数映射规则
    
    Args:
        mapping_id: 映射规则ID
        mapping_data: 映射规则更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的映射规则信息
    """
    mapping = db.query(ParameterNormalizationRule).filter(ParameterNormalizationRule.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数映射规则不存在"
        )
    
    # 更新映射规则字段
    update_data = mapping_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)
    
    try:
        db.commit()
        db.refresh(mapping)
        return mapping
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新参数映射规则失败，请检查输入数据"
        )


@router.delete("/parameter-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parameter_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> None:
    """
    删除参数映射规则
    
    Args:
        mapping_id: 映射规则ID
        db: 数据库会话
        current_user: 当前用户
    """
    mapping = db.query(ParameterNormalizationRule).filter(ParameterNormalizationRule.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数映射规则不存在"
        )
    
    db.delete(mapping)
    db.commit()


class ParameterConversionRequest(BaseModel):
    """参数转换请求Schema"""
    supplier_id: int
    model_type: Optional[str] = None
    parameters: Dict[str, Any]


class ParameterConversionResponse(BaseModel):
    """参数转换响应Schema"""
    success: bool
    normalized_parameters: Dict[str, Any]


@router.post("/parameter-conversion", response_model=ParameterConversionResponse)
def convert_parameters(
    request: ParameterConversionRequest,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    将供应商参数转换为标准参数
    
    Args:
        request: 参数转换请求数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        转换后的标准参数
    """
    try:
        normalized_params = ParameterNormalizer.normalize_parameters(
            supplier_id=request.supplier_id,
            raw_params=request.parameters,
            model_type=request.model_type
        )
        
        return ParameterConversionResponse(
            success=True,
            normalized_parameters=normalized_params
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"参数转换失败: {str(e)}"
        )
