"""参数归一化规则相关API接口"""
from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import get_db
from app.models.parameter_normalization import ParameterNormalizationRule
from app.schemas.parameter_normalization import (
    ParameterNormalizationRuleCreate,
    ParameterNormalizationRuleUpdate,
    ParameterNormalizationRuleResponse,
    ParameterNormalizationRuleListResponse
)

# 创建模拟用户类用于测试
class MockUser:
    def __init__(self):
        self.id = 1
        self.is_active = True
        self.is_superuser = True

def get_mock_user():
    return MockUser()

router = APIRouter()
parameter_normalization_rules_router = router


@router.post("/parameter-normalization-rules", response_model=ParameterNormalizationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_parameter_normalization_rule(
    rule_data: ParameterNormalizationRuleCreate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    创建参数归一化规则
    
    Args:
        rule_data: 规则创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的规则信息
    """
    # 创建新规则
    try:
        db_rule = ParameterNormalizationRule(**rule_data.model_dump())
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建参数归一化规则失败，请检查输入数据"
        )


@router.get("/parameter-normalization-rules", response_model=ParameterNormalizationRuleListResponse)
def get_parameter_normalization_rules(
    skip: int = 0,
    limit: int = 100,
    supplier_id: Optional[int] = None,
    model_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取参数归一化规则列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        supplier_id: 筛选特定供应商的规则
        model_type: 筛选特定模型类型的规则
        is_active: 筛选激活/未激活的规则
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        参数归一化规则列表
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


@router.get("/parameter-normalization-rules/{rule_id}", response_model=ParameterNormalizationRuleResponse)
def get_parameter_normalization_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取单个参数归一化规则
    
    Args:
        rule_id: 规则ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        参数归一化规则信息
    """
    rule = db.query(ParameterNormalizationRule).filter(ParameterNormalizationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数归一化规则不存在"
        )
    return rule


@router.put("/parameter-normalization-rules/{rule_id}", response_model=ParameterNormalizationRuleResponse)
def update_parameter_normalization_rule(
    rule_id: int,
    rule_data: ParameterNormalizationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新参数归一化规则
    
    Args:
        rule_id: 规则ID
        rule_data: 规则更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的规则信息
    """
    rule = db.query(ParameterNormalizationRule).filter(ParameterNormalizationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数归一化规则不存在"
        )
    
    # 更新规则字段
    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    try:
        db.commit()
        db.refresh(rule)
        return rule
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新参数归一化规则失败，请检查输入数据"
        )


@router.delete("/parameter-normalization-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parameter_normalization_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> None:
    """
    删除参数归一化规则
    
    Args:
        rule_id: 规则ID
        db: 数据库会话
        current_user: 当前用户
    """
    rule = db.query(ParameterNormalizationRule).filter(ParameterNormalizationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数归一化规则不存在"
        )
    
    db.delete(rule)
    db.commit()


@router.post("/parameter-normalization-rules/batch", response_model=List[ParameterNormalizationRuleResponse], status_code=status.HTTP_201_CREATED)
def batch_create_parameter_normalization_rules(
    rules_data: List[ParameterNormalizationRuleCreate],
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    批量创建参数归一化规则
    
    Args:
        rules_data: 规则创建数据列表
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的规则信息列表
    """
    created_rules = []
    
    try:
        for rule_data in rules_data:
            db_rule = ParameterNormalizationRule(**rule_data.model_dump())
            db.add(db_rule)
            created_rules.append(db_rule)
        
        db.commit()
        for rule in created_rules:
            db.refresh(rule)
            
        return created_rules
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="批量创建参数归一化规则失败，请检查输入数据"
        )


@router.post("/suppliers/{supplier_id}/parameter-normalization-rules/export")
def export_supplier_parameter_rules(
    supplier_id: int,
    model_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    导出供应商的参数归一化规则
    
    Args:
        supplier_id: 供应商ID
        model_type: 模型类型（可选）
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        导出的规则JSON数据
    """
    query = db.query(ParameterNormalizationRule).filter(
        ParameterNormalizationRule.supplier_id == supplier_id,
        ParameterNormalizationRule.is_active == True
    )
    
    if model_type:
        query = query.filter(ParameterNormalizationRule.model_type == model_type)
    
    rules = query.all()
    
    # 转换为字典格式
    rules_dict = {
        "supplier_id": supplier_id,
        "model_type": model_type,
        "rules": [
            {
                "param_name": rule.param_name,
                "standard_name": rule.standard_name,
                "param_type": rule.param_type,
                "mapped_from": rule.mapped_from,
                "default_value": rule.default_value,
                "range_min": rule.range_min,
                "range_max": rule.range_max,
                "regex_pattern": rule.regex_pattern,
                "enum_values": rule.enum_values,
                "is_active": rule.is_active,
                "description": rule.description
            }
            for rule in rules
        ]
    }
    
    return {
        "success": True,
        "data": rules_dict
    }