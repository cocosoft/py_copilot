"""
统一API响应工具函数
"""

from fastapi import HTTPException
from typing import Optional, TypeVar, Generic

from app.schemas.response import (
    SuccessResponse, SuccessData, SuccessMessage,
    ErrorResponse, NotFoundError, BadRequestError, 
    UnauthorizedError, ForbiddenError, ServerError,
    ListResponse
)

# 泛型类型变量
T = TypeVar('T')


def success_response(
    data: Optional[T] = None,
    message: str = "成功",
    code: int = 200
) -> SuccessResponse[T]:
    """生成成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 响应状态码
        
    Returns:
        SuccessResponse: 成功响应对象
    """
    return SuccessResponse(code=code, message=message, data=data)


def success_with_data(
    data: T,
    message: str = "成功",
    code: int = 200
) -> SuccessData[T]:
    """生成包含数据的成功响应
    
    Args:
        data: 响应数据（必须提供）
        message: 响应消息
        code: 响应状态码
        
    Returns:
        SuccessData: 包含数据的成功响应对象
    """
    return SuccessData(code=code, message=message, data=data)


def success_with_message(
    message: str,
    code: int = 200
) -> SuccessMessage:
    """生成仅包含消息的成功响应
    
    Args:
        message: 响应消息
        code: 响应状态码
        
    Returns:
        SuccessMessage: 仅包含消息的成功响应对象
    """
    return SuccessMessage(code=code, message=message)


def list_response(
    data: list[T],
    total: int,
    page: Optional[int] = None,
    size: Optional[int] = None,
    message: str = "成功",
    code: int = 200
) -> ListResponse[T]:
    """生成列表响应
    
    Args:
        data: 响应数据列表
        total: 总记录数
        page: 当前页码
        size: 每页大小
        message: 响应消息
        code: 响应状态码
        
    Returns:
        ListResponse: 列表响应对象
    """
    return ListResponse(
        code=code,
        message=message,
        data=data,
        total=total,
        page=page,
        size=size
    )


def error_response(
    detail: Optional[str] = None,
    message: str = "请求失败",
    code: int = 400
) -> ErrorResponse:
    """生成错误响应
    
    Args:
        detail: 错误详情
        message: 错误消息
        code: 错误状态码
        
    Returns:
        ErrorResponse: 错误响应对象
    """
    return ErrorResponse(code=code, message=message, detail=detail)


def not_found_error(
    detail: Optional[str] = None,
    message: str = "资源不存在"
) -> NotFoundError:
    """生成资源不存在错误响应
    
    Args:
        detail: 错误详情
        message: 错误消息
        
    Returns:
        NotFoundError: 资源不存在错误响应对象
    """
    return NotFoundError(message=message, detail=detail)


def bad_request_error(
    detail: Optional[str] = None,
    message: str = "请求参数错误"
) -> BadRequestError:
    """生成请求参数错误响应
    
    Args:
        detail: 错误详情
        message: 错误消息
        
    Returns:
        BadRequestError: 请求参数错误响应对象
    """
    return BadRequestError(message=message, detail=detail)


def unauthorized_error(
    detail: Optional[str] = None,
    message: str = "未授权访问"
) -> UnauthorizedError:
    """生成未授权错误响应
    
    Args:
        detail: 错误详情
        message: 错误消息
        
    Returns:
        UnauthorizedError: 未授权错误响应对象
    """
    return UnauthorizedError(message=message, detail=detail)


def forbidden_error(
    detail: Optional[str] = None,
    message: str = "禁止访问"
) -> ForbiddenError:
    """生成禁止访问错误响应
    
    Args:
        detail: 错误详情
        message: 错误消息
        
    Returns:
        ForbiddenError: 禁止访问错误响应对象
    """
    return ForbiddenError(message=message, detail=detail)


def server_error(
    detail: Optional[str] = None,
    message: str = "服务器内部错误"
) -> ServerError:
    """生成服务器内部错误响应
    
    Args:
        detail: 错误详情
        message: 错误消息
        
    Returns:
        ServerError: 服务器内部错误响应对象
    """
    return ServerError(message=message, detail=detail)


def raise_http_exception(
    status_code: int,
    detail: Optional[str] = None,
    message: str = "请求失败"
) -> None:
    """抛出HTTP异常
    
    Args:
        status_code: HTTP状态码
        detail: 错误详情
        message: 错误消息
        
    Raises:
        HTTPException: FastAPI HTTP异常
    """
    if detail is None:
        detail = message
    
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": status_code,
            "message": message,
            "detail": detail
        }
    )
