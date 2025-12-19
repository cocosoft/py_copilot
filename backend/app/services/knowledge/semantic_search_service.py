from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from datetime import datetime
from app.services.knowledge.chroma_service import ChromaService
from app.services.knowledge.retrieval_service import RetrievalService, AdvancedRetrievalService
from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

class SemanticSearchService:
    """语义搜索服务，提供增强的语义理解和搜索功能"""
    
    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.advanced_retrieval_service = AdvancedRetrievalService()
        self.chroma_service = ChromaService()
        self.knowledge_graph_service = KnowledgeGraphService()
        
        # 搜索优化参数
        self.semantic_boost_factors = {
            'entity_match': 1.5,      # 实体匹配提升
            'concept_similarity': 1.3, # 概念相似度提升
            'context_relevance': 1.2,  # 上下文相关性提升
            'recency_boost': 1.1      # 时效性提升
        }
        
        # 同义词词典
        self.synonyms = {
            '人工智能': ['AI', 'artificial intelligence', '智能技术'],
            '机器学习': ['ML', 'machine learning', '深度学习'],
            '自然语言处理': ['NLP', 'natural language processing', '文本分析'],
            '计算机视觉': ['CV', 'computer vision', '图像识别'],
            '数据分析': ['data analysis', '数据挖掘', '数据处理']
        }
    
    def semantic_search(self, query: str, n_results: int = 10, 
                       knowledge_base_id: Optional[int] = None,
                       use_entities: bool = True,
                       use_synonyms: bool = True,
                       boost_recent: bool = True,
                       semantic_boost: float = 0.3) -> List[Dict[str, Any]]:
        """语义搜索功能（带性能监控）"""
        import time
        
        start_time = time.time()
        search_stats = {
            'query': query,
            'n_results': n_results,
            'knowledge_base_id': knowledge_base_id,
            'use_entities': use_entities,
            'use_synonyms': use_synonyms,
            'boost_recent': boost_recent,
            'semantic_boost': semantic_boost
        }
        
        try:
            # 1. 查询预处理
            preprocessing_start = time.time()
            processed_query = self._preprocess_query(query, use_synonyms)
            preprocessing_time = time.time() - preprocessing_start
            
            # 2. 执行基础向量搜索
            vector_search_start = time.time()
            base_results = self.advanced_retrieval_service.advanced_search(
                query=processed_query,
                n_results=n_results * 2,  # 获取更多结果用于语义重排序
                knowledge_base_id=knowledge_base_id
            )
            vector_search_time = time.time() - vector_search_start
            
            # 3. 语义重排序
            reranking_start = time.time()
            if base_results and semantic_boost > 0:
                reordered_results = self._semantic_reranking(
                    base_results, query, processed_query, 
                    use_entities, boost_recent, semantic_boost
                )
                final_results = reordered_results[:n_results]
            else:
                final_results = base_results[:n_results]
            reranking_time = time.time() - reranking_start
            
            total_time = time.time() - start_time
            
            # 记录搜索统计信息
            search_stats.update({
                'preprocessing_time': round(preprocessing_time, 3),
                'vector_search_time': round(vector_search_time, 3),
                'reranking_time': round(reranking_time, 3),
                'total_time': round(total_time, 3),
                'base_results_count': len(base_results) if base_results else 0,
                'final_results_count': len(final_results),
                'success': True
            })
            
            logger.info(f"语义搜索完成 - 查询: '{query}', 耗时: {total_time:.3f}s, "
                       f"结果数: {len(final_results)}")
            
            # 添加搜索统计信息到结果中
            for result in final_results:
                result['search_stats'] = search_stats
            
            return final_results
            
        except Exception as e:
            total_time = time.time() - start_time
            search_stats.update({
                'total_time': round(total_time, 3),
                'success': False,
                'error': str(e)
            })
            
            logger.error(f"语义搜索失败 - 查询: '{query}', 耗时: {total_time:.3f}s, "
                        f"错误: {str(e)}")
            raise
    
    def _preprocess_query(self, query: str, use_synonyms: bool = True) -> str:
        """预处理查询，扩展同义词"""
        if not use_synonyms:
            return query
        
        expanded_query = query
        for term, synonyms in self.synonyms.items():
            if term in query:
                # 添加同义词到查询中
                synonyms_str = ' '.join(s for s in synonyms if s != term)
                expanded_query += ' ' + synonyms_str
        
        return expanded_query.strip()
    
    def _semantic_reranking(self, results: List[Dict[str, Any]], 
                          original_query: str, processed_query: str,
                          use_entities: bool, boost_recent: bool, 
                          semantic_boost: float) -> List[Dict[str, Any]]:
        """基于语义特征对搜索结果进行重排序"""
        
        enhanced_results = []
        
        for result in results:
            enhanced_score = result.get('score', 0.0)
            semantic_features = self._calculate_semantic_features(
                result, original_query, processed_query, use_entities, boost_recent
            )
            
            # 应用语义提升
            semantic_boost_value = sum(
                feature_score * self.semantic_boost_factors.get(feature_name, 1.0)
                for feature_name, feature_score in semantic_features.items()
            )
            
            enhanced_score = enhanced_score * (1 - semantic_boost) + semantic_boost_value * semantic_boost
            
            enhanced_results.append({
                **result,
                'score': enhanced_score,
                'semantic_features': semantic_features,
                'original_score': result.get('score', 0.0)
            })
        
        # 按增强后的分数排序
        enhanced_results.sort(key=lambda x: x['score'], reverse=True)
        return enhanced_results
    
    def _calculate_semantic_features(self, result: Dict[str, Any], 
                                   original_query: str, processed_query: str,
                                   use_entities: bool, boost_recent: bool) -> Dict[str, float]:
        """计算语义特征分数"""
        
        features = {}
        content = result.get('content', '')
        metadata = result.get('metadata', {})
        
        # 1. 实体匹配特征
        if use_entities:
            features['entity_match'] = self._calculate_entity_match_score(content, original_query)
        
        # 2. 概念相似度特征
        features['concept_similarity'] = self._calculate_concept_similarity(content, processed_query)
        
        # 3. 上下文相关性特征
        features['context_relevance'] = self._calculate_context_relevance(content, original_query)
        
        # 4. 时效性特征
        if boost_recent:
            features['recency_boost'] = self._calculate_recency_boost(metadata)
        
        return features
    
    def _calculate_entity_match_score(self, content: str, query: str) -> float:
        """计算实体匹配分数（优化版本）"""
        try:
            # 从查询中提取实体
            query_entities, _ = self.knowledge_graph_service.text_processor.extract_entities_relationships(query)
            
            # 从内容中提取实体
            content_entities, _ = self.knowledge_graph_service.text_processor.extract_entities_relationships(content)
            
            if not query_entities or not content_entities:
                return 0.0
            
            # 改进的实体匹配算法
            total_score = 0.0
            
            for q_entity in query_entities:
                best_match_score = 0.0
                
                for c_entity in content_entities:
                    # 1. 完全匹配（最高分）
                    if q_entity['text'] == c_entity['text']:
                        best_match_score = max(best_match_score, 1.0)
                        continue
                    
                    # 2. 类型匹配（中等分数）
                    if q_entity['type'] == c_entity['type']:
                        best_match_score = max(best_match_score, 0.7)
                        continue
                    
                    # 3. 部分匹配（基于字符串相似度）
                    if q_entity['text'] in c_entity['text'] or c_entity['text'] in q_entity['text']:
                        overlap_ratio = len(q_entity['text']) / max(len(c_entity['text']), 1)
                        best_match_score = max(best_match_score, 0.5 * overlap_ratio)
                
                total_score += best_match_score
            
            # 归一化分数
            return total_score / max(len(query_entities), 1)
            
        except Exception as e:
            logger.warning(f"实体匹配计算失败: {str(e)}")
            return 0.0
    
    def _calculate_concept_similarity(self, content: str, query: str) -> float:
        """计算概念相似度（优化版本）"""
        # 提取关键词（中文2个字符以上，英文3个字符以上）
        query_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', query.lower()))
        content_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', content.lower()))
        
        if not query_terms:
            return 0.0
        
        # 扩展查询词的同义词
        expanded_query_terms = self._expand_terms_with_synonyms(query_terms)
        
        # 计算扩展后的Jaccard相似度
        intersection = len(expanded_query_terms.intersection(content_terms))
        union = len(expanded_query_terms.union(content_terms))
        
        base_similarity = intersection / union if union > 0 else 0.0
        
        # 添加权重：查询词在内容中的出现频率和位置权重
        weighted_similarity = self._calculate_weighted_similarity(query_terms, content)
        
        # 综合评分：基础相似度 + 加权相似度
        final_score = 0.6 * base_similarity + 0.4 * weighted_similarity
        
        return min(final_score, 1.0)
    
    def _expand_terms_with_synonyms(self, terms: set) -> set:
        """扩展查询词的同义词"""
        expanded_terms = set(terms)
        
        for term in terms:
            # 检查同义词词典
            for key, synonyms in self.synonyms.items():
                if term == key or term in synonyms:
                    expanded_terms.update(synonyms)
                    expanded_terms.add(key)
        
        return expanded_terms
    
    def _calculate_weighted_similarity(self, query_terms: set, content: str) -> float:
        """计算加权相似度（考虑词频和位置）"""
        if not query_terms:
            return 0.0
        
        content_lower = content.lower()
        total_weight = 0.0
        
        for term in query_terms:
            # 计算词频
            term_count = content_lower.count(term)
            
            # 计算位置权重（标题和开头部分权重更高）
            position_weight = 1.0
            first_occurrence = content_lower.find(term)
            if first_occurrence >= 0:
                # 前20%的内容权重更高
                if first_occurrence < len(content) * 0.2:
                    position_weight = 1.5
                # 标题中的词权重最高
                elif first_occurrence < 100:  # 假设标题在开头100字符内
                    position_weight = 2.0
            
            term_weight = min(term_count * position_weight / 10, 1.0)  # 归一化
            total_weight += term_weight
        
        return total_weight / len(query_terms)
    
    def _calculate_context_relevance(self, content: str, query: str) -> float:
        """计算上下文相关性（优化版本）"""
        query_terms = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', query.lower())
        
        if not query_terms:
            return 0.0
        
        content_lower = content.lower()
        
        # 1. 计算查询词密度
        density_score = self._calculate_term_density(query_terms, content_lower)
        
        # 2. 计算查询词分布均匀性
        distribution_score = self._calculate_term_distribution(query_terms, content_lower)
        
        # 3. 计算查询词共现关系
        cooccurrence_score = self._calculate_cooccurrence_score(query_terms, content_lower)
        
        # 4. 计算语义连贯性
        coherence_score = self._calculate_semantic_coherence(query_terms, content_lower)
        
        # 综合评分
        final_score = (
            0.3 * density_score +
            0.25 * distribution_score +
            0.25 * cooccurrence_score +
            0.2 * coherence_score
        )
        
        return min(final_score, 1.0)
    
    def _calculate_term_density(self, query_terms: list, content_lower: str) -> float:
        """计算查询词密度"""
        total_matches = 0
        for term in query_terms:
            total_matches += content_lower.count(term)
        
        # 基于内容长度归一化
        content_length = len(content_lower)
        if content_length == 0:
            return 0.0
        
        density = total_matches / content_length * 1000  # 每千字符的匹配数
        return min(density / 10, 1.0)  # 归一化到0-1
    
    def _calculate_term_distribution(self, query_terms: list, content_lower: str) -> float:
        """计算查询词分布均匀性"""
        if len(query_terms) < 2:
            return 1.0  # 单个词分布总是均匀的
        
        content_length = len(content_lower)
        if content_length == 0:
            return 0.0
        
        # 计算每个词的位置分布
        positions = []
        for term in query_terms:
            term_positions = [m.start() for m in re.finditer(re.escape(term), content_lower)]
            if term_positions:
                positions.extend(term_positions)
        
        if len(positions) < 2:
            return 0.5  # 中等分数
        
        # 计算位置的标准差（越小表示分布越均匀）
        import statistics
        try:
            std_dev = statistics.stdev(positions)
            # 标准差越小，分布越均匀，分数越高
            distribution_score = 1.0 - min(std_dev / content_length, 1.0)
            return max(distribution_score, 0.0)
        except:
            return 0.5
    
    def _calculate_cooccurrence_score(self, query_terms: list, content_lower: str) -> float:
        """计算查询词共现关系"""
        if len(query_terms) < 2:
            return 1.0  # 单个词总是共现
        
        # 计算查询词在窗口内的共现次数
        window_size = 50  # 50字符窗口
        cooccurrence_count = 0
        total_windows = 0
        
        for i in range(0, len(content_lower) - window_size, window_size // 2):
            window = content_lower[i:i + window_size]
            terms_in_window = sum(1 for term in query_terms if term in window)
            
            if terms_in_window >= 2:  # 至少两个词在同一窗口
                cooccurrence_count += 1
            total_windows += 1
        
        if total_windows == 0:
            return 0.0
        
        return cooccurrence_count / total_windows
    
    def _calculate_semantic_coherence(self, query_terms: list, content_lower: str) -> float:
        """计算语义连贯性"""
        # 基于句子级别的语义连贯性
        sentences = re.split(r'[.!?。！？]+', content_lower)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # 计算包含查询词的句子比例
        relevant_sentences = 0
        for sentence in sentences:
            if any(term in sentence for term in query_terms):
                relevant_sentences += 1
        
        return relevant_sentences / len(sentences)
    
    def _calculate_recency_boost(self, metadata: Dict[str, Any]) -> float:
        """计算时效性提升分数"""
        # 基于文档创建时间的时效性评分
        if 'created_at' not in metadata:
            return 0.5  # 默认中等分数
        
        try:
            created_at = metadata['created_at']
            if isinstance(created_at, str):
                # 尝试解析日期字符串
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            # 计算与当前时间的差距（天数）
            days_diff = (datetime.now() - created_at).days
            
            # 时效性评分：越近的文档分数越高
            if days_diff <= 7:    # 一周内
                return 1.0
            elif days_diff <= 30:  # 一月内
                return 0.8
            elif days_diff <= 90:  # 三月内
                return 0.6
            elif days_diff <= 365: # 一年内
                return 0.4
            else:                  # 一年以上
                return 0.2
                
        except Exception:
            return 0.5
    
    def get_search_suggestions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取搜索建议"""
        suggestions = []
        
        # 1. 基于查询前缀的建议
        if len(query) >= 2:
            prefix_suggestions = self._get_prefix_suggestions(query, limit)
            for suggestion in prefix_suggestions:
                suggestions.append({
                    "suggestion": suggestion,
                    "score": 0.9,
                    "type": "expansion"
                })
        
        # 2. 基于语义相似性的建议
        semantic_suggestions = self._get_semantic_suggestions(query, limit)
        for suggestion in semantic_suggestions:
            suggestions.append({
                "suggestion": suggestion,
                "score": 0.8,
                "type": "semantic"
            })
        
        # 3. 同义词建议
        synonym_suggestions = self._get_synonym_suggestions(query)
        for suggestion in synonym_suggestions:
            suggestions.append({
                "suggestion": suggestion,
                "score": 0.95,
                "type": "synonym"
            })
        
        # 去重并限制数量
        unique_suggestions = []
        seen = set()
        for suggestion in suggestions:
            if suggestion["suggestion"] not in seen:
                seen.add(suggestion["suggestion"])
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:limit]
    
    def _get_prefix_suggestions(self, query: str, limit: int) -> List[str]:
        """基于前缀匹配的搜索建议"""
        try:
            # 获取所有文档标题作为候选建议
            all_documents = self.chroma_service.list_documents(limit=1000)
            
            suggestions = []
            query_lower = query.lower()
            
            for doc in all_documents:
                title = doc.get('metadata', {}).get('title', '')
                if title and title.lower().startswith(query_lower):
                    suggestions.append(title)
                    if len(suggestions) >= limit:
                        break
            
            return suggestions
            
        except Exception as e:
            logger.warning(f"前缀建议生成失败: {str(e)}")
            return []
    
    def _get_semantic_suggestions(self, query: str, limit: int) -> List[str]:
        """基于语义相似性的搜索建议"""
        try:
            # 使用向量搜索找到相似文档
            similar_docs = self.retrieval_service.search_documents(query, limit=limit * 2)
            
            suggestions = []
            for doc in similar_docs:
                title = doc.get('title', '')
                if title and title not in suggestions:
                    suggestions.append(title)
                    if len(suggestions) >= limit:
                        break
            
            return suggestions
            
        except Exception as e:
            logger.warning(f"语义建议生成失败: {str(e)}")
            return []

    def _get_synonym_suggestions(self, query: str) -> List[str]:
        """基于同义词的搜索建议"""
        suggestions = []
        
        # 检查同义词词典
        for key, synonyms in self.synonyms.items():
            if query == key:
                suggestions.extend(synonyms)
            elif query in synonyms:
                suggestions.append(key)
                suggestions.extend([s for s in synonyms if s != query])
        
        # 添加常见扩展
        if "技术" in query:
            suggestions.append(query.replace("技术", "技术发展"))
            suggestions.append(query.replace("技术", "技术应用"))
        
        if "算法" in query:
            suggestions.append(query.replace("算法", "算法设计"))
            suggestions.append(query.replace("算法", "算法优化"))
        
        return suggestions

    def analyze_search_patterns(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析搜索模式和效果"""
        analysis = {
            'query_complexity': self._analyze_query_complexity(query),
            'result_diversity': self._analyze_result_diversity(search_results),
            'relevance_distribution': self._analyze_relevance_distribution(search_results),
            'search_effectiveness': self._analyze_search_effectiveness(query, search_results)
        }
        
        return analysis
    
    def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """分析查询复杂度"""
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query)
        
        # 使用知识图谱服务的文本处理器提取实体
        entities, _ = self.knowledge_graph_service.text_processor.extract_entities_relationships(query)
        
        return {
            'word_count': len(words),
            'complexity_level': 'simple' if len(words) <= 2 else 'complex',
            'has_entities': len(entities) > 0
        }
    
    def _analyze_result_diversity(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析结果多样性"""
        if not results:
            return {'diversity_score': 0.0, 'diversity_level': 'low'}
        
        # 基于文档标题的多样性分析
        titles = [r.get('title', '') for r in results]
        unique_titles = set(titles)
        
        diversity_score = len(unique_titles) / len(results)
        
        return {
            'diversity_score': diversity_score,
            'diversity_level': 'high' if diversity_score > 0.7 else 'medium' if diversity_score > 0.4 else 'low'
        }
    
    def _analyze_relevance_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析相关性分布"""
        if not results:
            return {'average_relevance': 0.0, 'relevance_consistency': 'low'}
        
        scores = [r.get('score', 0.0) for r in results]
        avg_score = sum(scores) / len(scores)
        
        # 计算相关性一致性
        high_relevance_count = len([s for s in scores if s > 0.7])
        consistency = high_relevance_count / len(scores)
        
        return {
            'average_relevance': avg_score,
            'relevance_consistency': 'high' if consistency > 0.6 else 'medium' if consistency > 0.3 else 'low'
        }
    
    def _analyze_search_effectiveness(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析搜索效果"""
        effectiveness = {
            'result_count': len(results),
            'has_high_relevance_results': any(r.get('score', 0) > 0.7 for r in results),
            'query_coverage': self._calculate_query_coverage(query, results)
        }
        
        return effectiveness
    
    def _calculate_query_coverage(self, query: str, results: List[Dict[str, Any]]) -> float:
        """计算查询覆盖率"""
        if not results:
            return 0.0
        
        query_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', query.lower()))
        
        if not query_terms:
            return 0.0
        
        covered_terms = set()
        for result in results:
            content = result.get('content', '').lower()
            for term in query_terms:
                if term in content and term not in covered_terms:
                    covered_terms.add(term)
        
        return len(covered_terms) / len(query_terms)