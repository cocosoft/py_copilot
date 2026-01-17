"""性能监控和优化工具"""
import time
import psutil
import functools
from typing import Any, Callable, Dict, Optional
from functools import lru_cache
from app.core.config import settings


class PerformanceMonitor:
    """性能监控器，用于跟踪函数执行时间和资源消耗"""
    
    def __init__(self):
        self.metrics = {}
    
    def monitor(self, func: Callable) -> Callable:
        """装饰器：监控函数执行时间和资源消耗"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 记录开始时间和资源使用情况
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            start_cpu = psutil.cpu_percent(interval=0.1)
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 记录结束时间和资源使用情况
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            end_cpu = psutil.cpu_percent(interval=0.1)
            
            # 计算性能指标
            execution_time = (end_time - start_time) * 1000  # 转换为毫秒
            memory_used = (end_memory - start_memory) / (1024 * 1024)  # 转换为MB
            cpu_used = end_cpu - start_cpu
            
            # 存储性能指标
            func_name = func.__name__
            if func_name not in self.metrics:
                self.metrics[func_name] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0,
                    "min_time": float("inf"),
                    "total_memory": 0,
                    "avg_memory": 0,
                    "total_cpu": 0,
                    "avg_cpu": 0
                }
            
            metric = self.metrics[func_name]
            metric["count"] += 1
            metric["total_time"] += execution_time
            metric["avg_time"] = metric["total_time"] / metric["count"]
            metric["max_time"] = max(metric["max_time"], execution_time)
            metric["min_time"] = min(metric["min_time"], execution_time)
            metric["total_memory"] += memory_used
            metric["avg_memory"] = metric["total_memory"] / metric["count"]
            metric["total_cpu"] += cpu_used
            metric["avg_cpu"] = metric["total_cpu"] / metric["count"]
            
            # 记录性能数据到日志（如果启用）
            if settings.enable_performance_logging:
                import logging
                logger = logging.getLogger("performance")
                logger.info(
                    f"Performance: {func_name} took {execution_time:.2f}ms, "
                    f"used {memory_used:.2f}MB memory, {cpu_used:.2f}% CPU"
                )
            
            return result
        
        return wrapper
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有性能指标"""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """重置性能指标"""
        self.metrics = {}


# 全局性能监控器
performance_monitor = PerformanceMonitor()


class CachingDecorator:
    """缓存装饰器，用于优化重复调用"""
    
    @staticmethod
    def cached(cache_key_func: Optional[Callable] = None, maxsize: int = 128, typed: bool = False) -> Callable:
        """装饰器：缓存函数结果
        
        Args:
            cache_key_func: 自定义缓存键生成函数
            maxsize: 缓存大小
            typed: 是否区分参数类型
        """
        def decorator(func: Callable) -> Callable:
            # 如果提供了自定义缓存键生成函数
            if cache_key_func:
                @functools.wraps(func)
                def wrapper(*args, **kwargs) -> Any:
                    key = cache_key_func(*args, **kwargs)
                    # 使用LRU缓存
                    @lru_cache(maxsize=maxsize, typed=typed)
                    def cached_func(cache_key):
                        return func(*args, **kwargs)
                    return cached_func(key)
                return wrapper
            else:
                # 使用默认的LRU缓存
                return lru_cache(maxsize=maxsize, typed=typed)(func)
        
        return decorator


class ResourceOptimizer:
    """资源优化工具"""
    
    @staticmethod
    def batch_process(items: list, process_func: Callable, batch_size: int = 10) -> list:
        """批量处理函数，减少内存峰值
        
        Args:
            items: 待处理的项目列表
            process_func: 处理函数
            batch_size: 批量大小
        
        Returns:
            处理结果列表
        """
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            batch_results = [process_func(item) for item in batch]
            results.extend(batch_results)
            # 显式释放内存
            del batch
            del batch_results
        return results
    
    @staticmethod
    def lazy_load(func: Callable) -> Callable:
        """装饰器：延迟加载，只有在需要时才执行函数"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = None
            
            def get_result():
                nonlocal result
                if result is None:
                    result = func(*args, **kwargs)
                return result
            
            return get_result
        
        return wrapper
    
    @staticmethod
    def optimize_memory_usage(data: Any, max_depth: int = 3) -> Any:
        """优化数据结构的内存使用
        
        Args:
            data: 待优化的数据
            max_depth: 最大递归深度
        
        Returns:
            优化后的数据
        """
        if max_depth <= 0:
            return data
            
        if isinstance(data, dict):
            # 移除空值和不必要的字段
            optimized = {k: v for k, v in data.items() 
                       if v is not None and not k.startswith('_')}
            # 递归优化嵌套结构
            return {k: ResourceOptimizer.optimize_memory_usage(v, max_depth-1) 
                   for k, v in optimized.items()}
        elif isinstance(data, list):
            # 移除空值
            optimized = [v for v in data if v is not None]
            # 递归优化嵌套结构
            return [ResourceOptimizer.optimize_memory_usage(v, max_depth-1) 
                   for v in optimized]
        elif isinstance(data, str) and len(data) > 10000:
            # 截断过长的字符串
            return data[:10000] + "... (truncated)"
        return data
    
    @staticmethod
    def batch_generator(items: list, batch_size: int = 100) -> list:
        """批量生成器，减少内存峰值
        
        Args:
            items: 待处理的项目列表
            batch_size: 批量大小
        
        Yields:
            批量项目列表
        """
        for i in range(0, len(items), batch_size):
            yield items[i:i+batch_size]


# 全局缓存装饰器
cached = CachingDecorator.cached
