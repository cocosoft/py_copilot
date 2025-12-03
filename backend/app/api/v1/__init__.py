"""API v1 版本路由初始化"""
from fastapi import APIRouter

# 从模块化的API中导入路由
from app.modules.auth.api.auth import router as auth_router
from app.modules.conversation.api.conversations import router as conversation_router
from app.modules.llm.api.llm import router as llm_router
from app.modules.supplier_model_management.api.model_management import router as model_management_router
from app.modules.supplier_model_management.api.supplier_model import router as supplier_model_router
from app.api.v1.model_capabilities import router as model_capabilities_router
from app.api.v1.capability import router as capability_router
from app.modules.capability_category.api.category import router as category_router
from app.modules.capability_category.api.model_categories import router as model_categories_router

api_router = APIRouter()

# 注册所有模块的API路由
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(conversation_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(llm_router, prefix="/llm", tags=["llm"])
api_router.include_router(model_management_router, prefix="/model-management", tags=["model-management"])
api_router.include_router(supplier_model_router, prefix="/model-management", tags=["supplier-model"])
api_router.include_router(model_capabilities_router, tags=["model_capabilities"])
api_router.include_router(capability_router, tags=["capability"])
api_router.include_router(category_router, tags=["category"])
api_router.include_router(model_categories_router, tags=["model-categories"])