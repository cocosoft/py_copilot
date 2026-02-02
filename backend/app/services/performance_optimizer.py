"""
性能优化服务

实现文件I/O和向量计算的优化，提升系统性能与可扩展性
"""
import asyncio
import aiofiles
import functools
import time
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)


class AsyncFileManager:
    """异步文件管理器"""
    
    def __init__(self, buffer_size: int = 8192):
        """初始化异步文件管理器
        
        Args:
            buffer_size: 缓冲区大小
        """
        self.buffer_size = buffer_size
        self.lock = asyncio.Lock()
        logger.info("异步文件管理器已初始化")
    
    async def read_file(self, file_path: str) -> Optional[str]:
        """异步读取文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        try:
            async with self.lock:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                logger.debug(f"异步读取文件完成: {file_path}")
                return content
        except Exception as e:
            logger.error(f"异步读取文件失败: {file_path}, 错误: {str(e)}")
            return None
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """异步写入文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            file_dir = Path(file_path).parent
            file_dir.mkdir(parents=True, exist_ok=True)
            
            async with self.lock:
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
                logger.debug(f"异步写入文件完成: {file_path}")
                return True
        except Exception as e:
            logger.error(f"异步写入文件失败: {file_path}, 错误: {str(e)}")
            return False
    
    async def append_file(self, file_path: str, content: str) -> bool:
        """异步追加文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            file_dir = Path(file_path).parent
            file_dir.mkdir(parents=True, exist_ok=True)
            
            async with self.lock:
                async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
                    await f.write(content)
                logger.debug(f"异步追加文件完成: {file_path}")
                return True
        except Exception as e:
            logger.error(f"异步追加文件失败: {file_path}, 错误: {str(e)}")
            return False
    
    async def batch_read_files(self, file_paths: List[str]) -> Dict[str, Optional[str]]:
        """批量异步读取文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件内容字典
        """
        tasks = [self.read_file(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks)
        
        return dict(zip(file_paths, results))
    
    async def batch_write_files(self, file_contents: Dict[str, str]) -> Dict[str, bool]:
        """批量异步写入文件
        
        Args:
            file_contents: 文件路径到内容的映射
            
        Returns:
            文件写入状态字典
        """
        tasks = [self.write_file(file_path, content) for file_path, content in file_contents.items()]
        results = await asyncio.gather(*tasks)
        
        return dict(zip(file_contents.keys(), results))


class MemoryCache:
    """内存缓存"""
    
    def __init__(self, max_size: int = 1000, expiration_seconds: int = 3600):
        """初始化内存缓存
        
        Args:
            max_size: 最大缓存项数
            expiration_seconds: 缓存过期时间（秒）
        """
        self.max_size = max_size
        self.expiration_seconds = expiration_seconds
        self.cache = {}
        self.lock = threading.RLock()
        logger.info(f"内存缓存已初始化，最大大小: {max_size}, 过期时间: {expiration_seconds}秒")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            value, timestamp = self.cache[key]
            
            # 检查是否过期
            if time.time() - timestamp > self.expiration_seconds:
                del self.cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any) -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            
        Returns:
            是否成功
        """
        with self.lock:
            # 检查缓存大小
            if len(self.cache) >= self.max_size:
                # 删除最早的缓存项
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                logger.debug(f"缓存已满，删除最早的缓存项: {oldest_key}")
            
            # 设置缓存
            self.cache[key] = (value, time.time())
            logger.debug(f"缓存已设置: {key}")
            return True
    
    def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"缓存已删除: {key}")
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            logger.info("缓存已清空")
    
    def get_size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存项数
        """
        with self.lock:
            return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "expiration_seconds": self.expiration_seconds
            }


class VectorComputationOptimizer:
    """向量计算优化器"""
    
    def __init__(self, batch_size: int = 32, use_caching: bool = True):
        """初始化向量计算优化器
        
        Args:
            batch_size: 批处理大小
            use_caching: 是否使用缓存
        """
        self.batch_size = batch_size
        self.use_caching = use_caching
        self.vector_cache = MemoryCache(max_size=10000, expiration_seconds=7200)
        logger.info(f"向量计算优化器已初始化，批处理大小: {batch_size}, 使用缓存: {use_caching}")
    
    def batch_generate_vectors(self, texts: List[str]) -> List[np.ndarray]:
        """批量生成向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        vectors = []
        
        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i+self.batch_size]
            batch_vectors = self._process_batch(batch_texts)
            vectors.extend(batch_vectors)
        
        return vectors
    
    def _process_batch(self, texts: List[str]) -> List[np.ndarray]:
        """处理批次
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        vectors = []
        
        for text in texts:
            # 检查缓存
            if self.use_caching:
                cache_key = f"vector:{hash(text)}"
                cached_vector = self.vector_cache.get(cache_key)
                if cached_vector is not None:
                    vectors.append(cached_vector)
                    continue
            
            # 生成向量
            vector = self._generate_vector(text)
            vectors.append(vector)
            
            # 缓存向量
            if self.use_caching:
                cache_key = f"vector:{hash(text)}"
                self.vector_cache.set(cache_key, vector)
        
        return vectors
    
    def _generate_vector(self, text: str) -> np.ndarray:
        """生成文本向量
        
        Args:
            text: 文本内容
            
        Returns:
            向量数组
        """
        # 简单的词频向量实现
        # 实际应用中应使用更高级的嵌入模型
        import re
        words = re.findall(r'\w+', text.lower())
        word_freq = {}
        
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 创建固定长度的向量
        vector_size = 512
        vector = np.zeros(vector_size)
        
        for i, (word, freq) in enumerate(word_freq.items()):
            if i < vector_size:
                # 使用哈希值确定词的位置
                word_hash = hash(word) % vector_size
                vector[word_hash] += freq
        
        # 归一化向量
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def batch_cosine_similarity(self, vectors1: List[np.ndarray], vectors2: List[np.ndarray]) -> List[float]:
        """批量计算余弦相似度
        
        Args:
            vectors1: 向量列表1
            vectors2: 向量列表2
            
        Returns:
            相似度列表
        """
        similarities = []
        
        # 分批处理
        for i in range(0, len(vectors1), self.batch_size):
            batch_vectors1 = vectors1[i:i+self.batch_size]
            batch_vectors2 = vectors2[i:i+self.batch_size]
            batch_similarities = self._compute_batch_similarity(batch_vectors1, batch_vectors2)
            similarities.extend(batch_similarities)
        
        return similarities
    
    def _compute_batch_similarity(self, vectors1: List[np.ndarray], vectors2: List[np.ndarray]) -> List[float]:
        """计算批次相似度
        
        Args:
            vectors1: 向量列表1
            vectors2: 向量列表2
            
        Returns:
            相似度列表
        """
        similarities = []
        
        for v1, v2 in zip(vectors1, vectors2):
            # 确保向量长度相同
            min_len = min(len(v1), len(v2))
            v1 = v1[:min_len]
            v2 = v2[:min_len]
            
            # 计算余弦相似度
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 > 0 and norm2 > 0:
                similarity = dot_product / (norm1 * norm2)
            else:
                similarity = 0.0
            
            similarities.append(similarity)
        
        return similarities
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return self.vector_cache.get_stats()


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        """初始化性能优化器"""
        self.async_file_manager = AsyncFileManager()
        self.memory_cache = MemoryCache()
        self.vector_optimizer = VectorComputationOptimizer()
        self.performance_metrics = {
            "file_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "vector_computations": 0,
            "batch_operations": 0
        }
        logger.info("性能优化器已初始化")
    
    def async_file_read(self, file_path: str) -> Optional[str]:
        """异步读取文件（同步接口）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        loop = asyncio.get_event_loop()
        content = loop.run_until_complete(self.async_file_manager.read_file(file_path))
        self.performance_metrics["file_operations"] += 1
        return content
    
    def async_file_write(self, file_path: str, content: str) -> bool:
        """异步写入文件（同步接口）
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功
        """
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(self.async_file_manager.write_file(file_path, content))
        self.performance_metrics["file_operations"] += 1
        return success
    
    def async_file_append(self, file_path: str, content: str) -> bool:
        """异步追加文件（同步接口）
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功
        """
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(self.async_file_manager.append_file(file_path, content))
        self.performance_metrics["file_operations"] += 1
        return success
    
    def batch_file_read(self, file_paths: List[str]) -> Dict[str, Optional[str]]:
        """批量读取文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件内容字典
        """
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.async_file_manager.batch_read_files(file_paths))
        self.performance_metrics["file_operations"] += len(file_paths)
        self.performance_metrics["batch_operations"] += 1
        return results
    
    def batch_file_write(self, file_contents: Dict[str, str]) -> Dict[str, bool]:
        """批量写入文件
        
        Args:
            file_contents: 文件路径到内容的映射
            
        Returns:
            文件写入状态字典
        """
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.async_file_manager.batch_write_files(file_contents))
        self.performance_metrics["file_operations"] += len(file_contents)
        self.performance_metrics["batch_operations"] += 1
        return results
    
    def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        value = self.memory_cache.get(key)
        if value is not None:
            self.performance_metrics["cache_hits"] += 1
        else:
            self.performance_metrics["cache_misses"] += 1
        return value
    
    def set_cache(self, key: str, value: Any) -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            
        Returns:
            是否成功
        """
        return self.memory_cache.set(key, value)
    
    def delete_cache(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        return self.memory_cache.delete(key)
    
    def generate_vector(self, text: str) -> np.ndarray:
        """生成向量
        
        Args:
            text: 文本内容
            
        Returns:
            向量
        """
        vector = self.vector_optimizer._generate_vector(text)
        self.performance_metrics["vector_computations"] += 1
        return vector
    
    def batch_generate_vectors(self, texts: List[str]) -> List[np.ndarray]:
        """批量生成向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        vectors = self.vector_optimizer.batch_generate_vectors(texts)
        self.performance_metrics["vector_computations"] += len(texts)
        self.performance_metrics["batch_operations"] += 1
        return vectors
    
    def compute_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """计算相似度
        
        Args:
            vector1: 向量1
            vector2: 向量2
            
        Returns:
            相似度
        """
        # 确保向量长度相同
        min_len = min(len(vector1), len(vector2))
        vector1 = vector1[:min_len]
        vector2 = vector2[:min_len]
        
        # 计算余弦相似度
        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        
        if norm1 > 0 and norm2 > 0:
            similarity = dot_product / (norm1 * norm2)
        else:
            similarity = 0.0
        
        return similarity
    
    def batch_compute_similarity(self, vectors1: List[np.ndarray], vectors2: List[np.ndarray]) -> List[float]:
        """批量计算相似度
        
        Args:
            vectors1: 向量列表1
            vectors2: 向量列表2
            
        Returns:
            相似度列表
        """
        similarities = self.vector_optimizer.batch_cosine_similarity(vectors1, vectors2)
        self.performance_metrics["batch_operations"] += 1
        return similarities
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            性能指标
        """
        return self.performance_metrics.copy()
    
    def reset_performance_metrics(self):
        """重置性能指标"""
        self.performance_metrics = {
            "file_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "vector_computations": 0,
            "batch_operations": 0
        }
        logger.info("性能指标已重置")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        return {
            "performance_metrics": self.performance_metrics,
            "cache_stats": self.memory_cache.get_stats(),
            "vector_cache_stats": self.vector_optimizer.get_cache_stats()
        }


# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()


# 装饰器：缓存函数结果
def cache_result(cache_key_func=None, expiration_seconds: int = 3600):
    """缓存函数结果的装饰器
    
    Args:
        cache_key_func: 缓存键生成函数
        expiration_seconds: 缓存过期时间
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                # 使用函数名和参数生成缓存键
                args_repr = [repr(arg) for arg in args]
                kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
                cache_key = f"{func.__name__}:{':'.join(args_repr + kwargs_repr)}"
            
            # 检查缓存
            cached_result = performance_optimizer.get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            performance_optimizer.set_cache(cache_key, result)
            
            return result
        
        return wrapper
    
    return decorator


# 装饰器：异步执行
def async_executor(func):
    """异步执行函数的装饰器
    
    Args:
        func: 要异步执行的函数
        
    Returns:
        装饰器函数
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    
    return wrapper
