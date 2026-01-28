"""
内存使用监控模块

提供详细的内存使用监控功能，包括进程内存、系统内存和内存泄漏检测。
"""
import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """内存类型枚举"""
    PROCESS_RSS = "process_rss"  # 进程常驻内存
    PROCESS_VMS = "process_vms"  # 进程虚拟内存
    SYSTEM_TOTAL = "system_total"  # 系统总内存
    SYSTEM_AVAILABLE = "system_available"  # 系统可用内存
    SYSTEM_USED = "system_used"  # 系统已用内存
    SYSTEM_PERCENT = "system_percent"  # 系统内存使用百分比


class MemoryMetric:
    """内存指标类"""
    
    def __init__(self, memory_type: MemoryType, value: float, timestamp: datetime):
        """初始化内存指标
        
        Args:
            memory_type: 内存类型
            value: 指标值
            timestamp: 时间戳
        """
        self.memory_type = memory_type
        self.value = value
        self.timestamp = timestamp
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "memory_type": self.memory_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat()
        }


class MemoryStats:
    """内存统计类"""
    
    def __init__(self, window_size: int = 100):
        """初始化内存统计
        
        Args:
            window_size: 统计窗口大小
        """
        self.window_size = window_size
        self.metrics: Dict[MemoryType, deque] = {}
        for memory_type in MemoryType:
            self.metrics[memory_type] = deque(maxlen=window_size)
        self.start_time = datetime.now()
        
    def add_metric(self, metric: MemoryMetric):
        """添加内存指标
        
        Args:
            metric: 内存指标
        """
        self.metrics[metric.memory_type].append(metric)
        
    def get_memory_stats(self, memory_type: MemoryType) -> Dict[str, Any]:
        """获取指定内存类型的统计
        
        Args:
            memory_type: 内存类型
            
        Returns:
            内存统计信息
        """
        metrics = list(self.metrics[memory_type])
        
        if not metrics:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "current": 0
            }
            
        values = [m.value for m in metrics]
        current_value = metrics[-1].value if metrics else 0
        
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "current": current_value
        }
        
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有内存统计
        
        Returns:
            所有内存统计信息
        """
        stats = {}
        for memory_type in MemoryType:
            stats[memory_type.value] = self.get_memory_stats(memory_type)
            
        stats["window_size"] = self.window_size
        stats["start_time"] = self.start_time.isoformat()
        
        return stats
        
    def detect_memory_leak(self, memory_type: MemoryType, threshold: float = 0.1) -> bool:
        """检测内存泄漏
        
        Args:
            memory_type: 内存类型
            threshold: 泄漏阈值（MB/分钟）
            
        Returns:
            是否检测到内存泄漏
        """
        metrics = list(self.metrics[memory_type])
        
        if len(metrics) < 10:  # 需要足够的数据点
            return False
            
        # 计算内存增长速率
        first_value = metrics[0].value
        last_value = metrics[-1].value
        time_diff = (metrics[-1].timestamp - metrics[0].timestamp).total_seconds() / 60  # 分钟
        
        if time_diff == 0:
            return False
            
        growth_rate = (last_value - first_value) / time_diff
        
        return growth_rate > threshold


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, window_size: int = 100, interval: float = 60.0):
        """初始化内存监控器
        
        Args:
            window_size: 统计窗口大小
            interval: 监控间隔（秒）
        """
        self.stats = MemoryStats(window_size)
        self.process = psutil.Process()
        self.interval = interval
        self.last_monitor_time = 0
        
    def collect_memory_metrics(self):
        """收集内存指标"""
        current_time = time.time()
        
        # 检查是否达到监控间隔
        if current_time - self.last_monitor_time < self.interval:
            return
            
        self.last_monitor_time = current_time
        timestamp = datetime.now()
        
        try:
            # 收集进程内存信息
            process_memory = self.process.memory_info()
            
            # 进程常驻内存（RSS）
            rss_metric = MemoryMetric(
                memory_type=MemoryType.PROCESS_RSS,
                value=process_memory.rss / 1024 / 1024,  # 转换为MB
                timestamp=timestamp
            )
            self.stats.add_metric(rss_metric)
            
            # 进程虚拟内存（VMS）
            vms_metric = MemoryMetric(
                memory_type=MemoryType.PROCESS_VMS,
                value=process_memory.vms / 1024 / 1024,  # 转换为MB
                timestamp=timestamp
            )
            self.stats.add_metric(vms_metric)
            
            # 收集系统内存信息
            system_memory = psutil.virtual_memory()
            
            # 系统总内存
            total_metric = MemoryMetric(
                memory_type=MemoryType.SYSTEM_TOTAL,
                value=system_memory.total / 1024 / 1024 / 1024,  # 转换为GB
                timestamp=timestamp
            )
            self.stats.add_metric(total_metric)
            
            # 系统可用内存
            available_metric = MemoryMetric(
                memory_type=MemoryType.SYSTEM_AVAILABLE,
                value=system_memory.available / 1024 / 1024 / 1024,  # 转换为GB
                timestamp=timestamp
            )
            self.stats.add_metric(available_metric)
            
            # 系统已用内存
            used_metric = MemoryMetric(
                memory_type=MemoryType.SYSTEM_USED,
                value=system_memory.used / 1024 / 1024 / 1024,  # 转换为GB
                timestamp=timestamp
            )
            self.stats.add_metric(used_metric)
            
            # 系统内存使用百分比
            percent_metric = MemoryMetric(
                memory_type=MemoryType.SYSTEM_PERCENT,
                value=system_memory.percent,
                timestamp=timestamp
            )
            self.stats.add_metric(percent_metric)
            
        except Exception as e:
            logger.error(f"收集内存指标失败: {e}")
            
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取内存摘要
        
        Returns:
            内存摘要信息
        """
        # 确保收集最新指标
        self.collect_memory_metrics()
        
        return self.stats.get_all_stats()
        
    def check_memory_health(self) -> Dict[str, Any]:
        """检查内存健康状态
        
        Returns:
            内存健康状态信息
        """
        summary = self.get_memory_summary()
        
        # 获取关键指标
        process_rss = summary[MemoryType.PROCESS_RSS.value]["current"]
        system_percent = summary[MemoryType.SYSTEM_PERCENT.value]["current"]
        
        # 健康状态判断
        is_healthy = True
        warnings = []
        
        # 进程内存检查（超过500MB为警告）
        if process_rss > 500:
            warnings.append(f"进程内存使用过高: {process_rss:.2f}MB")
            is_healthy = False
            
        # 系统内存检查（超过80%为警告）
        if system_percent > 80:
            warnings.append(f"系统内存使用过高: {system_percent:.2f}%")
            is_healthy = False
            
        # 内存泄漏检查
        if self.stats.detect_memory_leak(MemoryType.PROCESS_RSS):
            warnings.append("检测到进程内存泄漏迹象")
            is_healthy = False
            
        return {
            "status": "healthy" if is_healthy else "warning",
            "timestamp": datetime.now().isoformat(),
            "process_rss_mb": process_rss,
            "system_memory_percent": system_percent,
            "warnings": warnings,
            "is_healthy": is_healthy
        }
        
    def get_memory_trend(self, memory_type: MemoryType, hours: int = 24) -> List[Dict[str, Any]]:
        """获取内存趋势数据
        
        Args:
            memory_type: 内存类型
            hours: 时间范围（小时）
            
        Returns:
            内存趋势数据
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指定时间范围内的指标
        recent_metrics = [
            m for m in self.stats.metrics[memory_type]
            if m.timestamp >= cutoff_time
        ]
        
        return [metric.to_dict() for metric in recent_metrics]


# 全局内存监控器实例
memory_monitor = MemoryMonitor()