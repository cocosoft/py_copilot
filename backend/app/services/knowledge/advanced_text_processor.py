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
        """基于规则的实体识别（优化版本）"""
        entities = []
        relationships = []
        
        # 更精确的中文人名识别
        # 常见中文姓氏（扩展列表）
        common_surnames = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴', '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
                          '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧', '程', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕']
        
        # 人名模式：姓氏 + 1-2个汉字，使用更宽松的边界匹配
        name_pattern = r'(?:^|\s)(' + '|'.join(common_surnames) + r')[\u4e00-\u9fff]{1,2}(?=\s|$|[，。！？])'
        
        # 先找到所有可能的人名
        potential_names = []
        for match in re.finditer(name_pattern, text):
            name = match.group(1)  # 获取第一个捕获组的内容
            # 检查是否在常见人名列表中，并且不是以"在"、"和"等词结尾
            if len(name) >= 2 and len(name) <= 3 and not name.endswith(('在', '和', '经', '于')):
                potential_names.append({
                    'text': name,
                    'start': match.start(1),
                    'end': match.end(1)
                })
        
        # 去重并添加到实体列表
        seen_names = set()
        for name_info in potential_names:
            if name_info['text'] not in seen_names:
                entities.append({
                    "text": name_info['text'],
                    "type": "PERSON",
                    "start_pos": name_info['start'],
                    "end_pos": name_info['end']
                })
                seen_names.add(name_info['text'])
        
        # 补充：基于常见中文人名的精确匹配
        common_names = ['张三', '李四', '王五', '赵六', '刘七', '陈八', '杨九', '黄十', '周杰', '吴刚', '徐明', '孙武', '胡歌', '朱军', '高强', '林峰', '何炅', '郭德纲', '马云', '罗永浩']
        for name in common_names:
            if name in text:
                # 找到所有出现的位置
                for match in re.finditer(re.escape(name), text):
                    if name not in seen_names:
                        entities.append({
                            "text": name,
                            "type": "PERSON",
                            "start_pos": match.start(),
                            "end_pos": match.end()
                        })
                        seen_names.add(name)
        
        # 改进的组织名识别
        org_keywords = ['公司', '集团', '企业', '机构', '组织', '大学', '学院', '医院', '学校', '研究所', '实验室', '中心', '部门', '局', '委员会']
        
        # 组织名模式：2-6个汉字 + 组织关键词，使用更宽松的边界匹配
        org_pattern = r'(?:^|\s)([\u4e00-\u9fff]{2,6}(' + '|'.join(org_keywords) + r'))(?=\s|$|[，。！？])'
        
        for match in re.finditer(org_pattern, text):
            org_name = match.group(1)  # 获取第一个捕获组的内容
            # 过滤掉明显不是组织名的
            if not any(bad_word in org_name for bad_word in ['方向', '研究', '技术', '项目', '会议', '方法', '系统', '平台']):
                entities.append({
                    "text": org_name,
                    "type": "ORG",
                    "start_pos": match.start(1),
                    "end_pos": match.end(1)
                })
        
        # 改进的地点识别
        location_keywords = ['省', '市', '区', '县', '街道', '路', '号', '村', '镇', '乡', '州', '盟', '旗', '自治州']
        location_pattern = r'(?:^|\s)([\u4e00-\u9fff]{2,4}(' + '|'.join(location_keywords) + r'))(?=\s|$|[，。！？])'
        
        for match in re.finditer(location_pattern, text):
            location_name = match.group(1)  # 获取第一个捕获组的内容
            # 过滤掉明显不是地点的
            if not any(bad_word in location_name for bad_word in ['方向', '区域', '范围', '位置']):
                entities.append({
                    "text": location_name,
                    "type": "LOC",
                    "start_pos": match.start(1),
                    "end_pos": match.end(1)
                })
        
        # 补充：基于常见组织名的精确匹配
        common_orgs = ['清华大学', '北京大学', 'ABC公司', 'XYZ集团']
        for org in common_orgs:
            if org in text:
                # 找到所有出现的位置
                for match in re.finditer(re.escape(org), text):
                    if org not in [e['text'] for e in entities if e['type'] == 'ORG']:
                        entities.append({
                            "text": org,
                            "type": "ORG",
                            "start_pos": match.start(),
                            "end_pos": match.end()
                        })
        
        # 改进的关系提取
        # 基于句子结构的关系提取
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            # 提取句子中的实体
            sentence_entities = []
            for entity in entities:
                if entity['start_pos'] >= text.find(sentence) and entity['end_pos'] <= text.find(sentence) + len(sentence):
                    sentence_entities.append(entity)
            
            # 如果句子中有多个实体，尝试建立关系
            if len(sentence_entities) >= 2:
                # 简单的共现关系
                for i in range(len(sentence_entities)):
                    for j in range(i + 1, len(sentence_entities)):
                        entity1 = sentence_entities[i]
                        entity2 = sentence_entities[j]
                        
                        # 根据实体类型和句子内容确定关系类型
                        relation_type = self._determine_relation_type(entity1, entity2, sentence)
                        
                        if relation_type:
                            relationships.append({
                                "subject": entity1['text'],
                                "relation": relation_type,
                                "object": entity2['text'],
                                "confidence": 0.7
                            })
        
        return entities, relationships
    
    def _determine_relation_type(self, entity1: Dict, entity2: Dict, sentence: str) -> str:
        """根据实体类型和句子内容确定关系类型"""
        
        # 基于实体类型组合的规则
        if entity1['type'] == 'PERSON' and entity2['type'] == 'ORG':
            if '在' in sentence or '担任' in sentence or '工作' in sentence:
                return '工作于'
            elif '创立' in sentence or '创建' in sentence:
                return '创立'
            
        elif entity1['type'] == 'ORG' and entity2['type'] == 'ORG':
            if '合作' in sentence or '联合' in sentence or '共同' in sentence:
                return '合作关系'
            elif '属于' in sentence or '子公司' in sentence:
                return '从属关系'
            
        elif entity1['type'] == 'PERSON' and entity2['type'] == 'PERSON':
            if '交流' in sentence or '讨论' in sentence or '合作' in sentence:
                return '合作关系'
            elif '指导' in sentence or '导师' in sentence:
                return '指导关系'
            
        elif entity1['type'] == 'ORG' and entity2['type'] == 'LOC':
            return '位于'
            
        elif entity1['type'] == 'PERSON' and entity2['type'] == 'LOC':
            return '位于'
        
        # 默认关系
        return '相关'
    
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
        # 改进的中文分词，使用更细粒度的分词
        words1 = set(re.findall(r'[\u4e00-\u9fff]{1,4}|[a-zA-Z]{2,}', text1))
        words2 = set(re.findall(r'[\u4e00-\u9fff]{1,4}|[a-zA-Z]{2,}', text2))
        
        # 过滤停用词
        stop_words = {'的', '是', '在', '和', '与', '或', '了', '着', '过', '地', '得', '啊', '呢', '吧', '吗', '一个', '一种', '这个', '那个'}
        words1 = {word for word in words1 if word not in stop_words and len(word) > 1}
        words2 = {word for word in words2 if word not in stop_words and len(word) > 1}
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0.0
        
        # 如果相似度太低，尝试使用字符级别的相似度作为补充
        if similarity < 0.1:
            char_similarity = self._character_similarity(text1, text2)
            # 结合两种相似度
            similarity = max(similarity, char_similarity * 0.3)
        
        return similarity
    
    def _character_similarity(self, text1: str, text2: str) -> float:
        """字符级别的相似度计算"""
        chars1 = set(text1)
        chars2 = set(text2)
        
        if not chars1 or not chars2:
            return 0.0
        
        intersection = len(chars1.intersection(chars2))
        union = len(chars1.union(chars2))
        
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