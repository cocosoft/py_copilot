"""
统一向量化服务 - 整合所有向量化相关功能

基于现有向量化服务进行整合，解决功能重复问题：
- 整合 ChromaService (vectorization/chroma_service.py)
- 整合 FAISSIndexService (vectorization/faiss_index_service.py)
- 整合 VectorStoreAdapter (vectorization/vector_store_adapter.py)
- 整合检索服务功能

设计原则：
1. 模块化设计，支持多种向量存储后端
2. 向下兼容现有API调用
3. 支持同步和异步操作
4. 集成智能索引管理
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from enum import Enum

# 导入现有核心模块
from app.services.knowledge.vectorization.chroma_service import ChromaService
from app.services.knowledge.vectorization.faiss_index_service import FAISSIndexService
from app.services.knowledge.vectorization.vector_store_adapter import VectorStoreAdapter
from app.services.knowledge.retrieval.retrieval_service import RetrievalService
from app.services.knowledge.retrieval.semantic_search_service import SemanticSearchService

logger = logging.getLogger(__name__)


class VectorStoreType(Enum):
    """向量存储类型枚举"""
    CHROMA = "chroma"
    FAISS = "faiss"
    HYBRID = "hybrid"


class UnifiedVectorizationService:
    """统一向量化服务 - 整合所有向量化相关功能"""
    
    def __init__(self, vector_store_type: VectorStoreType = VectorStoreType.CHROMA):
        """
        初始化统一向量化服务
        
        Args:
            vector_store_type: 向量存储类型，默认为ChromaDB
        """
        self.vector_store_type = vector_store_type
        
        # ChromaDB服务 - 使用现有的ChromaService
        self.chroma_service = ChromaService()
        
        # FAISS索引服务 - 使用现有的FAISSIndexService
        self.faiss_service = FAISSIndexService()
        
        # 向量存储适配器 - 使用现有的VectorStoreAdapter
        from app.services.knowledge.vectorization.vector_store_adapter import VectorStoreConfig, VectorStoreBackend
        
        # 创建默认配置
        vector_config = VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008",
            default_collection="default",
            dimension=1536
        )
        self.vector_adapter = VectorStoreAdapter(vector_config)
        
        # 检索服务 - 使用现有的RetrievalService
        self.retrieval_service = RetrievalService()
        
        # 语义搜索服务 - 使用现有的SemanticSearchService
        self.semantic_search_service = SemanticSearchService()
        
        logger.info(f"统一向量化服务初始化完成，使用存储类型: {vector_store_type.value}")
    
    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None,
                     collection_name: str = "default") -> Dict[str, Any]:
        """
        添加文档到向量存储 - 整合现有添加功能
        
        Args:
            documents: 文档列表
            metadatas: 元数据列表
            collection_name: 集合名称
            
        Returns:
            添加结果
        """
        try:
            if self.vector_store_type == VectorStoreType.CHROMA:
                return self.chroma_service.add_documents(documents, metadatas, collection_name)
            elif self.vector_store_type == VectorStoreType.FAISS:
                return self.faiss_service.add_documents(documents, metadatas)
            elif self.vector_store_type == VectorStoreType.HYBRID:
                # 混合模式：同时存储到ChromaDB和FAISS
                chroma_result = self.chroma_service.add_documents(documents, metadatas, collection_name)
                faiss_result = self.faiss_service.add_documents(documents, metadatas)
                return {
                    'chroma': chroma_result,
                    'faiss': faiss_result,
                    'success': True
                }
            else:
                raise ValueError(f"不支持的向量存储类型: {self.vector_store_type}")
                
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search(self, query: str, n_results: int = 10, collection_name: str = "default",
               filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        向量搜索 - 整合现有搜索功能
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            collection_name: 集合名称
            filters: 过滤条件
            
        Returns:
            搜索结果
        """
        try:
            if self.vector_store_type == VectorStoreType.CHROMA:
                return self.chroma_service.search(query, n_results, collection_name, filters)
            elif self.vector_store_type == VectorStoreType.FAISS:
                return self.faiss_service.search(query, n_results, filters)
            elif self.vector_store_type == VectorStoreType.HYBRID:
                # 混合搜索：从两个存储中搜索并合并结果
                chroma_results = self.chroma_service.search(query, n_results, collection_name, filters)
                faiss_results = self.faiss_service.search(query, n_results, filters)
                
                # 合并和去重结果
                merged_results = self._merge_search_results(chroma_results, faiss_results, n_results)
                return merged_results
            else:
                raise ValueError(f"不支持的向量存储类型: {self.vector_store_type}")
                
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def semantic_search(self, query: str, n_results: int = 10, 
                       collection_name: str = "default") -> Dict[str, Any]:
        """
        语义搜索 - 使用现有的语义搜索服务
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            collection_name: 集合名称
            
        Returns:
            语义搜索结果
        """
        try:
            return self.semantic_search_service.search(query, n_results, collection_name)
        except Exception as e:
            logger.error(f"语义搜索失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """
        获取文档分块 - 使用现有的检索服务
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档分块列表
        """
        try:
            return self.retrieval_service.get_document_chunks(document_id)
        except Exception as e:
            logger.error(f"获取文档分块失败: {str(e)}")
            return []
    
    def delete_documents(self, document_ids: List[str], collection_name: str = "default") -> Dict[str, Any]:
        """
        删除文档 - 整合现有删除功能
        
        Args:
            document_ids: 文档ID列表
            collection_name: 集合名称
            
        Returns:
            删除结果
        """
        try:
            if self.vector_store_type == VectorStoreType.CHROMA:
                return self.chroma_service.delete_documents(document_ids, collection_name)
            elif self.vector_store_type == VectorStoreType.FAISS:
                return self.faiss_service.delete_documents(document_ids)
            elif self.vector_store_type == VectorStoreType.HYBRID:
                chroma_result = self.chroma_service.delete_documents(document_ids, collection_name)
                faiss_result = self.faiss_service.delete_documents(document_ids)
                return {
                    'chroma': chroma_result,
                    'faiss': faiss_result,
                    'success': True
                }
            else:
                raise ValueError(f"不支持的向量存储类型: {self.vector_store_type}")
                
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_collection_info(self, collection_name: str = "default") -> Dict[str, Any]:
        """
        获取集合信息 - 整合现有信息查询功能
        
        Args:
            collection_name: 集合名称
            
        Returns:
            集合信息
        """
        try:
            if self.vector_store_type == VectorStoreType.CHROMA:
                return self.chroma_service.get_collection_info(collection_name)
            elif self.vector_store_type == VectorStoreType.FAISS:
                return self.faiss_service.get_index_info()
            elif self.vector_store_type == VectorStoreType.HYBRID:
                chroma_info = self.chroma_service.get_collection_info(collection_name)
                faiss_info = self.faiss_service.get_index_info()
                return {
                    'chroma': chroma_info,
                    'faiss': faiss_info
                }
            else:
                raise ValueError(f"不支持的向量存储类型: {self.vector_store_type}")
                
        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _merge_search_results(self, chroma_results: Dict[str, Any], 
                            faiss_results: Dict[str, Any], n_results: int) -> Dict[str, Any]:
        """
        合并ChromaDB和FAISS的搜索结果
        
        Args:
            chroma_results: ChromaDB搜索结果
            faiss_results: FAISS搜索结果
            n_results: 需要的结果数量
            
        Returns:
            合并后的搜索结果
        """
        # 简单的结果合并策略：按相似度分数排序
        all_results = []
        
        if chroma_results.get('success', False):
            all_results.extend(chroma_results.get('documents', []))
        
        if faiss_results.get('success', False):
            all_results.extend(faiss_results.get('documents', []))
        
        # 去重和排序
        seen_docs = set()
        unique_results = []
        
        for result in sorted(all_results, key=lambda x: x.get('score', 0), reverse=True):
            doc_id = result.get('document_id')
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_results.append(result)
            
            if len(unique_results) >= n_results:
                break
        
        return {
            'success': True,
            'documents': unique_results,
            'total_count': len(unique_results)
        }
    
    async def add_documents_async(self, documents: List[str], 
                                 metadatas: Optional[List[Dict[str, Any]]] = None,
                                 collection_name: str = "default") -> Dict[str, Any]:
        """
        异步添加文档
        
        Args:
            同同步添加文档参数
            
        Returns:
            添加结果
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.add_documents, documents, metadatas, collection_name
        )
    
    async def search_async(self, query: str, n_results: int = 10, 
                          collection_name: str = "default",
                          filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        异步向量搜索
        
        Args:
            同同步搜索参数
            
        Returns:
            搜索结果
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.search, query, n_results, collection_name, filters
        )


# 创建全局实例，便于现有代码迁移
unified_vectorization_service = UnifiedVectorizationService()