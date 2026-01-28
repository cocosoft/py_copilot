"""
长期记忆机制 - 记忆管理API

提供记忆的创建、查询、更新、删除、检索和压缩功能。
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .memory_models import (
    MemoryItem, MemoryType, MemoryPriority, MemoryAccessPattern,
    memory_manager
)
from .memory_retrieval import (
    memory_retrieval_engine, memory_compression_engine
)

router = APIRouter(prefix="/api/memory", tags=["记忆管理"])


class MemoryCreateRequest(BaseModel):
    """记忆创建请求模型"""
    agent_id: str
    user_id: str
    memory_type: str
    content: str
    summary: str = ""
    priority: str = "medium"
    expires_in_days: Optional[int] = None
    metadata: Dict[str, Any] = None
    tags: List[str] = None


class MemoryUpdateRequest(BaseModel):
    """记忆更新请求模型"""
    content: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[str] = None
    expires_in_days: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class MemoryResponse(BaseModel):
    """记忆响应模型"""
    memory_id: str
    agent_id: str
    user_id: str
    memory_type: str
    content: str
    summary: str
    priority: str
    access_count: int
    last_accessed: str
    created_at: str
    expires_at: Optional[str]
    metadata: Dict[str, Any]
    tags: List[str]


class MemoryRetrievalRequest(BaseModel):
    """记忆检索请求模型"""
    query: Optional[str] = None
    context: Optional[str] = None
    memory_types: Optional[List[str]] = None
    access_pattern: str = "recent"
    max_results: int = 5
    min_relevance: float = 0.1


class MemoryRetrievalResponse(BaseModel):
    """记忆检索响应模型"""
    memories: List[MemoryResponse]
    total_found: int
    retrieval_time_ms: float
    query: Optional[str]
    context: Optional[str]


class MemoryStatsResponse(BaseModel):
    """记忆统计响应模型"""
    total_memories: int
    type_stats: Dict[str, int]
    priority_stats: Dict[str, int]
    expired_count: int
    recent_access_count: int
    agent_id: Optional[str]
    user_id: Optional[str]


class MemoryCompressionResponse(BaseModel):
    """记忆压缩响应模型"""
    compressed: bool
    original_count: int
    compressed_count: int
    reduction_ratio: float
    memories_kept: List[str]
    error: Optional[str] = None


@router.post("", response_model=MemoryResponse)
async def create_memory(request: MemoryCreateRequest):
    """创建记忆
    
    Args:
        request: 创建请求
        
    Returns:
        创建的记忆
    """
    try:
        # 验证记忆类型
        try:
            memory_type = MemoryType(request.memory_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的记忆类型: {request.memory_type}")
        
        # 验证优先级
        try:
            priority = MemoryPriority(request.priority)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的优先级: {request.priority}")
        
        # 计算过期时间
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.now() + timedelta(days=request.expires_in_days)
        
        # 创建记忆项
        memory = MemoryItem(
            agent_id=request.agent_id,
            user_id=request.user_id,
            memory_type=memory_type,
            content=request.content,
            summary=request.summary,
            priority=priority,
            expires_at=expires_at,
            metadata=request.metadata or {},
            tags=request.tags or []
        )
        
        # 保存到数据库
        if not memory_manager.store_memory(memory):
            raise HTTPException(status_code=500, detail="创建记忆失败")
        
        return MemoryResponse(**memory.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建记忆失败: {str(e)}")


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """获取记忆
    
    Args:
        memory_id: 记忆ID
        
    Returns:
        记忆信息
    """
    memory = memory_manager.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"记忆 {memory_id} 未找到")
    
    return MemoryResponse(**memory.to_dict())


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: str, request: MemoryUpdateRequest):
    """更新记忆
    
    Args:
        memory_id: 记忆ID
        request: 更新请求
        
    Returns:
        更新后的记忆
    """
    # 获取现有记忆
    memory = memory_manager.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"记忆 {memory_id} 未找到")
    
    try:
        # 更新字段
        if request.content is not None:
            memory.content = request.content
            
        if request.summary is not None:
            memory.summary = request.summary
            
        if request.priority is not None:
            try:
                memory.priority = MemoryPriority(request.priority)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的优先级: {request.priority}")
                
        if request.expires_in_days is not None:
            if request.expires_in_days > 0:
                memory.expires_at = datetime.now() + timedelta(days=request.expires_in_days)
            else:
                memory.expires_at = None
                
        if request.metadata is not None:
            memory.metadata = request.metadata
            
        if request.tags is not None:
            memory.tags = request.tags
            
        # 更新数据库
        if not memory_manager.store_memory(memory):
            raise HTTPException(status_code=500, detail="更新记忆失败")
        
        return MemoryResponse(**memory.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新记忆失败: {str(e)}")


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """删除记忆
    
    Args:
        memory_id: 记忆ID
        
    Returns:
        删除结果
    """
    # 检查记忆是否存在
    memory = memory_manager.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"记忆 {memory_id} 未找到")
    
    # 删除记忆
    if not memory_manager.delete_memory(memory_id):
        raise HTTPException(status_code=500, detail="删除记忆失败")
    
    return {
        "status": "success",
        "message": f"记忆 {memory_id} 已删除",
        "memory_id": memory_id,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/retrieve", response_model=MemoryRetrievalResponse)
async def retrieve_memories(
    agent_id: str = Query(...),
    user_id: str = Query(...),
    request: MemoryRetrievalRequest = None
):
    """检索记忆
    
    Args:
        agent_id: 智能体ID
        user_id: 用户ID
        request: 检索请求
        
    Returns:
        检索结果
    """
    import time
    start_time = time.time()
    
    try:
        # 解析记忆类型
        memory_types = None
        if request and request.memory_types:
            try:
                memory_types = [MemoryType(mt) for mt in request.memory_types]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"不支持的记忆类型: {str(e)}")
        
        # 解析访问模式
        access_pattern = MemoryAccessPattern.RECENT
        if request and request.access_pattern:
            try:
                access_pattern = MemoryAccessPattern(request.access_pattern)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的访问模式: {request.access_pattern}")
        
        # 检索记忆
        memories = await memory_retrieval_engine.retrieve_memories(
            agent_id=agent_id,
            user_id=user_id,
            query=request.query if request else None,
            context=request.context if request else None,
            memory_types=memory_types,
            access_pattern=access_pattern,
            max_results=request.max_results if request else 5,
            min_relevance=request.min_relevance if request else 0.1
        )
        
        retrieval_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        # 转换为响应模型
        memory_responses = [MemoryResponse(**memory.to_dict()) for memory in memories]
        
        return MemoryRetrievalResponse(
            memories=memory_responses,
            total_found=len(memories),
            retrieval_time_ms=round(retrieval_time, 2),
            query=request.query if request else None,
            context=request.context if request else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索记忆失败: {str(e)}")


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    agent_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """获取记忆统计信息
    
    Args:
        agent_id: 智能体ID过滤
        user_id: 用户ID过滤
        
    Returns:
        统计信息
    """
    try:
        stats = memory_manager.get_memory_stats(agent_id, user_id)
        
        return MemoryStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆统计失败: {str(e)}")


@router.post("/compress", response_model=MemoryCompressionResponse)
async def compress_memories(
    agent_id: str = Query(...),
    user_id: str = Query(...),
    target_size: int = Query(500, ge=10, le=10000)
):
    """压缩记忆
    
    Args:
        agent_id: 智能体ID
        user_id: 用户ID
        target_size: 目标记忆数量
        
    Returns:
        压缩结果
    """
    try:
        result = await memory_compression_engine.compress_memories(
            agent_id=agent_id,
            user_id=user_id,
            target_size=target_size
        )
        
        return MemoryCompressionResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"压缩记忆失败: {str(e)}")


@router.post("/cleanup")
async def cleanup_expired_memories():
    """清理过期记忆
    
    Returns:
        清理结果
    """
    try:
        deleted_count = memory_manager.cleanup_expired_memories()
        
        return {
            "status": "success",
            "message": f"清理了 {deleted_count} 个过期记忆",
            "deleted_count": deleted_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理过期记忆失败: {str(e)}")


@router.get("/search")
async def search_memories(
    agent_id: str = Query(...),
    user_id: str = Query(...),
    query: str = Query(None),
    memory_type: str = Query(None),
    priority: str = Query(None),
    tags: str = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """搜索记忆
    
    Args:
        agent_id: 智能体ID
        user_id: 用户ID
        query: 查询文本
        memory_type: 记忆类型过滤
        priority: 优先级过滤
        tags: 标签过滤（逗号分隔）
        limit: 限制数量
        offset: 偏移量
        
    Returns:
        搜索结果
    """
    try:
        # 解析记忆类型
        memory_type_enum = None
        if memory_type:
            try:
                memory_type_enum = MemoryType(memory_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的记忆类型: {memory_type}")
        
        # 解析优先级
        priority_enum = None
        if priority:
            try:
                priority_enum = MemoryPriority(priority)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的优先级: {priority}")
        
        # 解析标签
        tags_list = tags.split(",") if tags else None
        
        # 搜索记忆
        memories = memory_manager.search_memories(
            agent_id=agent_id,
            user_id=user_id,
            query=query,
            memory_type=memory_type_enum,
            priority=priority_enum,
            tags=tags_list,
            limit=limit,
            offset=offset
        )
        
        # 转换为响应模型
        memory_responses = [MemoryResponse(**memory.to_dict()) for memory in memories]
        
        return {
            "query": query,
            "filters": {
                "memory_type": memory_type,
                "priority": priority,
                "tags": tags_list
            },
            "results": memory_responses,
            "total_count": len(memories),
            "has_more": len(memories) == limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {str(e)}")


@router.get("/types/memory-types")
async def get_memory_types():
    """获取支持的记忆类型
    
    Returns:
        记忆类型列表
    """
    return {
        "memory_types": [memory_type.value for memory_type in MemoryType],
        "descriptions": {
            "conversation": "对话记忆 - 用户与智能体的对话记录",
            "fact": "事实记忆 - 客观事实和知识",
            "preference": "偏好记忆 - 用户的个人偏好",
            "behavior": "行为记忆 - 用户的行为模式",
            "knowledge": "知识记忆 - 领域专业知识",
            "event": "事件记忆 - 重要事件记录",
            "relationship": "关系记忆 - 实体间的关系",
            "custom": "自定义记忆 - 用户自定义类型"
        }
    }


@router.get("/types/priority-types")
async def get_priority_types():
    """获取支持的优先级类型
    
    Returns:
        优先级类型列表
    """
    return {
        "priority_types": [priority.value for priority in MemoryPriority],
        "descriptions": {
            "low": "低优先级 - 可以安全遗忘的记忆",
            "medium": "中优先级 - 一般重要的记忆",
            "high": "高优先级 - 重要的记忆",
            "critical": "关键优先级 - 必须保留的关键记忆"
        }
    }


@router.get("/types/access-patterns")
async def get_access_patterns():
    """获取支持的访问模式
    
    Returns:
        访问模式列表
    """
    return {
        "access_patterns": [pattern.value for pattern in MemoryAccessPattern],
        "descriptions": {
            "frequent": "频繁访问 - 优先返回访问频率高的记忆",
            "recent": "最近访问 - 优先返回最近访问的记忆",
            "important": "重要记忆 - 优先返回高优先级的记忆",
            "random": "随机访问 - 随机返回记忆"
        }
    }


@router.post("/batch")
async def batch_create_memories(memories: List[MemoryCreateRequest]):
    """批量创建记忆
    
    Args:
        memories: 记忆列表
        
    Returns:
        批量创建结果
    """
    try:
        results = []
        success_count = 0
        
        for memory_request in memories:
            try:
                # 验证记忆类型
                try:
                    memory_type = MemoryType(memory_request.memory_type)
                except ValueError:
                    results.append({
                        "status": "error",
                        "error": f"不支持的记忆类型: {memory_request.memory_type}",
                        "agent_id": memory_request.agent_id,
                        "user_id": memory_request.user_id
                    })
                    continue
                
                # 验证优先级
                try:
                    priority = MemoryPriority(memory_request.priority)
                except ValueError:
                    results.append({
                        "status": "error",
                        "error": f"不支持的优先级: {memory_request.priority}",
                        "agent_id": memory_request.agent_id,
                        "user_id": memory_request.user_id
                    })
                    continue
                
                # 计算过期时间
                expires_at = None
                if memory_request.expires_in_days:
                    expires_at = datetime.now() + timedelta(days=memory_request.expires_in_days)
                
                # 创建记忆项
                memory = MemoryItem(
                    agent_id=memory_request.agent_id,
                    user_id=memory_request.user_id,
                    memory_type=memory_type,
                    content=memory_request.content,
                    summary=memory_request.summary,
                    priority=priority,
                    expires_at=expires_at,
                    metadata=memory_request.metadata or {},
                    tags=memory_request.tags or []
                )
                
                # 保存到数据库
                if memory_manager.store_memory(memory):
                    results.append({
                        "status": "success",
                        "memory_id": memory.memory_id,
                        "agent_id": memory_request.agent_id,
                        "user_id": memory_request.user_id
                    })
                    success_count += 1
                else:
                    results.append({
                        "status": "error",
                        "error": "存储记忆失败",
                        "agent_id": memory_request.agent_id,
                        "user_id": memory_request.user_id
                    })
                    
            except Exception as e:
                results.append({
                    "status": "error",
                    "error": str(e),
                    "agent_id": memory_request.agent_id,
                    "user_id": memory_request.user_id
                })
        
        return {
            "status": "success",
            "total_requests": len(memories),
            "success_count": success_count,
            "error_count": len(memories) - success_count,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量创建记忆失败: {str(e)}")


@router.get("/health")
async def get_memory_system_health():
    """获取记忆系统健康状态
    
    Returns:
        健康状态
    """
    try:
        # 获取系统统计
        stats = memory_manager.get_memory_stats()
        
        # 检查系统状态
        is_healthy = True
        warnings = []
        
        if stats["expired_count"] > 100:
            warnings.append(f"有 {stats['expired_count']} 个过期记忆需要清理")
            
        if stats["total_memories"] > 10000:
            warnings.append("记忆数量较多，建议进行压缩")
            
        if stats["recent_access_count"] == 0:
            warnings.append("最近7天没有记忆被访问")
            
        return {
            "status": "healthy" if is_healthy else "warning",
            "is_healthy": is_healthy,
            "warnings": warnings,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆系统健康状态失败: {str(e)}")