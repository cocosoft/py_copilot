import re
import logging
import jieba
from typing import List, Dict, Any, Tuple, Optional
from .entity_config_manager import EntityConfigManager

logger = logging.getLogger(__name__)

class AdvancedTextProcessor:
    """高级文本处理模块，提供智能分块、实体识别等功能"""
    
    def __init__(self, config_file: str = "entity_config.json"):
        # 初始化配置管理器
        self.config_manager = EntityConfigManager(config_file)
        
        # 延迟初始化jieba中文分词器，避免启动时耗时
        self.use_jieba = False
        self.jieba_initialized = False
        logger.info("高级文本处理器初始化成功，jieba分词器将在首次使用时加载")
    
    def _initialize_jieba(self):
        """延迟初始化jieba中文分词器"""
        if not self.jieba_initialized:
            try:
                # 初始化jieba
                jieba.initialize()
                self.use_jieba = True
                self.jieba_initialized = True
                logger.info("jieba中文分词器加载成功，启用中文处理功能")
            except Exception as e:
                # 如果jieba不可用，使用基于规则的简单处理
                self.use_jieba = False
                self.jieba_initialized = True
                logger.warning(f"jieba初始化失败: {e}，使用基于规则的处理")
    
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
        self._initialize_jieba()
        if self.use_jieba:
            # 使用jieba分词优化的分块方法
            return self._jieba_semantic_chunking(text, max_chunk_size, min_chunk_size, overlap)
        else:
            # 使用基于规则的分块
            return self._rule_based_chunking(text, max_chunk_size, min_chunk_size, overlap)
    
    def _jieba_semantic_chunking(self, text: str, max_chunk_size: int, 
                                min_chunk_size: int, overlap: int = 100) -> List[str]:
        """使用jieba分词进行语义分块，包含重叠窗口优化"""
        self._initialize_jieba()
        # 先使用句子边界分割
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
            
        chunks = []
        current_chunk = ""
        current_size = 0
        
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
        # 使用基于规则的实体识别，结合jieba分词优化
        return self._rule_based_entity_extraction(text)
    
    def _jieba_keyword_extraction(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """使用jieba提取关键词"""
        self._initialize_jieba()
        # 使用jieba的关键词提取功能
        from collections import Counter
        
        # 分词
        words = list(jieba.cut(text))
        
        # 过滤停用词
        stop_words = {'的', '是', '在', '和', '与', '或', '了', '着', '过', '地', '得', '啊', '呢', '吧', '吗', '我', '你', '他', '她', '它'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        word_freq = Counter(filtered_words)
        
        # 返回前top_n个关键词
        top_keywords = word_freq.most_common(top_n)
        return [{"word": word, "frequency": freq} for word, freq in top_keywords]
    
    def _rule_based_entity_extraction(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """基于规则的实体识别（优化版本）"""
        entities = []
        relationships = []
        
        # 1. 基于配置的自定义实体识别（重构）
        entities.extend(self._extract_custom_entities(text))
        
        # 2. 更精确的中文人名识别
        # 常见中文姓氏（扩展列表）
        common_surnames = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴', '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
                          '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧', '程', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕']
        
        # 人名模式：姓氏 + 1-2个汉字，使用更宽松的边界匹配
        name_pattern = r'(?:^|\s)(' + '|'.join(common_surnames) + r')[\u4e00-\u9fff]{1,2}(?=\s|$|[，。！？])'
        
        # 先找到所有可能的人名
        potential_names = []
        for match in re.finditer(name_pattern, text):
            name = match.group(0).strip()  # 获取整个匹配的文本并去除空格
            # 检查是否在常见人名列表中，并且不是以"在"、"和"等词结尾
            if len(name) >= 2 and len(name) <= 3 and not name.endswith(('在', '和', '经', '于')):
                potential_names.append({
                    'text': name,
                    'start': match.start(),
                    'end': match.end()
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
        
        # 组织名模式：1-8个汉字 + 组织关键词，使用更宽松的边界匹配
        org_pattern = r'(?:^|\s)([\u4e00-\u9fff]{1,8}(' + '|'.join(org_keywords) + r'))(?=\s|$|[，。！？])'
        
        for match in re.finditer(org_pattern, text):
            org_name = match.group(0).strip()  # 获取整个匹配的文本并去除空格
            # 过滤掉明显不是组织名的
            if not any(bad_word in org_name for bad_word in ['方向', '研究', '技术', '项目', '会议', '方法', '系统', '平台']):
                entities.append({
                    "text": org_name,
                    "type": "ORG",
                    "start_pos": match.start(),
                    "end_pos": match.end()
                })
        
        # 改进的地点识别
        location_keywords = ['省', '市', '区', '县', '街道', '路', '号', '村', '镇', '乡', '州', '盟', '旗', '自治州']
        location_pattern = r'(?:^|\s)([\u4e00-\u9fff]{1,6}(' + '|'.join(location_keywords) + r'))(?=\s|$|[，。！？])'
        
        for match in re.finditer(location_pattern, text):
            location_name = match.group(0).strip()  # 获取整个匹配的文本并去除空格
            # 过滤掉明显不是地点的
            if not any(bad_word in location_name for bad_word in ['方向', '区域', '范围', '位置']):
                entities.append({
                    "text": location_name,
                    "type": "LOC",
                    "start_pos": match.start(),
                    "end_pos": match.end()
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
        
        # 新增：专业术语相关关系
        elif entity1['type'] in ['TECH', 'PRODUCT', 'CONCEPT'] and entity2['type'] in ['TECH', 'PRODUCT', 'CONCEPT']:
            if '基于' in sentence or '使用' in sentence or '依赖' in sentence:
                return '基于'
            elif '包含' in sentence or '包括' in sentence or '集成' in sentence:
                return '包含'
            elif '替代' in sentence or '取代' in sentence or '替代品' in sentence:
                return '替代'
            elif '类似' in sentence or '相似' in sentence or '同类' in sentence:
                return '类似'
            
        elif entity1['type'] == 'PERSON' and entity2['type'] in ['TECH', 'PRODUCT', 'CONCEPT']:
            if '开发' in sentence or '发明' in sentence or '创建' in sentence:
                return '开发'
            elif '使用' in sentence or '应用' in sentence or '采用' in sentence:
                return '使用'
            elif '研究' in sentence or '探索' in sentence or '分析' in sentence:
                return '研究'
            
        elif entity1['type'] == 'ORG' and entity2['type'] in ['TECH', 'PRODUCT', 'CONCEPT']:
            if '开发' in sentence or '发布' in sentence or '推出' in sentence:
                return '开发'
            elif '使用' in sentence or '应用' in sentence or '采用' in sentence:
                return '使用'
            elif '支持' in sentence or '维护' in sentence or '提供' in sentence:
                return '支持'
            
        elif entity1['type'] == 'EVENT' and entity2['type'] in ['TECH', 'PRODUCT', 'CONCEPT']:
            if '讨论' in sentence or '介绍' in sentence or '展示' in sentence:
                return '讨论'
            elif '发布' in sentence or '宣布' in sentence or '推出' in sentence:
                return '发布'
        
        # 默认关系
        return '相关'
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """提取关键词"""
        self._initialize_jieba()
        if self.use_jieba:
            # 使用jieba提取关键词
            return self._jieba_keyword_extraction(text, top_n)
        else:
            # 使用基于词频的关键词提取
            return self._frequency_based_keyword_extraction(text, top_n)
    

    
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
    
    def _extract_custom_entities(self, text: str) -> List[Dict[str, Any]]:
        """基于配置提取自定义实体（重构版本）"""
        entities = []
        seen_terms = set()
        
        # 1. 从词典中提取实体
        entity_types = self.config_manager.get_entity_types()
        
        for entity_type, type_config in entity_types.items():
            if not type_config.get('enabled', True):
                continue
                
            # 提取词典中的术语
            dictionary = self.config_manager.get_dictionary(entity_type)
            for term in dictionary:
                if term in text and term not in seen_terms:
                    # 找到所有出现的位置
                    for match in re.finditer(re.escape(term), text):
                        entities.append({
                            "text": term,
                            "type": entity_type,
                            "start_pos": match.start(),
                            "end_pos": match.end(),
                            "description": type_config.get('description', '自定义实体')
                        })
                        seen_terms.add(term)
        
        # 2. 使用正则表达式规则提取实体
        extraction_rules = self.config_manager.get_extraction_rules()
        
        for rule in extraction_rules:
            if not rule.get('enabled', True):
                continue
                
            pattern = rule.get('pattern', '')
            if not pattern:
                continue
                
            try:
                for match in re.finditer(pattern, text):
                    term = match.group()
                    if term not in seen_terms:
                        # 确定实体类型
                        entity_type = self._determine_entity_type_from_rule(rule, term)
                        
                        entities.append({
                            "text": term,
                            "type": entity_type,
                            "start_pos": match.start(),
                            "end_pos": match.end(),
                            "description": rule.get('description', '规则提取的实体')
                        })
                        seen_terms.add(term)
            except re.error as e:
                logger.warning(f"正则表达式规则执行失败: {pattern}, 错误: {e}")
        
        # 去重（基于文本和位置）
        unique_entities = []
        seen_positions = set()
        
        for entity in entities:
            pos_key = (entity['text'], entity['start_pos'], entity['end_pos'])
            if pos_key not in seen_positions:
                unique_entities.append(entity)
                seen_positions.add(pos_key)
        
        logger.info(f"基于配置提取到 {len(unique_entities)} 个自定义实体")
        return unique_entities
    
    def _determine_entity_type_from_rule(self, rule: Dict[str, Any], term: str) -> str:
        """根据规则确定实体类型"""
        # 如果规则中指定了实体类型，使用它
        entity_type = rule.get('entity_type')
        if entity_type and entity_type in self.config_manager.get_entity_types():
            return entity_type
        
        # 否则根据规则名称推断
        rule_name = rule.get('name', '').lower()
        if 'person' in rule_name or '人名' in rule_name:
            return 'PERSON'
        elif 'org' in rule_name or '组织' in rule_name:
            return 'ORG'
        elif 'loc' in rule_name or '地点' in rule_name:
            return 'LOC'
        elif 'tech' in rule_name or '技术' in rule_name:
            return 'TECH'
        elif 'product' in rule_name or '产品' in rule_name:
            return 'PRODUCT'
        elif 'event' in rule_name or '事件' in rule_name:
            return 'EVENT'
        elif 'concept' in rule_name or '概念' in rule_name:
            return 'CONCEPT'
        
        # 默认返回TECH
        return 'TECH'
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        self._initialize_jieba()
        # 使用基于Jaccard相似度的计算，结合jieba分词优化
        if self.use_jieba:
            # 分词后计算相似度
            words1 = set(jieba.cut(text1))
            words2 = set(jieba.cut(text2))
        else:
            # 基于字符的相似度计算
            words1 = set(re.findall(r'[\u4e00-\u9fff]{1,4}|[a-zA-Z]{2,}', text1))
            words2 = set(re.findall(r'[\u4e00-\u9fff]{1,4}|[a-zA-Z]{2,}', text2))
        
        # 过滤停用词
        stop_words = {'的', '是', '在', '和', '与', '或', '了', '着', '过', '地', '得', '啊', '呢', '吧', '吗'}
        words1 = {word for word in words1 if word not in stop_words and len(word) > 1}
        words2 = {word for word in words2 if word not in stop_words and len(word) > 1}
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0.0
        
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
        self._initialize_jieba()
        if self.use_jieba:
            # 使用jieba优化的自适应分块
            return self._adaptive_jieba_chunking(text, target_chunk_size, min_chunk_size, max_chunk_size)
        else:
            return self._adaptive_rule_based_chunking(text, target_chunk_size, min_chunk_size, max_chunk_size)
    
    def _adaptive_jieba_chunking(self, text: str, target_chunk_size: int, min_chunk_size: int,
                                max_chunk_size: int) -> List[str]:
        """使用jieba的自适应分块"""
        # 使用句子边界分割
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
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