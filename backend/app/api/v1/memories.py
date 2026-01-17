from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.memory import (
    MemoryCreate,
    MemoryUpdate,
    MemoryResponse,
    MemorySearchRequest,
    MemoryStatsResponse,
    MemoryPatternsResponse,
    UserMemoryConfigUpdate,
    UserMemoryConfigResponse
)
from app.modules.memory.services.memory_service import MemoryService

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("/", response_model=MemoryResponse)
async def create_memory(
    memory_data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的记忆条目"""
    try:
        memory = MemoryService.create_memory(db, memory_data, current_user.id)
        return memory
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建记忆失败: {str(e)}")


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定记忆条目详情"""
    memory = MemoryService.get_memory(db, memory_id, current_user.id)
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return memory


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    memory_update: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新记忆条目"""
    memory = MemoryService.update_memory(db, memory_id, memory_update, current_user.id)
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return memory


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除记忆条目"""
    success = MemoryService.delete_memory(db, memory_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return {"message": "记忆已成功删除"}


@router.get("/", response_model=List[MemoryResponse])
async def get_user_memories(
    memory_types: Optional[List[str]] = Query(None, description="记忆类型过滤"),
    memory_categories: Optional[List[str]] = Query(None, description="记忆类别过滤"),
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    session_id: Optional[str] = Query(None, description="会话ID过滤"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有记忆条目"""
    memories = MemoryService.get_user_memories(
        db, current_user.id, memory_types, memory_categories, limit, offset, session_id
    )
    return memories


@router.post("/search", response_model=List[MemoryResponse])
async def search_memories(
    search_request: MemorySearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索记忆条目"""
    memories = MemoryService.search_memories(
        db, search_request.query, current_user.id,
        search_request.memory_types, search_request.memory_categories,
        search_request.limit, search_request.session_id, search_request.context_ids
    )
    return memories


@router.get("/analytics/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    time_range: str = Query("30d", description="时间范围"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户记忆统计信息"""
    stats = MemoryService.get_user_memory_stats(db, current_user.id, time_range)
    return stats


@router.get("/analytics/patterns", response_model=MemoryPatternsResponse)
async def get_memory_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户记忆模式分析"""
    patterns = MemoryService.analyze_user_patterns(db, current_user.id)
    return patterns


@router.get("/config", response_model=UserMemoryConfigResponse)
async def get_memory_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户记忆配置"""
    config = MemoryService.get_user_memory_config(db, current_user.id)
    if not config:
        raise HTTPException(status_code=404, detail="用户记忆配置不存在")
    return config


@router.put("/config", response_model=UserMemoryConfigResponse)
async def update_memory_config(
    config_update: UserMemoryConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户记忆配置"""
    config_data = config_update.model_dump(exclude_unset=True)
    config = MemoryService.update_user_memory_config(db, current_user.id, config_data)
    return config


@router.get("/context/memories", response_model=List[MemoryResponse])
async def get_session_context_memories(
    conversation_id: int,
    limit: int = Query(10, ge=1, le=50, description="结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为对话获取相关上下文记忆"""
    # TODO: 实现上下文相关记忆检索逻辑
    # 目前返回用户最近的记忆
    memories = await MemoryService.get_user_memories(db, current_user.id, limit=limit)
    return memories


@router.get("/conversations/{conversation_id}/memories", response_model=List[MemoryResponse])
async def get_conversation_memories(
    conversation_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定对话关联的所有记忆条目"""
    memories = await MemoryService.get_conversation_memories(
        db, conversation_id, current_user.id, limit=limit, offset=offset
    )
    return memories


@router.get("/knowledge-bases/{knowledge_base_id}/memories", response_model=List[MemoryResponse])
async def get_knowledge_memories(
    knowledge_base_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定知识库关联的所有记忆条目"""
    memories = MemoryService.get_knowledge_memories(
        db, knowledge_base_id, current_user.id, limit=limit, offset=offset
    )
    return memories


@router.post("/cleanup")
async def cleanup_expired_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清理过期的短期记忆"""
    deleted_count = MemoryService.cleanup_expired_memories(db, current_user.id)
    return {
        "message": "成功清理过期记忆",
        "deleted_count": deleted_count
    }


@router.post("/compress")
async def compress_similar_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """压缩相似的短期记忆为长期记忆"""
    result = MemoryService.compress_similar_memories(db, current_user.id)
    return {
        "message": "成功压缩相似记忆",
        "result": result
    }