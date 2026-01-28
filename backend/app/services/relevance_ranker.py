"""
相关性排序器

负责计算搜索结果的相关性分数，支持多因素权重计算和智能排序。
结合文本匹配度、语义相似度、使用频率等因素进行综合评分。
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.logging_config import logger
from app.schemas.skill_metadata import SkillMetadata


@dataclass
class RankedResult:
    """排序后的搜索结果"""
    skill_id: str
    final_score: float
    component_scores: Dict[str, float]
    skill_metadata: Optional[SkillMetadata] = None


@dataclass
class RankingWeights:
    """排序权重配置"""
    text_similarity: float = 0.4      # 文本相似度权重
    semantic_similarity: float = 0.3  # 语义相似度权重
    usage_frequency: float = 0.15     # 使用频率权重
    recency: float = 0.1              # 时效性权重
    popularity: float = 0.05          # 流行度权重


@dataclass
class RankingStatistics:
    """排序统计信息"""
    total_rankings: int = 0
    average_ranking_time: float = 0.0
    weight_distribution: Dict[str, float] = None
    performance_metrics: Dict[str, float] = None


class TextSimilarityCalculator:
    """文本相似度计算器"""
    
    def __init__(self):
        # 停用词列表
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去'
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（基于Jaccard相似度）"""
        if not text1 or not text2:
            return 0.0
        
        # 分词
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # 计算Jaccard相似度
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _tokenize(self, text: str) -> List[str]:
        """中文分词（简化实现）"""
        if not text:
            return []
        
        # 转换为小写
        text = text.lower()
        
        # 简单的分词
        tokens = re.findall(r'[\w\u4e00-\u9fff]+', text)
        
        # 过滤停用词和短词
        tokens = [
            token for token in tokens 
            if len(token) > 1 and token not in self.stop_words
        ]
        
        return tokens


class SemanticSimilarityCalculator:
    """语义相似度计算器（简化实现）"""
    
    def __init__(self):
        # 预定义的语义关系（生产环境应使用词向量模型）
        self.semantic_relations = {
            '算法': {'计算', '程序', '代码', '逻辑', '数学'},
            '艺术': {'设计', '创意', '美学', '视觉', '创作'},
            '数据': {'分析', '统计', '信息', '数字', '处理'},
            '工具': {'软件', '应用', '程序', '系统', '平台'},
            '生成': {'创建', '产生', '制作', '构建', '形成'}
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 提取关键词
        keywords1 = self._extract_keywords(text1)
        keywords2 = self._extract_keywords(text2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # 计算语义重叠度
        semantic_overlap = self._calculate_semantic_overlap(keywords1, keywords2)
        
        return semantic_overlap
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（生产环境应使用TF-IDF等算法）
        tokens = re.findall(r'[\w\u4e00-\u9fff]{2,}', text.lower())
        
        # 过滤常见词
        common_words = {'这个', '那个', '一些', '各种', '多个', '不同'}
        keywords = [token for token in tokens if token not in common_words]
        
        # 取前10个关键词
        return keywords[:10]
    
    def _calculate_semantic_overlap(self, keywords1: List[str], keywords2: List[str]) -> float:
        """计算语义重叠度"""
        if not keywords1 or not keywords2:
            return 0.0
        
        overlap_score = 0.0
        
        for kw1 in keywords1:
            for kw2 in keywords2:
                # 直接匹配
                if kw1 == kw2:
                    overlap_score += 1.0
                # 语义关系匹配
                elif self._has_semantic_relation(kw1, kw2):
                    overlap_score += 0.5
        
        # 归一化到0-1范围
        max_possible = len(keywords1) * len(keywords2)
        return overlap_score / max_possible if max_possible > 0 else 0.0
    
    def _has_semantic_relation(self, word1: str, word2: str) -> bool:
        """检查两个词是否有语义关系"""
        for concept, related_words in self.semantic_relations.items():
            if word1 == concept and word2 in related_words:
                return True
            if word2 == concept and word1 in related_words:
                return True
        
        return False


class UsageTracker:
    """使用频率跟踪器"""
    
    def __init__(self):
        self.usage_data: Dict[str, Dict] = defaultdict(dict)
        
    def record_usage(self, skill_id: str, timestamp: datetime = None):
        """记录技能使用"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if skill_id not in self.usage_data:
            self.usage_data[skill_id] = {
                'total_uses': 0,
                'recent_uses': [],
                'first_used': timestamp,
                'last_used': timestamp
            }
        
        data = self.usage_data[skill_id]
        data['total_uses'] += 1
        data['recent_uses'].append(timestamp)
        data['last_used'] = timestamp
        
        # 清理过期的使用记录（保留最近30天）
        cutoff_time = timestamp - timedelta(days=30)
        data['recent_uses'] = [
            t for t in data['recent_uses'] if t > cutoff_time
        ]
    
    def get_usage_score(self, skill_id: str) -> float:
        """计算使用频率分数"""
        if skill_id not in self.usage_data:
            return 0.0
        
        data = self.usage_data[skill_id]
        
        # 基于总使用次数和近期使用频率计算分数
        total_uses = data['total_uses']
        recent_uses = len(data['recent_uses'])
        
        # 使用对数函数避免极端值影响
        total_score = math.log10(total_uses + 1) / 3.0  # 归一化到0-1范围
        recent_score = min(recent_uses / 10.0, 1.0)     # 近期使用分数
        
        # 综合分数（近期使用权重更高）
        final_score = (total_score * 0.3 + recent_score * 0.7)
        
        return min(final_score, 1.0)
    
    def get_recency_score(self, skill_id: str) -> float:
        """计算时效性分数"""
        if skill_id not in self.usage_data:
            return 0.0
        
        data = self.usage_data[skill_id]
        last_used = data['last_used']
        
        # 计算距离现在的时间（天数）
        days_since_last_use = (datetime.now() - last_used).days
        
        # 使用指数衰减函数计算时效性分数
        # 最近使用（0天）得1分，30天前使用得0.1分
        recency_score = math.exp(-days_since_last_use / 10.0)
        
        return min(recency_score, 1.0)


class RelevanceRanker:
    """相关性排序器"""
    
    def __init__(self, weights: RankingWeights = None):
        """
        初始化相关性排序器
        
        Args:
            weights: 排序权重配置
        """
        self.weights = weights or RankingWeights()
        self.text_similarity_calc = TextSimilarityCalculator()
        self.semantic_similarity_calc = SemanticSimilarityCalculator()
        self.usage_tracker = UsageTracker()
        self.statistics = RankingStatistics()
        
        # 验证权重总和为1
        self._validate_weights()
    
    def rank_results(
        self, 
        search_results: List[Dict[str, Any]], 
        query: str,
        skill_registry: Any = None
    ) -> List[RankedResult]:
        """
        对搜索结果进行相关性排序
        
        Args:
            search_results: 原始搜索结果
            query: 搜索查询
            skill_registry: 技能注册器（用于获取技能元数据）
            
        Returns:
            排序后的结果列表
        """
        import time
        start_time = time.time()
        
        try:
            ranked_results = []
            
            for result in search_results:
                skill_id = result.get('skill_id')
                base_score = result.get('score', 0.0)
                
                # 获取技能元数据
                skill_metadata = None
                if skill_registry:
                    skill_metadata = skill_registry.get_skill(skill_id)
                
                # 计算各组件分数
                component_scores = self._calculate_component_scores(
                    skill_id, query, skill_metadata, base_score
                )
                
                # 计算最终分数
                final_score = self._calculate_final_score(component_scores)
                
                # 创建排序结果
                ranked_result = RankedResult(
                    skill_id=skill_id,
                    final_score=final_score,
                    component_scores=component_scores,
                    skill_metadata=skill_metadata
                )
                
                ranked_results.append(ranked_result)
            
            # 按最终分数排序
            ranked_results.sort(key=lambda x: x.final_score, reverse=True)
            
            # 更新统计信息
            ranking_time = time.time() - start_time
            self._update_statistics(len(ranked_results), ranking_time)
            
            logger.debug(f"相关性排序完成，共排序 {len(ranked_results)} 个结果，耗时 {ranking_time:.3f} 秒")
            
            return ranked_results
            
        except Exception as e:
            logger.error(f"相关性排序失败: {e}")
            return []
    
    def _calculate_component_scores(
        self, 
        skill_id: str, 
        query: str, 
        skill_metadata: Optional[SkillMetadata],
        base_score: float
    ) -> Dict[str, float]:
        """计算各组件分数"""
        scores = {'base_score': base_score}
        
        if skill_metadata:
            # 文本相似度
            text_similarity = self._calculate_text_similarity(skill_metadata, query)
            scores['text_similarity'] = text_similarity
            
            # 语义相似度
            semantic_similarity = self._calculate_semantic_similarity(skill_metadata, query)
            scores['semantic_similarity'] = semantic_similarity
        else:
            scores['text_similarity'] = 0.0
            scores['semantic_similarity'] = 0.0
        
        # 使用频率
        usage_frequency = self.usage_tracker.get_usage_score(skill_id)
        scores['usage_frequency'] = usage_frequency
        
        # 时效性
        recency = self.usage_tracker.get_recency_score(skill_id)
        scores['recency'] = recency
        
        # 流行度（简化实现，基于使用频率）
        popularity = usage_frequency  # 使用频率作为流行度代理
        scores['popularity'] = popularity
        
        return scores
    
    def _calculate_text_similarity(self, skill_metadata: SkillMetadata, query: str) -> float:
        """计算文本相似度"""
        # 组合技能文本
        skill_text = f"{skill_metadata.name} {skill_metadata.description} {' '.join(skill_metadata.tags)}"
        
        return self.text_similarity_calc.calculate_similarity(skill_text, query)
    
    def _calculate_semantic_similarity(self, skill_metadata: SkillMetadata, query: str) -> float:
        """计算语义相似度"""
        # 组合技能文本
        skill_text = f"{skill_metadata.name} {skill_metadata.description}"
        
        return self.semantic_similarity_calc.calculate_similarity(skill_text, query)
    
    def _calculate_final_score(self, component_scores: Dict[str, float]) -> float:
        """计算最终分数"""
        final_score = 0.0
        
        # 基础搜索分数
        final_score += component_scores['base_score'] * 0.2
        
        # 文本相似度
        final_score += component_scores['text_similarity'] * self.weights.text_similarity
        
        # 语义相似度
        final_score += component_scores['semantic_similarity'] * self.weights.semantic_similarity
        
        # 使用频率
        final_score += component_scores['usage_frequency'] * self.weights.usage_frequency
        
        # 时效性
        final_score += component_scores['recency'] * self.weights.recency
        
        # 流行度
        final_score += component_scores['popularity'] * self.weights.popularity
        
        return min(final_score, 1.0)
    
    def record_skill_usage(self, skill_id: str, timestamp: datetime = None):
        """记录技能使用"""
        self.usage_tracker.record_usage(skill_id, timestamp)
    
    def update_weights(self, new_weights: RankingWeights) -> bool:
        """更新排序权重"""
        try:
            self.weights = new_weights
            self._validate_weights()
            logger.info("排序权重更新成功")
            return True
        except Exception as e:
            logger.error(f"更新排序权重失败: {e}")
            return False
    
    def get_statistics(self) -> RankingStatistics:
        """获取排序统计信息"""
        return self.statistics
    
    def _validate_weights(self):
        """验证权重总和为1"""
        total_weight = (
            self.weights.text_similarity +
            self.weights.semantic_similarity +
            self.weights.usage_frequency +
            self.weights.recency +
            self.weights.popularity
        )
        
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"权重总和必须为1，当前总和: {total_weight}")
    
    def _update_statistics(self, rankings_count: int, ranking_time: float):
        """更新统计信息"""
        self.statistics.total_rankings += rankings_count
        
        # 计算平均排序时间
        total_time = self.statistics.average_ranking_time * (self.statistics.total_rankings - rankings_count)
        self.statistics.average_ranking_time = (total_time + ranking_time) / self.statistics.total_rankings
        
        # 更新权重分布
        self.statistics.weight_distribution = {
            'text_similarity': self.weights.text_similarity,
            'semantic_similarity': self.weights.semantic_similarity,
            'usage_frequency': self.weights.usage_frequency,
            'recency': self.weights.recency,
            'popularity': self.weights.popularity
        }
        
        # 更新性能指标
        self.statistics.performance_metrics = {
            'last_ranking_time': ranking_time,
            'rankings_per_second': rankings_count / ranking_time if ranking_time > 0 else 0.0
        }


def create_relevance_ranker(weights: RankingWeights = None) -> RelevanceRanker:
    """
    创建相关性排序器实例
    
    Args:
        weights: 排序权重配置
        
    Returns:
        相关性排序器实例
    """
    return RelevanceRanker(weights)


# 测试函数
def test_relevance_ranker():
    """测试相关性排序器功能"""
    # 创建排序器
    weights = RankingWeights(
        text_similarity=0.4,
        semantic_similarity=0.3,
        usage_frequency=0.15,
        recency=0.1,
        popularity=0.05
    )
    
    ranker = RelevanceRanker(weights)
    
    # 创建测试搜索结果
    search_results = [
        {'skill_id': 'skill_001', 'score': 0.8},
        {'skill_id': 'skill_002', 'score': 0.6},
        {'skill_id': 'skill_003', 'score': 0.9}
    ]
    
    # 创建测试技能元数据
    from app.schemas.skill_metadata import SkillMetadata, SkillCategory
    from datetime import datetime
    
    test_skills = {
        'skill_001': SkillMetadata(
            skill_id='skill_001',
            name='算法艺术生成',
            description='基于算法的艺术创作工具',
            category=SkillCategory.DESIGN.value,
            tags=['艺术', '算法', '生成'],
            # 其他字段省略...
        ),
        'skill_002': SkillMetadata(
            skill_id='skill_002', 
            name='数据分析工具',
            description='强大的数据分析工具',
            category=SkillCategory.DATA.value,
            tags=['数据', '分析', '统计'],
            # 其他字段省略...
        ),
        'skill_003': SkillMetadata(
            skill_id='skill_003',
            name='文档处理工具',
            description='高效的文档处理工具',
            category=SkillCategory.DOCUMENT.value,
            tags=['文档', '处理', '工具'],
            # 其他字段省略...
        )
    }
    
    # 模拟技能注册器
    class MockSkillRegistry:
        def get_skill(self, skill_id: str):
            return test_skills.get(skill_id)
    
    # 记录使用记录
    ranker.record_skill_usage('skill_001')
    ranker.record_skill_usage('skill_001')  # 多次使用
    ranker.record_skill_usage('skill_002')
    
    # 测试排序
    query = "算法艺术生成工具"
    ranked_results = ranker.rank_results(search_results, query, MockSkillRegistry())
    
    print(f"查询: {query}")
    print("排序结果:")
    for i, result in enumerate(ranked_results):
        print(f"{i+1}. {result.skill_id}: {result.final_score:.4f}")
        print(f"   组件分数: {result.component_scores}")
    
    # 测试统计信息
    stats = ranker.get_statistics()
    print(f"\n排序统计: {stats}")


if __name__ == "__main__":
    test_relevance_ranker()