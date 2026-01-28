"""
记忆-知识库联动API

提供记忆与知识库协同工作的RESTful API接口。
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from .knowledge_linking import MemoryKnowledgeLinker, MemoryKnowledgeWorkflow
from .memory_models import MemoryPriority

router = APIRouter()


@router.post("/memory/{memory_id}/extract-knowledge")
async def extract_knowledge_from_memory(
    memory_id: int,
    knowledge_base_id: Optional[int] = Query(None, description="目标知识库ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """从记忆中提取知识到知识库
    
    Args:
        memory_id: 记忆ID
        knowledge_base_id: 目标知识库ID（可选）
        db: 数据库会话
        
    Returns:
        提取结果
    """
    try:
        linker = MemoryKnowledgeLinker(db)
        result = linker.extract_knowledge_from_memory(
            memory_id=memory_id,
            knowledge_base_id=knowledge_base_id
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', '提取失败'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取知识失败: {str(e)}")


@router.post("/memory/{memory_id}/enhance-with-knowledge")
async def enhance_memory_with_knowledge(
    memory_id: int,
    query: Optional[str] = Query(None, description="搜索查询（可选，默认使用记忆内容）"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID（可选）"),
    limit: int = Query(3, ge=1, le=10, description="返回结果数量限制"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """使用知识库增强记忆
    
    Args:
        memory_id: 记忆ID
        query: 搜索查询（可选）
        knowledge_base_id: 知识库ID（可选）
        limit: 返回结果数量限制
        db: 数据库会话
        
    Returns:
        增强结果
    """
    try:
        linker = MemoryKnowledgeLinker(db)
        result = linker.enhance_memory_with_knowledge(
            memory_id=memory_id,
            query=query,
            knowledge_base_id=knowledge_base_id,
            limit=limit
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', '增强失败'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记忆增强失败: {str(e)}")


@router.post("/memory/{memory_id}/sync-with-knowledge")
async def sync_memory_with_knowledge(
    memory_id: int,
    knowledge_base_id: int = Query(..., description="知识库ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """同步记忆与知识库
    
    Args:
        memory_id: 记忆ID
        knowledge_base_id: 知识库ID
        db: 数据库会话
        
    Returns:
        同步结果
    """
    try:
        linker = MemoryKnowledgeLinker(db)
        result = linker.sync_memory_knowledge(
            memory_id=memory_id,
            knowledge_base_id=knowledge_base_id
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', '同步失败'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/workflow/auto-extract-high-value-memories")
async def auto_extract_high_value_memories(
    knowledge_base_id: int = Query(..., description="目标知识库ID"),
    priority_threshold: MemoryPriority = Query(MemoryPriority.HIGH, description="优先级阈值"),
    batch_size: int = Query(10, ge=1, le=50, description="批量处理大小"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """自动提取高价值记忆到知识库
    
    Args:
        knowledge_base_id: 目标知识库ID
        priority_threshold: 优先级阈值
        batch_size: 批量处理大小
        db: 数据库会话
        
    Returns:
        提取结果
    """
    try:
        workflow = MemoryKnowledgeWorkflow(db)
        result = workflow.auto_extract_high_value_memories(
            knowledge_base_id=knowledge_base_id,
            priority_threshold=priority_threshold,
            batch_size=batch_size
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', '自动提取失败'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自动提取失败: {str(e)}")


@router.get("/memory/{memory_id}/knowledge-status")
async def get_memory_knowledge_status(
    memory_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取记忆的知识库状态
    
    Args:
        memory_id: 记忆ID
        db: 数据库会话
        
    Returns:
        知识库状态信息
    """
    try:
        from .memory_models import memory_manager
        
        memory = memory_manager.get_memory(memory_id, db)
        if not memory:
            raise HTTPException(status_code=404, detail="记忆不存在")
        
        metadata = memory.metadata or {}
        
        status_info = {
            "memory_id": memory_id,
            "memory_type": memory.memory_type.value,
            "priority": memory.priority.value,
            "knowledge_extracted": metadata.get('knowledge_extracted', False),
            "knowledge_enhanced": metadata.get('knowledge_enhanced', False),
            "knowledge_synced": metadata.get('knowledge_synced', False),
            "target_knowledge_base": metadata.get('target_knowledge_base'),
            "extraction_time": metadata.get('knowledge_extraction_time'),
            "enhancement_time": metadata.get('knowledge_enhancement_time'),
            "sync_time": metadata.get('sync_time'),
            "relevance_score": memory.calculate_relevance_score()
        }
        
        return status_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/workflow/stats")
async def get_workflow_statistics(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取工作流统计信息
    
    Args:
        db: 数据库会话
        
    Returns:
        工作流统计信息
    """
    try:
        from .memory_models import Memory
        
        # 获取记忆总数
        total_memories = db.query(Memory).count()
        
        # 获取已提取知识的记忆数
        extracted_memories = db.query(Memory).filter(
            Memory.metadata.op('->>')('knowledge_extracted').cast(db.Boolean) == True
        ).count()
        
        # 获取已增强的记忆数
        enhanced_memories = db.query(Memory).filter(
            Memory.metadata.op('->>')('knowledge_enhanced').cast(db.Boolean) == True
        ).count()
        
        # 获取已同步的记忆数
        synced_memories = db.query(Memory).filter(
            Memory.metadata.op('->>')('knowledge_synced').cast(db.Boolean) == True
        ).count()
        
        # 计算高价值记忆比例（HIGH和CRITICAL优先级）
        high_value_memories = db.query(Memory).filter(
            Memory.priority.in_([MemoryPriority.HIGH, MemoryPriority.CRITICAL])
        ).count()
        
        stats = {
            "total_memories": total_memories,
            "extracted_memories": extracted_memories,
            "enhanced_memories": enhanced_memories,
            "synced_memories": synced_memories,
            "high_value_memories": high_value_memories,
            "extraction_rate": extracted_memories / total_memories if total_memories > 0 else 0,
            "enhancement_rate": enhanced_memories / total_memories if total_memories > 0 else 0,
            "sync_rate": synced_memories / total_memories if total_memories > 0 else 0,
            "high_value_rate": high_value_memories / total_memories if total_memories > 0 else 0
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")