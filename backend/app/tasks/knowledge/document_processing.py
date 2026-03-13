#!/usr/bin/env python3
"""
文档处理Celery任务

提供异步文档处理功能，支持完整的7步处理流程
"""

import logging
from typing import Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# 尝试导入Celery，如果不可用则使用模拟实现
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery不可用，使用同步任务模式")
    
    # 模拟Celery的shared_task装饰器
    def shared_task(*args, **kwargs):
        def decorator(func):
            @wraps(func)
            def wrapper(*f_args, **f_kwargs):
                # 模拟self参数
                class MockTask:
                    request = type('Request', (), {'id': 'sync-task-id', 'retries': 0})()
                    max_retries = kwargs.get('max_retries', 3)
                    
                    def retry(self, exc=None, countdown=0):
                        raise exc
                
                return func(MockTask(), *f_args, **f_kwargs)
            
            # 添加delay方法
            def delay(*d_args, **d_kwargs):
                return wrapper(*d_args, **d_kwargs)
            
            wrapper.delay = delay
            return wrapper
        
        if args and callable(args[0]):
            return decorator(args[0])
        return decorator


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, document_id: int, knowledge_base_id: int, 
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    处理单个文档的Celery任务
    
    执行完整的7步处理流程：
    1. 文档解析
    2. 文本清理
    3. 智能分块
    4. 实体识别与关系提取
    5. 实体对齐
    6. 向量化处理
    7. 知识图谱构建
    
    Args:
        document_id: 文档ID
        knowledge_base_id: 知识库ID
        options: 处理选项，可包含：
            - skip_vectorization: 是否跳过向量化
            - skip_graph: 是否跳过知识图谱构建
            - chunk_size: 分块大小
            
    Returns:
        处理结果字典，包含：
        - success: 是否成功
        - document_id: 文档ID
        - entities_count: 实体数量
        - relationships_count: 关系数量
        - chunks_count: 分块数量
        - vectorization_rate: 向量化成功率
        - error: 错误信息（如果失败）
    """
    
    logger.info(f"[任务 {self.request.id}] 开始处理文档 {document_id}")
    
    try:
        # 导入必要的模块
        from app.core.database import SessionLocal
        from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
        from app.services.knowledge.core.document_processor import DocumentProcessor
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 获取文档信息
            document = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()
            
            if not document:
                logger.error(f"[任务 {self.request.id}] 文档不存在: {document_id}")
                return {
                    "success": False,
                    "document_id": document_id,
                    "error": f"文档不存在: {document_id}"
                }
            
            logger.info(f"[任务 {self.request.id}] 获取文档: {document.title}")
            
            # 更新文档状态为处理中
            document.status = "processing"
            db.commit()
            
            # 创建处理器
            processor = DocumentProcessor()
            
            # 执行处理
            result = processor.process_document(
                file_path=document.file_path,
                file_type=document.file_type,
                document_id=document_id,
                knowledge_base_id=knowledge_base_id,
                db=db
            )
            
            # 处理结果
            if result.get("success"):
                # 更新文档状态为已处理
                document.status = "processed"
                document.processing_result = {
                    "entities_count": len(result.get("entities", [])),
                    "relationships_count": len(result.get("relationships", [])),
                    "chunks_count": len(result.get("chunks", [])),
                    "vectorization_rate": result.get("vectorization_rate", 0),
                    "task_id": str(self.request.id)
                }
                db.commit()
                
                logger.info(f"[任务 {self.request.id}] 文档 {document_id} 处理成功")
                
                return {
                    "success": True,
                    "document_id": document_id,
                    "entities_count": len(result.get("entities", [])),
                    "relationships_count": len(result.get("relationships", [])),
                    "chunks_count": len(result.get("chunks", [])),
                    "vectorization_rate": result.get("vectorization_rate", 0),
                    "graph_data": result.get("graph_data")
                }
            else:
                # 更新文档状态为失败
                document.status = "failed"
                document.error_message = result.get("error", "未知错误")
                db.commit()
                
                logger.error(f"[任务 {self.request.id}] 文档 {document_id} 处理失败: {result.get('error')}")
                
                return {
                    "success": False,
                    "document_id": document_id,
                    "error": result.get("error", "处理失败")
                }
                
        except Exception as e:
            logger.error(f"[任务 {self.request.id}] 处理文档异常: {e}")
            db.rollback()
            
            # 更新文档状态为失败
            try:
                document = db.query(KnowledgeDocument).filter(
                    KnowledgeDocument.id == document_id
                ).first()
                if document:
                    document.status = "failed"
                    document.error_message = str(e)
                    db.commit()
            except Exception as update_error:
                logger.error(f"更新文档状态失败: {update_error}")
            
            # 重试逻辑
            if self.request.retries < self.max_retries:
                logger.info(f"[任务 {self.request.id}] 将在60秒后重试 ({self.request.retries + 1}/{self.max_retries})")
                raise self.retry(exc=e)
            
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e)
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[任务 {self.request.id}] 任务执行异常: {e}")
        return {
            "success": False,
            "document_id": document_id,
            "error": str(e)
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def batch_process_documents_task(self, document_ids: list, knowledge_base_id: int,
                                 options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    批量处理文档的Celery任务
    
    Args:
        document_ids: 文档ID列表
        knowledge_base_id: 知识库ID
        options: 处理选项
        
    Returns:
        批量处理结果
    """
    logger.info(f"[任务 {self.request.id}] 开始批量处理 {len(document_ids)} 个文档")
    
    results = {
        "total": len(document_ids),
        "successful": 0,
        "failed": 0,
        "documents": []
    }
    
    for doc_id in document_ids:
        try:
            # 调用单个文档处理任务
            result = process_document_task.delay(doc_id, knowledge_base_id, options)
            results["documents"].append({
                "document_id": doc_id,
                "task_id": result.id,
                "status": "submitted"
            })
            results["successful"] += 1
        except Exception as e:
            logger.error(f"提交文档 {doc_id} 处理任务失败: {e}")
            results["documents"].append({
                "document_id": doc_id,
                "status": "failed",
                "error": str(e)
            })
            results["failed"] += 1
    
    logger.info(f"[任务 {self.request.id}] 批量处理任务提交完成: "
                f"成功 {results['successful']}, 失败 {results['failed']}")
    
    return results


@shared_task
def cleanup_old_processing_results(days: int = 30) -> Dict[str, Any]:
    """
    清理旧的文档处理结果
    
    Args:
        days: 保留天数，默认30天
        
    Returns:
        清理结果
    """
    logger.info(f"开始清理 {days} 天前的文档处理结果")
    
    try:
        from app.core.database import SessionLocal
        from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 查找旧的已处理文档
            old_docs = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.status == "processed",
                KnowledgeDocument.updated_at < cutoff_date
            ).all()
            
            cleaned_count = 0
            for doc in old_docs:
                # 清理处理结果（保留记录，只清理详细结果）
                if doc.processing_result:
                    doc.processing_result = None
                    cleaned_count += 1
            
            db.commit()
            
            logger.info(f"清理完成，共清理 {cleaned_count} 个文档的处理结果")
            
            return {
                "success": True,
                "cleaned_count": cleaned_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"清理旧处理结果失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
