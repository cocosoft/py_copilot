"""
异常类
自定义异常类和异常处理工具
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any
from app.core.error import ErrorResponse, ErrorContext, get_error_message


class AppException(HTTPException):
    """应用异常基类"""
    
    def __init__(
        self,
        code: str,
        status_code: int = 400,
        message: Optional[str] = None,
        details: Optional[str] = None,
        field: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        """
        初始化异常
        
        Args:
            code: 错误码
            status_code: HTTP状态码
            message: 错误消息
            details: 详细错误信息
            field: 错误字段
            context: 错误上下文
        """
        self.code = code
        self.message = message or get_error_message(code)
        self.details = details
        self.field = field
        self.context = context
        
        # 构建错误响应
        self.error_response = ErrorResponse(
            code=code,
            message=self.message,
            details=details,
            field=field,
            context=context
        )
        
        # 调用父类构造函数
        super().__init__(
            status_code=status_code,
            detail=self.error_response.to_dict()
        )


class AuthException(AppException):
    """认证异常"""
    
    def __init__(
        self,
        code: str = "AUTH_001",
        message: Optional[str] = None,
        details: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        """
        初始化认证异常
        
        Args:
            code: 错误码
            message: 错误消息
            details: 详细错误信息
            context: 错误上下文
        """
        super().__init__(
            code=code,
            status_code=401,
            message=message,
            details=details,
            context=context
        )


class PermissionException(AppException):
    """授权异常"""
    
    def __init__(
        self,
        code: str = "PERMISSION_001",
        message: Optional[str] = None,
        details: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        """
        初始化授权异常
        
        Args:
            code: 错误码
            message: 错误消息
            details: 详细错误信息
            context: 错误上下文
        """
        super().__init__(
            code=code,
            status_code=403,
            message=message,
            details=details,
            context=context
        )


class ValidationException(AppException):
    """验证异常"""
    
    def __init__(
        self,
        code: str = "VALIDATION_001",
        message: Optional[str] = None,
        details: Optional[str] = None,
        field: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        """
        初始化验证异常
        
        Args:
            code: 错误码
            message: 错误消息
            details: 详细错误信息
            field: 错误字段
            context: 错误上下文
        """
        super().__init__(
            code=code,
            status_code=422,
            message=message,
            details=details,
            field=field,
            context=context
        )


class ResourceException(AppException):
    """资源异常"""
    
    def __init__(
        self,
        code: str = "RESOURCE_001",
        status_code: int = 404,
        message: Optional[str] = None,
        details: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        """
        初始化资源异常
        
        Args:
            code: 错误码
            status_code: HTTP状态码
            message: 错误消息
            details: 详细错误信息
            context: 错误上下文
        """
        super().__init__(
            code=code,
            status_code=status_code,
            message=message,
            details=details,
            context=context
        )


class DatabaseException(AppException):
    """数据库异常"""
    
    def __init__(
        self,
        code: str = "DATABASE_001",
        message: Optional[str] = None,
        details: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        """
        初始化数据库异常
        
        Args:
            code: 错误码
            message: 错误消息
            details: 详细错误信息
            context: 错误上下文
        """
        super().__init__(
            code=code,
            status_code=500,
            message=message,
            details=details,
            context=context
        )


class ServiceException(AppException):
    """服务异常"""
    
    def __init__(
        self,
        code: str = "SERVICE_001",
        status_code: int = 500,
        message: Optional[str] = None,
        details: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        """
        初始化服务异常
        
        Args:
            code: 错误码
            status_code: HTTP状态码
            message: 错误消息
            details: 详细错误信息
            context: 错误上下文
        """
        super().__init__(
            code=code,
            status_code=status_code,
            message=message,
            details=details,
            context=context
        )


class ExternalApiException(AppException):
    """外部API异常"""
    
    def __init__(
        self,
        code: str = "EXTERNAL_001",
        status_code: int = 502,
        message: Optional[str] = None,
        details: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        """
        初始化外部API异常
        
        Args:
            code: 错误码
            status_code: HTTP状态码
            message: 错误消息
            details: 详细错误信息
            context: 错误上下文
        """
        super().__init__(
            code=code,
            status_code=status_code,
            message=message,
            details=details,
            context=context
        )


# 保留现有的工作流异常类
class WorkflowException(Exception):
    """工作流异常基类"""
    pass


class TransientError(WorkflowException):
    """临时性错误，可以重试"""
    pass


class PermanentError(WorkflowException):
    """永久性错误，不应重试"""
    pass


class NodeExecutionError(WorkflowException):
    """节点执行错误"""
    def __init__(self, node_id: str, message: str, is_transient: bool = True):
        self.node_id = node_id
        self.message = message
        self.is_transient = is_transient
        super().__init__(f"节点 {node_id} 执行错误: {message}")


class WorkflowValidationError(WorkflowException):
    """工作流验证错误"""
    def __init__(self, message: str):
        super().__init__(f"工作流验证错误: {message}")


class WorkflowExecutionError(WorkflowException):
    """工作流执行错误"""
    def __init__(self, workflow_id: str, message: str):
        self.workflow_id = workflow_id
        super().__init__(f"工作流 {workflow_id} 执行错误: {message}")

