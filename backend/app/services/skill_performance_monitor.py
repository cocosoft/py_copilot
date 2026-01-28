"""
技能执行性能监控器
监控技能执行性能，分析瓶颈，提供优化建议
"""

import time
import asyncio
import statistics
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
import threading
import psutil

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """执行指标数据类"""
    skill_id: str
    execution_id: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    input_size: int = 0
    output_size: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    @property
    def execution_time(self) -> float:
        """计算执行时间"""
        if self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def throughput(self) -> float:
        """计算吞吐量（数据量/时间）"""
        if self.execution_time > 0:
            return (self.input_size + self.output_size) / self.execution_time
        return 0.0


@dataclass
class PerformanceStats:
    """性能统计数据类"""
    skill_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time: float = 0.0
    min_execution_time: float = 0.0
    max_execution_time: float = 0.0
    p95_execution_time: float = 0.0
    p99_execution_time: float = 0.0
    avg_memory_usage: float = 0.0
    avg_cpu_usage: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    
    def update(self, metrics: ExecutionMetrics):
        """更新统计数据"""
        self.total_executions += 1
        
        if metrics.success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        # 计算错误率
        self.error_rate = self.failed_executions / self.total_executions
        
        # 更新执行时间统计
        execution_time = metrics.execution_time
        if self.total_executions == 1:
            self.avg_execution_time = execution_time
            self.min_execution_time = execution_time
            self.max_execution_time = execution_time
        else:
            self.avg_execution_time = (
                (self.avg_execution_time * (self.total_executions - 1) + execution_time) 
                / self.total_executions
            )
            self.min_execution_time = min(self.min_execution_time, execution_time)
            self.max_execution_time = max(self.max_execution_time, execution_time)
        
        # 更新资源使用统计
        self.avg_memory_usage = (
            (self.avg_memory_usage * (self.total_executions - 1) + metrics.memory_usage_mb) 
            / self.total_executions
        )
        self.avg_cpu_usage = (
            (self.avg_cpu_usage * (self.total_executions - 1) + metrics.cpu_usage_percent) 
            / self.total_executions
        )
        
        # 更新吞吐量
        self.throughput = (
            (self.throughput * (self.total_executions - 1) + metrics.throughput) 
            / self.total_executions
        )


class SkillPerformanceMonitor:
    """技能性能监控器"""
    
    def __init__(self, max_history_size: int = 1000, window_size: int = 100):
        """初始化性能监控器
        
        Args:
            max_history_size: 最大历史记录数
            window_size: 滑动窗口大小
        """
        self.max_history_size = max_history_size
        self.window_size = window_size
        
        # 执行历史记录
        self.execution_history: Dict[str, List[ExecutionMetrics]] = defaultdict(list)
        
        # 性能统计数据
        self.performance_stats: Dict[str, PerformanceStats] = {}
        
        # 滑动窗口数据（用于实时分析）
        self.sliding_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        
        # 性能阈值配置
        self.performance_thresholds = {
            "execution_time": 5.0,  # 5秒
            "memory_usage": 500.0,  # 500MB
            "cpu_usage": 80.0,      # 80%
            "error_rate": 0.05      # 5%
        }
        
        # 性能事件监听器
        self.performance_event_handlers: List[Callable] = []
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 基准性能数据
        self.baseline_performance: Dict[str, Dict[str, float]] = {}
    
    def start_monitoring_execution(self, skill_id: str, execution_id: str, 
                                 input_data: Dict[str, Any]) -> ExecutionMetrics:
        """开始监控技能执行
        
        Args:
            skill_id: 技能ID
            execution_id: 执行ID
            input_data: 输入数据
            
        Returns:
            执行指标对象
        """
        metrics = ExecutionMetrics(
            skill_id=skill_id,
            execution_id=execution_id,
            start_time=time.time(),
            input_size=len(str(input_data))
        )
        
        # 记录初始系统资源使用
        metrics.memory_usage_mb = self._get_memory_usage()
        metrics.cpu_usage_percent = self._get_cpu_usage()
        
        return metrics
    
    def end_monitoring_execution(self, metrics: ExecutionMetrics, 
                               success: bool = True, error: str = None,
                               output_data: Dict[str, Any] = None):
        """结束监控技能执行
        
        Args:
            metrics: 执行指标对象
            success: 是否成功
            error: 错误信息
            output_data: 输出数据
        """
        metrics.end_time = time.time()
        metrics.success = success
        metrics.error = error
        
        if output_data:
            metrics.output_size = len(str(output_data))
        
        # 记录最终系统资源使用
        metrics.memory_usage_mb = self._get_memory_usage()
        metrics.cpu_usage_percent = self._get_cpu_usage()
        
        # 保存执行记录
        self._save_execution_metrics(metrics)
        
        # 检查性能阈值
        self._check_performance_thresholds(metrics)
        
        logger.info(f"技能执行监控完成: {metrics.skill_id}, 时间: {metrics.execution_time:.3f}s")
    
    def _save_execution_metrics(self, metrics: ExecutionMetrics):
        """保存执行指标"""
        with self._lock:
            skill_id = metrics.skill_id
            
            # 添加到历史记录
            self.execution_history[skill_id].append(metrics)
            
            # 限制历史记录大小
            if len(self.execution_history[skill_id]) > self.max_history_size:
                self.execution_history[skill_id].pop(0)
            
            # 更新滑动窗口
            self.sliding_windows[skill_id].append(metrics)
            
            # 更新性能统计数据
            if skill_id not in self.performance_stats:
                self.performance_stats[skill_id] = PerformanceStats(skill_id=skill_id)
            
            self.performance_stats[skill_id].update(metrics)
    
    def _check_performance_thresholds(self, metrics: ExecutionMetrics):
        """检查性能阈值"""
        alerts = []
        
        # 检查执行时间阈值
        if metrics.execution_time > self.performance_thresholds["execution_time"]:
            alerts.append({
                "type": "execution_time",
                "message": f"执行时间过长: {metrics.execution_time:.3f}s",
                "threshold": self.performance_thresholds["execution_time"],
                "actual": metrics.execution_time
            })
        
        # 检查内存使用阈值
        if metrics.memory_usage_mb > self.performance_thresholds["memory_usage"]:
            alerts.append({
                "type": "memory_usage",
                "message": f"内存使用过高: {metrics.memory_usage_mb:.1f}MB",
                "threshold": self.performance_thresholds["memory_usage"],
                "actual": metrics.memory_usage_mb
            })
        
        # 检查CPU使用阈值
        if metrics.cpu_usage_percent > self.performance_thresholds["cpu_usage"]:
            alerts.append({
                "type": "cpu_usage",
                "message": f"CPU使用过高: {metrics.cpu_usage_percent:.1f}%",
                "threshold": self.performance_thresholds["cpu_usage"],
                "actual": metrics.cpu_usage_percent
            })
        
        # 触发性能事件
        if alerts:
            self._trigger_performance_events(metrics, alerts)
    
    def _trigger_performance_events(self, metrics: ExecutionMetrics, alerts: List[Dict]):
        """触发性能事件"""
        event_data = {
            "skill_id": metrics.skill_id,
            "execution_id": metrics.execution_id,
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "metrics": {
                "execution_time": metrics.execution_time,
                "memory_usage": metrics.memory_usage_mb,
                "cpu_usage": metrics.cpu_usage_percent
            }
        }
        
        for handler in self.performance_event_handlers:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"性能事件处理失败: {e}")
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # 转换为MB
    
    def _get_cpu_usage(self) -> float:
        """获取CPU使用率（%）"""
        process = psutil.Process()
        return process.cpu_percent()
    
    def get_performance_stats(self, skill_id: str, 
                            time_range: Optional[timedelta] = None) -> Optional[PerformanceStats]:
        """获取性能统计数据
        
        Args:
            skill_id: 技能ID
            time_range: 时间范围
            
        Returns:
            性能统计数据
        """
        if skill_id not in self.performance_stats:
            return None
        
        if not time_range:
            return self.performance_stats[skill_id]
        
        # 根据时间范围筛选数据
        cutoff_time = time.time() - time_range.total_seconds()
        
        filtered_metrics = [
            m for m in self.execution_history[skill_id]
            if m.start_time >= cutoff_time
        ]
        
        if not filtered_metrics:
            return None
        
        # 计算筛选后的统计数据
        stats = PerformanceStats(skill_id=skill_id)
        for metrics in filtered_metrics:
            stats.update(metrics)
        
        return stats
    
    def get_performance_trend(self, skill_id: str, 
                            window_size: int = 10) -> List[Dict[str, Any]]:
        """获取性能趋势数据
        
        Args:
            skill_id: 技能ID
            window_size: 窗口大小
            
        Returns:
            性能趋势数据
        """
        if skill_id not in self.execution_history:
            return []
        
        metrics_list = self.execution_history[skill_id]
        if len(metrics_list) < window_size:
            return []
        
        trends = []
        for i in range(0, len(metrics_list), window_size):
            window_metrics = metrics_list[i:i + window_size]
            
            if not window_metrics:
                continue
            
            execution_times = [m.execution_time for m in window_metrics]
            memory_usages = [m.memory_usage_mb for m in window_metrics]
            cpu_usages = [m.cpu_usage_percent for m in window_metrics]
            
            trends.append({
                "window_start": i,
                "window_end": i + len(window_metrics) - 1,
                "avg_execution_time": statistics.mean(execution_times),
                "avg_memory_usage": statistics.mean(memory_usages),
                "avg_cpu_usage": statistics.mean(cpu_usages),
                "sample_count": len(window_metrics)
            })
        
        return trends
    
    def detect_performance_anomalies(self, skill_id: str) -> List[Dict[str, Any]]:
        """检测性能异常
        
        Args:
            skill_id: 技能ID
            
        Returns:
            异常检测结果
        """
        if skill_id not in self.execution_history:
            return []
        
        metrics_list = self.execution_history[skill_id]
        if len(metrics_list) < 10:  # 至少需要10个样本
            return []
        
        anomalies = []
        
        # 计算执行时间的统计特征
        execution_times = [m.execution_time for m in metrics_list]
        mean_time = statistics.mean(execution_times)
        std_time = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        
        # 检测异常值（3σ原则）
        for i, metrics in enumerate(metrics_list):
            if std_time > 0:
                z_score = abs(metrics.execution_time - mean_time) / std_time
                
                if z_score > 3:  # 3个标准差以外的值视为异常
                    anomalies.append({
                        "index": i,
                        "execution_id": metrics.execution_id,
                        "type": "execution_time_anomaly",
                        "z_score": z_score,
                        "actual_time": metrics.execution_time,
                        "expected_range": f"{mean_time - 3*std_time:.3f} - {mean_time + 3*std_time:.3f}s"
                    })
        
        return anomalies
    
    def set_baseline_performance(self, skill_id: str, baseline_data: Dict[str, float]):
        """设置基准性能数据
        
        Args:
            skill_id: 技能ID
            baseline_data: 基准数据
        """
        self.baseline_performance[skill_id] = baseline_data
    
    def compare_with_baseline(self, skill_id: str) -> Dict[str, Any]:
        """与基准性能比较
        
        Args:
            skill_id: 技能ID
            
        Returns:
            比较结果
        """
        if skill_id not in self.baseline_performance:
            return {"error": "未设置基准性能数据"}
        
        if skill_id not in self.performance_stats:
            return {"error": "无性能统计数据"}
        
        baseline = self.baseline_performance[skill_id]
        current = self.performance_stats[skill_id]
        
        comparison = {
            "skill_id": skill_id,
            "comparison_time": datetime.now().isoformat(),
            "metrics": {}
        }
        
        # 比较执行时间
        if "avg_execution_time" in baseline:
            baseline_time = baseline["avg_execution_time"]
            current_time = current.avg_execution_time
            improvement = ((baseline_time - current_time) / baseline_time) * 100
            
            comparison["metrics"]["execution_time"] = {
                "baseline": baseline_time,
                "current": current_time,
                "improvement": improvement,
                "status": "improved" if improvement > 0 else "degraded"
            }
        
        # 比较内存使用
        if "avg_memory_usage" in baseline:
            baseline_memory = baseline["avg_memory_usage"]
            current_memory = current.avg_memory_usage
            improvement = ((baseline_memory - current_memory) / baseline_memory) * 100
            
            comparison["metrics"]["memory_usage"] = {
                "baseline": baseline_memory,
                "current": current_memory,
                "improvement": improvement,
                "status": "improved" if improvement > 0 else "degraded"
            }
        
        return comparison
    
    def add_performance_event_handler(self, handler: Callable):
        """添加性能事件处理器"""
        self.performance_event_handlers.append(handler)
    
    def get_system_resources(self) -> Dict[str, Any]:
        """获取系统资源状态"""
        return {
            "memory": {
                "total": psutil.virtual_memory().total / 1024 / 1024,  # MB
                "available": psutil.virtual_memory().available / 1024 / 1024,
                "used": psutil.virtual_memory().used / 1024 / 1024,
                "percent": psutil.virtual_memory().percent
            },
            "cpu": {
                "percent": psutil.cpu_percent(),
                "count": psutil.cpu_count()
            },
            "disk": {
                "total": psutil.disk_usage('/').total / 1024 / 1024 / 1024,  # GB
                "used": psutil.disk_usage('/').used / 1024 / 1024 / 1024,
                "free": psutil.disk_usage('/').free / 1024 / 1024 / 1024,
                "percent": psutil.disk_usage('/').percent
            }
        }


# 创建全局性能监控器实例
skill_performance_monitor = SkillPerformanceMonitor()