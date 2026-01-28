"""
高级缓存机制

实现多级缓存、智能缓存策略、缓存监控等高级缓存功能。
"""
import time
import hashlib
import logging
import threading
import pickle
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
import os
import json

logger = logging.getLogger(__name__)


class MultiLevelCache:
    """多级缓存管理器"""
    
    def __init__(self, 
                 memory_max_size: int = 1000, 
                 memory_ttl: int = 1800,  # 30分钟
                 disk_cache_dir: str = None,
                 disk_max_size: int = 10000,
                 disk_ttl: int = 86400):  # 24小时
        """初始化多级缓存
        
        Args:
            memory_max_size: 内存缓存最大条目数
            memory_ttl: 内存缓存生存时间（秒）
            disk_cache_dir: 磁盘缓存目录
            disk_max_size: 磁盘缓存最大条目数
            disk_ttl: 磁盘缓存生存时间（秒）
        """
        # 内存缓存（LRU策略）
        self.memory_cache = OrderedDict()
        self.memory_max_size = memory_max_size
        self.memory_ttl = memory_ttl
        
        # 磁盘缓存
        self.disk_cache_dir = disk_cache_dir or os.path.join(os.getcwd(), "cache")
        self.disk_max_size = disk_max_size
        self.disk_ttl = disk_ttl
        
        # 创建磁盘缓存目录
        os.makedirs(self.disk_cache_dir, exist_ok=True)
        
        # 统计信息
        self.stats = {
            "memory_hits": 0,
            "memory_misses": 0,
            "disk_hits": 0,
            "disk_misses": 0,
            "total_requests": 0
        }
        
        self.lock = threading.RLock()
        
        logger.info(f"多级缓存初始化完成，内存: {memory_max_size}条，磁盘: {disk_max_size}条")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        with self.lock:
            self.stats["total_requests"] += 1
            
            # 首先检查内存缓存
            memory_value = self._get_from_memory(key)
            if memory_value is not None:
                self.stats["memory_hits"] += 1
                return memory_value
            
            # 然后检查磁盘缓存
            disk_value = self._get_from_disk(key)
            if disk_value is not None:
                self.stats["disk_hits"] += 1
                # 将磁盘缓存提升到内存
                self._set_to_memory(key, disk_value)
                return disk_value
            
            # 缓存未命中
            self.stats["memory_misses"] += 1
            self.stats["disk_misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认值
        """
        with self.lock:
            # 设置到内存缓存
            self._set_to_memory(key, value, ttl or self.memory_ttl)
            
            # 设置到磁盘缓存
            self._set_to_disk(key, value, ttl or self.disk_ttl)
    
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """从内存缓存获取值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        if key not in self.memory_cache:
            return None
        
        cache_entry = self.memory_cache[key]
        
        # 检查是否过期
        if datetime.now() > cache_entry["expires_at"]:
            del self.memory_cache[key]
            return None
        
        # 移动到最近使用位置
        self.memory_cache.move_to_end(key)
        
        return cache_entry["value"]
    
    def _set_to_memory(self, key: str, value: Any, ttl: int = None) -> None:
        """设置值到内存缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
        """
        ttl = ttl or self.memory_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self.memory_cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        
        # 保持LRU顺序
        self.memory_cache.move_to_end(key)
        
        # 检查缓存大小，如果超过限制则移除最旧的条目
        if len(self.memory_cache) > self.memory_max_size:
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
    
    def _get_from_disk(self, key: str) -> Optional[Any]:
        """从磁盘缓存获取值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        file_path = self._get_disk_file_path(key)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否过期
            expires_at = datetime.fromisoformat(cache_data["expires_at"])
            if datetime.now() > expires_at:
                os.remove(file_path)
                return None
            
            # 反序列化值
            value = pickle.loads(bytes.fromhex(cache_data["value"]))
            return value
            
        except Exception as e:
            logger.warning(f"读取磁盘缓存失败: {e}")
            # 清理损坏的缓存文件
            try:
                os.remove(file_path)
            except:
                pass
            return None
    
    def _set_to_disk(self, key: str, value: Any, ttl: int = None) -> None:
        """设置值到磁盘缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
        """
        ttl = ttl or self.disk_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        file_path = self._get_disk_file_path(key)
        
        try:
            # 序列化值
            serialized_value = pickle.dumps(value).hex()
            
            cache_data = {
                "value": serialized_value,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now().isoformat(),
                "key": key
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"写入磁盘缓存失败: {e}")
    
    def _get_disk_file_path(self, key: str) -> str:
        """获取磁盘缓存文件路径
        
        Args:
            key: 缓存键
            
        Returns:
            文件路径
        """
        # 使用key的哈希作为文件名
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.disk_cache_dir, f"{key_hash}.json")
    
    def clear(self, level: str = "all") -> None:
        """清空缓存
        
        Args:
            level: 缓存级别（"memory", "disk", "all"）
        """
        with self.lock:
            if level in ["memory", "all"]:
                self.memory_cache.clear()
                logger.info("内存缓存已清空")
            
            if level in ["disk", "all"]:
                try:
                    for file_path in os.listdir(self.disk_cache_dir):
                        if file_path.endswith('.json'):
                            os.remove(os.path.join(self.disk_cache_dir, file_path))
                    logger.info("磁盘缓存已清空")
                except Exception as e:
                    logger.error(f"清空磁盘缓存失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息
        """
        with self.lock:
            memory_hit_rate = self.stats["memory_hits"] / self.stats["total_requests"] if self.stats["total_requests"] > 0 else 0
            disk_hit_rate = self.stats["disk_hits"] / self.stats["total_requests"] if self.stats["total_requests"] > 0 else 0
            total_hit_rate = (self.stats["memory_hits"] + self.stats["disk_hits"]) / self.stats["total_requests"] if self.stats["total_requests"] > 0 else 0
            
            return {
                "memory": {
                    "size": len(self.memory_cache),
                    "max_size": self.memory_max_size,
                    "hits": self.stats["memory_hits"],
                    "misses": self.stats["memory_misses"],
                    "hit_rate": memory_hit_rate
                },
                "disk": {
                    "size": self._get_disk_cache_size(),
                    "max_size": self.disk_max_size,
                    "hits": self.stats["disk_hits"],
                    "misses": self.stats["disk_misses"],
                    "hit_rate": disk_hit_rate
                },
                "overall": {
                    "total_requests": self.stats["total_requests"],
                    "total_hits": self.stats["memory_hits"] + self.stats["disk_hits"],
                    "total_misses": self.stats["memory_misses"] + self.stats["disk_misses"],
                    "hit_rate": total_hit_rate
                }
            }
    
    def _get_disk_cache_size(self) -> int:
        """获取磁盘缓存大小
        
        Returns:
            缓存条目数
        """
        try:
            cache_files = [f for f in os.listdir(self.disk_cache_dir) if f.endswith('.json')]
            return len(cache_files)
        except:
            return 0


class SmartCacheStrategy:
    """智能缓存策略"""
    
    def __init__(self, base_cache: MultiLevelCache):
        """初始化智能缓存策略
        
        Args:
            base_cache: 基础缓存实例
        """
        self.cache = base_cache
        self.access_patterns = defaultdict(list)
        self.popularity_scores = {}
        self.lock = threading.RLock()
    
    def get_with_strategy(self, key: str, generator: Callable[[], Any], 
                         strategy: str = "default", **kwargs) -> Any:
        """使用策略获取缓存值
        
        Args:
            key: 缓存键
            generator: 值生成器函数
            strategy: 缓存策略
            **kwargs: 策略参数
            
        Returns:
            缓存值或生成的值
        """
        # 记录访问模式
        self._record_access_pattern(key)
        
        # 首先尝试从缓存获取
        cached_value = self.cache.get(key)
        if cached_value is not None:
            return cached_value
        
        # 缓存未命中，生成新值
        new_value = generator()
        
        # 根据策略决定是否缓存
        should_cache = self._should_cache(key, new_value, strategy, **kwargs)
        
        if should_cache:
            ttl = self._calculate_ttl(key, new_value, strategy, **kwargs)
            self.cache.set(key, new_value, ttl)
        
        return new_value
    
    def _record_access_pattern(self, key: str) -> None:
        """记录访问模式
        
        Args:
            key: 缓存键
        """
        with self.lock:
            timestamp = time.time()
            self.access_patterns[key].append(timestamp)
            
            # 保持最近100次访问记录
            if len(self.access_patterns[key]) > 100:
                self.access_patterns[key] = self.access_patterns[key][-100:]
            
            # 更新流行度分数
            self._update_popularity_score(key)
    
    def _update_popularity_score(self, key: str) -> None:
        """更新流行度分数
        
        Args:
            key: 缓存键
        """
        accesses = self.access_patterns[key]
        
        if not accesses:
            self.popularity_scores[key] = 0
            return
        
        # 计算基于时间衰减的流行度分数
        current_time = time.time()
        score = 0
        
        for access_time in accesses[-10:]:  # 只考虑最近10次访问
            time_diff = current_time - access_time
            # 时间衰减因子：最近访问的权重更高
            decay_factor = max(0, 1 - time_diff / 3600)  # 1小时内衰减
            score += decay_factor
        
        self.popularity_scores[key] = score
    
    def _should_cache(self, key: str, value: Any, strategy: str, **kwargs) -> bool:
        """判断是否应该缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            strategy: 缓存策略
            **kwargs: 策略参数
            
        Returns:
            是否应该缓存
        """
        if strategy == "always":
            return True
        elif strategy == "never":
            return False
        elif strategy == "size_based":
            max_size = kwargs.get("max_size", 1024 * 1024)  # 默认1MB
            value_size = self._estimate_size(value)
            return value_size <= max_size
        elif strategy == "popularity_based":
            min_popularity = kwargs.get("min_popularity", 0.5)
            popularity = self.popularity_scores.get(key, 0)
            return popularity >= min_popularity
        elif strategy == "cost_based":
            # 基于生成成本的策略
            generation_cost = kwargs.get("generation_cost", 0)
            min_cost = kwargs.get("min_cost", 1.0)
            return generation_cost >= min_cost
        else:  # default strategy
            # 默认策略：缓存非空、大小合理的值
            value_size = self._estimate_size(value)
            return value is not None and value_size <= 10 * 1024 * 1024  # 10MB
    
    def _calculate_ttl(self, key: str, value: Any, strategy: str, **kwargs) -> int:
        """计算缓存生存时间
        
        Args:
            key: 缓存键
            value: 缓存值
            strategy: 缓存策略
            **kwargs: 策略参数
            
        Returns:
            生存时间（秒）
        """
        base_ttl = kwargs.get("base_ttl", 1800)  # 默认30分钟
        
        if strategy == "popularity_based":
            # 流行度越高，TTL越长
            popularity = self.popularity_scores.get(key, 0)
            popularity_factor = min(5.0, 1 + popularity)  # 最多5倍
            return int(base_ttl * popularity_factor)
        
        elif strategy == "size_based":
            # 值越大，TTL越短
            value_size = self._estimate_size(value)
            size_factor = max(0.1, 1 - value_size / (10 * 1024 * 1024))  # 10MB为基准
            return int(base_ttl * size_factor)
        
        else:
            return base_ttl
    
    def _estimate_size(self, value: Any) -> int:
        """估算值的大小
        
        Args:
            value: 要估算的值
            
        Returns:
            估算大小（字节）
        """
        try:
            if isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (list, tuple, dict)):
                # 简单估算：假设每个元素平均100字节
                return len(str(value)) * 10
            else:
                return len(str(value))
        except:
            return 0


class CacheMonitor:
    """缓存监控器"""
    
    def __init__(self, cache: MultiLevelCache):
        """初始化缓存监控器
        
        Args:
            cache: 缓存实例
        """
        self.cache = cache
        self.monitoring_data = []
        self.monitoring_enabled = True
        self.monitoring_thread = None
        self.stop_monitoring = False
    
    def start_monitoring(self, interval: int = 60) -> None:
        """开始监控
        
        Args:
            interval: 监控间隔（秒）
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("监控线程已在运行")
            return
        
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"缓存监控已启动，间隔: {interval}秒")
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("缓存监控已停止")
    
    def _monitoring_loop(self, interval: int) -> None:
        """监控循环
        
        Args:
            interval: 监控间隔
        """
        while not self.stop_monitoring:
            try:
                stats = self.cache.get_stats()
                monitoring_record = {
                    "timestamp": datetime.now().isoformat(),
                    "stats": stats
                }
                
                self.monitoring_data.append(monitoring_record)
                
                # 保持最近1000条记录
                if len(self.monitoring_data) > 1000:
                    self.monitoring_data = self.monitoring_data[-1000:]
                
                # 检查缓存健康状态
                self._check_cache_health(stats)
                
            except Exception as e:
                logger.error(f"缓存监控错误: {e}")
            
            time.sleep(interval)
    
    def _check_cache_health(self, stats: Dict[str, Any]) -> None:
        """检查缓存健康状态
        
        Args:
            stats: 缓存统计信息
        """
        memory_hit_rate = stats["memory"]["hit_rate"]
        disk_hit_rate = stats["disk"]["hit_rate"]
        total_hit_rate = stats["overall"]["hit_rate"]
        
        # 检查命中率
        if total_hit_rate < 0.1:  # 低于10%的命中率
            logger.warning(f"缓存命中率较低: {total_hit_rate:.2%}")
        
        if memory_hit_rate < 0.05:  # 内存命中率低于5%
            logger.warning(f"内存缓存命中率较低: {memory_hit_rate:.2%}")
    
    def get_monitoring_report(self, hours: int = 24) -> Dict[str, Any]:
        """获取监控报告
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            监控报告
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        relevant_records = [
            record for record in self.monitoring_data
            if datetime.fromisoformat(record["timestamp"]) >= cutoff_time
        ]
        
        if not relevant_records:
            return {"message": "没有找到监控数据"}
        
        # 计算统计信息
        hit_rates = [record["stats"]["overall"]["hit_rate"] for record in relevant_records]
        memory_sizes = [record["stats"]["memory"]["size"] for record in relevant_records]
        disk_sizes = [record["stats"]["disk"]["size"] for record in relevant_records]
        
        return {
            "time_range": f"最近{hours}小时",
            "record_count": len(relevant_records),
            "average_hit_rate": sum(hit_rates) / len(hit_rates),
            "max_hit_rate": max(hit_rates),
            "min_hit_rate": min(hit_rates),
            "average_memory_size": sum(memory_sizes) / len(memory_sizes),
            "average_disk_size": sum(disk_sizes) / len(disk_sizes),
            "latest_stats": relevant_records[-1]["stats"]
        }