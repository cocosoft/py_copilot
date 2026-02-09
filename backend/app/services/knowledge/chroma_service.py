import chromadb
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ChromaService:
    def __init__(self, storage_path: Optional[str] = None, default_collection: str = "documents"):
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
        self.default_collection = default_collection
        self.client = None
        self.collections = {}  # 存储多个集合
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
            # 初始化默认集合
            self.collections[self.default_collection] = self.client.get_or_create_collection(self.default_collection)
            self.available = True
            logger.info("ChromaDB向量数据库加载成功")
        except Exception as e:
            logger.error(f"ChromaDB初始化失败: {str(e)}")
            self.available = False
            self.collections = {}
        finally:
            self.initialized = True
    
    def _get_collection(self, collection_name: Optional[str] = None):
        """获取指定的集合，如果不存在则创建"""
        self._initialize()
        if not self.available:
            return None
        
        target_collection = collection_name or self.default_collection
        if target_collection not in self.collections:
            self.collections[target_collection] = self.client.get_or_create_collection(target_collection)
        
        return self.collections[target_collection]
    
    def add_document(self, document_id: str, text: str, metadata: Dict[str, Any], collection_name: Optional[str] = None) -> None:
        """添加文档到向量数据库"""
        collection = self._get_collection(collection_name)
        if not collection:
            logger.warning("ChromaDB不可用，跳过文档添加")
            return
        
        try:
            collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[document_id]
            )
        except Exception as e:
            logger.error(f"添加文档到向量数据库失败: {str(e)}")
    
    def search_similar(self, query: str, n_results: int = 5, where_filter: Optional[Dict[str, Any]] = None, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """相似性搜索"""
        collection = self._get_collection(collection_name)
        if not collection:
            logger.warning("ChromaDB不可用，返回空搜索结果")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        try:
            query_params = {
                "query_texts": [query],
                "n_results": n_results
            }
            
            if where_filter:
                query_params["where"] = where_filter
            
            results = collection.query(**query_params)
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def delete_document(self, document_id: str, collection_name: Optional[str] = None) -> None:
        """删除文档"""
        collection = self._get_collection(collection_name)
        if not collection:
            logger.warning("ChromaDB不可用，跳过文档删除")
            return
        
        try:
            collection.delete(ids=[document_id])
        except Exception as e:
            logger.error(f"从向量数据库删除文档失败: {str(e)}")
    
    def update_document(self, document_id: str, text: str, metadata: Dict[str, Any], collection_name: Optional[str] = None) -> None:
        """更新文档"""
        collection = self._get_collection(collection_name)
        if not collection:
            logger.warning("ChromaDB不可用，跳过文档更新")
            return
        
        try:
            collection.update(
                documents=[text],
                metadatas=[metadata],
                ids=[document_id]
            )
        except Exception as e:
            logger.error(f"更新向量数据库文档失败: {str(e)}")
    
    def get_document_count(self, collection_name: Optional[str] = None) -> int:
        """获取文档数量"""
        try:
            collection = self._get_collection(collection_name)
            if not collection:
                return 0
            
            # 尝试获取文档数量，添加超时保护
            import time
            start_time = time.time()
            count = collection.count()
            elapsed = time.time() - start_time
            if elapsed > 1:
                logger.warning(f"获取向量数据库文档数量耗时较长: {elapsed:.2f}秒")
            return count
        except Exception as e:
            logger.error(f"获取向量数据库文档数量失败: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return 0
    
    def list_documents(self, limit: int = 100, collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有文档"""
        collection = self._get_collection(collection_name)
        if not collection:
            return []
        
        try:
            results = collection.get(limit=limit)
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
    
    def delete_documents_by_metadata(self, where_filter: Dict[str, Any], collection_name: Optional[str] = None) -> int:
        """根据元数据删除文档，返回删除的文档数量"""
        collection = self._get_collection(collection_name)
        if not collection:
            logger.warning("ChromaDB不可用，跳过文档删除")
            return 0
        
        try:
            # 先查询所有匹配的文档
            matching_docs = collection.get(where=where_filter, limit=10000)  # 增加limit以获取所有匹配文档
            
            if not matching_docs or not matching_docs.get('ids'):
                logger.info(f"没有找到匹配元数据 {where_filter} 的文档")
                return 0
            
            doc_ids = matching_docs['ids']
            logger.info(f"找到 {len(doc_ids)} 个匹配的文档，准备删除")
            
            # 批量删除（ChromaDB支持一次性删除多个ID）
            collection.delete(ids=doc_ids)
            
            logger.info(f"成功从向量数据库删除 {len(doc_ids)} 个文档")
            return len(doc_ids)
            
        except Exception as e:
            logger.error(f"根据元数据删除文档失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return 0
    
    def search_documents_by_metadata(self, where_filter: Dict[str, Any], limit: int = 100, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """根据元数据查询文档"""
        collection = self._get_collection(collection_name)
        if not collection:
            logger.warning("ChromaDB不可用，返回空搜索结果")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]]}
        
        try:
            results = collection.get(where=where_filter, limit=limit)
            return results
        except Exception as e:
            logger.error(f"根据元数据查询文档失败: {str(e)}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]]}
    
    def delete_all_documents(self, collection_name: Optional[str] = None) -> None:
        """删除所有文档"""
        collection = self._get_collection(collection_name)
        if not collection:
            logger.warning("ChromaDB不可用，跳过文档删除")
            return
        
        try:
            # 获取所有文档的ID
            all_documents = collection.get()
            if all_documents['ids']:
                collection.delete(ids=all_documents['ids'])
                logger.info(f"向量数据库所有 {len(all_documents['ids'])} 个文档已成功删除")
            else:
                logger.info("向量数据库已经是空的")
        except Exception as e:
            logger.error(f"删除向量数据库所有文档失败: {str(e)}")