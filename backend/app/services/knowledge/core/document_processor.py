import logging
import re
import gc
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.knowledge.processing_progress_service import processing_progress_service

logger = logging.getLogger(__name__)


def release_memory():
    """主动释放内存，删除大对象并强制垃圾回收
    
    该函数用于在文档处理完成后释放内存，避免内存持续增长
    """
    try:
        # 强制垃圾回收
        gc.collect()
        gc.collect()  # 第二次调用确保清理更彻底
        
        # 记录内存释放信息
        logger.info("内存释放完成")
    except Exception as e:
        logger.warning(f"内存释放时出错: {e}")


class DocumentProcessor:
    """文档处理核心模块，负责文档解析、分块、向量化

    处理流程（4步）：
    1. 文档解析
    2. 文本清理
    3. 智能分块
    4. 向量化处理

    注：实体识别、实体对齐、知识图谱构建已分离到独立服务
    """

    def __init__(self):
        # 使用现有的文档解析器
        from app.services.knowledge.core.document_parser import DocumentParser
        self.parser = DocumentParser()

        # 使用高级文本处理器（支持spacy）
        from app.services.knowledge.core.advanced_text_processor import AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()

        # 使用现有的ChromaService
        from app.services.knowledge.vectorization.chroma_service import ChromaService
        self.chroma_service = ChromaService()

        # 使用现有的检索服务
        from app.services.knowledge.retrieval.retrieval_service import RetrievalService
        self.retrieval_service = RetrievalService()

    def _simple_chunking(self, text: str, max_chunk_size: int = 1000,
                         min_chunk_size: int = 200, overlap: int = 50) -> List[str]:
        """基于规则的简单分块方法（高性能版本）

        使用段落和句子边界进行分块，避免LLM调用，大幅提升处理速度。

        Args:
            text: 输入文本
            max_chunk_size: 最大块大小（字符数）
            min_chunk_size: 最小块大小（字符数）
            overlap: 块之间的重叠大小（字符数）

        Returns:
            分块后的文本列表
        """
        if not text:
            return []

        if len(text) <= max_chunk_size:
            return [text]

        chunks = []

        # 首先按段落分割（优先在段落边界分割）
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        current_chunk = ""
        current_size = 0

        for paragraph in paragraphs:
            para_size = len(paragraph)

            # 如果当前段落本身就超过最大块大小，需要进一步分割
            if para_size > max_chunk_size:
                # 先保存当前块
                if current_chunk and current_size >= min_chunk_size:
                    chunks.append(current_chunk.strip())
                    # 保留重叠部分
                    if overlap > 0 and len(current_chunk) > overlap:
                        current_chunk = current_chunk[-overlap:]
                        current_size = len(current_chunk)
                    else:
                        current_chunk = ""
                        current_size = 0

                # 按句子分割这个长段落
                sentences = re.split(r'(?<=[.!?。！？])\s+', paragraph)
                sentences = [s.strip() for s in sentences if s.strip()]

                for sentence in sentences:
                    sent_size = len(sentence)

                    if current_size + sent_size <= max_chunk_size:
                        current_chunk += " " + sentence if current_chunk else sentence
                        current_size += sent_size
                    else:
                        # 保存当前块
                        if current_chunk and current_size >= min_chunk_size:
                            chunks.append(current_chunk.strip())
                            # 保留重叠部分
                            if overlap > 0 and len(current_chunk) > overlap:
                                current_chunk = current_chunk[-overlap:] + " " + sentence
                                current_size = overlap + sent_size
                            else:
                                current_chunk = sentence
                                current_size = sent_size
                        else:
                            current_chunk = sentence
                            current_size = sent_size
            else:
                # 正常段落处理
                if current_size + para_size <= max_chunk_size:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                    current_size += para_size + 2  # +2 for \n\n
                else:
                    # 保存当前块
                    if current_chunk and current_size >= min_chunk_size:
                        chunks.append(current_chunk.strip())
                        # 保留重叠部分
                        if overlap > 0 and len(current_chunk) > overlap:
                            current_chunk = current_chunk[-overlap:] + "\n\n" + paragraph
                            current_size = overlap + para_size + 2
                        else:
                            current_chunk = paragraph
                            current_size = para_size
                    else:
                        current_chunk = paragraph
                        current_size = para_size

        # 保存最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"基于规则的分块完成，生成 {len(chunks)} 个块")
        return chunks

    def process_document(self, file_path: str, file_type: str, document_id: int,
                        knowledge_base_id: Optional[int] = None, db: Session = None,
                        document_name: str = None) -> Dict[str, Any]:
        """文档向量化处理流程
        
        处理流程（4步）：
        1. 文档解析
        2. 文本清理
        3. 智能分块
        4. 向量化处理
        
        注：实体识别、实体对齐、知识图谱构建已分离到独立服务
        """

        # 初始化进度追踪
        doc_id_str = str(document_id)
        
        # 如果没有提供文档名称，从文件路径中提取
        if not document_name:
            import os
            document_name = os.path.basename(file_path)
        
        processing_progress_service.start_processing(doc_id_str, total_steps=4, document_name=document_name)

        try:
            # 1. 解析文档
            processing_progress_service.update_progress(
                doc_id_str, 1, "文档解析",
                "正在解析文档内容...",
                {"file_path": file_path}
            )
            raw_text = self.parser.parse_document(file_path)
            if not raw_text:
                raise ValueError(f"无法解析文档: {file_path}")

            logger.info(f"文档解析完成，内容长度: {len(raw_text)} 字符")

            # 2. 文本预处理与清理
            processing_progress_service.update_progress(
                doc_id_str, 2, "文本清理",
                "正在清理和预处理文本...",
                {"text_length": len(raw_text)}
            )
            cleaned_text = self.text_processor.clean_text(raw_text)

            # 3. 智能分块（使用高性能规则分块，避免LLM调用）
            processing_progress_service.update_progress(
                doc_id_str, 3, "智能分块",
                "正在进行语义分块...",
                {"cleaned_text_length": len(cleaned_text)}
            )
            # 使用基于规则的高性能分块方法，避免LLM调用耗时
            chunks = self._simple_chunking(cleaned_text, max_chunk_size=1000, min_chunk_size=200, overlap=50)
            logger.info(f"文档分块完成，共 {len(chunks)} 个块")
            
            # 4. 向量化处理 - 分批次批量处理优化版
            # 注：实体识别、实体对齐、知识图谱构建已分离到独立服务
            vector_results = []
            success_count = 0
            failed_chunks = []

            # 根据chunks数量决定批次大小
            # 增加批次大小以减少HTTP请求次数，提升处理速度
            total_chunks = len(chunks)
            if total_chunks <= 100:
                batch_size = total_chunks  # 小文件一次性处理
            elif total_chunks <= 500:
                batch_size = 100  # 中等文件每批100个
            else:
                batch_size = 100  # 大文件每批100个chunks

            total_batches = (total_chunks + batch_size - 1) // batch_size
            logger.info(f"开始分批次向量化处理: {total_chunks} 个块, 分成 {total_batches} 批, 每批 {batch_size} 个")

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, total_chunks)
                current_batch_chunks = chunks[start_idx:end_idx]

                # 更新进度（步骤6：向量化）
                processing_progress_service.update_progress(
                    doc_id_str, 6, "向量化处理",
                    f"正在处理第 {batch_idx + 1}/{total_batches} 批向量数据...",
                    {
                        "batch": batch_idx + 1,
                        "total_batches": total_batches,
                        "progress": f"{start_idx + 1}-{end_idx}/{total_chunks}"
                    }
                )

                # 准备当前批次数据
                batch_documents = []
                for i, chunk in enumerate(current_batch_chunks):
                    global_idx = start_idx + i
                    chunk_id = f"{document_id}_chunk_{global_idx}"
                    metadata = {
                        "document_id": document_id,
                        "knowledge_base_id": knowledge_base_id,
                        "chunk_index": global_idx,
                        "total_chunks": total_chunks,
                        "title": f"文档 {document_id} 第 {global_idx + 1} 块"
                    }
                    batch_documents.append({
                        "document_id": chunk_id,
                        "text": chunk,
                        "metadata": metadata
                    })

                # 批量添加当前批次到向量数据库
                logger.info(f"处理批次 {batch_idx + 1}/{total_batches}: {len(batch_documents)} 个块")
                batch_result = self.chroma_service.add_documents_batch(batch_documents)

                if batch_result.get("success"):
                    batch_success = batch_result.get("count", 0)
                    success_count += batch_success
                    logger.info(f"批次 {batch_idx + 1} 处理成功: {batch_success}/{len(batch_documents)} 个块")

                    # 构建结果列表
                    for i, chunk in enumerate(current_batch_chunks):
                        global_idx = start_idx + i
                        chunk_id = f"{document_id}_chunk_{global_idx}"
                        vector_results.append({
                            "chunk_id": chunk_id,
                            "chunk_index": global_idx,
                            "vector_id": chunk_id,
                            "content": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                            "status": "success"
                        })
                else:
                    # 批量失败，回退到逐个处理当前批次
                    logger.warning(f"批次 {batch_idx + 1} 批量处理失败: {batch_result.get('error')}, 回退到逐个处理")
                    for i, chunk in enumerate(current_batch_chunks):
                        global_idx = start_idx + i
                        chunk_id = f"{document_id}_chunk_{global_idx}"
                        metadata = {
                            "document_id": document_id,
                            "knowledge_base_id": knowledge_base_id,
                            "chunk_index": global_idx,
                            "total_chunks": total_chunks,
                            "title": f"文档 {document_id} 第 {global_idx + 1} 块"
                        }

                        try:
                            self.chroma_service.add_document(chunk_id, chunk, metadata)
                            success_count += 1
                            vector_results.append({
                                "chunk_id": chunk_id,
                                "chunk_index": global_idx,
                                "vector_id": chunk_id,
                                "content": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                                "status": "success"
                            })
                        except Exception as e:
                            failed_chunks.append({"index": global_idx, "chunk_id": chunk_id, "reason": str(e)})
                            vector_results.append({
                                "chunk_id": chunk_id,
                                "chunk_index": global_idx,
                                "vector_id": chunk_id,
                                "content": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                                "status": "failed"
                            })
                            logger.error(f"向量化块 {global_idx} 失败: {e}")

                # 每处理完一批，释放资源
                if batch_idx < total_batches - 1:
                    # 删除当前批次的大对象
                    del batch_documents
                    del current_batch_chunks
                    
                    # 触发垃圾回收
                    gc.collect()
                    
                    # 仅在大量批次时短暂暂停，避免系统过载
                    if total_batches > 10:
                        import time
                        time.sleep(0.1)

            # 计算向量化成功率
            vectorization_rate = success_count / len(chunks) if chunks else 0
            logger.info(f"向量化处理完成，成功率: {vectorization_rate:.2%} ({success_count}/{len(chunks)})")

            if failed_chunks:
                logger.warning(f"以下块向量化失败: {failed_chunks}")

            # 5. 保存分块到PostgreSQL（供实体识别使用）
            if db and chunks:
                try:
                    self._save_chunks_to_db(db, document_id, knowledge_base_id, chunks)
                    logger.info(f"分块已保存到PostgreSQL: {len(chunks)} 个")
                except Exception as e:
                    logger.error(f"保存分块到PostgreSQL失败: {e}")
                    # 不影响主流程，继续执行

            # 4. 更新进度 - 向量化完成（步骤4）
            processing_progress_service.update_progress(
                doc_id_str, 4, "向量化完成",
                f"向量化处理完成，成功率: {vectorization_rate:.2%}",
                {
                    "vectorization_rate": vectorization_rate,
                    "success_count": success_count,
                    "total_chunks": len(chunks)
                }
            )

            # 完成处理
            # 注：实体识别、实体对齐、知识图谱构建已分离到独立服务
            result = {
                "text": cleaned_text,
                "chunks": chunks,
                "vectors": vector_results,
                "vectorization_rate": vectorization_rate,
                "success_count": success_count,
                "total_chunks": len(chunks),
                "failed_chunks": failed_chunks,
                "success": True
            }

            processing_progress_service.complete_processing(doc_id_str, success=True, result=result)
            
            # 主动释放内存：删除大对象变量
            logger.info(f"文档 {document_id} 处理完成，开始释放内存...")
            del raw_text
            del cleaned_text
            del chunks
            del batch_documents
            del vector_results
            
            # 触发垃圾回收
            release_memory()
            logger.info(f"文档 {document_id} 内存释放完成")

            return result

        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            processing_progress_service.complete_processing(doc_id_str, success=False, result={"error": str(e)})
            
            # 即使处理失败也尝试释放内存
            try:
                if 'raw_text' in locals():
                    del raw_text
                if 'cleaned_text' in locals():
                    del cleaned_text
                if 'chunks' in locals():
                    del chunks
                release_memory()
            except:
                pass
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_documents(self, query: str, n_results: int = 10, 
                        knowledge_base_id: Optional[int] = None, 
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """搜索文档"""
        try:
            # 构建过滤条件
            where_filter = {}
            if knowledge_base_id:
                where_filter["knowledge_base_id"] = knowledge_base_id
            
            if filters:
                where_filter.update(filters)
            
            # 使用ChromaService进行向量搜索
            results = self.chroma_service.search_similar(query, n_results, where_filter)
            
            # 处理搜索结果
            processed_results = []
            for result in results:
                processed_results.append({
                    "id": result.get("id", ""),
                    "title": result.get("metadata", {}).get("title", ""),
                    "content": result.get("document", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return []
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """提取关键词"""
        return self.text_processor.extract_keywords_sync(text, top_n)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        return self.text_processor.calculate_similarity_sync(text1, text2)

    def _save_chunks_to_db(self, db: Session, document_id: int,
                           knowledge_base_id: Optional[int], chunks: List[str]):
        """保存分块到PostgreSQL数据库

        供实体识别服务使用

        Args:
            db: 数据库会话
            document_id: 文档ID
            knowledge_base_id: 知识库ID
            chunks: 分块文本列表
        """
        from app.modules.knowledge.models.knowledge_document import DocumentChunk

        # 先删除旧的分块
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete(synchronize_session=False)

        # 保存新的分块
        total_chunks = len(chunks)
        current_pos = 0
        for idx, chunk_text in enumerate(chunks):
            chunk_len = len(chunk_text)
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_text=chunk_text,
                chunk_index=idx,
                total_chunks=total_chunks,
                chunk_metadata={
                    "knowledge_base_id": knowledge_base_id,
                    "vector_id": f"{document_id}_chunk_{idx}"
                },
                vector_id=f"{document_id}_chunk_{idx}"
            )

            # 设置数据库表必需的字段（使用 SQLAlchemy 的 ORM 属性设置）
            # 这些字段在模型中未定义但在数据库表中存在
            from sqlalchemy import text
            db.execute(
                text("""
                    INSERT INTO document_chunks 
                    (document_id, chunk_text, chunk_index, total_chunks, 
                     start_pos, end_pos, vector_id, is_vectorized, created_at)
                    VALUES 
                    (:doc_id, :text, :idx, :total, 
                     :start_pos, :end_pos, :vector_id, 0, CURRENT_TIMESTAMP)
                """),
                {
                    "doc_id": document_id,
                    "text": chunk_text,
                    "idx": idx,
                    "total": total_chunks,
                    "start_pos": current_pos,
                    "end_pos": current_pos + chunk_len,
                    "vector_id": f"{document_id}_chunk_{idx}"
                }
            )
            current_pos += chunk_len

        db.commit()
        logger.info(f"已保存 {total_chunks} 个分块到PostgreSQL (文档ID: {document_id})")

    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """获取文档的分块信息"""
        try:
            # 构建查询条件
            where_filter = {"document_id": document_id}
            
            # 从向量数据库获取文档块
            results = self.chroma_service.get_documents_by_filter(where_filter)
            
            chunks = []
            for result in results:
                chunks.append({
                    "chunk_id": result.get("id", ""),
                    "content": result.get("document", ""),
                    "metadata": result.get("metadata", {})
                })
            
            # 按块索引排序
            chunks.sort(key=lambda x: x.get("metadata", {}).get("chunk_index", 0))
            
            return chunks
            
        except Exception as e:
            logger.error(f"获取文档块失败: {e}")
            return []
    
    def delete_document_vectors(self, document_id: int) -> bool:
        """删除文档的向量数据"""
        try:
            # 构建查询条件
            where_filter = {"document_id": document_id}
            
            # 从向量数据库删除文档块
            deleted_count = self.chroma_service.delete_documents_by_metadata(where_filter)
            
            logger.info(f"成功删除文档 {document_id} 的 {deleted_count} 个向量片段")
            return True
            
        except Exception as e:
            logger.error(f"删除文档向量数据失败: {e}")
            return False
    
    def update_document_vectors(self, document_id: int, new_content: str) -> Dict[str, Any]:
        """更新文档的向量数据"""
        try:
            # 1. 删除旧的向量数据
            self.delete_document_vectors(document_id)
            
            # 2. 重新处理文档内容
            # 智能分块
            chunks = self.text_processor.semantic_chunking_sync(new_content)
            
            # 3. 重新向量化（带验证）
            vector_results = []
            success_count = 0
            failed_chunks = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "title": f"文档 {document_id} 第 {i+1} 块"
                }
                
                try:
                    # 添加到向量数据库
                    self.chroma_service.add_document(chunk_id, chunk, metadata)
                    
                    # 验证是否成功写入
                    if self.chroma_service.verify_document_exists(chunk_id):
                        success_count += 1
                        vector_results.append({
                            "chunk_id": chunk_id,
                            "chunk_index": i,
                            "vector_id": chunk_id,
                            "status": "success"
                        })
                    else:
                        failed_chunks.append({"index": i, "chunk_id": chunk_id, "reason": "验证失败"})
                        vector_results.append({
                            "chunk_id": chunk_id,
                            "chunk_index": i,
                            "vector_id": chunk_id,
                            "status": "failed"
                        })
                except Exception as e:
                    failed_chunks.append({"index": i, "chunk_id": chunk_id, "reason": str(e)})
                    vector_results.append({
                        "chunk_id": chunk_id,
                        "chunk_index": i,
                        "vector_id": chunk_id,
                        "status": "failed"
                    })
                    logger.error(f"向量化块 {i} 失败: {e}")
            
            # 计算向量化成功率
            vectorization_rate = success_count / len(chunks) if chunks else 0
            logger.info(f"文档 {document_id} 向量数据更新完成，成功率: {vectorization_rate:.2%} ({success_count}/{len(chunks)})")
            
            if failed_chunks:
                logger.warning(f"以下块向量化失败: {failed_chunks}")
            
            return {
                "success": True,
                "chunks_count": len(vector_results),
                "success_count": success_count,
                "vectorization_rate": vectorization_rate,
                "failed_chunks": failed_chunks
            }
            
        except Exception as e:
            logger.error(f"更新文档向量数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_document_text(self, text: str) -> List[str]:
        """处理纯文本文档，返回分块结果"""
        try:
            # 文本预处理与清理
            cleaned_text = self.text_processor.clean_text(text)
            
            # 智能分块
            chunks = self.text_processor.semantic_chunking(cleaned_text)
            
            logger.info(f"文档文本处理完成，共 {len(chunks)} 个块")
            return chunks
            
        except Exception as e:
            logger.error(f"文档文本处理失败: {e}")
            return []