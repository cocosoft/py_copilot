"""
知识图谱缓存服务

提供知识图谱构建结果的缓存，避免重复构建
"""
import time
import threading
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class KnowledgeGraphCache:
    """知识图谱缓存服务"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, ttl_seconds: int = 3600):
        if self._initialized:
            return

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()
        self._ttl_seconds = ttl_seconds
        self._initialized = True

        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        logger.info(f"知识图谱缓存服务初始化完成，TTL: {ttl_seconds}秒")

    def _generate_cache_key(self, document_id: int, content_hash: Optional[str] = None) -> str:
        """生成缓存键"""
        if content_hash:
            return f"doc_{document_id}_{content_hash}"
        return f"doc_{document_id}"

    def _generate_kb_cache_key(self, knowledge_base_id: int, version_hash: Optional[str] = None) -> str:
        """生成知识库缓存键"""
        if version_hash:
            return f"kb_{knowledge_base_id}_{version_hash}"
        return f"kb_{knowledge_base_id}"

    def get(self, document_id: int, content_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取缓存的知识图谱

        @param document_id: 文档ID
        @param content_hash: 内容哈希（可选，用于验证缓存是否过期）
        @returns: 缓存的图谱数据，如果不存在或已过期返回None
        """
        cache_key = self._generate_cache_key(document_id, content_hash)

        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if not cached:
                return None

            # 检查是否过期
            cached_time = datetime.fromisoformat(cached["cached_at"])
            if datetime.now() - cached_time > timedelta(seconds=self._ttl_seconds):
                # 过期，删除缓存
                del self._cache[cache_key]
                return None

            logger.debug(f"知识图谱缓存命中: {cache_key}")
            return cached["data"]

    def set(self, document_id: int, graph_data: Dict[str, Any],
            content_hash: Optional[str] = None) -> None:
        """
        设置知识图谱缓存

        @param document_id: 文档ID
        @param graph_data: 图谱数据
        @param content_hash: 内容哈希（可选）
        """
        cache_key = self._generate_cache_key(document_id, content_hash)

        with self._cache_lock:
            self._cache[cache_key] = {
                "data": graph_data,
                "cached_at": datetime.now().isoformat(),
                "document_id": document_id
            }

        logger.debug(f"知识图谱缓存已设置: {cache_key}")

    def invalidate(self, document_id: int) -> None:
        """
        使指定文档的缓存失效

        @param document_id: 文档ID
        """
        with self._cache_lock:
            # 删除所有与该文档相关的缓存
            keys_to_delete = [
                key for key in self._cache.keys()
                if key.startswith(f"doc_{document_id}")
            ]
            for key in keys_to_delete:
                del self._cache[key]

        logger.debug(f"知识图谱缓存已失效: doc_{document_id}")

    def get_kb_graph(self, knowledge_base_id: int, version_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取缓存的知识库知识图谱

        @param knowledge_base_id: 知识库ID
        @param version_hash: 版本哈希（可选，用于验证缓存是否过期）
        @returns: 缓存的图谱数据，如果不存在或已过期返回None
        """
        cache_key = self._generate_kb_cache_key(knowledge_base_id, version_hash)

        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if not cached:
                return None

            # 检查是否过期
            cached_time = datetime.fromisoformat(cached["cached_at"])
            if datetime.now() - cached_time > timedelta(seconds=self._ttl_seconds):
                # 过期，删除缓存
                del self._cache[cache_key]
                return None

            logger.debug(f"知识库知识图谱缓存命中: {cache_key}")
            return cached["data"]

    def set_kb_graph(self, knowledge_base_id: int, graph_data: Dict[str, Any],
                     version_hash: Optional[str] = None) -> None:
        """
        设置知识库知识图谱缓存

        @param knowledge_base_id: 知识库ID
        @param graph_data: 图谱数据
        @param version_hash: 版本哈希（可选）
        """
        cache_key = self._generate_kb_cache_key(knowledge_base_id, version_hash)

        with self._cache_lock:
            self._cache[cache_key] = {
                "data": graph_data,
                "cached_at": datetime.now().isoformat(),
                "knowledge_base_id": knowledge_base_id
            }

        logger.debug(f"知识库知识图谱缓存已设置: {cache_key}")

    def invalidate_kb_graph(self, knowledge_base_id: int) -> None:
        """
        使指定知识库的缓存失效

        @param knowledge_base_id: 知识库ID
        """
        with self._cache_lock:
            # 删除所有与该知识库相关的缓存
            keys_to_delete = [
                key for key in self._cache.keys()
                if key.startswith(f"kb_{knowledge_base_id}")
            ]
            for key in keys_to_delete:
                del self._cache[key]

        logger.debug(f"知识库知识图谱缓存已失效: kb_{knowledge_base_id}")

    def invalidate_all(self) -> None:
        """使所有缓存失效"""
        with self._cache_lock:
            self._cache.clear()

        logger.info("所有知识图谱缓存已清除")

    def _cleanup_loop(self):
        """清理过期缓存的循环"""
        while True:
            try:
                time.sleep(300)  # 每5分钟清理一次
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"清理知识图谱缓存失败: {e}")

    def _cleanup_expired(self):
        """清理过期的缓存项"""
        expired_time = datetime.now() - timedelta(seconds=self._ttl_seconds)

        with self._cache_lock:
            expired_keys = [
                key for key, value in self._cache.items()
                if datetime.fromisoformat(value["cached_at"]) < expired_time
            ]
            for key in expired_keys:
                del self._cache[key]

        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 条过期的知识图谱缓存")


# 全局实例
knowledge_graph_cache = KnowledgeGraphCache(ttl_seconds=3600)  # 1小时缓存
