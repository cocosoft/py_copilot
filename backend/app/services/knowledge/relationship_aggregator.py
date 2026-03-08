#!/usr/bin/env python3
"""
关系聚合器模块

提供高级关系聚合功能，包括：
1. 关系聚合算法
2. 关系冲突检测
3. 关系置信度计算
4. 关系时间戳处理
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """冲突类型"""
    NO_CONFLICT = "no_conflict"
    TYPE_MISMATCH = "type_mismatch"  # 关系类型不匹配
    DIRECTION_CONFLICT = "direction_conflict"  # 方向冲突
    TEMPORAL_CONFLICT = "temporal_conflict"  # 时间冲突
    SEVERITY_HIGH = "severity_high"  # 高严重性冲突


class AggregationStrategy(Enum):
    """聚合策略"""
    UNION = "union"  # 并集
    INTERSECTION = "intersection"  # 交集
    WEIGHTED = "weighted"  # 加权平均
    MAJORITY = "majority"  # 多数投票
    CONFIDENCE_BASED = "confidence_based"  # 基于置信度


@dataclass
class RelationshipEvidence:
    """关系证据"""
    source_id: str
    source_type: str  # 'document', 'kb', 'global'
    relationship_type: str
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedRelationship:
    """聚合后的关系"""
    source_id: str
    target_id: str
    relationship_type: str
    confidence: float
    aggregated_count: int
    evidence_list: List[RelationshipEvidence]
    first_seen: datetime
    last_updated: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ConflictInfo:
    """冲突信息"""
    conflict_type: ConflictType
    severity: float  # 0-1
    description: str
    involved_relationships: List[str]
    suggested_resolution: str


class RelationshipAggregator:
    """
    关系聚合器

    提供高级关系聚合功能，支持多种聚合策略和冲突检测。
    """

    def __init__(self, strategy: AggregationStrategy = AggregationStrategy.CONFIDENCE_BASED):
        self.strategy = strategy
        self.confidence_threshold = 0.5
        self.conflict_threshold = 0.3

    def aggregate_relationships(
        self,
        relationships: List[Dict[str, Any]],
        source_entity_id: str,
        target_entity_id: str
    ) -> Optional[AggregatedRelationship]:
        """
        聚合关系列表

        Args:
            relationships: 关系列表
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID

        Returns:
            聚合后的关系
        """
        if not relationships:
            return None

        # 1. 检测冲突
        conflicts = self._detect_conflicts(relationships)

        # 2. 根据策略聚合
        if self.strategy == AggregationStrategy.UNION:
            return self._aggregate_by_union(relationships, source_entity_id, target_entity_id, conflicts)
        elif self.strategy == AggregationStrategy.INTERSECTION:
            return self._aggregate_by_intersection(relationships, source_entity_id, target_entity_id, conflicts)
        elif self.strategy == AggregationStrategy.WEIGHTED:
            return self._aggregate_by_weighted(relationships, source_entity_id, target_entity_id, conflicts)
        elif self.strategy == AggregationStrategy.MAJORITY:
            return self._aggregate_by_majority(relationships, source_entity_id, target_entity_id, conflicts)
        elif self.strategy == AggregationStrategy.CONFIDENCE_BASED:
            return self._aggregate_by_confidence(relationships, source_entity_id, target_entity_id, conflicts)
        else:
            return self._aggregate_by_union(relationships, source_entity_id, target_entity_id, conflicts)

    def _detect_conflicts(self, relationships: List[Dict[str, Any]]) -> List[ConflictInfo]:
        """
        检测关系冲突

        检测以下类型的冲突：
        1. 关系类型不匹配
        2. 方向冲突
        3. 时间冲突
        """
        conflicts = []

        # 按关系类型分组
        type_groups = defaultdict(list)
        for rel in relationships:
            rel_type = rel.get('relationship_type', 'UNKNOWN')
            type_groups[rel_type].append(rel)

        # 检测类型冲突
        if len(type_groups) > 1:
            # 不同类型之间的关系可能存在冲突
            main_type = max(type_groups.keys(), key=lambda x: len(type_groups[x]))
            for rel_type, rels in type_groups.items():
                if rel_type != main_type and len(rels) > 0:
                    conflict = ConflictInfo(
                        conflict_type=ConflictType.TYPE_MISMATCH,
                        severity=0.6,
                        description=f"关系类型冲突: {main_type} vs {rel_type}",
                        involved_relationships=[str(r.get('id', 'unknown')) for r in rels],
                        suggested_resolution=f"选择多数类型: {main_type}"
                    )
                    conflicts.append(conflict)

        # 检测方向冲突
        directions = defaultdict(int)
        for rel in relationships:
            direction = rel.get('direction', 'forward')
            directions[direction] += 1

        if len(directions) > 1:
            main_direction = max(directions.keys(), key=lambda x: directions[x])
            for direction, count in directions.items():
                if direction != main_direction and count > 0:
                    conflict = ConflictInfo(
                        conflict_type=ConflictType.DIRECTION_CONFLICT,
                        severity=0.7,
                        description=f"方向冲突: {main_direction} vs {direction}",
                        involved_relationships=[],
                        suggested_resolution=f"选择多数方向: {main_direction}"
                    )
                    conflicts.append(conflict)

        # 检测时间冲突
        timestamps = []
        for rel in relationships:
            ts = rel.get('timestamp') or rel.get('created_at')
            if ts:
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except:
                        continue
                timestamps.append(ts)

        if len(timestamps) > 1:
            timestamps.sort()
            time_span = timestamps[-1] - timestamps[0]
            if time_span > timedelta(days=365):
                conflict = ConflictInfo(
                    conflict_type=ConflictType.TEMPORAL_CONFLICT,
                    severity=0.5,
                    description=f"时间跨度冲突: {time_span.days} 天",
                    involved_relationships=[],
                    suggested_resolution="考虑关系的时效性"
                )
                conflicts.append(conflict)

        return conflicts

    def _aggregate_by_union(
        self,
        relationships: List[Dict[str, Any]],
        source_id: str,
        target_id: str,
        conflicts: List[ConflictInfo]
    ) -> AggregatedRelationship:
        """并集聚合策略"""
        # 收集所有关系类型
        all_types = set()
        for rel in relationships:
            all_types.add(rel.get('relationship_type', 'UNKNOWN'))

        # 选择最常见的关系类型
        if len(all_types) == 1:
            main_type = list(all_types)[0]
        else:
            type_counts = defaultdict(int)
            for rel in relationships:
                type_counts[rel.get('relationship_type', 'UNKNOWN')] += 1
            main_type = max(type_counts.keys(), key=lambda x: type_counts[x])

        # 计算平均置信度
        confidences = [r.get('confidence', 0.5) for r in relationships]
        avg_confidence = np.mean(confidences) if confidences else 0.5

        # 收集证据
        evidence_list = []
        for rel in relationships:
            evidence = RelationshipEvidence(
                source_id=str(rel.get('id', 'unknown')),
                source_type=rel.get('source_type', 'document'),
                relationship_type=rel.get('relationship_type', 'UNKNOWN'),
                confidence=rel.get('confidence', 0.5),
                timestamp=self._parse_timestamp(rel.get('timestamp') or rel.get('created_at')),
                metadata=rel.get('metadata', {})
            )
            evidence_list.append(evidence)

        # 排序证据
        evidence_list.sort(key=lambda x: x.confidence, reverse=True)

        return AggregatedRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=main_type,
            confidence=avg_confidence,
            aggregated_count=len(relationships),
            evidence_list=evidence_list,
            first_seen=min(e.timestamp for e in evidence_list),
            last_updated=max(e.timestamp for e in evidence_list),
            conflicts=[self._conflict_to_dict(c) for c in conflicts]
        )

    def _aggregate_by_intersection(
        self,
        relationships: List[Dict[str, Any]],
        source_id: str,
        target_id: str,
        conflicts: List[ConflictInfo]
    ) -> AggregatedRelationship:
        """交集聚合策略"""
        # 只保留共同的关系类型
        type_counts = defaultdict(int)
        for rel in relationships:
            type_counts[rel.get('relationship_type', 'UNKNOWN')] += 1

        # 选择所有关系中共同的关系类型
        common_types = [t for t, count in type_counts.items() if count == len(relationships)]

        if common_types:
            main_type = common_types[0]
        else:
            # 如果没有共同类型，使用多数投票
            main_type = max(type_counts.keys(), key=lambda x: type_counts[x])

        # 只保留该类型的关系
        filtered_rels = [r for r in relationships if r.get('relationship_type') == main_type]

        return self._aggregate_by_union(filtered_rels, source_id, target_id, conflicts)

    def _aggregate_by_weighted(
        self,
        relationships: List[Dict[str, Any]],
        source_id: str,
        target_id: str,
        conflicts: List[ConflictInfo]
    ) -> AggregatedRelationship:
        """加权聚合策略"""
        # 按来源类型加权
        weights = {
            'global': 1.0,
            'kb': 0.8,
            'document': 0.6
        }

        # 计算加权置信度
        weighted_confidences = []
        for rel in relationships:
            source_type = rel.get('source_type', 'document')
            weight = weights.get(source_type, 0.5)
            confidence = rel.get('confidence', 0.5)
            weighted_confidences.append(weight * confidence)

        avg_confidence = np.mean(weighted_confidences) if weighted_confidences else 0.5

        # 创建结果
        result = self._aggregate_by_union(relationships, source_id, target_id, conflicts)
        result.confidence = avg_confidence

        return result

    def _aggregate_by_majority(
        self,
        relationships: List[Dict[str, Any]],
        source_id: str,
        target_id: str,
        conflicts: List[ConflictInfo]
    ) -> AggregatedRelationship:
        """多数投票聚合策略"""
        # 统计关系类型
        type_counts = defaultdict(list)
        for rel in relationships:
            rel_type = rel.get('relationship_type', 'UNKNOWN')
            type_counts[rel_type].append(rel)

        # 选择得票最多的类型
        main_type = max(type_counts.keys(), key=lambda x: len(type_counts[x]))
        majority_rels = type_counts[main_type]

        # 计算多数投票的置信度
        majority_ratio = len(majority_rels) / len(relationships)

        result = self._aggregate_by_union(majority_rels, source_id, target_id, conflicts)
        result.confidence *= majority_ratio  # 根据多数比例调整置信度

        return result

    def _aggregate_by_confidence(
        self,
        relationships: List[Dict[str, Any]],
        source_id: str,
        target_id: str,
        conflicts: List[ConflictInfo]
    ) -> AggregatedRelationship:
        """基于置信度的聚合策略"""
        # 按置信度排序
        sorted_rels = sorted(relationships, key=lambda x: x.get('confidence', 0), reverse=True)

        # 选择置信度最高的关系类型
        top_rel = sorted_rels[0]
        main_type = top_rel.get('relationship_type', 'UNKNOWN')

        # 过滤相同类型的高置信度关系
        high_confidence_rels = [
            r for r in sorted_rels
            if r.get('relationship_type') == main_type and r.get('confidence', 0) >= self.confidence_threshold
        ]

        if not high_confidence_rels:
            high_confidence_rels = sorted_rels[:max(1, len(sorted_rels) // 2)]

        # 计算加权平均置信度
        confidences = [r.get('confidence', 0.5) for r in high_confidence_rels]
        weights = np.array(confidences) / sum(confidences) if sum(confidences) > 0 else np.ones(len(confidences)) / len(confidences)
        weighted_confidence = np.average(confidences, weights=weights)

        result = self._aggregate_by_union(high_confidence_rels, source_id, target_id, conflicts)
        result.confidence = weighted_confidence

        return result

    def calculate_confidence(
        self,
        relationships: List[Dict[str, Any]],
        evidence_sources: List[str] = None
    ) -> float:
        """
        计算关系置信度

        基于以下因素：
        1. 证据数量
        2. 证据来源多样性
        3. 证据一致性
        4. 证据时效性
        """
        if not relationships:
            return 0.0

        # 1. 基础置信度（证据数量）
        count_score = min(1.0, len(relationships) / 5.0)  # 最多5个证据得满分

        # 2. 来源多样性
        if evidence_sources is None:
            evidence_sources = [r.get('source_type', 'document') for r in relationships]

        unique_sources = len(set(evidence_sources))
        diversity_score = min(1.0, unique_sources / 3.0)  # 最多3种来源得满分

        # 3. 一致性（关系类型的一致性）
        types = [r.get('relationship_type', 'UNKNOWN') for r in relationships]
        if types:
            type_counts = defaultdict(int)
            for t in types:
                type_counts[t] += 1
            max_count = max(type_counts.values())
            consistency_score = max_count / len(types)
        else:
            consistency_score = 0.0

        # 4. 时效性
        timestamps = []
        for rel in relationships:
            ts = rel.get('timestamp') or rel.get('created_at')
            if ts:
                timestamps.append(self._parse_timestamp(ts))

        if timestamps:
            now = datetime.now()
            recency_scores = []
            for ts in timestamps:
                days_old = (now - ts).days
                # 越新越好，30天内满分，超过365天0分
                recency = max(0, 1 - days_old / 365)
                recency_scores.append(recency)
            recency_score = np.mean(recency_scores)
        else:
            recency_score = 0.5  # 默认中等时效性

        # 综合计算
        confidence = (
            0.25 * count_score +
            0.25 * diversity_score +
            0.30 * consistency_score +
            0.20 * recency_score
        )

        return min(1.0, max(0.0, confidence))

    def resolve_conflicts(self, conflicts: List[ConflictInfo]) -> Dict[str, Any]:
        """
        解析冲突并提供解决方案
        """
        resolutions = []

        for conflict in conflicts:
            resolution = {
                'conflict_type': conflict.conflict_type.value,
                'severity': conflict.severity,
                'description': conflict.description,
                'suggested_action': conflict.suggested_resolution,
                'auto_resolvable': conflict.severity < 0.7
            }
            resolutions.append(resolution)

        return {
            'total_conflicts': len(conflicts),
            'high_severity': len([c for c in conflicts if c.severity >= 0.7]),
            'medium_severity': len([c for c in conflicts if 0.4 <= c.severity < 0.7]),
            'low_severity': len([c for c in conflicts if c.severity < 0.4]),
            'resolutions': resolutions
        }

    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """解析时间戳"""
        if timestamp is None:
            return datetime.now()

        if isinstance(timestamp, datetime):
            return timestamp

        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return datetime.now()

        return datetime.now()

    def _conflict_to_dict(self, conflict: ConflictInfo) -> Dict[str, Any]:
        """将冲突信息转换为字典"""
        return {
            'type': conflict.conflict_type.value,
            'severity': conflict.severity,
            'description': conflict.description,
            'involved_relationships': conflict.involved_relationships,
            'suggested_resolution': conflict.suggested_resolution
        }


class TemporalRelationshipAggregator(RelationshipAggregator):
    """
    时序关系聚合器

    支持时序关系处理和版本管理
    """

    def __init__(self, strategy: AggregationStrategy = AggregationStrategy.CONFIDENCE_BASED):
        super().__init__(strategy)
        self.temporal_window = timedelta(days=30)  # 默认30天时间窗口

    def aggregate_with_temporal_consideration(
        self,
        relationships: List[Dict[str, Any]],
        source_id: str,
        target_id: str,
        reference_time: datetime = None
    ) -> AggregatedRelationship:
        """
        考虑时间因素的关系聚合

        Args:
            relationships: 关系列表
            source_id: 源实体ID
            target_id: 目标实体ID
            reference_time: 参考时间点（默认为当前时间）
        """
        if reference_time is None:
            reference_time = datetime.now()

        # 按时间窗口分组
        recent_rels = []
        old_rels = []

        for rel in relationships:
            ts = self._parse_timestamp(rel.get('timestamp') or rel.get('created_at'))
            if reference_time - ts <= self.temporal_window:
                recent_rels.append(rel)
            else:
                old_rels.append(rel)

        # 优先使用近期关系
        if recent_rels:
            # 给近期关系更高的权重
            for rel in recent_rels:
                rel['temporal_weight'] = 1.0
            for rel in old_rels:
                rel['temporal_weight'] = 0.5

            all_rels = recent_rels + old_rels
        else:
            all_rels = old_rels

        return self.aggregate_relationships(all_rels, source_id, target_id)

    def detect_temporal_changes(
        self,
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        检测关系的时序变化
        """
        if len(relationships) < 2:
            return []

        # 按时间排序
        sorted_rels = sorted(
            relationships,
            key=lambda x: self._parse_timestamp(x.get('timestamp') or x.get('created_at'))
        )

        changes = []
        for i in range(1, len(sorted_rels)):
            prev_rel = sorted_rels[i - 1]
            curr_rel = sorted_rels[i]

            # 检测关系类型变化
            if prev_rel.get('relationship_type') != curr_rel.get('relationship_type'):
                changes.append({
                    'change_type': 'relationship_type_change',
                    'from': prev_rel.get('relationship_type'),
                    'to': curr_rel.get('relationship_type'),
                    'timestamp': curr_rel.get('timestamp'),
                    'description': f"关系类型从 '{prev_rel.get('relationship_type')}' "
                                   f"变为 '{curr_rel.get('relationship_type')}'"
                })

            # 检测置信度显著变化
            prev_conf = prev_rel.get('confidence', 0.5)
            curr_conf = curr_rel.get('confidence', 0.5)
            if abs(curr_conf - prev_conf) > 0.3:
                changes.append({
                    'change_type': 'confidence_change',
                    'from': prev_conf,
                    'to': curr_conf,
                    'timestamp': curr_rel.get('timestamp'),
                    'description': f"置信度从 {prev_conf:.2f} 变为 {curr_conf:.2f}"
                })

        return changes


def temporal_aggregate_relationships(
    relationships: List[Dict[str, Any]],
    source_id: str,
    target_id: str,
    reference_time: datetime = None
) -> AggregatedRelationship:
    """
    时序关系聚合的便捷函数

    Args:
        relationships: 关系列表
        source_id: 源实体ID
        target_id: 目标实体ID
        reference_time: 参考时间点

    Returns:
        聚合后的关系
    """
    aggregator = TemporalRelationshipAggregator()
    return aggregator.aggregate_with_temporal_consideration(
        relationships, source_id, target_id, reference_time
    )
