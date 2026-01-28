"""
知识库性能优化器

实现知识库系统的性能优化，包括缓存机制、检索优化、大文档处理等。
"""
import time
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from datetime import datetime, timedelta
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueryCache:
    """查询缓存管理器"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """初始化查询缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存生存时间（秒）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.lock = threading.RLock()
    
    def _generate_cache_key(self, query: str, **kwargs) -> str:
        """生成缓存键
        
        Args:
            query: 查询文本
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        key_parts = [query]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}={v}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, **kwargs) -> Optional[Any]:
        """获取缓存结果
        
        Args:
            query: 查询文本
            **kwargs: 其他参数
            
        Returns:
            缓存结果，如果不存在或过期则返回None
        """
        with self.lock:
            cache_key = self._generate_cache_key(query, **kwargs)
            
            if cache_key not in self.cache:
                return None
            
            # 检查是否过期
            access_time = self.access_times.get(cache_key)
            if access_time and datetime.now() - access_time > timedelta(seconds=self.ttl_seconds):
                self._remove(cache_key)
                return None
            
            # 更新访问时间
            self.access_times[cache_key] = datetime.now()
            
            return self.cache[cache_key]
    
    def set(self, query: str, result: Any, **kwargs) -> None:
        """设置缓存结果
        
        Args:
            query: 查询文本
            result: 缓存结果
            **kwargs: 其他参数
        """
        with self.lock:
            cache_key = self._generate_cache_key(query, **kwargs)
            
            # 检查缓存大小，如果超过限制则清理最旧的条目
            if len(self.cache) >= self.max_size:
                self._cleanup_old_entries()
            
            self.cache[cache_key] = result
            self.access_times[cache_key] = datetime.now()
    
    def _remove(self, cache_key: str) -> None:
        """移除缓存条目
        
        Args:
            cache_key: 缓存键
        """
        if cache_key in self.cache:
            del self.cache[cache_key]
        if cache_key in self.access_times:
            del self.access_times[cache_key]
    
    def _cleanup_old_entries(self) -> None:
        """清理最旧的缓存条目"""
        if not self.access_times:
            return
        
        # 找到最旧的访问时间
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove(oldest_key)
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息
        """
        with self.lock:
            return {
                "cache_size": len(self.cache),
                "max_size": self.max_size,
                "utilization": len(self.cache) / self.max_size if self.max_size > 0 else 0,
                "oldest_entry": min(self.access_times.values()) if self.access_times else None,
                "newest_entry": max(self.access_times.values()) if self.access_times else None
            }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.metrics = defaultdict(list)
        self.lock = threading.RLock()
    
    def record_metric(self, metric_name: str, value: float, metadata: Dict[str, Any] = None) -> None:
        """记录性能指标
        
        Args:
            metric_name: 指标名称
            value: 指标值
            metadata: 元数据
        """
        with self.lock:
            timestamp = datetime.now()
            metric_data = {
                "timestamp": timestamp,
                "value": value,
                "metadata": metadata or {}
            }
            self.metrics[metric_name].append(metric_data)
            
            # 保持最近1000个记录
            if len(self.metrics[metric_name]) > 1000:
                self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def get_metric_stats(self, metric_name: str, time_window: timedelta = None) -> Dict[str, Any]:
        """获取指标统计信息
        
        Args:
            metric_name: 指标名称
            time_window: 时间窗口
            
        Returns:
            统计信息
        """
        with self.lock:
            if metric_name not in self.metrics:
                return {}
            
            metric_data = self.metrics[metric_name]
            
            # 应用时间窗口过滤
            if time_window:
                cutoff_time = datetime.now() - time_window
                metric_data = [m for m in metric_data if m["timestamp"] >= cutoff_time]
            
            if not metric_data:
                return {}
            
            values = [m["value"] for m in metric_data]
            
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p95": self._calculate_percentile(values, 95),
                "p99": self._calculate_percentile(values, 99)
            }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """计算百分位数
        
        Args:
            values: 值列表
            percentile: 百分位数
            
        Returns:
            百分位数值
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_values):
            return sorted_values[f] + c * (sorted_values[f + 1] - sorted_values[f])
        else:
            return sorted_values[f]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标统计信息
        
        Returns:
            所有指标统计
        """
        with self.lock:
            stats = {}
            for metric_name in self.metrics.keys():
                stats[metric_name] = self.get_metric_stats(metric_name)
            return stats


class OptimizedRetrievalService:
    """优化后的检索服务"""
    
    def __init__(self, original_retrieval_service):
        """初始化优化检索服务
        
        Args:
            original_retrieval_service: 原始检索服务实例
        """
        self.original_service = original_retrieval_service
        self.query_cache = QueryCache(max_size=500, ttl_seconds=1800)  # 30分钟TTL
        self.performance_monitor = PerformanceMonitor()
        self.cache_hits = 0
        self.cache_misses = 0
    
    def search_documents(self, query: str, limit: int = 10, knowledge_base_id: int = None) -> List[Dict[str, Any]]:
        """优化后的文档搜索
        
        Args:
            query: 查询文本
            limit: 结果数量限制
            knowledge_base_id: 知识库ID
            
        Returns:
            搜索结果
        """
        start_time = time.time()
        
        # 检查缓存
        cache_key_params = {"limit": limit, "knowledge_base_id": knowledge_base_id}
        cached_result = self.query_cache.get(query, **cache_key_params)
        
        if cached_result is not None:
            self.cache_hits += 1
            execution_time = time.time() - start_time
            
            # 记录性能指标
            self.performance_monitor.record_metric(
                "search_latency_cached", 
                execution_time,
                {"cache_hit": True, "query_length": len(query)}
            )
            
            logger.info(f"缓存命中: {query} (耗时: {execution_time:.3f}s)")
            return cached_result
        
        # 缓存未命中，执行实际搜索
        self.cache_misses += 1
        
        try:
            result = self.original_service.search_documents(query, limit, knowledge_base_id)
            
            # 缓存结果（仅当有结果时）
            if result:
                self.query_cache.set(query, result, **cache_key_params)
            
            execution_time = time.time() - start_time
            
            # 记录性能指标
            self.performance_monitor.record_metric(
                "search_latency", 
                execution_time,
                {
                    "cache_hit": False, 
                    "query_length": len(query),
                    "result_count": len(result)
                }
            )
            
            logger.info(f"搜索完成: {query} (耗时: {execution_time:.3f}s, 结果数: {len(result)})")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 记录错误指标
            self.performance_monitor.record_metric(
                "search_error", 
                execution_time,
                {"error": str(e), "query_length": len(query)}
            )
            
            logger.error(f"搜索失败: {query} (耗时: {execution_time:.3f}s, 错误: {e})")
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            性能统计
        """
        cache_stats = self.query_cache.get_stats()
        performance_stats = self.performance_monitor.get_all_metrics()
        
        total_searches = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_searches if total_searches > 0 else 0
        
        return {
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": cache_hit_rate,
                **cache_stats
            },
            "performance": performance_stats
        }
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.query_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info("检索缓存已清空")


class DocumentChunkOptimizer:
    """文档分块优化器"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        """初始化文档分块优化器
        
        Args:
            chunk_size: 分块大小（字符数）
            overlap: 重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunk_cache = {}
    
    def optimize_chunking(self, content: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """优化文档分块
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            优化后的分块列表
        """
        if not content:
            return []
        
        # 检查缓存
        content_hash = hashlib.md5(content.encode()).hexdigest()
        cache_key = f"{content_hash}_{self.chunk_size}_{self.overlap}"
        
        if cache_key in self.chunk_cache:
            return self.chunk_cache[cache_key]
        
        # 智能分块策略
        chunks = self._smart_chunking(content, metadata)
        
        # 缓存结果
        self.chunk_cache[cache_key] = chunks
        
        return chunks
    
    def _smart_chunking(self, content: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """智能分块策略
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            分块列表
        """
        chunks = []
        
        # 按段落分割（如果可能）
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        current_chunk_words = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 估算段落词数（简化实现）
            paragraph_words = len(paragraph.split())
            
            # 如果当前块加上新段落不超过限制，则合并
            if current_chunk_words + paragraph_words <= self.chunk_size // 5:  # 假设平均词长5字符
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_chunk_words += paragraph_words
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, chunk_index, metadata))
                    chunk_index += 1
                
                # 开始新块
                current_chunk = paragraph
                current_chunk_words = paragraph_words
        
        # 保存最后一个块
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_index, metadata))
        
        # 如果分块太大，进行二次分割
        final_chunks = []
        for chunk in chunks:
            if len(chunk['content']) > self.chunk_size:
                # 按句子分割
                sentences = chunk['content'].split('.')
                sub_chunk = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(sub_chunk) + len(sentence) + 1 <= self.chunk_size:
                        if sub_chunk:
                            sub_chunk += ". " + sentence
                        else:
                            sub_chunk = sentence
                    else:
                        if sub_chunk:
                            final_chunks.append(self._create_chunk(sub_chunk, len(final_chunks), metadata))
                        sub_chunk = sentence
                
                if sub_chunk:
                    final_chunks.append(self._create_chunk(sub_chunk, len(final_chunks), metadata))
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _create_chunk(self, content: str, index: int, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建分块对象
        
        Args:
            content: 分块内容
            index: 分块索引
            metadata: 元数据
            
        Returns:
            分块对象
        """
        chunk_metadata = (metadata or {}).copy()
        chunk_metadata.update({
            "chunk_index": index,
            "chunk_size": len(content),
            "word_count": len(content.split())
        })
        
        return {
            "content": content,
            "metadata": chunk_metadata,
            "summary": self._generate_chunk_summary(content)
        }
    
    def _generate_chunk_summary(self, content: str, max_length: int = 100) -> str:
        """生成分块摘要
        
        Args:
            content: 分块内容
            max_length: 摘要最大长度
            
        Returns:
            分块摘要
        """
        if len(content) <= max_length:
            return content
        
        # 简单的摘要生成：取前N个字符
        sentences = content.split('.')
        summary_parts = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if current_length + len(sentence) + 1 <= max_length:
                summary_parts.append(sentence)
                current_length += len(sentence) + 1
            else:
                break
        
        summary = ". ".join(summary_parts) + "."
        
        # 如果仍然太长，进行截断
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary