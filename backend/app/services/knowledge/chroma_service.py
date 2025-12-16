import chromadb
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ChromaService:
    def __init__(self, storage_path: Optional[str] = None):
        # 前端可配置的存储路径，默认为前端public目录下的knowledge文件夹
        if storage_path is None:
            # 确保使用正确的绝对路径，无论从哪个目录启动
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 计算从当前文件到frontend/public/knowledge/chromadb的绝对路径
            # 路径结构: backend/app/services/knowledge/chroma_service.py -> frontend/public/knowledge/chromadb
            storage_path = os.path.abspath(os.path.join(
                current_dir, 
                "../../../../frontend/public", 
                "knowledge", 
                "chromadb"
            ))
        
        # 确保路径存在
        os.makedirs(storage_path, exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(path=storage_path)
            self.collection = self.client.get_or_create_collection("documents")
            self.available = True
        except Exception as e:
            logger.error(f"ChromaDB初始化失败: {str(e)}")
            self.available = False
            self.collection = None
    
    def add_document(self, document_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """添加文档到向量数据库"""
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，跳过文档添加")
            return
        
        try:
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[document_id]
            )
        except Exception as e:
            logger.error(f"添加文档到向量数据库失败: {str(e)}")
    
    def search_similar(self, query: str, n_results: int = 5, where_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """相似性搜索"""
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，返回空搜索结果")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        try:
            query_params = {
                "query_texts": [query],
                "n_results": n_results
            }
            
            if where_filter:
                query_params["where"] = where_filter
            
            results = self.collection.query(**query_params)
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def delete_document(self, document_id: str) -> None:
        """删除文档"""
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，跳过文档删除")
            return
        
        try:
            self.collection.delete(ids=[document_id])
        except Exception as e:
            logger.error(f"从向量数据库删除文档失败: {str(e)}")
    
    def update_document(self, document_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """更新文档"""
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，跳过文档更新")
            return
        
        try:
            self.collection.update(
                documents=[text],
                metadatas=[metadata],
                ids=[document_id]
            )
        except Exception as e:
            logger.error(f"更新向量数据库文档失败: {str(e)}")
    
    def get_document_count(self) -> int:
        """获取文档数量"""
        if not self.available or self.collection is None:
            return 0
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"获取向量数据库文档数量失败: {str(e)}")
            return 0
    
    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有文档"""
        if not self.available or self.collection is None:
            return []
        
        try:
            results = self.collection.get(limit=limit)
            documents = []
            for i, doc_id in enumerate(results['ids']):
                documents.append({
                    'id': doc_id,
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
            return documents
        except Exception as e:
            logger.error(f"列出向量数据库文档失败: {str(e)}")
            return []
    
    def delete_documents_by_metadata(self, where_filter: Dict[str, Any]) -> None:
        """根据元数据删除文档"""
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，跳过文档删除")
            return
        
        try:
            self.collection.delete(where=where_filter)
        except Exception as e:
            logger.error(f"根据元数据删除文档失败: {str(e)}")