"""
数据库索引优化工具 - DB-002

提供索引分析、优化建议、性能测试等功能

@task DB-002
@phase 数据库任务
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from sqlalchemy import text, Index, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.sql import select, func

from app.models.base import Base

logger = logging.getLogger(__name__)


class IndexType(Enum):
    """索引类型"""
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    FULLTEXT = "fulltext"


class IndexRecommendation(Enum):
    """索引优化建议类型"""
    CREATE = "create"
    DROP = "drop"
    MODIFY = "modify"
    KEEP = "keep"


@dataclass
class IndexInfo:
    """索引信息"""
    name: str
    table_name: str
    columns: List[str]
    is_unique: bool = False
    is_primary: bool = False
    index_type: str = "btree"
    size_bytes: int = 0
    usage_count: int = 0
    last_used: Optional[str] = None


@dataclass
class QueryPattern:
    """查询模式"""
    query_template: str
    table_name: str
    where_columns: List[str]
    order_by_columns: List[str] = field(default_factory=list)
    join_columns: List[str] = field(default_factory=list)
    execution_count: int = 0
    avg_execution_time: float = 0.0


@dataclass
class IndexRecommendationResult:
    """索引优化建议结果"""
    recommendation: IndexRecommendation
    table_name: str
    index_name: str
    columns: List[str]
    reason: str
    expected_benefit: str
    priority: str  # high, medium, low


class IndexAnalyzer:
    """
    索引分析器
    
    分析数据库索引使用情况，提供优化建议
    """
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)
    
    def analyze_table_indexes(self, table_name: str) -> List[IndexInfo]:
        """
        分析表的索引情况
        
        Args:
            table_name: 表名
            
        Returns:
            索引信息列表
        """
        indexes = []
        
        try:
            # 获取表索引信息
            index_info = self.inspector.get_indexes(table_name)
            
            for idx in index_info:
                index = IndexInfo(
                    name=idx['name'],
                    table_name=table_name,
                    columns=idx['column_names'],
                    is_unique=idx.get('unique', False),
                    index_type=idx.get('type', 'btree')
                )
                
                # 获取索引大小和使用情况（PostgreSQL）
                if self.engine.dialect.name == 'postgresql':
                    size_query = text("""
                        SELECT pg_size_pretty(pg_relation_size(indexrelid)) as size
                        FROM pg_stat_user_indexes
                        WHERE indexrelname = :index_name
                    """)
                    result = self.engine.execute(size_query, {"index_name": idx['name']})
                    row = result.fetchone()
                    if row:
                        index.size_bytes = self._parse_size(row[0])
                
                indexes.append(index)
            
            # 获取主键信息
            pk_info = self.inspector.get_pk_constraint(table_name)
            if pk_info:
                pk_index = IndexInfo(
                    name=pk_info.get('name', f"pk_{table_name}"),
                    table_name=table_name,
                    columns=pk_info.get('constrained_columns', []),
                    is_primary=True,
                    is_unique=True
                )
                indexes.append(pk_index)
            
        except Exception as e:
            logger.error(f"分析表 {table_name} 索引失败: {e}")
        
        return indexes
    
    def analyze_all_tables(self) -> Dict[str, List[IndexInfo]]:
        """
        分析所有表的索引
        
        Returns:
            表名到索引列表的映射
        """
        result = {}
        
        try:
            table_names = self.inspector.get_table_names()
            
            for table_name in table_names:
                if table_name.startswith('alembic_'):
                    continue
                
                indexes = self.analyze_table_indexes(table_name)
                result[table_name] = indexes
                
        except Exception as e:
            logger.error(f"分析所有表索引失败: {e}")
        
        return result
    
    def find_missing_indexes(self, query_patterns: List[QueryPattern]) -> List[IndexRecommendationResult]:
        """
        根据查询模式找出缺失的索引
        
        Args:
            query_patterns: 查询模式列表
            
        Returns:
            索引优化建议列表
        """
        recommendations = []
        
        # 按表分组查询模式
        table_patterns = defaultdict(list)
        for pattern in query_patterns:
            table_patterns[pattern.table_name].append(pattern)
        
        for table_name, patterns in table_patterns.items():
            # 获取现有索引
            existing_indexes = self.analyze_table_indexes(table_name)
            existing_columns = set()
            for idx in existing_indexes:
                existing_columns.update(idx.columns)
            
            # 分析WHERE条件列
            where_column_freq = defaultdict(int)
            for pattern in patterns:
                for col in pattern.where_columns:
                    where_column_freq[col] += pattern.execution_count
            
            # 找出高频查询但无索引的列
            for col, freq in where_column_freq.items():
                if col not in existing_columns and freq > 100:
                    recommendations.append(IndexRecommendationResult(
                        recommendation=IndexRecommendation.CREATE,
                        table_name=table_name,
                        index_name=f"idx_{table_name}_{col}",
                        columns=[col],
                        reason=f"列 {col} 在WHERE条件中高频使用({freq}次)但无索引",
                        expected_benefit=f"预计减少查询时间50-80%",
                        priority="high" if freq > 1000 else "medium"
                    ))
            
            # 分析复合索引需求
            multi_col_patterns = [p for p in patterns if len(p.where_columns) > 1]
            for pattern in multi_col_patterns:
                if pattern.execution_count > 50:
                    recommendations.append(IndexRecommendationResult(
                        recommendation=IndexRecommendation.CREATE,
                        table_name=table_name,
                        index_name=f"idx_{table_name}_{'_'.join(pattern.where_columns[:2])}",
                        columns=pattern.where_columns[:2],
                        reason=f"多列WHERE条件高频使用({pattern.execution_count}次)",
                        expected_benefit="减少回表查询，提高复合条件过滤效率",
                        priority="medium"
                    ))
        
        return recommendations
    
    def find_unused_indexes(self, min_days: int = 30) -> List[IndexRecommendationResult]:
        """
        找出未使用的索引
        
        Args:
            min_days: 最少未使用天数
            
        Returns:
            索引优化建议列表
        """
        recommendations = []
        
        try:
            if self.engine.dialect.name == 'postgresql':
                query = text("""
                    SELECT 
                        schemaname,
                        relname as table_name,
                        indexrelname as index_name,
                        idx_scan as usage_count,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                    AND indexrelname NOT LIKE 'pg_toast%'
                    AND indexrelname NOT LIKE 'pk_%'
                    ORDER BY pg_relation_size(indexrelid) DESC
                """)
                
                result = self.engine.execute(query)
                for row in result:
                    recommendations.append(IndexRecommendationResult(
                        recommendation=IndexRecommendation.DROP,
                        table_name=row[1],
                        index_name=row[2],
                        columns=[],
                        reason=f"索引从未被使用(扫描次数: {row[3]})",
                        expected_benefit=f"释放存储空间({row[4]})",
                        priority="low"
                    ))
            
        except Exception as e:
            logger.error(f"查找未使用索引失败: {e}")
        
        return recommendations
    
    def find_duplicate_indexes(self) -> List[IndexRecommendationResult]:
        """
        找出重复或冗余的索引
        
        Returns:
            索引优化建议列表
        """
        recommendations = []
        
        try:
            if self.engine.dialect.name == 'postgresql':
                query = text("""
                    SELECT 
                        t.tablename,
                        array_agg(i.indexname ORDER BY i.indexname) as indexes,
                        array_agg(array_agg(a.attname ORDER BY array_position(i.indexdef::text, a.attname::text))
                                  ORDER BY i.indexname) as columns
                    FROM pg_indexes i
                    JOIN pg_tables t ON i.tablename = t.tablename
                    JOIN pg_class c ON c.relname = i.indexname
                    JOIN pg_index pi ON pi.indexrelid = c.oid
                    JOIN pg_attribute a ON a.attrelid = pi.indrelid AND a.attnum = ANY(pi.indkey)
                    WHERE t.schemaname = 'public'
                    GROUP BY t.tablename
                    HAVING count(*) > 1
                """)
                
                result = self.engine.execute(query)
                for row in result:
                    table_name = row[0]
                    indexes = row[1]
                    columns_list = row[2]
                    
                    # 检查前缀重复的索引
                    for i in range(len(columns_list)):
                        for j in range(i + 1, len(columns_list)):
                            cols_i = set(columns_list[i])
                            cols_j = set(columns_list[j])
                            
                            if cols_i.issubset(cols_j) or cols_j.issubset(cols_i):
                                redundant_idx = indexes[i] if len(cols_i) < len(cols_j) else indexes[j]
                                keep_idx = indexes[j] if len(cols_i) < len(cols_j) else indexes[i]
                                
                                recommendations.append(IndexRecommendationResult(
                                    recommendation=IndexRecommendation.DROP,
                                    table_name=table_name,
                                    index_name=redundant_idx,
                                    columns=columns_list[i] if len(cols_i) < len(cols_j) else columns_list[j],
                                    reason=f"索引 {redundant_idx} 是 {keep_idx} 的前缀子集",
                                    expected_benefit="减少索引维护开销，释放存储空间",
                                    priority="medium"
                                ))
            
        except Exception as e:
            logger.error(f"查找重复索引失败: {e}")
        
        return recommendations
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """
        生成索引优化报告
        
        Returns:
            优化报告字典
        """
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "database_type": self.engine.dialect.name,
            "tables_analyzed": 0,
            "total_indexes": 0,
            "recommendations": [],
            "summary": {}
        }
        
        # 分析所有表
        all_indexes = self.analyze_all_tables()
        report["tables_analyzed"] = len(all_indexes)
        report["total_indexes"] = sum(len(idxs) for idxs in all_indexes.values())
        
        # 查找未使用的索引
        unused = self.find_unused_indexes()
        report["recommendations"].extend(unused)
        
        # 查找重复索引
        duplicates = self.find_duplicate_indexes()
        report["recommendations"].extend(duplicates)
        
        # 汇总
        report["summary"] = {
            "total_recommendations": len(report["recommendations"]),
            "create_count": len([r for r in report["recommendations"] if r.recommendation == IndexRecommendation.CREATE]),
            "drop_count": len([r for r in report["recommendations"] if r.recommendation == IndexRecommendation.DROP]),
            "modify_count": len([r for r in report["recommendations"] if r.recommendation == IndexRecommendation.MODIFY]),
            "high_priority": len([r for r in report["recommendations"] if r.priority == "high"]),
            "medium_priority": len([r for r in report["recommendations"] if r.priority == "medium"]),
            "low_priority": len([r for r in report["recommendations"] if r.priority == "low"])
        }
        
        return report
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节数"""
        units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        
        parts = size_str.split()
        if len(parts) == 2:
            value = float(parts[0])
            unit = parts[1].upper()
            return int(value * units.get(unit, 1))
        return 0


class IndexOptimizer:
    """
    索引优化器
    
    执行索引创建、删除、修改等操作
    """
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.analyzer = IndexAnalyzer(engine)
    
    def create_index(self, table_name: str, index_name: str, columns: List[str],
                     unique: bool = False, index_type: str = "btree") -> bool:
        """
        创建索引
        
        Args:
            table_name: 表名
            index_name: 索引名
            columns: 列名列表
            unique: 是否唯一索引
            index_type: 索引类型
            
        Returns:
            是否成功
        """
        try:
            unique_str = "UNIQUE" if unique else ""
            columns_str = ", ".join(columns)
            
            if self.engine.dialect.name == 'postgresql':
                query = text(f"""
                    CREATE {unique_str} INDEX CONCURRENTLY IF NOT EXISTS {index_name}
                    ON {table_name} USING {index_type} ({columns_str})
                """)
            else:
                query = text(f"""
                    CREATE {unique_str} INDEX IF NOT EXISTS {index_name}
                    ON {table_name} ({columns_str})
                """)
            
            self.engine.execute(query)
            logger.info(f"创建索引 {index_name} 成功")
            return True
            
        except Exception as e:
            logger.error(f"创建索引 {index_name} 失败: {e}")
            return False
    
    def drop_index(self, table_name: str, index_name: str) -> bool:
        """
        删除索引
        
        Args:
            table_name: 表名
            index_name: 索引名
            
        Returns:
            是否成功
        """
        try:
            if self.engine.dialect.name == 'postgresql':
                query = text(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}")
            else:
                query = text(f"DROP INDEX IF EXISTS {index_name}")
            
            self.engine.execute(query)
            logger.info(f"删除索引 {index_name} 成功")
            return True
            
        except Exception as e:
            logger.error(f"删除索引 {index_name} 失败: {e}")
            return False
    
    def apply_recommendations(self, recommendations: List[IndexRecommendationResult],
                              dry_run: bool = True) -> Dict[str, List[str]]:
        """
        应用索引优化建议
        
        Args:
            recommendations: 优化建议列表
            dry_run: 是否仅预览不执行
            
        Returns:
            执行结果
        """
        results = {
            "executed": [],
            "failed": [],
            "skipped": []
        }
        
        for rec in recommendations:
            if rec.priority == "low" and not dry_run:
                results["skipped"].append(f"{rec.index_name}: 低优先级跳过")
                continue
            
            if rec.recommendation == IndexRecommendation.CREATE:
                if dry_run:
                    results["executed"].append(f"[DRY RUN] 将创建索引: {rec.index_name} ON {rec.table_name}({', '.join(rec.columns)})")
                else:
                    success = self.create_index(rec.table_name, rec.index_name, rec.columns)
                    if success:
                        results["executed"].append(f"创建索引成功: {rec.index_name}")
                    else:
                        results["failed"].append(f"创建索引失败: {rec.index_name}")
            
            elif rec.recommendation == IndexRecommendation.DROP:
                if dry_run:
                    results["executed"].append(f"[DRY RUN] 将删除索引: {rec.index_name} FROM {rec.table_name}")
                else:
                    success = self.drop_index(rec.table_name, rec.index_name)
                    if success:
                        results["executed"].append(f"删除索引成功: {rec.index_name}")
                    else:
                        results["failed"].append(f"删除索引失败: {rec.index_name}")
        
        return results


class QueryPerformanceTester:
    """
    查询性能测试器
    
    测试索引优化前后的查询性能
    """
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def test_query_performance(self, query: str, params: Dict[str, Any] = None,
                               iterations: int = 10) -> Dict[str, float]:
        """
        测试查询性能
        
        Args:
            query: SQL查询
            params: 查询参数
            iterations: 测试次数
            
        Returns:
            性能统计
        """
        times = []
        
        for _ in range(iterations):
            start = time.time()
            self.engine.execute(text(query), params or {})
            elapsed = time.time() - start
            times.append(elapsed)
        
        return {
            "min_time": min(times),
            "max_time": max(times),
            "avg_time": sum(times) / len(times),
            "median_time": sorted(times)[len(times) // 2]
        }
    
    def compare_performance(self, query: str, params: Dict[str, Any] = None,
                           index_name: str = None, iterations: int = 10) -> Dict[str, Any]:
        """
        对比有无索引的查询性能
        
        Args:
            query: SQL查询
            params: 查询参数
            index_name: 要临时禁用的索引名
            iterations: 测试次数
            
        Returns:
            性能对比结果
        """
        # 测试有索引的性能
        with_index = self.test_query_performance(query, params, iterations)
        
        # 临时禁用索引（PostgreSQL）
        if index_name and self.engine.dialect.name == 'postgresql':
            self.engine.execute(text(f"UPDATE pg_index SET indisvalid = false WHERE indexrelname = '{index_name}'"))
        
        # 测试无索引的性能
        without_index = self.test_query_performance(query, params, iterations)
        
        # 恢复索引
        if index_name and self.engine.dialect.name == 'postgresql':
            self.engine.execute(text(f"UPDATE pg_index SET indisvalid = true WHERE indexrelname = '{index_name}'"))
        
        # 计算提升
        improvement = ((without_index["avg_time"] - with_index["avg_time"]) / without_index["avg_time"]) * 100
        
        return {
            "with_index": with_index,
            "without_index": without_index,
            "improvement_percent": improvement,
            "speedup_ratio": without_index["avg_time"] / with_index["avg_time"] if with_index["avg_time"] > 0 else 0
        }


# 便捷函数

def analyze_indexes(engine: Engine) -> Dict[str, Any]:
    """
    分析所有索引并生成报告
    
    Args:
        engine: 数据库引擎
        
    Returns:
        分析报告
    """
    analyzer = IndexAnalyzer(engine)
    return analyzer.generate_optimization_report()


def optimize_indexes(engine: Engine, dry_run: bool = True) -> Dict[str, List[str]]:
    """
    自动优化索引
    
    Args:
        engine: 数据库引擎
        dry_run: 是否仅预览
        
    Returns:
        优化结果
    """
    analyzer = IndexAnalyzer(engine)
    optimizer = IndexOptimizer(engine)
    
    # 查找未使用的索引
    unused = analyzer.find_unused_indexes()
    
    # 查找重复索引
    duplicates = analyzer.find_duplicate_indexes()
    
    # 合并建议
    recommendations = unused + duplicates
    
    # 应用建议
    return optimizer.apply_recommendations(recommendations, dry_run)


def get_index_usage_stats(engine: Engine) -> List[Dict[str, Any]]:
    """
    获取索引使用统计
    
    Args:
        engine: 数据库引擎
        
    Returns:
        索引使用统计列表
    """
    stats = []
    
    try:
        if engine.dialect.name == 'postgresql':
            query = text("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    idx_scan as scan_count,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
            """)
            
            result = engine.execute(query)
            for row in result:
                stats.append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "scan_count": row[3],
                    "tuples_read": row[4],
                    "tuples_fetched": row[5],
                    "size": row[6]
                })
    
    except Exception as e:
        logger.error(f"获取索引使用统计失败: {e}")
    
    return stats
