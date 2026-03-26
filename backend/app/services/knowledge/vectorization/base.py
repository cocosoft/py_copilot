"""
向量存储抽象基类

定义统一的向量存储接口，支持多种后端实现
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStoreBase(ABC):
    """
    向量存储抽象基类
    
    所有向量存储后端必须实现此接口，以确保统一的使用方式
    """
    
    @abstractmethod
    def add_document(
        self, 
        document_id: str, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        添加单个文档到向量存储
        
        Args:
            document_id: 文档唯一标识
            text: 文档文本内容
            metadata: 文档元数据
            
        Returns:
            操作结果，包含 success 状态和相关信息
        """
        pass
    
    @abstractmethod
    def add_documents_batch(
        self, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量添加文档到向量存储
        
        Args:
            documents: 文档列表，每个文档包含 document_id, text, metadata
            
        Returns:
            操作结果，包含 success 状态和成功添加的数量
        """
        pass
    
    @abstractmethod
    def search(
        self, 
        query: str, 
        top_k: int = 5, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件，如 {"knowledge_base_id": 1}
            
        Returns:
            搜索结果列表，每个结果包含 document_id, text, metadata, score
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档唯一标识
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            document_id: 文档唯一标识
            
        Returns:
            文档信息，如果不存在返回 None
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息，包含：
            - healthy: 是否健康
            - message: 状态描述
            - details: 详细信息
        """
        pass
    
    def close(self):
        """
        关闭存储连接
        
        子类可以重写此方法以释放资源
        """
        pass
