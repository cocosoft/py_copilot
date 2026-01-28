"""
全文索引器

负责构建和维护技能全文索引，支持中文分词、倒排索引和快速全文检索。
提供高效的全文搜索能力，替代现有的简单文本匹配。
"""

import os
import re
import json
import pickle
import threading
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path

from app.core.logging_config import logger
from app.schemas.skill_metadata import SkillMetadata


@dataclass
class SearchResult:
    """搜索结果"""
    skill_id: str
    score: float
    highlights: List[str] = None


@dataclass
class IndexStatistics:
    """索引统计信息"""
    total_documents: int = 0
    total_tokens: int = 0
    unique_tokens: int = 0
    average_document_length: float = 0.0
    index_size_bytes: int = 0
    last_updated: str = ""


class ChineseTokenizer:
    """中文分词器（简化实现，生产环境应使用jieba等专业库）"""
    
    def __init__(self):
        # 中文停用词
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她', '它', '我们', '你们', '他们', '这个', '那个'
        }
        
        # 中文标点符号
        self.punctuation = set('，。！？；：""‘’“”（）【】《》〈〉〔〕…—～·')
    
    def tokenize(self, text: str) -> List[str]:
        """中文分词（简化实现）"""
        if not text:
            return []
        
        # 转换为小写
        text = text.lower()
        
        # 移除标点符号
        for punc in self.punctuation:
            text = text.replace(punc, ' ')
        
        # 简单的空格和特殊字符分割
        tokens = re.findall(r'[\w\u4e00-\u9fff]+', text)
        
        # 过滤停用词和短词
        tokens = [
            token for token in tokens 
            if (len(token) > 1 or token.isalnum()) and token not in self.stop_words
        ]
        
        return tokens


class FullTextIndexer:
    """全文索引器"""
    
    def __init__(self, index_path: Optional[str] = None):
        """
        初始化全文索引器
        
        Args:
            index_path: 索引存储路径
        """
        self.index_path = index_path or "data/fulltext_index"
        self.tokenizer = ChineseTokenizer()
        self._lock = threading.RLock()
        
        # 索引数据结构
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)  # 词项 -> 技能ID集合
        self.document_store: Dict[str, Dict] = {}                    # 技能ID -> 文档信息
        self.document_lengths: Dict[str, int] = {}                  # 技能ID -> 文档长度
        self.statistics = IndexStatistics()
        
        # 加载现有索引
        self._load_index()
    
    def build_index(self, skills: List[SkillMetadata]) -> bool:
        """
        构建全文索引
        
        Args:
            skills: 技能元数据列表
            
        Returns:
            是否构建成功
        """
        with self._lock:
            try:
                logger.info(f"开始构建全文索引，共 {len(skills)} 个技能")
                
                # 清空现有索引
                self.inverted_index.clear()
                self.document_store.clear()
                self.document_lengths.clear()
                
                # 构建索引
                total_tokens = 0
                
                for skill in skills:
                    # 提取技能文本内容
                    text_content = self._extract_skill_text(skill)
                    
                    # 分词
                    tokens = self.tokenizer.tokenize(text_content)
                    
                    # 更新倒排索引
                    for token in tokens:
                        self.inverted_index[token].add(skill.skill_id)
                    
                    # 存储文档信息
                    self.document_store[skill.skill_id] = {
                        'name': skill.name,
                        'description': skill.description,
                        'category': skill.category,
                        'tags': skill.tags,
                        'content': text_content
                    }
                    
                    # 记录文档长度
                    self.document_lengths[skill.skill_id] = len(tokens)
                    total_tokens += len(tokens)
                
                # 更新统计信息
                self._update_statistics(len(skills), total_tokens)
                
                # 保存索引
                self._save_index()
                
                logger.info(f"全文索引构建完成，共索引 {len(skills)} 个文档，{len(self.inverted_index)} 个唯一词项")
                return True
                
            except Exception as e:
                logger.error(f"构建全文索引失败: {e}")
                return False
    
    def search(self, query: str, limit: int = 100) -> List[SearchResult]:
        """
        全文搜索
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            
        Returns:
            搜索结果列表
        """
        with self._lock:
            if not self.inverted_index:
                logger.warning("全文索引为空，请先构建索引")
                return []
            
            try:
                # 查询分词
                query_tokens = self.tokenizer.tokenize(query)
                
                if not query_tokens:
                    return []
                
                # 计算TF-IDF分数
                results = {}
                
                for token in query_tokens:
                    if token in self.inverted_index:
                        # 计算IDF（逆文档频率）
                        idf = self._calculate_idf(token)
                        
                        for skill_id in self.inverted_index[token]:
                            # 计算TF（词频）
                            tf = self._calculate_tf(token, skill_id)
                            
                            # TF-IDF分数
                            score = tf * idf
                            
                            if skill_id not in results:
                                results[skill_id] = 0
                            results[skill_id] += score
                
                # 转换为搜索结果并排序
                search_results = []
                for skill_id, score in results.items():
                    # 计算高亮片段
                    highlights = self._generate_highlights(skill_id, query_tokens)
                    
                    search_results.append(SearchResult(
                        skill_id=skill_id,
                        score=score,
                        highlights=highlights
                    ))
                
                # 按分数排序
                search_results.sort(key=lambda x: x.score, reverse=True)
                
                # 限制结果数量
                return search_results[:limit]
                
            except Exception as e:
                logger.error(f"全文搜索失败: {e}")
                return []
    
    def update_index(self, skill: SkillMetadata) -> bool:
        """
        更新索引（添加或更新单个技能）
        
        Args:
            skill: 技能元数据
            
        Returns:
            是否更新成功
        """
        with self._lock:
            try:
                skill_id = skill.skill_id
                
                # 如果技能已存在，先移除
                if skill_id in self.document_store:
                    self._remove_document(skill_id)
                
                # 提取技能文本内容
                text_content = self._extract_skill_text(skill)
                
                # 分词
                tokens = self.tokenizer.tokenize(text_content)
                
                # 更新倒排索引
                for token in tokens:
                    self.inverted_index[token].add(skill_id)
                
                # 更新文档存储
                self.document_store[skill_id] = {
                    'name': skill.name,
                    'description': skill.description,
                    'category': skill.category,
                    'tags': skill.tags,
                    'content': text_content
                }
                
                # 更新文档长度
                self.document_lengths[skill_id] = len(tokens)
                
                # 更新统计信息
                self._update_statistics(
                    len(self.document_store),
                    sum(self.document_lengths.values())
                )
                
                # 保存索引
                self._save_index()
                
                logger.info(f"索引更新成功: {skill.name}")
                return True
                
            except Exception as e:
                logger.error(f"更新索引失败 {skill.name}: {e}")
                return False
    
    def remove_from_index(self, skill_id: str) -> bool:
        """
        从索引中移除技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            是否移除成功
        """
        with self._lock:
            try:
                if skill_id not in self.document_store:
                    logger.warning(f"技能不存在于索引中: {skill_id}")
                    return False
                
                # 从索引中移除
                self._remove_document(skill_id)
                
                # 更新统计信息
                self._update_statistics(
                    len(self.document_store),
                    sum(self.document_lengths.values())
                )
                
                # 保存索引
                self._save_index()
                
                logger.info(f"从索引中移除技能: {skill_id}")
                return True
                
            except Exception as e:
                logger.error(f"从索引移除技能失败 {skill_id}: {e}")
                return False
    
    def optimize_index(self) -> bool:
        """优化索引（清理无用词项等）"""
        with self._lock:
            try:
                # 清理低频词项（出现次数少于2次）
                tokens_to_remove = []
                for token, skill_ids in self.inverted_index.items():
                    if len(skill_ids) < 2:
                        tokens_to_remove.append(token)
                
                for token in tokens_to_remove:
                    del self.inverted_index[token]
                
                logger.info(f"索引优化完成，清理了 {len(tokens_to_remove)} 个低频词项")
                
                # 保存优化后的索引
                self._save_index()
                
                return True
                
            except Exception as e:
                logger.error(f"优化索引失败: {e}")
                return False
    
    def get_statistics(self) -> IndexStatistics:
        """获取索引统计信息"""
        return self.statistics
    
    def _extract_skill_text(self, skill: SkillMetadata) -> str:
        """提取技能文本内容"""
        text_parts = []
        
        if skill.name:
            text_parts.append(skill.name)
        
        if skill.display_name:
            text_parts.append(skill.display_name)
        
        if skill.description:
            text_parts.append(skill.description)
        
        if skill.tags:
            text_parts.extend(skill.tags)
        
        if skill.content:
            # 只取内容的前1000个字符，避免内容过长
            text_parts.append(skill.content[:1000])
        
        return ' '.join(text_parts)
    
    def _calculate_tf(self, token: str, skill_id: str) -> float:
        """计算词频（TF）"""
        if skill_id not in self.document_store:
            return 0.0
        
        # 获取文档内容
        content = self.document_store[skill_id]['content']
        
        # 计算词频
        tokens = self.tokenizer.tokenize(content)
        token_count = tokens.count(token)
        
        # 标准化TF（避免长文档优势）
        return token_count / len(tokens) if tokens else 0.0
    
    def _calculate_idf(self, token: str) -> float:
        """计算逆文档频率（IDF）"""
        if token not in self.inverted_index:
            return 0.0
        
        # 包含该词项的文档数
        doc_count = len(self.inverted_index[token])
        
        # 总文档数
        total_docs = len(self.document_store)
        
        # IDF计算
        if doc_count == 0 or total_docs == 0:
            return 0.0
        
        return 1.0 + (total_docs / (1.0 + doc_count))
    
    def _generate_highlights(self, skill_id: str, query_tokens: List[str]) -> List[str]:
        """生成高亮片段"""
        if skill_id not in self.document_store:
            return []
        
        content = self.document_store[skill_id]['content']
        highlights = []
        
        # 简单的片段生成（生产环境应使用更复杂的算法）
        for token in query_tokens:
            if token in content.lower():
                # 查找包含查询词的片段
                start = max(0, content.lower().find(token) - 50)
                end = min(len(content), start + 100)
                
                snippet = content[start:end]
                if snippet not in highlights:
                    highlights.append(snippet)
                
                # 最多生成3个片段
                if len(highlights) >= 3:
                    break
        
        return highlights
    
    def _remove_document(self, skill_id: str):
        """从索引中移除文档"""
        # 从倒排索引中移除
        tokens_to_remove = []
        for token, skill_ids in self.inverted_index.items():
            if skill_id in skill_ids:
                skill_ids.remove(skill_id)
                if not skill_ids:
                    tokens_to_remove.append(token)
        
        # 清理空词项
        for token in tokens_to_remove:
            del self.inverted_index[token]
        
        # 从文档存储中移除
        if skill_id in self.document_store:
            del self.document_store[skill_id]
        
        # 从文档长度中移除
        if skill_id in self.document_lengths:
            del self.document_lengths[skill_id]
    
    def _update_statistics(self, total_documents: int, total_tokens: int):
        """更新统计信息"""
        self.statistics.total_documents = total_documents
        self.statistics.total_tokens = total_tokens
        self.statistics.unique_tokens = len(self.inverted_index)
        self.statistics.average_document_length = (
            total_tokens / total_documents if total_documents > 0 else 0.0
        )
        
        # 估算索引大小
        import sys
        self.statistics.index_size_bytes = (
            sys.getsizeof(self.inverted_index) +
            sys.getsizeof(self.document_store) +
            sys.getsizeof(self.document_lengths)
        )
        
        from datetime import datetime
        self.statistics.last_updated = datetime.now().isoformat()
    
    def _save_index(self):
        """保存索引到文件"""
        try:
            # 创建目录
            os.makedirs(self.index_path, exist_ok=True)
            
            # 保存索引数据
            index_data = {
                'inverted_index': dict(self.inverted_index),
                'document_store': self.document_store,
                'document_lengths': self.document_lengths,
                'statistics': self.statistics.__dict__
            }
            
            index_file = os.path.join(self.index_path, 'index.pkl')
            with open(index_file, 'wb') as f:
                pickle.dump(index_data, f)
            
            logger.debug("索引保存成功")
            
        except Exception as e:
            logger.error(f"保存索引失败: {e}")
    
    def _load_index(self):
        """从文件加载索引"""
        try:
            index_file = os.path.join(self.index_path, 'index.pkl')
            
            if not os.path.exists(index_file):
                logger.info("索引文件不存在，将创建新索引")
                return
            
            with open(index_file, 'rb') as f:
                index_data = pickle.load(f)
            
            # 加载索引数据
            self.inverted_index = defaultdict(set, index_data.get('inverted_index', {}))
            self.document_store = index_data.get('document_store', {})
            self.document_lengths = index_data.get('document_lengths', {})
            
            # 加载统计信息
            stats_dict = index_data.get('statistics', {})
            self.statistics = IndexStatistics(**stats_dict)
            
            logger.info(f"索引加载成功，共 {len(self.document_store)} 个文档")
            
        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            # 初始化空索引
            self.inverted_index = defaultdict(set)
            self.document_store = {}
            self.document_lengths = {}


def create_fulltext_indexer(index_path: Optional[str] = None) -> FullTextIndexer:
    """
    创建全文索引器实例
    
    Args:
        index_path: 索引存储路径
        
    Returns:
        全文索引器实例
    """
    return FullTextIndexer(index_path)


# 测试函数
def test_fulltext_indexer():
    """测试全文索引器功能"""
    indexer = FullTextIndexer()
    
    # 创建测试技能
    from app.schemas.skill_metadata import SkillMetadata, SkillCategory
    from datetime import datetime
    
    test_skills = [
        SkillMetadata(
            skill_id="test_skill_001",
            name="算法艺术生成",
            display_name="算法艺术生成工具",
            description="基于算法的艺术创作工具，支持生成各种艺术图案",
            category=SkillCategory.DESIGN.value,
            version="1.0.0",
            author="测试作者",
            tags=["艺术", "算法", "生成"],
            dependencies=[],
            enabled=True,
            file_path="/path/to/skill.md",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            config_schema=None,
            content="这是一个用于生成算法艺术的工具，支持多种算法和参数设置。",
            parameters_schema=None
        ),
        SkillMetadata(
            skill_id="test_skill_002", 
            name="数据分析工具",
            display_name="数据分析工具",
            description="强大的数据分析工具，支持统计分析和可视化",
            category=SkillCategory.DATA.value,
            version="1.0.0",
            author="测试作者",
            tags=["数据", "分析", "统计"],
            dependencies=[],
            enabled=True,
            file_path="/path/to/skill2.md",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            config_schema=None,
            content="这是一个用于数据分析和可视化的工具，支持多种数据格式。",
            parameters_schema=None
        )
    ]
    
    # 测试构建索引
    success = indexer.build_index(test_skills)
    print(f"索引构建结果: {success}")
    
    # 测试搜索
    results = indexer.search("算法艺术")
    print(f"搜索 '算法艺术' 结果: {len(results)} 个匹配")
    for result in results:
        print(f"  - {result.skill_id}: {result.score:.4f}")
    
    # 测试统计信息
    stats = indexer.get_statistics()
    print(f"索引统计: {stats}")


if __name__ == "__main__":
    test_fulltext_indexer()