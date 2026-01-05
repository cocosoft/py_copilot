"""搜索管理API接口（仅联网搜索配置）"""
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.search_management_service import SearchManagementService
from app.schemas.search_settings import (
    SearchSettingResponse,
    SearchSettingUpdate
)

router = APIRouter(prefix="/search", tags=["search"])

# 初始化服务
search_management_service = SearchManagementService()


@router.get("/settings", response_model=SearchSettingResponse)
async def get_search_settings(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取搜索设置
    
    Args:
        user_id: 用户ID（可选），如果提供则获取用户级设置，否则获取全局设置
        db: 数据库会话
    
    Returns:
        搜索设置信息
    """
    settings = search_management_service.get_search_settings(db, user_id)
    if not settings:
        # 如果没有设置，创建默认的全局设置
        settings = search_management_service.update_search_settings(db, {}, user_id)
    return settings


@router.put("/settings", response_model=SearchSettingResponse)
async def update_search_settings(
    settings_update: SearchSettingUpdate,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    更新搜索设置
    
    Args:
        settings_update: 要更新的搜索设置数据
        user_id: 用户ID（可选），如果提供则更新用户级设置，否则更新全局设置
        db: 数据库会话
    
    Returns:
        更新后的搜索设置信息
    """
    return search_management_service.update_search_settings(db, settings_update.model_dump(exclude_unset=True), user_id)