"""监控服务应用"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from typing import Dict, Any

from app.core.microservices_config import microservices_settings
from app.core.performance_middleware import PerformanceMiddleware
from app.services.monitoring.monitoring_service import MonitoringService
from app.api.microservices.monitoring import router as monitoring_router

# 创建监控服务应用
monitoring_app = FastAPI(
    title="Py Copilot 监控服务",
    version="1.0.0",
    description="微服务架构的监控服务",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
monitoring_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建监控服务实例（简化版，避免数据库依赖）
_monitoring_service = None

def get_monitoring_service():
    """获取监控服务实例"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service

# 启用性能监控中间件
monitoring_service = get_monitoring_service()
monitoring_app.add_middleware(PerformanceMiddleware, monitoring_service=monitoring_service)

# 注册监控路由
monitoring_app.include_router(monitoring_router, prefix="/api/monitoring", tags=["monitoring"])

@monitoring_app.get("/")
async def root():
    """监控服务根路径"""
    return {
        "service": "monitoring",
        "version": "1.0.0",
        "status": "running",
        "timestamp": asyncio.get_event_loop().time()
    }

@monitoring_app.get("/health")
async def health_check():
    """监控服务健康检查"""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": asyncio.get_event_loop().time()
    }

@monitoring_app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    import time
    
    start_time = time.time()
    
    # 记录请求开始
    print(f"监控服务请求开始: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # 计算响应时间
        process_time = time.time() - start_time
        
        # 记录请求完成
        print(f"监控服务请求完成: {request.method} {request.url.path} - "
              f"状态: {response.status_code} - 耗时: {process_time:.4f}秒")
        
        return response
        
    except Exception as e:
        # 记录错误
        process_time = time.time() - start_time
        print(f"监控服务请求错误: {request.method} {request.url.path} - "
              f"错误: {str(e)} - 耗时: {process_time:.4f}秒")
        raise

# 监控服务启动函数
def start_monitoring_service():
    """启动监控服务"""
    print("启动监控服务...")
    
    config = uvicorn.Config(
        app="app.api.microservices.monitoring_service:monitoring_app",
        host=microservices_settings.MONITORING_SERVICE_HOST,
        port=microservices_settings.MONITORING_SERVICE_PORT,
        workers=microservices_settings.MONITORING_SERVICE_WORKERS,
        log_level="info",
        reload=False
    )
    
    server = uvicorn.Server(config)
    
    try:
        server.run()
    except Exception as e:
        print(f"监控服务启动失败: {e}")

if __name__ == "__main__":
    start_monitoring_service()