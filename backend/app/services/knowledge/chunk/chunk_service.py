"""
文档切片服务

提供文档重新切片功能
"""

import re
import json
import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ChunkService:
    """切片服务"""

    def __init__(self, db: Session):
        self.db = db

    def simple_chunking(self, text: str, max_chunk_size: int = 1500,
                        min_chunk_size: int = 300, overlap: int = 100) -> list:
        """
        基于规则的简单分块方法

        使用滑动窗口和句子边界检测，确保切片大小均匀且语义完整。

        Args:
            text: 输入文本
            max_chunk_size: 最大块大小（字符数）
            min_chunk_size: 最小块大小（字符数）
            overlap: 块之间的重叠大小（字符数）

        Returns:
            分块后的文本列表，每个元素包含text、start、end
        """
        if not text:
            return []

        if len(text) <= max_chunk_size:
            return [{'text': text, 'start': 0, 'end': len(text)}]

        chunks = []
        position = 0

        while position < len(text):
            # 计算当前块的结束位置
            end_pos = min(position + max_chunk_size, len(text))

            # 如果不是最后一块，尝试在句子边界处分割
            if end_pos < len(text):
                # 向前查找句子结束标记
                search_start = end_pos - 100  # 往回搜索100个字符
                if search_start < position:
                    search_start = position

                search_text = text[search_start:end_pos + 100]

                # 查找最后一个句子结束标记
                sentence_ends = []
                for i, char in enumerate(search_text):
                    if char in '.!?。！？':
                        actual_pos = search_start + i + 1
                        if actual_pos > position + min_chunk_size:
                            sentence_ends.append(actual_pos)

                if sentence_ends:
                    end_pos = sentence_ends[-1]

            # 提取块文本
            chunk_text = text[position:end_pos].strip()

            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'start': position,
                    'end': end_pos
                })

            # 移动位置，考虑重叠
            position = end_pos
            if overlap > 0 and position < len(text):
                position = max(position - overlap, position)

        return chunks

    def rechunk_document(self, document_id: int, max_chunk_size: int = 1500,
                         min_chunk_size: int = 300, overlap: int = 100) -> dict:
        """
        重新切片文档

        Args:
            document_id: 文档ID
            max_chunk_size: 最大切片大小
            min_chunk_size: 最小切片大小
            overlap: 重叠大小

        Returns:
            操作结果
        """
        try:
            # 1. 获取文档内容
            result = self.db.execute(text("""
                SELECT id, content, title
                FROM knowledge_documents
                WHERE id = :doc_id
            """), {"doc_id": document_id})
            doc = result.fetchone()

            if not doc:
                return {"error": f"未找到文档 ID {document_id}"}

            content = doc.content
            logger.info(f"重新切片文档 {document_id}: {doc.title}, 内容长度 {len(content)}")

            # 2. 获取旧切片数量
            result = self.db.execute(text("""
                SELECT COUNT(*) as count
                FROM document_chunks
                WHERE document_id = :doc_id
            """), {"doc_id": document_id})
            old_chunks = result.fetchone().count

            # 3. 删除旧实体
            result = self.db.execute(text("""
                DELETE FROM chunk_entities
                WHERE document_id = :doc_id
            """), {"doc_id": document_id})
            old_entities_deleted = result.rowcount
            logger.info(f"删除了 {old_entities_deleted} 个旧实体")

            # 4. 删除旧切片
            result = self.db.execute(text("""
                DELETE FROM document_chunks
                WHERE document_id = :doc_id
            """), {"doc_id": document_id})
            deleted_chunks = result.rowcount
            logger.info(f"删除了 {deleted_chunks} 个旧切片")

            # 5. 重新切片
            chunks = self.simple_chunking(content, max_chunk_size, min_chunk_size, overlap)
            logger.info(f"生成了 {len(chunks)} 个新切片")

            # 6. 保存新切片
            now = datetime.now().isoformat()
            for i, chunk_data in enumerate(chunks):
                chunk_text = chunk_data['text']
                start_pos = chunk_data['start']
                end_pos = chunk_data['end']

                # 准备元数据
                metadata = json.dumps({
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split()),
                    'paragraph_count': chunk_text.count('\n\n') + 1
                })

                self.db.execute(text("""
                    INSERT INTO document_chunks
                    (document_id, chunk_index, chunk_text, start_pos, end_pos,
                     total_chunks, is_vectorized, created_at, chunk_metadata)
                    VALUES (:doc_id, :index, :text, :start_pos, :end_pos,
                            :total_chunks, 0, :created_at, :metadata)
                """), {
                    "doc_id": document_id,
                    "index": i,
                    "text": chunk_text,
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "total_chunks": len(chunks),
                    "created_at": now,
                    "metadata": metadata
                })

            # 7. 更新文档信息
            self.db.execute(text("""
                UPDATE knowledge_documents
                SET updated_at = :updated_at
                WHERE id = :doc_id
            """), {
                "updated_at": now,
                "doc_id": document_id
            })

            self.db.commit()

            # 8. 计算统计信息
            sizes = [len(c['text']) for c in chunks]
            result = {
                "document_id": document_id,
                "old_chunks": old_chunks,
                "new_chunks": len(chunks),
                "old_entities_deleted": old_entities_deleted,
                "avg_chunk_size": sum(sizes) // len(sizes) if chunks else 0,
                "min_chunk_size": min(sizes) if chunks else 0,
                "max_chunk_size": max(sizes) if chunks else 0
            }

            logger.info(f"重新切片完成: {result}")
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"重新切片失败: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
