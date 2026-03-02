"""
Function Calling工具基类

提供工具的基础抽象类和通用功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import time

from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolDefinition,
    ToolExecutionContext,
    ToolValidationResult,
    ToolValidationError
)

logger = logging.getLogger(__name__)


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
    async def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """
        执行工具
        
        Args:
            parameters: 工具参数字典
            
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
    
    def validate_parameters(self, **kwargs) -> ToolValidationResult:
        """
        验证工具参数
        
        Args:
            **kwargs: 待验证的参数
            
        Returns:
            验证结果
        """
        result = ToolValidationResult(is_valid=True)
        
        # 检查必需参数
        for param in self._parameters:
            if param.required and param.name not in kwargs:
                result.add_error(
                    field=param.name,
                    message=f"缺少必需参数: {param.name}"
                )
        
        # 检查参数类型
        for param_name, param_value in kwargs.items():
            param_def = next((p for p in self._parameters if p.name == param_name), None)
            if param_def:
                if not self._validate_parameter_type(param_def.type, param_value):
                    result.add_error(
                        field=param_name,
                        message=f"参数类型错误，期望: {param_def.type}，实际: {type(param_value).__name__}",
                        value=param_value
                    )
        
        return result
    
    def _validate_parameter_type(self, expected_type: str, value: Any) -> bool:
        """
        验证参数类型
        
        Args:
            expected_type: 期望的类型
            value: 待验证的值
            
        Returns:
            是否验证通过
        """
        type_mapping = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected = type_mapping.get(expected_type)
        if expected is None:
            return True
        
        return isinstance(value, expected)
    
    def get_tool_definition(self) -> ToolDefinition:
        """
        获取工具定义对象
        
        Returns:
            工具定义对象
        """
        properties = {}
        for param in self._parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
        
        return ToolDefinition(
            name=self._metadata.name,
            description=self._metadata.description,
            parameters={
                "type": "object",
                "properties": properties,
                "required": [p.name for p in self._parameters if p.required],
                "additionalProperties": False
            }
        )
    
    def get_openai_schema(self) -> Dict[str, Any]:
        """
        获取OpenAI格式的工具定义
        
        Returns:
            OpenAI格式的工具定义
        """
        return self.get_tool_definition().to_openai_format()
    
    async def execute_with_timing(self, **kwargs) -> ToolExecutionResult:
        """
        带计时的工具执行
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        start_time = time.time()
        try:
            result = await self.execute(**kwargs)
            result.execution_time = time.time() - start_time
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"工具执行异常: {self._metadata.name}, 错误: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=str(e),
                error_code="EXECUTION_ERROR",
                execution_time=execution_time
            )


class ServiceTool(BaseTool):
    """
    基于服务的工具基类
    
    用于包装现有服务为工具
    """
    
    def __init__(self):
        """初始化服务工具"""
        self._service = None
        super().__init__()
    
    @abstractmethod
    def _get_service(self):
        """
        获取服务实例
        
        Returns:
            服务实例
        """
        pass
    
    def get_service(self):
        """
        获取或创建服务实例（懒加载）
        
        Returns:
            服务实例
        """
        if self._service is None:
            self._service = self._get_service()
        return self._service
