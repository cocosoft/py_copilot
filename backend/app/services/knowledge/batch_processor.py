"""批量处理服务

提供批量实体提取、批量文档处理等功能，提高处理效率并降低成本。
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time

from app.services.knowledge.llm_extractor import LLMEntityExtractor
from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor
from app.services.knowledge.entity_extraction_cache import EntityExtractionCache

logger = logging.getLogger(__name__)


@dataclass
class BatchProcessResult:
    """批量处理结果"""
    success: bool
    items_processed: int
    items_failed: int
    results: List[Dict[str, Any]]
    errors: List[str]
    processing_time: float
    cache_hits: int = 0


class BatchEntityExtractor:
    """批量实体提取器
    
    支持并发批量提取实体，提供进度回调和错误处理。
    """
    
    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        """
        初始化批量实体提取器
        
        Args:
            max_workers: 最大并发工作线程数
            batch_size: 每批处理的文本数量
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.extractor = LLMEntityExtractor()
        self.cache = EntityExtractionCache()
        
    async def extract_entities_batch(
        self,
        texts: List[str],
        use_cache: bool = True,
        progress_callback: Optional[callable] = None
    ) -> BatchProcessResult:
        """
        批量提取实体
        
        Args:
            texts: 文本列表
            use_cache: 是否使用缓存
            progress_callback: 进度回调函数，接收(current, total)参数
            
        Returns:
            批量处理结果
        """
        start_time = time.time()
        results = []
        errors = []
        cache_hits = 0
        
        total = len(texts)
        processed = 0
        failed = 0
        
        logger.info(f"开始批量提取实体，共 {total} 个文本，批大小 {self.batch_size}")
        
        # 分批处理
        for i in range(0, total, self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size
            
            logger.info(f"处理第 {batch_num}/{total_batches} 批，共 {len(batch)} 个文本")
            
            # 并发处理批次内的文本
            batch_tasks = []
            for idx, text in enumerate(batch):
                global_idx = i + idx
                task = self._process_single_text(
                    text, global_idx, use_cache
                )
                batch_tasks.append(task)
            
            # 等待批次完成
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 处理结果
            for idx, result in enumerate(batch_results):
                global_idx = i + idx
                if isinstance(result, Exception):
                    logger.error(f"文本 {global_idx} 处理失败: {result}")
                    errors.append(f"文本 {global_idx}: {str(result)}")
                    results.append({
                        "index": global_idx,
                        "text": texts[global_idx][:100] + "..." if len(texts[global_idx]) > 100 else texts[global_idx],
                        "entities": [],
                        "relationships": [],
                        "success": False,
                        "error": str(result)
                    })
                    failed += 1
                else:
                    entities, relationships, from_cache = result
                    results.append({
                        "index": global_idx,
                        "text": texts[global_idx][:100] + "..." if len(texts[global_idx]) > 100 else texts[global_idx],
                        "entities": entities,
                        "relationships": relationships,
                        "success": True,
                        "from_cache": from_cache
                    })
                    if from_cache:
                        cache_hits += 1
                    processed += 1
            
            # 进度回调
            if progress_callback:
                progress_callback(min(i + self.batch_size, total), total)
            
            # 短暂延迟，避免过载
            if batch_num < total_batches:
                await asyncio.sleep(0.5)
        
        processing_time = time.time() - start_time
        
        logger.info(f"批量提取完成: {processed} 成功, {failed} 失败, "
                   f"{cache_hits} 缓存命中, 耗时 {processing_time:.2f}秒")
        
        return BatchProcessResult(
            success=failed == 0,
            items_processed=processed,
            items_failed=failed,
            results=results,
            errors=errors,
            processing_time=processing_time,
            cache_hits=cache_hits
        )
    
    async def _process_single_text(
        self,
        text: str,
        index: int,
        use_cache: bool
    ) -> Tuple[List[Dict], List[Dict], bool]:
        """
        处理单个文本
        
        Args:
            text: 输入文本
            index: 文本索引
            use_cache: 是否使用缓存
            
        Returns:
            (实体列表, 关系列表, 是否来自缓存)
        """
        if not text or not text.strip():
            return [], [], False
        
        # 检查缓存
        if use_cache:
            cached = await self.cache.get_cached_result(text, use_redis=False)
            if cached:
                logger.debug(f"文本 {index} 缓存命中")
                return cached[0], cached[1], True
        
        # 提取实体和关系
        entities, relationships = await self.extractor.extract_entities_and_relationships(
            text, use_cache=use_cache
        )
        
        return entities, relationships, False


class BatchDocumentProcessor:
    """批量文档处理器
    
    支持批量处理文档，提供并发处理和进度跟踪。
    """
    
    def __init__(self, max_workers: int = 3):
        """
        初始化批量文档处理器
        
        Args:
            max_workers: 最大并发工作线程数
        """
        self.max_workers = max_workers
        from app.services.knowledge.document_processor import DocumentProcessor
        self.document_processor = DocumentProcessor()
        
    async def process_documents_batch(
        self,
        documents: List[Dict[str, Any]],
        progress_callback: Optional[callable] = None
    ) -> BatchProcessResult:
        """
        批量处理文档
        
        Args:
            documents: 文档列表，每个文档包含 file_path, file_type, document_id 等
            progress_callback: 进度回调函数
            
        Returns:
            批量处理结果
        """
        start_time = time.time()
        results = []
        errors = []
        
        total = len(documents)
        processed = 0
        failed = 0
        
        logger.info(f"开始批量处理文档，共 {total} 个")
        
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_with_semaphore(doc: Dict, index: int):
            async with semaphore:
                return await self._process_single_document(doc, index)
        
        # 创建所有任务
        tasks = [
            process_with_semaphore(doc, i)
            for i, doc in enumerate(documents)
        ]
        
        # 处理完成的任务
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                results.append(result)
                if result.get("success"):
                    processed += 1
                else:
                    failed += 1
                    errors.append(f"文档 {result.get('document_id')}: {result.get('error')}")
            except Exception as e:
                logger.error(f"处理文档时发生错误: {e}")
                errors.append(f"未知文档: {str(e)}")
                failed += 1
            
            # 进度回调
            if progress_callback:
                progress_callback(i + 1, total)
        
        # 按原始顺序排序结果
        results.sort(key=lambda x: x.get("index", 0))
        
        processing_time = time.time() - start_time
        
        logger.info(f"批量处理完成: {processed} 成功, {failed} 失败, "
                   f"耗时 {processing_time:.2f}秒")
        
        return BatchProcessResult(
            success=failed == 0,
            items_processed=processed,
            items_failed=failed,
            results=results,
            errors=errors,
            processing_time=processing_time
        )
    
    async def _process_single_document(
        self,
        document: Dict[str, Any],
        index: int
    ) -> Dict[str, Any]:
        """
        处理单个文档
        
        Args:
            document: 文档信息
            index: 文档索引
            
        Returns:
            处理结果
        """
        file_path = document.get("file_path")
        file_type = document.get("file_type")
        document_id = document.get("document_id")
        knowledge_base_id = document.get("knowledge_base_id")
        
        try:
            # 使用线程池运行同步的文档处理
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.document_processor.process_document(
                    file_path=file_path,
                    file_type=file_type,
                    document_id=document_id,
                    knowledge_base_id=knowledge_base_id
                )
            )
            
            result["index"] = index
            result["document_id"] = document_id
            return result
            
        except Exception as e:
            logger.error(f"文档 {document_id} 处理失败: {e}")
            return {
                "index": index,
                "document_id": document_id,
                "success": False,
                "error": str(e)
            }


class BatchKnowledgeGraphBuilder:
    """批量知识图谱构建器
    
    支持批量构建知识图谱，优化处理流程。
    """
    
    def __init__(self, max_workers: int = 5):
        """
        初始化批量知识图谱构建器
        
        Args:
            max_workers: 最大并发工作线程数
        """
        self.max_workers = max_workers
        from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService
        self.kg_service = KnowledgeGraphService()
        
    async def build_graphs_batch(
        self,
        document_ids: List[int],
        db=None,
        progress_callback: Optional[callable] = None
    ) -> BatchProcessResult:
        """
        批量构建知识图谱
        
        Args:
            document_ids: 文档ID列表
            db: 数据库会话
            progress_callback: 进度回调函数
            
        Returns:
            批量处理结果
        """
        start_time = time.time()
        results = []
        errors = []
        
        total = len(document_ids)
        processed = 0
        failed = 0
        
        logger.info(f"开始批量构建知识图谱，共 {total} 个文档")
        
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def build_with_semaphore(doc_id: int, index: int):
            async with semaphore:
                return await self._build_single_graph(doc_id, index, db)
        
        # 创建所有任务
        tasks = [
            build_with_semaphore(doc_id, i)
            for i, doc_id in enumerate(document_ids)
        ]
        
        # 处理完成的任务
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                results.append(result)
                if result.get("success"):
                    processed += 1
                else:
                    failed += 1
                    errors.append(f"文档 {result.get('document_id')}: {result.get('error')}")
            except Exception as e:
                logger.error(f"构建图谱时发生错误: {e}")
                errors.append(f"未知文档: {str(e)}")
                failed += 1
            
            # 进度回调
            if progress_callback:
                progress_callback(i + 1, total)
        
        # 按原始顺序排序结果
        results.sort(key=lambda x: x.get("index", 0))
        
        processing_time = time.time() - start_time
        
        logger.info(f"批量构建完成: {processed} 成功, {failed} 失败, "
                   f"耗时 {processing_time:.2f}秒")
        
        return BatchProcessResult(
            success=failed == 0,
            items_processed=processed,
            items_failed=failed,
            results=results,
            errors=errors,
            processing_time=processing_time
        )
    
    async def _build_single_graph(
        self,
        document_id: int,
        index: int,
        db
    ) -> Dict[str, Any]:
        """
        构建单个文档的知识图谱
        
        Args:
            document_id: 文档ID
            index: 索引
            db: 数据库会话
            
        Returns:
            构建结果
        """
        try:
            # 使用线程池运行同步的图谱构建
            loop = asyncio.get_event_loop()
            graph_data = await loop.run_in_executor(
                None,
                lambda: self.kg_service.build_document_graph(document_id, db)
            )
            
            if "error" in graph_data:
                return {
                    "index": index,
                    "document_id": document_id,
                    "success": False,
                    "error": graph_data["error"]
                }
            
            return {
                "index": index,
                "document_id": document_id,
                "success": True,
                "node_count": len(graph_data.get("nodes", [])),
                "edge_count": len(graph_data.get("edges", [])),
                "graph_data": graph_data
            }
            
        except Exception as e:
            logger.error(f"文档 {document_id} 图谱构建失败: {e}")
            return {
                "index": index,
                "document_id": document_id,
                "success": False,
                "error": str(e)
            }


# 便捷函数

async def extract_entities_batch(
    texts: List[str],
    max_workers: int = 5,
    batch_size: int = 10,
    use_cache: bool = True,
    progress_callback: Optional[callable] = None
) -> BatchProcessResult:
    """
    便捷函数：批量提取实体
    
    Args:
        texts: 文本列表
        max_workers: 最大并发数
        batch_size: 批大小
        use_cache: 是否使用缓存
        progress_callback: 进度回调
        
    Returns:
        批量处理结果
    """
    extractor = BatchEntityExtractor(max_workers=max_workers, batch_size=batch_size)
    return await extractor.extract_entities_batch(texts, use_cache, progress_callback)


async def process_documents_batch(
    documents: List[Dict[str, Any]],
    max_workers: int = 3,
    progress_callback: Optional[callable] = None
) -> BatchProcessResult:
    """
    便捷函数：批量处理文档
    
    Args:
        documents: 文档列表
        max_workers: 最大并发数
        progress_callback: 进度回调
        
    Returns:
        批量处理结果
    """
    processor = BatchDocumentProcessor(max_workers=max_workers)
    return await processor.process_documents_batch(documents, progress_callback)


async def build_knowledge_graphs_batch(
    document_ids: List[int],
    db=None,
    max_workers: int = 5,
    progress_callback: Optional[callable] = None
) -> BatchProcessResult:
    """
    便捷函数：批量构建知识图谱
    
    Args:
        document_ids: 文档ID列表
        db: 数据库会话
        max_workers: 最大并发数
        progress_callback: 进度回调
        
    Returns:
        批量处理结果
    """
    builder = BatchKnowledgeGraphBuilder(max_workers=max_workers)
    return await builder.build_graphs_batch(document_ids, db, progress_callback)
