"""
能力发现服务

本模块提供能力发现、搜索和匹配功能
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import re

from app.capabilities.base_capability import BaseCapability
from app.capabilities.types import (
    CapabilityMetadata,
    CapabilityType,
    CapabilityLevel,
    CapabilityMatch
)
from app.capabilities.center.unified_center import UnifiedCapabilityCenter

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    capability: BaseCapability
    score: float
    match_type: str
    matched_fields: List[str]


class DiscoveryService:
    """
    能力发现服务

    提供能力搜索、匹配和推荐功能。
    支持多种搜索策略：关键词、标签、语义、场景等。

    Attributes:
        _center: 统一能力中心
        _search_index: 搜索索引
        _match_weights: 匹配权重配置
    """

    # 默认匹配权重
    DEFAULT_WEIGHTS = {
        'name_exact': 1.0,
        'name_partial': 0.8,
        'description': 0.6,
        'tag': 0.7,
        'category': 0.5,
        'semantic': 0.4
    }

    def __init__(self, center: UnifiedCapabilityCenter):
        """
        初始化发现服务

        Args:
            center: 统一能力中心
        """
        self._center = center
        self._search_index: Dict[str, List[str]] = {}
        self._match_weights = self.DEFAULT_WEIGHTS.copy()

        logger.info("能力发现服务已创建")

    def build_index(self):
        """
        构建搜索索引

        为所有能力构建关键词索引
        """
        logger.info("开始构建能力搜索索引...")

        self._search_index.clear()

        capabilities = self._center.get_all_capabilities()

        for name, capability in capabilities.items():
            metadata = capability.metadata

            # 索引名称
            self._add_to_index(metadata.name.lower(), name)
            self._add_to_index(metadata.display_name.lower(), name)

            # 索引描述中的关键词
            if metadata.description:
                words = self._extract_keywords(metadata.description)
                for word in words:
                    self._add_to_index(word, name)

            # 索引标签
            for tag in metadata.tags:
                self._add_to_index(tag.lower(), name)

            # 索引分类
            if metadata.category:
                self._add_to_index(metadata.category.lower(), name)

        logger.info(f"搜索索引构建完成，共 {len(self._search_index)} 个关键词")

    def _add_to_index(self, keyword: str, capability_name: str):
        """
        添加到索引

        Args:
            keyword: 关键词
            capability_name: 能力名称
        """
        if keyword not in self._search_index:
            self._search_index[keyword] = []

        if capability_name not in self._search_index[keyword]:
            self._search_index[keyword].append(capability_name)

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词

        Args:
            text: 文本

        Returns:
            List[str]: 关键词列表
        """
        # 简单的关键词提取：分词并过滤
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fa5]+\b', text.lower())

        # 过滤停用词（简化版）
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', '的', '是', '和'}

        return [w for w in words if w not in stop_words and len(w) > 1]

    def search(self,
               query: str,
               capability_type: Optional[CapabilityType] = None,
               limit: int = 10) -> List[SearchResult]:
        """
        搜索能力

        Args:
            query: 搜索查询
            capability_type: 能力类型过滤
            limit: 返回数量限制

        Returns:
            List[SearchResult]: 搜索结果
        """
        if not query.strip():
            return []

        query_lower = query.lower()
        results: Dict[str, SearchResult] = {}

        # 获取所有能力（或按类型过滤）
        if capability_type:
            capabilities = self._center.get_capabilities_by_type(capability_type)
        else:
            capabilities = list(self._center.get_all_capabilities().values())

        for capability in capabilities:
            score, match_type, matched_fields = self._calculate_match_score(
                capability, query_lower
            )

            if score > 0:
                results[capability.name] = SearchResult(
                    capability=capability,
                    score=score,
                    match_type=match_type,
                    matched_fields=matched_fields
                )

        # 按分数排序
        sorted_results = sorted(
            results.values(),
            key=lambda r: r.score,
            reverse=True
        )

        return sorted_results[:limit]

    def _calculate_match_score(self,
                               capability: BaseCapability,
                               query: str) -> tuple:
        """
        计算匹配分数

        Args:
            capability: 能力
            query: 查询

        Returns:
            tuple: (分数, 匹配类型, 匹配字段)
        """
        metadata = capability.metadata
        score = 0.0
        match_type = ""
        matched_fields = []

        # 名称完全匹配
        if query == metadata.name.lower():
            score = self._match_weights['name_exact']
            match_type = "name_exact"
            matched_fields.append("name")
            return score, match_type, matched_fields

        # 名称部分匹配
        if query in metadata.name.lower():
            score = max(score, self._match_weights['name_partial'])
            match_type = "name_partial"
            matched_fields.append("name")

        # 显示名称匹配
        if query in metadata.display_name.lower():
            score = max(score, self._match_weights['name_partial'] * 0.9)
            if not match_type:
                match_type = "display_name"
            matched_fields.append("display_name")

        # 描述匹配
        if metadata.description and query in metadata.description.lower():
            score = max(score, self._match_weights['description'])
            if not match_type:
                match_type = "description"
            matched_fields.append("description")

        # 标签匹配
        for tag in metadata.tags:
            if query in tag.lower():
                score = max(score, self._match_weights['tag'])
                if not match_type:
                    match_type = "tag"
                matched_fields.append(f"tag:{tag}")
                break

        # 分类匹配
        if metadata.category and query in metadata.category.lower():
            score = max(score, self._match_weights['category'])
            if not match_type:
                match_type = "category"
            matched_fields.append("category")

        return score, match_type, matched_fields

    def find_by_tags(self, tags: List[str]) -> List[BaseCapability]:
        """
        按标签查找能力

        Args:
            tags: 标签列表

        Returns:
            List[BaseCapability]: 能力列表
        """
        if not tags:
            return []

        capabilities = self._center.get_all_capabilities()
        results = []

        for capability in capabilities.values():
            capability_tags = set(t.lower() for t in capability.metadata.tags)
            query_tags = set(t.lower() for t in tags)

            # 至少匹配一个标签
            if capability_tags & query_tags:
                results.append(capability)

        return results

    def find_by_category(self, category: str) -> List[BaseCapability]:
        """
        按分类查找能力

        Args:
            category: 分类

        Returns:
            List[BaseCapability]: 能力列表
        """
        capabilities = self._center.get_all_capabilities()

        return [
            cap for cap in capabilities.values()
            if cap.metadata.category.lower() == category.lower()
        ]

    def find_by_type(self, capability_type: CapabilityType) -> List[BaseCapability]:
        """
        按类型查找能力

        Args:
            capability_type: 能力类型

        Returns:
            List[BaseCapability]: 能力列表
        """
        return self._center.get_capabilities_by_type(capability_type)

    def find_by_level(self, level: CapabilityLevel) -> List[BaseCapability]:
        """
        按级别查找能力

        Args:
            level: 能力级别

        Returns:
            List[BaseCapability]: 能力列表
        """
        capabilities = self._center.get_all_capabilities()

        return [
            cap for cap in capabilities.values()
            if cap.metadata.level == level
        ]

    def get_recommendations(self,
                           context: Dict[str, Any],
                           limit: int = 5) -> List[BaseCapability]:
        """
        获取推荐能力

        基于上下文推荐相关能力

        Args:
            context: 上下文信息
            limit: 返回数量

        Returns:
            List[BaseCapability]: 推荐的能力列表
        """
        # 简化实现：基于历史使用频率和标签相似度
        capabilities = self._center.get_all_capabilities()

        # 计算推荐分数
        scored_capabilities = []

        for capability in capabilities.values():
            score = 0.0

            # 基于使用频率
            stats = capability.execution_stats
            if stats.total_executions > 0:
                score += stats.success_count / stats.total_executions * 0.5

            # 基于标签匹配
            context_tags = context.get('tags', [])
            capability_tags = set(capability.metadata.tags)
            matching_tags = capability_tags & set(context_tags)
            score += len(matching_tags) * 0.3

            if score > 0:
                scored_capabilities.append((capability, score))

        # 排序并返回
        scored_capabilities.sort(key=lambda x: x[1], reverse=True)
        return [cap for cap, _ in scored_capabilities[:limit]]

    def get_similar_capabilities(self,
                                 capability_name: str,
                                 limit: int = 5) -> List[BaseCapability]:
        """
        获取相似能力

        Args:
            capability_name: 参考能力名称
            limit: 返回数量

        Returns:
            List[BaseCapability]: 相似能力列表
        """
        reference = self._center.get_capability(capability_name)

        if not reference:
            return []

        ref_metadata = reference.metadata
        capabilities = self._center.get_all_capabilities()

        similarities = []

        for name, capability in capabilities.items():
            if name == capability_name:
                continue

            metadata = capability.metadata
            score = 0.0

            # 相同类型
            if metadata.capability_type == ref_metadata.capability_type:
                score += 0.3

            # 相同分类
            if metadata.category == ref_metadata.category:
                score += 0.3

            # 标签相似度
            ref_tags = set(ref_metadata.tags)
            cap_tags = set(metadata.tags)
            if ref_tags:
                tag_similarity = len(ref_tags & cap_tags) / len(ref_tags)
                score += tag_similarity * 0.4

            if score > 0:
                similarities.append((capability, score))

        # 排序并返回
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [cap for cap, _ in similarities[:limit]]

    def set_match_weights(self, weights: Dict[str, float]):
        """
        设置匹配权重

        Args:
            weights: 权重字典
        """
        self._match_weights.update(weights)
        logger.info(f"匹配权重已更新: {self._match_weights}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "indexed_keywords": len(self._search_index),
            "match_weights": self._match_weights,
            "total_capabilities": len(self._center.get_all_capabilities())
        }
