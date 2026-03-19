"""数据库查询性能监控服务

监控数据库查询性能，识别慢查询，提供优化建议。
"""
import logging
import time
from typing import Dict, List, Optional, Callable
from functools import wraps
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """查询指标"""
    query: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    params: Optional[Dict] = None
    rows_affected: int = 0


class QueryPerformanceMonitor:
    """查询性能监控器
    
    监控SQL查询性能，收集统计信息，识别慢查询。
    """
    
    def __init__(self, slow_query_threshold: float = 1.0):
        """
        初始化查询性能监控器
        
        Args:
            slow_query_threshold: 慢查询阈值（秒）
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf'),
            'avg_time': 0.0
        })
        self.slow_queries: List[QueryMetrics] = []
        self.recent_queries: List[QueryMetrics] = []
        self.max_recent_queries = 1000
        self._enabled = False
    
    def enable_monitoring(self, engine: Engine):
        """启用查询监控
        
        Args:
            engine: SQLAlchemy引擎
        """
        if self._enabled:
            return
        
        # 监听查询开始事件
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        # 监听查询结束事件
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            duration = time.time() - context._query_start_time
            
            # 记录查询统计
            self._record_query(statement, duration, parameters, cursor.rowcount)
        
        self._enabled = True
        logger.info("查询性能监控已启用")
    
    def _record_query(self, query: str, duration: float, params: Optional[Dict], rowcount: int):
        """记录查询
        
        Args:
            query: SQL查询语句
            duration: 执行时间
            params: 查询参数
            rowcount: 影响的行数
        """
        # 标准化查询（去除参数值）
        normalized_query = self._normalize_query(query)
        
        # 更新统计
        stats = self.query_stats[normalized_query]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['max_time'] = max(stats['max_time'], duration)
        stats['min_time'] = min(stats['min_time'], duration)
        stats['avg_time'] = stats['total_time'] / stats['count']
        
        # 创建查询指标
        metric = QueryMetrics(
            query=normalized_query,
            duration=duration,
            params=params,
            rows_affected=rowcount
        )
        
        # 添加到最近查询列表
        self.recent_queries.append(metric)
        if len(self.recent_queries) > self.max_recent_queries:
            self.recent_queries.pop(0)
        
        # 记录慢查询
        if duration > self.slow_query_threshold:
            self.slow_queries.append(metric)
            logger.warning(f"慢查询: {normalized_query[:100]}... 耗时: {duration:.3f}s")
    
    def _normalize_query(self, query: str) -> str:
        """标准化查询语句
        
        去除参数值，使相似的查询可以聚合统计。
        
        Args:
            query: 原始查询
            
        Returns:
            标准化后的查询
        """
        # 简单的标准化：截断并清理
        query = query.strip()
        if len(query) > 200:
            query = query[:200] + "..."
        return query
    
    def get_slow_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """获取慢查询列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            慢查询列表
        """
        return sorted(
            self.slow_queries,
            key=lambda x: x.duration,
            reverse=True
        )[:limit]
    
    def get_query_stats(self, top_n: int = 10) -> List[Dict]:
        """获取查询统计
        
        Args:
            top_n: 返回前N个最慢的查询类型
            
        Returns:
            查询统计列表
        """
        sorted_stats = sorted(
            [
                {
                    'query': query,
                    **stats
                }
                for query, stats in self.query_stats.items()
            ],
            key=lambda x: x['avg_time'],
            reverse=True
        )
        
        return sorted_stats[:top_n]
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要
        
        Returns:
            性能摘要
        """
        if not self.query_stats:
            return {
                'total_queries': 0,
                'slow_queries': 0,
                'avg_response_time': 0.0,
                'max_response_time': 0.0
            }
        
        total_queries = sum(stats['count'] for stats in self.query_stats.values())
        total_time = sum(stats['total_time'] for stats in self.query_stats.values())
        max_time = max(stats['max_time'] for stats in self.query_stats.values())
        
        return {
            'total_queries': total_queries,
            'slow_queries': len(self.slow_queries),
            'avg_response_time': total_time / total_queries if total_queries > 0 else 0.0,
            'max_response_time': max_time
        }
    
    def clear_stats(self):
        """清空统计信息"""
        self.query_stats.clear()
        self.slow_queries.clear()
        self.recent_queries.clear()
        logger.info("查询统计已清空")
    
    def generate_report(self) -> str:
        """生成性能报告
        
        Returns:
            性能报告文本
        """
        summary = self.get_performance_summary()
        top_queries = self.get_query_stats(5)
        slow_queries = self.get_slow_queries(5)
        
        report = []
        report.append("=" * 60)
        report.append("数据库查询性能报告")
        report.append("=" * 60)
        report.append("")
        
        # 摘要
        report.append("性能摘要:")
        report.append(f"  总查询数: {summary['total_queries']}")
        report.append(f"  慢查询数: {summary['slow_queries']}")
        report.append(f"  平均响应时间: {summary['avg_response_time']:.3f}s")
        report.append(f"  最大响应时间: {summary['max_response_time']:.3f}s")
        report.append("")
        
        # 最慢的查询类型
        if top_queries:
            report.append("最慢的查询类型:")
            for i, stats in enumerate(top_queries, 1):
                report.append(f"  {i}. 平均: {stats['avg_time']:.3f}s, 次数: {stats['count']}")
                report.append(f"     {stats['query'][:80]}...")
            report.append("")
        
        # 具体慢查询
        if slow_queries:
            report.append("具体慢查询:")
            for i, query in enumerate(slow_queries, 1):
                report.append(f"  {i}. 耗时: {query.duration:.3f}s, 时间: {query.timestamp.strftime('%H:%M:%S')}")
                report.append(f"     {query.query[:80]}...")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


# 全局监控器实例
query_monitor = QueryPerformanceMonitor()


def monitor_query(threshold: float = 1.0):
    """查询监控装饰器
    
    Args:
        threshold: 慢查询阈值（秒）
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if duration > threshold:
                    logger.warning(f"慢查询: {func.__name__} 耗时 {duration:.3f}s")
        
        return wrapper
    return decorator


def get_query_recommendations() -> List[str]:
    """获取查询优化建议
    
    Returns:
        优化建议列表
    """
    recommendations = []
    
    stats = query_monitor.get_query_stats(10)
    
    for stat in stats:
        query = stat['query'].upper()
        
        # 检查是否需要索引
        if 'SELECT' in query and 'WHERE' in query:
            if stat['count'] > 100 and stat['avg_time'] > 0.1:
                recommendations.append(
                    f"查询 '{stat['query'][:50]}...' 执行次数多且较慢，建议添加索引"
                )
        
        # 检查是否需要分页
        if 'SELECT' in query and 'LIMIT' not in query and 'OFFSET' not in query:
            if stat['avg_time'] > 0.5:
                recommendations.append(
                    f"查询 '{stat['query'][:50]}...' 耗时较长且无分页，建议添加分页"
                )
        
        # 检查是否需要缓存
        if stat['count'] > 1000 and 'SELECT' in query:
            recommendations.append(
                f"查询 '{stat['query'][:50]}...' 执行频率高，建议添加缓存"
            )
    
    return recommendations


# 便捷函数

def print_performance_report():
    """打印性能报告"""
    report = query_monitor.generate_report()
    print(report)


def get_slow_query_summary() -> Dict:
    """获取慢查询摘要"""
    slow_queries = query_monitor.get_slow_queries(10)
    
    return {
        'count': len(query_monitor.slow_queries),
        'top_slow_queries': [
            {
                'query': q.query[:100],
                'duration': q.duration,
                'timestamp': q.timestamp.isoformat()
            }
            for q in slow_queries
        ]
    }