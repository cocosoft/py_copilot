"""API路由初始化"""
from fastapi import APIRouter

from app.api.v1 import api_router as api_router_v1

api_router = APIRouter()

# 包含v1版本的API路由
api_router.include_router(api_router_v1, prefix="/api")