"""API v1 版本路由初始化"""
from fastapi import APIRouter

# 只导入我们刚刚创建的模块，避免触发langsmith兼容性问题
# 其他模块暂时注释掉
# from app.api.v1 import auth, conversations, model_management, model_categories, model_capabilities
from app.api.v1 import supplier_model, capability, category

api_router = APIRouter()

# 暂时注释所有可能触发langsmith的路由
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
# api_router.include_router(model_management.router, prefix="/model-management", tags=["model-management"])
# api_router.include_router(model_categories.router, prefix="/model", tags=["model_categories"])
# api_router.include_router(model_capabilities.router, prefix="/model", tags=["model_capabilities"])

# 只注册我们刚刚创建的路由
api_router.include_router(capability.router, tags=["capability"])
api_router.include_router(category.router, tags=["category"])
api_router.include_router(supplier_model.router, prefix="/model-management", tags=["supplier-model"])