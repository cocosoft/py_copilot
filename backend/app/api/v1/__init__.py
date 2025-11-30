"""API v1 版本路由初始化"""
from fastapi import APIRouter

# 只导入必要的API路由模块，避免langchain相关的错误
from app.api.v1 import model_management, supplier_model, capability, category

api_router = APIRouter()

# 只注册必要的API路由
api_router.include_router(model_management.router, prefix="/model-management", tags=["model-management"])
api_router.include_router(capability.router, tags=["capability"])
api_router.include_router(category.router, tags=["category"])
api_router.include_router(supplier_model.router, prefix="/model-management", tags=["supplier-model"])