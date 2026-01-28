"""
错误模型
定义统一的错误模型、错误码和错误消息
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


# 错误码映射
ERROR_CODES = {
    # 认证错误
    "AUTH_001": "认证失败，请重新登录",
    "AUTH_002": "令牌过期，请重新登录",
    "AUTH_003": "无效的认证令牌",
    
    # 授权错误
    "PERMISSION_001": "权限不足，无法访问该资源",
    
    # 验证错误
    "VALIDATION_001": "数据验证失败",
    "VALIDATION_002": "必填字段不能为空",
    "VALIDATION_003": "字段格式错误",
    
    # 数据库错误
    "DATABASE_001": "数据库操作失败",
    "DATABASE_002": "数据重复",
    
    # 网络错误
    "NETWORK_001": "网络连接失败",
    "NETWORK_002": "请求超时",
    
    # 服务错误
    "SERVICE_001": "内部服务错误",
    "SERVICE_002": "服务暂时不可用",
    
    # 资源错误
    "RESOURCE_001": "请求的资源不存在",
    "RESOURCE_002": "资源冲突",
    "RESOURCE_003": "资源已被删除",
    
    # 配置错误
    "CONFIG_001": "配置参数错误",
    "CONFIG_002": "缺少必要的配置",
    
    # 外部API错误
    "EXTERNAL_001": "外部服务调用失败",
    "EXTERNAL_002": "外部服务返回错误",
    
    # 系统错误
    "SYSTEM_001": "系统错误，请联系管理员",
    "SYSTEM_002": "系统维护中"
}


# HTTP状态码映射到错误码
HTTP_STATUS_TO_ERROR_CODE = {
    400: "VALIDATION_001",
    401: "AUTH_001",
    403: "PERMISSION_001",
    404: "RESOURCE_001",
    409: "RESOURCE_002",
    422: "VALIDATION_001",
    429: "NETWORK_002",
    500: "SERVICE_001",
    502: "EXTERNAL_001",
    503: "SERVICE_002",
    504: "NETWORK_002"
}


@dataclass
class ErrorContext:
    """错误上下文"""
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    user_id: Optional[int] = None
    client_ip: Optional[str] = None
    additional: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.additional is None:
            self.additional = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "path": self.path,
            "method": self.method,
            "user_id": self.user_id,
            "client_ip": self.client_ip,
            **self.additional
        }


@dataclass
class ErrorResponse:
    """错误响应模型"""
    code: str
    message: str
    details: Optional[str] = None
    field: Optional[str] = None
    context: Optional[ErrorContext] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "field": self.field,
            "context": {
                "request_id": self.context.request_id,
                "timestamp": self.context.timestamp,
                "path": self.context.path,
                "method": self.context.method,
                "user_id": self.context.user_id,
                "client_ip": self.context.client_ip,
                **self.context.additional
            } if self.context else None
        }


@dataclass
class ApiResponse:
    """API响应模型"""
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorResponse] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        response = {"success": self.success}
        if self.data is not None:
            response["data"] = self.data
        if self.error is not None:
            response["error"] = self.error.to_dict()
        return response


def get_error_message(error_code: str) -> str:
    """
    获取错误消息
    
    Args:
        error_code: 错误码
    
    Returns:
        错误消息
    """
    return ERROR_CODES.get(error_code, "未知错误")


def get_error_code_from_status(status_code: int) -> str:
    """
    从HTTP状态码获取错误码
    
    Args:
        status_code: HTTP状态码
    
    Returns:
        错误码
    """
    return HTTP_STATUS_TO_ERROR_CODE.get(status_code, "SYSTEM_001")
