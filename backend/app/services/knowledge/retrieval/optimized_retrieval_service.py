"""
优化后的检索服务包装器

将性能优化功能集成到现有的检索服务中，提供缓存、监控等优化功能。
"""
import logging
from typing import List, Dict, Any, Optional

from .retrieval_service import RetrievalService, AdvancedRetrievalService
from .performance_optimizer import OptimizedRetrievalService, DocumentChunkOptimizer, PerformanceMonitor

logger = logging.getLogger(__name__)


class OptimizedRetrievalServiceWrapper:
    """优化检索服务包装器"""
    
    def __init__(self):
        """初始化优化检索服务包装器"""
        # 创建原始服务实例
        self.original_retrieval_service = RetrievalService()
        self.original_advanced_service = AdvancedRetrievalService()
        
        # 创建优化服务
        self.optimized_retrieval = OptimizedRetrievalService(self.original_retrieval_service)
        self.document_optimizer = DocumentChunkOptimizer()
        
        logger.info("优化检索服务初始化完成")
    
    def search_documents(self, query: str, limit: int = 10, knowledge_base_id: int = None) -> List[Dict[str, Any]]:
        """优化后的文档搜索
        
        Args:
            query: 查询文本
            limit: 结果数量限制
            knowledge_base_id: 知识库ID
            
        Returns:
            搜索结果
        """
        return self.optimized_retrieval.search_documents(query, limit, knowledge_base_id)
    
    def advanced_search(self, query: str, n_results: int = 10, 
                       knowledge_base_id: Optional[int] = None, 
                       tags: Optional[List[str]] = None, 
                       filters: Optional[Dict[str, Any]] = None, 
                       sort_by: str = "relevance", 
                       entity_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """优化后的高级搜索
        
        Args:
            query: 查询文本
            n_results: 结果数量
            knowledge_base_id: 知识库ID
            tags: 标签过滤
            filters: 其他过滤条件
            sort_by: 排序方式
            entity_filter: 实体过滤
            
        Returns:
            搜索结果
        """
        # 高级搜索暂时不缓存，因为参数组合太多
        return self.original_advanced_service.advanced_search(
            query, n_results, knowledge_base_id, tags, filters, sort_by, entity_filter
        )
    
    def hybrid_search(self, query: str, n_results: int = 10, 
                     keyword_weight: float = 0.3, 
                     vector_weight: float = 0.7, 
                     **kwargs) -> List[Dict[str, Any]]:
        """优化后的混合搜索
        
        Args:
            query: 查询文本
            n_results: 结果数量
            keyword_weight: 关键词权重
            vector_weight: 向量权重
            **kwargs: 其他参数
            
        Returns:
            搜索结果
        """
        return self.original_advanced_service.hybrid_search(
            query, n_results, keyword_weight, vector_weight, **kwargs
        )
    
    def add_document_to_index(self, document_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """将文档添加到索引（优化分块）
        
        Args:
            document_id: 文档ID
            text: 文档文本
            metadata: 文档元数据
        """
        # 使用优化分块
        optimized_chunks = self.document_optimizer.optimize_chunking(text, metadata)
        
        # 添加每个分块到索引
        for i, chunk in enumerate(optimized_chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_metadata = chunk['metadata'].copy()
            chunk_metadata.update({
                "parent_document_id": document_id,
                "chunk_summary": chunk.get('summary', '')
            })
            
            self.original_retrieval_service.add_document_to_index(
                chunk_id, chunk['content'], chunk_metadata
            )
        
        logger.info(f"文档 {document_id} 已优化分块并添加到索引，分块数: {len(optimized_chunks)}")
    
    def delete_document_from_index(self, document_id: str) -> None:
        """从索引中删除文档
        
        Args:
            document_id: 文档ID
        """
        self.original_retrieval_service.delete_document_from_index(document_id)
        
        # 同时删除相关的分块
        metadata_filter = {"parent_document_id": document_id}
        self.original_retrieval_service.delete_documents_by_metadata(metadata_filter)
    
    def get_document_count(self) -> int:
        """获取索引中的文档数量
        
        Returns:
            文档数量
        """
        return self.original_retrieval_service.get_document_count()
    
    def delete_documents_by_metadata(self, metadata_filter: Dict[str, Any]) -> int:
        """根据元数据删除文档
        
        Args:
            metadata_filter: 元数据过滤条件
            
        Returns:
            删除的文档数量
        """
        return self.original_retrieval_service.delete_documents_by_metadata(metadata_filter)
    
    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """获取指定文档的所有向量片段
        
        Args:
            document_id: 文档ID
            
        Returns:
            向量片段列表
        """
        return self.original_retrieval_service.get_document_chunks(document_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            性能统计
        """
        return self.optimized_retrieval.get_performance_stats()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.optimized_retrieval.clear_cache()
    
    def optimize_document_processing(self, content: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """优化文档处理
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            优化后的分块列表
        """
        return self.document_optimizer.optimize_chunking(content, metadata)


# 全局优化检索服务实例
_optimized_retrieval_service = None


def get_optimized_retrieval_service() -> OptimizedRetrievalServiceWrapper:
    """获取优化检索服务实例
    
    Returns:
        优化检索服务实例
    """
    global _optimized_retrieval_service
    if _optimized_retrieval_service is None:
        _optimized_retrieval_service = OptimizedRetrievalServiceWrapper()
    return _optimized_retrieval_service


def create_optimized_knowledge_service():
    """创建优化的知识服务（替换原始服务）"""
    from app.modules.knowledge.services.knowledge_service import KnowledgeService
    
    class OptimizedKnowledgeService(KnowledgeService):
        """优化的知识服务"""
        
        def __init__(self):
            """初始化优化的知识服务"""
            super().__init__()
            
            # 替换检索服务
            self.retrieval_service = get_optimized_retrieval_service()
            
            logger.info("优化知识服务初始化完成")
        
        def search_documents(self, query: str, limit: int = 10, knowledge_base_id: int = None) -> List[Dict[str, Any]]:
            """优化后的文档搜索
            
            Args:
                query: 查询文本
                limit: 结果数量限制
                knowledge_base_id: 知识库ID
                
            Returns:
                搜索结果
            """
            return self.retrieval_service.search_documents(query, limit, knowledge_base_id)
        
        def add_document_to_knowledge_base(self, knowledge_base_id: int, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
            """优化后的文档添加
            
            Args:
                knowledge_base_id: 知识库ID
                content: 文档内容
                metadata: 文档元数据
                
            Returns:
                添加结果
            """
            # 使用优化分块
            optimized_chunks = self.retrieval_service.optimize_document_processing(content, metadata)
            
            result = {
                "success": True,
                "knowledge_base_id": knowledge_base_id,
                "chunk_count": len(optimized_chunks),
                "total_characters": len(content),
                "optimized_chunks": optimized_chunks
            }
            
            logger.info(f"文档已优化处理，分块数: {len(optimized_chunks)}")
            
            return result
    
    return OptimizedKnowledgeService()