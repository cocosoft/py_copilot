import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.knowledge.processing_progress_service import processing_progress_service

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """文档处理核心模块，负责文档解析、分块、向量化和图谱化"""

    def __init__(self):
        # 使用现有的文档解析器
        from app.services.knowledge.document_parser import DocumentParser
        self.parser = DocumentParser()

        # 使用高级文本处理器（支持spacy）
        from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()

        # 使用现有的ChromaService
        from app.services.knowledge.chroma_service import ChromaService
        self.chroma_service = ChromaService()

        # 使用现有的检索服务
        from app.services.knowledge.retrieval_service import RetrievalService
        self.retrieval_service = RetrievalService()

        # 使用知识图谱服务
        from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService
        self.knowledge_graph_service = KnowledgeGraphService()

    def process_document(self, file_path: str, file_type: str, document_id: int,
                        knowledge_base_id: Optional[int] = None, db: Session = None,
                        document_uuid: Optional[str] = None) -> Dict[str, Any]:
        """完整文档处理流程 - 集成图谱化操作和进度反馈

        Args:
            file_path: 文件路径
            file_type: 文件类型
            document_id: 文档ID（数据库自增ID）
            knowledge_base_id: 知识库ID
            db: 数据库会话
            document_uuid: 文档UUID（用于向量存储）
        """

        # 使用uuid作为进度追踪ID（如果提供）
        doc_id_str = document_uuid if document_uuid else str(document_id)
        processing_progress_service.start_processing(doc_id_str, total_steps=6)

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

            # 3. 智能分块
            processing_progress_service.update_progress(
                doc_id_str, 3, "智能分块",
                "正在进行语义分块...",
                {"cleaned_text_length": len(cleaned_text)}
            )
            chunks = self.text_processor.semantic_chunking_sync(cleaned_text)
            logger.info(f"文档分块完成，共 {len(chunks)} 个块")

            # 4. 实体识别与关系提取
            processing_progress_service.update_progress(
                doc_id_str, 4, "实体识别",
                "正在识别实体和提取关系...",
                {"chunks_count": len(chunks)}
            )
            entities, relationships = self.text_processor.extract_entities_relationships_sync(cleaned_text)
            logger.info(f"实体识别完成，识别到 {len(entities)} 个实体和 {len(relationships)} 个关系")
            
            # 5. 向量化处理 - 分批次批量处理优化版
            vector_results = []
            success_count = 0
            failed_chunks = []

            # 根据chunks数量决定批次大小
            # 如果chunks过多，分批次处理以避免内存占用过高和请求超时
            total_chunks = len(chunks)
            if total_chunks <= 50:
                batch_size = total_chunks  # 小文件一次性处理
            elif total_chunks <= 100:
                batch_size = 50  # 中等文件分2批
            else:
                batch_size = 50  # 大文件每批50个chunks

            total_batches = (total_chunks + batch_size - 1) // batch_size
            logger.info(f"开始分批次向量化处理: {total_chunks} 个块, 分成 {total_batches} 批, 每批 {batch_size} 个")

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, total_chunks)
                current_batch_chunks = chunks[start_idx:end_idx]

                # 更新进度
                processing_progress_service.update_progress(
                    doc_id_str, 5, "向量化处理",
                    f"正在处理第 {batch_idx + 1}/{total_batches} 批向量数据...",
                    {
                        "batch": batch_idx + 1,
                        "total_batches": total_batches,
                        "progress": f"{start_idx + 1}-{end_idx}/{total_chunks}"
                    }
                )

                # 准备当前批次数据
                # 使用uuid作为向量存储的document_id（如果提供）
                vector_doc_id = document_uuid if document_uuid else str(document_id)
                batch_documents = []
                for i, chunk in enumerate(current_batch_chunks):
                    global_idx = start_idx + i
                    chunk_id = f"{vector_doc_id}_chunk_{global_idx}"
                    metadata = {
                        "document_id": vector_doc_id,  # 使用uuid作为document_id
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
                        chunk_id = f"{vector_doc_id}_chunk_{global_idx}"
                        metadata = {
                            "document_id": vector_doc_id,  # 使用uuid作为document_id
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

                # 每处理完一批，短暂释放资源
                if batch_idx < total_batches - 1:
                    import gc
                    gc.collect()  # 触发垃圾回收
                    import time
                    time.sleep(0.5)  # 短暂暂停，让系统有时间处理其他请求

            # 计算向量化成功率
            vectorization_rate = success_count / len(chunks) if chunks else 0
            logger.info(f"向量化处理完成，成功率: {vectorization_rate:.2%} ({success_count}/{len(chunks)})")

            if failed_chunks:
                logger.warning(f"以下块向量化失败: {failed_chunks}")

            # 5.5 更新进度 - 向量化完成
            processing_progress_service.update_progress(
                doc_id_str, 5, "向量化完成",
                f"向量化处理完成，成功率: {vectorization_rate:.2%}",
                {
                    "vectorization_rate": vectorization_rate,
                    "success_count": success_count,
                    "total_chunks": len(chunks)
                }
            )

            # 6. ✨ 新增：图谱化操作（如果提供了数据库连接）
            processing_progress_service.update_progress(
                doc_id_str, 6, "知识图谱构建",
                "正在构建知识图谱...",
                {}
            )

            graph_data = None
            if db:
                try:
                    # 导入KnowledgeDocument模型
                    from app.modules.knowledge.models.knowledge_document import KnowledgeDocument

                    # 获取文档对象
                    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
                    if document:
                        # 提取并存储实体关系（传递已提取的实体，避免重复提取）
                        entity_result = self.knowledge_graph_service.extract_and_store_entities(
                            db, document, entities, relationships
                        )

                        if entity_result.get("success"):
                            # 构建知识图谱
                            graph_data = self.knowledge_graph_service.build_document_graph(document_id, db)

                            if "error" not in graph_data:
                                logger.info(f"图谱化操作完成，构建了包含 {len(graph_data.get('nodes', []))} 个节点和 {len(graph_data.get('edges', []))} 条边的知识图谱")
                            else:
                                logger.warning(f"图谱构建失败: {graph_data.get('error')}")
                        else:
                            logger.warning(f"实体提取失败: {entity_result.get('error')}")
                    else:
                        logger.warning(f"未找到文档 {document_id}，跳过图谱化操作")

                except Exception as graph_error:
                    logger.error(f"图谱化操作失败: {graph_error}")
                    # 图谱化失败不影响文档处理流程继续
            else:
                logger.info("未提供数据库连接，跳过图谱化操作")

            # 完成处理
            result = {
                "text": cleaned_text,
                "chunks": chunks,
                "entities": entities,
                "relationships": relationships,
                "vectors": vector_results,
                "vectorization_rate": vectorization_rate,
                "success_count": success_count,
                "total_chunks": len(chunks),
                "failed_chunks": failed_chunks,
                "graph_data": graph_data,
                "success": True
            }

            processing_progress_service.complete_processing(doc_id_str, success=True, result=result)

            return result

        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            processing_progress_service.complete_processing(doc_id_str, success=False, result={"error": str(e)})
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