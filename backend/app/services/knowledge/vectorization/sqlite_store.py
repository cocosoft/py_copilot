"""
SQLite 向量存储实现

使用 SQLite 存储文档向量，无需外部服务。
使用简单的哈希和文本匹配实现相似度搜索。
"""

import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, Float, JSON, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

from .base import VectorStoreBase

logger = logging.getLogger(__name__)

Base = declarative_base()


class VectorDocument(Base):
    """向量文档模型"""
    __tablename__ = "vector_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), nullable=False, index=True)  # 文档ID
    chunk_id = Column(String(100), nullable=False, index=True)     # 块ID
    text = Column(Text, nullable=False)                            # 文本内容
    vector = Column(JSON, nullable=True)                           # 向量数据（JSON格式）
    knowledge_base_id = Column(Integer, nullable=True, index=True) # 知识库ID
    chunk_index = Column(Integer, nullable=True)                   # 块索引
    total_chunks = Column(Integer, nullable=True)                  # 总块数
    meta_data = Column(JSON, nullable=True)                        # 元数据（使用meta_data避免保留字冲突）
    created_at = Column(String(50), nullable=True)                 # 创建时间


class SQLiteVectorStore(VectorStoreBase):
    """
    SQLite 向量存储实现
    
    特点：
    - 无需外部服务，内嵌在应用中
    - 使用 SQLite 存储文档和向量
    - 使用余弦相似度进行搜索
    - 适合中小规模数据（< 10万条）
    """
    
    def __init__(self, db_path: str = "./vector_store.db"):
        """
        初始化 SQLite 向量存储
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"SQLiteVectorStore 初始化完成: {db_path}")
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        return self.Session()
    
    def _text_to_vector(self, text: str, dim: int = 384) -> List[float]:
        """
        将文本转换为向量（简单实现）
        
        使用字符级别的 n-gram 哈希来生成向量。
        这不是真正的语义向量，但可用于简单的相似度匹配。
        
        Args:
            text: 输入文本
            dim: 向量维度
            
        Returns:
            向量列表
        """
        # 简单的词袋模型向量
        vector = np.zeros(dim)
        words = text.lower().split()
        
        for word in words:
            # 使用哈希将单词映射到向量位置
            hash_val = hash(word) % dim
            vector[hash_val] += 1.0
        
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数（-1 到 1）
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(v1, v2) / (norm1 * norm2))
    
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
            操作结果
        """
        try:
            session = self._get_session()
            
            # 生成向量
            vector = self._text_to_vector(text)
            
            # 创建文档记录
            doc = VectorDocument(
                document_id=document_id,
                chunk_id=metadata.get("chunk_id", document_id),
                text=text,
                vector=vector,
                knowledge_base_id=metadata.get("knowledge_base_id"),
                chunk_index=metadata.get("chunk_index", 0),
                total_chunks=metadata.get("total_chunks", 1),
                meta_data=metadata,
                created_at=func.now()
            )
            
            session.add(doc)
            session.commit()
            session.close()
            
            logger.info(f"文档添加成功: {document_id}")
            return {
                "success": True,
                "document_id": document_id,
                "message": "文档添加成功"
            }
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return {
                "success": False,
                "document_id": document_id,
                "message": f"添加失败: {str(e)}"
            }
    
    def add_documents_batch(
        self, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            操作结果
        """
        success_count = 0
        failed_documents = []
        
        try:
            session = self._get_session()
            
            for doc_data in documents:
                try:
                    document_id = doc_data.get("document_id")
                    text = doc_data.get("text", "")
                    metadata = doc_data.get("metadata", {})
                    
                    # 生成向量
                    vector = self._text_to_vector(text)
                    
                    # 创建文档记录
                    doc = VectorDocument(
                        document_id=document_id,
                        chunk_id=metadata.get("chunk_id", document_id),
                        text=text,
                        vector=vector,
                        knowledge_base_id=metadata.get("knowledge_base_id"),
                        chunk_index=metadata.get("chunk_index", 0),
                        total_chunks=metadata.get("total_chunks", 1),
                        meta_data=metadata,
                        created_at=func.now()
                    )
                    
                    session.add(doc)
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"添加文档失败: {doc_data.get('document_id')}, 错误: {e}")
                    failed_documents.append({
                        "document_id": doc_data.get("document_id"),
                        "error": str(e)
                    })
            
            session.commit()
            session.close()
            
            logger.info(f"批量添加完成: 成功 {success_count}/{len(documents)}")
            return {
                "success": True,
                "count": success_count,
                "total": len(documents),
                "failed": failed_documents,
                "message": f"成功添加 {success_count} 个文档"
            }
            
        except Exception as e:
            logger.error(f"批量添加失败: {e}")
            return {
                "success": False,
                "count": success_count,
                "total": len(documents),
                "failed": failed_documents,
                "message": f"批量添加失败: {str(e)}"
            }
    
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
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            session = self._get_session()
            
            # 生成查询向量
            query_vector = self._text_to_vector(query)
            
            # 构建查询
            query_obj = session.query(VectorDocument)
            
            # 应用过滤条件
            if filters:
                if "knowledge_base_id" in filters:
                    query_obj = query_obj.filter(
                        VectorDocument.knowledge_base_id == filters["knowledge_base_id"]
                    )
                if "document_id" in filters:
                    query_obj = query_obj.filter(
                        VectorDocument.document_id == filters["document_id"]
                    )
            
            # 获取所有文档
            documents = query_obj.all()
            
            # 计算相似度
            results = []
            for doc in documents:
                if doc.vector:
                    similarity = self._cosine_similarity(query_vector, doc.vector)
                    results.append({
                        "document_id": doc.document_id,
                        "chunk_id": doc.chunk_id,
                        "text": doc.text,
                        "metadata": doc.meta_data,
                        "score": similarity,
                        "knowledge_base_id": doc.knowledge_base_id
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # 返回前 top_k 个结果
            session.close()
            return results[:top_k]
            
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
            session = self._get_session()
            
            # 删除所有相关记录
            session.query(VectorDocument).filter(
                VectorDocument.document_id == document_id
            ).delete()
            
            session.commit()
            session.close()
            
            logger.info(f"文档删除成功: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            document_id: 文档唯一标识
            
        Returns:
            文档信息
        """
        try:
            session = self._get_session()
            
            doc = session.query(VectorDocument).filter(
                VectorDocument.document_id == document_id
            ).first()
            
            if doc:
                result = {
                    "document_id": doc.document_id,
                    "chunk_id": doc.chunk_id,
                    "text": doc.text,
                    "metadata": doc.meta_data,
                    "knowledge_base_id": doc.knowledge_base_id,
                    "chunk_index": doc.chunk_index,
                    "total_chunks": doc.total_chunks
                }
            else:
                result = None
            
            session.close()
            return result
            
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
            session = self._get_session()
            
            # 获取文档数量
            count = session.query(VectorDocument).count()
            
            session.close()
            
            return {
                "healthy": True,
                "message": "SQLite 向量存储运行正常",
                "details": {
                    "total_documents": count,
                    "db_path": self.db_path
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"SQLite 向量存储异常: {str(e)}",
                "details": {
                    "error": str(e),
                    "db_path": self.db_path
                }
            }
    
    def close(self):
        """关闭存储连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("SQLiteVectorStore 连接已关闭")
