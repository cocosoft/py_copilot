"""Function Calling工具基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class ToolParameter(BaseModel):
    """工具参数定义"""
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


class ToolMetadata(BaseModel):
    """工具元数据"""
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


class ToolExecutionResult(BaseModel):
    """工具执行结果"""
    success: bool = Field(..., description="执行是否成功")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误码")
    execution_time: float = Field(..., description="执行时间（秒）")
    tool_name: str = Field(..., description="工具名称")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")


class BaseTool(ABC):
    """工具基类，所有工具必须继承此类"""
    
    def __init__(self):
        """初始化工具"""
        self._metadata = self._get_metadata()
        self._parameters = self._get_parameters()
        self._validate_definition()
    
    @abstractmethod
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            工具元数据
        """
        pass
    
    @abstractmethod
    def _get_parameters(self) -> List[ToolParameter]:
        """
        获取工具参数定义
        
        Returns:
            参数定义列表
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        pass
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        获取工具定义（用于Function Calling）
        
        Returns:
            工具定义字典，符合OpenAI Function Calling格式
        """
        return {
            "type": "function",
            "function": {
                "name": self._metadata.name,
                "description": self._metadata.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        param.name: {
                            "type": param.type,
                            "description": param.description
                        }
                        for param in self._parameters
                    },
                    "required": [
                        param.name for param in self._parameters if param.required
                    ],
                    "additionalProperties": False
                }
            }
        }
    
    def get_metadata(self) -> ToolMetadata:
        """获取工具元数据"""
        return self._metadata
    
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return self._parameters
    
    def _validate_definition(self):
        """验证工具定义"""
        if not self._metadata.name or not isinstance(self._metadata.name, str):
            raise ValueError(f"工具名称必须是非空字符串: {self._metadata.name}")
        
        if not self._metadata.description or not isinstance(self._metadata.description, str):
            raise ValueError(f"工具描述必须是非空字符串: {self._metadata.description}")
        
        param_names = [param.name for param in self._parameters]
        if len(param_names) != len(set(param_names)):
            raise ValueError(f"工具参数名称不能重复: {self._metadata.name}")
        
        logger.info(f"工具定义验证通过: {self._metadata.name}")
