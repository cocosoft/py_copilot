"""API依赖函数模块"""
# 从核心模块导入依赖函数，避免重复定义
from app.core.dependencies import get_db, get_current_user, engine

# 此文件保留用于API特定的依赖函数（如果需要）
# 数据库和用户认证等通用依赖已移至app.core.dependencies