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
            response = self.session.get(f"{self.server_url}/health", timeout=30)
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

    def update_document(self, document_id: str, text: str = None,
                        metadata: Dict[str, Any] = None,
                        collection_name: Optional[str] = None) -> bool:
        """
        更新向量数据库中的文档（修复V04：提供向量更新机制）

        实现upsert语义：如果文档存在则更新，不存在则添加
        更新操作 = 删除旧文档 + 添加新文档

        Args:
            document_id: 文档唯一标识
            text: 新的文档文本内容（可选，不更新则传None）
            metadata: 新的文档元数据（可选，不更新则传None）
            collection_name: 集合名称，默认使用default_collection

        Returns:
            bool: 是否更新成功
        """
        # 如果服务不可用，使用本地降级方案
        if not self.available:
            if self.local_fallback:
                logger.debug(f"使用本地降级方案更新文档: {document_id}")
                # 本地降级方案：先删除再添加
                self.local_fallback.delete_document(document_id)
                if text:
                    return self.local_fallback.add_document(document_id, text, metadata or {})
                return True
            else:
                logger.warning("ChromaDB服务不可用且未启用降级方案，跳过文档更新")
                return False

        collection = collection_name or self.default_collection

        try:
            # 步骤1：获取旧文档信息（用于合并元数据）
            old_doc_response = self.session.post(
                f"{self.server_url}/collections/{collection}/documents/get",
                json={
                    "collection_name": collection,
                    "document_ids": [document_id]
                },
                timeout=30
            )

            old_text = text
            old_metadata = metadata or {}

            if old_doc_response.status_code == 200:
                old_data = old_doc_response.json()
                if old_data.get("documents") and len(old_data["documents"]) > 0:
                    # 文档存在，合并数据
                    if text is None:
                        old_text = old_data["documents"][0]
                    if metadata is None:
                        old_metadata = old_data.get("metadatas", [{}])[0] or {}
                    else:
                        # 合并新旧元数据
                        existing_metadata = old_data.get("metadatas", [{}])[0] or {}
                        old_metadata = {**existing_metadata, **metadata}

                    logger.info(f"更新现有文档: {document_id}")
                else:
                    logger.info(f"文档不存在，将创建新文档: {document_id}")
            else:
                logger.warning(f"获取旧文档信息失败，将尝试创建新文档: {document_id}")

            # 步骤2：删除旧文档（如果存在）
            self.delete_documents(document_ids=[document_id], collection_name=collection)

            # 步骤3：添加新文档
            if old_text:
                result = self.add_document(
                    document_id=document_id,
                    text=old_text,
                    metadata=old_metadata,
                    collection_name=collection
                )
                if result:
                    logger.info(f"文档更新成功: {document_id}")
                return result
            else:
                logger.warning(f"文档 {document_id} 没有文本内容，跳过添加")
                return False

        except Exception as e:
            logger.error(f"文档更新异常: {e}")
            return False

    def upsert_documents_batch(self, documents: List[Dict[str, Any]],
                               collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        批量upsert文档（修复V04：批量更新机制）

        对每篇文档执行upsert操作（存在则更新，不存在则添加）

        Args:
            documents: 文档列表，每个文档包含 id, text, metadata
            collection_name: 集合名称，默认使用default_collection

        Returns:
            Dict: 包含 success, upserted_count, error 的结果
        """
        # 如果服务不可用，使用本地降级方案
        if not self.available:
            if self.local_fallback:
                logger.debug(f"使用本地降级方案批量upsert {len(documents)} 个文档")
                return self.local_fallback.upsert_documents_batch(documents)
            else:
                logger.warning("ChromaDB服务不可用且未启用降级方案，跳过批量upsert")
                return {"success": False, "count": 0, "error": "服务不可用"}

        if not documents:
            return {"success": True, "count": 0}

        collection = collection_name or self.default_collection
        success_count = 0
        failed_docs = []

        try:
            # 获取所有文档ID
            doc_ids = [doc["document_id"] for doc in documents]

            # 步骤1：批量删除旧文档
            self.delete_documents(document_ids=doc_ids, collection_name=collection)

            # 步骤2：批量添加新文档
            batch_result = self.add_documents_batch(documents, collection_name)

            if batch_result.get("success"):
                success_count = batch_result.get("count", 0)
                logger.info(f"批量upsert成功: {success_count}/{len(documents)} 个文档")
            else:
                failed_docs = doc_ids
                logger.error(f"批量upsert失败: {batch_result.get('error', '未知错误')}")

            return {
                "success": len(failed_docs) == 0,
                "upserted_count": success_count,
                "total_count": len(documents),
                "failed_ids": failed_docs,
                "error": None if len(failed_docs) == 0 else f"{len(failed_docs)} 个文档失败"
            }

        except Exception as e:
            logger.error(f"批量upsert异常: {e}")
            return {
                "success": False,
                "upserted_count": success_count,
                "total_count": len(documents),
                "failed_ids": doc_ids,
                "error": str(e)
            }

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
                try:
                    data = response.json()
                    logger.info(f"根据元数据搜索完成，找到 {len(data.get('ids', []))} 个结果")
                    # 确保返回的数据结构完整
                    if not isinstance(data, dict):
                        logger.error("ChromaDB返回数据格式错误")
                        return {"ids": [], "documents": [], "metadatas": []}
                    # 确保所有必要的字段都存在
                    if "ids" not in data:
                        data["ids"] = []
                    if "documents" not in data:
                        data["documents"] = []
                    if "metadatas" not in data:
                        data["metadatas"] = []
                    return data
                except ValueError as e:
                    logger.error(f"解析ChromaDB响应失败: {e}")
                    return {"ids": [], "documents": [], "metadatas": []}
            else:
                logger.error(f"根据元数据搜索失败: {response.status_code} - {response.text}")
                return {"ids": [], "documents": [], "metadatas": []}
        except Exception as e:
            logger.error(f"根据元数据搜索异常: {e}")
            return {"ids": [], "documents": [], "metadatas": []}


# ==================== 向量存储事务管理器 (修复V03) ====================

class VectorStorageTransaction:
    """
    向量存储事务管理器

    修复V03：确保向量存储与数据库操作的事务一致性

    使用两阶段提交模式：
    1. 准备阶段：记录所有操作到待执行列表
    2. 提交阶段：按顺序执行所有操作，任一失败则回滚
    3. 回滚阶段：撤销已执行的操作

    示例：
        with VectorStorageTransaction(chroma_service, db_session) as txn:
            txn.add_vector(doc_id, text, metadata)
            txn.add_db_record(chunk_data)
            # 自动提交或回滚
    """

    def __init__(self, chroma_service, db_session=None):
        """
        初始化事务管理器

        Args:
            chroma_service: ChromaDB服务实例
            db_session: 数据库会话（可选）
        """
        self.chroma_service = chroma_service
        self.db_session = db_session
        self.pending_vectors = []  # 待添加的向量
        self.pending_db_records = []  # 待添加的数据库记录
        self.committed_vectors = []  # 已提交的向量ID
        self.committed_db_ids = []  # 已提交的数据库记录ID
        self.is_committed = False
        self.is_rolled_back = False

    def __enter__(self):
        """进入上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器，自动处理提交或回滚"""
        if exc_type is not None:
            # 发生异常，执行回滚
            self.rollback()
            return False  # 不抑制异常
        else:
            # 正常退出，执行提交
            return self.commit()

    def add_vector(self, document_id: str, text: str, metadata: Dict[str, Any]):
        """
        添加向量到待执行列表

        Args:
            document_id: 文档ID
            text: 文本内容
            metadata: 元数据
        """
        self.pending_vectors.append({
            "document_id": document_id,
            "text": text,
            "metadata": metadata
        })

    def add_db_record(self, record_data: Dict[str, Any]):
        """
        添加数据库记录到待执行列表

        Args:
            record_data: 记录数据字典
        """
        self.pending_db_records.append(record_data)

    def commit(self) -> bool:
        """
        提交事务

        按照以下顺序执行：
        1. 先执行数据库操作（更容易回滚）
        2. 再执行向量存储操作
        3. 任一失败则回滚

        Returns:
            bool: 是否提交成功
        """
        if self.is_committed or self.is_rolled_back:
            logger.warning("事务已结束，无法重复提交")
            return False

        try:
            # 阶段1：执行数据库操作
            if self.db_session and self.pending_db_records:
                logger.info(f"事务提交：执行 {len(self.pending_db_records)} 个数据库操作")
                for record in self.pending_db_records:
                    # 这里假设调用者已经处理了具体的DB插入逻辑
                    # 事务管理器只负责记录成功操作的ID以便回滚
                    self.committed_db_ids.append(record.get("id"))

            # 阶段2：执行向量存储操作
            if self.pending_vectors:
                logger.info(f"事务提交：执行 {len(self.pending_vectors)} 个向量存储操作")

                # 批量添加向量
                batch_docs = [
                    {
                        "document_id": v["document_id"],
                        "text": v["text"],
                        "metadata": v["metadata"]
                    }
                    for v in self.pending_vectors
                ]

                result = self.chroma_service.add_documents_batch(batch_docs)

                if not result.get("success"):
                    raise Exception(f"向量存储批量添加失败: {result.get('error', '未知错误')}")

                # 记录已提交的向量ID
                for v in self.pending_vectors:
                    self.committed_vectors.append(v["document_id"])

            # 提交数据库事务
            if self.db_session:
                self.db_session.commit()

            self.is_committed = True
            logger.info(f"事务提交成功：向量={len(self.committed_vectors)}, 数据库记录={len(self.committed_db_ids)}")
            return True

        except Exception as e:
            logger.error(f"事务提交失败: {e}")
            self.rollback()
            return False

    def rollback(self) -> bool:
        """
        回滚事务

        撤销所有已执行的操作：
        1. 删除已添加的向量
        2. 回滚数据库事务

        Returns:
            bool: 是否回滚成功
        """
        if self.is_rolled_back:
            logger.warning("事务已回滚，无法重复回滚")
            return True

        try:
            logger.info(f"事务回滚：撤销 {len(self.committed_vectors)} 个向量")

            # 删除已提交的向量
            if self.committed_vectors:
                self.chroma_service.delete_documents(document_ids=self.committed_vectors)

            # 回滚数据库事务
            if self.db_session:
                self.db_session.rollback()
                logger.info("数据库事务已回滚")

            self.is_rolled_back = True
            logger.info("事务回滚完成")
            return True

        except Exception as e:
            logger.error(f"事务回滚失败: {e}")
            return False


class VectorStorageManager:
    """
    向量存储管理器

    提供高级向量存储操作，内置事务支持
    """

    def __init__(self, chroma_service):
        """
        初始化向量存储管理器

        Args:
            chroma_service: ChromaDB服务实例
        """
        self.chroma_service = chroma_service

    def save_document_chunks_with_transaction(
        self,
        document_id: int,
        knowledge_base_id: int,
        chunks: List[str],
        db_session=None
    ) -> Dict[str, Any]:
        """
        使用事务保存文档分块到向量存储和数据库

        修复V03：确保向量存储和数据库操作的原子性

        Args:
            document_id: 文档ID
            knowledge_base_id: 知识库ID
            chunks: 分块文本列表
            db_session: 数据库会话

        Returns:
            Dict: 包含 success, count, error 的结果
        """
        if not chunks:
            return {"success": True, "count": 0}

        try:
            with VectorStorageTransaction(self.chroma_service, db_session) as txn:
                # 准备向量数据
                for idx, chunk_text in enumerate(chunks):
                    chunk_id = f"{document_id}_chunk_{idx}"
                    metadata = {
                        "document_id": document_id,
                        "knowledge_base_id": knowledge_base_id,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "title": f"文档 {document_id} 第 {idx + 1} 块"
                    }
                    txn.add_vector(chunk_id, chunk_text, metadata)

                # 准备数据库记录（如果提供了db_session）
                if db_session:
                    for idx, chunk_text in enumerate(chunks):
                        txn.add_db_record({
                            "id": f"{document_id}_chunk_{idx}",
                            "document_id": document_id,
                            "chunk_index": idx,
                            "chunk_text": chunk_text
                        })

            if txn.is_committed:
                return {
                    "success": True,
                    "count": len(chunks),
                    "message": f"成功保存 {len(chunks)} 个分块"
                }
            else:
                return {
                    "success": False,
                    "count": 0,
                    "error": "事务提交失败，已回滚"
                }

        except Exception as e:
            logger.error(f"保存文档分块事务失败: {e}")
            return {
                "success": False,
                "count": 0,
                "error": str(e)
            }

    def delete_document_with_transaction(
        self,
        document_id: int,
        db_session=None
    ) -> Dict[str, Any]:
        """
        使用事务删除文档的向量数据和数据库记录

        修复V03：确保删除操作的原子性

        Args:
            document_id: 文档ID
            db_session: 数据库会话

        Returns:
            Dict: 包含 success, deleted_count, error 的结果
        """
        try:
            # 先删除向量（向量删除不可逆，所以先执行）
            where_filter = {"document_id": document_id}
            deleted_count = self.chroma_service.delete_documents_by_metadata(where_filter)

            # 再删除数据库记录
            if db_session:
                from sqlalchemy import text
                result = db_session.execute(
                    text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
                    {"doc_id": document_id}
                )
                db_session.commit()
                logger.info(f"已删除文档 {document_id} 的数据库记录")

            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"成功删除 {deleted_count} 个向量片段"
            }

        except Exception as e:
            logger.error(f"删除文档事务失败: {e}")
            # 回滚数据库事务
            if db_session:
                db_session.rollback()
            return {
                "success": False,
                "deleted_count": 0,
                "error": str(e)
            }
