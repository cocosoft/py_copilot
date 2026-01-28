"""
长期记忆机制 - 记忆检索算法

实现智能记忆检索、相关性排序、记忆压缩和优化算法。
"""
import math
import re
import heapq
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from .memory_models import (
    MemoryItem, MemoryType, MemoryPriority, MemoryAccessPattern,
    memory_manager
)


class MemoryRetrievalEngine:
    """记忆检索引擎"""
    
    def __init__(self):
        """初始化记忆检索引擎"""
        self.cache = {}
        self.cache_ttl = 300  # 缓存TTL（秒）
        
    async def retrieve_memories(self, 
                              agent_id: str,
                              user_id: str,
                              query: str = None,
                              context: str = None,
                              memory_types: List[MemoryType] = None,
                              access_pattern: MemoryAccessPattern = MemoryAccessPattern.RECENT,
                              max_results: int = 5,
                              min_relevance: float = 0.1) -> List[MemoryItem]:
        """检索记忆
        
        Args:
            agent_id: 智能体ID
            user_id: 用户ID
            query: 查询文本
            context: 上下文信息
            memory_types: 记忆类型过滤
            access_pattern: 访问模式
            max_results: 最大结果数
            min_relevance: 最小相关性阈值
            
        Returns:
            记忆项列表
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                agent_id, user_id, query, context, memory_types, access_pattern
            )
            
            # 检查缓存
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result[:max_results]
                
            # 获取基础记忆列表
            base_memories = memory_manager.search_memories(
                agent_id=agent_id,
                user_id=user_id,
                query=query,
                memory_type=memory_types[0] if memory_types and len(memory_types) == 1 else None,
                limit=100  # 获取更多结果用于排序
            )
            
            # 应用访问模式过滤
            filtered_memories = self._apply_access_pattern(
                base_memories, access_pattern, query
            )
            
            # 应用记忆类型过滤
            if memory_types and len(memory_types) > 1:
                filtered_memories = [m for m in filtered_memories 
                                   if m.memory_type in memory_types]
            
            # 计算相关性分数
            scored_memories = []
            for memory in filtered_memories:
                relevance_score = self._calculate_relevance_score(
                    memory, query, context
                )
                
                if relevance_score >= min_relevance:
                    scored_memories.append((relevance_score, memory))
            
            # 按相关性排序
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            
            # 选择最佳结果
            result_memories = [memory for score, memory in scored_memories[:max_results]]
            
            # 缓存结果
            self._cache_result(cache_key, result_memories)
            
            return result_memories
            
        except Exception as e:
            print(f"检索记忆失败: {e}")
            return []
            
    def _generate_cache_key(self, 
                          agent_id: str,
                          user_id: str,
                          query: str,
                          context: str,
                          memory_types: List[MemoryType],
                          access_pattern: MemoryAccessPattern) -> str:
        """生成缓存键
        
        Args:
            agent_id: 智能体ID
            user_id: 用户ID
            query: 查询文本
            context: 上下文信息
            memory_types: 记忆类型
            access_pattern: 访问模式
            
        Returns:
            缓存键
        """
        type_str = "|".join([t.value for t in memory_types]) if memory_types else "all"
        pattern_str = access_pattern.value if access_pattern else "recent"
        
        key_parts = [
            f"agent:{agent_id}",
            f"user:{user_id}",
            f"query:{query or 'none'}",
            f"context:{context or 'none'}",
            f"types:{type_str}",
            f"pattern:{pattern_str}"
        ]
        
        return "|".join(key_parts)
        
    def _get_cached_result(self, cache_key: str) -> Optional[List[MemoryItem]]:
        """获取缓存结果
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存结果，如果未找到或过期返回None
        """
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            timestamp, memories = cached_data
            
            # 检查是否过期
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return memories
            else:
                # 清理过期缓存
                del self.cache[cache_key]
                
        return None
        
    def _cache_result(self, cache_key: str, memories: List[MemoryItem]):
        """缓存结果
        
        Args:
            cache_key: 缓存键
            memories: 记忆列表
        """
        # 限制缓存大小
        if len(self.cache) > 1000:
            # 清理最旧的缓存
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]
            
        self.cache[cache_key] = (datetime.now(), memories)
        
    def _apply_access_pattern(self, 
                            memories: List[MemoryItem],
                            access_pattern: MemoryAccessPattern,
                            query: str = None) -> List[MemoryItem]:
        """应用访问模式过滤
        
        Args:
            memories: 记忆列表
            access_pattern: 访问模式
            query: 查询文本
            
        Returns:
            过滤后的记忆列表
        """
        if not memories:
            return []
            
        if access_pattern == MemoryAccessPattern.FREQUENT:
            # 按访问频率排序
            return sorted(memories, key=lambda m: m.access_count, reverse=True)
            
        elif access_pattern == MemoryAccessPattern.RECENT:
            # 按最近访问排序
            return sorted(memories, key=lambda m: m.last_accessed, reverse=True)
            
        elif access_pattern == MemoryAccessPattern.IMPORTANT:
            # 按优先级和相关性排序
            scored_memories = []
            for memory in memories:
                score = self._calculate_importance_score(memory, query)
                scored_memories.append((score, memory))
                
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            return [memory for score, memory in scored_memories]
            
        elif access_pattern == MemoryAccessPattern.RANDOM:
            # 随机排序
            import random
            random.shuffle(memories)
            return memories
            
        else:
            # 默认按最近访问排序
            return sorted(memories, key=lambda m: m.last_accessed, reverse=True)
            
    def _calculate_relevance_score(self, 
                                 memory: MemoryItem,
                                 query: str = None,
                                 context: str = None) -> float:
        """计算记忆相关性分数
        
        Args:
            memory: 记忆项
            query: 查询文本
            context: 上下文信息
            
        Returns:
            相关性分数（0-1）
        """
        # 基础相关性分数
        base_score = memory.calculate_relevance_score(query)
        
        # 上下文相关性
        context_score = 0.0
        if context:
            context_score = self._calculate_text_similarity(memory.content, context) * 0.3
            
        # 类型权重
        type_weights = {
            MemoryType.CONVERSATION: 0.8,
            MemoryType.FACT: 1.0,
            MemoryType.PREFERENCE: 0.9,
            MemoryType.BEHAVIOR: 0.7,
            MemoryType.KNOWLEDGE: 1.0,
            MemoryType.EVENT: 0.6,
            MemoryType.RELATIONSHIP: 0.8,
            MemoryType.CUSTOM: 0.5
        }
        type_weight = type_weights.get(memory.memory_type, 0.5)
        
        # 组合分数
        relevance_score = (base_score * 0.6) + (context_score * 0.4)
        relevance_score *= type_weight
        
        return min(1.0, relevance_score)
        
    def _calculate_importance_score(self, 
                                  memory: MemoryItem,
                                  query: str = None) -> float:
        """计算记忆重要性分数
        
        Args:
            memory: 记忆项
            query: 查询文本
            
        Returns:
            重要性分数（0-1）
        """
        # 优先级分数
        priority_scores = {
            MemoryPriority.LOW: 0.2,
            MemoryPriority.MEDIUM: 0.5,
            MemoryPriority.HIGH: 0.8,
            MemoryPriority.CRITICAL: 1.0
        }
        priority_score = priority_scores.get(memory.priority, 0.5)
        
        # 访问频率分数（对数缩放）
        access_score = min(1.0, math.log10(memory.access_count + 1) / 2.0)
        
        # 时间衰减分数
        days_since_creation = (datetime.now() - memory.created_at).days
        creation_score = max(0.1, 1.0 - (days_since_creation / 365.0))
        
        # 内容长度分数（较长的内容可能更重要）
        length_score = min(1.0, len(memory.content) / 1000.0)
        
        # 组合分数
        importance_score = (
            priority_score * 0.3 +
            access_score * 0.25 +
            creation_score * 0.25 +
            length_score * 0.2
        )
        
        # 如果提供了查询，增加查询相关性权重
        if query:
            query_relevance = memory.calculate_relevance_score(query)
            importance_score = (importance_score * 0.7) + (query_relevance * 0.3)
            
        return min(1.0, importance_score)
        
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数（0-1）
        """
        if not text1 or not text2:
            return 0.0
            
        # 简单的Jaccard相似度
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0


class MemoryCompressionEngine:
    """记忆压缩引擎"""
    
    def __init__(self):
        """初始化记忆压缩引擎"""
        self.compression_threshold = 1000  # 压缩阈值（记忆数量）
        
    async def compress_memories(self, 
                              agent_id: str,
                              user_id: str,
                              target_size: int = 500) -> Dict[str, Any]:
        """压缩记忆
        
        Args:
            agent_id: 智能体ID
            user_id: 用户ID
            target_size: 目标记忆数量
            
        Returns:
            压缩结果
        """
        try:
            # 获取所有记忆
            all_memories = memory_manager.search_memories(
                agent_id=agent_id,
                user_id=user_id,
                limit=10000  # 获取大量记忆用于压缩
            )
            
            if len(all_memories) <= target_size:
                return {
                    "compressed": False,
                    "reason": "记忆数量未超过阈值",
                    "original_count": len(all_memories),
                    "target_count": target_size
                }
            
            # 计算记忆重要性分数
            scored_memories = []
            retrieval_engine = MemoryRetrievalEngine()
            
            for memory in all_memories:
                importance_score = retrieval_engine._calculate_importance_score(memory)
                scored_memories.append((importance_score, memory))
            
            # 按重要性排序
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            
            # 选择最重要的记忆
            important_memories = [memory for score, memory in scored_memories[:target_size]]
            
            # 合并相似记忆
            compressed_memories = self._merge_similar_memories(important_memories)
            
            # 更新数据库（实际实现应该更复杂）
            # 这里只是返回压缩结果，实际应该删除不重要的记忆
            
            return {
                "compressed": True,
                "original_count": len(all_memories),
                "compressed_count": len(compressed_memories),
                "reduction_ratio": (len(all_memories) - len(compressed_memories)) / len(all_memories),
                "memories_kept": [m.memory_id for m in compressed_memories[:10]]  # 只显示前10个
            }
            
        except Exception as e:
            return {
                "compressed": False,
                "error": str(e),
                "original_count": 0,
                "compressed_count": 0
            }
            
    def _merge_similar_memories(self, memories: List[MemoryItem]) -> List[MemoryItem]:
        """合并相似记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            合并后的记忆列表
        """
        if len(memories) <= 1:
            return memories
            
        # 按类型分组
        memories_by_type = defaultdict(list)
        for memory in memories:
            memories_by_type[memory.memory_type].append(memory)
        
        merged_memories = []
        
        for memory_type, type_memories in memories_by_type.items():
            if memory_type in [MemoryType.CONVERSATION, MemoryType.EVENT]:
                # 对于对话和事件类型，按时间聚类
                clustered_memories = self._cluster_by_time(type_memories)
                merged_memories.extend(clustered_memories)
            else:
                # 对于其他类型，按内容相似度合并
                clustered_memories = self._cluster_by_content(type_memories)
                merged_memories.extend(clustered_memories)
                
        return merged_memories
        
    def _cluster_by_time(self, memories: List[MemoryItem], 
                        time_window_hours: int = 24) -> List[MemoryItem]:
        """按时间聚类记忆
        
        Args:
            memories: 记忆列表
            time_window_hours: 时间窗口（小时）
            
        Returns:
            聚类后的记忆列表
        """
        if not memories:
            return []
            
        # 按时间排序
        memories.sort(key=lambda m: m.created_at)
        
        clusters = []
        current_cluster = []
        
        for memory in memories:
            if not current_cluster:
                current_cluster.append(memory)
            else:
                # 检查是否在同一时间窗口内
                last_memory = current_cluster[-1]
                time_diff = (memory.created_at - last_memory.created_at).total_seconds() / 3600
                
                if time_diff <= time_window_hours:
                    current_cluster.append(memory)
                else:
                    # 创建新的聚类
                    clusters.append(self._merge_cluster(current_cluster))
                    current_cluster = [memory]
        
        # 添加最后一个聚类
        if current_cluster:
            clusters.append(self._merge_cluster(current_cluster))
            
        return clusters
        
    def _cluster_by_content(self, memories: List[MemoryItem],
                           similarity_threshold: float = 0.7) -> List[MemoryItem]:
        """按内容相似度聚类记忆
        
        Args:
            memories: 记忆列表
            similarity_threshold: 相似度阈值
            
        Returns:
            聚类后的记忆列表
        """
        if len(memories) <= 1:
            return memories
            
        retrieval_engine = MemoryRetrievalEngine()
        clusters = []
        
        for memory in memories:
            matched = False
            
            for cluster in clusters:
                # 计算与聚类中心记忆的相似度
                center_memory = cluster[0]  # 使用第一个记忆作为中心
                similarity = retrieval_engine._calculate_text_similarity(
                    memory.content, center_memory.content
                )
                
                if similarity >= similarity_threshold:
                    cluster.append(memory)
                    matched = True
                    break
                    
            if not matched:
                # 创建新的聚类
                clusters.append([memory])
                
        # 合并每个聚类
        merged_memories = []
        for cluster in clusters:
            if len(cluster) == 1:
                merged_memories.append(cluster[0])
            else:
                merged_memories.append(self._merge_cluster(cluster))
                
        return merged_memories
        
    def _merge_cluster(self, cluster: List[MemoryItem]) -> MemoryItem:
        """合并聚类中的记忆
        
        Args:
            cluster: 记忆聚类
            
        Returns:
            合并后的记忆项
        """
        if not cluster:
            return None
            
        if len(cluster) == 1:
            return cluster[0]
            
        # 选择最重要的记忆作为基础
        base_memory = max(cluster, key=lambda m: m.priority.value)
        
        # 合并内容
        merged_content = base_memory.content
        if len(cluster) > 1:
            # 添加其他记忆的摘要
            other_summaries = []
            for memory in cluster:
                if memory != base_memory and memory.summary:
                    other_summaries.append(memory.summary)
                    
            if other_summaries:
                merged_content += "\n\n相关记忆：" + "; ".join(other_summaries)
        
        # 创建合并后的记忆
        merged_memory = MemoryItem(
            agent_id=base_memory.agent_id,
            user_id=base_memory.user_id,
            memory_type=base_memory.memory_type,
            content=merged_content,
            summary=f"合并了{len(cluster)}个相关记忆",
            priority=base_memory.priority,
            access_count=sum(m.access_count for m in cluster),
            last_accessed=max(m.last_accessed for m in cluster),
            created_at=base_memory.created_at,
            metadata={
                "merged_from": [m.memory_id for m in cluster],
                "original_count": len(cluster)
            },
            tags=list(set(tag for m in cluster for tag in m.tags))
        )
        
        return merged_memory


# 全局记忆检索引擎实例
memory_retrieval_engine = MemoryRetrievalEngine()

# 全局记忆压缩引擎实例
memory_compression_engine = MemoryCompressionEngine()