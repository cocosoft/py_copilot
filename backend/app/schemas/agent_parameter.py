"""智能体参数数据校验模型"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentParameterBase(BaseModel):
    """智能体参数基础Schema"""
    parameter_name: str = Field(..., description="参数名称")
    parameter_value: Any = Field(..., description="参数值")
    parameter_type: str = Field(default="string", description="参数类型")
    description: Optional[str] = Field(default=None, description="参数描述")
    parameter_group: Optional[str] = Field(default=None, description="参数分组")


class AgentParameterCreate(AgentParameterBase):
    """智能体参数创建Schema"""
    pass


class AgentParameterUpdate(BaseModel):
    """智能体参数更新Schema"""
    parameter_value: Any = Field(..., description="参数值")
    parameter_type: Optional[str] = Field(default=None, description="参数类型")
    description: Optional[str] = Field(default=None, description="参数描述")
    parameter_group: Optional[str] = Field(default=None, description="参数分组")


class AgentParameterResponse(AgentParameterBase):
    """智能体参数响应Schema"""
    id: int
    agent_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class AgentParameterListResponse(BaseModel):
    """智能体参数列表响应Schema"""
    parameters: List[AgentParameterResponse]
    total: int


class AgentParametersBulkCreate(BaseModel):
    """批量创建智能体参数Schema"""
    parameters: Dict[str, Any] = Field(..., description="参数字典 {参数名: 参数值}")
    parameter_group: Optional[str] = Field(default=None, description="参数分组")


class AgentParameterEffectiveItem(BaseModel):
    """有效参数项Schema"""
    parameter_name: str
    parameter_value: Any
    parameter_type: Optional[str] = None
    source: str = "agent"
    is_effective: bool = True


class AgentParameterEffectiveResponse(BaseModel):
    """智能体有效参数响应Schema"""
    agent_id: int
    parameters: Dict[str, Any]
    inherited_from_model: bool = False
    model_id: Optional[int] = None


class AgentParametersWithSourceItem(BaseModel):
    """带来源信息的参数项Schema"""
    id: Optional[int] = None
    parameter_name: str
    parameter_value: Any
    parameter_type: Optional[str] = None
    description: Optional[str] = None
    source: str
    is_effective: bool = True


class AgentParametersWithSourceResponse(BaseModel):
    """带来源信息的参数列表响应Schema"""
    agent_id: int
    parameters: List[AgentParametersWithSourceItem]


class AgentParametersValidationResponse(BaseModel):
    """参数校验响应Schema"""
    valid: bool
    errors: List[str]
