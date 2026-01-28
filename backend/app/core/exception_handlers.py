"""
异常处理器
统一的异常处理函数，转换异常为标准错误响应
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional
import traceback

from app.core.error import (
    ErrorResponse, 
    ErrorContext, 
    get_error_code_from_status, 
    get_error_message
)
from app.core.logging_config import logger
from app.core.exceptions import AppException


def create_error_context(request: Request, **kwargs) -> ErrorContext:
    """
    创建错误上下文
    
    Args:
        request: 请求对象
        **kwargs: 额外的上下文信息
    
    Returns:
        错误上下文
    """
    return ErrorContext(
        request_id=request.headers.get("X-Request-ID"),
        path=str(request.url.path),
        method=request.method,
        client_ip=request.client.host if request.client else None,
        additional=kwargs
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    处理应用异常
    
    Args:
        request: 请求对象
        exc: 应用异常
    
    Returns:
        JSON响应
    """
    # 确保错误上下文包含请求信息
    if not exc.context:
        exc.context = create_error_context(request)
    
    # 记录错误日志
    logger.error(
        f"AppException: {exc.code} - {exc.message}",
        extra={
            "error_code": exc.code,
            "error_message": exc.message,
            "error_details": exc.details,
            "error_field": exc.field,
            "context": exc.context.to_dict() if exc.context else {},
            "traceback": traceback.format_exc()
        }
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.error_response.to_dict()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    处理HTTP异常
    
    Args:
        request: 请求对象
        exc: HTTP异常
    
    Returns:
        JSON响应
    """
    # 从状态码获取错误码
    error_code = get_error_code_from_status(exc.status_code)
    
    # 构建错误响应
    error_context = create_error_context(request)
    
    # 处理异常详情
    details = exc.detail
    error_message = get_error_message(error_code)
    error_details = None
    error_field = None
    
    # 处理验证错误详情
    if isinstance(details, dict) and "detail" in details:
        error_details = details["detail"]
    elif isinstance(details, str):
        error_message = details
    
    error_response = ErrorResponse(
        code=error_code,
        message=error_message,
        details=error_details,
        field=error_field,
        context=error_context
    )
    
    # 记录错误日志
    logger.error(
        f"HTTPException: {error_code} - {error_message}",
        extra={
            "error_code": error_code,
            "error_message": error_message,
            "error_details": error_details,
            "context": error_context.to_dict(),
            "status_code": exc.status_code,
            "traceback": traceback.format_exc()
        }
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": error_response.to_dict()
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求验证异常
    
    Args:
        request: 请求对象
        exc: 请求验证异常
    
    Returns:
        JSON响应
    """
    # 构建错误详情
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    # 构建错误响应
    error_context = create_error_context(request)
    error_response = ErrorResponse(
        code="VALIDATION_001",
        message="数据验证失败",
        details=str(error_details),
        context=error_context
    )
    
    # 记录错误日志
    logger.error(
        "RequestValidationError: 数据验证失败",
        extra={
            "error_code": "VALIDATION_001",
            "error_details": error_details,
            "context": error_context.to_dict(),
            "traceback": traceback.format_exc()
        }
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": error_response.to_dict()
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理通用异常
    
    Args:
        request: 请求对象
        exc: 异常
    
    Returns:
        JSON响应
    """
    # 构建错误响应
    error_context = create_error_context(request)
    error_response = ErrorResponse(
        code="SYSTEM_001",
        message="系统错误，请联系管理员",
        details=str(exc),
        context=error_context
    )
    
    # 记录错误日志
    logger.error(
        f"GeneralException: {str(exc)}",
        extra={
            "error_code": "SYSTEM_001",
            "error_message": "系统错误",
            "error_details": str(exc),
            "context": error_context.to_dict(),
            "traceback": traceback.format_exc()
        }
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": error_response.to_dict()
        }
    )


async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理404错误
    
    Args:
        request: 请求对象
        exc: 异常
    
    Returns:
        JSON响应
    """
    # 构建错误响应
    error_context = create_error_context(request)
    error_response = ErrorResponse(
        code="RESOURCE_001",
        message="请求的资源不存在",
        context=error_context
    )
    
    # 记录错误日志
    logger.warning(
        f"NotFound: {request.url.path}",
        extra={
            "error_code": "RESOURCE_001",
            "context": error_context.to_dict()
        }
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": error_response.to_dict()
        }
    )


async def unicode_decode_error_handler(request: Request, exc: UnicodeDecodeError) -> JSONResponse:
    """
    处理UnicodeDecodeError异常
    
    Args:
        request: 请求对象
        exc: UnicodeDecodeError异常
    
    Returns:
        JSON响应
    """
    # 构建错误响应
    error_context = create_error_context(request)
    error_response = ErrorResponse(
        code="VALIDATION_001",
        message="请求数据格式错误",
        details=str(exc),
        context=error_context
    )
    
    # 记录错误日志
    logger.error(
        f"UnicodeDecodeError: {str(exc)}",
        extra={
            "error_code": "VALIDATION_001",
            "error_details": str(exc),
            "context": error_context.to_dict(),
            "traceback": traceback.format_exc()
        }
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": error_response.to_dict()
        }
    )
