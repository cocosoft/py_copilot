"""搜索管理API接口（仅联网搜索配置）"""
from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.search_management_service import SearchManagementService
from app.services.web_search_service import web_search_service
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


@router.post("", response_model=Dict[str, Any])
async def perform_search(
    search_query: str = Body(..., alias="query", description="搜索查询词"),
    search_type: str = Body(default="web", description="搜索类型（web）"),
    limit: int = Body(default=10, description="返回结果数量"),
    db: Session = Depends(get_db)
) -> Any:
    """
    执行联网搜索
    
    Args:
        search_query: 搜索查询词
        search_type: 搜索类型（web）
        limit: 返回结果数量
        db: 数据库会话
    
    Returns:
        搜索结果字典，包含查询信息和结果列表
    """
    try:
        if not search_query:
            raise HTTPException(status_code=400, detail="搜索查询词不能为空")
        
        # 执行搜索
        result = web_search_service.search(
            query=search_query,
            engine="google",  # 默认使用Google搜索引擎
            safe_search=True,
            num_results=limit
        )
        
        # 格式化响应
        return {
            "results": result.get("results", []),
            "query": search_query,
            "search_type": search_type,
            "limit": limit,
            "success": result.get("success", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")