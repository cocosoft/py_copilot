"""
ChromaDB服务 - 通过HTTP API调用独立服务
避免在主应用中直接加载PyTorch模型，解决Windows DLL冲突问题
"""
import os
import time
from typing import List, Dict, Any, Optional
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def create_retry_session(
    retries=3,
    backoff_factor=1,
    status_forcelist=(500, 502, 503, 504),
    timeout=60
):
    """
    创建带重试机制的HTTP会话
    
    Args:
        retries: 最大重试次数
        backoff_factor: 重试间隔指数退避因子
        status_forcelist: 需要重试的HTTP状态码
        timeout: 请求超时时间（秒）
    
    Returns:
        requests.Session: 配置好的会话对象
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.timeout = timeout
    return session


class ChromaService:
    """ChromaDB向量数据库服务客户端，通过HTTP API与独立服务通信"""
    
    def __init__(self, server_url: str = "http://localhost:8008", default_collection: str = "documents"):
        """
        初始化ChromaDB服务客户端
        
        Args:
            server_url: ChromaDB独立服务地址
            default_collection: 默认集合名称
        """
        self.server_url = server_url.rstrip('/')
        self.default_collection = default_collection
        self.available = False
        self.session = create_retry_session(retries=3, timeout=60)
        
        # 检查服务是否可用
        self._check_health()
        
        logger.info(f"ChromaDB服务客户端初始化完成，服务器地址: {server_url}")
    
    def _check_health(self) -> bool:
        """检查ChromaDB服务是否可用"""
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.available = data.get("client_initialized", False)
                if self.available:
                    logger.info("ChromaDB独立服务连接成功")
                else:
                    logger.warning("ChromaDB独立服务未初始化")
            else:
                self.available = False
                logger.warning(f"ChromaDB独立服务健康检查失败: {response.status_code}")
        except Exception as e:
            self.available = False
            logger.warning(f"ChromaDB独立服务连接失败: {e}")
        
        return self.available
    
    def add_document(self, document_id: str, text: str, metadata: Dict[str, Any],
                     collection_name: Optional[str] = None) -> bool:
        """
        添加单个文档到向量数据库

        Args:
            document_id: 文档唯一标识
            text: 文档文本内容
            metadata: 文档元数据
            collection_name: 集合名称，默认使用default_collection

        Returns:
            bool: 是否添加成功
        """
        if not self.available and not self._check_health():
            logger.warning("ChromaDB服务不可用，跳过文档添加")
            return False

        collection = collection_name or self.default_collection

        try:
            response = self.session.post(
                f"{self.server_url}/collections/{collection}/documents",
                json={
                    "collection_name": collection,
                    "document_id": document_id,
                    "text": text,
                    "metadata": metadata
                },
                timeout=60
            )

            if response.status_code == 200:
                logger.info(f"文档添加成功: {document_id}")
                return True
            else:
                logger.error(f"文档添加失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"文档添加异常: {e}")
            return False

    def add_documents_batch(self, documents: List[Dict[str, Any]],
                            collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        批量添加文档到向量数据库 - 性能优化版

        Args:
            documents: 文档列表，每个文档包含 id, text, metadata
            collection_name: 集合名称，默认使用default_collection

        Returns:
            Dict: 包含 success (bool) 和 count (int) 的结果
        """
        if not self.available and not self._check_health():
            logger.warning("ChromaDB服务不可用，跳过批量文档添加")
            return {"success": False, "count": 0, "error": "服务不可用"}

        if not documents:
            return {"success": True, "count": 0}

        collection = collection_name or self.default_collection

        try:
            # 准备批量请求数据
            batch_docs = [
                {
                    "id": doc["document_id"],
                    "text": doc["text"],
                    "metadata": doc["metadata"]
                }
                for doc in documents
            ]

            response = self.session.post(
                f"{self.server_url}/collections/{collection}/documents/batch",
                json={
                    "collection_name": collection,
                    "documents": batch_docs
                },
                timeout=180  # 批量操作需要更长的超时时间，增加到180秒
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"批量文档添加成功: {data.get('count', len(documents))} 个")
                return {"success": True, "count": data.get('count', len(documents))}
            else:
                logger.error(f"批量文档添加失败: {response.text}")
                return {"success": False, "count": 0, "error": response.text}
        except Exception as e:
            logger.error(f"批量文档添加异常: {e}")
            return {"success": False, "count": 0, "error": str(e)}
    
    def search_similar(self, query: str, top_k: int = 5, 
                       filters: Optional[Dict[str, Any]] = None,
                       collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            collection_name: 集合名称
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.available and not self._check_health():
            logger.warning("ChromaDB服务不可用，返回空结果")
            return []
        
        collection = collection_name or self.default_collection
        
        try:
            response = self.session.post(
                f"{self.server_url}/collections/{collection}/search",
                json={
                    "collection_name": collection,
                    "query": query,
                    "top_k": top_k,
                    "filters": filters
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                logger.info(f"搜索完成，找到 {len(results)} 个结果")
                return results
            else:
                logger.error(f"搜索失败: {response.text}")
                return []
        except Exception as e:
            logger.error(f"搜索异常: {e}")
            return []
    
    def delete_documents(self, document_ids: Optional[List[str]] = None,
                        filters: Optional[Dict[str, Any]] = None,
                        collection_name: Optional[str] = None) -> bool:
        """
        删除文档
        
        Args:
            document_ids: 要删除的文档ID列表
            filters: 过滤条件
            collection_name: 集合名称
            
        Returns:
            bool: 是否删除成功
        """
        if not self.available and not self._check_health():
            logger.warning("ChromaDB服务不可用，跳过删除")
            return False
        
        collection = collection_name or self.default_collection
        
        try:
            response = self.session.delete(
                f"{self.server_url}/collections/{collection}/documents",
                json={
                    "collection_name": collection,
                    "document_ids": document_ids,
                    "filters": filters
                },
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info("文档删除成功")
                return True
            else:
                logger.error(f"文档删除失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"文档删除异常: {e}")
            return False
    
    def count_documents(self, collection_name: Optional[str] = None) -> int:
        """
        获取文档数量

        Args:
            collection_name: 集合名称

        Returns:
            int: 文档数量
        """
        if not self.available and not self._check_health():
            logger.warning("ChromaDB服务不可用，返回0")
            return 0

        collection = collection_name or self.default_collection

        try:
            response = self.session.get(
                f"{self.server_url}/collections/{collection}/count",
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                logger.info(f"文档数量: {count}")
                return count
            else:
                logger.error(f"获取文档数量失败: {response.text}")
                return 0
        except Exception as e:
            logger.error(f"获取文档数量异常: {e}")
            return 0

    def delete_documents_by_metadata(self, filters: Dict[str, Any],
                                      collection_name: Optional[str] = None) -> int:
        """
        根据元数据删除文档

        Args:
            filters: 过滤条件
            collection_name: 集合名称

        Returns:
            int: 删除的文档数量
        """
        if not self.available and not self._check_health():
            logger.warning("ChromaDB服务不可用，跳过删除")
            return 0

        collection = collection_name or self.default_collection

        try:
            # 先搜索符合条件的文档
            search_response = self.session.post(
                f"{self.server_url}/collections/{collection}/documents/get",
                json={
                    "collection_name": collection,
                    "filters": filters
                },
                timeout=60
            )

            if search_response.status_code != 200:
                logger.error(f"搜索文档失败: {search_response.text}")
                return 0

            search_data = search_response.json()
            doc_ids = search_data.get("ids", [])

            if not doc_ids:
                logger.info("没有找到符合条件的文档")
                return 0

            # 删除这些文档
            delete_response = self.session.delete(
                f"{self.server_url}/collections/{collection}/documents",
                json={
                    "collection_name": collection,
                    "document_ids": doc_ids
                },
                timeout=60
            )

            if delete_response.status_code == 200:
                logger.info(f"成功删除 {len(doc_ids)} 个文档")
                return len(doc_ids)
            else:
                logger.error(f"删除文档失败: {delete_response.text}")
                return 0
        except Exception as e:
            logger.error(f"根据元数据删除文档异常: {e}")
            return 0

    def search_documents_by_metadata(self, filters: Dict[str, Any],
                                      collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        根据元数据搜索文档

        Args:
            filters: 过滤条件
            collection_name: 集合名称

        Returns:
            Dict: 包含 ids, documents, metadatas 的结果字典
        """
        if not self.available and not self._check_health():
            logger.warning("ChromaDB服务不可用，返回空结果")
            return {"ids": [], "documents": [], "metadatas": []}

        collection = collection_name or self.default_collection

        try:
            response = self.session.post(
                f"{self.server_url}/collections/{collection}/documents/get",
                json={
                    "collection_name": collection,
                    "filters": filters
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"根据元数据搜索完成，找到 {len(data.get('ids', []))} 个结果")
                return data
            else:
                logger.error(f"根据元数据搜索失败: {response.text}")
                return {"ids": [], "documents": [], "metadatas": []}
        except Exception as e:
            logger.error(f"根据元数据搜索异常: {e}")
            return {"ids": [], "documents": [], "metadatas": []}
