"""性能监控中间件"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from typing import Dict, Any

from app.core.logging_config import performance_logger
from app.services.monitoring.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app: ASGIApp, monitoring_service: MonitoringService):
        super().__init__(app)
        self.monitoring_service = monitoring_service
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """处理请求并记录性能指标"""
        # 开始计时
        start_time = time.time()
        timer_id = performance_logger.start_timer("http_request")
        
        # 记录请求开始
        self._log_request_start(request)
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 记录响应时间
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 记录性能指标
            self._record_performance_metrics(request, response, response_time)
            
            # 记录请求完成
            self._log_request_complete(request, response, response_time)
            
            return response
            
        except Exception as e:
            # 记录错误
            response_time = (time.time() - start_time) * 1000
            self._log_request_error(request, e, response_time)
            raise
        
        finally:
            # 停止计时器
            performance_logger.stop_timer(timer_id, {
                "endpoint": str(request.url.path),
                "method": request.method,
                "status_code": getattr(response, 'status_code', 500) if 'response' in locals() else 500
            })
    
    def _log_request_start(self, request: Request):
        """记录请求开始"""
        logger.debug(f"请求开始: {request.method} {request.url.path}")
    
    def _log_request_complete(self, request: Request, response: Response, response_time: float):
        """记录请求完成"""
        log_level = logging.INFO
        if response_time > 5000:  # 超过5秒
            log_level = logging.WARNING
        elif response_time > 10000:  # 超过10秒
            log_level = logging.ERROR
        
        logger.log(
            log_level,
            f"请求完成: {request.method} {request.url.path} - "
            f"状态: {response.status_code} - "
            f"耗时: {response_time:.2f}ms"
        )
    
    def _log_request_error(self, request: Request, error: Exception, response_time: float):
        """记录请求错误"""
        logger.error(
            f"请求错误: {request.method} {request.url.path} - "
            f"错误: {str(error)} - "
            f"耗时: {response_time:.2f}ms"
        )
    
    def _record_performance_metrics(self, request: Request, response: Response, response_time: float):
        """记录性能指标"""
        try:
            # 记录响应时间指标
            self.monitoring_service.record_metric(
                "response_time",
                response_time,
                {
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "status_code": str(response.status_code)
                }
            )
            
            # 记录请求计数
            self.monitoring_service.record_metric(
                "request_count",
                1,
                {
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "status_code": str(response.status_code)
                }
            )
            
            # 如果是错误响应，记录错误率
            if response.status_code >= 400:
                self.monitoring_service.record_metric(
                    "error_count",
                    1,
                    {
                        "endpoint": str(request.url.path),
                        "method": request.method,
                        "status_code": str(response.status_code)
                    }
                )
            
        except Exception as e:
            logger.warning(f"记录性能指标失败: {str(e)}")

class ErrorRateCalculator:
    """错误率计算器"""
    
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
    
    async def calculate_error_rates(self):
        """计算错误率"""
        while True:
            try:
                # 获取最近5分钟的请求计数和错误计数
                request_summary = self.monitoring_service.get_metrics_summary("request_count", 300)
                error_summary = self.monitoring_service.get_metrics_summary("error_count", 300)
                
                if request_summary["count"] > 0:
                    error_rate = (error_summary["count"] / request_summary["count"]) * 100
                    
                    # 记录错误率指标
                    self.monitoring_service.record_metric("error_rate", error_rate)
                    
                    # 记录错误率日志
                    if error_rate > 10:  # 错误率超过10%
                        logger.warning(f"高错误率警告: {error_rate:.1f}%")
                    
                # 计算响应时间P95
                response_time_summary = self.monitoring_service.get_metrics_summary("response_time", 300)
                if response_time_summary["count"] > 0:
                    self.monitoring_service.record_metric("response_time_p95", response_time_summary["p95"])
                
            except Exception as e:
                logger.error(f"计算错误率失败: {str(e)}")
            
            # 每30秒计算一次
            import asyncio
            await asyncio.sleep(30)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
        self.error_rate_calculator = ErrorRateCalculator(monitoring_service)
    
    async def start_monitoring(self):
        """开始性能监控"""
        # 启动错误率计算任务
        import asyncio
        asyncio.create_task(self.error_rate_calculator.calculate_error_rates())
        
        logger.info("性能监控已启动")
    
    def get_performance_summary(self, duration: int = 300) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            response_time_summary = self.monitoring_service.get_metrics_summary("response_time", duration)
            request_summary = self.monitoring_service.get_metrics_summary("request_count", duration)
            error_summary = self.monitoring_service.get_metrics_summary("error_count", duration)
            error_rate_summary = self.monitoring_service.get_metrics_summary("error_rate", duration)
            
            return {
                "response_time": response_time_summary,
                "request_count": request_summary,
                "error_count": error_summary,
                "error_rate": error_rate_summary,
                "duration_seconds": duration
            }
        except Exception as e:
            logger.error(f"获取性能摘要失败: {str(e)}")
            return {}

# 创建全局性能监控器
_performance_monitor = None

def get_performance_monitor(monitoring_service: MonitoringService) -> PerformanceMonitor:
    """获取性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(monitoring_service)
    return _performance_monitor