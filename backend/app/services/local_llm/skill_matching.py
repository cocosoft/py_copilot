from typing import Dict, Any, List, Optional
from app.services.llm_service import LLMService
from app.services.skill_registry import SkillRegistry
from app.core.database import get_db
from sqlalchemy.orm import Session
import logging
import time

logger = logging.getLogger(__name__)


class LocalSkillMatchingService:
    """本地技能匹配服务"""
    
    def __init__(self):
        """初始化本地技能匹配服务"""
        self.llm_service = LLMService()
        self.skill_registry = SkillRegistry()
        self.local_model = "deepseek-r1:1.5b"
        # 缓存字典
        self._cache = {}
        self._cache_expiry = {}
        self._cache_ttl = 3600  # 缓存过期时间（秒）
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [method]
        for k, v in sorted(kwargs.items()):
            if isinstance(v, str):
                key_parts.append(f"{k}:{v[:100]}")
            else:
                key_parts.append(f"{k}:{str(v)}")
        return ":".join(key_parts)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache:
            return False
        if cache_key not in self._cache_expiry:
            return False
        return time.time() < self._cache_expiry[cache_key]
    
    def _set_cache(self, cache_key: str, value: Any) -> None:
        """设置缓存"""
        self._cache[cache_key] = value
        self._cache_expiry[cache_key] = time.time() + self._cache_ttl
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """获取缓存"""
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        return None
    
    def _clear_cache(self, cache_key: str) -> None:
        """清除缓存"""
        if cache_key in self._cache:
            del self._cache[cache_key]
        if cache_key in self._cache_expiry:
            del self._cache_expiry[cache_key]
        
    async def recognize_skill_intent(
        self,
        db: Session,
        user_input: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """识别技能意图
        
        Args:
            db: 数据库会话
            user_input: 用户输入
            user_id: 用户ID
            
        Returns:
            技能意图识别结果，包含意图类型、置信度等
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("recognize_skill_intent", user_input=user_input, user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 获取可用技能列表
            available_skills = self.skill_registry.get_all_skills(db)
            skill_names = [skill.name for skill in available_skills]
            
            # 构建识别Prompt
            newline = "\n"
            skill_list = newline.join([f"- {skill}" for skill in skill_names])
            
            prompt = f"""
            请分析以下用户输入，识别其是否需要调用技能，以及需要调用哪个技能：
            
            用户输入：{user_input}
            
            可用技能列表：
            {skill_list}
            
            请从以下几个方面进行分析：
            1. 需要调用技能：是/否
            2. 推荐技能：如果需要，推荐一个最匹配的技能
            3. 置信度：推荐的置信度（0-1）
            4. 原因：推荐该技能的原因
            5. 备选技能：如果有多个可能的技能，列出其他备选
            
            请以JSON格式返回分析结果，包含以下字段：
            - needs_skill: 是否需要调用技能
            - recommended_skill: 推荐的技能
            - confidence: 置信度
            - reason: 推荐原因
            - alternative_skills: 备选技能列表
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的技能意图识别专家，擅长分析用户输入并判断是否需要调用技能。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=self.local_model,
                max_tokens=500,
                temperature=0.2,
                db=db
            )
            
            # 解析结果
            intent_result = self._parse_intent_result(result["generated_text"])
            
            # 设置缓存
            self._set_cache(cache_key, intent_result)
            
            return intent_result
        except Exception as e:
            logger.error(f"技能意图识别失败: {e}")
            return {
                "needs_skill": False,
                "recommended_skill": None,
                "confidence": 0.0,
                "reason": "",
                "alternative_skills": []
            }
    
    async def extract_skill_parameters(
        self,
        db: Session,
        user_input: str,
        skill_name: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """提取技能参数
        
        Args:
            db: 数据库会话
            user_input: 用户输入
            skill_name: 技能名称
            user_id: 用户ID
            
        Returns:
            提取的参数，包含参数名称和值
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("extract_skill_parameters", user_input=user_input, skill_name=skill_name, user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 获取技能信息
            skill = self.skill_registry.get_skill_by_name(db, skill_name)
            
            # 构建参数提取Prompt
            prompt = f"""
            请从以下用户输入中提取调用{skill_name}技能所需的参数：
            
            用户输入：{user_input}
            
            请分析用户输入，提取可能的参数值。如果技能需要特定参数，请尝试从输入中识别这些参数。
            
            请以JSON格式返回提取结果，包含以下字段：
            - parameters: 提取的参数字典，键为参数名，值为参数值
            - missing_parameters: 可能缺失的参数列表
            - confidence: 提取的置信度（0-1）
            - notes: 提取过程中的注意事项
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的参数提取专家，擅长从用户输入中提取技能所需的参数。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=self.local_model,
                max_tokens=500,
                temperature=0.2,
                db=db
            )
            
            # 解析结果
            parameters = self._parse_parameters_result(result["generated_text"])
            
            # 设置缓存
            self._set_cache(cache_key, parameters)
            
            return parameters
        except Exception as e:
            logger.error(f"技能参数提取失败: {e}")
            return {
                "parameters": {},
                "missing_parameters": [],
                "confidence": 0.0,
                "notes": ""
            }
    
    async def analyze_execution_result(
        self,
        db: Session,
        skill_name: str,
        execution_result: Any,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """分析执行结果
        
        Args:
            db: 数据库会话
            skill_name: 技能名称
            execution_result: 执行结果
            user_id: 用户ID
            
        Returns:
            分析结果，包含执行状态、错误信息、建议等
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("analyze_execution_result", skill_name=skill_name, execution_result=str(execution_result), user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 构建分析Prompt
            prompt = f"""
            请分析以下技能执行结果：
            
            技能名称：{skill_name}
            执行结果：{str(execution_result)}
            
            请从以下几个方面进行分析：
            1. 执行状态：成功/失败/部分成功
            2. 错误信息：如果失败，提取错误信息
            3. 结果摘要：对执行结果的简要总结
            4. 建议：对用户的后续建议
            5. 置信度：分析的置信度（0-1）
            
            请以JSON格式返回分析结果，包含以下字段：
            - execution_status: 执行状态
            - error_message: 错误信息
            - result_summary: 结果摘要
            - recommendations: 建议
            - confidence: 置信度
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的技能执行结果分析专家，擅长分析技能执行结果并提供建议。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=self.local_model,
                max_tokens=500,
                temperature=0.2,
                db=db
            )
            
            # 解析结果
            analysis = self._parse_analysis_result(result["generated_text"])
            
            # 设置缓存
            self._set_cache(cache_key, analysis)
            
            return analysis
        except Exception as e:
            logger.error(f"执行结果分析失败: {e}")
            return {
                "execution_status": "未知",
                "error_message": "",
                "result_summary": "",
                "recommendations": [],
                "confidence": 0.0
            }
    
    def _parse_intent_result(self, llm_output: str) -> Dict[str, Any]:
        """解析意图识别结果
        
        Args:
            llm_output: LLM输出
            
        Returns:
            解析后的结果字典
        """
        import json
        import re
        
        try:
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', llm_output)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # 尝试直接解析
                return json.loads(llm_output)
        except Exception as e:
            logger.error(f"解析意图识别结果失败: {e}")
            return {
                "needs_skill": False,
                "recommended_skill": None,
                "confidence": 0.0,
                "reason": "",
                "alternative_skills": []
            }
    
    def _parse_parameters_result(self, llm_output: str) -> Dict[str, Any]:
        """解析参数提取结果
        
        Args:
            llm_output: LLM输出
            
        Returns:
            解析后的结果字典
        """
        import json
        import re
        
        try:
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', llm_output)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # 尝试直接解析
                return json.loads(llm_output)
        except Exception as e:
            logger.error(f"解析参数提取结果失败: {e}")
            return {
                "parameters": {},
                "missing_parameters": [],
                "confidence": 0.0,
                "notes": ""
            }
    
    def _parse_analysis_result(self, llm_output: str) -> Dict[str, Any]:
        """解析执行结果分析结果
        
        Args:
            llm_output: LLM输出
            
        Returns:
            解析后的结果字典
        """
        import json
        import re
        
        try:
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', llm_output)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # 尝试直接解析
                return json.loads(llm_output)
        except Exception as e:
            logger.error(f"解析执行结果分析失败: {e}")
            return {
                "execution_status": "未知",
                "error_message": "",
                "result_summary": "",
                "recommendations": [],
                "confidence": 0.0
            }
    
    async def batch_recognize_skill_intent(
        self,
        db: Session,
        user_inputs: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        批量识别技能意图
        
        Args:
            db: 数据库会话
            user_inputs: 用户输入列表
            user_id: 用户ID
            
        Returns:
            意图识别结果列表
        """
        results = []
        
        # 处理每个用户输入
        for user_input in user_inputs:
            try:
                # 检查缓存
                cache_key = self._get_cache_key("recognize_skill_intent", user_input=user_input, user_id=user_id)
                cached_result = self._get_cache(cache_key)
                
                if cached_result:
                    results.append(cached_result)
                else:
                    # 调用单个识别方法
                    result = await self.recognize_skill_intent(db, user_input, user_id)
                    results.append(result)
            except Exception as e:
                logger.error(f"批量识别技能意图失败: {e}")
                results.append({
                    "needs_skill": False,
                    "recommended_skill": None,
                    "confidence": 0.0,
                    "reason": "",
                    "alternative_skills": []
                })
        
        return results
    
    async def batch_extract_skill_parameters(
        self,
        db: Session,
        user_inputs: List[str],
        skill_names: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        批量提取技能参数
        
        Args:
            db: 数据库会话
            user_inputs: 用户输入列表
            skill_names: 技能名称列表
            user_id: 用户ID
            
        Returns:
            参数提取结果列表
        """
        results = []
        
        # 确保输入列表长度一致
        min_length = min(len(user_inputs), len(skill_names))
        
        # 处理每个用户输入和技能名称对
        for i in range(min_length):
            user_input = user_inputs[i]
            skill_name = skill_names[i]
            
            try:
                # 检查缓存
                cache_key = self._get_cache_key("extract_skill_parameters", user_input=user_input, skill_name=skill_name, user_id=user_id)
                cached_result = self._get_cache(cache_key)
                
                if cached_result:
                    results.append(cached_result)
                else:
                    # 调用单个提取方法
                    result = await self.extract_skill_parameters(db, user_input, skill_name, user_id)
                    results.append(result)
            except Exception as e:
                logger.error(f"批量提取技能参数失败: {e}")
                results.append({
                    "parameters": {},
                    "missing_parameters": [],
                    "confidence": 0.0,
                    "notes": ""
                })
        
        return results
