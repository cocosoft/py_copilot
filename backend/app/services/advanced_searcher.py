"""
高级搜索器

负责提供高级搜索功能，包括布尔搜索、模糊搜索、短语搜索、字段限定搜索等。
支持复杂的搜索查询语法和智能查询解析。
"""

import re
import operator
from typing import List, Dict, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass
from enum import Enum
from functools import reduce

from app.core.logging_config import logger


class SearchOperator(Enum):
    """搜索操作符"""
    AND = "AND"      # 与操作
    OR = "OR"        # 或操作
    NOT = "NOT"      # 非操作
    NEAR = "NEAR"    # 邻近操作


class FieldType(Enum):
    """字段类型"""
    NAME = "name"              # 技能名称
    DESCRIPTION = "description" # 技能描述
    TAGS = "tags"              # 技能标签
    CATEGORY = "category"      # 技能分类
    AUTHOR = "author"          # 技能作者
    CONTENT = "content"        # 技能内容


@dataclass
class SearchToken:
    """搜索词元"""
    value: str
    field: Optional[FieldType] = None
    operator: SearchOperator = SearchOperator.AND
    is_phrase: bool = False
    is_fuzzy: bool = False
    proximity: int = 5  # 邻近搜索距离


@dataclass
class ParsedQuery:
    """解析后的查询"""
    tokens: List[SearchToken]
    original_query: str
    has_boolean_operators: bool = False
    has_field_restrictions: bool = False
    has_phrases: bool = False


@dataclass
class SearchResult:
    """搜索结果"""
    skill_id: str
    score: float
    match_details: Dict[str, Any]


class QueryParser:
    """查询解析器"""
    
    def __init__(self):
        # 字段映射
        self.field_mapping = {
            'name': FieldType.NAME,
            'desc': FieldType.DESCRIPTION,
            'description': FieldType.DESCRIPTION,
            'tag': FieldType.TAGS,
            'tags': FieldType.TAGS,
            'category': FieldType.CATEGORY,
            'author': FieldType.AUTHOR,
            'content': FieldType.CONTENT
        }
        
        # 操作符映射
        self.operator_mapping = {
            'AND': SearchOperator.AND,
            'OR': SearchOperator.OR,
            'NOT': SearchOperator.NOT,
            'NEAR': SearchOperator.NEAR
        }
    
    def parse_query(self, query: str) -> ParsedQuery:
        """
        解析搜索查询
        
        Args:
            query: 搜索查询字符串
            
        Returns:
            解析后的查询对象
        """
        try:
            tokens = []
            
            # 预处理查询
            normalized_query = self._normalize_query(query)
            
            # 解析短语（引号内的内容）
            phrase_tokens = self._extract_phrases(normalized_query)
            tokens.extend(phrase_tokens)
            
            # 移除已解析的短语
            query_without_phrases = self._remove_phrases(normalized_query)
            
            # 解析剩余部分
            remaining_tokens = self._parse_remaining(query_without_phrases)
            tokens.extend(remaining_tokens)
            
            # 分析查询特征
            has_boolean = any(token.operator != SearchOperator.AND for token in tokens)
            has_fields = any(token.field is not None for token in tokens)
            has_phrases = any(token.is_phrase for token in tokens)
            
            return ParsedQuery(
                tokens=tokens,
                original_query=query,
                has_boolean_operators=has_boolean,
                has_field_restrictions=has_fields,
                has_phrases=has_phrases
            )
            
        except Exception as e:
            logger.error(f"解析查询失败: {e}")
            # 返回基本的查询解析
            return ParsedQuery(
                tokens=[SearchToken(value=query)],
                original_query=query
            )
    
    def _normalize_query(self, query: str) -> str:
        """标准化查询"""
        # 移除多余空格
        query = re.sub(r'\s+', ' ', query.strip())
        
        # 标准化操作符（大写）
        for op in self.operator_mapping:
            query = re.sub(rf'\b{op}\b', op, query, flags=re.IGNORECASE)
        
        return query
    
    def _extract_phrases(self, query: str) -> List[SearchToken]:
        """提取短语（引号内的内容）"""
        tokens = []
        
        # 查找引号内的内容
        phrase_pattern = r'"([^"]+)"'
        phrases = re.findall(phrase_pattern, query)
        
        for phrase in phrases:
            # 检查是否有字段限定
            field, phrase_content = self._extract_field_restriction(phrase)
            
            token = SearchToken(
                value=phrase_content,
                field=field,
                is_phrase=True
            )
            tokens.append(token)
        
        return tokens
    
    def _remove_phrases(self, query: str) -> str:
        """移除已解析的短语"""
        return re.sub(r'"[^"]+"', '', query).strip()
    
    def _parse_remaining(self, query: str) -> List[SearchToken]:
        """解析剩余部分"""
        if not query:
            return []
        
        tokens = []
        parts = query.split()
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # 检查是否为操作符
            if part.upper() in self.operator_mapping:
                operator = self.operator_mapping[part.upper()]
                
                # 获取下一个词作为操作数
                if i + 1 < len(parts):
                    next_part = parts[i + 1]
                    
                    # 检查是否有字段限定
                    field, value = self._extract_field_restriction(next_part)
                    
                    token = SearchToken(
                        value=value,
                        field=field,
                        operator=operator
                    )
                    tokens.append(token)
                    i += 2
                else:
                    # 操作符在末尾，忽略
                    i += 1
            
            # 检查是否为字段限定词
            elif ':' in part and not part.startswith(':'):
                field, value = self._extract_field_restriction(part)
                
                token = SearchToken(
                    value=value,
                    field=field
                )
                tokens.append(token)
                i += 1
            
            # 普通词
            else:
                # 检查模糊搜索（以~结尾）
                is_fuzzy = part.endswith('~')
                value = part.rstrip('~') if is_fuzzy else part
                
                token = SearchToken(
                    value=value,
                    is_fuzzy=is_fuzzy
                )
                tokens.append(token)
                i += 1
        
        return tokens
    
    def _extract_field_restriction(self, text: str) -> Tuple[Optional[FieldType], str]:
        """提取字段限定"""
        if ':' in text:
            parts = text.split(':', 1)
            field_name = parts[0].lower()
            value = parts[1]
            
            if field_name in self.field_mapping:
                return self.field_mapping[field_name], value
        
        return None, text


class AdvancedSearcher:
    """高级搜索器"""
    
    def __init__(self, fulltext_indexer=None, skill_registry=None):
        """
        初始化高级搜索器
        
        Args:
            fulltext_indexer: 全文索引器实例
            skill_registry: 技能注册器实例
        """
        self.query_parser = QueryParser()
        self.fulltext_indexer = fulltext_indexer
        self.skill_registry = skill_registry
    
    def search(
        self, 
        query: str, 
        filters: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[SearchResult]:
        """
        执行高级搜索
        
        Args:
            query: 搜索查询
            filters: 过滤条件
            limit: 返回结果数量限制
            
        Returns:
            搜索结果列表
        """
        try:
            # 解析查询
            parsed_query = self.query_parser.parse_query(query)
            
            logger.debug(f"解析后的查询: {parsed_query}")
            
            # 执行搜索
            if self.fulltext_indexer:
                # 使用全文索引器进行搜索
                results = self._search_with_fulltext(parsed_query, limit)
            else:
                # 回退到简单搜索
                results = self._simple_search(parsed_query, limit)
            
            # 应用过滤
            if filters:
                results = self._apply_filters(results, filters)
            
            # 排序结果
            results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"高级搜索完成，查询: '{query}'，找到 {len(results)} 个结果")
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"高级搜索失败: {e}")
            return []
    
    def _search_with_fulltext(self, parsed_query: ParsedQuery, limit: int) -> List[SearchResult]:
        """使用全文索引器进行搜索"""
        # 处理布尔查询
        if parsed_query.has_boolean_operators:
            return self._handle_boolean_query(parsed_query, limit)
        
        # 处理字段限定查询
        elif parsed_query.has_field_restrictions:
            return self._handle_field_restricted_query(parsed_query, limit)
        
        # 简单查询
        else:
            return self._handle_simple_query(parsed_query, limit)
    
    def _handle_boolean_query(self, parsed_query: ParsedQuery, limit: int) -> List[SearchResult]:
        """处理布尔查询"""
        # 分组词元（按操作符）
        and_tokens = []
        or_tokens = []
        not_tokens = []
        
        for token in parsed_query.tokens:
            if token.operator == SearchOperator.AND:
                and_tokens.append(token)
            elif token.operator == SearchOperator.OR:
                or_tokens.append(token)
            elif token.operator == SearchOperator.NOT:
                not_tokens.append(token)
        
        # 执行AND搜索
        and_results = set()
        if and_tokens:
            for token in and_tokens:
                token_results = self._search_token(token, limit * 10)  # 扩大限制以进行交集
                if and_results:
                    and_results = and_results.intersection(
                        {r.skill_id for r in token_results}
                    )
                else:
                    and_results = {r.skill_id for r in token_results}
        
        # 执行OR搜索
        or_results = set()
        for token in or_tokens:
            token_results = self._search_token(token, limit)
            or_results.update({r.skill_id for r in token_results})
        
        # 合并结果
        if and_results and or_results:
            final_ids = and_results.union(or_results)
        elif and_results:
            final_ids = and_results
        elif or_results:
            final_ids = or_results
        else:
            final_ids = set()
        
        # 排除NOT结果
        not_ids = set()
        for token in not_tokens:
            token_results = self._search_token(token, limit)
            not_ids.update({r.skill_id for r in token_results})
        
        final_ids = final_ids - not_ids
        
        # 获取完整结果
        return self._get_results_by_ids(list(final_ids), limit)
    
    def _handle_field_restricted_query(self, parsed_query: ParsedQuery, limit: int) -> List[SearchResult]:
        """处理字段限定查询"""
        results = []
        
        for token in parsed_query.tokens:
            if token.field:
                # 字段限定搜索
                field_results = self._search_field(token, limit)
                results.extend(field_results)
            else:
                # 普通搜索
                token_results = self._search_token(token, limit)
                results.extend(token_results)
        
        # 去重并排序
        unique_results = {}
        for result in results:
            if result.skill_id not in unique_results or result.score > unique_results[result.skill_id].score:
                unique_results[result.skill_id] = result
        
        return sorted(unique_results.values(), key=lambda x: x.score, reverse=True)[:limit]
    
    def _handle_simple_query(self, parsed_query: ParsedQuery, limit: int) -> List[SearchResult]:
        """处理简单查询"""
        results = []
        
        for token in parsed_query.tokens:
            token_results = self._search_token(token, limit)
            results.extend(token_results)
        
        # 合并结果（取最高分）
        unique_results = {}
        for result in results:
            if result.skill_id not in unique_results or result.score > unique_results[result.skill_id].score:
                unique_results[result.skill_id] = result
        
        return sorted(unique_results.values(), key=lambda x: x.score, reverse=True)[:limit]
    
    def _search_token(self, token: SearchToken, limit: int) -> List[SearchResult]:
        """搜索单个词元"""
        if not self.fulltext_indexer:
            return []
        
        # 构建搜索查询
        search_query = token.value
        
        # 处理短语搜索
        if token.is_phrase:
            search_query = f'"{token.value}"'
        
        # 处理模糊搜索
        elif token.is_fuzzy:
            search_query = f'{token.value}~'
        
        # 执行搜索
        raw_results = self.fulltext_indexer.search(search_query, limit * 2)  # 扩大限制
        
        # 转换为标准格式
        results = []
        for raw_result in raw_results:
            result = SearchResult(
                skill_id=raw_result.skill_id,
                score=raw_result.score,
                match_details={
                    'token': token.value,
                    'highlights': raw_result.highlights
                }
            )
            results.append(result)
        
        return results
    
    def _search_field(self, token: SearchToken, limit: int) -> List[SearchResult]:
        """字段限定搜索"""
        if not self.skill_registry:
            return []
        
        # 获取所有技能
        all_skills, _ = self.skill_registry.list_skills()
        
        results = []
        for skill in all_skills:
            # 获取对应字段的值
            field_value = self._get_field_value(skill, token.field)
            
            if field_value and self._matches_field(field_value, token.value, token.is_fuzzy):
                # 计算匹配分数
                score = self._calculate_field_match_score(field_value, token.value)
                
                result = SearchResult(
                    skill_id=skill.skill_id,
                    score=score,
                    match_details={
                        'field': token.field.value,
                        'value': token.value,
                        'matched_value': field_value
                    }
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.score, reverse=True)[:limit]
    
    def _get_field_value(self, skill, field_type: FieldType) -> Optional[str]:
        """获取技能字段值"""
        if field_type == FieldType.NAME:
            return skill.name
        elif field_type == FieldType.DESCRIPTION:
            return skill.description
        elif field_type == FieldType.TAGS:
            return ' '.join(skill.tags) if skill.tags else None
        elif field_type == FieldType.CATEGORY:
            return skill.category
        elif field_type == FieldType.AUTHOR:
            return skill.author
        elif field_type == FieldType.CONTENT:
            return skill.content
        
        return None
    
    def _matches_field(self, field_value: str, search_value: str, is_fuzzy: bool) -> bool:
        """检查字段值是否匹配"""
        if not field_value:
            return False
        
        field_value_lower = field_value.lower()
        search_value_lower = search_value.lower()
        
        if is_fuzzy:
            # 模糊匹配（包含关系）
            return search_value_lower in field_value_lower
        else:
            # 精确匹配（词边界）
            return re.search(rf'\b{re.escape(search_value_lower)}\b', field_value_lower) is not None
    
    def _calculate_field_match_score(self, field_value: str, search_value: str) -> float:
        """计算字段匹配分数"""
        # 简单的基于字符串相似度的分数
        field_lower = field_value.lower()
        search_lower = search_value.lower()
        
        if search_lower in field_lower:
            # 计算匹配位置和长度比例
            position = field_lower.find(search_lower)
            length_ratio = len(search_lower) / len(field_lower)
            
            # 位置越靠前，分数越高
            position_score = 1.0 - (position / max(len(field_lower), 1))
            
            return (position_score + length_ratio) / 2.0
        
        return 0.0
    
    def _get_results_by_ids(self, skill_ids: List[str], limit: int) -> List[SearchResult]:
        """根据技能ID获取结果"""
        results = []
        
        for skill_id in skill_ids[:limit]:
            # 这里简化处理，实际应该根据匹配程度计算分数
            result = SearchResult(
                skill_id=skill_id,
                score=1.0,  # 简化分数
                match_details={'type': 'boolean_query'}
            )
            results.append(result)
        
        return results
    
    def _apply_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """应用过滤条件"""
        if not self.skill_registry:
            return results
        
        filtered_results = []
        
        for result in results:
            skill = self.skill_registry.get_skill(result.skill_id)
            if skill and self._matches_filters(skill, filters):
                filtered_results.append(result)
        
        return filtered_results
    
    def _matches_filters(self, skill, filters: Dict[str, Any]) -> bool:
        """检查技能是否匹配过滤条件"""
        for field, value in filters.items():
            if field == 'category' and skill.category != value:
                return False
            elif field == 'enabled' and skill.enabled != value:
                return False
            elif field == 'tags' and value not in (skill.tags or []):
                return False
            elif field == 'author' and skill.author != value:
                return False
        
        return True
    
    def _simple_search(self, parsed_query: ParsedQuery, limit: int) -> List[SearchResult]:
        """简单搜索（回退方案）"""
        # 组合所有词元的值
        search_terms = [token.value for token in parsed_query.tokens]
        search_query = ' '.join(search_terms)
        
        if not self.fulltext_indexer:
            return []
        
        raw_results = self.fulltext_indexer.search(search_query, limit)
        
        results = []
        for raw_result in raw_results:
            result = SearchResult(
                skill_id=raw_result.skill_id,
                score=raw_result.score,
                match_details={'highlights': raw_result.highlights}
            )
            results.append(result)
        
        return results


def create_advanced_searcher(fulltext_indexer=None, skill_registry=None) -> AdvancedSearcher:
    """
    创建高级搜索器实例
    
    Args:
        fulltext_indexer: 全文索引器实例
        skill_registry: 技能注册器实例
        
    Returns:
        高级搜索器实例
    """
    return AdvancedSearcher(fulltext_indexer, skill_registry)


# 测试函数
def test_advanced_searcher():
    """测试高级搜索器功能"""
    # 创建测试组件
    from app.services.fulltext_indexer import FullTextIndexer
    from app.schemas.skill_metadata import SkillMetadata, SkillCategory
    from datetime import datetime
    
    # 创建测试技能
    test_skills = [
        SkillMetadata(
            skill_id='skill_001',
            name='算法艺术生成',
            description='基于算法的艺术创作工具',
            category=SkillCategory.DESIGN.value,
            tags=['艺术', '算法', '生成'],
            author='作者A',
            content='这是一个用于生成算法艺术的工具。',
            # 其他字段省略...
        ),
        SkillMetadata(
            skill_id='skill_002',
            name='数据分析工具', 
            description='强大的数据分析工具',
            category=SkillCategory.DATA.value,
            tags=['数据', '分析', '统计'],
            author='作者B',
            content='这是一个用于数据分析和可视化的工具。',
            # 其他字段省略...
        )
    ]
    
    # 创建全文索引器
    indexer = FullTextIndexer()
    indexer.build_index(test_skills)
    
    # 创建模拟技能注册器
    class MockSkillRegistry:
        def list_skills(self):
            return test_skills, len(test_skills)
        
        def get_skill(self, skill_id):
            for skill in test_skills:
                if skill.skill_id == skill_id:
                    return skill
            return None
    
    # 创建高级搜索器
    searcher = AdvancedSearcher(indexer, MockSkillRegistry())
    
    # 测试各种搜索查询
    test_queries = [
        '算法艺术',                          # 简单搜索
        'name:算法艺术',                     # 字段限定搜索
        '算法 AND 艺术',                     # 布尔搜索
        '算法 OR 数据',                      # 或搜索
        '算法 NOT 数据',                     # 非搜索
        '"算法艺术"',                       # 短语搜索
        '算法~',                            # 模糊搜索
        'category:design',                  # 分类搜索
        'author:作者A',                     # 作者搜索
    ]
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        results = searcher.search(query, limit=5)
        
        if results:
            for i, result in enumerate(results):
                print(f"  {i+1}. {result.skill_id}: {result.score:.4f}")
        else:
            print("  没有找到结果")


if __name__ == "__main__":
    test_advanced_searcher()