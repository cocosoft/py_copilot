#!/usr/bin/env python3
"""
片段级实体识别任务服务

支持异步处理大文档的实体提取，提供任务状态查询功能
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_document import DocumentChunk, ChunkEntity
from app.services.knowledge.extraction.llm_extractor import LLMEntityExtractor

logger = logging.getLogger(__name__)


class ChunkEntityTaskService:
    """片段级实体识别任务服务"""
    
    # 任务存储（使用类变量作为简单内存存储）
    _tasks: Dict[str, Dict[str, Any]] = {}
    _executor = ThreadPoolExecutor(max_workers=2)
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, document_id: int, max_workers: int = 4) -> str:
        """
        创建新的实体提取任务
        
        Args:
            document_id: 文档ID
            max_workers: 并行工作线程数
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        # 获取文档信息
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        total_chunks = len(chunks)
        
        task = {
            "task_id": task_id,
            "document_id": document_id,
            "status": "pending",  # pending, processing, completed, failed
            "progress": 0,
            "total_chunks": total_chunks,
            "completed_chunks": 0,
            "failed_chunks": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message": "等待开始处理",
            "error": None,
            "result": None
        }
        
        ChunkEntityTaskService._tasks[task_id] = task
        
        # 启动异步处理
        asyncio.create_task(self._process_task_async(task_id, document_id, max_workers))
        
        logger.info(f"创建实体提取任务: {task_id}, 文档: {document_id}, 片段数: {total_chunks}")
        
        return task_id
    
    async def _process_task_async(self, task_id: str, document_id: int, max_workers: int):
        """
        异步处理任务
        
        Args:
            task_id: 任务ID
            document_id: 文档ID
            max_workers: 并行工作线程数
        """
        task = ChunkEntityTaskService._tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        # 更新任务状态
        task["status"] = "processing"
        task["message"] = "正在处理片段..."
        task["updated_at"] = datetime.now().isoformat()
        
        try:
            # 在新线程中执行同步的数据库操作
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._process_document_chunks,
                task_id,
                document_id,
                max_workers
            )
            
            # 更新任务完成状态
            task["status"] = "completed"
            task["progress"] = 100
            task["completed_chunks"] = result["completed"]
            task["failed_chunks"] = result["failed"]
            task["message"] = f"处理完成: 成功 {result['completed']}, 失败 {result['failed']}"
            task["result"] = result
            task["updated_at"] = datetime.now().isoformat()
            
            logger.info(f"任务完成: {task_id}, 结果: {result}")
            
        except Exception as e:
            logger.error(f"任务处理失败: {task_id}, 错误: {e}")
            task["status"] = "failed"
            task["error"] = str(e)
            task["message"] = f"处理失败: {str(e)}"
            task["updated_at"] = datetime.now().isoformat()
    
    def _extract_single_chunk_sync(self, chunk_id: int, knowledge_base_id: int, task_id: str) -> Dict[str, Any]:
        """
        同步提取单个片段的实体（用于线程池）
        
        Args:
            chunk_id: 片段ID
            knowledge_base_id: 知识库ID
            task_id: 任务ID
            
        Returns:
            提取结果
        """
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
        
        # 在新线程中创建新的数据库会话
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine('sqlite:///py_copilot.db')
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 获取片段
            chunk = db.query(DocumentChunk).filter(
                DocumentChunk.id == chunk_id
            ).first()
            
            if not chunk:
                return {"chunk_id": chunk_id, "entity_count": 0, "error": "片段不存在"}
            
            # 使用LLM提取实体
            from app.services.knowledge.extraction.llm_extractor import LLMEntityExtractor
            
            extractor = LLMEntityExtractor(
                db,
                knowledge_base_id=knowledge_base_id or chunk.document.knowledge_base_id
            )
            
            # 在新线程中运行异步代码
            import asyncio
            import concurrent.futures
            
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(extractor.extract_entities(chunk.chunk_text))
                finally:
                    loop.close()
            
            # 在子线程中执行异步代码
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as inner_executor:
                future = inner_executor.submit(run_async)
                entities = future.result(timeout=600)  # 10分钟超时
            
            # 保存为ChunkEntity
            chunk_entities = []
            for entity in entities:
                chunk_entity = ChunkEntity(
                    chunk_id=chunk_id,
                    document_id=chunk.document_id,
                    entity_text=entity.get("text", ""),
                    entity_type=entity.get("type", "UNKNOWN"),
                    start_pos=entity.get("start_pos", 0),
                    end_pos=entity.get("end_pos", 0),
                    confidence=entity.get("confidence", 0.8),
                    context=entity.get("context", "")
                )
                db.add(chunk_entity)
                chunk_entities.append(chunk_entity)
            
            db.commit()
            
            return {
                "chunk_id": chunk_id,
                "entity_count": len(chunk_entities),
                "entities": [{"text": e.entity_text, "type": e.entity_type} for e in chunk_entities]
            }
            
        except concurrent.futures.TimeoutError:
            db.rollback()
            logger.error(f"[任务 {task_id}] 提取片段 {chunk_id} 实体超时")
            return {"chunk_id": chunk_id, "entity_count": 0, "error": "处理超时"}
        except Exception as e:
            db.rollback()
            logger.error(f"[任务 {task_id}] 提取片段 {chunk_id} 实体失败: {e}")
            return {"chunk_id": chunk_id, "entity_count": 0, "error": str(e)}
        finally:
            db.close()
    
    def _process_document_chunks(self, task_id: str, document_id: int, max_workers: int) -> Dict[str, Any]:
        """
        处理文档的所有片段（同步方法，在线程池中执行）
        
        Args:
            task_id: 任务ID
            document_id: 文档ID
            max_workers: 并行工作线程数
            
        Returns:
            处理结果
        """
        import sys
        sys.path.insert(0, '.')
        
        # 在新线程中创建新的数据库会话
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine('sqlite:///py_copilot.db')
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 获取文档的所有片段
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()
            
            if not chunks:
                return {"document_id": document_id, "total_chunks": 0, "completed": 0, "failed": 0}
            
            total = len(chunks)
            completed = 0
            failed = 0
            
            logger.info(f"[任务 {task_id}] 开始处理文档 {document_id} 的 {total} 个片段")
            
            # 获取知识库ID
            kb_id = None
            if chunks:
                kb_id = chunks[0].document.knowledge_base_id if hasattr(chunks[0], 'document') else None
            
            # 使用线程池并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_chunk = {
                    executor.submit(
                        self._extract_single_chunk_sync, 
                        chunk.id, 
                        kb_id,
                        task_id
                    ): chunk
                    for chunk in chunks
                }
                
                # 处理结果
                for future in future_to_chunk:
                    chunk = future_to_chunk[future]
                    try:
                        result = future.result()
                        if "error" in result:
                            failed += 1
                            logger.warning(f"[任务 {task_id}] 片段 {chunk.id} 处理失败: {result['error']}")
                        else:
                            completed += 1
                    except Exception as e:
                        failed += 1
                        logger.error(f"[任务 {task_id}] 片段 {chunk.id} 处理异常: {e}")
                    
                    # 更新进度
                    progress = int((completed + failed) / total * 100)
                    task = ChunkEntityTaskService._tasks.get(task_id)
                    if task:
                        task["progress"] = progress
                        task["completed_chunks"] = completed
                        task["failed_chunks"] = failed
                        task["message"] = f"处理中: {completed + failed}/{total} ({progress}%)"
                        task["updated_at"] = datetime.now().isoformat()
            
            logger.info(f"[任务 {task_id}] 文档 {document_id} 处理完成: 成功 {completed}, 失败 {failed}")
            
            return {
                "document_id": document_id,
                "total_chunks": total,
                "completed": completed,
                "failed": failed
            }
            
        finally:
            db.close()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        task = ChunkEntityTaskService._tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task["task_id"],
            "document_id": task["document_id"],
            "status": task["status"],
            "progress": task["progress"],
            "total_chunks": task["total_chunks"],
            "completed_chunks": task["completed_chunks"],
            "failed_chunks": task["failed_chunks"],
            "message": task["message"],
            "error": task["error"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"]
        }
    
    def list_tasks(self, document_id: Optional[int] = None) -> list:
        """
        列出任务
        
        Args:
            document_id: 可选的文档ID过滤
            
        Returns:
            任务列表
        """
        tasks = []
        for task in ChunkEntityTaskService._tasks.values():
            if document_id is None or task["document_id"] == document_id:
                tasks.append({
                    "task_id": task["task_id"],
                    "document_id": task["document_id"],
                    "status": task["status"],
                    "progress": task["progress"],
                    "message": task["message"],
                    "created_at": task["created_at"],
                    "updated_at": task["updated_at"]
                })
        
        # 按创建时间倒序
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        return tasks
