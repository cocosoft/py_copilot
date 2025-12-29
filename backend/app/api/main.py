"""FastAPI应用主入口"""
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

# 使用硬编码配置避免复杂导入
API_TITLE = "Py Copilot API"
API_VERSION = "1.0.0"
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5175", "http://127.0.0.1:5175", "http://localhost:5176", "http://127.0.0.1:5176"]
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

# 自定义异常处理器 - 处理UnicodeDecodeError
@app.exception_handler(UnicodeDecodeError)
async def unicode_decode_error_handler(request: Request, exc: UnicodeDecodeError):
    """
    处理UnicodeDecodeError异常，特别是在解析multipart/form-data请求时
    """
    logger.error(f"UnicodeDecodeError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Bad request. There was an error processing your request."},
    )

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
from app.core.performance_middleware import PerformanceMiddleware, get_performance_monitor
from app.services.monitoring.monitoring_service import MonitoringService
from app.services.monitoring.alert_notifier import NotificationManager
from app.api.deps import get_db

# 创建全局监控服务实例
_monitoring_service = None
_performance_monitor = None

# 注释掉监控服务的初始化，避免在服务器启动时立即访问数据库
# def get_monitoring_service():
#     """获取监控服务实例"""
#     global _monitoring_service
#     if _monitoring_service is None:
#         # 使用数据库依赖获取数据库会话
#         db = next(get_db())
#         _monitoring_service = MonitoringService(db)
#         
#         # 添加告警通知处理器
#         notification_manager = NotificationManager()
#         _monitoring_service.add_alert_handler(notification_manager.send_alert_notification)
#     
#     return _monitoring_service

# 注释掉性能监控中间件，避免启动时的数据库依赖
# monitoring_service = get_monitoring_service()
# performance_monitor = get_performance_monitor(monitoring_service)
# app.add_middleware(PerformanceMiddleware, monitoring_service=monitoring_service)

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

# 404异常处理
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found"},
    )

# 500异常处理
@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

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

# 导入路由 - 使用动态导入避免循环导入
from app.api import api_router
app.include_router(api_router, prefix="/api")

