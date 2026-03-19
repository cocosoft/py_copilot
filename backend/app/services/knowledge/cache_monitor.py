"""缓存监控服务

监控缓存使用情况、性能和健康状态，提供缓存分析和优化建议。
"""
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, deque

from app.core.cache import cache_service
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class CacheMetrics:
    """缓存指标
    
    记录缓存操作的指标。
    """
    
    def __init__(self):
        """初始化缓存指标"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.get_times: List[float] = []
        self.set_times: List[float] = []
        self.delete_times: List[float] = []
        self.last_reset = datetime.now()
    
    def record_hit(self, time_taken: float):
        """记录缓存命中"""
        self.hits += 1
        self.get_times.append(time_taken)
    
    def record_miss(self, time_taken: float):
        """记录缓存未命中"""
        self.misses += 1
        self.get_times.append(time_taken)
    
    def record_set(self, time_taken: float):
        """记录缓存设置"""
        self.sets += 1
        self.set_times.append(time_taken)
    
    def record_delete(self, time_taken: float):
        """记录缓存删除"""
        self.deletes += 1
        self.delete_times.append(time_taken)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_gets = self.hits + self.misses
        hit_rate = (self.hits / total_gets * 100) if total_gets > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_gets": total_gets,
            "hit_rate": hit_rate,
            "sets": self.sets,
            "deletes": self.deletes,
            "avg_get_time": statistics.mean(self.get_times) if self.get_times else 0,
            "avg_set_time": statistics.mean(self.set_times) if self.set_times else 0,
            "avg_delete_time": statistics.mean(self.delete_times) if self.delete_times else 0,
            "max_get_time": max(self.get_times) if self.get_times else 0,
            "max_set_time": max(self.set_times) if self.set_times else 0,
            "max_delete_time": max(self.delete_times) if self.delete_times else 0,
            "last_reset": self.last_reset.isoformat()
        }
    
    def reset(self):
        """重置指标"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.get_times = []
        self.set_times = []
        self.delete_times = []
        self.last_reset = datetime.now()


class CacheMonitor:
    """缓存监控器
    
    监控缓存使用情况和性能。
    """
    
    def __init__(self, window_size: int = 1000):
        """
        初始化缓存监控器
        
        Args:
            window_size: 滑动窗口大小
        """
        self.redis_client = get_redis()
        self.metrics = CacheMetrics()
        self.window_size = window_size
        self.operation_history = deque(maxlen=window_size)
        self.key_stats: Dict[str, Dict] = defaultdict(lambda: {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "last_access": datetime.now()
        })
        self.last_health_check = datetime.now()
        self.health_check_interval = timedelta(minutes=5)
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存值并记录指标"""
        start_time = time.time()
        value = await cache_service.get(key)
        time_taken = time.time() - start_time
        
        if value:
            self.metrics.record_hit(time_taken)
            self.key_stats[key]["hits"] += 1
        else:
            self.metrics.record_miss(time_taken)
            self.key_stats[key]["misses"] += 1
        
        self.key_stats[key]["last_access"] = datetime.now()
        self.operation_history.append({
            "operation": "get",
            "key": key,
            "success": value is not None,
            "time_taken": time_taken,
            "timestamp": datetime.now()
        })
        
        return value
    
    async def set(self, key: str, value: Dict[str, Any], timeout: Optional[timedelta] = None) -> bool:
        """设置缓存值并记录指标"""
        start_time = time.time()
        success = await cache_service.set(key, value, timeout)
        time_taken = time.time() - start_time
        
        self.metrics.record_set(time_taken)
        if success:
            self.key_stats[key]["sets"] += 1
        
        self.key_stats[key]["last_access"] = datetime.now()
        self.operation_history.append({
            "operation": "set",
            "key": key,
            "success": success,
            "time_taken": time_taken,
            "timestamp": datetime.now()
        })
        
        return success
    
    async def delete(self, key: str) -> bool:
        """删除缓存值并记录指标"""
        start_time = time.time()
        success = await cache_service.delete(key)
        time_taken = time.time() - start_time
        
        self.metrics.record_delete(time_taken)
        if success:
            self.key_stats[key]["deletes"] += 1
        
        self.key_stats[key]["last_access"] = datetime.now()
        self.operation_history.append({
            "operation": "delete",
            "key": key,
            "success": success,
            "time_taken": time_taken,
            "timestamp": datetime.now()
        })
        
        return success
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        metrics = self.metrics.get_stats()
        
        # 计算热门键
        hot_keys = sorted(
            self.key_stats.items(),
            key=lambda x: x[1]["hits"] + x[1]["misses"],
            reverse=True
        )[:10]
        
        # 计算最近操作
        recent_operations = list(self.operation_history)[-50:]
        
        return {
            "metrics": metrics,
            "hot_keys": [
                {
                    "key": key,
                    "hits": stats["hits"],
                    "misses": stats["misses"],
                    "last_access": stats["last_access"].isoformat()
                }
                for key, stats in hot_keys
            ],
            "recent_operations": recent_operations,
            "total_keys": len(self.key_stats),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取缓存健康状态"""
        current_time = datetime.now()
        
        # 检查是否需要执行健康检查
        if current_time - self.last_health_check >= self.health_check_interval:
            self.last_health_check = current_time
        
        health_status = {
            "status": "healthy",
            "backend": "redis" if self.redis_client else "memory",
            "timestamp": current_time.isoformat()
        }
        
        if self.redis_client:
            try:
                # 测试Redis连接
                self.redis_client.ping()
                
                # 获取Redis信息
                info = self.redis_client.info()
                health_status.update({
                    "redis_info": {
                        "used_memory": info.get("used_memory_human", "N/A"),
                        "keys": info.get("db0", {}).get("keys", 0),
                        "expired_keys": info.get("expired_keys", 0),
                        "evicted_keys": info.get("evicted_keys", 0),
                        "uptime": info.get("uptime_in_seconds", 0)
                    }
                })
            except Exception as e:
                health_status["status"] = "unhealthy"
                health_status["error"] = str(e)
        
        # 添加性能指标
        performance_stats = self.get_performance_stats()
        health_status["performance"] = performance_stats["metrics"]
        
        return health_status
    
    def get_optimization_recommendations(self) -> List[str]:
        """获取优化建议"""
        recommendations = []
        
        stats = self.metrics.get_stats()
        hit_rate = stats["hit_rate"]
        
        # 检查命中率
        if hit_rate < 50:
            recommendations.append("缓存命中率较低，建议增加缓存预热和优化缓存键策略")
        elif hit_rate < 80:
            recommendations.append("缓存命中率可以进一步优化，建议分析未命中的键模式")
        
        # 检查响应时间
        if stats["avg_get_time"] > 0.1:
            recommendations.append("缓存获取响应时间较长，建议检查Redis连接和网络延迟")
        
        if stats["avg_set_time"] > 0.1:
            recommendations.append("缓存设置响应时间较长，建议检查Redis写入性能")
        
        # 分析热门键
        hot_keys = sorted(
            self.key_stats.items(),
            key=lambda x: x[1]["hits"] + x[1]["misses"],
            reverse=True
        )[:5]
        
        for key, stats in hot_keys:
            if stats["misses"] > stats["hits"]:
                recommendations.append(f"键 '{key}' 未命中率较高，建议优化缓存策略")
        
        return recommendations
    
    def reset_metrics(self):
        """重置指标"""
        self.metrics.reset()
        logger.info("缓存监控指标已重置")
    
    async def generate_report(self) -> str:
        """生成监控报告"""
        health_status = await self.get_health_status()
        performance_stats = self.get_performance_stats()
        recommendations = self.get_optimization_recommendations()
        
        report = []
        report.append("=" * 80)
        report.append("缓存监控报告")
        report.append("=" * 80)
        report.append("")
        
        # 健康状态
        report.append("健康状态:")
        report.append(f"  状态: {health_status['status']}")
        report.append(f"  后端: {health_status['backend']}")
        report.append(f"  时间: {health_status['timestamp']}")
        
        if 'redis_info' in health_status:
            report.append("  Redis信息:")
            redis_info = health_status['redis_info']
            for key, value in redis_info.items():
                report.append(f"    {key}: {value}")
        report.append("")
        
        # 性能统计
        report.append("性能统计:")
        metrics = performance_stats['metrics']
        report.append(f"  命中率: {metrics['hit_rate']:.1f}%")
        report.append(f"  总获取次数: {metrics['total_gets']}")
        report.append(f"  命中次数: {metrics['hits']}")
        report.append(f"  未命中次数: {metrics['misses']}")
        report.append(f"  设置次数: {metrics['sets']}")
        report.append(f"  删除次数: {metrics['deletes']}")
        report.append(f"  平均获取时间: {metrics['avg_get_time']:.3f}s")
        report.append(f"  平均设置时间: {metrics['avg_set_time']:.3f}s")
        report.append("")
        
        # 热门键
        report.append("热门键:")
        for key_info in performance_stats['hot_keys']:
            report.append(f"  键: {key_info['key']}")
            report.append(f"    命中: {key_info['hits']}, 未命中: {key_info['misses']}")
            report.append(f"    最后访问: {key_info['last_access']}")
        report.append("")
        
        # 优化建议
        if recommendations:
            report.append("优化建议:")
            for i, recommendation in enumerate(recommendations, 1):
                report.append(f"  {i}. {recommendation}")
        else:
            report.append("优化建议: 暂无")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


# 全局缓存监控器实例
cache_monitor = CacheMonitor()


# 替换缓存服务的方法，添加监控
class MonitoredCacheService:
    """监控的缓存服务
    
    包装缓存服务，添加监控功能。
    """
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存值"""
        return await cache_monitor.get(key)
    
    async def set(self, key: str, value: Dict[str, Any], timeout: Optional[timedelta] = None) -> bool:
        """设置缓存值"""
        return await cache_monitor.set(key, value, timeout)
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        return await cache_monitor.delete(key)
    
    async def clear(self) -> bool:
        """清空缓存"""
        return await cache_service.clear()
    
    async def get_or_set(self, key: str, func: Callable, 
                        timeout: Optional[timedelta] = None) -> Dict[str, Any]:
        """获取或设置缓存值"""
        # 尝试从监控的缓存获取
        value = await self.get(key)
        if value:
            return value
        
        # 缓存未命中，执行函数
        value = func()
        
        # 设置缓存
        await self.set(key, value, timeout)
        
        return value


# 创建监控的缓存服务实例
monitored_cache_service = MonitoredCacheService()


# 便捷函数

async def get_cache_performance():  # 修正: 添加返回类型注解
    """获取缓存性能信息
    
    Returns:
        缓存性能信息
    """
    return cache_monitor.get_performance_stats()


async def get_cache_health():
    """获取缓存健康状态
    
    Returns:
        缓存健康状态
    """
    return await cache_monitor.get_health_status()


async def get_cache_recommendations():
    """获取缓存优化建议
    
    Returns:
        优化建议列表
    """
    return cache_monitor.get_optimization_recommendations()


async def generate_cache_report():
    """生成缓存监控报告
    
    Returns:
        监控报告文本
    """
    return await cache_monitor.generate_report()


# 缓存分析工具
class CacheAnalyzer:
    """缓存分析器
    
    分析缓存使用模式和性能。
    """
    
    def __init__(self):
        """初始化缓存分析器"""
        self.monitor = cache_monitor
    
    def analyze_cache_patterns(self) -> Dict[str, Any]:
        """分析缓存使用模式
        
        Returns:
            缓存使用模式分析
        """
        key_patterns = defaultdict(int)
        operation_patterns = defaultdict(int)
        
        # 分析键模式
        for key in self.monitor.key_stats:
            # 提取键的前缀
            parts = key.split(":")
            if len(parts) > 1:
                pattern = parts[1]  # 假设格式为 knowledge:pattern:...
                key_patterns[pattern] += 1
        
        # 分析操作模式
        for op in self.monitor.operation_history:
            operation_patterns[op["operation"]] += 1
        
        return {
            "key_patterns": dict(key_patterns),
            "operation_patterns": dict(operation_patterns),
            "total_keys": len(self.monitor.key_stats),
            "analysis_time": datetime.now().isoformat()
        }
    
    def identify_cache_hotspots(self) -> List[Dict[str, Any]]:
        """识别缓存热点
        
        Returns:
            缓存热点列表
        """
        hotspots = []
        
        for key, stats in self.monitor.key_stats.items():
            total_accesses = stats["hits"] + stats["misses"]
            if total_accesses > 10:  # 访问次数超过10次视为热点
                hotspots.append({
                    "key": key,
                    "total_accesses": total_accesses,
                    "hits": stats["hits"],
                    "misses": stats["misses"],
                    "hit_rate": (stats["hits"] / total_accesses * 100) if total_accesses > 0 else 0,
                    "last_access": stats["last_access"].isoformat()
                })
        
        # 按总访问次数排序
        hotspots.sort(key=lambda x: x["total_accesses"], reverse=True)
        
        return hotspots


# 全局缓存分析器实例
cache_analyzer = CacheAnalyzer()