"""
预警历史记录模块

实现预警数据的持久化存储、历史查询和统计分析功能。
"""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .alert_system import AlertRecord, AlertSeverity, AlertType, MetricType

logger = logging.getLogger(__name__)


class AlertHistoryManager:
    """预警历史记录管理器"""
    
    def __init__(self, database_path: str = "backend/py_copilot.db"):
        """初始化预警历史记录管理器
        
        Args:
            database_path: 数据库文件路径
        """
        self.database_path = database_path
        self._init_database()
        
    def _init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 创建预警记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_history (
                    alert_id TEXT PRIMARY KEY,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    resolved BOOLEAN NOT NULL DEFAULT FALSE,
                    resolved_time DATETIME,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alert_timestamp 
                ON alert_history(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alert_severity 
                ON alert_history(severity)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alert_type 
                ON alert_history(alert_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alert_resolved 
                ON alert_history(resolved)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("预警历史记录数据库初始化完成")
            
        except Exception as e:
            logger.error(f"初始化预警历史记录数据库失败: {e}")
            
    def save_alert(self, alert: AlertRecord) -> bool:
        """保存预警记录到数据库
        
        Args:
            alert: 预警记录
            
        Returns:
            保存是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 序列化元数据
            metadata_json = json.dumps(alert.metadata) if alert.metadata else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO alert_history 
                (alert_id, alert_type, severity, metric_type, metric_value, 
                 threshold_value, message, timestamp, resolved, resolved_time, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id,
                alert.alert_type.value,
                alert.severity.value,
                alert.metric_type.value,
                alert.metric_value,
                alert.threshold_value,
                alert.message,
                alert.timestamp.isoformat(),
                alert.resolved,
                alert.resolved_time.isoformat() if alert.resolved_time else None,
                metadata_json
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"预警记录已保存: {alert.alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存预警记录失败: {e}")
            return False
            
    def get_alert(self, alert_id: str) -> Optional[AlertRecord]:
        """根据ID获取预警记录
        
        Args:
            alert_id: 预警ID
            
        Returns:
            预警记录，如果未找到返回None
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM alert_history WHERE alert_id = ?
            ''', (alert_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_alert_record(row)
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取预警记录失败: {e}")
            return None
            
    def get_alerts(self, limit: int = 100, offset: int = 0,
                  severity: Optional[AlertSeverity] = None,
                  alert_type: Optional[AlertType] = None,
                  resolved: Optional[bool] = None,
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None) -> List[AlertRecord]:
        """获取预警记录列表
        
        Args:
            limit: 限制数量
            offset: 偏移量
            severity: 严重程度过滤
            alert_type: 预警类型过滤
            resolved: 是否解决过滤
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            预警记录列表
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if severity:
                conditions.append("severity = ?")
                params.append(severity.value)
                
            if alert_type:
                conditions.append("alert_type = ?")
                params.append(alert_type.value)
                
            if resolved is not None:
                conditions.append("resolved = ?")
                params.append(1 if resolved else 0)
                
            if start_time:
                conditions.append("timestamp >= ?")
                params.append(start_time.isoformat())
                
            if end_time:
                conditions.append("timestamp <= ?")
                params.append(end_time.isoformat())
                
            # 构建查询语句
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f'''
                SELECT * FROM alert_history 
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            '''
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            conn.close()
            
            alerts = [self._row_to_alert_record(row) for row in rows]
            return alerts
            
        except Exception as e:
            logger.error(f"获取预警记录列表失败: {e}")
            return []
            
    def update_alert_resolved(self, alert_id: str, resolved: bool = True) -> bool:
        """更新预警解决状态
        
        Args:
            alert_id: 预警ID
            resolved: 是否解决
            
        Returns:
            更新是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            resolved_time = datetime.now() if resolved else None
            
            cursor.execute('''
                UPDATE alert_history 
                SET resolved = ?, resolved_time = ?
                WHERE alert_id = ?
            ''', (
                1 if resolved else 0,
                resolved_time.isoformat() if resolved_time else None,
                alert_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"预警解决状态已更新: {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新预警解决状态失败: {e}")
            return False
            
    def get_alert_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取预警统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            预警统计信息
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 总预警数量
            cursor.execute('''
                SELECT COUNT(*) FROM alert_history 
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            total_alerts = cursor.fetchone()[0]
            
            # 活跃预警数量
            cursor.execute('''
                SELECT COUNT(*) FROM alert_history 
                WHERE timestamp BETWEEN ? AND ? AND resolved = 0
            ''', (start_time.isoformat(), end_time.isoformat()))
            active_alerts = cursor.fetchone()[0]
            
            # 按严重程度统计
            cursor.execute('''
                SELECT severity, COUNT(*) FROM alert_history 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY severity
            ''', (start_time.isoformat(), end_time.isoformat()))
            severity_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按预警类型统计
            cursor.execute('''
                SELECT alert_type, COUNT(*) FROM alert_history 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY alert_type
            ''', (start_time.isoformat(), end_time.isoformat()))
            type_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按日期统计
            cursor.execute('''
                SELECT DATE(timestamp), COUNT(*) FROM alert_history 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            ''', (start_time.isoformat(), end_time.isoformat()))
            daily_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 最频繁的预警
            cursor.execute('''
                SELECT message, COUNT(*) as count FROM alert_history 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY message
                ORDER BY count DESC
                LIMIT 10
            ''', (start_time.isoformat(), end_time.isoformat()))
            frequent_alerts = [{"message": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "resolved_alerts": total_alerts - active_alerts,
                "severity_stats": severity_stats,
                "type_stats": type_stats,
                "daily_stats": daily_stats,
                "frequent_alerts": frequent_alerts,
                "time_range_days": days,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取预警统计失败: {e}")
            return {}
            
    def get_alert_trend(self, metric_type: Optional[MetricType] = None,
                       days: int = 30) -> List[Dict[str, Any]]:
        """获取预警趋势数据
        
        Args:
            metric_type: 指标类型过滤
            days: 时间范围（天）
            
        Returns:
            预警趋势数据
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 构建查询条件
            conditions = ["timestamp BETWEEN ? AND ?"]
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if metric_type:
                conditions.append("metric_type = ?")
                params.append(metric_type.value)
                
            where_clause = " AND ".join(conditions)
            
            # 按天统计预警数量
            cursor.execute(f'''
                SELECT DATE(timestamp), COUNT(*) FROM alert_history 
                WHERE {where_clause}
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            ''', params)
            
            trend_data = []
            for row in cursor.fetchall():
                trend_data.append({
                    "date": row[0],
                    "count": row[1]
                })
            
            conn.close()
            return trend_data
            
        except Exception as e:
            logger.error(f"获取预警趋势数据失败: {e}")
            return []
            
    def cleanup_old_alerts(self, days: int = 90) -> int:
        """清理旧的预警记录
        
        Args:
            days: 保留天数
            
        Returns:
            删除的记录数量
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 获取要删除的记录数量
            cursor.execute('''
                SELECT COUNT(*) FROM alert_history 
                WHERE timestamp < ?
            ''', (cutoff_time.isoformat(),))
            
            count_before = cursor.fetchone()[0]
            
            # 删除旧记录
            cursor.execute('''
                DELETE FROM alert_history 
                WHERE timestamp < ?
            ''', (cutoff_time.isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.info(f"已清理 {count_before} 条旧预警记录")
            return count_before
            
        except Exception as e:
            logger.error(f"清理旧预警记录失败: {e}")
            return 0
            
    def _row_to_alert_record(self, row: Tuple) -> AlertRecord:
        """将数据库行转换为预警记录对象
        
        Args:
            row: 数据库行
            
        Returns:
            预警记录对象
        """
        alert_id, alert_type_str, severity_str, metric_type_str, metric_value, \
        threshold_value, message, timestamp_str, resolved_int, resolved_time_str, metadata_json = row[1:12]
        
        # 解析枚举值
        alert_type = AlertType(alert_type_str)
        severity = AlertSeverity(severity_str)
        metric_type = MetricType(metric_type_str)
        
        # 解析时间戳
        timestamp = datetime.fromisoformat(timestamp_str)
        resolved_time = datetime.fromisoformat(resolved_time_str) if resolved_time_str else None
        
        # 解析元数据
        metadata = json.loads(metadata_json) if metadata_json else None
        
        return AlertRecord(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            metric_type=metric_type,
            metric_value=metric_value,
            threshold_value=threshold_value,
            message=message,
            timestamp=timestamp,
            resolved=bool(resolved_int),
            resolved_time=resolved_time,
            metadata=metadata
        )


# 全局预警历史记录管理器实例
alert_history_manager = AlertHistoryManager()


class AlertHistoryAPI:
    """预警历史记录API集成类"""
    
    def __init__(self, alert_manager, history_manager):
        """初始化预警历史记录API
        
        Args:
            alert_manager: 预警管理器
            history_manager: 历史记录管理器
        """
        self.alert_manager = alert_manager
        self.history_manager = history_manager
        
    def save_alert_to_history(self, alert: AlertRecord):
        """保存预警到历史记录
        
        Args:
            alert: 预警记录
        """
        try:
            self.history_manager.save_alert(alert)
        except Exception as e:
            logger.error(f"保存预警到历史记录失败: {e}")
            
    def sync_alerts_to_history(self):
        """同步内存中的预警到历史记录"""
        try:
            alerts = self.alert_manager.get_active_alerts()
            
            for alert in alerts:
                self.save_alert_to_history(alert)
                
            logger.info(f"已同步 {len(alerts)} 个活跃预警到历史记录")
            
        except Exception as e:
            logger.error(f"同步预警到历史记录失败: {e}")
            
    def get_combined_alert_history(self, limit: int = 100) -> List[AlertRecord]:
        """获取合并的预警历史（内存 + 数据库）
        
        Args:
            limit: 限制数量
            
        Returns:
            合并的预警历史列表
        """
        try:
            # 获取内存中的活跃预警
            memory_alerts = self.alert_manager.get_active_alerts()
            
            # 获取数据库中的历史预警（不包括已解决的）
            db_alerts = self.history_manager.get_alerts(
                limit=limit - len(memory_alerts),
                resolved=False
            )
            
            # 合并并去重
            combined_alerts = memory_alerts + db_alerts
            
            # 按时间戳排序
            combined_alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 去重（基于alert_id）
            seen_ids = set()
            unique_alerts = []
            
            for alert in combined_alerts:
                if alert.alert_id not in seen_ids:
                    seen_ids.add(alert.alert_id)
                    unique_alerts.append(alert)
                    
            return unique_alerts[:limit]
            
        except Exception as e:
            logger.error(f"获取合并预警历史失败: {e}")
            return []


# 创建预警历史记录API集成实例
alert_history_api = AlertHistoryAPI(alert_manager, alert_history_manager)