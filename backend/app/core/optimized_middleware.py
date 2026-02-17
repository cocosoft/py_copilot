"""中间件优化配置"""
from fastapi import Request, Response
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from typing import Callable, Awaitable
from app.core.logging_config import logger


class RequestIDMiddleware:
    """请求ID中间件，为每个请求生成唯一标识"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class OptimizedLoggingMiddleware:
    """优化的日志中间件，减少日志开销"""
    
    def __init__(self, skip_paths: list = None, slow_threshold: float = 1.0):
        self.skip_paths = skip_paths or ["/health", "/health/detailed", "/favicon.ico"]
        self.slow_threshold = slow_threshold
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # 跳过健康检查等路径的日志
        if any(skip_path in path for skip_path in self.skip_paths):
            return await call_next(request)
        
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 只记录慢请求或错误请求
            if process_time > self.slow_threshold or response.status_code >= 400:
                logger.info(
                    f"[{request_id}] {request.method} {path} - "
                    f"状态码: {response.status_code}, 响应时间: {process_time:.4f}秒"
                )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {path} - "
                f"错误: {str(e)}, 响应时间: {process_time:.4f}秒"
            )
            raise


class CompressionMiddleware:
    """响应压缩中间件"""
    
    def __init__(self, minimum_size: int = 1024):
        self.minimum_size = minimum_size
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 只对文本响应进行压缩
        content_type = response.headers.get("content-type", "")
        if "text" in content_type or "json" in content_type or "xml" in content_type:
            response.headers["Content-Encoding"] = "gzip"
        
        return response


def get_optimized_middleware(cors_origins: list) -> list:
    """
    获取优化的中间件列表
    
    Args:
        cors_origins: CORS允许的源列表
        
    Returns:
        中间件列表
    """
    return [
        Middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(RequestIDMiddleware),
        Middleware(OptimizedLoggingMiddleware),
        Middleware(CompressionMiddleware),
    ]
