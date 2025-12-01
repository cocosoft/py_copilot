"""LLM任务处理服务模块"""
import time
from typing import Dict, Any, List, Optional, Union
import logging

from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class LLMTasks:
    """LLM任务处理服务类"""
    
    def __init__(self, llm_service=None):
        """初始化LLM任务处理服务"""
        from app.services.llm_service import llm_service as default_llm_service
        self.llm_service = llm_service or default_llm_service
    
    def summarize_text(self, text: str, **options) -> Dict[str, Any]:
        """
        文本摘要功能
        
        Args:
            text: 需要摘要的文本
            options: 可选参数
                - max_length: 摘要的最大长度（token）
                - min_length: 摘要的最小长度（token）
                - model_name: 使用的模型名称
                - language: 摘要语言（'zh', 'en'等）
        
        Returns:
            包含摘要结果和元数据的字典
        """
        # 输入验证
        if not isinstance(text, str) or not text.strip():
            return {"error": "文本不能为空", "success": False}
            
        start_time = time.time()
        
        max_length = options.get('max_length', 150)
        min_length = options.get('min_length', 30)
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        language = options.get('language', 'zh')
        
        # 验证参数
        if not isinstance(max_length, int) or max_length <= 0:
            max_length = 150
        if not isinstance(min_length, int) or min_length <= 0:
            min_length = 30
        if min_length > max_length:
            min_length, max_length = max_length, min_length
        
        language = str(language).lower()
        if language not in ['zh', 'en']:
            language = 'zh'
        
        # 构建摘要提示词
        if language == 'zh':
            prompt = f"请为以下文本生成一个简洁的摘要，长度在{min_length}到{max_length}个token之间：\n\n{text}"
        else:
            prompt = f"Please provide a concise summary of the following text, between {min_length} and {max_length} tokens:\n\n{text}"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的文本摘要助手。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=max_length + 100  # 留出额外空间
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"文本摘要失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": f"这是一个模拟的文本摘要。原始文本长度约为{len(text)}个字符。",
                    "model": f"{model_name} (simulation)",
                    "tokens_used": len(text.split()) // 3,
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def generate_code(self, text: str, **options) -> Dict[str, Any]:
        """
        代码生成功能
        
        Args:
            text: 代码生成的描述
            options: 可选参数
                - language: 代码语言（'python', 'javascript', 'java'等）
                - model_name: 使用的模型名称
                - explain: 是否包含代码解释（布尔值）
        
        Returns:
            包含生成代码和元数据的字典
        """
        # 输入验证
        if not isinstance(text, str) or not text.strip():
            return {"error": "代码需求描述不能为空", "success": False}
            
        start_time = time.time()
        
        language = options.get('language', 'python')
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        explain = options.get('explain', True)
        
        # 验证参数
        if not isinstance(language, str) or not language.strip():
            language = 'python'
        if not isinstance(explain, bool):
            explain = True
        
        # 构建代码生成提示词
        explain_text = "请同时提供代码的详细解释。" if explain else ""
        prompt = f"请根据以下描述生成{language}代码：\n\n{text}\n\n{explain_text}\n\n请确保代码是正确的、可运行的，并且有适当的注释。"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的编程助手，能够生成高质量的代码。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=1000,
                temperature=0.3  # 较低的温度以确保代码的准确性
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"代码生成失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": f"这是一个模拟的{language}代码生成结果。\n\ndef example_function():\n    print('Hello, this is generated code for: {text[:50]}...')",
                    "model": f"{model_name} (simulation)",
                    "tokens_used": 150,
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def translate_text(self, text: str, **options) -> Dict[str, Any]:
        """
        文本翻译功能
        
        Args:
            text: 需要翻译的文本
            options: 可选参数
                - target_language: 目标语言（'zh', 'en', 'ja'等）
                - source_language: 源语言（默认为自动检测）
                - model_name: 使用的模型名称
        
        Returns:
            包含翻译结果和元数据的字典
        """
        # 输入验证
        if not isinstance(text, str) or not text.strip():
            return {"error": "需要翻译的文本不能为空", "success": False}
            
        start_time = time.time()
        
        target_language = options.get('target_language', 'en')
        source_language = options.get('source_language', 'auto')
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        
        # 验证参数
        if not isinstance(target_language, str) or not target_language.strip():
            target_language = 'en'
        if not isinstance(source_language, str) or not source_language.strip():
            source_language = 'auto'
        
        # 语言名称映射
        language_names = {
            'zh': '中文',
            'en': '英文',
            'ja': '日语',
            'ko': '韩语',
            'fr': '法语',
            'de': '德语',
            'es': '西班牙语',
            'ru': '俄语'
        }
        
        target_name = language_names.get(target_language, target_language)
        source_text = f"从{language_names.get(source_language, source_language)}" if source_language != 'auto' else "从自动检测的语言"
        
        # 构建翻译提示词
        prompt = f"请将以下文本{source_text}翻译成{target_name}：\n\n{text}\n\n请只返回翻译结果，不要添加额外的解释。"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译助手。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=len(text.split()) * 2,  # 留出足够的翻译空间
                temperature=0.1  # 较低的温度以确保翻译准确性
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"文本翻译失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": f"[Simulated translation to {target_name}] This is a simulation of translated text.",
                    "model": f"{model_name} (simulation)",
                    "tokens_used": len(text.split()),
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def analyze_sentiment(self, text: str, **options) -> Dict[str, Any]:
        """
        情感分析功能
        
        Args:
            text: 需要分析情感的文本
            options: 可选参数
                - model_name: 使用的模型名称
                - detailed: 是否返回详细的情感分析（布尔值）
        
        Returns:
            包含情感分析结果和元数据的字典
        """
        # 输入验证
        if not isinstance(text, str) or not text.strip():
            return {"error": "需要分析的文本不能为空", "success": False}
            
        start_time = time.time()
        
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        detailed = options.get('detailed', True)
        
        # 验证参数
        if not isinstance(detailed, bool):
            detailed = True
        
        # 构建情感分析提示词
        detailed_text = "请提供详细的情感分析，包括主要情感类别、情感强度（0-100）以及关键情感词的分析。" if detailed else "请简单判断情感倾向。"
        prompt = f"请对以下文本进行情感分析：\n\n{text}\n\n{detailed_text}\n\n请以JSON格式返回结果，包含'sentiment'（'positive', 'negative', 'neutral'）、'score'（0-100）和'analysis'（分析文本）字段。"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的情感分析助手。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=500,
                temperature=0.1
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"情感分析失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": '{"sentiment": "neutral", "score": 50, "analysis": "这是一个模拟的情感分析结果。"}',
                    "model": f"{model_name} (simulation)",
                    "tokens_used": 80,
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def generate_ideas(self, topic: str, **options) -> Dict[str, Any]:
        """
        创意生成功能
        
        Args:
            topic: 创意生成的主题
            options: 可选参数
                - count: 生成的创意数量
                - model_name: 使用的模型名称
                - creative_level: 创意程度（1-5）
        
        Returns:
            包含创意列表和元数据的字典
        """
        # 输入验证
        if not isinstance(topic, str) or not topic.strip():
            return {"error": "创意主题不能为空", "success": False}
            
        start_time = time.time()
        
        count = options.get('count', 5)
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        creative_level = options.get('creative_level', 3)
        
        # 验证参数
        if not isinstance(count, int) or count <= 0:
            count = 5
        if count > 20:
            count = 20  # 限制最大创意数量
        if not isinstance(creative_level, int) or creative_level < 1:
            creative_level = 1
        if creative_level > 5:
            creative_level = 5
        
        # 根据创意程度调整temperature
        temperature = 0.3 + (creative_level * 0.14)  # 0.3到1.0之间
        
        # 构建创意生成提示词
        prompt = f"请为主题'{topic}'生成{count}个创意想法，每个想法简要描述，使用数字列表格式。"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个创意十足的助手，擅长生成新颖独特的想法。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=1000,
                temperature=temperature
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"创意生成失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                ideas_list = [f"创意 {i+1}: 关于'{topic}'的模拟创意内容" for i in range(count)]
                return {
                    "result": "\n".join(ideas_list),
                    "model": f"{model_name} (simulation)",
                    "tokens_used": 100 + (count * 20),
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def answer_question(self, text: str, **options) -> Dict[str, Any]:
        """
        问答功能
        
        Args:
            text: 包含问题的文本
            options: 可选参数
                - context: 上下文信息（可选）
                - model_name: 使用的模型名称
                - detailed: 是否需要详细回答
        
        Returns:
            包含答案和元数据的字典
        """
        start_time = time.time()
        
        context = options.get('context', '')
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        detailed = options.get('detailed', True)
        
        # 构建问答提示词
        context_text = f"基于以下上下文信息：\n\n{context}\n\n" if context else ""
        detailed_text = "请提供详细、全面的回答。" if detailed else "请提供简洁明了的回答。"
        
        prompt = f"{context_text}请回答以下问题：\n\n{text}\n\n{detailed_text}"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个知识渊博的问答助手，能够基于提供的信息准确回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=1000,
                temperature=0.3
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"问答失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": f"这是一个模拟的问题回答。\n\n问题: {text[:50]}...",
                    "model": f"{model_name} (simulation)",
                    "tokens_used": 120,
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def generate_content(self, topic: str, **options) -> Dict[str, Any]:
        """
        内容生成功能
        
        Args:
            topic: 内容生成的主题
            options: 可选参数
                - type: 内容类型（'article', 'email', 'report', 'story'等）
                - length: 内容长度（'short', 'medium', 'long'）
                - model_name: 使用的模型名称
                - tone: 内容语气（'formal', 'casual', 'professional'等）
        
        Returns:
            包含生成内容和元数据的字典
        """
        start_time = time.time()
        
        content_type = options.get('type', 'article')
        length = options.get('length', 'medium')
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        tone = options.get('tone', 'professional')
        
        # 长度映射
        length_map = {
            "short": "200-500字",
            "medium": "500-1000字",
            "long": "1000-2000字"
        }
        
        # 构建内容生成提示词
        prompt = f"请生成一篇关于'{topic}'的{content_type}，长度约{length_map.get(length, 'medium')}，语气要{tone}，内容要详实、有深度。"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": f"你是一个专业的内容创作者，擅长生成各种类型和风格的内容。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=2000 if length == 'long' else 1000,
                temperature=0.7
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"内容生成失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": f"这是一篇关于'{topic}'的{content_type}（模拟生成）。\n\n{topic}是一个重要的主题，在当今社会具有广泛的影响..." * 3,
                    "model": f"{model_name} (simulation)",
                    "tokens_used": 500,
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def correct_grammar(self, text: str, **options) -> Dict[str, Any]:
        """
        语法纠正功能
        
        Args:
            text: 需要纠正的文本
            options: 可选参数
                - language: 文本语言
                - model_name: 使用的模型名称
                - explain: 是否提供错误解释
        
        Returns:
            包含纠正结果和元数据的字典
        """
        # 输入验证
        if not isinstance(text, str) or not text.strip():
            return {"error": "需要纠正的文本不能为空", "success": False}
            
        start_time = time.time()
        
        language = options.get('language', '中文')
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        explain = options.get('explain', False)
        
        # 验证参数
        if not isinstance(explain, bool):
            explain = False
        if not isinstance(language, str) or not language.strip():
            language = '中文'
        
        # 构建语法纠正提示词
        explain_text = "请同时解释修改的内容和原因。" if explain else "请只返回纠正后的完整文本。"
        prompt = f"请纠正以下{language}文本中的语法、拼写和标点错误：\n\n{text}\n\n{explain_text}"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的语言教师，擅长纠正各种语言的语法错误。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=len(text.split()) * 2,
                temperature=0.1
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"语法纠正失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": f"[模拟纠正]{text}",
                    "model": f"{model_name} (simulation)",
                    "tokens_used": len(text.split()),
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def create_conversation(self, **options) -> Dict[str, Any]:
        """
        创建对话功能
        
        Args:
            options: 可选参数
                - system_role: 系统角色（'general_assistant', 'teacher', 'programmer'等）
                - model_name: 使用的模型名称
        
        Returns:
            包含对话ID和系统提示的字典
        """
        import uuid
        start_time = time.time()
        
        system_role = options.get('system_role', 'general_assistant')
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        
        # 角色提示映射
        role_prompts = {
            'general_assistant': '你是一个通用助手，能够回答各种问题并提供帮助。',
            'teacher': '你是一位知识渊博的教师，擅长解释复杂概念。',
            'programmer': '你是一位经验丰富的程序员，擅长解决编程问题。',
            'creative_writer': '你是一位富有创造力的作家，擅长撰写各类内容。'
        }
        
        system_prompt = role_prompts.get(system_role, role_prompts['general_assistant'])
        conversation_id = str(uuid.uuid4())
        
        try:
            # 记录对话创建
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "conversation_id": conversation_id,
                "system_prompt": system_prompt,
                "model": model_name,
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"创建对话失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "conversation_id": conversation_id,
                    "system_prompt": system_prompt,
                    "model": f"{model_name} (simulation)",
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def process_conversation(self, messages: List[Dict[str, str]], **options) -> Dict[str, Any]:
        """
        处理对话功能
        
        Args:
            messages: 对话消息列表，每个消息包含role和content
            options: 可选参数
                - model_name: 使用的模型名称
                - max_tokens: 最大token数
        
        Returns:
            包含回复内容和元数据的字典
        """
        # 输入验证
        if not isinstance(messages, list) or not messages:
            return {"error": "对话消息列表不能为空", "success": False}
            
        start_time = time.time()
        
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        max_tokens = options.get('max_tokens', 4000)
        
        # 验证参数
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            max_tokens = 4000
        
        # 确保消息格式正确
        if not all(isinstance(msg, dict) and 'role' in msg and 'content' in msg for msg in messages):
            return {"error": "消息格式不正确，每个消息必须是包含role和content字段的字典", "success": False}
            
        # 验证角色和内容
        valid_roles = ['system', 'user', 'assistant']
        for msg in messages:
            if msg['role'] not in valid_roles:
                return {"error": f"无效的消息角色: {msg['role']}，有效角色为: {', '.join(valid_roles)}", "success": False}
            if not isinstance(msg['content'], str) or not msg['content'].strip():
                return {"error": "消息内容不能为空", "success": False}
        
        # 如果没有系统消息，添加默认的
        has_system_message = any(msg["role"] == "system" for msg in messages)
        if not has_system_message:
            messages.insert(0, {"role": "system", "content": "你是一个通用助手，能够回答各种问题并提供帮助。"})
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=messages,
                model_name=model_name,
                max_tokens=1000
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"处理对话失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": "这是一个模拟的对话回复。",
                    "model": f"{model_name} (simulation)",
                    "tokens_used": 50,
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def paraphrase_text(self, text: str, **options) -> Dict[str, Any]:
        """
        文本改写功能
        
        Args:
            text: 需要改写的文本
            options: 可选参数
                - model_name: 使用的模型名称
                - style: 改写风格（'formal', 'casual', 'creative'等）
        
        Returns:
            包含改写结果和元数据的字典
        """
        start_time = time.time()
        
        # 输入验证
        if not isinstance(text, str) or not text.strip():
            return {"error": "需要改写的文本不能为空", "success": False}
        
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        style = options.get('style', 'formal')
        
        # 验证参数
        if not isinstance(style, str) or not style.strip():
            style = 'formal'
        
        # 构建改写提示词
        prompt = f"请用{style}风格改写以下文本，保持原文意思不变：\n\n{text}"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的文本改写助手，擅长保持原意的同时改变表达方式。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=len(text.split()) * 2,
                temperature=0.7
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"文本改写失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                return {
                    "result": f"[模拟改写 ({style})]{text}",
                    "model": f"{model_name} (simulation)",
                    "tokens_used": len(text.split()),
                    "execution_time_ms": round(execution_time, 2),
                    "success": True
                }
            return {"error": str(e), "success": False}
    
    def classify_text(self, text: str, **options) -> Dict[str, Any]:
        """
        文本分类功能
        
        Args:
            text: 需要分类的文本
            options: 可选参数
                - categories: 分类类别列表
                - model_name: 使用的模型名称
                - multi_label: 是否允许多标签分类
        
        Returns:
            包含分类结果和元数据的字典
        """
        start_time = time.time()
        
        # 输入验证
        if not isinstance(text, str) or not text.strip():
            return {"error": "需要分类的文本不能为空", "success": False}
        
        categories = options.get('categories', ['体育', '科技', '娱乐', '财经', '教育', '其他'])
        model_name = options.get('model_name', 'gpt-3.5-turbo')
        multi_label = options.get('multi_label', False)
        
        # 验证参数
        if not isinstance(categories, list) or not categories:
            categories = ['体育', '科技', '娱乐', '财经', '教育', '其他']
        # 确保categories中的每个元素都是字符串
        categories = [str(cat).strip() for cat in categories if str(cat).strip()]
        if not categories:
            categories = ['其他']
        
        if not isinstance(multi_label, bool):
            multi_label = False
        
        # 构建分类提示词
        categories_text = ", ".join(categories)
        multi_label_text = "可以选择多个类别" if multi_label else "只能选择一个最符合的类别"
        
        prompt = f"请将以下文本分类到指定类别中：\n\n文本：{text}\n\n类别：{categories_text}\n\n{multi_label_text}。请以JSON格式返回结果，包含'categories'字段，值为分类结果数组。" if multi_label else f"请将以下文本分类到指定类别中：\n\n文本：{text}\n\n类别：{categories_text}\n\n{multi_label_text}。请以JSON格式返回结果，包含'category'字段，值为分类结果。"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的文本分类助手，擅长根据给定类别对文本进行准确分类。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=model_name,
                max_tokens=500,
                temperature=0.1
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "execution_time_ms": round(execution_time, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"文本分类失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                if multi_label:
                    return {
                        "result": '{"categories": ["其他"]}',
                        "model": f"{model_name} (simulation)",
                        "tokens_used": 50,
                        "execution_time_ms": round(execution_time, 2),
                        "success": True
                    }
                else:
                    return {
                        "result": '{"category": "其他"}',
                        "model": f"{model_name} (simulation)",
                        "tokens_used": 50,
                        "execution_time_ms": round(execution_time, 2),
                        "success": True
                    }
            return {"error": str(e), "success": False}
    
    def extract_info(self, text: str, entities: list = None):
        """
        从文本中提取指定类型的信息
        
        Args:
            text: 要提取信息的文本内容
            entities: 要提取的实体类型列表，如['人名', '地点', '时间']
            
        Returns:
            提取的信息字典
        """
        # 输入验证
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        
        if entities is not None:
            if not isinstance(entities, list):
                raise ValueError("entities参数必须是列表类型")
            if not all(isinstance(entity, str) for entity in entities):
                raise ValueError("entities列表中的元素必须是字符串类型")
        
        # 默认实体类型
        if entities is None:
            entities = ['人名', '地点', '时间', '组织', '数值']
        
        # 构建提示
        entities_str = ", ".join(entities)
        prompt = f"从以下文本中提取以下实体类型的信息：{entities_str}\n\n文本：{text}\n\n请以JSON格式返回，键为实体类型，值为该类型的实体列表。"
        
        try:
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的信息提取助手，擅长从文本中提取指定类型的实体信息。"},
                    {"role": "user", "content": prompt}
                ],
                model_name="gpt-3.5-turbo",
                max_tokens=1000
            )
            
            # 尝试解析JSON
            try:
                import json
                extracted_result = json.loads(result["generated_text"])
                return {
                    "result": extracted_result,
                    "model": result["model"],
                    "tokens_used": result["tokens_used"],
                    "success": True
                }
            except json.JSONDecodeError:
                # 如果不是有效的JSON，返回格式化的文本响应
                return {
                    "result": {"extracted_info": result["generated_text"]},
                    "model": result["model"],
                    "tokens_used": result["tokens_used"],
                    "success": True
                }
        except Exception as e:
            logger.error(f"信息提取失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                return {
                    "result": {entity: [] for entity in entities},
                    "model": "gpt-3.5-turbo (simulation)",
                    "tokens_used": 100,
                    "success": True
                }
            raise RuntimeError(f"信息提取失败: {str(e)}")
    
    def expand_text(self, text: str, length: str = "medium", style: str = "detailed"):
        """
        扩写文本内容
        
        Args:
            text: 要扩写的文本内容
            length: 扩写后的长度，可选值: short, medium, long
            style: 扩写风格，可选值: detailed, concise, formal, casual
            
        Returns:
            扩写后的文本
        """
        # 输入验证
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("文本内容不能为空")
        
        # 验证长度参数
        valid_lengths = ["short", "medium", "long"]
        if not isinstance(length, str) or length not in valid_lengths:
            raise ValueError(f"length参数必须是以下值之一: {', '.join(valid_lengths)}")
        
        # 验证风格参数
        valid_styles = ["detailed", "concise", "formal", "casual"]
        if not isinstance(style, str) or style not in valid_styles:
            raise ValueError(f"style参数必须是以下值之一: {', '.join(valid_styles)}")
        
        # 根据长度和风格构建提示
        length_desc = {
            "short": "稍作扩展，保持简洁",
            "medium": "适度扩展，增加细节",
            "long": "充分扩展，添加详细信息和背景"
        }
        
        style_desc = {
            "detailed": "详细的",
            "concise": "简洁的",
            "formal": "正式的",
            "casual": "随意的"
        }
        
        prompt = f"请将以下文本进行{style_desc[style]}扩写，{length_desc[length]}，保持原文意思不变。\n\n原文：{text}\n\n扩写后："
        
        try:
            # 根据长度设置不同的max_tokens
            max_tokens_map = {"short": 500, "medium": 1000, "long": 2000}
            # 使用聊天补全API
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的文本扩写助手，擅长根据要求扩展文本内容。"},
                    {"role": "user", "content": prompt}
                ],
                model_name="gpt-3.5-turbo",
                max_tokens=max_tokens_map[length]
            )
            
            return {
                "result": result["generated_text"],
                "model": result["model"],
                "tokens_used": result["tokens_used"],
                "success": True
            }
        except Exception as e:
            logger.error(f"文本扩写失败: {str(e)}")
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                return {
                    "result": f"[模拟扩写 ({style}, {length})] {text}\n\n这是扩写后的内容示例。",
                    "model": "gpt-3.5-turbo (simulation)",
                    "tokens_used": 200,
                    "success": True
                }
            raise RuntimeError(f"文本扩写失败: {str(e)}")


# 创建全局LLM任务实例
llm_tasks = LLMTasks()