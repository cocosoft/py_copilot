"""
批量知识图谱构建服务

提供批量文档的知识图谱构建功能，支持并发控制和进度追踪。
参考向量化流程，实现高效的批量构建。
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time
from enum import Enum

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class BatchBuildStatus(Enum):
    """批量构建状态"""
    PENDING = "pending"           # 等待处理
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    PARTIAL = "partial"           # 部分成功


@dataclass
class DocumentBuildTask:
    """文档构建任务"""
    document_id: int
    document_name: str
    knowledge_base_id: int
    status: BatchBuildStatus = BatchBuildStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class BatchBuildResult:
    """批量构建结果"""
    batch_id: str
    status: BatchBuildStatus
    total_documents: int
    completed_count: int
    failed_count: int
    skipped_count: int
    tasks: List[DocumentBuildTask]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_entities: int = 0
    total_relationships: int = 0
    processing_time: float = 0.0


class BatchGraphBuilder:
    """批量知识图谱构建器
    
    功能：
    1. 批量构建多个文档的知识图谱
    2. 并发控制，避免系统资源耗尽
    3. 进度追踪和回调
    4. 错误处理和重试机制
    5. 支持按知识库批量构建
    """
    
    def __init__(self, max_concurrent: int = 3, batch_size: int = 10):
        """
        初始化批量构建器
        
        Args:
            max_concurrent: 最大并发处理文档数
            batch_size: 每批处理的文档数量
        """
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.knowledge_graph_service = KnowledgeGraphService()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        
        logger.info(f"批量知识图谱构建器初始化完成，最大并发: {max_concurrent}, 批大小: {batch_size}")
    
    async def build_graphs_batch(
        self,
        document_ids: List[int],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        db: Session = None
    ) -> BatchBuildResult:
        """
        批量构建知识图谱
        
        Args:
            document_ids: 文档ID列表
            progress_callback: 进度回调函数，接收(current, total, message)参数
            db: 数据库会话
            
        Returns:
            批量构建结果
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"开始批量构建知识图谱，批次ID: {batch_id}, 文档数: {len(document_ids)}")
        
        # 创建任务列表
        tasks = await self._create_tasks(document_ids, db)
        total = len(tasks)
        
        if progress_callback:
            progress_callback(0, total, f"准备处理 {total} 个文档...")
        
        # 分批处理
        completed_count = 0
        failed_count = 0
        skipped_count = 0
        total_entities = 0
        total_relationships = 0
        
        for i in range(0, total, self.batch_size):
            batch = tasks[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size
            
            logger.info(f"处理第 {batch_num}/{total_batches} 批，共 {len(batch)} 个文档")
            
            if progress_callback:
                progress_callback(
                    completed_count + failed_count + skipped_count,
                    total,
                    f"处理第 {batch_num}/{total_batches} 批文档..."
                )
            
            # 并发处理批次内的文档
            batch_tasks = []
            for task in batch:
                task_func = self._process_single_document(task, db)
                batch_tasks.append(task_func)
            
            # 等待批次完成
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 统计结果
            for task, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    task.status = BatchBuildStatus.FAILED
                    task.error_message = str(result)
                    failed_count += 1
                    logger.error(f"文档 {task.document_id} 构建失败: {result}")
                elif result and result.get('success'):
                    task.status = BatchBuildStatus.COMPLETED
                    task.result = result
                    completed_count += 1
                    total_entities += result.get('nodes_count', 0)
                    total_relationships += result.get('edges_count', 0)
                    logger.info(f"文档 {task.document_id} 构建成功: {result.get('nodes_count', 0)} 个实体")
                else:
                    task.status = BatchBuildStatus.FAILED
                    task.error_message = result.get('error', '未知错误') if result else '无结果'
                    failed_count += 1
                    logger.warning(f"文档 {task.document_id} 构建失败: {task.error_message}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 确定整体状态
        if failed_count == 0:
            status = BatchBuildStatus.COMPLETED
        elif completed_count == 0:
            status = BatchBuildStatus.FAILED
        else:
            status = BatchBuildStatus.PARTIAL
        
        result = BatchBuildResult(
            batch_id=batch_id,
            status=status,
            total_documents=total,
            completed_count=completed_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            tasks=tasks,
            start_time=start_time,
            end_time=end_time,
            total_entities=total_entities,
            total_relationships=total_relationships,
            processing_time=processing_time
        )
        
        logger.info(
            f"批量构建完成: 成功 {completed_count}/{total}, 失败 {failed_count}, "
            f"实体 {total_entities}, 关系 {total_relationships}, 耗时 {processing_time:.2f}s"
        )
        
        if progress_callback:
            progress_callback(total, total, f"批量构建完成: 成功 {completed_count}, 失败 {failed_count}")
        
        return result
    
    async def build_graphs_by_knowledge_base(
        self,
        knowledge_base_id: int,
        document_ids: Optional[List[int]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        db: Session = None
    ) -> BatchBuildResult:
        """
        按知识库批量构建知识图谱
        
        Args:
            knowledge_base_id: 知识库ID
            document_ids: 指定文档ID列表（可选，默认构建知识库下所有文档）
            progress_callback: 进度回调函数
            db: 数据库会话
            
        Returns:
            批量构建结果
        """
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True
        
        try:
            # 如果没有指定文档ID，获取知识库下所有文档
            if document_ids is None:
                documents = db.query(KnowledgeDocument).filter(
                    KnowledgeDocument.knowledge_base_id == knowledge_base_id,
                    KnowledgeDocument.is_deleted == False
                ).all()
                document_ids = [doc.id for doc in documents]
                logger.info(f"知识库 {knowledge_base_id} 共有 {len(document_ids)} 个文档待构建")
            
            if not document_ids:
                logger.warning(f"知识库 {knowledge_base_id} 没有可构建的文档")
                return BatchBuildResult(
                    batch_id=f"kb_{knowledge_base_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    status=BatchBuildStatus.COMPLETED,
                    total_documents=0,
                    completed_count=0,
                    failed_count=0,
                    skipped_count=0,
                    tasks=[],
                    start_time=datetime.now(),
                    end_time=datetime.now()
                )
            
            return await self.build_graphs_batch(document_ids, progress_callback, db)
            
        finally:
            if should_close_db:
                db.close()
    
    async def _create_tasks(
        self,
        document_ids: List[int],
        db: Session
    ) -> List[DocumentBuildTask]:
        """创建文档构建任务列表"""
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True
        
        try:
            tasks = []
            for doc_id in document_ids:
                # 查询文档信息
                document = db.query(KnowledgeDocument).filter(
                    KnowledgeDocument.id == doc_id,
                    KnowledgeDocument.is_deleted == False
                ).first()
                
                if document:
                    task = DocumentBuildTask(
                        document_id=doc_id,
                        document_name=document.document_name or f"文档_{doc_id}",
                        knowledge_base_id=document.knowledge_base_id
                    )
                    tasks.append(task)
                else:
                    logger.warning(f"文档 {doc_id} 不存在或已删除，跳过")
            
            return tasks
            
        finally:
            if should_close_db:
                db.close()
    
    async def _process_single_document(
        self,
        task: DocumentBuildTask,
        db: Session
    ) -> Dict[str, Any]:
        """处理单个文档"""
        async with self._semaphore:
            task.started_at = datetime.now()
            task.status = BatchBuildStatus.PROCESSING
            
            logger.info(f"开始构建文档 {task.document_id} 的知识图谱")
            
            try:
                # 使用线程池执行同步的数据库操作
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor,
                    self._build_graph_sync,
                    task.document_id,
                    db
                )
                
                task.completed_at = datetime.now()
                return result
                
            except Exception as e:
                task.completed_at = datetime.now()
                task.status = BatchBuildStatus.FAILED
                task.error_message = str(e)
                logger.error(f"文档 {task.document_id} 构建失败: {e}")
                raise
    
    def _build_graph_sync(self, document_id: int, db: Session) -> Dict[str, Any]:
        """同步构建知识图谱（在线程池中执行）"""
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True
        
        try:
            result = self.knowledge_graph_service.build_document_graph(db, document_id)
            return result
        finally:
            if should_close_db:
                db.close()
    
    def get_batch_status(self, batch_result: BatchBuildResult) -> Dict[str, Any]:
        """获取批量构建状态信息"""
        return {
            "batch_id": batch_result.batch_id,
            "status": batch_result.status.value,
            "total_documents": batch_result.total_documents,
            "completed_count": batch_result.completed_count,
            "failed_count": batch_result.failed_count,
            "skipped_count": batch_result.skipped_count,
            "total_entities": batch_result.total_entities,
            "total_relationships": batch_result.total_relationships,
            "processing_time": batch_result.processing_time,
            "start_time": batch_result.start_time.isoformat() if batch_result.start_time else None,
            "end_time": batch_result.end_time.isoformat() if batch_result.end_time else None,
            "progress_percentage": round(
                (batch_result.completed_count + batch_result.failed_count) / batch_result.total_documents * 100, 2
            ) if batch_result.total_documents > 0 else 0
        }
    
    def get_failed_tasks(self, batch_result: BatchBuildResult) -> List[Dict[str, Any]]:
        """获取失败的任务列表"""
        failed_tasks = [
            {
                "document_id": task.document_id,
                "document_name": task.document_name,
                "error_message": task.error_message,
                "retry_count": task.retry_count
            }
            for task in batch_result.tasks
            if task.status == BatchBuildStatus.FAILED
        ]
        return failed_tasks
