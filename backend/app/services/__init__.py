"""服务层模块"""
from app.services.model_category_service import model_category_service
from app.services.model_capability_service import model_capability_service

__all__ = [
    "model_category_service",
    "model_capability_service",
]