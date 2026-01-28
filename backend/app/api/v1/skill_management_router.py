"""
技能管理API路由

集成技能发现机制，提供技能注册表查询、分类管理、搜索等功能
"""
from fastapi import APIRouter

from app.api.v1.skill_management import router as skill_management_router

router = APIRouter()

# 包含技能管理API路由
router.include_router(skill_management_router, prefix="/skill-management", tags=["skill-management"])