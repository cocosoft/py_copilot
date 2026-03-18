"""知识图谱API路由"""
import logging
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import uuid

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
from app.services.knowledge.graph.knowledge_graph_service import KnowledgeGraphService
from app.services.knowledge.graph.batch_graph_builder import BatchGraphBuilder, BatchBuildResult

logger = logging.getLogger(__name__)

# 创建Pydantic模型用于API请求和响应
from pydantic import BaseModel, validator, model_validator
from typing import List, Dict, Any, Optional

# ==================== 批量构建任务状态管理 ====================

# 内存中的任务状态存储
_batch_build_tasks: Dict[str, Dict[str, Any]] = {}


def _update_batch_progress(batch_id: str, current: int, total: int, message: str = ""):
    """
    更新批量构建任务进度
    
    Args:
        batch_id: 批次ID
        current: 当前完成数量
        total: 总数量
        message: 进度消息
    """
    if batch_id in _batch_build_tasks:
        progress = (current / total * 100) if total > 0 else 0
        _batch_build_tasks[batch_id].update({
            "progress": round(progress, 2),
            "completed_documents": current,
            "current_message": message,
            "updated_at": datetime.now().isoformat()
        })


async def _run_batch_build_task(
    batch_id: str,
    document_ids: List[int],
    max_workers: int,
    knowledge_base_id: int = None
):
    """
    后台执行批量构建任务

    Args:
        batch_id: 批次ID
        document_ids: 文档ID列表
        max_workers: 最大并发数
        knowledge_base_id: 知识库ID，用于加载知识库级提取策略配置
    """
    logger.info(f"[后台任务] 开始执行批量构建任务: batch_id={batch_id}, "
               f"document_ids={document_ids}, knowledge_base_id={knowledge_base_id}")

    from app.services.knowledge.batch_processor import BatchKnowledgeGraphBuilder
    from app.core.database import SessionLocal

    db = None
    try:
        db = SessionLocal()

        # 如果没有传入 knowledge_base_id，尝试从第一个文档获取
        if knowledge_base_id is None and document_ids:
            first_doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_ids[0]
            ).first()
            if first_doc:
                knowledge_base_id = first_doc.knowledge_base_id
                logger.info(f"从文档获取知识库ID: {knowledge_base_id}")
        
        # 创建构建器，传入 knowledge_base_id 以使用正确的提取策略
        builder = BatchKnowledgeGraphBuilder(
            max_workers=max_workers,
            knowledge_base_id=knowledge_base_id
        )
        
        # 更新任务状态为处理中
        _batch_build_tasks[batch_id].update({
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "total_documents": len(document_ids)
        })
        
        # 定义进度回调
        def progress_callback(current: int, total: int):
            _update_batch_progress(batch_id, current, total, f"已处理 {current}/{total} 个文档")
        
        # 执行批量构建
        result = await builder.build_graphs_batch(
            document_ids=document_ids,
            db=db,
            progress_callback=progress_callback
        )
        
        # 更新任务状态为完成
        _batch_build_tasks[batch_id].update({
            "status": "completed" if result.success else "failed",
            "completed_documents": result.items_processed,
            "failed_documents": result.items_failed,
            "progress": 100.0,
            "results": result.results,
            "errors": result.errors,
            "processing_time": result.processing_time,
            "completed_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        # 更新任务状态为失败
        _batch_build_tasks[batch_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })
    finally:
        if db:
            db.close()


class EntityExtractionRequest(BaseModel):
    document_id: Optional[int] = None
    text: Optional[str] = None
    knowledge_base_id: Optional[int] = None  # 知识库ID，用于加载知识库级提取策略配置
    entity_types: Optional[List[str]] = None  # 实体类型列表
    threshold: Optional[float] = 0.7  # 置信度阈值
    use_llm: Optional[bool] = True  # 是否使用LLM提取
    model_id: Optional[str] = None  # 模型ID
    model_configuration: Optional[Dict[str, Any]] = None  # 模型配置

    class Config:
        extra = "ignore"  # 忽略额外的字段，提高兼容性


class EntityExtractionResponse(BaseModel):
    success: bool
    entities_count: int = 0
    relationships_count: int = 0
    error: Optional[str] = None


class EntityExtractionResponseFixed(BaseModel):
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    success: bool


class EntitySearchRequest(BaseModel):
    entity_text: str
    entity_type: Optional[str] = None
    knowledge_base_id: Optional[int] = None


class EntityRelationshipResponse(BaseModel):
    entity: Dict[str, Any]
    outgoing_relationships: List[Dict[str, Any]]
    incoming_relationships: List[Dict[str, Any]]


class KnowledgeGraphDataResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class GraphBuildRequest(BaseModel):
    document_id: Optional[int] = None
    knowledge_base_id: Optional[int] = None
    rebuild: bool = False

    class Config:
        extra = "ignore"  # 忽略额外的字段，提高兼容性
        populate_by_name = True  # 允许通过字段名填充


class GraphBuildResponse(BaseModel):
    success: bool
    graph_id: Optional[str] = None
    nodes_count: int = 0
    edges_count: int = 0
    communities_count: int = 0
    statistics: Dict[str, Any] = {}
    error: Optional[str] = None


class GraphAnalysisResponse(BaseModel):
    graph_id: str
    analysis: Dict[str, Any]
    communities: List[Dict[str, Any]]
    central_nodes: List[Dict[str, Any]]


class DocumentSemanticsResponse(BaseModel):
    text_length: int
    word_count: int
    entity_count: int
    entity_density: float
    top_keywords: List[Dict[str, Any]]
    semantic_richness: float


class BatchGraphBuildRequest(BaseModel):
    """批量构建知识图谱请求"""
    document_ids: Optional[List[int]] = None
    knowledge_base_id: Optional[int] = None
    max_concurrent: int = 3
    batch_size: int = 10

    class Config:
        extra = "ignore"


class BatchGraphBuildResponse(BaseModel):
    """批量构建知识图谱响应"""
    success: bool
    batch_id: str
    status: str
    total_documents: int
    completed_count: int
    failed_count: int
    skipped_count: int
    total_entities: int
    total_relationships: int
    processing_time: float
    progress_percentage: float
    failed_tasks: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


router = APIRouter(tags=["knowledge-graph"])
knowledge_graph_service = KnowledgeGraphService()


@router.post("/extract-entities", response_model=EntityExtractionResponseFixed)
async def extract_entities(
    request: EntityExtractionRequest,
    db: Session = Depends(get_db)
):
    """从文档或文本中提取实体和关系"""
    try:
        logger.info(f"[extract_entities] 收到实体提取请求: document_id={request.document_id}, "
                   f"knowledge_base_id={request.knowledge_base_id}, use_llm={request.use_llm}, "
                   f"model_id={request.model_id}")

        # 验证必须提供document_id或text参数
        if not request.document_id and not request.text:
            logger.warning("[extract_entities] 请求参数错误: 必须提供document_id或text参数")
            raise HTTPException(status_code=400, detail="必须提供document_id或text参数")

        if request.document_id:
            # 从文档中提取实体和关系
            logger.info(f"[extract_entities] 开始从文档提取实体: document_id={request.document_id}")

            document = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == request.document_id
            ).first()

            if not document:
                logger.warning(f"[extract_entities] 文档不存在: document_id={request.document_id}")
                raise HTTPException(status_code=404, detail="文档不存在")

            logger.info(f"[extract_entities] 文档信息: id={document.id}, title={document.title}, "
                       f"content_length={len(document.content) if document.content else 0}, "
                       f"is_vectorized={document.is_vectorized}")

            # 检查文档是否已向量化（即是否已处理）
            if not document.is_vectorized:
                logger.warning(f"[extract_entities] 文档尚未处理: document_id={request.document_id}")
                raise HTTPException(status_code=400, detail="文档尚未处理，请先在文档管理页面处理文档后再进行实体识别")

            # 检查文档是否有内容
            if not document.content or not document.content.strip():
                logger.warning(f"[extract_entities] 文档内容为空: document_id={request.document_id}")
                raise HTTPException(status_code=400, detail="文档内容为空，无法提取实体。请重新处理文档或上传包含文本内容的文档")

            # 确定知识库ID
            kb_id = request.knowledge_base_id or document.knowledge_base_id
            logger.info(f"[extract_entities] 使用知识库ID: {kb_id}")

            # 如果前端传递了模型配置，优先使用
            if request.model_id:
                logger.info(f"[extract_entities] 使用前端传递的模型: {request.model_id}")
                # 传递模型配置给提取服务
                result = knowledge_graph_service.extract_and_store_entities(
                    db, document, knowledge_base_id=kb_id, model_id=request.model_id
                )
            else:
                # 提取实体和关系并存储
                result = knowledge_graph_service.extract_and_store_entities(
                    db, document, knowledge_base_id=kb_id
                )

            if not result["success"]:
                logger.error(f"[extract_entities] 实体提取失败: {result.get('error', '未知错误')}")
                raise HTTPException(status_code=500, detail=result.get("error", "提取失败"))

            logger.info(f"[extract_entities] 实体提取成功: entities_count={result.get('entities_count', 0)}, "
                       f"relationships_count={result.get('relationships_count', 0)}")

            # 获取存储的实体和关系
            entities = knowledge_graph_service.get_document_entities(db, request.document_id)
            relationships = knowledge_graph_service.get_document_relationships(db, request.document_id)

            logger.info(f"[extract_entities] 返回结果: entities={len(entities)}, relationships={len(relationships)}")
            logger.info(f"[extract_entities] 前5个实体: {entities[:5]}")

            return {
                "entities": entities,
                "relationships": relationships,
                "success": True
            }
        elif request.text:
            # 从文本内容直接提取实体和关系（不存储到数据库）
            if not request.text.strip():
                raise HTTPException(status_code=400, detail="文本内容不能为空")

            # 使用 _get_text_processor 方法获取文本处理器
            text_processor = knowledge_graph_service._get_text_processor(db, request.knowledge_base_id)
            # 直接从文本提取实体和关系（使用 await 调用异步函数）
            entities, relationships = await text_processor.extract_entities_relationships(request.text)
            
            # 转换实体格式以匹配前端预期
            formatted_entities = []
            for i, entity in enumerate(entities):
                formatted_entities.append({
                    "id": i + 1,
                    "text": entity["text"],
                    "type": entity["type"],
                    "start_pos": entity.get("start_pos", 0),
                    "end_pos": entity.get("end_pos", len(entity["text"])),
                    "confidence": entity.get("confidence", 0.7)
                })
            
            # 转换关系格式以匹配前端预期
            formatted_relationships = []
            for i, rel in enumerate(relationships):
                # 查找对应的实体索引
                source_idx = next((idx for idx, ent in enumerate(formatted_entities) if ent["text"] == rel["subject"]), None)
                target_idx = next((idx for idx, ent in enumerate(formatted_entities) if ent["text"] == rel["object"]), None)
                
                if source_idx is not None and target_idx is not None:
                    formatted_relationships.append({
                        "id": i + 1,
                        "subject": rel["subject"],
                        "object": rel["object"],
                        "relation": rel["relation"],
                        "source": {
                            "id": source_idx + 1,
                            "text": rel["subject"]
                        },
                        "target": {
                            "id": target_idx + 1,
                            "text": rel["object"]
                        },
                        "confidence": rel.get("confidence", 0.7)
                    })
            
            return {
                "entities": formatted_entities,
                "relationships": formatted_relationships,
                "success": True
            }
        
        # 这种情况理论上不会发生，因为validator已经检查过
        raise HTTPException(status_code=400, detail="必须提供document_id或text参数")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实体提取失败: {str(e)}")


@router.get("/documents/{document_id}/entities")
async def get_document_entities(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有实体"""
    try:
        entities = knowledge_graph_service.get_document_entities(db, document_id)
        return {"entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体失败: {str(e)}")

@router.get("/knowledge-bases/{knowledge_base_id}/entities")
async def get_knowledge_base_entities(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """获取知识库的所有实体"""
    try:
        entities = knowledge_graph_service.get_knowledge_base_entities(db, knowledge_base_id)
        return {"entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库实体失败: {str(e)}")

# 添加单数形式的路由以兼容前端请求
@router.get("/document/{document_id}/entities")
async def get_document_entities_singular(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有实体（单数形式路由，兼容前端请求）"""
    return await get_document_entities(document_id, db)


@router.get("/documents/{document_id}/relationships")
async def get_document_relationships(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有关系"""
    try:
        relationships = knowledge_graph_service.get_document_relationships(db, document_id)
        return {"relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关系失败: {str(e)}")

# 添加单数形式的路由以兼容前端请求
@router.get("/document/{document_id}/relationships")
async def get_document_relationships_singular(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有关系（单数形式路由，兼容前端请求）"""
    return await get_document_relationships(document_id, db)


@router.get("/search-entities")
async def search_entities(
    entity_text: Optional[str] = Query(None, description="实体文本"),
    entity_type: Optional[str] = Query(None, description="实体类型"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """搜索实体
    
    如果提供 entity_text，则按文本搜索；
    如果不提供 entity_text，则返回知识库下的所有实体（支持分页）
    """
    try:
        from app.modules.knowledge.models.knowledge_document import DocumentEntity
        
        # 构建查询
        query = db.query(DocumentEntity)
        
        # 如果指定了知识库ID，添加过滤条件
        if knowledge_base_id:
            query = query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        
        # 如果提供了实体文本，添加文本搜索条件
        if entity_text:
            query = query.filter(DocumentEntity.entity_text.contains(entity_text))
        
        # 如果提供了实体类型，添加类型过滤
        if entity_type:
            query = query.filter(DocumentEntity.entity_type == entity_type)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        entities = query.offset(skip).limit(limit).all()
        
        # 格式化结果
        entity_list = []
        for entity in entities:
            entity_list.append({
                "id": entity.id,
                "name": entity.entity_text,
                "type": entity.entity_type,
                "documentId": entity.document_id,
                "document_count": 1,
                "relation_count": 0,
                "confidence": entity.confidence or 1.0,
                "createdAt": entity.created_at.isoformat() if entity.created_at else None
            })
        
        return {
            "data": entity_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索实体失败: {str(e)}")


@router.get("/entities/{entity_id}/relationships")
async def get_entity_relationships(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """获取实体的所有关系"""
    try:
        result = knowledge_graph_service.get_entity_relationships(db, entity_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return EntityRelationshipResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体关系失败: {str(e)}")


@router.get("/graph-data")
async def get_knowledge_graph_data(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    document_id: Optional[int] = Query(None, description="文档ID"),
    layer: Optional[str] = Query("document", description="图层类型: document, kb, global"),
    db: Session = Depends(get_db)
):
    """获取知识图谱数据（用于可视化）
    
    支持三级图谱数据查询：
    - document: 文档级实体和关系
    - kb: 知识库级实体和关系
    - global: 全局级实体和关系
    """
    try:
        graph_data = knowledge_graph_service.get_graph_data_by_layer(
            db, 
            layer=layer,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id
        )
        
        # 检查是否返回错误
        if "error" in graph_data:
            # 返回空数据而不是抛出异常
            return {
                "nodes": [],
                "edges": [],
                "statistics": {
                    "error": graph_data["error"],
                    "total_entities": 0,
                    "total_relationships": 0
                }
            }
        
        return KnowledgeGraphDataResponse(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识图谱数据失败: {str(e)}")


@router.get("/documents/{document_id}/keywords")
async def get_document_keywords(
    document_id: int,
    top_n: int = Query(10, ge=1, le=50, description="返回关键词数量"),
    db: Session = Depends(get_db)
):
    """获取文档的关键词"""
    try:
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        keywords = knowledge_graph_service.extract_keywords_from_document(document, top_n)
        return {"keywords": keywords}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取关键词失败: {str(e)}")


@router.post("/build-graph", response_model=GraphBuildResponse)
async def build_knowledge_graph(
    request: GraphBuildRequest,
    db: Session = Depends(get_db)
):
    """构建知识图谱"""
    try:
        # 验证参数
        if not request.document_id and not request.knowledge_base_id:
            raise HTTPException(status_code=400, detail="必须提供document_id或knowledge_base_id参数")

        if request.document_id:
            # 先检查文档是否存在
            document = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == request.document_id
            ).first()

            if not document:
                raise HTTPException(status_code=404, detail="文档不存在")

            # 检查文档是否已向量化
            if not document.is_vectorized:
                raise HTTPException(status_code=400, detail="文档尚未向量化，请先处理文档")

            # 检查文档是否有内容
            if not document.content or not document.content.strip():
                raise HTTPException(status_code=400, detail="文档内容为空，无法构建知识图谱。请重新处理文档或上传包含文本内容的文档")

            # 构建单个文档的知识图谱
            result = knowledge_graph_service.build_document_graph(request.document_id, db)
        else:
            # 构建整个知识库的知识图谱
            result = knowledge_graph_service.build_knowledge_base_graph(request.knowledge_base_id, db)

        if "error" in result:
            # 根据错误类型返回不同的状态码
            error_msg = result["error"]
            if "内容为空" in error_msg or "没有内容" in error_msg:
                raise HTTPException(status_code=400, detail=f"无法构建知识图谱: {error_msg}")
            elif "不存在" in error_msg:
                raise HTTPException(status_code=404, detail=error_msg)
            elif "实体提取" in error_msg or "没有发现任何实体" in error_msg:
                # 实体提取失败是内容质量问题，返回400而不是500
                raise HTTPException(status_code=400, detail=f"文档内容无法提取有效实体，请检查文档内容质量或更换文档后重试。详情: {error_msg}")
            else:
                raise HTTPException(status_code=500, detail=error_msg)

        return GraphBuildResponse(
            success=True,
            graph_id=result.get("graph_id"),
            nodes_count=result.get("nodes_count", 0),
            edges_count=result.get("edges_count", 0),
            communities_count=result.get("communities_count", 0),
            statistics=result.get("statistics", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建知识图谱失败: {str(e)}")


@router.get("/documents/{document_id}/graph")
async def get_document_graph(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的知识图谱数据"""
    try:
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查文档是否已向量化
        if not document.is_vectorized:
            raise HTTPException(status_code=400, detail="文档尚未向量化，请先处理文档")

        # 检查文档是否有内容
        if not document.content or not document.content.strip():
            raise HTTPException(status_code=400, detail="文档内容为空，无法获取知识图谱数据")

        graph_data = knowledge_graph_service.get_document_graph_data(db, document_id)

        if "error" in graph_data:
            # 根据错误类型返回不同的状态码
            error_msg = graph_data["error"]
            if "内容为空" in error_msg or "没有内容" in error_msg:
                raise HTTPException(status_code=400, detail=f"无法获取知识图谱: {error_msg}")
            elif "不存在" in error_msg:
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)

        return KnowledgeGraphDataResponse(**graph_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档图谱数据失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/graph")
async def get_knowledge_base_graph(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """获取知识库的知识图谱数据"""
    try:
        graph_data = knowledge_graph_service.get_knowledge_base_graph_data(db, knowledge_base_id)

        if "error" in graph_data:
            error_msg = graph_data["error"]
            if "不存在" in error_msg:
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)

        # 检查是否是空知识库
        metadata = graph_data.get("metadata", {})
        if metadata.get("is_empty", False):
            # 返回空图谱数据，但状态码为 200
            return KnowledgeGraphDataResponse(
                nodes=[],
                edges=[],
                statistics={
                    "total_entities": 0,
                    "total_relationships": 0,
                    "message": "知识库存在但没有文档，请先上传文档"
                }
            )

        return KnowledgeGraphDataResponse(**graph_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库图谱数据失败: {str(e)}")


@router.get("/graphs/{graph_id}/analyze", response_model=GraphAnalysisResponse)
async def analyze_graph(
    graph_id: str,
    db: Session = Depends(get_db)
):
    """分析知识图谱"""
    try:
        analysis_result = knowledge_graph_service.analyze_graph(graph_id, db)
        
        if "error" in analysis_result:
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        return GraphAnalysisResponse(**analysis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析知识图谱失败: {str(e)}")


@router.get("/graphs/{graph_id}/similar-nodes")
async def find_similar_nodes(
    graph_id: str,
    node_id: str,
    max_results: int = Query(10, ge=1, le=50, description="最大返回结果数量"),
    db: Session = Depends(get_db)
):
    """查找相似节点"""
    try:
        similar_nodes = knowledge_graph_service.find_similar_nodes(graph_id, node_id, max_results, db)
        
        if "error" in similar_nodes:
            raise HTTPException(status_code=500, detail=similar_nodes["error"])
        
        return {"similar_nodes": similar_nodes}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找相似节点失败: {str(e)}")


@router.get("/graphs/{graph_id}/path")
async def find_path_between_nodes(
    graph_id: str,
    source_node: str,
    target_node: str,
    max_path_length: int = Query(5, ge=1, le=10, description="最大路径长度"),
    db: Session = Depends(get_db)
):
    """查找两个节点之间的路径"""
    try:
        path_result = knowledge_graph_service.find_path_between_nodes(
            graph_id, source_node, target_node, max_path_length, db
        )
        
        if "error" in path_result:
            raise HTTPException(status_code=500, detail=path_result["error"])
        
        return {"path": path_result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找路径失败: {str(e)}")


@router.get("/documents/{document_id}/semantics")
async def analyze_document_semantics(
    document_id: int,
    db: Session = Depends(get_db)
):
    """分析文档语义特征"""
    try:
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        semantics = knowledge_graph_service.analyze_document_semantics(document)
        if "error" in semantics:
            raise HTTPException(status_code=400, detail=semantics["error"])
        
        return DocumentSemanticsResponse(**semantics)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析文档语义失败: {str(e)}")


@router.get("/statistics")
async def get_knowledge_graph_statistics(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    db: Session = Depends(get_db)
):
    """获取知识图谱统计信息"""
    try:
        from sqlalchemy import func
        from app.modules.knowledge.models.knowledge_document import (
            DocumentEntity, EntityRelationship, KnowledgeDocument
        )
        
        # 构建查询
        entity_query = db.query(DocumentEntity)
        relationship_query = db.query(EntityRelationship)
        
        if knowledge_base_id:
            entity_query = entity_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
            relationship_query = relationship_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        
        # 统计信息
        total_entities = entity_query.count()
        total_relationships = relationship_query.count()
        
        # 按实体类型统计
        entity_types = entity_query.with_entities(
            DocumentEntity.entity_type, func.count(DocumentEntity.id)
        ).group_by(DocumentEntity.entity_type).all()
        
        # 按关系类型统计
        relationship_types = relationship_query.with_entities(
            EntityRelationship.relationship_type, func.count(EntityRelationship.id)
        ).group_by(EntityRelationship.relationship_type).all()
        
        return {
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "entity_types": dict(entity_types),
            "relationship_types": dict(relationship_types)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# ==================== 批量处理API ====================

class BatchEntityExtractionRequest(BaseModel):
    """批量实体提取请求"""
    texts: List[str]
    max_workers: int = 5
    batch_size: int = 10
    use_cache: bool = True


class BatchEntityExtractionResponse(BaseModel):
    """批量实体提取响应"""
    success: bool
    items_processed: int
    items_failed: int
    cache_hits: int
    processing_time: float
    results: List[Dict[str, Any]]
    errors: List[str]


class BatchDocumentProcessingRequest(BaseModel):
    """批量文档处理请求"""
    documents: List[Dict[str, Any]]
    max_workers: int = 3


class BatchDocumentProcessingResponse(BaseModel):
    """批量文档处理响应"""
    success: bool
    items_processed: int
    items_failed: int
    processing_time: float
    results: List[Dict[str, Any]]
    errors: List[str]


class BatchGraphBuildingRequest(BaseModel):
    """批量图谱构建请求"""
    document_ids: List[int]
    max_workers: int = 5
    knowledge_base_id: Optional[int] = None


class BatchGraphBuildingResponse(BaseModel):
    """批量图谱构建响应"""
    success: bool
    items_processed: int
    items_failed: int
    processing_time: float
    results: List[Dict[str, Any]]
    errors: List[str]


class BatchGraphBuildAsyncRequest(BaseModel):
    """异步批量图谱构建请求"""
    document_ids: List[int]
    max_workers: int = 3
    extract_entities: bool = True
    extract_relations: bool = True
    min_confidence: float = 0.7
    knowledge_base_id: Optional[int] = None


class BatchGraphBuildAsyncData(BaseModel):
    """异步批量图谱构建响应数据"""
    batch_id: str
    status: str
    total_documents: int
    message: str


class BatchGraphBuildAsyncResponse(BaseModel):
    """异步批量图谱构建响应"""
    success: bool
    data: BatchGraphBuildAsyncData


class BatchGraphBuildStatusData(BaseModel):
    """批量图谱构建状态响应数据"""
    batch_id: str
    status: str
    progress: float
    total_documents: int
    completed_documents: int
    failed_documents: int
    current_message: Optional[str] = None
    processing_time: Optional[float] = None
    results: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[str]] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class BatchGraphBuildStatusResponse(BaseModel):
    """批量图谱构建状态响应"""
    success: bool
    data: BatchGraphBuildStatusData


class BatchGraphBuildCancelData(BaseModel):
    """批量图谱构建取消响应数据"""
    batch_id: str
    status: str
    message: str


class BatchGraphBuildCancelResponse(BaseModel):
    """批量图谱构建取消响应"""
    success: bool
    data: BatchGraphBuildCancelData


@router.post("/batch/extract-entities", response_model=BatchEntityExtractionResponse)
async def batch_extract_entities(
    request: BatchEntityExtractionRequest
):
    """
    批量提取实体和关系

    支持并发批量处理多个文本，自动使用缓存减少LLM调用。
    """
    try:
        from app.services.knowledge.batch_processor import extract_entities_batch

        result = await extract_entities_batch(
            texts=request.texts,
            max_workers=request.max_workers,
            batch_size=request.batch_size,
            use_cache=request.use_cache
        )

        return BatchEntityExtractionResponse(
            success=result.success,
            items_processed=result.items_processed,
            items_failed=result.items_failed,
            cache_hits=result.cache_hits,
            processing_time=result.processing_time,
            results=result.results,
            errors=result.errors
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量实体提取失败: {str(e)}")


@router.post("/batch/process-documents", response_model=BatchDocumentProcessingResponse)
async def batch_process_documents(
    request: BatchDocumentProcessingRequest,
    db: Session = Depends(get_db)
):
    """
    批量处理文档

    并发处理多个文档，包括解析、分块、向量化和图谱化。
    """
    try:
        from app.services.knowledge.batch_processor import process_documents_batch

        result = await process_documents_batch(
            documents=request.documents,
            max_workers=request.max_workers
        )

        return BatchDocumentProcessingResponse(
            success=result.success,
            items_processed=result.items_processed,
            items_failed=result.items_failed,
            processing_time=result.processing_time,
            results=result.results,
            errors=result.errors
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量文档处理失败: {str(e)}")


@router.post("/batch/build-graphs", response_model=BatchGraphBuildingResponse)
async def batch_build_graphs(
    request: BatchGraphBuildingRequest,
    db: Session = Depends(get_db)
):
    """
    批量构建知识图谱

    为多个文档并发构建知识图谱。
    """
    try:
        from app.services.knowledge.batch_processor import build_knowledge_graphs_batch

        # 如果没有传入 knowledge_base_id，尝试从第一个文档获取
        knowledge_base_id = request.knowledge_base_id
        if knowledge_base_id is None and request.document_ids:
            first_doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == request.document_ids[0]
            ).first()
            if first_doc:
                knowledge_base_id = first_doc.knowledge_base_id
                logger.info(f"从文档获取知识库ID: {knowledge_base_id}")

        result = await build_knowledge_graphs_batch(
            document_ids=request.document_ids,
            db=db,
            max_workers=request.max_workers,
            knowledge_base_id=knowledge_base_id
        )

        return BatchGraphBuildingResponse(
            success=result.success,
            items_processed=result.items_processed,
            items_failed=result.items_failed,
            processing_time=result.processing_time,
            results=result.results,
            errors=result.errors
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量图谱构建失败: {str(e)}")


@router.post("/batch/build-graphs-async", response_model=BatchGraphBuildAsyncResponse)
async def batch_build_graphs_async(
    request: BatchGraphBuildAsyncRequest,
    background_tasks: BackgroundTasks
):
    """
    异步批量构建知识图谱

    启动后台任务为多个文档并发构建知识图谱，立即返回任务ID用于进度查询。
    """
    try:
        # 记录接收到的请求参数
        logger.info(f"[API] 接收到批量构建请求: document_ids={request.document_ids}, "
                   f"knowledge_base_id={request.knowledge_base_id}, max_workers={request.max_workers}")

        # 生成唯一的批次ID
        batch_id = f"kg_batch_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 初始化任务状态
        _batch_build_tasks[batch_id] = {
            "batch_id": batch_id,
            "status": "pending",
            "progress": 0.0,
            "total_documents": len(request.document_ids),
            "completed_documents": 0,
            "failed_documents": 0,
            "current_message": "等待开始...",
            "created_at": datetime.now().isoformat(),
            "document_ids": request.document_ids,
            "max_workers": request.max_workers
        }
        
        # 启动后台任务，传入 knowledge_base_id 以使用正确的提取策略
        background_tasks.add_task(
            _run_batch_build_task,
            batch_id,
            request.document_ids,
            request.max_workers,
            request.knowledge_base_id
        )
        
        return BatchGraphBuildAsyncResponse(
            success=True,
            data=BatchGraphBuildAsyncData(
                batch_id=batch_id,
                status="pending",
                total_documents=len(request.document_ids),
                message="批量构建任务已启动"
            )
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动批量图谱构建失败: {str(e)}")


@router.get("/batch/status/{batch_id}", response_model=BatchGraphBuildStatusResponse)
async def get_batch_build_status(batch_id: str):
    """
    获取批量构建任务状态

    查询指定批次ID的构建进度和状态。
    """
    try:
        if batch_id not in _batch_build_tasks:
            raise HTTPException(status_code=404, detail=f"未找到批次ID: {batch_id}")
        
        task = _batch_build_tasks[batch_id]
        
        return BatchGraphBuildStatusResponse(
            success=True,
            data=BatchGraphBuildStatusData(
                batch_id=batch_id,
                status=task.get("status", "unknown"),
                progress=task.get("progress", 0.0),
                total_documents=task.get("total_documents", 0),
                completed_documents=task.get("completed_documents", 0),
                failed_documents=task.get("failed_documents", 0),
                current_message=task.get("current_message"),
                processing_time=task.get("processing_time"),
                results=task.get("results"),
                errors=task.get("errors"),
                created_at=task.get("created_at"),
                started_at=task.get("started_at"),
                completed_at=task.get("completed_at")
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.post("/batch/cancel/{batch_id}", response_model=BatchGraphBuildCancelResponse)
async def cancel_batch_build(batch_id: str):
    """
    取消批量构建任务

    取消指定批次ID的构建任务（仅对正在等待或处理中的任务有效）。
    """
    try:
        if batch_id not in _batch_build_tasks:
            raise HTTPException(status_code=404, detail=f"未找到批次ID: {batch_id}")
        
        task = _batch_build_tasks[batch_id]
        current_status = task.get("status", "unknown")
        
        # 只能取消等待中或处理中的任务
        if current_status not in ["pending", "processing"]:
            return BatchGraphBuildCancelResponse(
                success=False,
                data=BatchGraphBuildCancelData(
                    batch_id=batch_id,
                    status=current_status,
                    message=f"任务状态为 {current_status}，无法取消"
                )
            )
        
        # 更新任务状态为已取消
        task.update({
            "status": "cancelled",
            "completed_at": datetime.now().isoformat(),
            "current_message": "任务已取消"
        })
        
        return BatchGraphBuildCancelResponse(
            success=True,
            data=BatchGraphBuildCancelData(
                batch_id=batch_id,
                status="cancelled",
                message="任务已成功取消"
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


# ==================== 关系管理API ====================

@router.get("/relationships")
async def get_relationships(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    filter: Optional[str] = Query("all", description="过滤条件: all, active, inactive"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    relation_type: Optional[str] = Query(None, description="关系类型"),
    source_entity_type: Optional[str] = Query(None, description="源实体类型"),
    target_entity_type: Optional[str] = Query(None, description="目标实体类型"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="最小置信度"),
    max_confidence: Optional[float] = Query(None, ge=0, le=1, description="最大置信度"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取关系列表
    
    支持按知识库、关系类型、实体类型、置信度范围、时间范围等条件筛选
    """
    try:
        from app.modules.knowledge.models.knowledge_document import EntityRelationship, DocumentEntity, KnowledgeDocument
        from sqlalchemy import and_, or_
        
        # 构建查询 - 同时加载关联的实体信息
        query = db.query(EntityRelationship, DocumentEntity).join(
            DocumentEntity,
            EntityRelationship.source_id == DocumentEntity.id
        )
        
        # 如果指定了知识库ID，添加过滤条件
        if knowledge_base_id:
            query = query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        
        # 如果提供了关系类型，添加过滤
        if relation_type:
            query = query.filter(EntityRelationship.relationship_type == relation_type)
        
        # 如果提供了关键词，搜索源实体文本
        if keyword:
            query = query.filter(
                or_(
                    DocumentEntity.entity_text.contains(keyword),
                    EntityRelationship.relationship_type.contains(keyword)
                )
            )
        
        # 置信度范围过滤
        if min_confidence is not None:
            query = query.filter(EntityRelationship.confidence >= min_confidence)
        if max_confidence is not None:
            query = query.filter(EntityRelationship.confidence <= max_confidence)
        
        # 时间范围过滤
        if start_date:
            from datetime import datetime
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(EntityRelationship.created_at >= start)
            except ValueError:
                pass  # 忽略无效的日期格式
        if end_date:
            from datetime import datetime
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(EntityRelationship.created_at <= end)
            except ValueError:
                pass  # 忽略无效的日期格式
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        results = query.offset(skip).limit(limit).all()
        
        # 格式化结果
        relationship_list = []
        for rel, source_entity in results:
            # 获取目标实体信息
            target_entity = db.query(DocumentEntity).filter(DocumentEntity.id == rel.target_id).first()
            target_entity_text = target_entity.entity_text if target_entity else ""
            
            relationship_list.append({
                "id": rel.id,
                "sourceEntityId": rel.source_id,
                "sourceEntity": source_entity.entity_text if source_entity else "",
                "sourceEntityType": source_entity.entity_type if source_entity else "",
                "targetEntityId": rel.target_id,
                "targetEntity": target_entity_text,
                "targetEntityType": target_entity.entity_type if target_entity else "",
                "relationType": rel.relationship_type,
                "relationTypeId": rel.relationship_type,
                "confidence": rel.confidence or 1.0,
                "documentId": rel.document_id,
                "status": "active",
                "createdAt": rel.created_at.isoformat() if rel.created_at else None
            })
        
        return {
            "data": relationship_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        import traceback
        print(f"获取关系列表错误: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取关系列表失败: {str(e)}")


@router.get("/relation-types")
async def get_relation_types(
    db: Session = Depends(get_db)
):
    """获取所有关系类型
    
    返回系统中存在的所有关系类型列表
    """
    try:
        from app.modules.knowledge.models.knowledge_document import EntityRelationship
        from sqlalchemy import func
        
        # 查询所有不同的关系类型
        relation_types = db.query(
            EntityRelationship.relationship_type,
            func.count(EntityRelationship.id).label('count')
        ).group_by(EntityRelationship.relationship_type).all()
        
        # 格式化结果
        type_list = []
        for rel_type, count in relation_types:
            if rel_type:  # 排除空值
                type_list.append({
                    "id": rel_type,
                    "name": rel_type,
                    "count": count
                })
        
        return {
            "success": True,
            "data": type_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关系类型失败: {str(e)}")


@router.post("/relation-types")
async def add_relation_type(
    data: dict,
    db: Session = Depends(get_db)
):
    """添加关系类型
    
    注意：关系类型会在创建关系时自动添加，此端点主要用于兼容性
    """
    try:
        relation_type = data.get('name')
        if not relation_type:
            raise HTTPException(status_code=400, detail="关系类型名称不能为空")
        
        return {
            "success": True,
            "message": f"关系类型 '{relation_type}' 已添加",
            "data": {
                "id": relation_type,
                "name": relation_type,
                "count": 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加关系类型失败: {str(e)}")


@router.put("/relation-types/{relation_type}")
async def update_relation_type(
    relation_type: str,
    data: dict,
    db: Session = Depends(get_db)
):
    """更新关系类型
    
    注意：关系类型是关系的属性，此端点主要用于兼容性
    """
    try:
        new_name = data.get('name', relation_type)
        
        return {
            "success": True,
            "message": f"关系类型 '{relation_type}' 已更新为 '{new_name}'",
            "data": {
                "id": new_name,
                "name": new_name,
                "count": 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新关系类型失败: {str(e)}")


@router.delete("/relation-types/{relation_type}")
async def delete_relation_type(
    relation_type: str,
    db: Session = Depends(get_db)
):
    """删除关系类型
    
    从所有表中删除指定的关系类型
    """
    try:
        from app.modules.knowledge.models.knowledge_document import (
            EntityRelationship, KBRelationship, GlobalRelationship
        )
        
        # 计算删除前的数量
        before_counts = {
            "entity_relationships": db.query(EntityRelationship).filter(
                EntityRelationship.relationship_type == relation_type
            ).count(),
            "kb_relationships": db.query(KBRelationship).filter(
                KBRelationship.relationship_type == relation_type
            ).count(),
            "global_relationships": db.query(GlobalRelationship).filter(
                GlobalRelationship.relationship_type == relation_type
            ).count()
        }
        
        # 删除文档级关系
        db.query(EntityRelationship).filter(
            EntityRelationship.relationship_type == relation_type
        ).delete()
        
        # 删除知识库级关系
        db.query(KBRelationship).filter(
            KBRelationship.relationship_type == relation_type
        ).delete()
        
        # 删除全局级关系
        db.query(GlobalRelationship).filter(
            GlobalRelationship.relationship_type == relation_type
        ).delete()
        
        db.commit()
        
        # 计算删除后的数量（应为0）
        after_counts = {
            "entity_relationships": db.query(EntityRelationship).filter(
                EntityRelationship.relationship_type == relation_type
            ).count(),
            "kb_relationships": db.query(KBRelationship).filter(
                KBRelationship.relationship_type == relation_type
            ).count(),
            "global_relationships": db.query(GlobalRelationship).filter(
                GlobalRelationship.relationship_type == relation_type
            ).count()
        }
        
        return {
            "success": True,
            "message": f"成功删除关系类型 '{relation_type}'",
            "data": {
                "deleted_type": relation_type,
                "deleted_counts": before_counts,
                "remaining_counts": after_counts
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除关系类型失败: {str(e)}")


# ==================== 知识图谱数据清理API ====================

class ClearGraphDataRequest(BaseModel):
    """清理知识图谱数据请求"""
    level: str = "all"  # 清理级别: all, document, kb, global
    knowledge_base_id: Optional[int] = None  # 指定知识库ID（可选）
    document_id: Optional[int] = None  # 指定文档ID（可选）
    confirm: bool = False  # 确认删除


class ClearGraphDataResponse(BaseModel):
    """清理知识图谱数据响应"""
    success: bool
    message: str
    data: Dict[str, Any]


@router.post("/clear-data", response_model=ClearGraphDataResponse)
async def clear_knowledge_graph_data(
    request: ClearGraphDataRequest,
    db: Session = Depends(get_db)
):
    """
    清理知识图谱数据
    
    根据指定的级别清理实体和关系数据：
    - all: 清理所有层级的数据
    - document: 仅清理文档级数据
    - kb: 清理知识库级和文档级数据
    - global: 仅清理全局级数据
    
    可以指定knowledge_base_id或document_id进行精确清理
    """
    try:
        from sqlalchemy import text
        from app.modules.knowledge.models.knowledge_document import (
            DocumentEntity, EntityRelationship, KBEntity, KBRelationship,
            GlobalEntity, GlobalRelationship, KnowledgeDocument
        )
        
        if not request.confirm:
            # 仅统计将要删除的数据，不实际执行
            stats = {}
            
            if request.level == "all" or request.level == "document":
                # 统计文档级数据
                entity_query = db.query(DocumentEntity)
                rel_query = db.query(EntityRelationship)
                
                if request.document_id:
                    entity_query = entity_query.filter(DocumentEntity.document_id == request.document_id)
                    rel_query = rel_query.filter(EntityRelationship.document_id == request.document_id)
                elif request.knowledge_base_id:
                    entity_query = entity_query.join(KnowledgeDocument).filter(
                        KnowledgeDocument.knowledge_base_id == request.knowledge_base_id
                    )
                    rel_query = rel_query.join(KnowledgeDocument).filter(
                        KnowledgeDocument.knowledge_base_id == request.knowledge_base_id
                    )
                
                stats['document_entities'] = entity_query.count()
                stats['document_relationships'] = rel_query.count()
            
            if request.level == "all" or request.level == "kb":
                # 统计知识库级数据
                kb_entity_query = db.query(KBEntity)
                kb_rel_query = db.query(KBRelationship)
                
                if request.knowledge_base_id:
                    kb_entity_query = kb_entity_query.filter(KBEntity.knowledge_base_id == request.knowledge_base_id)
                    kb_rel_query = kb_rel_query.filter(KBRelationship.knowledge_base_id == request.knowledge_base_id)
                
                stats['kb_entities'] = kb_entity_query.count()
                stats['kb_relationships'] = kb_rel_query.count()
            
            if request.level == "all" or request.level == "global":
                # 统计全局级数据
                stats['global_entities'] = db.query(GlobalEntity).count()
                stats['global_relationships'] = db.query(GlobalRelationship).count()
            
            total = sum(stats.values())
            
            return ClearGraphDataResponse(
                success=True,
                message=f"将要删除 {total} 条数据。请设置 confirm=true 确认删除。",
                data={
                    "preview": True,
                    "level": request.level,
                    "stats": stats,
                    "total": total
                }
            )
        
        # 执行删除
        deleted_counts = {}
        
        if request.level == "all" or request.level == "global":
            # 清理全局级数据
            result = db.execute(text("DELETE FROM global_relationships"))
            deleted_counts['global_relationships'] = result.rowcount
            
            result = db.execute(text("DELETE FROM global_entities"))
            deleted_counts['global_entities'] = result.rowcount
        
        if request.level == "all" or request.level == "kb":
            # 清理知识库级数据
            if request.knowledge_base_id:
                result = db.execute(text(
                    f"DELETE FROM kb_relationships WHERE knowledge_base_id = {request.knowledge_base_id}"
                ))
                deleted_counts['kb_relationships'] = result.rowcount
                
                result = db.execute(text(
                    f"DELETE FROM kb_entities WHERE knowledge_base_id = {request.knowledge_base_id}"
                ))
                deleted_counts['kb_entities'] = result.rowcount
            else:
                result = db.execute(text("DELETE FROM kb_relationships"))
                deleted_counts['kb_relationships'] = result.rowcount
                
                result = db.execute(text("DELETE FROM kb_entities"))
                deleted_counts['kb_entities'] = result.rowcount
        
        if request.level == "all" or request.level == "document":
            # 清理文档级数据
            if request.document_id:
                result = db.execute(text(
                    f"DELETE FROM entity_relationships WHERE document_id = {request.document_id}"
                ))
                deleted_counts['document_relationships'] = result.rowcount
                
                result = db.execute(text(
                    f"DELETE FROM document_entities WHERE document_id = {request.document_id}"
                ))
                deleted_counts['document_entities'] = result.rowcount
                
                # 重置文档状态
                db.execute(text(
                    f"UPDATE knowledge_documents SET is_vectorized = 0 WHERE id = {request.document_id}"
                ))
                deleted_counts['documents_reset'] = 1
                
            elif request.knowledge_base_id:
                # 获取该知识库下的所有文档ID
                doc_ids_result = db.execute(text(
                    f"SELECT id FROM knowledge_documents WHERE knowledge_base_id = {request.knowledge_base_id}"
                )).fetchall()
                doc_ids = [row[0] for row in doc_ids_result]
                
                if doc_ids:
                    doc_ids_str = ','.join(map(str, doc_ids))
                    result = db.execute(text(
                        f"DELETE FROM entity_relationships WHERE document_id IN ({doc_ids_str})"
                    ))
                    deleted_counts['document_relationships'] = result.rowcount
                    
                    result = db.execute(text(
                        f"DELETE FROM document_entities WHERE document_id IN ({doc_ids_str})"
                    ))
                    deleted_counts['document_entities'] = result.rowcount
                
                # 重置文档状态
                result = db.execute(text(
                    f"UPDATE knowledge_documents SET is_vectorized = 0 WHERE knowledge_base_id = {request.knowledge_base_id}"
                ))
                deleted_counts['documents_reset'] = result.rowcount
                
            else:
                result = db.execute(text("DELETE FROM entity_relationships"))
                deleted_counts['document_relationships'] = result.rowcount
                
                result = db.execute(text("DELETE FROM document_entities"))
                deleted_counts['document_entities'] = result.rowcount
                
                # 重置所有文档状态
                result = db.execute(text(
                    "UPDATE knowledge_documents SET is_vectorized = 0 WHERE is_vectorized = 1"
                ))
                deleted_counts['documents_reset'] = result.rowcount
        
        db.commit()
        
        total_deleted = sum(v for k, v in deleted_counts.items() if k != 'documents_reset')
        
        return ClearGraphDataResponse(
            success=True,
            message=f"成功清理 {total_deleted} 条数据",
            data={
                "preview": False,
                "level": request.level,
                "deleted_counts": deleted_counts,
                "total_deleted": total_deleted
            }
        )
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"清理知识图谱数据错误: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"清理知识图谱数据失败: {str(e)}")