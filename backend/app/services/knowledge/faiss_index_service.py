#!/usr/bin/env python3
"""
FAISS索引服务

提供高性能的向量索引和相似度搜索功能，
支持多种索引类型和增量更新。
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


@dataclass
class IndexConfig:
    """索引配置"""
    dimension: int = 768  # 向量维度
    index_type: str = "IVF_FLAT"  # 索引类型
    nlist: int = 100  # 倒排列表数量
    nprobe: int = 10  # 搜索时探查的列表数
    metric_type: str = "METRIC_L2"  # 距离度量类型


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    score: float
    metadata: Dict[str, Any]
    vector: Optional[np.ndarray] = None


class FAISSIndexService:
    """
    FAISS索引服务

    提供高效的向量索引和相似度搜索，支持：
    1. 多种索引类型（Flat、IVF、HNSW等）
    2. 增量添加和删除
    3. 持久化和加载
    4. 多线程安全
    """

    def __init__(self, index_name: str = "default", config: IndexConfig = None):
        """
        初始化FAISS索引服务

        Args:
            index_name: 索引名称
            config: 索引配置
        """
        self.index_name = index_name
        self.config = config or IndexConfig()
        self.index = None
        self.id_map = {}  # id -> index映射
        self.metadata = {}  # id -> metadata映射
        self.vectors = {}  # id -> vector映射（用于重建索引）

        self._lock = threading.RLock()
        self._is_trained = False

        # 索引存储路径
        self.index_dir = Path("data/faiss_indexes")
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / f"{index_name}.faiss"
        self.metadata_path = self.index_dir / f"{index_name}_metadata.pkl"

        # 延迟导入FAISS
        self._faiss = None
        self._load_faiss()

        logger.info(f"FAISS索引服务初始化: {index_name}, 维度: {self.config.dimension}")

    def _load_faiss(self):
        """延迟加载FAISS库"""
        if self._faiss is None:
            try:
                import faiss
                self._faiss = faiss
                logger.info("FAISS库加载成功")
            except ImportError:
                logger.warning("FAISS库未安装，将使用回退方法")
                self._faiss = None

    def _create_index(self) -> Any:
        """创建FAISS索引"""
        if self._faiss is None:
            return None

        dimension = self.config.dimension
        index_type = self.config.index_type

        # 根据索引类型创建索引
        if index_type == "FLAT":
            # 精确搜索，适合小数据集
            index = self._faiss.IndexFlatIP(dimension)  # 内积（余弦相似度）

        elif index_type == "IVF_FLAT":
            # 倒排文件索引，平衡速度和精度
            quantizer = self._faiss.IndexFlatIP(dimension)
            index = self._faiss.IndexIVFFlat(
                quantizer, dimension,
                self.config.nlist,
                self._faiss.METRIC_INNER_PRODUCT
            )

        elif index_type == "IVF_PQ":
            # 乘积量化，适合大数据集
            quantizer = self._faiss.IndexFlatIP(dimension)
            index = self._faiss.IndexIVFPQ(
                quantizer, dimension,
                self.config.nlist,  # 倒排列表数
                8,  # 每个向量的字节数
                8   # 子量化器数量
            )

        elif index_type == "HNSW":
            # HNSW图索引，高召回率
            index = self._faiss.IndexHNSWFlat(dimension, 32)
            index.hnsw.efConstruction = 200

        else:
            # 默认使用FLAT
            index = self._faiss.IndexFlatIP(dimension)

        return index

    def initialize(self):
        """初始化索引"""
        with self._lock:
            if self.index is None:
                self.index = self._create_index()
                if self.index:
                    logger.info(f"索引创建成功: {self.config.index_type}")
                else:
                    logger.warning("使用回退索引（无FAISS）")

    def add_vectors(self, ids: List[str], vectors: np.ndarray,
                   metadata: List[Dict[str, Any]] = None) -> bool:
        """
        添加向量到索引

        Args:
            ids: 向量ID列表
            vectors: 向量矩阵 (n, dimension)
            metadata: 元数据列表

        Returns:
            是否添加成功
        """
        with self._lock:
            if len(ids) == 0:
                return True

            # 确保索引已初始化
            if self.index is None:
                self.initialize()

            # 归一化向量（用于余弦相似度）
            vectors = self._normalize_vectors(vectors)

            # 保存向量和元数据
            for i, id in enumerate(ids):
                self.vectors[id] = vectors[i]
                if metadata and i < len(metadata):
                    self.metadata[id] = metadata[i]

            if self._faiss and self.index:
                try:
                    # 训练索引（如果是IVF类型且未训练）
                    if not self._is_trained and hasattr(self.index, 'is_trained'):
                        if not self.index.is_trained:
                            self.index.train(vectors)
                            self._is_trained = True
                            logger.info("索引训练完成")

                    # 添加向量
                    start_idx = len(self.id_map)
                    self.index.add(vectors)

                    # 更新ID映射
                    for i, id in enumerate(ids):
                        self.id_map[id] = start_idx + i

                    logger.info(f"成功添加 {len(ids)} 个向量到索引")
                    return True

                except Exception as e:
                    logger.error(f"添加向量到FAISS索引失败: {e}")
                    return False
            else:
                # 回退方法：仅保存到内存
                for i, id in enumerate(ids):
                    self.id_map[id] = len(self.id_map)
                logger.info(f"使用回退方法添加 {len(ids)} 个向量")
                return True

    def search(self, query_vector: np.ndarray, k: int = 10,
               filter_fn: callable = None) -> List[SearchResult]:
        """
        搜索相似向量

        Args:
            query_vector: 查询向量
            k: 返回结果数量
            filter_fn: 过滤函数

        Returns:
            搜索结果列表
        """
        with self._lock:
            if len(self.id_map) == 0:
                return []

            # 归一化查询向量
            query_vector = self._normalize_vectors(query_vector.reshape(1, -1))

            results = []

            if self._faiss and self.index:
                try:
                    # 设置搜索参数
                    if hasattr(self.index, 'nprobe'):
                        self.index.nprobe = self.config.nprobe

                    # 执行搜索
                    scores, indices = self.index.search(query_vector, k)

                    # 构建结果
                    id_list = list(self.id_map.keys())
                    for i, idx in enumerate(indices[0]):
                        if idx < 0 or idx >= len(id_list):
                            continue

                        id = id_list[idx]
                        score = float(scores[0][i])

                        # 应用过滤
                        if filter_fn and not filter_fn(id, self.metadata.get(id)):
                            continue

                        result = SearchResult(
                            id=id,
                            score=score,
                            metadata=self.metadata.get(id, {}),
                            vector=self.vectors.get(id)
                        )
                        results.append(result)

                except Exception as e:
                    logger.error(f"FAISS搜索失败: {e}")
                    # 回退到暴力搜索
                    results = self._brute_force_search(query_vector[0], k, filter_fn)
            else:
                # 使用暴力搜索
                results = self._brute_force_search(query_vector[0], k, filter_fn)

            return results

    def _brute_force_search(self, query_vector: np.ndarray, k: int,
                           filter_fn: callable = None) -> List[SearchResult]:
        """暴力搜索（回退方法）"""
        results = []

        for id, vector in self.vectors.items():
            # 计算余弦相似度
            score = np.dot(query_vector, vector)

            # 应用过滤
            if filter_fn and not filter_fn(id, self.metadata.get(id)):
                continue

            results.append(SearchResult(
                id=id,
                score=float(score),
                metadata=self.metadata.get(id, {}),
                vector=vector
            ))

        # 按相似度排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:k]

    def delete_vectors(self, ids: List[str]) -> bool:
        """
        从索引中删除向量

        Note: FAISS不直接支持删除，需要重建索引
        """
        with self._lock:
            try:
                # 从映射中删除
                for id in ids:
                    if id in self.id_map:
                        del self.id_map[id]
                    if id in self.metadata:
                        del self.metadata[id]
                    if id in self.vectors:
                        del self.vectors[id]

                # 重建索引
                if self._faiss and self.index:
                    self._rebuild_index()

                logger.info(f"成功删除 {len(ids)} 个向量")
                return True

            except Exception as e:
                logger.error(f"删除向量失败: {e}")
                return False

    def _rebuild_index(self):
        """重建索引"""
        if not self.vectors:
            self.index = self._create_index()
            self._is_trained = False
            return

        # 收集所有向量
        ids = list(self.vectors.keys())
        vectors = np.array([self.vectors[id] for id in ids])

        # 重新创建索引
        self.index = self._create_index()
        self._is_trained = False

        # 重新添加向量
        if self._faiss and self.index:
            if hasattr(self.index, 'train'):
                self.index.train(vectors)
                self._is_trained = True
            self.index.add(vectors)

        # 更新ID映射
        self.id_map = {id: i for i, id in enumerate(ids)}

        logger.info(f"索引重建完成，包含 {len(ids)} 个向量")

    def save(self) -> bool:
        """保存索引到磁盘"""
        with self._lock:
            try:
                # 保存FAISS索引
                if self._faiss and self.index:
                    self._faiss.write_index(self.index, str(self.index_path))

                # 保存元数据和映射
                data = {
                    'id_map': self.id_map,
                    'metadata': self.metadata,
                    'vectors': self.vectors,
                    'config': self.config,
                    'is_trained': self._is_trained
                }

                with open(self.metadata_path, 'wb') as f:
                    pickle.dump(data, f)

                logger.info(f"索引保存成功: {self.index_path}")
                return True

            except Exception as e:
                logger.error(f"保存索引失败: {e}")
                return False

    def load(self) -> bool:
        """从磁盘加载索引"""
        with self._lock:
            try:
                # 检查文件是否存在
                if not self.metadata_path.exists():
                    logger.info("索引文件不存在，创建新索引")
                    self.initialize()
                    return True

                # 加载元数据
                with open(self.metadata_path, 'rb') as f:
                    data = pickle.load(f)

                self.id_map = data['id_map']
                self.metadata = data['metadata']
                self.vectors = data['vectors']
                self.config = data.get('config', self.config)
                self._is_trained = data.get('is_trained', False)

                # 加载FAISS索引
                if self._faiss and self.index_path.exists():
                    self.index = self._faiss.read_index(str(self.index_path))
                    logger.info(f"FAISS索引加载成功，包含 {len(self.id_map)} 个向量")
                else:
                    # 重建索引
                    self._rebuild_index()

                return True

            except Exception as e:
                logger.error(f"加载索引失败: {e}")
                self.initialize()
                return False

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        with self._lock:
            return {
                'index_name': self.index_name,
                'index_type': self.config.index_type,
                'vector_count': len(self.id_map),
                'dimension': self.config.dimension,
                'is_trained': self._is_trained,
                'has_faiss': self._faiss is not None,
                'index_path': str(self.index_path),
                'metadata_count': len(self.metadata)
            }

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """归一化向量"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1  # 避免除零
        return vectors / norms


class MultiIndexService:
    """
    多索引服务

    管理多个FAISS索引，支持按知识库隔离
    """

    def __init__(self):
        self.indexes: Dict[str, FAISSIndexService] = {}
        self._lock = threading.RLock()

    def get_index(self, index_name: str, config: IndexConfig = None) -> FAISSIndexService:
        """获取或创建索引"""
        with self._lock:
            if index_name not in self.indexes:
                self.indexes[index_name] = FAISSIndexService(index_name, config)
                self.indexes[index_name].load()
            return self.indexes[index_name]

    def delete_index(self, index_name: str) -> bool:
        """删除索引"""
        with self._lock:
            if index_name in self.indexes:
                del self.indexes[index_name]

                # 删除文件
                index_dir = Path("data/faiss_indexes")
                index_path = index_dir / f"{index_name}.faiss"
                metadata_path = index_dir / f"{index_name}_metadata.pkl"

                try:
                    if index_path.exists():
                        index_path.unlink()
                    if metadata_path.exists():
                        metadata_path.unlink()
                    return True
                except Exception as e:
                    logger.error(f"删除索引文件失败: {e}")
                    return False
            return True

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有索引的统计信息"""
        with self._lock:
            return {name: index.get_stats() for name, index in self.indexes.items()}


# 单例模式
_multi_index_service = None


def get_multi_index_service() -> MultiIndexService:
    """获取多索引服务单例"""
    global _multi_index_service
    if _multi_index_service is None:
        _multi_index_service = MultiIndexService()
    return _multi_index_service
