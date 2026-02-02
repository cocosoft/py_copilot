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
from app.core.enhanced_error_handler import (
    get_error_handler,
    ErrorCategory,
    ErrorSeverity,
    EnhancedError
)


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
    
    # 使用增强错误处理器
    error_handler = get_error_handler(logger)
    
    # 创建增强错误
    enhanced_error = EnhancedError(
        code=exc.code,
        message=exc.message,
        category=ErrorCategory.SERVICE,
        severity=ErrorSeverity.MEDIUM,
        details=exc.details,
        field=exc.field,
        context=exc.context.to_dict() if exc.context else {}
    )
    
    # 处理错误
    error_response = error_handler.handle_error(
        enhanced_error,
        request_id=request.headers.get("X-Request-ID"),
        user_id=exc.context.user_id if exc.context else None,
        path=request.url.path,
        method=request.method
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
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
    # 使用增强错误处理器
    error_handler = get_error_handler(logger)
    
    # 从状态码获取错误码
    error_code = get_error_code_from_status(exc.status_code)
    
    # 构建错误上下文
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
    
    # 根据状态码确定错误分类和严重程度
    category_mapping = {
        400: ErrorCategory.VALIDATION,
        401: ErrorCategory.AUTHENTICATION,
        403: ErrorCategory.AUTHORIZATION,
        404: ErrorCategory.RESOURCE,
        409: ErrorCategory.RESOURCE,
        422: ErrorCategory.VALIDATION,
        429: ErrorCategory.NETWORK,
        500: ErrorCategory.SERVICE,
        502: ErrorCategory.EXTERNAL,
        503: ErrorCategory.SERVICE,
        504: ErrorCategory.NETWORK
    }
    
    severity_mapping = {
        400: ErrorSeverity.LOW,
        401: ErrorSeverity.MEDIUM,
        403: ErrorSeverity.MEDIUM,
        404: ErrorSeverity.LOW,
        409: ErrorSeverity.MEDIUM,
        422: ErrorSeverity.LOW,
        429: ErrorSeverity.MEDIUM,
        500: ErrorSeverity.HIGH,
        502: ErrorSeverity.HIGH,
        503: ErrorSeverity.HIGH,
        504: ErrorSeverity.HIGH
    }
    
    category = category_mapping.get(exc.status_code, ErrorCategory.SERVICE)
    severity = severity_mapping.get(exc.status_code, ErrorSeverity.MEDIUM)
    
    # 创建增强错误
    enhanced_error = EnhancedError(
        code=error_code,
        message=error_message,
        category=category,
        severity=severity,
        details=error_details,
        field=error_field,
        context=error_context.to_dict() if error_context else {}
    )
    
    # 处理错误
    error_response = error_handler.handle_error(
        enhanced_error,
        request_id=request.headers.get("X-Request-ID"),
        path=request.url.path,
        method=request.method
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
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
    # 使用增强错误处理器
    error_handler = get_error_handler(logger)
    
    # 构建错误详情
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    # 构建错误上下文
    error_context = create_error_context(request)
    
    # 创建增强错误
    enhanced_error = EnhancedError(
        code="VALIDATION_001",
        message="数据验证失败",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        details=str(error_details),
        context=error_context.to_dict() if error_context else {}
    )
    
    # 处理错误
    error_response = error_handler.handle_error(
        enhanced_error,
        request_id=request.headers.get("X-Request-ID"),
        path=request.url.path,
        method=request.method
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=422,
        content=error_response
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
    # 使用增强错误处理器
    error_handler = get_error_handler(logger)
    
    # 构建错误上下文
    error_context = create_error_context(request)
    
    # 使用增强错误处理器自动转换错误
    error_response = error_handler.handle_error(
        exc,
        request_id=request.headers.get("X-Request-ID"),
        path=request.url.path,
        method=request.method
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=500,
        content=error_response
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
    # 使用增强错误处理器
    error_handler = get_error_handler(logger)
    
    # 构建错误上下文
    error_context = create_error_context(request)
    
    # 创建增强错误
    enhanced_error = EnhancedError(
        code="RESOURCE_001",
        message="请求的资源不存在",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.LOW,
        context=error_context.to_dict() if error_context else {}
    )
    
    # 处理错误
    error_response = error_handler.handle_error(
        enhanced_error,
        request_id=request.headers.get("X-Request-ID"),
        path=request.url.path,
        method=request.method
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=404,
        content=error_response
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
    # 使用增强错误处理器
    error_handler = get_error_handler(logger)
    
    # 构建错误上下文
    error_context = create_error_context(request)
    
    # 创建增强错误
    enhanced_error = EnhancedError(
        code="VALIDATION_001",
        message="请求数据格式错误",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        details=str(exc),
        context=error_context.to_dict() if error_context else {}
    )
    
    # 处理错误
    error_response = error_handler.handle_error(
        enhanced_error,
        request_id=request.headers.get("X-Request-ID"),
        path=request.url.path,
        method=request.method
    )
    
    # 返回标准错误响应
    return JSONResponse(
        status_code=400,
        content=error_response
    )
