"""FastAPI应用主入口"""
import signal
import sys
import asyncio
import threading
import psutil
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import requests
import time
from urllib.parse import urlparse

# 导入日志记录器
from app.core.logging_config import logger

# 导入错误处理相关模块
from app.core.exception_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    not_found_handler,
    unicode_decode_error_handler
)
from app.core.error_middleware import error_context_middleware
from app.core.exceptions import AppException
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

def signal_handler(signum, frame):
    """处理系统信号，实现优雅关闭"""
    logger.info(f"接收到信号 {signum}，正在优雅关闭服务器...")
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def monitor_memory():
    """内存监控函数"""
    process = psutil.Process()
    while True:
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        
        # 设置内存使用阈值（500MB）
        if memory_usage_mb > 500:
            logger.warning(f"内存使用过高: {memory_usage_mb:.2f}MB")
        
        # 每30秒检查一次
        threading.Event().wait(30)

# 启动内存监控线程（后台运行）
memory_monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
memory_monitor_thread.start()

# 使用硬编码配置避免复杂导入
API_TITLE = "Py Copilot API"
API_VERSION = "1.0.0"
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5175", "http://127.0.0.1:5175", "http://localhost:5176", "http://127.0.0.1:5176", "http://localhost:5177", "http://127.0.0.1:5177"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# 从dependencies模块导入数据库引擎
from app.api.dependencies import engine

# 修改FastAPI的默认编码器，为bytes类型添加安全的编码器
from fastapi.encoders import ENCODERS_BY_TYPE

# 保存原始的bytes编码器
original_bytes_encoder = ENCODERS_BY_TYPE.get(bytes)

# 添加更安全的bytes编码器
def safe_bytes_encoder(o):
    """安全的bytes编码器，避免UnicodeDecodeError"""
    try:
        return o.decode()
    except UnicodeDecodeError:
        # 如果无法解码为UTF-8，返回base64编码的字符串
        import base64
        return base64.b64encode(o).decode('ascii')

ENCODERS_BY_TYPE[bytes] = safe_bytes_encoder

# 创建FastAPI应用实例
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    docs_url="/docs",
    redirect_slashes=False,  # Disable automatic trailing slash redirects to avoid CORS issues
)

# 设置请求体大小限制为60MB，以支持50MB的文件上传
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if "content-length" in request.headers:
        content_length = int(request.headers["content-length"])
        max_size = 60 * 1024 * 1024  # 60MB
        if content_length > max_size:
            return JSONResponse(
                status_code=413,
                content={"detail": "请求体过大，文件大小不能超过50MB"},
            )
    response = await call_next(request)
    return response

# 添加静态文件服务，提供上传的图片访问
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UPLOAD_DIR = os.path.join(BASE_DIR, "frontend", "public", "logos", "agents")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/logos/agents", StaticFiles(directory=UPLOAD_DIR), name="agent_logos")

# 添加logo文件的静态文件服务
PROVIDERS_LOGOS_DIR = os.path.join(BASE_DIR, "frontend", "public", "logos", "providers")
os.makedirs(PROVIDERS_LOGOS_DIR, exist_ok=True)
app.mount("/logos/providers", StaticFiles(directory=PROVIDERS_LOGOS_DIR), name="logos")

# 添加分类logo文件的静态文件服务
CATEGORIES_LOGOS_DIR = os.path.join(BASE_DIR, "frontend", "public", "logos", "categories")
os.makedirs(CATEGORIES_LOGOS_DIR, exist_ok=True)
app.mount("/logos/categories", StaticFiles(directory=CATEGORIES_LOGOS_DIR), name="category_logos")

# 添加模型logo文件的静态文件服务
MODELS_LOGOS_DIR = os.path.join(BASE_DIR, "frontend", "public", "logos", "models")
os.makedirs(MODELS_LOGOS_DIR, exist_ok=True)
app.mount("/logos/models", StaticFiles(directory=MODELS_LOGOS_DIR), name="model_logos")

# 添加能力logo文件的静态文件服务
CAPABILITIES_LOGOS_DIR = os.path.join(BASE_DIR, "frontend", "public", "logos", "capabilities")
os.makedirs(CAPABILITIES_LOGOS_DIR, exist_ok=True)
app.mount("/logos/capabilities", StaticFiles(directory=CAPABILITIES_LOGOS_DIR), name="capability_logos")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

# 添加错误上下文中间件 - 使用正确的middleware装饰器方式
@app.middleware("http")
async def error_context_middleware_wrapper(request: Request, call_next):
    """错误上下文中间件包装器"""
    return await error_context_middleware(request, call_next)

# 注册异常处理器
app.exception_handler(AppException)(app_exception_handler)
app.exception_handler(HTTPException)(http_exception_handler)
app.exception_handler(RequestValidationError)(validation_exception_handler)
app.exception_handler(Exception)(general_exception_handler)
app.exception_handler(404)(not_found_handler)
app.exception_handler(UnicodeDecodeError)(unicode_decode_error_handler)

# 自定义请求验证异常处理器 - 覆盖默认处理器
# @app.exception_handler(RequestValidationError)
# async def custom_request_validation_exception_handler(request: Request, exc: RequestValidationError):
#     """
#     自定义请求验证异常处理器，避免在处理multipart/form-data时出现UnicodeDecodeError
#     """
#     # 直接构建响应，完全避免使用jsonable_encoder
#     return JSONResponse(
#         status_code=422,
#         content={"detail": "请求验证错误"},
#     )

# 导入监控系统
from app.core.performance_middleware import PerformanceMiddleware
from app.services.monitoring.monitoring_service import MonitoringService, SystemMetricsCollector

# 导入任务队列
from app.core.task_queue import start_task_queue, stop_task_queue

# 创建简化的监控服务实例（避免数据库依赖）
_monitoring_service = None
_system_metrics_collector = None

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("应用正在启动...")
    
    # 启动任务队列
    try:
        await start_task_queue()
        logger.info("任务队列已启动")
    except Exception as e:
        logger.error(f"启动任务队列失败: {e}")
    
    # 初始化模型监控服务
    try:
        from app.services.enhanced_model_service import initialize_model_monitoring
        await initialize_model_monitoring()
        logger.info("模型监控服务已初始化")
    except Exception as e:
        logger.error(f"初始化模型监控服务失败: {e}")
    
    # 启动系统指标收集器
    try:
        global _system_metrics_collector
        monitoring_service = get_monitoring_service()
        _system_metrics_collector = SystemMetricsCollector(monitoring_service)
        # 启动后台任务收集系统指标
        asyncio.create_task(_system_metrics_collector.collect_system_metrics())
        logger.info("系统指标收集器已启动")
    except Exception as e:
        logger.error(f"启动系统指标收集器失败: {e}")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("应用正在关闭...")
    
    # 停止任务队列
    try:
        await stop_task_queue()
        logger.info("任务队列已停止")
    except Exception as e:
        logger.error(f"停止任务队列失败: {e}")
    
    # 关闭模型监控服务
    try:
        from app.services.enhanced_model_service import shutdown_model_monitoring
        await shutdown_model_monitoring()
        logger.info("模型监控服务已关闭")
    except Exception as e:
        logger.error(f"关闭模型监控服务失败: {e}")

def get_monitoring_service():
    """获取监控服务实例（简化版，避免数据库依赖）"""
    global _monitoring_service
    if _monitoring_service is None:
        # 创建不依赖数据库的监控服务实例
        _monitoring_service = MonitoringService()
    
    return _monitoring_service

# 启用性能监控中间件
monitoring_service = get_monitoring_service()
app.add_middleware(PerformanceMiddleware, monitoring_service=monitoring_service)

# 请求日志中间件（增强版，包含性能监控）
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    记录所有HTTP请求的中间件
    
    Args:
        request: 请求对象
        call_next: 下一个中间件或路由处理函数
    
    Returns:
        响应对象
    """
    # 请求开始时间
    start_time = time.time()
    
    # 记录请求信息
    logger.info(
        f"请求开始 - 路径: {request.url.path}, 方法: {request.method}, "
        f"客户端: {request.client.host if request.client else '未知'}"
    )
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 计算响应时间
        process_time = time.time() - start_time
        
        # 记录响应信息
        logger.info(
            f"请求结束 - 路径: {request.url.path}, 方法: {request.method}, "
            f"状态码: {response.status_code}, 响应时间: {process_time:.4f}秒"
        )
        
        return response
    except UnicodeDecodeError as e:
        # 专门处理UnicodeDecodeError异常
        process_time = time.time() - start_time
        logger.error(
            f"请求错误 - 路径: {request.url.path}, 方法: {request.method}, "
            f"UnicodeDecodeError: {str(e)}, 响应时间: {process_time:.4f}秒"
        )
        return JSONResponse(
            status_code=400,
            content={"detail": "Bad request. There was an error processing your request."},
        )
    except Exception as e:
        # 计算响应时间
        process_time = time.time() - start_time
        
        # 记录错误信息
        logger.error(
            f"请求错误 - 路径: {request.url.path}, 方法: {request.method}, "
            f"错误: {str(e)}, 响应时间: {process_time:.4f}秒"
        )
        raise

# 根路径
@app.get("/")
def root():
    return {"message": "Py Copilot API is running"}

# 健康检查端点
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# 详细健康检查端点
@app.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查端点，提供系统状态信息"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "status": "healthy",
        "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
        "cpu_percent": round(process.cpu_percent(), 2),
        "thread_count": process.num_threads(),
        "create_time": process.create_time(),
        "database_connection": "正常",
        "timestamp": time.time()
    }



# 图片代理端点，用于处理外部URL的logo请求，避免ORB安全限制
@app.get("/proxy-image")
async def proxy_image(url: str = Query(..., description="要代理的外部图片URL")):
    """代理外部图片请求的端点"""
    # 验证URL是否为有效的图片URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or parsed_url.scheme not in ["http", "https"]:
        raise HTTPException(status_code=400, detail="无效的图片URL")
    
    try:
        # 获取外部图片
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # 获取内容类型
        content_type = response.headers.get("content-type", "image/jpeg")
        
        # 返回图片数据
        return Response(
            content=response.content,
            media_type=content_type
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"获取图片失败: {str(e)}")

# 监控服务API端点
@app.get("/api/monitoring/metrics/summary")
async def get_metrics_summary(metric_name: str = Query(..., description="指标名称"), duration: int = Query(3600, description="时间范围（秒）")):
    """获取指标摘要"""
    monitoring_service = get_monitoring_service()
    summary = monitoring_service.get_metrics_summary(metric_name, duration)
    return {
        "status": "success",
        "metric": metric_name,
        "duration": duration,
        "summary": summary
    }

@app.get("/api/monitoring/alerts")
async def get_active_alerts():
    """获取活跃告警"""
    monitoring_service = get_monitoring_service()
    alerts = monitoring_service.get_active_alerts()
    
    # 转换告警对象为字典
    alerts_dict = []
    for alert in alerts:
        alerts_dict.append({
            "id": alert.id,
            "rule_name": alert.rule_name,
            "level": alert.level.value,
            "type": alert.type.value,
            "message": alert.message,
            "metric_value": alert.metric_value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp.isoformat(),
            "resolved": alert.resolved,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
        })
    
    return {
        "status": "success",
        "alerts": alerts_dict,
        "count": len(alerts_dict)
    }

@app.get("/api/monitoring/system/info")
async def get_system_info():
    """获取系统信息"""
    process = psutil.Process()
    memory_info = process.memory_info()
    cpu_usage = process.cpu_percent()
    disk_usage = psutil.disk_usage('/')
    
    return {
        "status": "success",
        "system_info": {
            "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
            "cpu_percent": round(cpu_usage, 2),
            "thread_count": process.num_threads(),
            "disk_usage_percent": round(disk_usage.percent, 2),
            "disk_total_gb": round(disk_usage.total / 1024 / 1024 / 1024, 2),
            "disk_used_gb": round(disk_usage.used / 1024 / 1024 / 1024, 2),
            "disk_free_gb": round(disk_usage.free / 1024 / 1024 / 1024, 2),
            "create_time": process.create_time(),
            "uptime_seconds": time.time() - process.create_time()
        }
    }

@app.get("/api/monitoring/alerts/stats")
async def get_alert_statistics(duration: int = Query(3600, description="时间范围（秒）")):
    """获取告警统计"""
    monitoring_service = get_monitoring_service()
    stats = monitoring_service.get_alert_statistics(duration)
    return {
        "status": "success",
        "duration": duration,
        "statistics": stats
    }

# 导入路由 - 使用动态导入避免循环导入
from app.api import api_router
app.include_router(api_router, prefix="/api")

