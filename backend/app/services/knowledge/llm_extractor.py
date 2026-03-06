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
    
    def __init__(self, db: Session = None):
        """
        初始化LLM实体提取器
        
        Args:
            db: 数据库会话，用于获取模型配置
        """
        self.db = db
        self.llm_service = LLMService()
        self.scene = "knowledge"  # 默认模型管理中的知识库场景
        self.fallback_scene = "chat"  # 回退场景：聊天
        
        logger.info("LLM实体提取器初始化成功")
    
    def _get_model_for_extraction(self) -> Optional[str]:
        """
        获取用于实体提取的模型
        
        按照以下优先级获取模型：
        1. 知识库场景(knowledge)的默认模型（从缓存或数据库）
        2. 聊天场景(chat)的默认模型（回退）
        3. 全局默认模型
        4. LLM服务默认模型
        
        Returns:
            模型ID或None（使用LLM服务默认模型）
        """
        # 1. 尝试获取知识库场景(knowledge)的默认模型
        model_id = self._get_scene_model_from_cache_or_db(self.scene)
        if model_id:
            logger.info(f"使用知识库场景默认模型: {model_id}")
            return model_id
        
        # 2. 如果知识库场景未配置，使用聊天场景(chat)作为回退
        logger.info(f"知识库场景未配置模型，尝试使用聊天场景")
        model_id = self._get_scene_model_from_cache_or_db(self.fallback_scene)
        if model_id:
            logger.info(f"使用聊天场景默认模型作为回退: {model_id}")
            return model_id
        
        # 3. 如果聊天场景也未配置，使用全局默认模型
        global_models = DefaultModelCacheService.get_cached_global_default_models()
        if global_models and len(global_models) > 0:
            model_int_id = global_models[0].get('model_id')
            # 转换为字符串ID
            model_id = self._get_model_string_id(model_int_id)
            if model_id:
                logger.info(f"使用全局默认模型: {model_id}")
                return model_id
        
        # 4. 如果都没有配置，返回None（使用LLM服务默认模型）
        logger.warning("未配置默认模型，使用LLM服务默认模型")
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
        
        Args:
            text: 输入文本
            
        Returns:
            用于实体提取的Prompt
        """
        prompt = f"""请从以下文本中提取所有实体，并以JSON格式返回。

文本内容：
{text}

请识别以下类型的实体：
- PERSON: 人名（如：张三、李四）
- ORG: 组织机构（如：阿里巴巴、清华大学）
- LOC: 地点（如：北京、上海）
- TECH: 技术术语（如：人工智能、深度学习）
- PRODUCT: 产品名称（如：iPhone、ChatGPT）
- CONCEPT: 概念（如：数字化转型、可持续发展）
- EVENT: 事件（如：奥运会、发布会）

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
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体列表
        """
        if not text or not text.strip():
            return []
        
        try:
            # 获取模型
            model_name = self._get_model_for_extraction()
            
            # 构建Prompt
            prompt = self._build_entity_extraction_prompt(text)
            
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
                    # 显示更多内容以便诊断问题
                    logger.error(f"问题JSON内容(前1000字符): {json_str[:1000]}")
                    logger.error(f"问题JSON内容(1000-2000字符): {json_str[1000:2000]}")
                    return []
            
            entities = result.get('entities', [])
            
            # 添加来源标记
            for entity in entities:
                entity['source'] = 'llm'
            
            logger.info(f"LLM提取到 {len(entities)} 个实体")
            return entities
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return []
    
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
        # 1. 检查缓存
        if use_cache:
            try:
                from app.services.knowledge.entity_extraction_cache import EntityExtractionCache
                cached_result = await EntityExtractionCache.get_cached_result(text)
                if cached_result:
                    logger.info("使用缓存的实体提取结果")
                    return cached_result
            except Exception as e:
                logger.warning(f"缓存读取失败: {e}")

        # 2. 提取实体
        entities = await self.extract_entities(text)

        # 3. 提取关系
        relationships = await self.extract_relationships(text, entities)

        # 4. 缓存结果
        if use_cache:
            try:
                from app.services.knowledge.entity_extraction_cache import EntityExtractionCache
                await EntityExtractionCache.cache_result(text, entities, relationships)
                logger.info("实体提取结果已缓存")
            except Exception as e:
                logger.warning(f"缓存写入失败: {e}")

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
            
            # 构建Prompt
            prompt = self._build_disambiguation_prompt(entity_mentions, context)
            
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
            
            logger.info(f"LLM消歧完成，生成 {len(entity_groups)} 个实体组")
            return entity_groups
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f"实体消歧失败: {e}")
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
