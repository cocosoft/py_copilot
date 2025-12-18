import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class AdvancedTextProcessor:
    """高级文本处理模块，提供智能分块、实体识别等功能"""
    
    def __init__(self):
        # 尝试导入spacy，如果不可用则使用基于规则的处理
        try:
            import spacy
            # 尝试加载spacy中文模型
            self.nlp = spacy.load("zh_core_web_sm")
            self.use_spacy = True
            logger.info("spacy中文模型加载成功，启用高级NLP功能")
        except (OSError, ImportError) as e:
            # 如果spacy模型不可用，使用基于规则的简单处理
            self.nlp = None
            self.use_spacy = False
            logger.warning(f"spacy中文模型未安装或加载失败: {e}，使用基于规则的处理")
    
    def clean_text(self, text: str) -> str:
        """清理文本，移除多余空格和特殊字符"""
        # 处理None值
        if text is None:
            return ""
        
        # 移除多余的空格和换行
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符，保留中文、英文、数字和基本标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}]', '', text)
        return text.strip()
    
    def semantic_chunking(self, text: str, max_chunk_size: int = 1000, 
                         min_chunk_size: int = 200, overlap: int = 100,
                         semantic_threshold: float = 0.7) -> List[str]:
        """智能语义分块，基于句子边界和语义单元
        
        Args:
            text: 输入文本
            max_chunk_size: 最大块大小
            min_chunk_size: 最小块大小
            overlap: 重叠窗口大小
            semantic_threshold: 语义相似度阈值
        
        Returns:
            分块后的文本列表
        """
        
        if self.use_spacy and self.nlp:
            # 使用spacy进行智能分块
            return self._spacy_semantic_chunking(text, max_chunk_size, min_chunk_size, overlap, semantic_threshold)
        else:
            # 使用基于规则的分块
            return self._rule_based_chunking(text, max_chunk_size, min_chunk_size, overlap)
    
    def _spacy_semantic_chunking(self, text: str, max_chunk_size: int, 
                                min_chunk_size: int, overlap: int = 100,
                                semantic_threshold: float = 0.7) -> List[str]:
        """使用spacy进行语义分块，包含语义相似度检测和重叠窗口优化"""
        doc = self.nlp(text)
        chunks = []
        current_chunk = ""
        current_size = 0
        
        # 获取所有句子
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        if not sentences:
            return []
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_size = len(sentence)
            
            # 如果当前块加上新句子不超过最大大小，则添加到当前块
            if current_size + sentence_size <= max_chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size += sentence_size
                i += 1
            else:
                # 检查是否需要语义分割
                if current_chunk and i < len(sentences):
                    # 计算当前块与下一句子的语义相似度
                    next_sentence = sentences[i]
                    similarity = self.calculate_similarity(current_chunk, next_sentence)
                    
                    # 如果相似度低于阈值，进行分割
                    if similarity < semantic_threshold and current_size >= min_chunk_size:
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
                        current_size = 0
                        # 不增加i，下一轮继续处理当前句子
                        continue
                
                # 如果当前块不为空且达到最小大小，则保存
                if current_chunk and current_size >= min_chunk_size:
                    chunks.append(current_chunk.strip())
                    
                    # 应用重叠窗口：保留最后一部分内容作为下一块的开始
                    if overlap > 0:
                        # 从当前块末尾提取重叠部分
                        overlap_text = self._extract_overlap_text(current_chunk, overlap)
                        current_chunk = overlap_text
                        current_size = len(overlap_text)
                    else:
                        current_chunk = ""
                        current_size = 0
                else:
                    # 如果当前块太小，强制添加下一句子
                    current_chunk += " " + sentence if current_chunk else sentence
                    current_size += sentence_size
                    i += 1
        
        # 添加最后一个块
        if current_chunk and current_size >= min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _rule_based_chunking(self, text: str, max_chunk_size: int, 
                           min_chunk_size: int, overlap: int = 100) -> List[str]:
        """基于规则的分块，包含重叠窗口优化"""
        # 按句子分割（中文和英文标点）
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        chunks = []
        current_chunk = ""
        current_size = 0
        
        if not sentences:
            return []
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_size = len(sentence)
            
            # 如果当前块加上新句子不超过最大大小，则添加到当前块
            if current_size + sentence_size <= max_chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size += sentence_size
                i += 1
            else:
                # 如果当前块不为空且达到最小大小，则保存
                if current_chunk and current_size >= min_chunk_size:
                    chunks.append(current_chunk.strip())
                    
                    # 应用重叠窗口：保留最后一部分内容作为下一块的开始
                    if overlap > 0:
                        overlap_text = self._extract_overlap_text(current_chunk, overlap)
                        current_chunk = overlap_text
                        current_size = len(overlap_text)
                    else:
                        current_chunk = ""
                        current_size = 0
                else:
                    # 如果当前块太小，强制添加下一句子
                    current_chunk += " " + sentence if current_chunk else sentence
                    current_size += sentence_size
                    i += 1
        
        # 添加最后一个块
        if current_chunk and current_size >= min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_entities_relationships(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """提取实体和关系"""
        
        if self.use_spacy and self.nlp:
            # 使用spacy进行实体识别
            return self._spacy_entity_extraction(text)
        else:
            # 使用基于规则的实体识别
            return self._rule_based_entity_extraction(text)
    
    def _spacy_entity_extraction(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """使用spacy提取实体和关系"""
        doc = self.nlp(text)
        entities = []
        relationships = []
        
        # 提取命名实体
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "type": ent.label_,
                "start_pos": ent.start_char,
                "end_pos": ent.end_char
            })
        
        # 提取依存关系（简化版本）
        for token in doc:
            if token.dep_ in ["nsubj", "dobj", "pobj"] and token.head.pos_ in ["NOUN", "PROPN"]:
                relationships.append({
                    "subject": token.head.text,
                    "relation": token.dep_,
                    "object": token.text,
                    "confidence": 0.7
                })
        
        return entities, relationships
    
    def _rule_based_entity_extraction(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """基于规则的实体识别"""
        entities = []
        relationships = []
        
        # 识别中文人名（2-4个汉字）
        name_pattern = r'[\u4e00-\u9fff]{2,4}'
        for match in re.finditer(name_pattern, text):
            # 简单的启发式规则：如果前后有特定称谓，可能是人名
            context_start = max(0, match.start() - 10)
            context_end = min(len(text), match.end() + 10)
            context = text[context_start:context_end]
            
            # 检查是否有称谓词
            honorifics = ['先生', '女士', '老师', '教授', '博士', '主任', '经理']
            if any(honorific in context for honorific in honorifics):
                entities.append({
                    "text": match.group(),
                    "type": "PERSON",
                    "start_pos": match.start(),
                    "end_pos": match.end()
                })
        
        # 识别组织名（包含"公司"、"集团"等关键词）
        org_pattern = r'[\u4e00-\u9fff]+(公司|集团|企业|机构|组织|大学|学院|医院)'
        for match in re.finditer(org_pattern, text):
            entities.append({
                "text": match.group(),
                "type": "ORG",
                "start_pos": match.start(),
                "end_pos": match.end()
            })
        
        # 识别地点（包含"省"、"市"、"区"等关键词）
        location_pattern = r'[\u4e00-\u9fff]+(省|市|区|县|街道|路|号)'
        for match in re.finditer(location_pattern, text):
            entities.append({
                "text": match.group(),
                "type": "LOC",
                "start_pos": match.start(),
                "end_pos": match.end()
            })
        
        # 简单的基于关键词的关系提取
        relation_keywords = ['是', '在', '位于', '属于', '包含', '包括']
        for keyword in relation_keywords:
            if keyword in text:
                # 简单的模式匹配
                pattern = f'([\u4e00-\u9fff]+){keyword}([\u4e00-\u9fff]+)'
                for match in re.finditer(pattern, text):
                    relationships.append({
                        "subject": match.group(1),
                        "relation": keyword,
                        "object": match.group(2),
                        "confidence": 0.5
                    })
        
        return entities, relationships
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """提取关键词"""
        
        if self.use_spacy and self.nlp:
            # 使用spacy提取关键词
            return self._spacy_keyword_extraction(text, top_n)
        else:
            # 使用基于词频的关键词提取
            return self._frequency_based_keyword_extraction(text, top_n)
    
    def _spacy_keyword_extraction(self, text: str, top_n: int) -> List[Dict[str, Any]]:
        """使用spacy提取关键词"""
        doc = self.nlp(text)
        
        # 提取名词和专有名词作为关键词候选
        keywords = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop:
                keywords.append(token.text)
        
        # 统计词频
        from collections import Counter
        keyword_freq = Counter(keywords)
        
        # 返回前top_n个关键词
        top_keywords = keyword_freq.most_common(top_n)
        return [{"word": word, "frequency": freq} for word, freq in top_keywords]
    
    def _frequency_based_keyword_extraction(self, text: str, top_n: int) -> List[Dict[str, Any]]:
        """基于词频的关键词提取"""
        # 简单的分词（按空格和标点分割）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        
        # 过滤停用词（简化版本）
        stop_words = {'的', '是', '在', '和', '与', '或', '了', '着', '过', '地', '得', '啊', '呢', '吧', '吗'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        from collections import Counter
        word_freq = Counter(filtered_words)
        
        # 返回前top_n个关键词
        top_keywords = word_freq.most_common(top_n)
        return [{"word": word, "frequency": freq} for word, freq in top_keywords]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        
        if self.use_spacy and self.nlp:
            # 使用spacy计算相似度
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)
            return doc1.similarity(doc2)
        else:
            # 使用基于Jaccard相似度的简单计算
            return self._jaccard_similarity(text1, text2)
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """基于Jaccard相似度的计算"""
        # 简单的分词
        words1 = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text1))
        words2 = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_overlap_text(self, text: str, overlap_size: int) -> str:
        """从文本末尾提取重叠部分
        
        Args:
            text: 输入文本
            overlap_size: 重叠窗口大小
            
        Returns:
            重叠部分的文本
        """
        if len(text) <= overlap_size:
            return text
        
        # 尝试按句子边界分割
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            # 如果没有句子边界，直接截取末尾overlap_size个字符
            return text[-overlap_size:]
        
        # 从后向前累加句子，直到达到重叠大小
        overlap_text = ""
        for i in range(len(sentences) - 1, -1, -1):
            sentence = sentences[i]
            if len(overlap_text) + len(sentence) <= overlap_size:
                overlap_text = sentence + " " + overlap_text if overlap_text else sentence
            else:
                break
        
        return overlap_text.strip()
    
    def adaptive_chunking(self, text: str, target_chunk_size: int = 800, 
                         min_chunk_size: int = 200, max_chunk_size: int = 1200,
                         semantic_threshold: float = 0.6) -> List[str]:
        """自适应分块，根据内容语义动态调整块大小
        
        Args:
            text: 输入文本
            target_chunk_size: 目标块大小
            min_chunk_size: 最小块大小
            max_chunk_size: 最大块大小
            semantic_threshold: 语义相似度阈值
            
        Returns:
            分块后的文本列表
        """
        
        if self.use_spacy and self.nlp:
            return self._adaptive_spacy_chunking(text, target_chunk_size, min_chunk_size, 
                                               max_chunk_size, semantic_threshold)
        else:
            return self._adaptive_rule_based_chunking(text, target_chunk_size, min_chunk_size, 
                                                    max_chunk_size)
    
    def _adaptive_spacy_chunking(self, text: str, target_chunk_size: int, min_chunk_size: int,
                                max_chunk_size: int, semantic_threshold: float) -> List[str]:
        """使用spacy的自适应分块"""
        doc = self.nlp(text)
        chunks = []
        current_chunk = ""
        current_size = 0
        
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        if not sentences:
            return []
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_size = len(sentence)
            
            # 动态调整块大小：根据语义连贯性调整
            if current_chunk and i < len(sentences):
                next_sentence = sentences[i]
                similarity = self.calculate_similarity(current_chunk, next_sentence)
                
                # 如果语义相似度高，允许更大的块
                if similarity > semantic_threshold + 0.2:
                    effective_max_size = max_chunk_size + 200
                # 如果语义相似度低，使用更小的块
                elif similarity < semantic_threshold - 0.2:
                    effective_max_size = min(max_chunk_size - 200, target_chunk_size)
                else:
                    effective_max_size = max_chunk_size
            else:
                effective_max_size = max_chunk_size
            
            # 如果当前块加上新句子不超过有效最大大小，则添加到当前块
            if current_size + sentence_size <= effective_max_size:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size += sentence_size
                i += 1
            else:
                # 如果当前块达到最小大小，则保存
                if current_chunk and current_size >= min_chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_size = 0
                else:
                    # 如果当前块太小，强制添加下一句子
                    current_chunk += " " + sentence if current_chunk else sentence
                    current_size += sentence_size
                    i += 1
        
        # 添加最后一个块
        if current_chunk and current_size >= min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _adaptive_rule_based_chunking(self, text: str, target_chunk_size: int, 
                                     min_chunk_size: int, max_chunk_size: int) -> List[str]:
        """基于规则的自适应分块"""
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        chunks = []
        current_chunk = ""
        current_size = 0
        
        if not sentences:
            return []
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_size = len(sentence)
            
            # 简单的自适应：根据当前块大小调整
            if current_size < target_chunk_size:
                effective_max_size = max_chunk_size
            else:
                effective_max_size = target_chunk_size
            
            if current_size + sentence_size <= effective_max_size:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size += sentence_size
                i += 1
            else:
                if current_chunk and current_size >= min_chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_size = 0
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
                    current_size += sentence_size
                    i += 1
        
        if current_chunk and current_size >= min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def analyze_chunk_quality(self, chunks: List[str]) -> Dict[str, Any]:
        """分析分块质量
        
        Args:
            chunks: 分块列表
            
        Returns:
            分块质量分析结果
        """
        if not chunks:
            return {"error": "没有分块数据"}
        
        chunk_sizes = [len(chunk) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunks)
        max_size = max(chunk_sizes)
        min_size = min(chunk_sizes)
        
        # 计算语义连贯性（相邻块的相似度）
        semantic_coherence = []
        for i in range(len(chunks) - 1):
            similarity = self.calculate_similarity(chunks[i], chunks[i + 1])
            semantic_coherence.append(similarity)
        
        avg_coherence = sum(semantic_coherence) / len(semantic_coherence) if semantic_coherence else 0
        
        return {
            "total_chunks": len(chunks),
            "average_chunk_size": round(avg_size, 2),
            "max_chunk_size": max_size,
            "min_chunk_size": min_size,
            "average_semantic_coherence": round(avg_coherence, 3),
            "chunk_size_distribution": {
                "small": len([s for s in chunk_sizes if s < 200]),
                "medium": len([s for s in chunk_sizes if 200 <= s <= 800]),
                "large": len([s for s in chunk_sizes if s > 800])
            }
        }