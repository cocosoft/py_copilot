"""内存使用优化服务

提供内存监控、泄漏检测、内存使用分析和优化建议功能。
"""
import logging
import gc
import tracemalloc
import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from collections import defaultdict, deque

from app.core.logging_config import logger


class MemorySnapshot:
    """内存快照"""
    
    def __init__(self, timestamp: datetime, stats: Dict[str, Any]):
        """
        初始化内存快照
        
        Args:
            timestamp: 快照时间
            stats: 内存统计信息
        """
        self.timestamp = timestamp
        self.stats = stats
        self.diff = None  # 与上一个快照的差异
    
    def calculate_diff(self, previous_snapshot):
        """计算与上一个快照的差异"""
        if not previous_snapshot:
            return
        
        self.diff = {}
        for key, value in self.stats.items():
            if key in previous_snapshot.stats:
                self.diff[key] = value - previous_snapshot.stats[key]
    
    def to_dict(self):
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "stats": self.stats,
            "diff": self.diff
        }


class MemoryAnalyzer:
    """内存分析器"""
    
    def __init__(self, window_size: int = 60):
        """
        初始化内存分析器
        
        Args:
            window_size: 分析窗口大小（分钟）
        """
        self.window_size = window_size
        self.snapshots = deque(maxlen=window_size * 60 // 5)  # 每5秒一个快照
        self.peak_memory = 0
        self.memory_trend = []
        self.thread = None
        self.running = False
        self.loop = None
    
    def start(self):
        """开始内存分析"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._collect_memory_stats, daemon=True)
        self.thread.start()
        logger.info("内存分析器已启动")
    
    def stop(self):
        """停止内存分析"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("内存分析器已停止")
    
    def _collect_memory_stats(self):
        """收集内存统计信息"""
        while self.running:
            try:
                snapshot = self._create_memory_snapshot()
                self.snapshots.append(snapshot)
                
                # 计算与上一个快照的差异
                if len(self.snapshots) > 1:
                    current = self.snapshots[-1]
                    previous = self.snapshots[-2]
                    current.calculate_diff(previous)
                
                # 更新峰值内存
                current_memory = snapshot.stats['rss']
                if current_memory > self.peak_memory:
                    self.peak_memory = current_memory
                
                # 更新内存趋势
                self.memory_trend.append({
                    'timestamp': snapshot.timestamp,
                    'memory': current_memory
                })
                
                # 保持趋势数据在窗口内
                cutoff_time = datetime.now() - timedelta(minutes=self.window_size)
                self.memory_trend = [t for t in self.memory_trend if t['timestamp'] > cutoff_time]
                
                time.sleep(5)  # 每5秒收集一次
            except Exception as e:
                logger.error(f"收集内存统计信息失败: {str(e)}")
                time.sleep(5)
    
    def _create_memory_snapshot(self) -> MemorySnapshot:
        """创建内存快照"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        stats = {
            'rss': memory_info.rss,  # 物理内存使用
            'vms': memory_info.vms,  # 虚拟内存使用
            'shared': memory_info.shared,  # 共享内存
            'text': memory_info.text,  # 代码段
            'data': memory_info.data,  # 数据段
            'percent': memory_percent,  # 内存使用率
            'num_threads': process.num_threads(),  # 线程数
            'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0  # 文件描述符数
        }
        
        return MemorySnapshot(datetime.now(), stats)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        if not self.snapshots:
            return {}
        
        latest_snapshot = self.snapshots[-1]
        
        # 计算平均值
        rss_values = [s.stats['rss'] for s in self.snapshots]
        avg_rss = sum(rss_values) / len(rss_values)
        
        # 计算内存增长率
        memory_growth_rate = 0
        if len(self.snapshots) > 1:
            first_rss = self.snapshots[0].stats['rss']
            last_rss = self.snapshots[-1].stats['rss']
            if first_rss > 0:
                memory_growth_rate = ((last_rss - first_rss) / first_rss) * 100
        
        return {
            'current': latest_snapshot.to_dict(),
            'peak': self.peak_memory,
            'average': avg_rss,
            'growth_rate': memory_growth_rate,
            'snapshots_count': len(self.snapshots),
            'window_size': self.window_size
        }
    
    def detect_memory_leak(self) -> Dict[str, Any]:
        """检测内存泄漏"""
        if len(self.snapshots) < 10:
            return {'detected': False, 'reason': '数据不足'}
        
        # 检查内存是否持续增长
        rss_values = [s.stats['rss'] for s in self.snapshots]
        
        # 计算趋势
        increasing_count = 0
        for i in range(1, len(rss_values)):
            if rss_values[i] > rss_values[i-1] * 1.01:  # 增长超过1%
                increasing_count += 1
        
        # 如果80%的时间内存都在增长，可能存在内存泄漏
        leak_probability = increasing_count / (len(rss_values) - 1)
        
        if leak_probability > 0.8:
            return {
                'detected': True,
                'probability': leak_probability,
                'message': '检测到可能的内存泄漏，内存持续增长'
            }
        
        return {'detected': False, 'probability': leak_probability}
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        if not self.snapshots:
            return suggestions
        
        latest_snapshot = self.snapshots[-1]
        memory_percent = latest_snapshot.stats['percent']
        rss = latest_snapshot.stats['rss']
        
        # 内存使用率高
        if memory_percent > 80:
            suggestions.append('内存使用率过高，建议检查内存密集型操作')
        elif memory_percent > 60:
            suggestions.append('内存使用率较高，建议优化内存使用')
        
        # 内存增长过快
        growth_rate = self.get_memory_stats()['growth_rate']
        if growth_rate > 50:  # 50%增长
            suggestions.append('内存增长过快，可能存在内存泄漏')
        
        # 线程数过多
        num_threads = latest_snapshot.stats['num_threads']
        if num_threads > 50:
            suggestions.append('线程数过多，建议优化线程管理')
        
        return suggestions
    
    def generate_report(self) -> Dict[str, Any]:
        """生成内存使用报告"""
        stats = self.get_memory_stats()
        leak_detection = self.detect_memory_leak()
        suggestions = self.get_optimization_suggestions()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'memory_stats': stats,
            'leak_detection': leak_detection,
            'optimization_suggestions': suggestions,
            'memory_trend': self.memory_trend
        }


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        """初始化内存优化器"""
        self.analyzer = MemoryAnalyzer()
        self.tracemalloc_started = False
        self.optimization_history = []
    
    def start_monitoring(self):
        """开始内存监控"""
        self.analyzer.start()
        self._start_tracemalloc()
        logger.info("内存监控已启动")
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.analyzer.stop()
        self._stop_tracemalloc()
        logger.info("内存监控已停止")
    
    def _start_tracemalloc(self):
        """启动内存跟踪"""
        if not self.tracemalloc_started:
            try:
                tracemalloc.start(10)  # 保留10帧堆栈
                self.tracemalloc_started = True
                logger.info("内存跟踪已启动")
            except Exception as e:
                logger.warning(f"启动内存跟踪失败: {str(e)}")
    
    def _stop_tracemalloc(self):
        """停止内存跟踪"""
        if self.tracemalloc_started:
            try:
                tracemalloc.stop()
                self.tracemalloc_started = False
                logger.info("内存跟踪已停止")
            except Exception as e:
                logger.warning(f"停止内存跟踪失败: {str(e)}")
    
    def optimize_memory(self) -> Dict[str, Any]:
        """执行内存优化"""
        start_time = time.time()
        
        # 执行垃圾回收
        gc.collect()
        
        # 清理循环引用
        self._break_cycles()
        
        # 再次执行垃圾回收
        gc.collect()
        
        # 记录优化结果
        optimization_result = {
            'timestamp': datetime.now().isoformat(),
            'duration': time.time() - start_time,
            'memory_before': psutil.Process().memory_info().rss,
            'memory_after': psutil.Process().memory_info().rss
        }
        
        optimization_result['freed_memory'] = optimization_result['memory_before'] - optimization_result['memory_after']
        self.optimization_history.append(optimization_result)
        
        logger.info(f"内存优化完成，释放内存: {optimization_result['freed_memory'] / 1024 / 1024:.2f} MB")
        
        return optimization_result
    
    def _break_cycles(self):
        """打破循环引用"""
        try:
            # 强制打破循环引用
            gc.collect(2)  # 执行完全垃圾回收
        except Exception as e:
            logger.warning(f"打破循环引用失败: {str(e)}")
    
    def get_top_memory_consumers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取内存消耗最多的对象"""
        consumers = []
        
        if not self.tracemalloc_started:
            return consumers
        
        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            for stat in top_stats[:limit]:
                consumers.append({
                    'filename': stat.traceback[0].filename,
                    'lineno': stat.traceback[0].lineno,
                    'size': stat.size,
                    'count': stat.count
                })
        except Exception as e:
            logger.error(f"获取内存消耗者失败: {str(e)}")
        
        return consumers
    
    def get_memory_report(self) -> Dict[str, Any]:
        """获取内存使用报告"""
        report = self.analyzer.generate_report()
        report['top_consumers'] = self.get_top_memory_consumers()
        report['optimization_history'] = self.optimization_history
        
        return report
    
    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存状态"""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'process': {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent(),
                'num_threads': process.num_threads()
            },
            'system': {
                'total': system_memory.total,
                'available': system_memory.available,
                'used': system_memory.used,
                'percent': system_memory.percent
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def auto_optimize(self, threshold: float = 70.0):
        """自动优化内存
        
        Args:
            threshold: 内存使用率阈值（%）
        """
        memory_status = self.get_memory_status()
        memory_percent = memory_status['process']['percent']
        
        if memory_percent > threshold:
            logger.info(f"内存使用率超过阈值 ({memory_percent:.1f}% > {threshold}%)，执行自动优化")
            return self.optimize_memory()
        
        return None


# 全局内存优化器实例
memory_optimizer = MemoryOptimizer()


# 后台内存监控任务
async def memory_monitoring_task():
    """后台内存监控任务"""
    memory_optimizer.start_monitoring()
    
    try:
        while True:
            # 每5分钟检查一次内存使用情况
            await asyncio.sleep(300)
            
            # 自动优化内存
            optimization_result = memory_optimizer.auto_optimize()
            if optimization_result:
                logger.info(f"自动内存优化结果: {optimization_result}")
            
            # 检查内存泄漏
            memory_report = memory_optimizer.get_memory_report()
            if memory_report['leak_detection']['detected']:
                logger.warning(f"内存泄漏检测: {memory_report['leak_detection']}")
                
    except asyncio.CancelledError:
        logger.info("内存监控任务已取消")
    finally:
        memory_optimizer.stop_monitoring()


# 便捷函数

def start_memory_monitoring():
    """开始内存监控"""
    memory_optimizer.start_monitoring()


def stop_memory_monitoring():
    """停止内存监控"""
    memory_optimizer.stop_monitoring()


def optimize_memory():
    """优化内存"""
    return memory_optimizer.optimize_memory()


def get_memory_report():
    """获取内存报告"""
    return memory_optimizer.get_memory_report()


def get_memory_status():
    """获取内存状态"""
    return memory_optimizer.get_memory_status()


def get_top_memory_consumers(limit: int = 10):
    """获取内存消耗最多的对象"""
    return memory_optimizer.get_top_memory_consumers(limit)


def auto_optimize_memory(threshold: float = 70.0):
    """自动优化内存"""
    return memory_optimizer.auto_optimize(threshold)
