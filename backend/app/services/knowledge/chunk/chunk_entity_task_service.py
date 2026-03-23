#!/usr/bin/env python3
"""
片段级实体识别任务服务 - 简化版

支持异步处理大文档的实体提取，提供任务状态查询功能
"""

import asyncio
import logging
import uuid
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_document import DocumentChunk, ChunkEntity
from app.services.knowledge.extraction.llm_extractor import LLMEntityExtractor
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class ChunkEntityTaskService:
    """片段级实体识别任务服务"""
    
    # 任务存储（使用类变量作为简单内存存储）
    _tasks: Dict[str, Dict[str, Any]] = {}
    
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

        # 启动后台线程处理任务
        thread = threading.Thread(
            target=self._process_task_sync,
            args=(task_id, document_id, max_workers),
            daemon=True
        )
        thread.start()

        logger.info(f"创建实体提取任务: {task_id}, 文档: {document_id}, 片段数: {total_chunks}")

        return task_id
    
    def _process_task_sync(self, task_id: str, document_id: int, max_workers: int):
        """
        同步处理任务（在线程中运行）

        Args:
            task_id: 任务ID
            document_id: 文档ID
            max_workers: 并行工作线程数
        """
        import asyncio

        # 在线程中创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                self._process_task_async(task_id, document_id, max_workers)
            )
        finally:
            loop.close()

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

        # 创建独立的数据库会话
        db = SessionLocal()

        try:
            # 获取所有片段
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()

            if not chunks:
                task["status"] = "completed"
                task["progress"] = 100
                task["message"] = "文档没有片段"
                task["result"] = {"completed": 0, "failed": 0, "total_entities": 0}
                task["updated_at"] = datetime.now().isoformat()
                return

            # 获取知识库ID
            knowledge_base_id = None
            if chunks and hasattr(chunks[0], 'document') and chunks[0].document:
                knowledge_base_id = chunks[0].document.knowledge_base_id

            # 创建提取器
            extractor = LLMEntityExtractor(db, knowledge_base_id=knowledge_base_id)

            # 串行处理每个片段（避免线程问题）
            completed = 0
            failed = 0
            total_entities = 0

            for i, chunk in enumerate(chunks):
                try:
                    # 更新进度
                    progress = int((i / len(chunks)) * 100)
                    task["progress"] = progress
                    task["message"] = f"正在处理片段 {i+1}/{len(chunks)}..."
                    task["updated_at"] = datetime.now().isoformat()

                    # 提取实体
                    entities = await extractor.extract_entities(chunk.chunk_text)

                    # 保存实体到数据库
                    for entity in entities:
                        chunk_entity = ChunkEntity(
                            chunk_id=chunk.id,
                            document_id=document_id,
                            entity_text=entity.get("text", ""),
                            entity_type=entity.get("type", "UNKNOWN"),
                            start_pos=entity.get("start_pos", 0),
                            end_pos=entity.get("end_pos", 0),
                            confidence=entity.get("confidence", 0.8),
                            context=entity.get("context", "")
                        )
                        db.add(chunk_entity)

                    db.commit()
                    completed += 1
                    total_entities += len(entities)

                    logger.info(f"[任务 {task_id}] 片段 {chunk.id} 处理完成，提取 {len(entities)} 个实体")

                except Exception as e:
                    db.rollback()
                    failed += 1
                    logger.error(f"[任务 {task_id}] 处理片段 {chunk.id} 失败: {e}")

                # 每处理5个片段提交一次，避免事务过大
                if i % 5 == 0:
                    db.commit()

            # 最终提交
            db.commit()

            # 更新任务完成状态
            task["status"] = "completed"
            task["progress"] = 100
            task["completed_chunks"] = completed
            task["failed_chunks"] = failed
            task["message"] = f"处理完成: 成功 {completed}, 失败 {failed}"
            task["result"] = {
                "completed": completed,
                "failed": failed,
                "total_entities": total_entities
            }
            task["updated_at"] = datetime.now().isoformat()

            logger.info(f"任务完成: {task_id}, 成功: {completed}, 失败: {failed}, 实体数: {total_entities}")

        except Exception as e:
            db.rollback()
            logger.error(f"任务处理失败: {task_id}, 错误: {e}")
            task["status"] = "failed"
            task["error"] = str(e)
            task["message"] = f"处理失败: {str(e)}"
            task["updated_at"] = datetime.now().isoformat()
        finally:
            db.close()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态字典，如果任务不存在返回None
        """
        task = ChunkEntityTaskService._tasks.get(task_id)
        if task:
            return task.copy()
        return None
    
    def list_tasks(self, document_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            document_id: 可选的文档ID过滤
            
        Returns:
            任务列表
        """
        tasks = []
        for task in ChunkEntityTaskService._tasks.values():
            if document_id is None or task.get("document_id") == document_id:
                tasks.append(task.copy())
        return sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)
