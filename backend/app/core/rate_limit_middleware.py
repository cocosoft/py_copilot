"""API频率限制中间件"""
import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.core.logging_config import logger


class RateLimiter:
    """API频率限制器"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.banned_ips: Dict[str, float] = {}
        self.cleanup_interval = 300  # 5分钟清理一次
        self.last_cleanup = time.time()
    
    def _cleanup_old_requests(self):
        """清理过期的请求记录"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        self.last_cleanup = current_time
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                req_time for req_time in self.requests[ip]
                if current_time - req_time < 3600  # 保留1小时内的记录
            ]
            if not self.requests[ip]:
                del self.requests[ip]
        
        for ip in list(self.banned_ips.keys()):
            if current_time - self.banned_ips[ip] > 3600:
                del self.banned_ips[ip]
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_rate_limit_key(self, request: Request) -> Tuple[str, str]:
        """获取频率限制的键"""
        ip = self._get_client_ip(request)
        path = request.url.path
        
        if path.startswith("/api/v1/"):
            return (ip, path)
        
        return (ip, "default")
    
    def is_rate_limited(
        self,
        request: Request,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否达到频率限制
        
        Args:
            request: 请求对象
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        
        Returns:
            (是否限制, 限制信息字典)
        """
        self._cleanup_old_requests()
        
        ip = self._get_client_ip(request)
        
        if ip in self.banned_ips:
            remaining_time = int(3600 - (time.time() - self.banned_ips[ip]))
            return True, {
                "error": "IP已被封禁",
                "retry_after": remaining_time
            }
        
        key = self._get_rate_limit_key(request)
        current_time = time.time()
        
        request_times = self.requests[key[0]]
        
        window_start = current_time - window_seconds
        recent_requests = [t for t in request_times if t > window_start]
        
        if len(recent_requests) >= max_requests:
            return True, {
                "error": "请求过于频繁",
                "retry_after": window_seconds,
                "limit": max_requests,
                "window": window_seconds
            }
        
        self.requests[key[0]].append(current_time)
        return False, None
    
    def ban_ip(self, request: Request, duration: int = 3600):
        """
        封禁IP地址
        
        Args:
            request: 请求对象
            duration: 封禁时长（秒）
        """
        ip = self._get_client_ip(request)
        self.banned_ips[ip] = time.time() + duration
        logger.warning(f"IP {ip} 已被封禁 {duration} 秒")
    
    def get_request_count(self, request: Request, window_seconds: int = 60) -> int:
        """
        获取指定时间窗口内的请求次数
        
        Args:
            request: 请求对象
            window_seconds: 时间窗口（秒）
        
        Returns:
            请求次数
        """
        ip = self._get_client_ip(request)
        current_time = time.time()
        window_start = current_time - window_seconds
        
        request_times = self.requests.get(ip, [])
        recent_requests = [t for t in request_times if t > window_start]
        
        return len(recent_requests)


class RateLimitMiddleware:
    """频率限制中间件"""
    
    def __init__(self, rate_limiter: RateLimiter = None):
        self.rate_limiter = rate_limiter or RateLimiter()
        
        self.rate_limits = {
            "default": {"max_requests": 100, "window_seconds": 60},
            "/api/v1/auth/login": {"max_requests": 5, "window_seconds": 60},
            "/api/v1/auth/register": {"max_requests": 3, "window_seconds": 60},
            "/api/v1/conversations": {"max_requests": 50, "window_seconds": 60},
            "/api/v1/agents": {"max_requests": 30, "window_seconds": 60},
            "/api/v1/models": {"max_requests": 60, "window_seconds": 60},
            "/api/v1/skills": {"max_requests": 40, "window_seconds": 60},
        }
    
    async def __call__(self, request: Request, call_next):
        """
        中间件处理函数
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数
        
        Returns:
            响应对象
        """
        path = request.url.path
        
        if not path.startswith("/api/"):
            return await call_next(request)
        
        rate_limit_config = self._get_rate_limit_config(path)
        
        is_limited, limit_info = self.rate_limiter.is_rate_limited(
            request,
            max_requests=rate_limit_config["max_requests"],
            window_seconds=rate_limit_config["window_seconds"]
        )
        
        if is_limited:
            logger.warning(
                f"频率限制触发 - IP: {self.rate_limiter._get_client_ip(request)}, "
                f"路径: {path}, 原因: {limit_info.get('error', '未知')}"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": {
                        "message": limit_info.get("error", "请求过于频繁"),
                        "status_code": 429,
                        "retry_after": limit_info.get("retry_after", 60),
                        "limit": rate_limit_config["max_requests"],
                        "window": rate_limit_config["window_seconds"]
                    }
                }
            )
        
        response = await call_next(request)
        
        request_count = self.rate_limiter.get_request_count(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit_config["max_requests"])
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, rate_limit_config["max_requests"] - request_count)
        )
        response.headers["X-RateLimit-Window"] = str(rate_limit_config["window_seconds"])
        
        return response
    
    def _get_rate_limit_config(self, path: str) -> Dict:
        """获取指定路径的频率限制配置"""
        for route, config in self.rate_limits.items():
            if path.startswith(route):
                return config
        return self.rate_limits["default"]


def get_rate_limiter() -> RateLimiter:
    """获取频率限制器实例"""
    return RateLimiter()


def get_rate_limit_middleware() -> RateLimitMiddleware:
    """获取频率限制中间件实例"""
    return RateLimitMiddleware()
