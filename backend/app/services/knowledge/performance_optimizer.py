#!/usr/bin/env python3
"""
性能优化模块

提供知识图谱系统的性能优化功能：
1. 缓存机制
2. 批量处理
3. 异步处理
4. 数据库查询优化
5. 内存管理
"""

import functools
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from functools import lru_cache
from datetime import datetime, timedelta
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil
import os

logger = logging.getLogger(__name__)


class CacheManager:
    """
    缓存管理器

    提供多级缓存支持：
    1. 内存缓存（LRU）
    2. 时间过期缓存
    3. 大小限制缓存
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                # 检查是否过期
                if entry['expires_at'] > datetime.now():
                    self._hit_count += 1
                    return entry['value']
                else:
                    # 删除过期项
                    del self._cache[key]

            self._miss_count += 1
            return None

    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存值"""
        if ttl is None:
            ttl = self.default_ttl

        with self._lock:
            # 检查缓存大小
            if len(self._cache) >= self.max_size and key not in self._cache:
                # 删除最旧的项
                self._evict_oldest()

            self._cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'created_at': datetime.now()
            }

    def delete(self, key: str):
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hit_count = 0
            self._miss_count = 0

    def _evict_oldest(self):
        """淘汰最旧的缓存项"""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['created_at']
        )
        del self._cache[oldest_key]

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total_requests if total_requests > 0 else 0

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_count': self._hit_count,
                'miss_count': self._miss_count,
                'hit_rate': hit_rate,
                'memory_usage_mb': self._estimate_memory_usage()
            }

    def _estimate_memory_usage(self) -> float:
        """估算内存使用量（MB）"""
        import sys
        total_size = 0
        for key, entry in self._cache.items():
            total_size += sys.getsizeof(key)
            total_size += sys.getsizeof(entry)
        return total_size / (1024 * 1024)


class BatchProcessor:
    """
    批量处理器

    优化批量操作性能：
    1. 批量插入
    2. 批量更新
    3. 批量查询
    """

    def __init__(self, batch_size: int = 100, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_batch(
        self,
        items: List[Any],
        process_func: Callable,
        *args,
        **kwargs
    ) -> List[Any]:
        """
        批量处理项目

        Args:
            items: 待处理项目列表
            process_func: 处理函数
            *args, **kwargs: 传递给处理函数的参数

        Returns:
            处理结果列表
        """
        results = []

        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]

            # 使用线程池并行处理
            loop = asyncio.get_event_loop()
            batch_results = await loop.run_in_executor(
                self._executor,
                lambda: [process_func(item, *args, **kwargs) for item in batch]
            )

            results.extend(batch_results)

            # 记录进度
            progress = min(100, (i + len(batch)) / len(items) * 100)
            logger.info(f"批量处理进度: {progress:.1f}%")

        return results

    def process_batch_sync(
        self,
        items: List[Any],
        process_func: Callable,
        *args,
        **kwargs
    ) -> List[Any]:
        """同步批量处理"""
        results = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = [process_func(item, *args, **kwargs) for item in batch]
            results.extend(batch_results)

        return results


class QueryOptimizer:
    """
    查询优化器

    优化数据库查询性能：
    1. 查询缓存
    2. 预加载
    3. 分页优化
    """

    def __init__(self, cache_manager: CacheManager = None):
        self.cache = cache_manager or CacheManager()
        self._query_stats: Dict[str, Dict[str, Any]] = {}

    def optimize_query(self, query_func: Callable) -> Callable:
        """查询优化装饰器"""
        @functools.wraps(query_func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{query_func.__name__}:{str(args)}:{str(kwargs)}"

            # 尝试从缓存获取
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行查询
            start_time = time.time()
            result = query_func(*args, **kwargs)
            query_time = time.time() - start_time

            # 记录统计
            self._record_query_stats(query_func.__name__, query_time)

            # 缓存结果（如果查询时间超过100ms）
            if query_time > 0.1:
                self.cache.set(cache_key, result, ttl=300)

            return result

        return wrapper

    def _record_query_stats(self, query_name: str, execution_time: float):
        """记录查询统计"""
        if query_name not in self._query_stats:
            self._query_stats[query_name] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf')
            }

        stats = self._query_stats[query_name]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)

    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计"""
        return {
            'queries': self._query_stats,
            'total_queries': sum(s['count'] for s in self._query_stats.values()),
            'slow_queries': [
                name for name, stats in self._query_stats.items()
                if stats['avg_time'] > 1.0
            ]
        }


class MemoryMonitor:
    """
    内存监控器

    监控系统内存使用情况：
    1. 内存使用统计
    2. 内存泄漏检测
    3. 内存优化建议
    """

    def __init__(self, warning_threshold: float = 80.0):
        self.warning_threshold = warning_threshold
        self._baseline_memory = None
        self._measurements: List[Dict[str, Any]] = []

    def start_monitoring(self):
        """开始监控"""
        self._baseline_memory = self._get_memory_usage()
        logger.info(f"内存监控开始，基线: {self._baseline_memory:.2f} MB")

    def record_measurement(self, label: str = ""):
        """记录内存测量"""
        current_memory = self._get_memory_usage()
        measurement = {
            'timestamp': datetime.now(),
            'memory_mb': current_memory,
            'label': label,
            'delta_from_baseline': current_memory - (self._baseline_memory or 0)
        }
        self._measurements.append(measurement)

        # 检查是否超过阈值
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.warning_threshold:
            logger.warning(f"内存使用超过阈值: {memory_percent:.1f}%")

        return measurement

    def _get_memory_usage(self) -> float:
        """获取当前内存使用（MB）"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    def get_memory_report(self) -> Dict[str, Any]:
        """获取内存报告"""
        if not self._measurements:
            return {'error': '没有测量数据'}

        memory_values = [m['memory_mb'] for m in self._measurements]

        return {
            'baseline_mb': self._baseline_memory,
            'current_mb': memory_values[-1],
            'peak_mb': max(memory_values),
            'avg_mb': sum(memory_values) / len(memory_values),
            'measurement_count': len(self._measurements),
            'trend': 'increasing' if memory_values[-1] > memory_values[0] else 'stable',
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """生成内存优化建议"""
        recommendations = []

        if not self._measurements:
            return recommendations

        memory_values = [m['memory_mb'] for m in self._measurements]
        current_memory = memory_values[-1]
        baseline = self._baseline_memory or 0

        # 检查内存增长
        if current_memory > baseline * 2:
            recommendations.append("内存使用增长显著，建议检查内存泄漏")

        # 检查峰值
        peak_memory = max(memory_values)
        if peak_memory > 1000:  # 1GB
            recommendations.append("内存峰值超过1GB，建议优化大数据处理")

        # 检查趋势
        if len(memory_values) > 10:
            recent_avg = sum(memory_values[-10:]) / 10
            early_avg = sum(memory_values[:10]) / 10
            if recent_avg > early_avg * 1.5:
                recommendations.append("内存使用呈上升趋势，建议进行内存优化")

        return recommendations


class PerformanceProfiler:
    """
    性能分析器

    分析函数执行性能：
    1. 执行时间分析
    2. 调用次数统计
    3. 性能瓶颈识别
    """

    def __init__(self):
        self._profiles: Dict[str, Dict[str, Any]] = {}

    def profile(self, func: Callable) -> Callable:
        """性能分析装饰器"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__

            if func_name not in self._profiles:
                self._profiles[func_name] = {
                    'call_count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                    'min_time': float('inf')
                }

            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            profile = self._profiles[func_name]
            profile['call_count'] += 1
            profile['total_time'] += execution_time
            profile['avg_time'] = profile['total_time'] / profile['call_count']
            profile['max_time'] = max(profile['max_time'], execution_time)
            profile['min_time'] = min(profile['min_time'], execution_time)

            return result

        return wrapper

    def get_profile_report(self) -> Dict[str, Any]:
        """获取性能分析报告"""
        if not self._profiles:
            return {'message': '没有性能数据'}

        # 找出最慢的函数
        sorted_profiles = sorted(
            self._profiles.items(),
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )

        return {
            'total_functions': len(self._profiles),
            'total_calls': sum(p['call_count'] for _, p in sorted_profiles),
            'slowest_functions': [
                {
                    'name': name,
                    'avg_time': stats['avg_time'],
                    'call_count': stats['call_count']
                }
                for name, stats in sorted_profiles[:5]
            ],
            'all_profiles': self._profiles
        }


# ============== 便捷函数 ==============

def timed_execution(func: Callable) -> Callable:
    """执行时间测量装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"{func.__name__} 执行时间: {execution_time:.3f}s")
        return result
    return wrapper


def async_timed_execution(func: Callable) -> Callable:
    """异步执行时间测量装饰器"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"{func.__name__} 执行时间: {execution_time:.3f}s")
        return result
    return wrapper


# 全局实例
cache_manager = CacheManager()
batch_processor = BatchProcessor()
query_optimizer = QueryOptimizer(cache_manager)
memory_monitor = MemoryMonitor()
performance_profiler = PerformanceProfiler()
