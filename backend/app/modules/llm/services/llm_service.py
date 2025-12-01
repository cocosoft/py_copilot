"""LLM服务模块"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
import logging
# 简化配置导入，使用默认值
# from app.core.config import settings

# 本地配置替代
class LocalSettings:
    DEFAULT_MODEL = "text-davinci-003"
    DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"

settings = LocalSettings()

logger = logging.getLogger(__name__)


class LLMService:
    """简化版LLM服务类，移除了对LangChain的依赖"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.llm_cache = {}
        # 默认模型配置
        self.default_model = getattr(settings, 'DEFAULT_MODEL', "text-davinci-003")
        self.default_chat_model = getattr(settings, 'DEFAULT_CHAT_MODEL', "gpt-3.5-turbo")
        
        # 可用模型列表
        self.available_models = [
            {
                "name": "gpt-3.5-turbo",
                "provider": "OpenAI",
                "type": "chat",
                "max_tokens": 4096,
                "description": "OpenAI的GPT-3.5 Turbo模型，适用于聊天和通用任务",
                "is_default": True
            },
            {
                "name": "text-davinci-003",
                "provider": "OpenAI",
                "type": "completion",
                "max_tokens": 4097,
                "description": "OpenAI的GPT-3文本生成模型",
                "is_default": False
            },
            {
                "name": "gpt-4",
                "provider": "OpenAI",
                "type": "chat",
                "max_tokens": 8192,
                "description": "OpenAI的GPT-4模型，适用于复杂任务",
                "is_default": False
            },
            {
                "name": "deepseek-chat",
                "provider": "DeepSeek",
                "type": "chat",
                "max_tokens": 16384,
                "description": "DeepSeek的对话模型，适用于多种聊天场景",
                "is_default": False
            }
        ]
        
        # 配置OpenAI客户端
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            if hasattr(settings, 'OPENAI_API_BASE') and settings.OPENAI_API_BASE:
                openai.api_base = settings.OPENAI_API_BASE
    
    def _initialize_default_llm(self):
        """初始化默认LLM模型"""
        # 简化版本，移除了LangChain依赖
        pass
    
    def get_llm(self, model_name: str = None, provider: str = None) -> Any:
        """获取指定的LLM模型实例 - 简化版本"""
        # 移除了LangChain依赖，直接返回模型名称作为标识
        model = model_name or ("gpt-3.5-turbo" if provider == "openai" or not provider else self.default_model)
        logger.info(f"Using model: {model}")
        return model
    
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成文本响应 - 简化版本"""
        # 简化实现，直接使用text_completion方法
        try:
            return self.text_completion(
                prompt=prompt,
                model_name=kwargs.get("model_name"),
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7)
            )
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return {
                "error": str(e),
                "model": kwargs.get("model_name", "default"),
                "success": False
            }
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """聊天功能 - 简化版本"""
        # 简化实现，直接使用chat_completion方法
        try:
            return self.chat_completion(
                messages=messages,
                model_name=kwargs.get("model_name"),
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7)
            )
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return {
                "error": str(e),
                "model": kwargs.get("model_name", "default"),
                "success": False
            }
    
    def create_conversation_chain(self, **kwargs) -> Dict:
        """创建对话链 - 简化版本"""
        # 移除了LangChain依赖，返回基本配置信息
        logger.warning("create_conversation_chain is a simplified version without LangChain dependencies")
        return {
            "model": kwargs.get("model_name", "gpt-3.5-turbo"),
            "provider": kwargs.get("provider", "openai"),
            "status": "simplified_mode"
        }
    
    def text_completion(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 1.0,
        n: int = 1,
        stop: Optional[List[str]] = None,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0
    ) -> Dict[str, Any]:
        """文本补全功能 - 简化版本"""
        start_time = time.time()
        model = model_name or self.default_model
        
        try:
            # 检查是否有openai模块
            import importlib.util
            has_openai = importlib.util.find_spec('openai') is not None
            
            # 如果有openai模块且配置了API密钥，尝试使用它
            if has_openai and hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                import openai
                try:
                    response = openai.Completion.create(
                        model=model,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        n=n,
                        stop=stop,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty
                    )
                    response_text = response.choices[0].text.strip() if response.choices else ""
                    tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
                    
                    execution_time = (time.time() - start_time) * 1000
                    return {
                        "model": model,
                        "generated_text": response_text,
                        "tokens_used": tokens_used,
                        "execution_time_ms": round(execution_time, 2),
                        "success": True
                    }
                except Exception as openai_error:
                    logger.warning(f"OpenAI API error, falling back to simulated response: {str(openai_error)}")
            
            # 模拟模式或OpenAI不可用时返回模拟响应
            execution_time = (time.time() - start_time) * 1000
            return {
                "model": f"{model} (simulation)",
                "generated_text": f"[模拟响应] 基于提示: {prompt[:50]}...",
                "tokens_used": len(prompt.split()) // 2 + max_tokens // 2,
                "execution_time_ms": round(execution_time, 2),
                "success": False,
                "simulated": True
            }
        except Exception as e:
            logger.error(f"Error in text completion: {str(e)}")
            execution_time = (time.time() - start_time) * 1000
            return {
                "model": model,
                "generated_text": f"[模拟响应] 基于提示: {prompt[:50]}...",
                "tokens_used": 0,
                "error": str(e),
                "execution_time_ms": round(execution_time, 2),
                "success": False,
                "simulated": True
            }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 1.0,
        n: int = 1,
        stop: Optional[List[str]] = None,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0
    ) -> Dict[str, Any]:
        """聊天补全功能 - 支持OpenAI和DeepSeek模型"""
        start_time = time.time()
        model_name = model_name or self.default_chat_model
        
        try:
            # 检查是否有openai模块
            import importlib.util
            has_openai = importlib.util.find_spec('openai') is not None
            
            if has_openai:
                import openai
                
                # 根据模型名称选择API配置
                if model_name.startswith("deepseek-"):
                    # DeepSeek模型配置 - 使用正确的小写配置名
                    if hasattr(settings, 'deepseek_api_key') and settings.deepseek_api_key:
                        # 保存原始配置
                        original_api_key = openai.api_key
                        original_api_base = openai.api_base
                        
                        try:
                            # 设置DeepSeek API配置
                            openai.api_key = settings.deepseek_api_key
                            openai.api_base = "https://api.deepseek.com/v1"
                            
                            # 使用OpenAI兼容的接口调用DeepSeek
                            response = openai.ChatCompletion.create(
                                model=model_name,
                                messages=messages,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                top_p=top_p,
                                n=n,
                                stop=stop,
                                frequency_penalty=frequency_penalty,
                                presence_penalty=presence_penalty
                            )
                            
                            response_text = response.choices[0].message.content.strip() if response.choices else ""
                            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
                            
                            logger.info(f"DeepSeek API调用成功: {model_name}")
                            
                            return {
                                "generated_text": response_text,
                                "model": model_name,
                                "tokens_used": tokens_used,
                                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                                "success": True
                            }
                        except Exception as deepseek_error:
                            logger.warning(f"DeepSeek API error: {str(deepseek_error)}")
                            # 恢复原始配置
                            openai.api_key = original_api_key
                            openai.api_base = original_api_base
                    else:
                        logger.warning("DeepSeek API密钥未配置或使用默认值")
                
                # OpenAI模型配置
                if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-api-key-here":
                    try:
                        response = openai.ChatCompletion.create(
                            model=model_name,
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            top_p=top_p,
                            n=n,
                            stop=stop,
                            frequency_penalty=frequency_penalty,
                            presence_penalty=presence_penalty
                        )
                        response_text = response.choices[0].message.content.strip() if response.choices else ""
                        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
                        
                        return {
                            "generated_text": response_text,
                            "model": model_name,
                            "tokens_used": tokens_used,
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": True
                        }
                    except Exception as openai_error:
                        logger.warning(f"OpenAI API error: {str(openai_error)}")
            
            # 如果所有API调用都失败，返回详细的错误信息而不是模拟响应
            logger.error(f"所有模型API调用失败: {model_name}")
            return {
                "generated_text": f"错误: 无法连接到{model_name}模型API。请检查API密钥和网络连接。",
                "model": model_name,
                "tokens_used": 0,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "success": False,
                "error": "API调用失败"
            }
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return {
                "generated_text": f"错误: 处理请求时发生异常 - {str(e)}",
                "model": model_name,
                "tokens_used": 0,
                "error": str(e),
                "response_time_ms": int((time.time() - start_time) * 1000),
                "success": False
            }
    
    def generate_embeddings(
        self,
        text: str,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成文本嵌入向量
        
        Args:
            text: 要生成嵌入向量的文本
            model_name: 嵌入模型名称，默认为text-embedding-ada-002
        
        Returns:
            包含嵌入向量和模型信息的字典
        """
        start_time = time.time()
        
        # 使用默认模型或指定模型
        model = model_name or "text-embedding-ada-002"
        
        try:
            # 调用OpenAI API生成嵌入向量
            response = openai.Embedding.create(
                input=text,
                model=model
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "model": model,
                "embedding": response.data[0].embedding,
                "tokens_used": response.usage.total_tokens,
                "execution_time_ms": round(execution_time, 2)
            }
        except Exception as e:
            # 模拟模式
            if hasattr(settings, 'SIMULATION_MODE') and settings.SIMULATION_MODE:
                execution_time = (time.time() - start_time) * 1000
                # 返回一个模拟的1536维向量
                return {
                    "model": f"{model} (simulation)",
                    "embedding": [0.1 for _ in range(1536)],
                    "tokens_used": len(text.split()) // 2,
                    "execution_time_ms": round(execution_time, 2)
                }
            logger.error(f"Embeddings generation error: {str(e)}")
            raise
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        获取可用的LLM模型列表
        
        Returns:
            可用模型列表
        """
        return self.available_models
    
    def log_request(
        self,
        user_id: int,
        model_name: str,
        prompt: str,
        response: str,
        tokens_used: int,
        task_type: str
    ) -> None:
        """
        记录LLM请求历史
        
        Args:
            user_id: 用户ID
            model_name: 模型名称
            prompt: 请求提示
            response: 模型响应
            tokens_used: 使用的token数
            task_type: 任务类型
        """
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 注意：这里应该导入并使用正确的RequestLog模型
            # 由于当前可能还没有创建RequestLog模型，这里只是占位
            # 实际使用时需要取消注释并修改为正确的导入
            # 
            # from app.models.request_log import RequestLog
            # 
            # log_entry = RequestLog(
            #     user_id=user_id,
            #     model_name=model_name,
            #     prompt=prompt,
            #     response=response,
            #     tokens_used=tokens_used,
            #     task_type=task_type,
            #     created_at=datetime.utcnow()
            # )
            # db.add(log_entry)
            # db.commit()
            # 
            # 暂时打印日志作为替代
            logger.info(f"[LLM Log] User: {user_id}, Model: {model_name}, Tokens: {tokens_used}, Type: {task_type}")
        
        except Exception as e:
            # 记录日志失败不应该影响主要功能
            logger.error(f"Failed to log LLM request: {str(e)}")
        finally:
            # 关闭数据库会话
            if 'db' in locals():
                db.close()


# 创建全局LLM服务实例
llm_service = LLMService()