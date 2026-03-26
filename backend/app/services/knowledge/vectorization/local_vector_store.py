"""
本地向量存储降级方案
当ChromaDB服务不可用时，使用内存中的向量存储作为降级方案
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalVectorStore:
    """本地内存向量存储 - 作为ChromaDB的降级方案
    
    特点：
    1. 数据存储在内存中，重启后丢失
    2. 使用简单的余弦相似度计算
    3. 适合开发和测试环境
    4. 不适合生产环境的大数据量场景
    """
    
    def __init__(self):
        """初始化本地向量存储"""
        self.documents = {}  # document_id -> {"text": str, "metadata": dict, "vector": np.array}
        self.collection_name = "documents"
        logger.info("本地向量存储初始化完成（降级方案）")
    
    def _simple_hash_vector(self, text: str, dim: int = 384) -> np.ndarray:
        """使用简单哈希生成文本向量
        
        这不是真正的语义向量，但在降级方案中可用作近似
        实际应用中应该使用轻量级embedding模型
        
        Args:
            text: 输入文本
            dim: 向量维度
            
        Returns:
            归一化的向量
        """
        # 使用字符哈希生成向量
        vector = np.zeros(dim)
        for i, char in enumerate(text):
            vector[i % dim] += ord(char)
        
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(vec1, vec2)
    
    def add_document(self, document_id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """添加单个文档
        
        Args:
            document_id: 文档唯一标识
            text: 文档文本内容
            metadata: 文档元数据
            
        Returns:
            bool: 是否添加成功
        """
        try:
            vector = self._simple_hash_vector(text)
            self.documents[document_id] = {
                "text": text,
                "metadata": metadata,
                "vector": vector,
                "created_at": datetime.now().isoformat()
            }
            logger.debug(f"本地存储：添加文档 {document_id}")
            return True
        except Exception as e:
            logger.error(f"本地存储：添加文档失败 {document_id}: {e}")
            return False
    
    def add_documents_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量添加文档
        
        Args:
            documents: 文档列表，每个文档包含 id, text, metadata
            
        Returns:
            Dict: 包含 success (bool) 和 count (int) 的结果
        """
        success_count = 0
        for doc in documents:
            doc_id = doc.get("id") or doc.get("document_id")
            if doc_id and self.add_document(doc_id, doc.get("text", ""), doc.get("metadata", {})):
                success_count += 1
        
        logger.info(f"本地存储：批量添加 {success_count}/{len(documents)} 个文档")
        return {"success": True, "count": success_count}
    
    def search_similar(self, query: str, top_k: int = 5, 
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件（本地存储暂不支持复杂过滤）
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.documents:
            return []
        
        query_vector = self._simple_hash_vector(query)
        
        # 计算相似度
        similarities = []
        for doc_id, doc_data in self.documents.items():
            score = self._cosine_similarity(query_vector, doc_data["vector"])
            similarities.append({
                "id": doc_id,
                "document": doc_data["text"],
                "metadata": doc_data["metadata"],
                "score": float(score)
            })
        
        # 排序并返回top_k
        similarities.sort(key=lambda x: x["score"], reverse=True)
        results = similarities[:top_k]
        
        logger.debug(f"本地存储：搜索 '{query[:30]}...' 返回 {len(results)} 个结果")
        return results
    
    def delete_documents(self, document_ids: Optional[List[str]] = None,
                        filters: Optional[Dict[str, Any]] = None) -> bool:
        """删除文档
        
        Args:
            document_ids: 要删除的文档ID列表
            filters: 过滤条件
            
        Returns:
            bool: 是否删除成功
        """
        if document_ids:
            for doc_id in document_ids:
                if doc_id in self.documents:
                    del self.documents[doc_id]
            logger.info(f"本地存储：删除 {len(document_ids)} 个文档")
        
        if filters:
            # 根据过滤条件删除（简单实现）
            to_delete = []
            for doc_id, doc_data in self.documents.items():
                metadata = doc_data.get("metadata", {})
                match = all(metadata.get(k) == v for k, v in filters.items())
                if match:
                    to_delete.append(doc_id)
            
            for doc_id in to_delete:
                del self.documents[doc_id]
            
            logger.info(f"本地存储：根据过滤条件删除 {len(to_delete)} 个文档")
        
        return True
    
    def count_documents(self) -> int:
        """获取文档数量
        
        Returns:
            int: 文档数量
        """
        return len(self.documents)
    
    def delete_documents_by_metadata(self, filters: Dict[str, Any]) -> int:
        """根据元数据删除文档
        
        Args:
            filters: 过滤条件
            
        Returns:
            int: 删除的文档数量
        """
        to_delete = []
        for doc_id, doc_data in self.documents.items():
            metadata = doc_data.get("metadata", {})
            match = all(metadata.get(k) == v for k, v in filters.items())
            if match:
                to_delete.append(doc_id)
        
        for doc_id in to_delete:
            del self.documents[doc_id]
        
        logger.info(f"本地存储：根据元数据删除 {len(to_delete)} 个文档")
        return len(to_delete)
    
    def search_documents_by_metadata(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """根据元数据搜索文档
        
        Args:
            filters: 过滤条件
            
        Returns:
            Dict: 包含 ids, documents, metadatas 的结果字典
        """
        ids = []
        documents = []
        metadatas = []
        
        for doc_id, doc_data in self.documents.items():
            metadata = doc_data.get("metadata", {})
            match = all(metadata.get(k) == v for k, v in filters.items())
            if match:
                ids.append(doc_id)
                documents.append(doc_data["text"])
                metadatas.append(metadata)
        
        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas
        }
    
    def verify_document_exists(self, document_id: str) -> bool:
        """验证文档是否存在
        
        Args:
            document_id: 文档ID
            
        Returns:
            bool: 是否存在
        """
        return document_id in self.documents
