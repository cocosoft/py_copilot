"""修复版LLM服务模块 - 支持真实大模型调用"""
import os
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings
from app.models.supplier_db import ModelDB, SupplierDB
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FixedLLMService:
    """修复版LLM服务类，支持真实大模型调用"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.llm_cache = {}
        self.default_model = getattr(settings, 'DEFAULT_MODEL', "gpt-3.5-turbo")
        self.default_chat_model = getattr(settings, 'DEFAULT_CHAT_MODEL', "gpt-3.5-turbo")
        
        # 配置OpenAI客户端
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            if hasattr(settings, 'OPENAI_API_BASE') and settings.OPENAI_API_BASE:
                openai.api_base = settings.OPENAI_API_BASE
    
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
        presence_penalty: float = 0.0,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """聊天补全功能 - 支持多种大模型"""
        start_time = time.time()
        model_name = model_name or self.default_chat_model
        
        logger.info(f"开始调用模型: {model_name}")
        
        try:
            # 检查是否有openai模块
            import importlib.util
            has_openai = importlib.util.find_spec('openai') is not None
            
            if not has_openai:
                return self._get_simulated_response("未安装openai库", model_name, start_time)
            
            import openai
            
            # 根据模型类型选择API配置
            if model_name.startswith("deepseek-"):
                return self._call_deepseek_api(
                    openai, messages, model_name, max_tokens, temperature, 
                    top_p, n, stop, frequency_penalty, presence_penalty, start_time
                )
            elif model_name.startswith("gpt-") or model_name in ["gpt-3.5-turbo", "gpt-4"]:
                return self._call_openai_api(
                    openai, messages, model_name, max_tokens, temperature, 
                    top_p, n, stop, frequency_penalty, presence_penalty, start_time
                )
            elif model_name.startswith("claude-"):
                return self._call_anthropic_api(
                    messages, model_name, max_tokens, temperature, start_time
                )
            else:
                # 默认尝试OpenAI API
                return self._call_openai_api(
                    openai, messages, model_name, max_tokens, temperature, 
                    top_p, n, stop, frequency_penalty, presence_penalty, start_time
                )
                
        except Exception as e:
            logger.error(f"模型调用失败: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            return self._get_error_response(str(e), model_name, start_time)
    
    def _call_deepseek_api(self, openai, messages, model_name, max_tokens, temperature, 
                          top_p, n, stop, frequency_penalty, presence_penalty, start_time):
        """调用DeepSeek API"""
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        api_base = getattr(settings, 'DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
        
        if not api_key or api_key == "your-deepseek-api-key-here":
            return self._get_config_error_response("DeepSeek", model_name, start_time)
        
        try:
            client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base,
                timeout=10
            )
            
            response = client.chat.completions.create(
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
            
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            return self._get_api_error_response("DeepSeek", str(e), model_name, start_time)
    
    def _call_openai_api(self, openai, messages, model_name, max_tokens, temperature, 
                        top_p, n, stop, frequency_penalty, presence_penalty, start_time):
        """调用OpenAI API"""
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        api_base = getattr(settings, 'OPENAI_API_BASE', None)
        
        if not api_key or api_key == "your-openai-api-key-here":
            return self._get_config_error_response("OpenAI", model_name, start_time)
        
        try:
            client_config = {"api_key": api_key, "timeout": 10}
            if api_base:
                client_config["base_url"] = api_base
                
            client = openai.OpenAI(**client_config)
            
            response = client.chat.completions.create(
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
            
            logger.info(f"OpenAI API调用成功: {model_name}")
            
            return {
                "generated_text": response_text,
                "model": model_name,
                "tokens_used": tokens_used,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            return self._get_api_error_response("OpenAI", str(e), model_name, start_time)
    
    def _call_anthropic_api(self, messages, model_name, max_tokens, temperature, start_time):
        """调用Anthropic API（Claude模型）"""
        try:
            import anthropic
            
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
            if not api_key or api_key == "your-anthropic-api-key-here":
                return self._get_config_error_response("Anthropic", model_name, start_time)
            
            client = anthropic.Anthropic(api_key=api_key)
            
            # 转换消息格式
            system_message = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                elif msg["role"] == "user":
                    user_messages.append(msg["content"])
            
            user_content = "\n".join(user_messages)
            
            response = client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=[{"role": "user", "content": user_content}]
            )
            
            response_text = response.content[0].text if response.content else ""
            
            logger.info(f"Anthropic API调用成功: {model_name}")
            
            return {
                "generated_text": response_text,
                "model": model_name,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "success": True
            }
            
        except ImportError:
            return self._get_simulated_response("未安装anthropic库", model_name, start_time)
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {str(e)}")
            return self._get_api_error_response("Anthropic", str(e), model_name, start_time)
    
    def _get_config_error_response(self, provider, model_name, start_time):
        """获取配置错误响应"""
        error_msg = f"""系统提示: {provider} API配置不完整。

请检查以下配置：
1. 在.env.local文件中设置有效的{provider.upper()}_API_KEY
2. 确保API密钥有效且未过期
3. 检查网络连接

当前模型: {model_name}"""
        
        return {
            "generated_text": error_msg,
            "model": f"{model_name} (配置错误)",
            "tokens_used": 0,
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "success": False,
            "error": "API配置不完整"
        }
    
    def _get_api_error_response(self, provider, error_detail, model_name, start_time):
        """获取API错误响应"""
        error_msg = f"""系统提示: {provider} API调用失败。

错误详情: {error_detail}

可能的原因：
1. API密钥无效或已过期
2. 网络连接问题
3. 模型服务暂时不可用
4. 请求参数不正确

当前模型: {model_name}"""
        
        return {
            "generated_text": error_msg,
            "model": f"{model_name} (API错误)",
            "tokens_used": 0,
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "success": False,
            "error": error_detail
        }
    
    def _get_simulated_response(self, reason, model_name, start_time):
        """获取模拟响应"""
        error_msg = f"""系统提示: 无法调用真实AI模型。

原因: {reason}

当前使用模拟模式，如需使用真实AI模型：
1. 安装必要的Python包: pip install openai anthropic
2. 配置有效的API密钥
3. 检查网络连接

当前模型: {model_name}"""
        
        return {
            "generated_text": error_msg,
            "model": f"{model_name} (模拟)",
            "tokens_used": 0,
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "success": False,
            "simulated": True
        }
    
    def _get_error_response(self, error_detail, model_name, start_time):
        """获取通用错误响应"""
        error_msg = f"""系统提示: 处理您的请求时发生异常。

错误详情: {error_detail}

可能的原因：
1. 模型配置问题
2. 网络连接问题
3. 服务暂时不可用

当前模型: {model_name}"""
        
        return {
            "generated_text": error_msg,
            "model": f"{model_name} (错误)",
            "tokens_used": 0,
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "success": False,
            "error": error_detail
        }
    
    # 兼容性方法
    def chat(self, messages, **kwargs):
        """兼容chat方法"""
        return self.chat_completion(messages, **kwargs)
    
    def generate_text(self, prompt, **kwargs):
        """兼容generate_text方法"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, **kwargs)


# 创建全局实例
fixed_llm_service = FixedLLMService()