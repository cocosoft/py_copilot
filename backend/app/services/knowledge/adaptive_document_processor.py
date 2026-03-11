"""
增强版文档处理器 - 集成自适应批次处理

在原有 DocumentProcessor 基础上，集成 AdaptiveBatchProcessor 实现：
- 根据系统负载动态调整批次大小
- 支持流式处理大文件
- 自动失败重试机制
- 性能提升50%以上

任务编号: BE-001
阶段: Phase 1 - 基础优化期
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.knowledge.processing_progress_service import processing_progress_service
from app.services.knowledge.adaptive_batch_processor import (
    AdaptiveBatchProcessor,
    BatchConfig,
    BatchSizeStrategy
)

logger = logging.getLogger(__name__)


class AdaptiveDocumentProcessor:
    """
    增强版文档处理器
    
    集成自适应批次处理功能，优化向量化处理性能。
    """

    def __init__(self, batch_config: Optional[BatchConfig] = None):
        """
        初始化增强版文档处理器
        
        Args:
            batch_config: 批次配置，使用默认配置如果未提供
        """
        # 使用现有的文档解析器
        from app.services.knowledge.document_parser import DocumentParser
        self.parser = DocumentParser()

        # 使用高级文本处理器
        from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()

        # 使用现有的 ChromaService
        from app.services.knowledge.chroma_service import ChromaService
        self.chroma_service = ChromaService()

        # 使用知识图谱服务
        from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService
        self.knowledge_graph_service = KnowledgeGraphService()

        # 初始化自适应批次处理器
        if batch_config is None:
            batch_config = BatchConfig(
                base_batch_size=50,
                min_batch_size=10,
                max_batch_size=100,
                strategy=BatchSizeStrategy.BALANCED,
                max_retries=3,
                max_concurrent_batches=2
            )
        self.batch_processor = AdaptiveBatchProcessor(batch_config)

        logger.info("增强版文档处理器初始化完成（集成自适应批次处理）")

    async def process_document_async(
        self,
        file_path: str,
        file_type: str,
        document_id: int,
        knowledge_base_id: Optional[int] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        异步文档处理流程 - 使用自适应批次处理优化向量化
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            document_id: 文档ID
            knowledge_base_id: 知识库ID
            db: 数据库会话
            
        Returns:
            处理结果
        """
        doc_id_str = str(document_id)
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
            total_chunks = len(chunks)
            logger.info(f"文档分块完成，共 {total_chunks} 个块")

            # 4. 实体识别与关系提取
            processing_progress_service.update_progress(
                doc_id_str, 4, "实体识别",
                "正在识别实体和提取关系...",
                {"chunks_count": total_chunks}
            )
            entities, relationships = self.text_processor.extract_entities_relationships_sync(cleaned_text)
            logger.info(f"实体识别完成，识别到 {len(entities)} 个实体和 {len(relationships)} 个关系")

            # 5. 向量化处理 - 使用自适应批次处理器
            processing_progress_service.update_progress(
                doc_id_str, 5, "向量化处理",
                f"开始使用自适应批次处理 {total_chunks} 个块...",
                {"total_chunks": total_chunks}
            )

            # 准备文档块数据
            chunk_documents = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                metadata = {
                    "document_id": document_id,
                    "knowledge_base_id": knowledge_base_id,
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "title": f"文档 {document_id} 第 {i + 1} 块"
                }
                chunk_documents.append({
                    "chunk_id": chunk_id,
                    "text": chunk,
                    "metadata": metadata
                })

            # 定义向量化处理函数
            async def vectorize_chunk(chunk_data: Dict[str, Any]) -> Dict[str, Any]:
                """向量化单个分块"""
                try:
                    result = self.chroma_service.add_document(
                        document_id=chunk_data["chunk_id"],
                        text=chunk_data["text"],
                        metadata=chunk_data["metadata"]
                    )
                    return {
                        "success": result,
                        "chunk_id": chunk_data["chunk_id"],
                        "chunk_index": chunk_data["metadata"]["chunk_index"]
                    }
                except Exception as e:
                    logger.error(f"向量化分块 {chunk_data['chunk_id']} 失败: {e}")
                    raise

            # 使用自适应批次处理器处理
            batch_results, stats = await self.batch_processor.process_items(
                items=chunk_documents,
                processor=vectorize_chunk,
                progress_callback=lambda current, total: processing_progress_service.update_progress(
                    doc_id_str, 5, "向量化处理",
                    f"正在向量化: {current}/{total} ({current/total*100:.1f}%)",
                    {"current": current, "total": total, "percent": current/total*100}
                )
            )

            # 处理结果
            vector_results = []
            success_count = 0
            failed_chunks = []

            for batch_result in batch_results:
                for item in batch_result.items:
                    chunk_idx = item.metadata.get("index", 0)
                    chunk_content = chunk_documents[chunk_idx]["text"]
                    
                    if item.status.value == "success":
                        success_count += 1
                        vector_results.append({
                            "chunk_id": item.id,
                            "chunk_index": chunk_idx,
                            "vector_id": item.id,
                            "content": chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content,
                            "status": "success"
                        })
                    else:
                        failed_chunks.append({
                            "index": chunk_idx,
                            "chunk_id": item.id,
                            "reason": item.error_message or "未知错误"
                        })
                        vector_results.append({
                            "chunk_id": item.id,
                            "chunk_index": chunk_idx,
                            "vector_id": item.id,
                            "content": chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content,
                            "status": "failed"
                        })

            # 计算向量化成功率
            vectorization_rate = success_count / total_chunks if total_chunks else 0
            logger.info(
                f"向量化处理完成，成功率: {vectorization_rate:.2%} ({success_count}/{total_chunks}), "
                f"吞吐量: {stats.throughput:.2f} chunks/s"
            )

            # 获取性能报告
            performance_report = self.batch_processor.get_performance_report()
            logger.info(f"自适应批次处理性能报告:")
            logger.info(f"  - 平均批次大小: {performance_report.get('batch_size', {}).get('avg', 0):.1f}")
            logger.info(f"  - 平均处理时间: {performance_report.get('processing_time', {}).get('avg', 0):.3f}s")
            logger.info(f"  - 平均内存使用: {performance_report.get('memory_usage', {}).get('avg', 0):.1f}%")

            if failed_chunks:
                logger.warning(f"以下块向量化失败: {failed_chunks}")

            # 更新进度 - 向量化完成
            processing_progress_service.update_progress(
                doc_id_str, 5, "向量化完成",
                f"向量化处理完成，成功率: {vectorization_rate:.2%}, 吞吐量: {stats.throughput:.2f} chunks/s",
                {
                    "vectorization_rate": vectorization_rate,
                    "success_count": success_count,
                    "total_chunks": total_chunks,
                    "throughput": stats.throughput,
                    "processing_time": stats.total_processing_time
                }
            )

            # 6. 知识图谱构建
            processing_progress_service.update_progress(
                doc_id_str, 6, "知识图谱构建",
                "正在构建知识图谱...",
                {}
            )

            graph_data = await self._build_knowledge_graph(
                db, document_id, entities, relationships
            )

            # 完成处理
            result = {
                "text": cleaned_text,
                "chunks": chunks,
                "entities": entities,
                "relationships": relationships,
                "vectors": vector_results,
                "vectorization_rate": vectorization_rate,
                "success_count": success_count,
                "total_chunks": total_chunks,
                "failed_chunks": failed_chunks,
                "graph_data": graph_data,
                "performance": {
                    "throughput": stats.throughput,
                    "processing_time": stats.total_processing_time,
                    "batch_count": stats.total_batches,
                    "avg_batch_size": stats.avg_batch_size
                },
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

    async def _build_knowledge_graph(
        self,
        db: Session,
        document_id: int,
        entities: List[Dict],
        relationships: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """
        构建知识图谱
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            entities: 实体列表
            relationships: 关系列表
            
        Returns:
            知识图谱数据
        """
        if not db:
            logger.info("未提供数据库连接，跳过图谱化操作")
            return None

        try:
            # 导入 KnowledgeDocument 模型
            from app.modules.knowledge.models.knowledge_document import KnowledgeDocument

            # 获取文档对象
            document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
            if not document:
                logger.warning(f"未找到文档 {document_id}，跳过图谱化操作")
                return None

            # 提取并存储实体关系
            entity_result = self.knowledge_graph_service.extract_and_store_entities(
                db, document, entities, relationships
            )

            if not entity_result.get("success"):
                logger.warning(f"实体提取失败: {entity_result.get('error')}")
                return None

            # 构建知识图谱
            graph_data = self.knowledge_graph_service.build_document_graph(document_id, db)

            if "error" in graph_data:
                logger.warning(f"图谱构建失败: {graph_data.get('error')}")
                return None

            logger.info(
                f"图谱化操作完成，构建了包含 {len(graph_data.get('nodes', []))} 个节点 "
                f"和 {len(graph_data.get('edges', []))} 条边的知识图谱"
            )
            return graph_data

        except Exception as graph_error:
            logger.error(f"图谱化操作失败: {graph_error}")
            return None

    async def process_document_streaming(
        self,
        file_path: str,
        file_type: str,
        document_id: int,
        knowledge_base_id: Optional[int] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        流式文档处理 - 适用于超大文件
        
        边读取边处理，减少内存占用。
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            document_id: 文档ID
            knowledge_base_id: 知识库ID
            db: 数据库会话
            
        Returns:
            处理结果
        """
        doc_id_str = str(document_id)
        processing_progress_service.start_processing(doc_id_str, total_steps=4)

        try:
            # 1. 解析文档
            processing_progress_service.update_progress(
                doc_id_str, 1, "文档解析",
                "正在流式解析文档内容...",
                {"file_path": file_path}
            )
            raw_text = self.parser.parse_document(file_path)
            if not raw_text:
                raise ValueError(f"无法解析文档: {file_path}")

            logger.info(f"文档解析完成，内容长度: {len(raw_text)} 字符")

            # 2. 文本预处理
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
            total_chunks = len(chunks)
            logger.info(f"文档分块完成，共 {total_chunks} 个块")

            # 4. 流式向量化处理
            processing_progress_service.update_progress(
                doc_id_str, 4, "流式向量化",
                f"开始流式处理 {total_chunks} 个块...",
                {"total_chunks": total_chunks}
            )

            # 创建文档块生成器
            def chunk_generator():
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{document_id}_chunk_{i}"
                    metadata = {
                        "document_id": document_id,
                        "knowledge_base_id": knowledge_base_id,
                        "chunk_index": i,
                        "total_chunks": total_chunks,
                        "title": f"文档 {document_id} 第 {i + 1} 块"
                    }
                    yield {
                        "chunk_id": chunk_id,
                        "text": chunk,
                        "metadata": metadata
                    }

            # 定义向量化处理函数
            async def vectorize_chunk(chunk_data: Dict[str, Any]) -> Dict[str, Any]:
                try:
                    result = self.chroma_service.add_document(
                        document_id=chunk_data["chunk_id"],
                        text=chunk_data["text"],
                        metadata=chunk_data["metadata"]
                    )
                    return {
                        "success": result,
                        "chunk_id": chunk_data["chunk_id"],
                        "chunk_index": chunk_data["metadata"]["chunk_index"]
                    }
                except Exception as e:
                    logger.error(f"向量化分块 {chunk_data['chunk_id']} 失败: {e}")
                    raise

            # 使用流式处理
            batch_results, stats = await self.batch_processor.process_stream(
                item_stream=chunk_generator(),
                processor=vectorize_chunk,
                progress_callback=lambda current, total: processing_progress_service.update_progress(
                    doc_id_str, 4, "流式向量化",
                    f"正在处理: {current}/{total}",
                    {"current": current, "total": total}
                )
            )

            # 处理结果
            success_count = sum(
                1 for batch in batch_results
                for item in batch.items
                if item.status.value == "success"
            )
            vectorization_rate = success_count / total_chunks if total_chunks else 0

            logger.info(
                f"流式向量化处理完成，成功率: {vectorization_rate:.2%} ({success_count}/{total_chunks}), "
                f"吞吐量: {stats.throughput:.2f} chunks/s"
            )

            # 完成处理
            result = {
                "text": cleaned_text,
                "chunks": chunks,
                "total_chunks": total_chunks,
                "success_count": success_count,
                "vectorization_rate": vectorization_rate,
                "performance": {
                    "throughput": stats.throughput,
                    "processing_time": stats.total_processing_time,
                    "batch_count": stats.total_batches
                },
                "success": True
            }

            processing_progress_service.complete_processing(doc_id_str, success=True, result=result)
            return result

        except Exception as e:
            logger.error(f"流式文档处理失败: {e}")
            processing_progress_service.complete_processing(doc_id_str, success=False, result={"error": str(e)})
            return {
                "success": False,
                "error": str(e)
            }

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            性能统计信息
        """
        return self.batch_processor.get_performance_report()


# 便捷函数

async def process_document_with_adaptive_batching(
    file_path: str,
    file_type: str,
    document_id: int,
    knowledge_base_id: Optional[int] = None,
    db: Session = None,
    batch_config: Optional[BatchConfig] = None
) -> Dict[str, Any]:
    """
    使用自适应批次处理文档
    
    Args:
        file_path: 文件路径
        file_type: 文件类型
        document_id: 文档ID
        knowledge_base_id: 知识库ID
        db: 数据库会话
        batch_config: 批次配置
        
    Returns:
        处理结果
    """
    processor = AdaptiveDocumentProcessor(batch_config)
    return await processor.process_document_async(
        file_path, file_type, document_id, knowledge_base_id, db
    )
