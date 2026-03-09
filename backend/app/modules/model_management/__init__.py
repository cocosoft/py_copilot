"""
模型管理模块

提供模型管理的完整功能，包括：
- 模型的增删改查
- 模型参数管理
- 模型分类管理
- 默认模型设置

模块结构：
- api/: API路由定义
- services/: 业务逻辑层
- schemas/: 数据校验模型
- utils/: 工具函数
"""

from app.services.model_management_service import (
    ModelManagementService,
    get_model_management_service
)

__all__ = [
    "ModelManagementService",
    "get_model_management_service",
]
