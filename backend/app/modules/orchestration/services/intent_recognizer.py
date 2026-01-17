from typing import Dict, Any
from app.services.llm_service import LLMService
import json
import logging
import time


class IntentRecognizer:
    """
    意图识别器类
    负责识别用户输入的意图类型
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        # 定义支持的意图类型
        self.supported_intents = {
            "simple_qa": "简单问答",
            "knowledge_query": "知识库查询",
            "web_search": "网页搜索",
            "complex_task": "复杂任务",
            "translation": "翻译",
            "code_generation": "代码生成",
            "sentiment_analysis": "情感分析",
            "workflow_request": "工作流请求",
            "entity_extraction": "实体提取",
            "summarization": "文本摘要",
            "planning": "任务规划",
            "calculation": "数学计算",
            "definition": "概念定义",
            "comparison": "比较分析",
            "recommendation": "推荐建议",
            "instruction_following": "指令执行",
            "troubleshooting": "问题排查",
            "explanation": "解释说明"
        }
        # 意图识别缓存
        self.intent_cache = {}  # 缓存格式: {input_text: (intent_result, timestamp)}
        self.cache_ttl = 3600  # 缓存有效期（秒）
    
    async def recognize_intent(
        self, 
        user_input: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        识别用户输入的意图
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息（可选）
            
        Returns:
            意图识别结果，格式为：
            {
                "type": 意图类型,
                "confidence": 置信度（0-1）,
                "params": 意图参数,
                "context_used": 是否使用了上下文信息
            }
        """
        try:
            # 检查缓存
            cache_key = f"{user_input[:500]}_{str(context)[:200]}" if context else user_input[:500]
            current_time = time.time()
            
            if cache_key in self.intent_cache:
                cached_result, cached_time = self.intent_cache[cache_key]
                if current_time - cached_time < self.cache_ttl:
                    logging.info(f"使用缓存的意图识别结果: {cached_result['type']}")
                    # 添加上下文使用标记
                    cached_result["context_used"] = "context" in cached_result
                    return cached_result
                else:
                    # 缓存过期，删除
                    del self.intent_cache[cache_key]
            
            # 构建意图识别提示词
            prompt = self._build_intent_prompt(user_input, context)
            
            # 使用大模型进行意图识别
            result = await self.llm_service.chat_completion(
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的意图识别专家，请根据用户输入和上下文准确识别意图类型。"
                    },
                    {"role": "user", "content": prompt}
                ],
                model_name="gpt-3.5-turbo",
                max_tokens=300,  # 增加最大令牌数以支持更详细的参数提取
                temperature=0.1
            )
            
            # 解析大模型返回的结果
            intent_result = self._parse_intent_result(result["generated_text"])
            
            # 验证意图类型是否支持
            if intent_result["type"] not in self.supported_intents:
                # 如果返回的意图类型不支持，尝试二次识别
                logging.warning(f"意图类型不支持: {intent_result['type']}")
                # 使用更严格的提示词重新识别
                strict_prompt = self._build_strict_intent_prompt(user_input, context)
                strict_result = await self.llm_service.chat_completion(
                    messages=[{"role": "user", "content": strict_prompt}],
                    model_name="gpt-3.5-turbo",
                    max_tokens=100,
                    temperature=0.0
                )
                strict_intent = self._parse_intent_result(strict_result["generated_text"])
                
                if strict_intent["type"] in self.supported_intents:
                    intent_result = strict_intent
                else:
                    # 如果二次识别仍然不支持，默认使用simple_qa
                    intent_result["type"] = "simple_qa"
                    intent_result["confidence"] = 0.5
            
            # 增强参数提取
            if not intent_result.get("params"):
                intent_result["params"] = await self._extract_intent_params(
                    user_input, 
                    intent_result["type"]
                )
            
            # 添加上下文使用标记
            intent_result["context_used"] = bool(context and "conversation_history" in context)
            
            # 缓存结果
            self.intent_cache[cache_key] = (intent_result, current_time)
            
            return intent_result
            
        except Exception as e:
            # 如果意图识别失败，返回默认结果
            logging.error(f"意图识别失败: {str(e)}")
            return {
                "type": "simple_qa",
                "confidence": 0.3,
                "params": {},
                "context_used": False
            }
    
    def _build_intent_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        构建意图识别提示词
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息（可选）
            
        Returns:
            构建好的提示词
        """
        # 构建意图类型列表
        intent_list = []
        for intent_type, description in self.supported_intents.items():
            intent_list.append(f"- {intent_type}: {description}")
        
        # 构建上下文信息
        context_info = ""
        if context and "conversation_history" in context and context["conversation_history"]:
            recent_context = "\n".join([
                f"- {item['content'][:100]}..." 
                for item in context["conversation_history"][-3:]
            ])
            context_info = f"\n\n对话上下文：\n{recent_context}"
        
        # 构建提示词
        prompt = f"""
        请识别以下用户输入的意图类型：
        用户输入：{user_input}{context_info}
        
        支持的意图类型：
        {"\n".join(intent_list)}
        
        请以JSON格式返回结果，包含以下字段：
        - type: 意图类型（必须是上述支持的类型之一）
        - confidence: 置信度（0-1之间的数字，表示识别的确定程度）
        - params: 意图参数（可选，根据意图类型提取的关键参数）
        
        示例：
        {{"type": "simple_qa", "confidence": 0.95, "params": {{}}}}
        {{"type": "translation", "confidence": 0.9, "params": {{"source_language": "中文", "target_language": "英文"}}}}
        
        请确保返回的是有效的JSON格式，不要包含任何其他解释或说明。
        """
        
        return prompt
    
    def _parse_intent_result(self, llm_output: str) -> Dict[str, Any]:
        """
        解析大模型返回的意图识别结果
        
        Args:
            llm_output: 大模型返回的文本
            
        Returns:
            解析后的意图识别结果
        """
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'\{[^}]*\}', llm_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # 如果没有找到JSON格式，尝试直接解析
                return json.loads(llm_output)
        except json.JSONDecodeError as e:
            # 如果JSON解析失败，记录错误并返回默认结果
            logging.error(f"解析意图识别结果失败: {str(e)}")
            return {
                "type": "simple_qa",
                "confidence": 0.3,
                "params": {}
            }
        except Exception as e:
            # 其他错误处理
            logging.error(f"解析意图识别结果失败: {str(e)}")
            return {
                "type": "simple_qa",
                "confidence": 0.3,
                "params": {}
            }
    
    def _build_strict_intent_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        构建更严格的意图识别提示词
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息（可选）
            
        Returns:
            构建好的严格提示词
        """
        # 只提供最基本的意图类型列表
        basic_intents = [
            "simple_qa", "knowledge_query", "web_search", "complex_task", 
            "translation", "code_generation", "sentiment_analysis", "workflow_request"
        ]
        
        intent_list = [f"- {intent}" for intent in basic_intents]
        
        # 构建上下文信息（如果有）
        context_info = ""
        if context and "conversation_history" in context and context["conversation_history"]:
            recent_context = "\n".join([
                f"- {item['content'][:50]}..." 
                for item in context["conversation_history"][-2:]
            ])
            context_info = f"\n\n简要上下文：\n{recent_context}"
        
        # 构建严格提示词
        prompt = f"""
        请从以下列表中选择最匹配的意图类型：
        用户输入：{user_input[:200]}...{context_info}
        
        可用意图类型：
        {"\n".join(intent_list)}
        
        请仅返回意图类型名称，不要添加任何其他内容。
        示例：simple_qa
        """
        
        return prompt
    
    async def _extract_intent_params(self, user_input: str, intent_type: str) -> Dict[str, Any]:
        """
        增强参数提取
        
        Args:
            user_input: 用户输入文本
            intent_type: 意图类型
            
        Returns:
            提取的参数
        """
        try:
            # 根据不同的意图类型构建不同的参数提取提示词
            param_prompts = {
                "translation": {
                    "system": "你是一个专业的翻译参数提取器，请从用户输入中提取源语言、目标语言和要翻译的文本。",
                    "user": f"请从以下文本中提取翻译参数：{user_input}"
                },
                "knowledge_query": {
                    "system": "你是一个专业的知识库查询参数提取器，请从用户输入中提取查询关键词、实体和相关概念。",
                    "user": f"请从以下文本中提取知识库查询参数：{user_input}"
                },
                "complex_task": {
                    "system": "你是一个专业的复杂任务参数提取器，请从用户输入中提取任务目标、子任务和所需资源。",
                    "user": f"请从以下文本中提取复杂任务参数：{user_input}"
                },
                "code_generation": {
                    "system": "你是一个专业的代码生成参数提取器，请从用户输入中提取编程语言、功能需求和约束条件。",
                    "user": f"请从以下文本中提取代码生成参数：{user_input}"
                }
            }
            
            # 如果没有特定的参数提取提示词，使用通用的
            if intent_type not in param_prompts:
                param_prompts[intent_type] = {
                    "system": "你是一个专业的参数提取器，请从用户输入中提取与意图相关的关键参数。",
                    "user": f"请从以下文本中提取与{intent_type}相关的参数：{user_input}"
                }
            
            # 使用大模型提取参数
            prompt = param_prompts[intent_type]
            result = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                model_name="gpt-3.5-turbo",
                max_tokens=200,
                temperature=0.1
            )
            
            # 解析参数结果
            params = json.loads(result["generated_text"])
            
            return params
            
        except Exception as e:
            # 如果参数提取失败，返回空字典
            logging.error(f"参数提取失败: {str(e)}")
            return {}
