"""FastAPI应用主入口"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# 使用硬编码配置避免复杂导入
API_TITLE = "Py Copilot API"
API_VERSION = "1.0.0"
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# 从dependencies模块导入数据库引擎
from app.api.dependencies import engine

# 创建FastAPI应用实例
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    docs_url="/docs",
)

# 添加静态文件服务，提供上传的图片访问
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 添加logo文件的静态文件服务
LOGOS_DIR = "../../frontend/public/logos/providers"
os.makedirs(LOGOS_DIR, exist_ok=True)
app.mount("/logos/providers", StaticFiles(directory=LOGOS_DIR), name="logos")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

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

# 导入路由 - 使用动态导入避免循环导入
from app.api import api_router
app.include_router(api_router)

# 创建数据库表
from app.models.base import Base
# 在创建表之前导入所有模型类，确保它们被注册
from app.models.supplier_db import SupplierDB, ModelDB
from app.models.capability_db import CapabilityDB
from app.models.category_db import ModelCategoryDB
Base.metadata.create_all(bind=engine)