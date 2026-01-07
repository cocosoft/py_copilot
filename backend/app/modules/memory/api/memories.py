"""记忆模块API接口"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.memory import GlobalMemory, MemoryAssociation
from app.modules.memory.services.memory_service import MemoryService
from app.schemas.memory import (
    MemoryCreate, MemoryUpdate, MemoryResponse, MemorySearchRequest,
    MemoryStatsResponse, MemoryPatternsResponse, UserMemoryConfigUpdate,
    UserMemoryConfigResponse, EnhancedSearchRequest, EnhancedSearchResponse
)

router = APIRouter()


@router.post("/memories", response_model=MemoryResponse)
async def create_memory(
    memory_data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的记忆条目"""
    memory = MemoryService.create_memory(db, memory_data, current_user.id)
    return memory


@router.get("/memories", response_model=List[MemoryResponse])
async def get_user_memories(
    memory_types: Optional[List[str]] = Query(None, description="记忆类型过滤"),
    memory_categories: Optional[List[str]] = Query(None, description="记忆类别过滤"),
    session_id: Optional[str] = Query(None, description="会话ID过滤"),
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有记忆条目"""
    memories = MemoryService.get_user_memories(
        db, current_user.id, memory_types, memory_categories, limit, offset, session_id
    )
    return memories


@router.delete("/memories")
async def delete_all_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空用户所有记忆"""
    deleted_count = MemoryService.delete_all_memories(db, current_user.id)
    return {"message": f"所有记忆已清空，共删除 {deleted_count} 条记录"}


@router.get("/memories/search", response_model=List[MemoryResponse])
async def search_memories(
    query: str = Query(..., description="搜索查询"),
    memory_types: Optional[List[str]] = Query(None, description="记忆类型过滤"),
    memory_categories: Optional[List[str]] = Query(None, description="记忆类别过滤"),
    session_id: Optional[str] = Query(None, description="会话ID过滤"),
    context_ids: Optional[List[int]] = Query(None, description="上下文记忆ID列表"),
    limit: int = Query(10, ge=1, le=100, description="结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索记忆条目"""
    memories = MemoryService.search_memories(
        db, query, current_user.id, memory_types, memory_categories, limit, session_id, context_ids
    )
    return memories


@router.get("/memories/knowledge-graph")
async def build_user_knowledge_graph(
    max_nodes: int = Query(100, ge=10, le=500, description="知识图谱最大节点数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """构建用户的知识图谱"""
    graph_data = MemoryService.build_knowledge_graph(db, current_user.id, max_nodes)
    return {
        "message": "知识图谱构建完成",
        "graph_data": graph_data
    }





@router.get("/memories/{memory_id}/knowledge-graph")
async def traverse_memory_knowledge_graph(
    memory_id: int,
    max_depth: int = Query(3, ge=1, le=10, description="知识图谱遍历深度限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从特定记忆节点开始遍历知识图谱"""
    # 验证记忆是否属于当前用户
    memory = MemoryService.get_memory(db, memory_id, current_user.id)
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    graph_data = MemoryService.traverse_knowledge_graph(db, current_user.id, memory_id, max_depth)
    return {
        "message": "知识图谱遍历完成",
        "graph_data": graph_data
    }


@router.get("/memories/{memory_id}", response_model=MemoryResponse)
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


@router.put("/memories/{memory_id}", response_model=MemoryResponse)
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


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除记忆条目"""
    success = MemoryService.delete_memory(db, memory_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return {"message": "记忆删除成功"}


@router.get("/memories/analytics/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    time_range: str = Query("30d", description="时间范围"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户记忆统计信息"""
    stats = MemoryService.get_user_memory_stats(db, current_user.id, time_range)
    return stats


@router.get("/memories/analytics/patterns", response_model=MemoryPatternsResponse)
async def get_memory_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户记忆模式分析"""
    patterns = MemoryService.analyze_user_patterns(db, current_user.id)
    return patterns


@router.get("/memories/analytics/preferences")
async def get_user_memory_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户记忆偏好分析"""
    preferences = MemoryService.analyze_user_preferences(db, current_user.id)
    return preferences


@router.get("/conversations/{conversation_id}/memories", response_model=List[MemoryResponse])
async def get_conversation_memories(
    conversation_id: int,
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定对话关联的所有记忆条目"""
    memories = MemoryService.get_conversation_memories(
        db, conversation_id, current_user.id, limit, offset
    )
    return memories


@router.get("/knowledge-bases/{knowledge_base_id}/memories", response_model=List[MemoryResponse])
async def get_knowledge_memories(
    knowledge_base_id: int,
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定知识库关联的所有记忆条目"""
    memories = MemoryService.get_knowledge_memories(
        db, knowledge_base_id, current_user.id, limit, offset
    )
    return memories


@router.get("/context/memories", response_model=List[MemoryResponse])
async def get_session_context_memories(
    conversation_id: int = Query(..., description="对话ID"),
    limit: int = Query(10, ge=1, le=50, description="结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为对话获取相关上下文记忆"""
    # 暂时复用conversation_memories接口
    memories = MemoryService.get_conversation_memories(
        db, conversation_id, current_user.id, limit, 0
    )
    return memories


@router.get("/knowledge/enhanced-search", response_model=EnhancedSearchResponse)
async def enhanced_knowledge_search(
    query: str = Query(..., description="搜索查询"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    use_memory: bool = Query(True, description="是否使用全局记忆增强搜索"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    context_ids: Optional[List[int]] = Query(None, description="上下文记忆ID列表"),
    limit: int = Query(10, ge=1, le=100, description="结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用全局记忆增强的知识库搜索"""
    results = []
    
    # 搜索记忆（如果启用）
    memory_results = []
    if use_memory:
        # 使用上下文感知搜索记忆
        memories = MemoryService.search_memories(
            db, query, current_user.id, limit=limit, session_id=session_id, context_ids=context_ids
        )
        memory_results = [{
            "type": "memory",
            "id": mem.id,
            "title": mem.title,
            "content": mem.content,
            "score": mem.importance_score or 0.5,
            "source": "memory",
            "created_at": mem.created_at.isoformat()
        } for mem in memories]
    
    # 搜索知识库（简化实现，实际需要与知识库模块集成）
    knowledge_results = []
    try:
        # 尝试导入知识库服务
        from app.services.knowledge import knowledge_service
        
        # 执行知识库搜索
        knowledge_search_results = knowledge_service.search_documents(
            query=query,
            knowledge_base_id=knowledge_base_id,
            user_id=current_user.id,
            limit=limit
        )
        
        # 转换知识库搜索结果格式
        knowledge_results = [{
            "type": "knowledge",
            "id": result["id"],
            "title": result["title"],
            "content": result["content"],
            "score": result["score"],
            "source": "knowledge_base",
            "created_at": result["created_at"]
        } for result in knowledge_search_results]
    except ImportError:
        # 如果知识库服务不可用，返回空结果
        pass
    except Exception as e:
        # 记录错误但不中断搜索
        import logging
        logging.error(f"知识库搜索错误: {str(e)}")
    
    # 合并结果并排序（按相关性分数）
    results = memory_results + knowledge_results
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 限制总结果数量
    results = results[:limit]
    
    return EnhancedSearchResponse(
        query=query,
        results=results,
        memory_used=use_memory,
        total_results=len(results),
        knowledge_base_used=bool(knowledge_results),
        session_id=session_id
    )


@router.get("/memory-config", response_model=UserMemoryConfigResponse)
async def get_user_memory_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户记忆配置"""
    config = MemoryService.get_user_memory_config(db, current_user.id)
    if not config:
        # 返回默认配置
        from datetime import datetime
        return UserMemoryConfigResponse(
            id=0,  # 临时ID，实际创建时会生成
            user_id=current_user.id,
            short_term_retention_days=7,
            long_term_threshold=0.7,
            auto_cleanup_enabled=True,
            privacy_level="MEDIUM",
            sync_enabled=False,
            preferred_embedding_model="text-embedding-ada-002",
            created_at=datetime.now(),
            updated_at=None
        )
    return config


@router.put("/memory-config", response_model=UserMemoryConfigResponse)
async def update_user_memory_config(
    config_update: UserMemoryConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户记忆配置"""
    config_data = config_update.model_dump(exclude_unset=True)
    config = MemoryService.update_user_memory_config(db, current_user.id, config_data)
    return config


@router.get("/memories/{memory_id}/associations", response_model=List[dict])
async def get_memory_associations(
    memory_id: int,
    association_types: Optional[List[str]] = Query(None, description="关联类型过滤"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定记忆的关联记忆"""
    # 验证记忆是否属于当前用户
    memory = MemoryService.get_memory(db, memory_id, current_user.id)
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    # 查询关联记忆
    from sqlalchemy.orm import joinedload
    associations = db.query(MemoryAssociation).filter(
        ((MemoryAssociation.source_memory_id == memory_id) | 
         (MemoryAssociation.target_memory_id == memory_id))
    ).all()
    
    # 过滤关联类型
    if association_types:
        associations = [assoc for assoc in associations if assoc.association_type in association_types]
    
    # 构建响应
    result = []
    for association in associations:
        # 确定目标记忆ID
        if association.source_memory_id == memory_id:
            target_id = association.target_memory_id
        else:
            target_id = association.source_memory_id
        
        # 获取目标记忆
        target_memory = MemoryService.get_memory(db, target_id, current_user.id)
        if target_memory:
            result.append({
                "memory_id": target_id,
                "title": target_memory.title,
                "content": target_memory.content[:100] + "..." if len(target_memory.content) > 100 else target_memory.content,
                "memory_type": target_memory.memory_type,
                "memory_category": target_memory.memory_category,
                "association_type": association.association_type,
                "strength": association.strength,
                "created_at": association.created_at.isoformat()
            })
    
    return result


@router.get("/memory-associations", response_model=List[dict])
async def get_all_user_memory_associations(
    association_types: Optional[List[str]] = Query(None, description="关联类型过滤"),
    limit: int = Query(50, ge=1, le=200, description="结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有记忆关联"""
    # 查询用户的所有记忆关联
    associations = db.query(MemoryAssociation).join(
        GlobalMemory, 
        GlobalMemory.id == MemoryAssociation.source_memory_id
    ).filter(
        GlobalMemory.user_id == current_user.id,
        GlobalMemory.is_active == True
    ).limit(limit).all()
    
    # 过滤关联类型
    if association_types:
        associations = [assoc for assoc in associations if assoc.association_type in association_types]
    
    # 构建响应
    result = []
    for association in associations:
        # 获取源记忆和目标记忆
        source_memory = MemoryService.get_memory(db, association.source_memory_id, current_user.id)
        target_memory = MemoryService.get_memory(db, association.target_memory_id, current_user.id)
        
        if source_memory and target_memory:
            result.append({
                "id": association.id,
                "source_memory_id": association.source_memory_id,
                "source_memory_title": source_memory.title,
                "target_memory_id": association.target_memory_id,
                "target_memory_title": target_memory.title,
                "association_type": association.association_type,
                "strength": association.strength,
                "created_at": association.created_at.isoformat()
            })
    
    return result


@router.post("/memories/cleanup")
async def cleanup_expired_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清理过期记忆"""
    deleted_count = MemoryService.cleanup_expired_memories(db, current_user.id)
    return {
        "message": f"清理完成",
        "deleted_count": deleted_count
    }


@router.post("/memories/compress")
async def compress_similar_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """压缩相似记忆"""
    result = MemoryService.compress_similar_memories(db, current_user.id)
    return {
        "message": f"压缩完成",
        "processed": result["processed"],
        "compressed": result["compressed"],
        "created": result["created"]
    }
