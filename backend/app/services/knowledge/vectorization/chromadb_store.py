"""
ChromaDB 向量存储实现

包装现有的 ChromaService，适配 VectorStoreBase 接口
通过 HTTP API 与独立的 ChromaDB 服务通信
"""

import logging
from typing import List, Dict, Any, Optional

from .base import VectorStoreBase

logger = logging.getLogger(__name__)


class ChromaDBVectorStore(VectorStoreBase):
    """
    ChromaDB 向量存储实现
    
    特点：
    - 通过 HTTP API 与独立 ChromaDB 服务通信
    - 使用专业的向量数据库，支持高效的相似度搜索
    - 适合大规模数据（> 10万条）
    - 需要外部 ChromaDB 服务运行
    
    使用示例：
        store = ChromaDBVectorStore(server_url="http://localhost:8008")
        store.add_document("doc_1", "文本内容", {"key": "value"})
        results = store.search("查询文本", top_k=5)
    """
    
    def __init__(self, server_url: str = "http://localhost:8008", 
                 default_collection: str = "documents"):
        """
        初始化 ChromaDB 向量存储
        
        Args:
            server_url: ChromaDB 独立服务地址
            default_collection: 默认集合名称
        """
        # 延迟导入，避免循环依赖
        from app.services.knowledge.vectorization.chroma_service import ChromaService
        
        self.chroma_service = ChromaService(
            server_url=server_url,
            default_collection=default_collection
        )
        self.server_url = server_url
        self.default_collection = default_collection
        
        logger.info(f"ChromaDBVectorStore 初始化完成: {server_url}")
    
    def add_document(self, document_id: str, text: str, 
                     metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加单个文档到向量存储
        
        Args:
            document_id: 文档唯一标识
            text: 文档文本内容
            metadata: 文档元数据
            
        Returns:
            包含操作结果的字典
        """
        try:
            success = self.chroma_service.add_document(
                document_id=document_id,
                text=text,
                metadata=metadata,
                collection_name=self.default_collection
            )
            
            if success:
                logger.info(f"文档添加成功: {document_id}")
                return {
                    "success": True,
                    "document_id": document_id,
                    "message": "文档添加成功"
                }
            else:
                logger.error(f"文档添加失败: {document_id}")
                return {
                    "success": False,
                    "document_id": document_id,
                    "message": "文档添加失败"
                }
                
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return {
                "success": False,
                "document_id": document_id,
                "message": f"添加文档失败: {str(e)}"
            }
    
    def add_documents_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量添加文档到向量存储
        
        Args:
            documents: 文档列表，每个文档包含 document_id, text, metadata
            
        Returns:
            包含操作结果的字典
        """
        try:
            # 转换文档格式以适配 ChromaService
            batch_docs = [
                {
                    "document_id": doc.get("document_id", doc.get("id", "")),
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {})
                }
                for doc in documents
            ]
            
            result = self.chroma_service.add_documents_batch(
                documents=batch_docs,
                collection_name=self.default_collection
            )
            
            if result.get("success"):
                logger.info(f"批量添加完成: 成功 {result.get('count', 0)}/{len(documents)}")
                return {
                    "success": True,
                    "count": result.get("count", 0),
                    "total": len(documents),
                    "failed": [],
                    "message": f"成功添加 {result.get('count', 0)} 个文档"
                }
            else:
                logger.error(f"批量添加失败: {result.get('error')}")
                return {
                    "success": False,
                    "count": 0,
                    "total": len(documents),
                    "failed": [{"document_id": doc.get("document_id"), 
                               "error": result.get("error")} for doc in documents],
                    "message": f"批量添加失败: {result.get('error')}"
                }
                
        except Exception as e:
            logger.error(f"批量添加文档失败: {e}")
            return {
                "success": False,
                "count": 0,
                "total": len(documents),
                "failed": [{"document_id": doc.get("document_id"), 
                           "error": str(e)} for doc in documents],
                "message": f"批量添加失败: {str(e)}"
            }
    
    def search(self, query: str, top_k: int = 5, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            results = self.chroma_service.search_similar(
                query=query,
                top_k=top_k,
                filters=filters,
                collection_name=self.default_collection
            )
            
            # 转换结果格式以适配 VectorStoreBase 接口
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "document_id": result.get("id", ""),
                    "chunk_id": result.get("metadata", {}).get("chunk_id", result.get("id", "")),
                    "text": result.get("document", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "knowledge_base_id": result.get("metadata", {}).get("knowledge_base_id")
                })
            
            logger.info(f"搜索完成，找到 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档唯一标识
            
        Returns:
            是否删除成功
        """
        try:
            success = self.chroma_service.delete_documents(
                document_ids=[document_id],
                collection_name=self.default_collection
            )
            
            if success:
                logger.info(f"文档删除成功: {document_id}")
            else:
                logger.warning(f"文档删除失败: {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            document_id: 文档唯一标识
            
        Returns:
            文档信息，如果不存在则返回 None
        """
        try:
            # ChromaService 没有直接的 get_document 方法
            # 使用 search 方法配合精确过滤来模拟
            results = self.chroma_service.search_similar(
                query="",  # 空查询
                top_k=1,
                filters={"document_id": document_id},
                collection_name=self.default_collection
            )
            
            if results:
                result = results[0]
                return {
                    "document_id": result.get("id", ""),
                    "chunk_id": result.get("metadata", {}).get("chunk_id", result.get("id", "")),
                    "text": result.get("document", ""),
                    "metadata": result.get("metadata", {}),
                    "knowledge_base_id": result.get("metadata", {}).get("knowledge_base_id"),
                    "chunk_index": result.get("metadata", {}).get("chunk_index", 0),
                    "total_chunks": result.get("metadata", {}).get("total_chunks", 1)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            is_healthy = self.chroma_service.available
            
            if is_healthy:
                return {
                    "healthy": True,
                    "message": "ChromaDB 向量存储运行正常",
                    "details": {
                        "server_url": self.server_url,
                        "collection": self.default_collection
                    }
                }
            else:
                return {
                    "healthy": False,
                    "message": "ChromaDB 服务不可用",
                    "details": {
                        "server_url": self.server_url,
                        "collection": self.default_collection
                    }
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "message": f"ChromaDB 向量存储异常: {str(e)}",
                "details": {
                    "error": str(e),
                    "server_url": self.server_url
                }
            }
