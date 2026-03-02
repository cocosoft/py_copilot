"""
工具Schemas定义

提供工具相关的数据模型和Schema定义
"""

from typing import Dict, Any, List, Optional, Callable, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
import json


class ToolParameterType(str, Enum):
    """工具参数类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolCategory(str, Enum):
    """工具分类枚举"""
    SEARCH = "search"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    FILE = "file"
    TEXT = "text"
    DATA = "data"
    CALCULATION = "calculation"
    IMAGE = "image"
    CODE = "code"
    API = "api"
    UTILITY = "utility"


class ToolParameter(BaseModel):
    """
    工具参数定义
    
    定义工具所需的参数结构
    """
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型：string, integer, number, boolean, array, object")
    description: str = Field(..., description="参数描述")
    required: bool = Field(True, description="是否必需")
    default: Optional[Any] = Field(None, description="默认值")
    enum: Optional[List[Any]] = Field(None, description="枚举值列表")
    
    @validator('type')
    def validate_type(cls, v):
        """验证参数类型"""
        valid_types = ['string', 'integer', 'number', 'boolean', 'array', 'object']
        if v not in valid_types:
            raise ValueError(f"无效的参数类型: {v}，必须是: {', '.join(valid_types)}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "type": self.type,
            "description": self.description
        }
        if self.enum:
            result["enum"] = self.enum
        if self.default is not None:
            result["default"] = self.default
        return result


class ToolMetadata(BaseModel):
    """
    工具元数据
    
    存储工具的基本信息和配置
    """
    name: str = Field(..., description="工具名称，全局唯一")
    display_name: str = Field(..., description="工具显示名称")
    description: str = Field(..., description="工具描述，用于大模型理解工具用途")
    category: str = Field(..., description="工具分类")
    version: str = Field("1.0.0", description="工具版本")
    author: Optional[str] = Field(None, description="工具作者")
    icon: str = Field("🔧", description="工具图标")
    tags: List[str] = Field(default_factory=list, description="工具标签")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ToolExecutionResult(BaseModel):
    """
    工具执行结果
    
    统一封装工具执行后的返回结果
    """
    success: bool = Field(..., description="执行是否成功")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误码")
    execution_time: float = Field(..., description="执行时间（秒）")
    tool_name: str = Field(..., description="工具名称")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")
    
    @validator('execution_time')
    def validate_execution_time(cls, v):
        """验证执行时间非负"""
        if v < 0:
            raise ValueError("执行时间不能为负数")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "error_code": self.error_code,
            "execution_time": self.execution_time,
            "tool_name": self.tool_name,
            "metadata": self.metadata
        }
    
    @classmethod
    def success_result(
        cls,
        tool_name: str,
        result: Any,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ToolExecutionResult":
        """
        创建成功的执行结果
        
        Args:
            tool_name: 工具名称
            result: 执行结果
            execution_time: 执行时间
            metadata: 附加元数据
            
        Returns:
            成功的执行结果实例
        """
        return cls(
            success=True,
            result=result,
            execution_time=execution_time,
            tool_name=tool_name,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_result(
        cls,
        tool_name: str,
        error: str,
        error_code: Optional[str] = None,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ToolExecutionResult":
        """
        创建失败的执行结果
        
        Args:
            tool_name: 工具名称
            error: 错误信息
            error_code: 错误码
            execution_time: 执行时间
            metadata: 附加元数据
            
        Returns:
            失败的执行结果实例
        """
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            execution_time=execution_time,
            tool_name=tool_name,
            metadata=metadata or {}
        )


class ToolDefinition(BaseModel):
    """
    工具定义
    
    用于Function Calling的工具定义格式
    """
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: Dict[str, Any] = Field(..., description="参数定义")
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI Function Calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def to_anthropic_format(self) -> Dict[str, Any]:
        """转换为Anthropic Claude格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }


class ToolExecutionContext(BaseModel):
    """
    工具执行上下文
    
    存储工具执行时的上下文信息
    """
    execution_id: str = Field(..., description="执行ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    request_metadata: Dict[str, Any] = Field(default_factory=dict, description="请求元数据")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ToolExecutionRecord(BaseModel):
    """
    工具执行记录
    
    用于记录工具执行历史
    """
    id: str = Field(..., description="记录ID")
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(..., description="执行参数")
    result: ToolExecutionResult = Field(..., description="执行结果")
    context: ToolExecutionContext = Field(..., description="执行上下文")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ToolValidationError(BaseModel):
    """工具参数验证错误"""
    field: str = Field(..., description="错误字段")
    message: str = Field(..., description="错误信息")
    value: Optional[Any] = Field(None, description="错误的值")


class ToolValidationResult(BaseModel):
    """工具参数验证结果"""
    is_valid: bool = Field(..., description="是否验证通过")
    errors: List[ToolValidationError] = Field(default_factory=list, description="错误列表")
    
    def add_error(self, field: str, message: str, value: Any = None):
        """添加验证错误"""
        self.errors.append(ToolValidationError(field=field, message=message, value=value))
        self.is_valid = False


class ServiceToolAdapterConfig(BaseModel):
    """
    服务工具适配器配置
    
    配置如何将服务方法适配为工具
    """
    service_method: str = Field(..., description="服务方法名称")
    parameter_mapping: Dict[str, str] = Field(default_factory=dict, description="参数映射")
    result_formatter: Optional[Callable] = Field(None, description="结果格式化函数")
    error_handler: Optional[Callable] = Field(None, description="错误处理函数")
