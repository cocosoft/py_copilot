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
            # 获取backend目录
            backend_dir = os.path.abspath(os.path.join(current_dir, "../../../.."))  # 从当前文件向上4级: knowledge -> services -> app -> backend
            # 获取项目根目录（backend的父目录）
            project_root = os.path.abspath(os.path.join(backend_dir, ".."))
            # 构建完整的存储路径
            storage_path = os.path.join(
                project_root, 
                "frontend",
                "public",
                "knowledges", 
                "chromadb"
            )
            storage_path = os.path.normpath(storage_path)  # 规范化路径
        
        self.storage_path = storage_path
        self.client = None
        self.collection = None
        self.available = False
        self.initialized = False
        
        logger.info("ChromaDB服务初始化完成，向量数据库将在首次使用时加载")
    
    def _initialize(self):
        """延迟初始化ChromaDB"""
        if self.initialized:
            return
            
        try:
            # 确保路径存在
            os.makedirs(self.storage_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=self.storage_path)
            self.collection = self.client.get_or_create_collection("documents")
            self.available = True
            logger.info("ChromaDB向量数据库加载成功")
        except Exception as e:
            logger.error(f"ChromaDB初始化失败: {str(e)}")
            self.available = False
            self.collection = None
        finally:
            self.initialized = True
    
    def add_document(self, document_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """添加文档到向量数据库"""
        self._initialize()
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
        self._initialize()
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
        self._initialize()
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，跳过文档删除")
            return
        
        try:
            self.collection.delete(ids=[document_id])
        except Exception as e:
            logger.error(f"从向量数据库删除文档失败: {str(e)}")
    
    def update_document(self, document_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """更新文档"""
        self._initialize()
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
        self._initialize()
        if not self.available or self.collection is None:
            return 0
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"获取向量数据库文档数量失败: {str(e)}")
            return 0
    
    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有文档"""
        self._initialize()
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
        self._initialize()
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，跳过文档删除")
            return
        
        try:
            self.collection.delete(where=where_filter)
        except Exception as e:
            logger.error(f"根据元数据删除文档失败: {str(e)}")
    
    def search_documents_by_metadata(self, where_filter: Dict[str, Any], limit: int = 100) -> Dict[str, Any]:
        """根据元数据查询文档"""
        self._initialize()
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，返回空搜索结果")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]]}
        
        try:
            results = self.collection.get(where=where_filter, limit=limit)
            return results
        except Exception as e:
            logger.error(f"根据元数据查询文档失败: {str(e)}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]]}
    
    def delete_all_documents(self) -> None:
        """删除所有文档"""
        self._initialize()
        if not self.available or self.collection is None:
            logger.warning("ChromaDB不可用，跳过文档删除")
            return
        
        try:
            # 获取所有文档的ID
            all_documents = self.collection.get()
            if all_documents['ids']:
                self.collection.delete(ids=all_documents['ids'])
                logger.info(f"向量数据库所有 {len(all_documents['ids'])} 个文档已成功删除")
            else:
                logger.info("向量数据库已经是空的")
        except Exception as e:
            logger.error(f"删除向量数据库所有文档失败: {str(e)}")