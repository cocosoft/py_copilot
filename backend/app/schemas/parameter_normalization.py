"""参数归一化规则相关Schema"""
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ParameterNormalizationRuleBase(BaseModel):
    """参数归一化规则基础Schema"""
    supplier_id: Optional[int] = None
    model_type: Optional[str] = None
    param_name: str = Field(..., min_length=1, max_length=100, description="供应商参数名")
    standard_name: str = Field(..., min_length=1, max_length=100, description="标准参数名")
    param_type: str = Field(..., pattern="^(int|float|string|bool|array|object|enum)$", description="参数类型")
    mapped_from: Optional[str] = Field(None, max_length=100, description="映射来源参数名")
    default_value: Optional[Any] = None
    range_min: Optional[int] = None
    range_max: Optional[int] = None
    regex_pattern: Optional[str] = Field(None, max_length=200, description="正则表达式")
    enum_values: Optional[List[Any]] = None
    is_active: bool = True
    description: Optional[str] = Field(None, max_length=500, description="规则描述")
    
    @field_validator('range_max')
    @classmethod
    def validate_range(cls, v, values):
        """验证范围值的合理性"""
        if v is not None and values.data.get('range_min') is not None:
            if v < values.data['range_min']:
                raise ValueError('最大值必须大于或等于最小值')
        return v


class ParameterNormalizationRuleCreate(ParameterNormalizationRuleBase):
    """参数归一化规则创建Schema"""
    pass


class ParameterNormalizationRuleUpdate(BaseModel):
    """参数归一化规则更新Schema"""
    supplier_id: Optional[int] = None
    model_type: Optional[str] = None
    param_name: Optional[str] = Field(None, min_length=1, max_length=100)
    standard_name: Optional[str] = Field(None, min_length=1, max_length=100)
    param_type: Optional[str] = Field(None, pattern="^(int|float|string|bool|array|object|enum)$")
    mapped_from: Optional[str] = Field(None, max_length=100)
    default_value: Optional[Any] = None
    range_min: Optional[int] = None
    range_max: Optional[int] = None
    regex_pattern: Optional[str] = Field(None, max_length=200)
    enum_values: Optional[List[Any]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('range_max')
    @classmethod
    def validate_range(cls, v, values):
        """验证范围值的合理性"""
        if v is not None and values.data.get('range_min') is not None:
            if v < values.data['range_min']:
                raise ValueError('最大值必须大于或等于最小值')
        return v


class ParameterNormalizationRuleResponse(ParameterNormalizationRuleBase):
    """参数归一化规则响应Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ParameterNormalizationRuleListResponse(BaseModel):
    """参数归一化规则列表响应Schema"""
    rules: List[ParameterNormalizationRuleResponse]
    total: int