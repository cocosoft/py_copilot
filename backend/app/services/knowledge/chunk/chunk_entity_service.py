"""
片段级实体识别服务

复用现有LLMEntityExtractor，实现片段级实体识别和并行处理
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_document import DocumentChunk, ChunkEntity
from app.services.knowledge.extraction.llm_extractor import LLMEntityExtractor

logger = logging.getLogger(__name__)


class ChunkEntityService:
    """片段级实体识别服务

    复用现有LLMEntityExtractor，实现片段级实体识别和并行处理
    """

    def __init__(self, db: Session):
        self.db = db

    def extract_chunk_entities(self, chunk_id: int,
                               knowledge_base_id: int = None) -> Dict[str, Any]:
        """
        对单个片段进行实体识别

        复用：LLMEntityExtractor.extract_entities()

        Args:
            chunk_id: 片段ID
            knowledge_base_id: 知识库ID（用于获取配置）

        Returns:
            {"chunk_id": int, "entity_count": int, "entities": List}
        """
        try:
            # 获取片段
            chunk = self.db.query(DocumentChunk).filter(
                DocumentChunk.id == chunk_id
            ).first()

            if not chunk:
                return {"chunk_id": chunk_id, "entity_count": 0, "error": "片段不存在"}

            # 复用现有LLM实体提取器
            extractor = LLMEntityExtractor(
                self.db,
                knowledge_base_id=knowledge_base_id or chunk.document.knowledge_base_id
            )

            # 提取实体（仅处理片段文本）
            # 修复：使用统一的异步工具方法，避免事件循环冲突
            from app.services.knowledge.utils.async_utils import run_async_safely
            entities = run_async_safely(extractor.extract_entities(chunk.chunk_text))

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
                self.db.add(chunk_entity)
                chunk_entities.append(chunk_entity)

            self.db.commit()

            logger.info(f"片段 {chunk_id} 实体识别完成: {len(chunk_entities)} 个实体")

            return {
                "chunk_id": chunk_id,
                "entity_count": len(chunk_entities),
                "entities": [{"id": e.id, "text": e.entity_text, "type": e.entity_type}
                            for e in chunk_entities]
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"片段 {chunk_id} 实体识别失败: {e}")
            return {"chunk_id": chunk_id, "entity_count": 0, "error": str(e)}

    def extract_document_entities_parallel(self, document_id: int,
                                          max_workers: int = 4,
                                          batch_size: int = 10) -> Dict[str, Any]:
        """
        并行处理文档的所有片段

        Args:
            document_id: 文档ID
            max_workers: 并行工作线程数
            batch_size: 每批处理的片段数

        Returns:
            {"document_id": int, "total_chunks": int, "completed": int, "failed": int}
        """
        # 获取文档的所有片段
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()

        if not chunks:
            return {"document_id": document_id, "total_chunks": 0, "completed": 0, "failed": 0}

        total = len(chunks)
        completed = 0
        failed = 0

        logger.info(f"开始并行处理文档 {document_id} 的 {total} 个片段")

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_chunk = {
                executor.submit(self.extract_chunk_entities, chunk.id): chunk
                for chunk in chunks
            }

            # 处理结果
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    if "error" in result:
                        failed += 1
                        logger.warning(f"片段 {chunk.id} 处理失败: {result['error']}")
                    else:
                        completed += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"片段 {chunk.id} 处理异常: {e}")

                # 记录进度
                if (completed + failed) % 10 == 0:
                    logger.info(f"文档 {document_id} 处理进度: {completed + failed}/{total}")

        logger.info(f"文档 {document_id} 处理完成: 成功 {completed}, 失败 {failed}")

        return {
            "document_id": document_id,
            "total_chunks": total,
            "completed": completed,
            "failed": failed
        }

    def get_chunk_entities(self, chunk_id: int) -> List[Dict[str, Any]]:
        """
        获取指定片段的所有实体

        Args:
            chunk_id: 片段ID

        Returns:
            实体列表
        """
        entities = self.db.query(ChunkEntity).filter(
            ChunkEntity.chunk_id == chunk_id
        ).all()

        return [
            {
                "id": e.id,
                "entity_text": e.entity_text,
                "entity_type": e.entity_type,
                "confidence": e.confidence,
                "start_pos": e.start_pos,
                "end_pos": e.end_pos,
                "context": e.context
            }
            for e in entities
        ]

    def get_document_chunk_entities(self, document_id: int) -> Dict[str, Any]:
        """
        获取文档的所有片段级实体

        Args:
            document_id: 文档ID

        Returns:
            {"document_id": int, "entities": List, "total": int}
        """
        entities = self.db.query(ChunkEntity).filter(
            ChunkEntity.document_id == document_id
        ).all()

        return {
            "document_id": document_id,
            "entities": [
                {
                    "id": e.id,
                    "chunk_id": e.chunk_id,
                    "entity_text": e.entity_text,
                    "entity_type": e.entity_type,
                    "confidence": e.confidence
                }
                for e in entities
            ],
            "total": len(entities)
        }
