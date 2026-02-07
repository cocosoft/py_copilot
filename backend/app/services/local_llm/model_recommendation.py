from typing import Dict, Any, List, Optional
from app.services.llm_service import LLMService
from app.services.model_query_service import ModelQueryService
from app.core.database import get_db
from sqlalchemy.orm import Session
import logging
import time

logger = logging.getLogger(__name__)


class LocalModelRecommendationService:
    """本地模型推荐服务"""
    
    def __init__(self):
        """初始化本地模型推荐服务"""
        self.llm_service = LLMService()
        self.model_query_service = ModelQueryService()
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
        
    async def evaluate_model_capability(
        self,
        db: Session,
        model_name: str,
        task_description: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """评估模型能力
        
        Args:
            db: 数据库会话
            model_name: 模型名称
            task_description: 任务描述
            user_id: 用户ID
            
        Returns:
            模型能力评估结果，包含适合度、优势、劣势等
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("evaluate_model_capability", model_name=model_name, task_description=task_description, user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 构建评估Prompt
            prompt = f"""
            请评估以下模型是否适合完成指定任务：
            
            模型名称：{model_name}
            任务描述：{task_description}
            
            请从以下几个方面进行评估：
            1. 适合度：模型对该任务的适合程度（1-5，5最高）
            2. 优势：模型在该任务上的优势
            3. 劣势：模型在该任务上的劣势
            4. 建议参数：推荐的模型参数设置
            5. 备选模型：如果该模型不适合，推荐的备选模型
            
            请以JSON格式返回评估结果，包含以下字段：
            - suitability: 适合度
            - strengths: 优势列表
            - weaknesses: 劣势列表
            - recommended_parameters: 推荐参数
            - alternative_models: 备选模型列表
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的模型评估专家，擅长评估不同模型对特定任务的适合程度。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=self.local_model,
                max_tokens=500,
                temperature=0.2,
                db=db
            )
            
            # 解析结果
            evaluation = self._parse_evaluation_result(result["generated_text"])
            
            # 设置缓存
            self._set_cache(cache_key, evaluation)
            
            return evaluation
        except Exception as e:
            logger.error(f"模型能力评估失败: {e}")
            return {
                "suitability": 3,
                "strengths": [],
                "weaknesses": [],
                "recommended_parameters": {},
                "alternative_models": []
            }
    
    async def optimize_model_parameters(
        self,
        db: Session,
        model_name: str,
        task_type: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """优化模型参数
        
        Args:
            db: 数据库会话
            model_name: 模型名称
            task_type: 任务类型
            user_id: 用户ID
            
        Returns:
            优化后的模型参数配置
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("optimize_model_parameters", model_name=model_name, task_type=task_type, user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 构建优化Prompt
            prompt = f"""
            请为以下模型针对指定任务类型优化参数配置：
            
            模型名称：{model_name}
            任务类型：{task_type}
            
            请从以下几个方面优化参数：
            1. temperature: 温度参数
            2. max_tokens: 最大生成长度
            3. top_p: 采样参数
            4. frequency_penalty: 频率惩罚
            5. presence_penalty: 存在惩罚
            6. 其他相关参数：如果有其他相关参数，请一并优化
            
            请以JSON格式返回优化结果，包含以下字段：
            - temperature: 温度参数
            - max_tokens: 最大生成长度
            - top_p: 采样参数
            - frequency_penalty: 频率惩罚
            - presence_penalty: 存在惩罚
            - other_parameters: 其他参数
            - explanation: 优化解释
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的模型参数优化专家，擅长为不同模型和任务类型优化参数配置。"},
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
            logger.error(f"模型参数优化失败: {e}")
            return {
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "other_parameters": {},
                "explanation": "使用默认参数配置"
            }
    
    async def analyze_performance_data(
        self,
        db: Session,
        model_name: str,
        performance_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """分析性能数据
        
        Args:
            db: 数据库会话
            model_name: 模型名称
            performance_data: 性能数据
            user_id: 用户ID
            
        Returns:
            性能分析结果，包含瓶颈、优化建议等
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("analyze_performance_data", model_name=model_name, performance_data=str(performance_data), user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 构建分析Prompt
            prompt = f"""
            请分析以下模型的性能数据：
            
            模型名称：{model_name}
            性能数据：{str(performance_data)}
            
            请从以下几个方面进行分析：
            1. 性能瓶颈：识别主要的性能瓶颈
            2. 优化建议：针对瓶颈提供具体的优化建议
            3. 性能评分：对模型性能进行评分（1-5，5最高）
            4. 预期提升：优化后预期的性能提升
            5. 监控建议：建议监控的关键指标
            
            请以JSON格式返回分析结果，包含以下字段：
            - performance_bottlenecks: 性能瓶颈列表
            - optimization_suggestions: 优化建议列表
            - performance_score: 性能评分
            - expected_improvement: 预期提升
            - monitoring_suggestions: 监控建议列表
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的性能分析专家，擅长分析模型性能数据并提供优化建议。"},
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
            logger.error(f"性能数据解析失败: {e}")
            return {
                "performance_bottlenecks": [],
                "optimization_suggestions": [],
                "performance_score": 3,
                "expected_improvement": "中等",
                "monitoring_suggestions": []
            }
    
    def _parse_evaluation_result(self, llm_output: str) -> Dict[str, Any]:
        """解析模型能力评估结果
        
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
            logger.error(f"解析模型能力评估结果失败: {e}")
            return {
                "suitability": 3,
                "strengths": [],
                "weaknesses": [],
                "recommended_parameters": {},
                "alternative_models": []
            }
    
    def _parse_parameters_result(self, llm_output: str) -> Dict[str, Any]:
        """解析模型参数优化结果
        
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
            logger.error(f"解析模型参数优化结果失败: {e}")
            return {
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "other_parameters": {},
                "explanation": "使用默认参数配置"
            }
    
    def _parse_analysis_result(self, llm_output: str) -> Dict[str, Any]:
        """解析性能数据分析结果
        
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
            logger.error(f"解析性能数据分析结果失败: {e}")
            return {
                "performance_bottlenecks": [],
                "optimization_suggestions": [],
                "performance_score": 3,
                "expected_improvement": "中等",
                "monitoring_suggestions": []
            }
    
    async def batch_evaluate_model_capability(
        self,
        db: Session,
        model_names: List[str],
        task_descriptions: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        批量评估模型能力
        
        Args:
            db: 数据库会话
            model_names: 模型名称列表
            task_descriptions: 任务描述列表
            user_id: 用户ID
            
        Returns:
            模型能力评估结果列表
        """
        results = []
        
        # 确保输入列表长度一致
        min_length = min(len(model_names), len(task_descriptions))
        
        # 处理每个模型和任务对
        for i in range(min_length):
            model_name = model_names[i]
            task_description = task_descriptions[i]
            
            try:
                # 检查缓存
                cache_key = self._get_cache_key("evaluate_model_capability", model_name=model_name, task_description=task_description, user_id=user_id)
                cached_result = self._get_cache(cache_key)
                
                if cached_result:
                    results.append(cached_result)
                else:
                    # 调用单个评估方法
                    result = await self.evaluate_model_capability(db, model_name, task_description, user_id)
                    results.append(result)
            except Exception as e:
                logger.error(f"批量评估模型能力失败: {e}")
                results.append({
                    "suitability": 3,
                    "strengths": [],
                    "weaknesses": [],
                    "recommended_parameters": {},
                    "alternative_models": []
                })
        
        return results
    
    async def batch_optimize_model_parameters(
        self,
        db: Session,
        model_names: List[str],
        task_types: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        批量优化模型参数
        
        Args:
            db: 数据库会话
            model_names: 模型名称列表
            task_types: 任务类型列表
            user_id: 用户ID
            
        Returns:
            模型参数优化结果列表
        """
        results = []
        
        # 确保输入列表长度一致
        min_length = min(len(model_names), len(task_types))
        
        # 处理每个模型和任务类型对
        for i in range(min_length):
            model_name = model_names[i]
            task_type = task_types[i]
            
            try:
                # 检查缓存
                cache_key = self._get_cache_key("optimize_model_parameters", model_name=model_name, task_type=task_type, user_id=user_id)
                cached_result = self._get_cache(cache_key)
                
                if cached_result:
                    results.append(cached_result)
                else:
                    # 调用单个优化方法
                    result = await self.optimize_model_parameters(db, model_name, task_type, user_id)
                    results.append(result)
            except Exception as e:
                logger.error(f"批量优化模型参数失败: {e}")
                results.append({
                    "temperature": 0.7,
                    "max_tokens": 1024,
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "other_parameters": {},
                    "explanation": "使用默认参数配置"
                })
        
        return results
