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
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5174", "http://127.0.0.1:5174"]
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
)

# 添加静态文件服务，提供上传的图片访问
UPLOAD_DIR = "E:/PY/CODES/py copilot IV/frontend/public/logos/agents"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/logos/agents", StaticFiles(directory=UPLOAD_DIR), name="agent_logos")

# 添加logo文件的静态文件服务
LOGOS_DIR = "../../frontend/public/logos/providers"
os.makedirs(LOGOS_DIR, exist_ok=True)
app.mount("/logos/providers", StaticFiles(directory=LOGOS_DIR), name="logos")

# 添加分类logo文件的静态文件服务
CATEGORIES_LOGOS_DIR = "../../frontend/public/logos/categories"
os.makedirs(CATEGORIES_LOGOS_DIR, exist_ok=True)
app.mount("/logos/categories", StaticFiles(directory=CATEGORIES_LOGOS_DIR), name="category_logos")

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

# 请求日志中间件
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
app.include_router(api_router)

# 创建数据库表 - 已通过init_db.py初始化，此处注释避免重复创建
# from app.core.database import Base
# 在创建表之前导入所有模型类，确保它们被注册
# from app.models.supplier_db import SupplierDB, ModelDB
# from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
# from app.modules.capability_category.models.category_db import ModelCategoryDB
# from app.models.parameter_template import ParameterTemplate
# from app.models.supplier_db import ModelParameter
# User模型暂时不导入，避免重复定义
# Base.metadata.create_all(bind=engine)