"""
错误中间件
全局错误捕获中间件、错误上下文收集
"""

from fastapi import Request
from fastapi.responses import JSONResponse
import time
import uuid

from app.core.logging_config import logger
from app.core.error import ErrorResponse, ErrorContext


async def error_context_middleware(request: Request, call_next):
    """
    错误上下文中间件
    为每个请求添加请求ID和错误上下文
    
    Args:
        request: 请求对象
        call_next: 下一个中间件或路由处理函数
    
    Returns:
        响应对象
    """
    # 生成请求ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # 添加请求ID到请求头
    request.scope["request_id"] = request_id
    
    # 记录请求开始
    start_time = time.time()
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id
        
        # 计算响应时间
        process_time = time.time() - start_time
        
        # 记录请求完成
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "status_code": response.status_code,
                "process_time": round(process_time, 4)
            }
        )
        
        return response
    except Exception as exc:
        # 计算响应时间
        process_time = time.time() - start_time
        
        # 记录错误信息
        logger.error(
            f"Request error: {str(exc)}",
            extra={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "process_time": round(process_time, 4),
                "error": str(exc)
            }
        )
        
        # 重新抛出异常，让异常处理器处理
        raise
