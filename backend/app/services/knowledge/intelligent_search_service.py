"""
智能搜索服务

基于现有语义搜索开发智能搜索功能

任务编号: Phase2-Week6
阶段: 第二阶段 - 功能简陋问题优化
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
import json

from app.core.logging_config import logger


class SearchIntent(Enum):
    """搜索意图类型"""
    INFORMATIONAL = "informational"  # 信息查询
    NAVIGATIONAL = "navigational"    # 导航查询
    TRANSACTIONAL = "transactional"  # 事务查询
    ENTITY = "entity"                # 实体查询
    RELATIONSHIP = "relationship"    # 关系查询
    UNKNOWN = "unknown"              # 未知


class QueryType(Enum):
    """查询类型"""
    KEYWORD = "keyword"              # 关键词查询
    NATURAL_LANGUAGE = "natural_language"  # 自然语言查询
    STRUCTURED = "structured"        # 结构化查询
    HYBRID = "hybrid"                # 混合查询


@dataclass
class SearchContext:
    """搜索上下文"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    previous_queries: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class IntelligentSearchResult:
    """智能搜索结果"""
    query: str
    original_query: str
    intent: SearchIntent
    query_type: QueryType
    results: List[Dict[str, Any]]
    suggestions: List[str]
    related_queries: List[str]
    facets: Dict[str, List[str]]
    total_count: int
    search_time: float
    context: SearchContext
    explanation: str


class QueryAnalyzer:
    """查询分析器"""

    def __init__(self):
        self.entity_patterns = {
            'person': r'(?:谁|什么人|哪位|名字是)',
            'organization': r'(?:哪家公司|哪个组织|机构)',
            'location': r'(?:哪里|什么地方|地点|位置)',
            'date': r'(?:什么时候|何时|时间|日期)',
        }

        self.intent_patterns = {
            SearchIntent.INFORMATIONAL: [
                r'(?:什么是|什么是|介绍|说明|解释)',
                r'(?:如何|怎么|怎样|方法)',
                r'(?:为什么|为何|原因)',
            ],
            SearchIntent.NAVIGATIONAL: [
                r'(?:打开|进入|访问|找到)',
                r'(?:页面|界面|功能|模块)',
            ],
            SearchIntent.TRANSACTIONAL: [
                r'(?:下载|导出|保存|创建|添加|删除)',
                r'(?:上传|导入|更新|修改)',
            ],
            SearchIntent.ENTITY: [
                r'(?:关于|有关|涉及|包含)',
                r'(?:列出|显示|查看)',
            ],
        }

    def analyze(self, query: str) -> Tuple[SearchIntent, QueryType, Dict[str, Any]]:
        """
        分析查询

        Args:
            query: 用户查询

        Returns:
            (意图, 查询类型, 分析详情)
        """
        # 检测查询类型
        query_type = self._detect_query_type(query)

        # 检测搜索意图
        intent = self._detect_intent(query)

        # 提取实体提及
        entities = self._extract_entities(query)

        # 提取关键词
        keywords = self._extract_keywords(query)

        analysis = {
            'entities': entities,
            'keywords': keywords,
            'complexity': self._calculate_complexity(query),
            'language': self._detect_language(query),
        }

        return intent, query_type, analysis

    def _detect_query_type(self, query: str) -> QueryType:
        """检测查询类型"""
        # 检查是否为结构化查询
        if any(op in query for op in ['AND', 'OR', 'NOT', ':', '>']):
            return QueryType.STRUCTURED

        # 检查是否为自然语言查询
        if len(query) > 10 and any(word in query for word in ['什么', '如何', '为什么', '哪里']):
            return QueryType.NATURAL_LANGUAGE

        # 检查是否为混合查询
        if re.search(r'["\']', query) or ':' in query:
            return QueryType.HYBRID

        return QueryType.KEYWORD

    def _detect_intent(self, query: str) -> SearchIntent:
        """检测搜索意图"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent

        # 检查是否为实体查询
        for entity_type, pattern in self.entity_patterns.items():
            if re.search(pattern, query):
                return SearchIntent.ENTITY

        return SearchIntent.UNKNOWN

    def _extract_entities(self, query: str) -> List[Dict[str, str]]:
        """提取实体提及"""
        entities = []

        # 简单的实体提取（实际应用中可以使用NER模型）
        # 提取引号中的内容
        quoted = re.findall(r'["\']([^"\']+)["\']', query)
        for text in quoted:
            entities.append({'text': text, 'type': 'quoted', 'position': query.find(text)})

        # 提取可能的专有名词（大写字母开头）
        proper_nouns = re.findall(r'[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*', query)
        for noun in proper_nouns:
            if len(noun) > 2:
                entities.append({'text': noun, 'type': 'proper_noun', 'position': query.find(noun)})

        return entities

    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 移除停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}

        words = re.findall(r'\b\w+\b', query)
        keywords = [w for w in words if w not in stop_words and len(w) > 1]

        return keywords

    def _calculate_complexity(self, query: str) -> float:
        """计算查询复杂度"""
        factors = [
            len(query) / 100,  # 长度因子
            len(re.findall(r'[，。？！；]', query)) / 5,  # 标点因子
            len(self._extract_keywords(query)) / 10,  # 关键词因子
        ]
        return min(sum(factors) / len(factors), 1.0)

    def _detect_language(self, query: str) -> str:
        """检测语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', query))
        total_chars = len(query)

        if chinese_chars / total_chars > 0.5:
            return 'zh'
        return 'en'


class QueryExpander:
    """查询扩展器"""

    def __init__(self):
        self.synonyms = {
            '人工智能': ['AI', '机器学习', '深度学习', '神经网络'],
            '公司': ['企业', '组织', '机构', '集团'],
            '产品': ['商品', '物品', '服务', '解决方案'],
        }

    def expand(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """
        扩展查询

        Args:
            query: 原始查询
            analysis: 查询分析结果

        Returns:
            扩展后的查询列表
        """
        expansions = [query]

        # 同义词扩展
        for word, synonyms in self.synonyms.items():
            if word in query:
                for synonym in synonyms:
                    expansion = query.replace(word, synonym)
                    if expansion != query:
                        expansions.append(expansion)

        # 关键词组合扩展
        keywords = analysis.get('keywords', [])
        if len(keywords) > 1:
            # 生成关键词的不同组合
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    expansion = f"{keywords[i]} {keywords[j]}"
                    if expansion != query:
                        expansions.append(expansion)

        return list(set(expansions))[:5]  # 最多返回5个扩展


class ResultRanker:
    """结果排序器"""

    def __init__(self):
        self.weights = {
            'relevance': 0.4,
            'recency': 0.2,
            'popularity': 0.2,
            'authority': 0.1,
            'personalization': 0.1,
        }

    def rank(self, results: List[Dict[str, Any]], context: SearchContext) -> List[Dict[str, Any]]:
        """
        对结果进行排序

        Args:
            results: 原始结果
            context: 搜索上下文

        Returns:
            排序后的结果
        """
        scored_results = []

        for result in results:
            score = self._calculate_score(result, context)
            scored_results.append({**result, '_score': score})

        # 按分数降序排序
        scored_results.sort(key=lambda x: x['_score'], reverse=True)

        return scored_results

    def _calculate_score(self, result: Dict[str, Any], context: SearchContext) -> float:
        """计算结果分数"""
        scores = {
            'relevance': result.get('relevance_score', 0.5),
            'recency': self._calculate_recency_score(result),
            'popularity': result.get('popularity_score', 0.5),
            'authority': result.get('authority_score', 0.5),
            'personalization': self._calculate_personalization_score(result, context),
        }

        total_score = sum(
            scores[key] * self.weights[key]
            for key in self.weights.keys()
        )

        return total_score

    def _calculate_recency_score(self, result: Dict[str, Any]) -> float:
        """计算时效性分数"""
        date_str = result.get('date') or result.get('created_at')
        if not date_str:
            return 0.5

        try:
            if isinstance(date_str, str):
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date = date_str

            days_ago = (datetime.now() - date).days
            # 30天内为满分，之后线性递减
            return max(0, 1 - days_ago / 30)
        except:
            return 0.5

    def _calculate_personalization_score(self, result: Dict[str, Any], context: SearchContext) -> float:
        """计算个性化分数"""
        preferences = context.user_preferences
        score = 0.5

        # 基于用户偏好调整分数
        preferred_types = preferences.get('preferred_types', [])
        if result.get('type') in preferred_types:
            score += 0.3

        preferred_tags = preferences.get('preferred_tags', [])
        result_tags = result.get('tags', [])
        if any(tag in preferred_tags for tag in result_tags):
            score += 0.2

        return min(score, 1.0)


class IntelligentSearchService:
    """智能搜索服务"""

    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.expander = QueryExpander()
        self.ranker = ResultRanker()
        self.search_history: List[Dict[str, Any]] = []

    async def search(
        self,
        query: str,
        context: Optional[SearchContext] = None,
        limit: int = 10
    ) -> IntelligentSearchResult:
        """
        执行智能搜索

        Args:
            query: 搜索查询
            context: 搜索上下文
            limit: 返回结果数量限制

        Returns:
            智能搜索结果
        """
        import time
        start_time = time.time()

        if context is None:
            context = SearchContext()

        logger.info(f"执行智能搜索: {query}")

        # 1. 查询分析
        intent, query_type, analysis = self.analyzer.analyze(query)
        logger.debug(f"查询分析: 意图={intent.value}, 类型={query_type.value}")

        # 2. 查询扩展
        expanded_queries = self.expander.expand(query, analysis)
        logger.debug(f"查询扩展: {expanded_queries}")

        # 3. 执行搜索（这里应该调用实际的搜索服务）
        raw_results = await self._execute_search(expanded_queries, context)

        # 4. 结果排序
        ranked_results = self.ranker.rank(raw_results, context)

        # 5. 生成建议
        suggestions = self._generate_suggestions(query, analysis)

        # 6. 生成相关查询
        related_queries = self._generate_related_queries(query, analysis)

        # 7. 生成分面
        facets = self._generate_facets(ranked_results)

        # 8. 生成解释
        explanation = self._generate_explanation(query, intent, query_type, analysis)

        search_time = time.time() - start_time

        # 记录搜索历史
        self._record_search(query, intent, len(ranked_results))

        return IntelligentSearchResult(
            query=query,
            original_query=query,
            intent=intent,
            query_type=query_type,
            results=ranked_results[:limit],
            suggestions=suggestions,
            related_queries=related_queries,
            facets=facets,
            total_count=len(ranked_results),
            search_time=search_time,
            context=context,
            explanation=explanation
        )

    async def _execute_search(
        self,
        queries: List[str],
        context: SearchContext
    ) -> List[Dict[str, Any]]:
        """执行实际搜索（模拟）"""
        # 这里应该调用语义搜索服务
        # 现在返回模拟数据
        mock_results = []

        for i, q in enumerate(queries):
            mock_results.append({
                'id': f'result_{i}',
                'title': f'搜索结果: {q}',
                'content': f'这是关于 "{q}" 的搜索结果的详细内容...',
                'type': 'document',
                'relevance_score': 0.9 - i * 0.1,
                'date': datetime.now().isoformat(),
                'tags': ['搜索', '结果'],
            })

        return mock_results

    def _generate_suggestions(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """生成搜索建议"""
        suggestions = []
        keywords = analysis.get('keywords', [])

        # 基于关键词生成建议
        for keyword in keywords[:3]:
            suggestions.append(f'{keyword} 教程')
            suggestions.append(f'{keyword} 案例')

        # 添加常见后缀
        suffixes = ['是什么', '怎么用', '最佳实践', '入门指南']
        for suffix in suffixes[:2]:
            suggestions.append(f'{query} {suffix}')

        return suggestions[:5]

    def _generate_related_queries(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """生成相关查询"""
        related = []
        keywords = analysis.get('keywords', [])

        # 基于实体生成相关查询
        entities = analysis.get('entities', [])
        for entity in entities[:2]:
            related.append(f'关于 {entity["text"]} 的更多信息')

        # 基于关键词组合
        if len(keywords) >= 2:
            related.append(f'{keywords[0]} 和 {keywords[1]} 的区别')
            related.append(f'{keywords[0]} 与 {keywords[1]} 的关系')

        return related[:4]

    def _generate_facets(self, results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """生成分面"""
        facets = {
            'type': [],
            'date': [],
            'tags': [],
        }

        type_count = {}
        tag_count = {}

        for result in results:
            # 类型分面
            result_type = result.get('type', 'unknown')
            type_count[result_type] = type_count.get(result_type, 0) + 1

            # 标签分面
            tags = result.get('tags', [])
            for tag in tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1

        # 按计数排序
        facets['type'] = [t for t, c in sorted(type_count.items(), key=lambda x: x[1], reverse=True)[:5]]
        facets['tags'] = [t for t, c in sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:10]]

        return facets

    def _generate_explanation(
        self,
        query: str,
        intent: SearchIntent,
        query_type: QueryType,
        analysis: Dict[str, Any]
    ) -> str:
        """生成搜索解释"""
        explanations = []

        explanations.append(f"搜索意图: {self._get_intent_description(intent)}")
        explanations.append(f"查询类型: {self._get_query_type_description(query_type)}")

        if analysis.get('entities'):
            entities_text = ', '.join([e['text'] for e in analysis['entities'][:3]])
            explanations.append(f"识别到的实体: {entities_text}")

        if analysis.get('keywords'):
            keywords_text = ', '.join(analysis['keywords'][:5])
            explanations.append(f"关键词: {keywords_text}")

        return ' | '.join(explanations)

    def _get_intent_description(self, intent: SearchIntent) -> str:
        """获取意图描述"""
        descriptions = {
            SearchIntent.INFORMATIONAL: '信息查询',
            SearchIntent.NAVIGATIONAL: '导航查询',
            SearchIntent.TRANSACTIONAL: '事务查询',
            SearchIntent.ENTITY: '实体查询',
            SearchIntent.RELATIONSHIP: '关系查询',
            SearchIntent.UNKNOWN: '未知意图',
        }
        return descriptions.get(intent, '未知')

    def _get_query_type_description(self, query_type: QueryType) -> str:
        """获取查询类型描述"""
        descriptions = {
            QueryType.KEYWORD: '关键词查询',
            QueryType.NATURAL_LANGUAGE: '自然语言查询',
            QueryType.STRUCTURED: '结构化查询',
            QueryType.HYBRID: '混合查询',
        }
        return descriptions.get(query_type, '未知')

    def _record_search(self, query: str, intent: SearchIntent, result_count: int):
        """记录搜索历史"""
        self.search_history.append({
            'query': query,
            'intent': intent.value,
            'result_count': result_count,
            'timestamp': datetime.now().isoformat(),
        })

        # 限制历史记录数量
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-1000:]

    def get_search_statistics(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        if not self.search_history:
            return {}

        total_searches = len(self.search_history)

        # 意图分布
        intent_count = {}
        for record in self.search_history:
            intent = record['intent']
            intent_count[intent] = intent_count.get(intent, 0) + 1

        # 平均结果数
        avg_results = sum(r['result_count'] for r in self.search_history) / total_searches

        return {
            'total_searches': total_searches,
            'intent_distribution': intent_count,
            'average_results': round(avg_results, 2),
            'recent_searches': self.search_history[-10:],
        }


# 全局智能搜索服务实例
intelligent_search_service = IntelligentSearchService()
