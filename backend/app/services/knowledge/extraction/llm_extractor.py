"""
LLM实体提取器模块

基于大语言模型(LLM)的实体和关系提取器，全面替代传统NLP方法。
提供高质量的实体识别、关系抽取和实体消歧功能。
"""

import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService
from app.services.default_model_cache_service import DefaultModelCacheService
from app.services.knowledge.entity_config_manager import EntityConfigManager

logger = logging.getLogger(__name__)


def _get_model_string_id_from_db(model_int_id: int, db: Session = None) -> Optional[str]:
    """
    将模型整数ID转换为字符串ID
    
    这是一个模块级函数，供LLMEntityExtractor和LLMEntityDisambiguator共用
    
    Args:
        model_int_id: 模型的整数ID
        db: 数据库会话，可选
        
    Returns:
        模型的字符串ID（如"deepseek-r1:1.5b"）或None
    """
    logger.info(f"[_get_model_string_id_from_db] 开始转换模型整数ID: {model_int_id}")
    
    if not model_int_id:
        logger.warning(f"[_get_model_string_id_from_db] 模型整数ID为空")
        return None
    
    # 如果已经是字符串，直接返回
    if isinstance(model_int_id, str):
        return model_int_id
        
    # 1. 先尝试从缓存获取
    try:
        all_models = DefaultModelCacheService.get_cached_all_models()
        logger.info(f"[_get_model_string_id_from_db] 缓存返回模型数量: {len(all_models) if all_models else 0}")
        if all_models:
            for model in all_models:
                if model.get('id') == model_int_id:
                    model_str_id = model.get('model_id')
                    logger.info(f"[_get_model_string_id_from_db] 从缓存找到模型字符串ID: {model_str_id}")
                    return model_str_id
                logger.warning(f"[_get_model_string_id_from_db] 缓存中未找到模型ID {model_int_id}")
    except Exception as e:
        logger.warning(f"[_get_model_string_id_from_db] 从缓存获取模型字符串ID失败: {e}")
    
    # 2. 缓存未命中，从数据库获取
    if db:
        try:
            from app.models.supplier_db import ModelDB
            model = db.query(ModelDB).filter(ModelDB.id == model_int_id).first()
            if model:
                logger.info(f"[_get_model_string_id_from_db] 从数据库找到模型字符串ID: {model.model_id}")
                return model.model_id
            else:
                logger.warning(f"[_get_model_string_id_from_db] 数据库中未找到模型ID {model_int_id}")
        except Exception as e:
            logger.error(f"[_get_model_string_id_from_db] 从数据库获取模型字符串ID失败: {e}")
    else:
        logger.warning(f"[_get_model_string_id_from_db] 数据库连接不可用")
    
    logger.warning(f"[_get_model_string_id_from_db] 未能转换模型整数ID {model_int_id}")
    return None


def _fix_json_common(json_str: str) -> str:
    """
    修复常见的JSON格式问题，包括处理截断的JSON
    
    这是一个模块级函数，供LLMEntityExtractor和LLMEntityDisambiguator共用
    
    Args:
        json_str: 原始JSON字符串
        
    Returns:
        修复后的JSON字符串
    """
    import re
    
    # 1. 移除JSON字符串中的注释
    json_str = re.sub(r'//.*?\n', '\n', json_str)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    
    # 2. 修复尾随逗号（在}或]之前的逗号）
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # 3. 修复多余的逗号
    json_str = re.sub(r',\s*,', ',', json_str)
    
    # 4. 修复对象或数组中缺少逗号的情况
    json_str = re.sub(r'(}\s*){', r'}\1{', json_str)
    json_str = re.sub(r'(]\s*)\[', r']\1[', json_str)
    
    # 5. 计算括号平衡
    brace_count = 0  # {}
    bracket_count = 0  # []
    in_string = False
    escape_next = False
    
    for char in json_str:
        if escape_next:
            escape_next = False
            continue
        if char == '\\':
            escape_next = True
            continue
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
    
    # 6. 如果JSON被截断，尝试修复
    # 策略：找到最后一个完整的对象，然后正确闭合数组和根对象
    if brace_count > 0 or bracket_count > 0:
        # 找到最后一个完整的实体对象（以}结尾，且不是在字符串中）
        # 从后向前查找，找到最后一个不在字符串中的 }
        last_brace_pos = -1
        in_string = False
        escape_next = False
        
        for i in range(len(json_str) - 1, -1, -1):
            char = json_str[i]
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if not in_string and char == '}':
                last_brace_pos = i
                break
        
        if last_brace_pos > 0:
            # 截断到最后一个完整对象之后
            json_str = json_str[:last_brace_pos + 1]
            
            # 重新计算括号平衡
            brace_count = 0
            bracket_count = 0
            in_string = False
            escape_next = False
            
            for char in json_str:
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                    elif char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
    
    # 7. 确保JSON以正确的括号结束
    # 结构应该是: {"entities": [...]}
    # 所以需要先关闭数组 ]，再关闭根对象 }
    if bracket_count > 0:
        json_str += ']' * bracket_count
    
    if brace_count > 0:
        json_str += '}' * brace_count
    
    return json_str


class LLMEntityExtractor:
    """
    LLM实体提取器
    
    基于大语言模型进行实体识别和关系抽取，支持多种实体类型和复杂关系。
    集成默认模型管理系统，自动获取知识库场景配置的模型。
    """
    
    def __init__(self, db: Session = None, knowledge_base_id: int = None):
        """
        初始化LLM实体提取器

        Args:
            db: 数据库会话，用于获取模型配置
            knowledge_base_id: 知识库ID，用于加载知识库级配置
        """
        self.db = db
        self.knowledge_base_id = knowledge_base_id
        self.specified_model_id = None  # 外部指定的模型ID（优先级最高）
        self.llm_service = LLMService()

        # 初始化配置管理器（支持知识库级配置）
        self.config_manager = EntityConfigManager(knowledge_base_id)

        # 定义分层场景（按优先级从高到低）
        self.scene_hierarchy = self._build_scene_hierarchy(knowledge_base_id)

        logger.info(f"LLM实体提取器初始化成功，知识库ID: {knowledge_base_id}，场景层级: {self.scene_hierarchy}")

    def _build_scene_hierarchy(self, knowledge_base_id: int = None) -> List[str]:
        """
        构建分层场景列表（按优先级从高到低）

        场景层级设计：
        1. 知识库任务级: knowledge_kb_{kb_id}_extraction
        2. 知识库级: knowledge_kb_{kb_id}
        3. 任务级: knowledge_extraction
        4. 通用知识库级: knowledge
        5. 回退级: chat

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            按优先级排序的场景列表
        """
        scenes = []

        # 1. 知识库任务级（最具体）
        if knowledge_base_id:
            scenes.append(f"knowledge_kb_{knowledge_base_id}_extraction")

        # 2. 知识库级
        if knowledge_base_id:
            scenes.append(f"knowledge_kb_{knowledge_base_id}")

        # 3. 任务级
        scenes.append("knowledge_extraction")

        # 4. 通用知识库级
        scenes.append("knowledge")

        # 5. 回退级（最通用）
        scenes.append("chat")

        return scenes

    def _get_model_for_extraction(self) -> Optional[str]:
        """
        获取用于实体提取的模型

        按照以下优先级获取模型：
        1. 外部指定的模型ID（specified_model_id，优先级最高）
        2. 遍历场景层级（从具体到通用）
        3. 如果所有场景都未配置，使用全局默认模型
        4. 如果全局也未配置，使用LLM服务默认模型

        Returns:
            模型ID或None（使用LLM服务默认模型）
        """
        logger.info(f"[_get_model_for_extraction] 开始获取模型, knowledge_base_id={self.knowledge_base_id}")
        logger.info(f"[_get_model_for_extraction] 场景层级: {self.scene_hierarchy}")
        logger.info(f"[_get_model_for_extraction] 外部指定模型ID: {self.specified_model_id}")

        # 1. 优先使用外部指定的模型ID
        if self.specified_model_id:
            logger.info(f"[_get_model_for_extraction] 使用外部指定的模型: {self.specified_model_id}")
            return self.specified_model_id

        # 2. 按优先级遍历场景层级
        for scene in self.scene_hierarchy:
            logger.info(f"[_get_model_for_extraction] 尝试场景: {scene}")
            model_id = self._get_scene_model_from_cache_or_db(scene)
            if model_id:
                logger.info(f"[_get_model_for_extraction] 使用场景 '{scene}' 的默认模型: {model_id}")
                return model_id
            else:
                logger.info(f"[_get_model_for_extraction] 场景 '{scene}' 未配置模型，尝试下一个场景")

        # 3. 如果所有场景都未配置，使用全局默认模型
        logger.info("[_get_model_for_extraction] 所有场景都未配置模型，尝试使用全局默认模型")
        global_models = DefaultModelCacheService.get_cached_global_default_models()
        logger.info(f"[_get_model_for_extraction] 全局默认模型: {global_models}")

        if global_models and len(global_models) > 0:
            model_int_id = global_models[0].get('model_id')
            logger.info(f"[_get_model_for_extraction] 全局模型整数ID: {model_int_id}")
            # 转换为字符串ID
            model_id = self._get_model_string_id(model_int_id)
            if model_id:
                logger.info(f"[_get_model_for_extraction] 使用全局默认模型: {model_id}")
                return model_id
            else:
                logger.warning(f"[_get_model_for_extraction] 无法将全局模型整数ID {model_int_id} 转换为字符串ID")
        else:
            logger.warning("[_get_model_for_extraction] 没有配置全局默认模型")

        # 3. 如果都没有配置，返回None（使用LLM服务默认模型）
        logger.warning("[_get_model_for_extraction] 未配置默认模型，将使用LLM服务默认模型")
        return None
    
    def _get_scene_model_from_cache_or_db(self, scene: str) -> Optional[str]:
        """
        从缓存或数据库获取场景默认模型
        
        Args:
            scene: 场景名称
            
        Returns:
            模型字符串ID（如"deepseek-r1:1.5b"）或None
        """
        logger.info(f"[_get_scene_model_from_cache_or_db] 开始获取{scene}场景模型")
        
        # 1. 先尝试从缓存获取
        scene_models = DefaultModelCacheService.get_cached_scene_default_models(scene)
        logger.info(f"[_get_scene_model_from_cache_or_db] 缓存返回: {scene_models}")
        if scene_models and len(scene_models) > 0:
            # 缓存返回的是模型整数ID，需要转换为字符串ID
            model_int_id = scene_models[0].get('model_id')
            logger.info(f"[_get_scene_model_from_cache_or_db] 从缓存获取模型整数ID: {model_int_id}")
            if model_int_id:
                model_str_id = self._get_model_string_id(model_int_id)
                logger.info(f"[_get_scene_model_from_cache_or_db] 缓存模型转换为字符串ID: {model_str_id}")
                return model_str_id
        
        # 2. 缓存未命中，从数据库获取
        if self.db:
            try:
                from app.models.default_model import DefaultModel
                config = self.db.query(DefaultModel).filter(
                    DefaultModel.scope == "scene",
                    DefaultModel.scene == scene,
                    DefaultModel.is_active == True
                ).order_by(DefaultModel.priority.asc()).first()
                
                if config:
                    logger.info(f"[_get_scene_model_from_cache_or_db] 从数据库获取到{scene}场景模型配置，模型整数ID: {config.model_id}")
                    # 转换为字符串ID
                    model_str_id = self._get_model_string_id(config.model_id)
                    if model_str_id:
                        logger.info(f"[_get_scene_model_from_cache_or_db] 数据库模型转换为字符串ID: {model_str_id}")
                        return model_str_id
                    else:
                        logger.warning(f"[_get_scene_model_from_cache_or_db] 无法将模型整数ID {config.model_id} 转换为字符串ID")
                else:
                    logger.info(f"[_get_scene_model_from_cache_or_db] 数据库中未找到{scene}场景配置")
            except Exception as e:
                logger.error(f"[_get_scene_model_from_cache_or_db] 从数据库获取{scene}场景模型失败: {e}")
        else:
            logger.warning(f"[_get_scene_model_from_cache_or_db] 数据库连接不可用")
        
        logger.warning(f"[_get_scene_model_from_cache_or_db] 未能获取到{scene}场景模型")
        return None
    
    def _get_model_string_id(self, model_int_id: int) -> Optional[str]:
        """
        将模型整数ID转换为字符串ID
        
        调用模块级函数，传入当前实例的数据库连接
        
        Args:
            model_int_id: 模型的整数ID
            
        Returns:
            模型的字符串ID（如"deepseek-r1:1.5b"）或None
        """
        return _get_model_string_id_from_db(model_int_id, self.db)
    
    def _fix_json(self, json_str: str) -> str:
        """
        修复常见的JSON格式问题，包括处理截断的JSON
        
        调用模块级函数

        Args:
            json_str: 原始JSON字符串

        Returns:
            修复后的JSON字符串
        """
        return _fix_json_common(json_str)
    
    def _build_entity_extraction_prompt(self, text: str) -> str:
        """
        构建实体提取的Prompt

        根据配置动态构建Prompt，支持自定义实体类型

        Args:
            text: 输入文本

        Returns:
            用于实体提取的Prompt
        """
        # 获取启用的实体类型配置
        entity_types = self.config_manager.get_entity_types()

        # 构建实体类型描述
        type_descriptions = []
        for type_key, type_config in entity_types.items():
            if type_config.get('enabled', True):
                name = type_config.get('name', type_key)
                description = type_config.get('description', '')
                type_descriptions.append(f"- {type_key}: {name}（{description}）")

        # 如果没有启用的实体类型，使用默认类型
        if not type_descriptions:
            type_descriptions = [
                "- PERSON: 人名（如：张三、李四）",
                "- ORG: 组织机构（如：阿里巴巴、清华大学）",
                "- LOC: 地点（如：北京、上海）",
                "- TECH: 技术术语（如：人工智能、深度学习）",
                "- PRODUCT: 产品名称（如：iPhone、ChatGPT）",
                "- CONCEPT: 概念（如：数字化转型、可持续发展）",
                "- EVENT: 事件（如：奥运会、发布会）"
            ]

        type_list = "\n".join(type_descriptions)

        prompt = f"""请从以下文本中提取所有实体，并以JSON格式返回。

文本内容：
{text}

请识别以下类型的实体：
{type_list}

请按以下JSON格式返回结果：
{{
    "entities": [
        {{
            "text": "实体文本",
            "type": "实体类型",
            "start_pos": 开始位置,
            "end_pos": 结束位置
        }}
    ]
}}

注意：
1. 确保提取所有相关实体，不要遗漏
2. 准确标注实体类型
3. 提供准确的字符位置
4. 只返回JSON格式，不要其他解释"""

        return prompt
    
    def _build_relationship_extraction_prompt(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """
        构建关系提取的Prompt
        
        Args:
            text: 输入文本
            entities: 已提取的实体列表
            
        Returns:
            用于关系提取的Prompt
        """
        entities_str = json.dumps(entities, ensure_ascii=False, indent=2)
        
        prompt = f"""请从以下文本中提取实体之间的关系，并以JSON格式返回。

文本内容：
{text}

已识别的实体：
{entities_str}

请识别以下类型的关系：
- 工作于: 人员与组织机构的关系
- 创立: 人员创建组织机构
- 位于: 实体与地点的关系
- 开发: 人员或组织开发技术/产品
- 使用: 实体使用技术/产品
- 包含: 实体之间的包含关系
- 合作: 实体之间的合作关系
- 属于: 实体之间的从属关系
- 相关: 其他相关关系

请按以下JSON格式返回结果：
{{
    "relationships": [
        {{
            "subject": "主体实体",
            "relation": "关系类型",
            "object": "客体实体",
            "confidence": 0.95
        }}
    ]
}}

注意：
1. 只提取文本中明确表达的关系
2. 为每个关系提供置信度(0-1)
3. 确保主体和客体都在已识别实体中
4. 只返回JSON格式，不要其他解释"""
        
        return prompt
    
    MAX_TEXT_LENGTH = 80000
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取实体

        Args:
            text: 输入文本

        Returns:
            实体列表
        """
        logger.info(f"[LLMExtractor] extract_entities 开始, 文本长度={len(text)}")

        if not text or not text.strip():
            logger.warning("[LLMExtractor] 文本为空，返回空列表")
            return []

        if len(text) > self.MAX_TEXT_LENGTH:
            logger.info(f"[LLMExtractor] 文本过长({len(text)}字符)，启用分段处理")
            return await self._extract_entities_from_long_text(text)

        try:
            # 获取模型
            model_name = self._get_model_for_extraction()
            logger.info(f"[LLMExtractor] 使用模型: {model_name}")

            # 构建Prompt
            prompt = self._build_entity_extraction_prompt(text)
            logger.info(f"[LLMExtractor] Prompt长度: {len(prompt)}")

            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            logger.info(f"[LLMExtractor] 调用LLM服务...")
            logger.info(f"[LLMExtractor] 请求参数: model_name={model_name}, max_tokens=2000, temperature=0.3")

            try:
                response = self.llm_service.chat_completion(
                    messages=messages,
                    model_name=model_name,
                    max_tokens=2000,
                    temperature=0.3,
                    db=self.db
                )
                logger.info(f"[LLMExtractor] LLM调用成功返回")
            except Exception as e:
                logger.error(f"[LLMExtractor] LLM调用抛出异常: {e}", exc_info=True)
                return []

            logger.info(f"[LLMExtractor] LLM响应类型: {type(response)}")
            logger.info(f"[LLMExtractor] LLM响应: success={response.get('success')}, keys={list(response.keys()) if isinstance(response, dict) else 'N/A'}")

            if not response.get('success'):
                logger.error(f"[LLMExtractor] LLM调用失败: {response.get('error')}")
                logger.error(f"[LLMExtractor] 完整响应: {response}")
                return []

            # 解析JSON响应
            content = response.get('generated_text', '')
            logger.info(f"[LLMExtractor] LLM生成内容类型: {type(content)}")
            logger.info(f"[LLMExtractor] LLM生成内容长度: {len(content) if content else 0}")

            if not content:
                logger.error(f"[LLMExtractor] LLM返回空内容! 完整响应: {response}")
                return []

            logger.info(f"[LLMExtractor] LLM生成内容前500字符: {content[:500]}")

            # 提取JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}')

            if json_start == -1 or json_end == -1:
                logger.warning(f"[LLMExtractor] LLM响应中没有找到JSON: {content[:500]}")
                return []

            json_str = content[json_start:json_end + 1]
            logger.info(f"[LLMExtractor] 提取的JSON长度: {len(json_str)}")

            # 尝试解析JSON，如果失败则尝试修复
            try:
                result = json.loads(json_str)
                logger.info(f"[LLMExtractor] JSON解析成功")
            except json.JSONDecodeError as e:
                logger.warning(f"[LLMExtractor] JSON解析失败，尝试修复: {e}")
                # 尝试修复常见的JSON格式问题
                json_str = self._fix_json(json_str)
                try:
                    result = json.loads(json_str)
                    logger.info(f"[LLMExtractor] JSON修复后解析成功")
                except json.JSONDecodeError as e2:
                    logger.error(f"[LLMExtractor] JSON修复后仍解析失败: {e2}")
                    # 显示更多内容以便诊断问题
                    logger.error(f"[LLMExtractor] 问题JSON内容(前1000字符): {json_str[:1000]}")
                    return []

            entities = result.get('entities', [])
            logger.info(f"[LLMExtractor] 从JSON中提取到 {len(entities)} 个实体")

            # 添加来源标记
            for entity in entities:
                entity['source'] = 'llm'

            logger.info(f"[LLMExtractor] 最终返回 {len(entities)} 个实体")
            return entities

        except json.JSONDecodeError as e:
            logger.error(f"[LLMExtractor] JSON解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f"[LLMExtractor] 实体提取失败: {e}", exc_info=True)
            return []
    
    async def _extract_entities_from_long_text(self, text: str) -> List[Dict[str, Any]]:
        """
        对长文本进行分段实体提取

        将长文本分割成多个较小的片段，分别提取实体，然后合并去重

        Args:
            text: 输入长文本

        Returns:
            合并后的实体列表
        """
        logger.info(f"[LLMExtractor] 开始分段处理长文本, 总长度={len(text)}")
        
        chunk_size = self.MAX_TEXT_LENGTH
        chunks = []
        
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            chunks.append({
                'text': chunk,
                'start_offset': i,
                'index': len(chunks)
            })
        
        logger.info(f"[LLMExtractor] 文本已分割为 {len(chunks)} 个片段")
        
        all_entities = []
        
        for chunk_info in chunks:
            chunk_text = chunk_info['text']
            chunk_index = chunk_info['index']
            start_offset = chunk_info['start_offset']
            
            logger.info(f"[LLMExtractor] 处理片段 {chunk_index + 1}/{len(chunks)}, 长度={len(chunk_text)}")
            
            try:
                entities = await self._extract_entities_single_chunk(chunk_text)
                
                for entity in entities:
                    entity['start_pos'] = entity.get('start_pos', 0) + start_offset
                    entity['end_pos'] = entity.get('end_pos', 0) + start_offset
                    entity['chunk_index'] = chunk_index
                
                all_entities.extend(entities)
                logger.info(f"[LLMExtractor] 片段 {chunk_index + 1} 提取到 {len(entities)} 个实体")
                
            except Exception as e:
                logger.error(f"[LLMExtractor] 片段 {chunk_index + 1} 提取失败: {e}")
                continue
        
        merged_entities = self._merge_and_deduplicate_entities(all_entities)
        
        logger.info(f"[LLMExtractor] 分段处理完成: 原始实体数={len(all_entities)}, 合并后={len(merged_entities)}")
        
        return merged_entities
    
    async def _extract_entities_single_chunk(self, text: str) -> List[Dict[str, Any]]:
        """
        从单个文本片段中提取实体（内部方法，不进行分段检测）

        Args:
            text: 输入文本片段

        Returns:
            实体列表
        """
        if not text or not text.strip():
            return []

        try:
            model_name = self._get_model_for_extraction()
            prompt = self._build_entity_extraction_prompt(text)
            messages = [{"role": "user", "content": prompt}]
            
            response = self.llm_service.chat_completion(
                messages=messages,
                model_name=model_name,
                max_tokens=2000,
                temperature=0.3,
                db=self.db
            )

            if not response.get('success'):
                logger.error(f"[LLMExtractor] LLM调用失败: {response.get('error')}")
                return []

            content = response.get('generated_text', '')
            if not content:
                return []

            json_start = content.find('{')
            json_end = content.rfind('}')

            if json_start == -1 or json_end == -1:
                return []

            json_str = content[json_start:json_end + 1]

            try:
                result = json.loads(json_str)
            except json.JSONDecodeError:
                json_str = self._fix_json(json_str)
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    return []

            entities = result.get('entities', [])

            # 修复：校准实体位置信息
            entities = self._calibrate_entity_positions(text, entities)

            for entity in entities:
                entity['source'] = 'llm'

            return entities

        except Exception as e:
            logger.error(f"[LLMExtractor] 单片段实体提取失败: {e}")
            return []

    def _calibrate_entity_positions(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """校准实体位置信息

        修复：LLM返回的位置信息可能不准确，使用字符串查找进行校准

        Args:
            text: 原始文本
            entities: 实体列表

        Returns:
            位置校准后的实体列表
        """
        calibrated = []

        for entity in entities:
            entity_text = entity.get('text', '').strip()
            if not entity_text:
                continue

            # 在文本中查找实体位置
            start_pos = text.find(entity_text)

            if start_pos != -1:
                # 找到精确匹配
                entity['start_pos'] = start_pos
                entity['end_pos'] = start_pos + len(entity_text)
            else:
                # 尝试模糊匹配（去除空格等）
                normalized_text = text.replace(' ', '').replace('\n', '').replace('\t', '')
                normalized_entity = entity_text.replace(' ', '').replace('\n', '').replace('\t', '')

                norm_start = normalized_text.find(normalized_entity)
                if norm_start != -1:
                    # 将归一化位置映射回原始文本
                    # 这是一个近似值
                    orig_start = entity.get('start_pos', 0)
                    orig_end = entity.get('end_pos', orig_start + len(entity_text))

                    # 如果LLM返回的位置在文本范围内，保留原位置
                    if 0 <= orig_start < len(text) and orig_end <= len(text):
                        entity['start_pos'] = orig_start
                        entity['end_pos'] = orig_end
                    else:
                        # 位置超出范围，设为0
                        entity['start_pos'] = 0
                        entity['end_pos'] = min(len(entity_text), len(text))
                else:
                    # 完全找不到，使用LLM返回的位置或设为0
                    orig_start = entity.get('start_pos', 0)
                    orig_end = entity.get('end_pos', orig_start + len(entity_text))

                    if orig_start >= len(text):
                        entity['start_pos'] = 0
                        entity['end_pos'] = min(len(entity_text), len(text))

            calibrated.append(entity)

        return calibrated
    
    def _merge_and_deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并并去重实体列表

        Args:
            entities: 原始实体列表（可能包含重复）

        Returns:
            去重后的实体列表
        """
        if not entities:
            return []
        
        entity_map = {}
        
        for entity in entities:
            text = entity.get('text', '').strip()
            entity_type = entity.get('type', 'UNKNOWN')
            
            if not text:
                continue
            
            key = (text, entity_type)
            
            if key not in entity_map:
                entity_map[key] = entity
            else:
                existing = entity_map[key]
                existing_confidence = existing.get('confidence', 0.5)
                new_confidence = entity.get('confidence', 0.5)
                
                if new_confidence > existing_confidence:
                    entity_map[key] = entity
        
        merged = list(entity_map.values())
        
        merged.sort(key=lambda x: x.get('start_pos', 0))
        
        return merged
    
    async def extract_relationships(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从文本中提取关系
        
        Args:
            text: 输入文本
            entities: 已提取的实体列表
            
        Returns:
            关系列表
        """
        if not text or not text.strip() or not entities:
            return []
        
        try:
            # 获取模型
            model_name = self._get_model_for_extraction()
            
            # 构建Prompt
            prompt = self._build_relationship_extraction_prompt(text, entities)
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_service.chat_completion(
                messages=messages,
                model_name=model_name,
                max_tokens=2000,
                temperature=0.3,
                db=self.db
            )
            
            if not response.get('success'):
                logger.error(f"LLM调用失败: {response.get('error')}")
                return []
            
            # 解析JSON响应
            content = response.get('generated_text', '')
            
            # 提取JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}')
            
            if json_start == -1 or json_end == -1:
                logger.warning(f"LLM响应中没有找到JSON: {content[:500]}")
                return []
            
            json_str = content[json_start:json_end + 1]
            
            # 尝试解析JSON，如果失败则尝试修复
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败，尝试修复: {e}")
                # 尝试修复常见的JSON格式问题
                json_str = self._fix_json(json_str)
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e2:
                    logger.error(f"JSON修复后仍解析失败: {e2}")
                    logger.error(f"问题JSON内容: {json_str[:500]}")
                    return []
            
            relationships = result.get('relationships', [])
            
            # 添加来源标记
            for rel in relationships:
                rel['source'] = 'llm'
            
            logger.info(f"LLM提取到 {len(relationships)} 个关系")
            return relationships
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f"关系提取失败: {e}")
            return []
    
    async def extract_entities_and_relationships(self, text: str, use_cache: bool = True) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        同时提取实体和关系

        Args:
            text: 输入文本
            use_cache: 是否使用缓存，默认True

        Returns:
            (实体列表, 关系列表)
        """
        logger.info(f"[LLMExtractor] 开始提取实体和关系, 文本长度={len(text)}, use_cache={use_cache}, "
                   f"knowledge_base_id={self.knowledge_base_id}, scene_hierarchy={self.scene_hierarchy}")

        # 1. 检查缓存（使用知识库ID区分不同知识库的缓存）
        if use_cache:
            try:
                from app.services.knowledge.extraction.entity_extraction_cache import EntityExtractionCache
                cached_result = await EntityExtractionCache.get_cached_result(text, knowledge_base_id=self.knowledge_base_id)
                if cached_result:
                    logger.info(f"[LLMExtractor] 使用缓存的实体提取结果 (knowledge_base_id={self.knowledge_base_id})")
                    return cached_result
            except Exception as e:
                logger.warning(f"[LLMExtractor] 缓存读取失败: {e}")

        # 2. 提取实体
        logger.info("[LLMExtractor] 开始提取实体...")
        try:
            entities = await self.extract_entities(text)
            logger.info(f"[LLMExtractor] 实体提取完成: {len(entities)} 个实体")
            if entities:
                logger.info(f"[LLMExtractor] 前3个实体: {entities[:3]}")
        except Exception as e:
            logger.error(f"[LLMExtractor] 实体提取失败: {e}", exc_info=True)
            entities = []

        # 3. 提取关系
        logger.info("[LLMExtractor] 开始提取关系...")
        try:
            relationships = await self.extract_relationships(text, entities)
            logger.info(f"[LLMExtractor] 关系提取完成: {len(relationships)} 个关系")
        except Exception as e:
            logger.error(f"[LLMExtractor] 关系提取失败: {e}", exc_info=True)
            relationships = []

        # 4. 缓存结果（使用知识库ID区分不同知识库的缓存）
        if use_cache:
            try:
                from app.services.knowledge.extraction.entity_extraction_cache import EntityExtractionCache
                await EntityExtractionCache.cache_result(text, entities, relationships, knowledge_base_id=self.knowledge_base_id)
                logger.info(f"[LLMExtractor] 实体提取结果已缓存 (knowledge_base_id={self.knowledge_base_id})")
            except Exception as e:
                logger.warning(f"[LLMExtractor] 缓存写入失败: {e}")

        logger.info(f"[LLMExtractor] 提取完成: {len(entities)} 个实体, {len(relationships)} 个关系")
        return entities, relationships


class LLMEntityDisambiguator:
    """
    LLM实体消歧器
    
    基于大语言模型进行实体消歧，解决实体指代不明、同名异义等问题。
    """
    
    def __init__(self, db: Session = None):
        """
        初始化LLM实体消歧器
        
        Args:
            db: 数据库会话，用于获取模型配置
        """
        self.db = db
        self.llm_service = LLMService()
        self.scene = "knowledge"
        self.fallback_scene = "chat"
        
        logger.info("LLM实体消歧器初始化成功")
    
    def _get_model_for_disambiguation(self) -> Optional[str]:
        """
        获取用于实体消歧的模型
        
        Returns:
            模型ID字符串或None
        """
        # 1. 尝试获取知识库场景(knowledge)的默认模型
        model_id = self._get_scene_model_from_cache_or_db(self.scene)
        if model_id:
            logger.info(f"使用知识库场景默认模型进行消歧: {model_id}")
            return model_id
        
        # 2. 如果知识库场景未配置，使用聊天场景(chat)作为回退
        model_id = self._get_scene_model_from_cache_or_db(self.fallback_scene)
        if model_id:
            logger.info(f"使用聊天场景默认模型进行消歧: {model_id}")
            return model_id
        
        # 3. 如果聊天场景也未配置，使用全局默认模型
        global_models = DefaultModelCacheService.get_cached_global_default_models()
        if global_models and len(global_models) > 0:
            model_id = global_models[0].get('model_id')
            if model_id:
                # 确保返回字符串类型，使用模块级函数
                model_id = _get_model_string_id_from_db(model_id, self.db)
                logger.info(f"使用全局默认模型进行消歧: {model_id}")
                return model_id
        
        # 4. 如果都没有配置，返回None
        logger.warning("未配置默认模型，使用LLM服务默认模型进行消歧")
        return None
    
    def _get_scene_model_from_cache_or_db(self, scene: str) -> Optional[str]:
        """
        从缓存或数据库获取场景默认模型
        
        Args:
            scene: 场景名称
            
        Returns:
            模型ID字符串或None
        """
        # 1. 先尝试从缓存获取
        scene_models = DefaultModelCacheService.get_cached_scene_default_models(scene)
        logger.info(f"[_get_scene_model_from_cache_or_db] 场景 {scene} 缓存结果: {scene_models}")
        if scene_models and len(scene_models) > 0:
            model_id = scene_models[0].get('model_id')
            logger.info(f"[_get_scene_model_from_cache_or_db] 从缓存获取到模型ID: {model_id} (类型: {type(model_id)})")
            if model_id:
                # 确保返回字符串类型，使用模块级函数
                return _get_model_string_id_from_db(model_id, self.db)
        
        # 2. 缓存未命中，从数据库获取
        if self.db:
            try:
                from app.models.default_model import DefaultModel
                config = self.db.query(DefaultModel).filter(
                    DefaultModel.scope == "scene",
                    DefaultModel.scene == scene,
                    DefaultModel.is_active == True
                ).order_by(DefaultModel.priority.asc()).first()
                
                if config:
                    logger.info(f"[_get_scene_model_from_cache_or_db] 从数据库获取到{scene}场景模型: {config.model_id} (类型: {type(config.model_id)})")
                    # 确保返回字符串类型，使用模块级函数
                    return _get_model_string_id_from_db(config.model_id, self.db)
                else:
                    logger.warning(f"[_get_scene_model_from_cache_or_db] 数据库中未找到{scene}场景模型配置")
            except Exception as e:
                logger.error(f"[_get_scene_model_from_cache_or_db] 从数据库获取{scene}场景模型失败: {e}")
        else:
            logger.warning(f"[_get_scene_model_from_cache_or_db] 数据库连接不可用，无法获取{scene}场景模型")
        
        return None
    
    def _build_disambiguation_prompt(self, entity_mentions: List[Dict[str, Any]], context: str = None) -> str:
        """
        构建实体消歧的Prompt
        
        Args:
            entity_mentions: 实体提及列表
            context: 上下文文本
            
        Returns:
            用于实体消歧的Prompt
        """
        mentions_str = json.dumps(entity_mentions, ensure_ascii=False, indent=2)
        
        context_str = f"\n上下文：\n{context}" if context else ""
        
        prompt = f"""请对以下实体提及进行消歧，判断哪些提及指向同一实体。

实体提及列表：
{mentions_str}
{context_str}

请分析每个实体提及的上下文，判断：
1. 哪些提及指向同一实体（同名同义）
2. 哪些提及指向不同实体（同名异义）
3. 为每个实体组生成唯一的实体ID和标准化名称

请按以下JSON格式返回结果：
{{
    "entity_groups": [
        {{
            "entity_id": "唯一实体ID",
            "canonical_name": "标准化名称",
            "mentions": ["提及1", "提及2"],
            "entity_type": "实体类型",
            "confidence": 0.95
        }}
    ]
}}

注意：
1. 仔细分析上下文，确保消歧准确
2. 为每个实体组提供置信度(0-1)
3. 标准化名称应该是该实体最通用的称呼
4. 只返回JSON格式，不要其他解释"""
        
        return prompt
    
    async def disambiguate_entities(self, entity_mentions: List[Dict[str, Any]], context: str = None) -> List[Dict[str, Any]]:
        """
        对实体提及进行消歧
        
        Args:
            entity_mentions: 实体提及列表，每个包含text, type, context等信息
            context: 整体上下文文本
            
        Returns:
            消歧后的实体组列表
        """
        if not entity_mentions:
            return []
        
        try:
            # 获取模型
            model_name = self._get_model_for_disambiguation()
            logger.info(f"[实体消歧] 开始消歧 {len(entity_mentions)} 个实体提及，使用模型: {model_name}")

            # 构建Prompt
            prompt = self._build_disambiguation_prompt(entity_mentions, context)
            logger.debug(f"[实体消歧] Prompt长度: {len(prompt)}")

            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            logger.info(f"[实体消歧] 调用LLM服务...")
            response = self.llm_service.chat_completion(
                messages=messages,
                model_name=model_name,
                max_tokens=2000,
                temperature=0.3,
                db=self.db
            )

            logger.info(f"[实体消歧] LLM响应: success={response.get('success')}")

            if not response.get('success'):
                logger.error(f"[实体消歧] LLM调用失败: {response.get('error')}")
                return []

            # 解析JSON响应
            content = response.get('generated_text', '')
            logger.info(f"[实体消歧] LLM生成的内容长度: {len(content)}")
            logger.debug(f"[实体消歧] LLM生成的内容: {content[:500]}...")
            
            # 提取JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}')
            
            if json_start == -1 or json_end == -1:
                logger.warning(f"LLM响应中没有找到JSON: {content}")
                return []
            
            json_str = content[json_start:json_end + 1]
            
            # 尝试解析JSON，如果失败则尝试修复
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败，尝试修复: {e}")
                # 尝试修复JSON
                fixed_json_str = _fix_json_common(json_str)
                try:
                    result = json.loads(fixed_json_str)
                    logger.info("JSON修复成功")
                except json.JSONDecodeError as e2:
                    logger.error(f"JSON修复后仍然失败: {e2}")
                    return []
            
            entity_groups = result.get('entity_groups', [])

            logger.info(f"[实体消歧] LLM消歧完成，生成 {len(entity_groups)} 个实体组")
            if entity_groups:
                logger.info(f"[实体消歧] 前3个实体组: {entity_groups[:3]}")
            else:
                logger.warning(f"[实体消歧] 实体组为空! 完整响应: {result}")
            return entity_groups

        except json.JSONDecodeError as e:
            logger.error(f"[实体消歧] JSON解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f"[实体消歧] 实体消歧失败: {e}", exc_info=True)
            return []
    
    async def resolve_coreference(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        指代消解，将代词指代解析为具体实体
        
        Args:
            text: 原始文本
            entities: 已提取的实体列表
            
        Returns:
            包含指代信息的实体列表
        """
        if not text or not entities:
            return entities
        
        try:
            # 获取模型
            model_name = self._get_model_for_disambiguation()
            
            entities_str = json.dumps(entities, ensure_ascii=False, indent=2)
            
            prompt = f"""请分析以下文本中的指代关系，将代词指代解析为具体实体。

文本内容：
{text}

已识别的实体：
{entities_str}

请识别文本中的代词（如：他、她、它、他们、该公司等），并判断它们分别指代哪个实体。

请按以下JSON格式返回结果：
{{
    "coreferences": [
        {{
            "pronoun": "代词文本",
            "position": 代词位置,
            "refers_to": "指代的实体文本",
            "entity_id": "实体ID",
            "confidence": 0.95
        }}
    ]
}}

注意：
1. 只识别明确的指代关系
2. 为每个指代提供置信度(0-1)
3. 如果无法确定指代关系，不要强行匹配
4. 只返回JSON格式，不要其他解释"""
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_service.chat_completion(
                messages=messages,
                model_name=model_name,
                max_tokens=2000,
                temperature=0.3,
                db=self.db
            )
            
            if not response.get('success'):
                logger.error(f"LLM调用失败: {response.get('error')}")
                return entities
            
            # 解析JSON响应
            content = response.get('generated_text', '')
            
            # 提取JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}')
            
            if json_start == -1 or json_end == -1:
                logger.warning(f"LLM响应中没有找到JSON: {content}")
                return entities
            
            json_str = content[json_start:json_end + 1]
            result = json.loads(json_str)
            
            coreferences = result.get('coreferences', [])
            
            # 将指代信息添加到实体中
            for coref in coreferences:
                for entity in entities:
                    if entity.get('text') == coref.get('refers_to'):
                        if 'coreferences' not in entity:
                            entity['coreferences'] = []
                        entity['coreferences'].append({
                            'pronoun': coref.get('pronoun'),
                            'position': coref.get('position'),
                            'confidence': coref.get('confidence')
                        })
            
            logger.info(f"LLM指代消解完成，识别 {len(coreferences)} 个指代关系")
            return entities
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return entities
        except Exception as e:
            logger.error(f"指代消解失败: {e}")
            return entities
