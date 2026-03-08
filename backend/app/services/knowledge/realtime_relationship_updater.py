#!/usr/bin/env python3
"""
实时关系更新服务

支持知识图谱关系的实时更新，包括：
- 实时关系检测
- 增量关系更新
- 关系变更通知
- 冲突检测与解决
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class RelationshipChangeType(Enum):
    """关系变更类型"""
    ADDED = "added"           # 新增关系
    UPDATED = "updated"       # 更新关系
    DELETED = "deleted"       # 删除关系
    STRENGTHENED = "strengthened"  # 关系增强
    WEAKENED = "weakened"     # 关系减弱


@dataclass
class RelationshipChange:
    """关系变更事件"""
    change_id: str
    change_type: RelationshipChangeType
    relationship: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"    # 变更来源
    confidence: float = 1.0   # 变更置信度


@dataclass
class RelationshipUpdate:
    """关系更新操作"""
    update_id: str
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any]
    operation: str = "upsert"  # upsert, delete, merge
    timestamp: datetime = field(default_factory=datetime.now)


class RealtimeRelationshipUpdater:
    """
    实时关系更新服务
    
    提供知识图谱关系的实时更新能力
    """
    
    def __init__(self, 
                 batch_size: int = 100,
                 flush_interval: float = 5.0,
                 enable_notifications: bool = True):
        """
        初始化实时关系更新服务
        
        Args:
            batch_size: 批处理大小
            flush_interval: 刷新间隔（秒）
            enable_notifications: 是否启用通知
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enable_notifications = enable_notifications
        
        # 更新缓冲区
        self.update_buffer: List[RelationshipUpdate] = []
        self.buffer_lock = threading.Lock()
        
        # 变更历史
        self.change_history: List[RelationshipChange] = []
        self.max_history_size = 10000
        
        # 通知回调
        self.notification_callbacks: List[Callable[[RelationshipChange], None]] = []
        
        # 运行状态
        self._running = False
        self._flush_task = None
        
        # 关系索引（用于快速查找）
        self.relationship_index: Dict[str, Dict[str, Any]] = {}
        
        logger.info("实时关系更新服务初始化完成")
    
    def start(self):
        """启动服务"""
        if self._running:
            return
        
        self._running = True
        
        # 启动后台刷新任务
        if self.flush_interval > 0:
            asyncio.create_task(self._background_flush())
        
        logger.info("实时关系更新服务已启动")
    
    def stop(self):
        """停止服务"""
        self._running = False
        
        # 刷新剩余数据
        asyncio.create_task(self._flush_buffer())
        
        logger.info("实时关系更新服务已停止")
    
    async def _background_flush(self):
        """后台刷新任务"""
        while self._running:
            await asyncio.sleep(self.flush_interval)
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        """刷新缓冲区"""
        with self.buffer_lock:
            if not self.update_buffer:
                return
            
            updates = self.update_buffer.copy()
            self.update_buffer = []
        
        # 处理批量更新
        await self._process_batch_updates(updates)
    
    async def _process_batch_updates(self, updates: List[RelationshipUpdate]):
        """
        处理批量更新
        
        Args:
            updates: 更新操作列表
        """
        logger.info(f"处理批量更新: {len(updates)} 个操作")
        
        # 按关系类型分组
        grouped = defaultdict(list)
        for update in updates:
            key = f"{update.source_id}_{update.target_id}_{update.relation_type}"
            grouped[key].append(update)
        
        # 处理每组更新
        for key, group in grouped.items():
            # 取最新的更新
            latest_update = max(group, key=lambda u: u.timestamp)
            await self._apply_update(latest_update)
    
    async def _apply_update(self, update: RelationshipUpdate):
        """
        应用单个更新
        
        Args:
            update: 更新操作
        """
        # 生成关系ID
        rel_id = f"{update.source_id}_{update.target_id}_{update.relation_type}"
        
        # 检查现有关系
        existing = self.relationship_index.get(rel_id)
        
        if update.operation == "delete":
            if existing:
                # 删除关系
                del self.relationship_index[rel_id]
                
                # 记录变更
                change = RelationshipChange(
                    change_id=f"chg_{datetime.now().timestamp()}",
                    change_type=RelationshipChangeType.DELETED,
                    relationship=existing,
                    previous_state=existing,
                    source="realtime_updater",
                    confidence=update.properties.get('confidence', 1.0)
                )
                self._record_change(change)
        
        elif update.operation == "upsert":
            if existing:
                # 更新现有关系
                previous = existing.copy()
                existing.update(update.properties)
                existing['updated_at'] = update.timestamp.isoformat()
                
                # 检测变更类型
                change_type = self._detect_change_type(previous, existing)
                
                change = RelationshipChange(
                    change_id=f"chg_{datetime.now().timestamp()}",
                    change_type=change_type,
                    relationship=existing,
                    previous_state=previous,
                    source="realtime_updater",
                    confidence=update.properties.get('confidence', 1.0)
                )
                self._record_change(change)
            
            else:
                # 新增关系
                new_relationship = {
                    'id': rel_id,
                    'source_id': update.source_id,
                    'target_id': update.target_id,
                    'relation_type': update.relation_type,
                    'created_at': update.timestamp.isoformat(),
                    'updated_at': update.timestamp.isoformat(),
                    **update.properties
                }
                
                self.relationship_index[rel_id] = new_relationship
                
                # 记录变更
                change = RelationshipChange(
                    change_id=f"chg_{datetime.now().timestamp()}",
                    change_type=RelationshipChangeType.ADDED,
                    relationship=new_relationship,
                    source="realtime_updater",
                    confidence=update.properties.get('confidence', 1.0)
                )
                self._record_change(change)
    
    def _detect_change_type(self, 
                           previous: Dict[str, Any], 
                           current: Dict[str, Any]) -> RelationshipChangeType:
        """
        检测变更类型
        
        Args:
            previous: 之前的状态
            current: 当前状态
        
        Returns:
            变更类型
        """
        prev_conf = previous.get('confidence', 0.5)
        curr_conf = current.get('confidence', 0.5)
        
        if curr_conf > prev_conf * 1.2:
            return RelationshipChangeType.STRENGTHENED
        elif curr_conf < prev_conf * 0.8:
            return RelationshipChangeType.WEAKENED
        else:
            return RelationshipChangeType.UPDATED
    
    def _record_change(self, change: RelationshipChange):
        """
        记录变更
        
        Args:
            change: 变更事件
        """
        self.change_history.append(change)
        
        # 限制历史大小
        if len(self.change_history) > self.max_history_size:
            self.change_history = self.change_history[-self.max_history_size:]
        
        # 发送通知
        if self.enable_notifications:
            self._notify_change(change)
    
    def _notify_change(self, change: RelationshipChange):
        """
        通知变更
        
        Args:
            change: 变更事件
        """
        for callback in self.notification_callbacks:
            try:
                callback(change)
            except Exception as e:
                logger.error(f"通知回调执行失败: {e}")
    
    def add_relationship(self,
                        source_id: str,
                        target_id: str,
                        relation_type: str,
                        properties: Dict[str, Any] = None,
                        immediate: bool = False) -> str:
        """
        添加关系
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 关系属性
            immediate: 是否立即处理
        
        Returns:
            更新ID
        """
        import uuid
        
        update = RelationshipUpdate(
            update_id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties or {},
            operation="upsert"
        )
        
        if immediate:
            asyncio.create_task(self._apply_update(update))
        else:
            with self.buffer_lock:
                self.update_buffer.append(update)
                
                # 如果达到批处理大小，触发刷新
                if len(self.update_buffer) >= self.batch_size:
                    asyncio.create_task(self._flush_buffer())
        
        return update.update_id
    
    def update_relationship(self,
                           source_id: str,
                           target_id: str,
                           relation_type: str,
                           properties: Dict[str, Any],
                           immediate: bool = False) -> str:
        """
        更新关系
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 更新的属性
            immediate: 是否立即处理
        
        Returns:
            更新ID
        """
        return self.add_relationship(source_id, target_id, relation_type, properties, immediate)
    
    def delete_relationship(self,
                           source_id: str,
                           target_id: str,
                           relation_type: str,
                           immediate: bool = False) -> str:
        """
        删除关系
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            immediate: 是否立即处理
        
        Returns:
            更新ID
        """
        import uuid
        
        update = RelationshipUpdate(
            update_id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties={},
            operation="delete"
        )
        
        if immediate:
            asyncio.create_task(self._apply_update(update))
        else:
            with self.buffer_lock:
                self.update_buffer.append(update)
        
        return update.update_id
    
    def get_relationship(self, 
                        source_id: str, 
                        target_id: str, 
                        relation_type: str) -> Optional[Dict[str, Any]]:
        """
        获取关系
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
        
        Returns:
            关系数据
        """
        rel_id = f"{source_id}_{target_id}_{relation_type}"
        return self.relationship_index.get(rel_id)
    
    def get_relationships_by_entity(self, 
                                   entity_id: str,
                                   direction: str = "both") -> List[Dict[str, Any]]:
        """
        获取实体的所有关系
        
        Args:
            entity_id: 实体ID
            direction: 方向 (outgoing, incoming, both)
        
        Returns:
            关系列表
        """
        relationships = []
        
        for rel in self.relationship_index.values():
            if direction in ["outgoing", "both"] and rel.get('source_id') == entity_id:
                relationships.append(rel)
            if direction in ["incoming", "both"] and rel.get('target_id') == entity_id:
                relationships.append(rel)
        
        return relationships
    
    def get_recent_changes(self, 
                          limit: int = 100,
                          change_type: Optional[RelationshipChangeType] = None) -> List[RelationshipChange]:
        """
        获取最近的变更
        
        Args:
            limit: 返回数量限制
            change_type: 变更类型过滤
        
        Returns:
            变更列表
        """
        changes = self.change_history
        
        if change_type:
            changes = [c for c in changes if c.change_type == change_type]
        
        # 按时间倒序
        changes = sorted(changes, key=lambda c: c.timestamp, reverse=True)
        
        return changes[:limit]
    
    def register_notification_callback(self, callback: Callable[[RelationshipChange], None]):
        """
        注册变更通知回调
        
        Args:
            callback: 回调函数
        """
        self.notification_callbacks.append(callback)
        logger.info(f"注册通知回调，当前回调数: {len(self.notification_callbacks)}")
    
    def unregister_notification_callback(self, callback: Callable[[RelationshipChange], None]):
        """
        注销变更通知回调
        
        Args:
            callback: 回调函数
        """
        if callback in self.notification_callbacks:
            self.notification_callbacks.remove(callback)
            logger.info(f"注销通知回调，当前回调数: {len(self.notification_callbacks)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.buffer_lock:
            buffer_size = len(self.update_buffer)
        
        return {
            'buffer_size': buffer_size,
            'buffer_capacity': self.batch_size,
            'indexed_relationships': len(self.relationship_index),
            'change_history_size': len(self.change_history),
            'notification_callbacks': len(self.notification_callbacks),
            'is_running': self._running
        }


# 便捷函数
def create_realtime_updater(**kwargs) -> RealtimeRelationshipUpdater:
    """创建实时关系更新服务"""
    return RealtimeRelationshipUpdater(**kwargs)


if __name__ == '__main__':
    # 测试实时关系更新
    async def test():
        updater = RealtimeRelationshipUpdater(batch_size=5, flush_interval=2.0)
        
        # 注册通知回调
        def on_change(change: RelationshipChange):
            print(f"[{change.change_type.value}] {change.relationship.get('relation_type')} "
                  f"({change.timestamp.strftime('%H:%M:%S')})")
        
        updater.register_notification_callback(on_change)
        updater.start()
        
        # 添加关系
        print("添加关系...")
        for i in range(10):
            updater.add_relationship(
                source_id=f"entity_{i}",
                target_id=f"entity_{i+1}",
                relation_type="RELATED_TO",
                properties={'confidence': 0.8 + i * 0.02, 'weight': i}
            )
        
        # 等待刷新
        await asyncio.sleep(3)
        
        # 更新关系
        print("\n更新关系...")
        updater.update_relationship(
            source_id="entity_0",
            target_id="entity_1",
            relation_type="RELATED_TO",
            properties={'confidence': 0.95, 'updated': True}
        )
        
        await asyncio.sleep(1)
        
        # 获取统计
        print("\n统计信息:")
        stats = updater.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 获取变更历史
        print("\n最近变更:")
        changes = updater.get_recent_changes(limit=5)
        for change in changes:
            print(f"  {change.change_type.value}: {change.relationship.get('source_id')} -> "
                  f"{change.relationship.get('target_id')}")
        
        updater.stop()
    
    asyncio.run(test())
