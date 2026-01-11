"""LLM服务模块"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
import logging
import inspect
from app.core.config import settings
from app.models.supplier_db import ModelDB, SupplierDB
from sqlalchemy.orm import Session

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
                "model_id": "gpt-3.5-turbo",
                "provider": "OpenAI",
                "type": "chat",
                "max_tokens": 4096,
                "description": "OpenAI的GPT-3.5 Turbo模型，适用于聊天和通用任务",
                "is_default": True
            },
            {
                "model_id": "text-davinci-003",
                "provider": "OpenAI",
                "type": "completion",
                "max_tokens": 4097,
                "description": "OpenAI的GPT-3文本生成模型",
                "is_default": False
            },
            {
                "model_id": "gpt-4",
                "provider": "OpenAI",
                "type": "chat",
                "max_tokens": 8192,
                "description": "OpenAI的GPT-4模型，适用于复杂任务",
                "is_default": False
            },
            {
                "model_id": "deepseek-chat",
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
                max_tokens=kwargs.get("max_tokens", 4000),
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
                max_tokens=kwargs.get("max_tokens", 4000),
                temperature=kwargs.get("temperature", 0.7),
                db=kwargs.get("db")
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
            
            # 模拟模式或OpenAI不可用时返回明确错误信息
            execution_time = (time.time() - start_time) * 1000
            
            error_response = "系统提示: 当前AI模型连接失败。\n\n"
            error_response += "可能的原因：\n"
            error_response += "1. API密钥无效或已过期\n"
            error_response += "2. 网络连接问题\n"
            error_response += "3. 模型服务暂时不可用\n\n"
            error_response += "请检查并更新您的API密钥配置。"
            
            return {
                "model": f"{model} (错误)",
                "generated_text": error_response,
                "tokens_used": 0,
                "execution_time_ms": round(execution_time, 2),
                "success": False,
                "simulated": False,
                "error": "API调用失败或模型服务不可用"
            }
        except Exception as e:
            logger.error(f"Error in text completion: {str(e)}")
            execution_time = (time.time() - start_time) * 1000
            
            error_response = "系统提示: 处理您的请求时发生异常。\n\n"
            error_response += "错误详情：" + str(e) + "\n\n"
            error_response += "可能的原因：\n"
            error_response += "1. API密钥无效或已过期\n"
            error_response += "2. 网络连接问题\n"
            error_response += "3. 模型服务暂时不可用\n\n"
            error_response += "请检查并更新您的API密钥配置。"
            
            return {
                "model": model,
                "generated_text": error_response,
                "tokens_used": 0,
                "error": str(e),
                "execution_time_ms": round(execution_time, 2),
                "success": False,
                "simulated": False
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
        presence_penalty: float = 0.0,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """聊天补全功能 - 支持OpenAI和DeepSeek模型"""
        print("DEBUG: 进入chat_completion方法")
        start_time = time.time()
        model_name = model_name or self.default_chat_model
        
        # 从数据库获取模型和供应商信息
        model_info = None
        supplier_info = None
        all_models = []
        all_suppliers = []
        
        print(f"DEBUG: db是否存在: {db is not None}")
        try:
            if db:
                # 查询所有模型
                all_models = db.query(ModelDB).all()
                print(f"DEBUG: 从数据库获取到的所有模型数: {len(all_models)}")
                
                # 查询指定模型
                model_info = db.query(ModelDB).filter(
                    ModelDB.model_id == model_name,
                    ModelDB.is_active == True
                ).first()
                print(f"DEBUG: 查询到的模型信息: {model_info}")
                
                if model_info:
                    # 查询供应商信息
                    supplier_info = db.query(SupplierDB).filter(
                        SupplierDB.id == model_info.supplier_id,
                        SupplierDB.is_active == True
                    ).first()
                    print(f"DEBUG: 查询到的供应商信息: {supplier_info}")
                    
                    # 查询所有供应商
                    all_suppliers = db.query(SupplierDB).all()
        except Exception as e:
            import traceback
            error_message = f"数据库查询异常: {str(e)}\n{traceback.format_exc()}"
            print(f"DEBUG: 数据库查询异常: {error_message}")
            return {
                "model": model_name,
                "generated_text": error_message,
                "tokens_used": 0,
                "error": "数据库查询失败",
                "execution_time_ms": 0,
                "success": False
            }
        

        
        print("DEBUG: 进入主处理try块")
        try:
            # 检查是否有openai模块
            import importlib.util
            has_openai = importlib.util.find_spec('openai') is not None
            
            print(f"DEBUG: 是否有openai模块: {has_openai}")
            print(f"DEBUG: model_name: {model_name}")
            print(f"DEBUG: supplier_info类型: {type(supplier_info)}")
            print(f"DEBUG: supplier_info内容: {supplier_info}")
            
            if has_openai:
                import openai
                
                # 导入必要的服务
                from app.services.model_query_service import ModelQueryService
                
                # 检查供应商是否为Ollama
                is_ollama_supplier = False
                if supplier_info and supplier_info.name == "Ollama":
                    is_ollama_supplier = True
                    print(f"DEBUG: 检测到Ollama供应商，将使用Ollama API")
                
                # 根据模型名称或供应商选择API配置
                if is_ollama_supplier:
                    # Ollama模型配置
                    api_key = None
                    api_base = None
                    
                    # 优先从数据库获取Ollama配置
                    if supplier_info:
                        api_base = supplier_info.api_endpoint
                        logger.info(f"从数据库获取Ollama API端点: {api_base}")
                        
                        # 确保Ollama API端点格式正确
                        if api_base:
                            # 调试：显示原始API端点
                            print(f"DEBUG: 原始API端点: {api_base}")
                            
                            # 如果API端点以/api结尾，将其替换为/v1
                            if api_base.endswith('/api'):
                                api_base = api_base[:-4] + '/v1'
                            elif api_base.endswith('/api/'):
                                api_base = api_base[:-5] + '/v1'
                            # 如果API端点不以/v1结尾，添加/v1
                            elif not api_base.endswith('/v1'):
                                if api_base.endswith('/'):
                                    api_base += 'v1'
                                else:
                                    api_base += '/v1'
                            logger.info(f"修正后的Ollama API端点: {api_base}")
                            print(f"DEBUG: 修正后的API端点: {api_base}")
                    else:
                        print("DEBUG: 未找到Ollama供应商信息")
                        logger.warning("未找到Ollama供应商信息")
                        
                        # 使用默认的Ollama API端点
                        api_base = "http://localhost:11434/v1"
                        logger.info(f"使用默认的Ollama API端点: {api_base}")
                        print(f"DEBUG: 使用默认API端点: {api_base}")
                    
                    if api_base:
                        try:
                            print(f"DEBUG: 最终使用的Ollama API端点: {api_base}")
                            logger.info(f"最终使用的Ollama API端点: {api_base}")
                            
                            # 使用OpenAI客户端对象配置Ollama API
                            print("DEBUG: 创建Ollama客户端...")
                            ollama_client = openai.OpenAI(
                                api_key="ollama",  # Ollama不需要实际的API密钥，但需要提供一个值
                                base_url=api_base,
                                timeout=30  # 设置较长超时
                            )
                            print(f"DEBUG: Ollama客户端创建成功，base_url: {api_base}")
                            
                            print("DEBUG: 开始调用Ollama API...")
                            logger.info("正在调用Ollama API...")
                            
                            # 打印调用参数
                            print(f"DEBUG: 调用参数 - model: {model_name}, messages: {messages}")
                            
                            # 使用配置好的客户端调用Ollama
                            response = ollama_client.chat.completions.create(
                                model=model_name,
                                messages=messages,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                top_p=top_p,
                                n=n,
                                stop=stop
                            )
                            
                            response_text = response.choices[0].message.content.strip() if response.choices else ""
                            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
                            
                            logger.info(f"Ollama API调用成功: {model_name}")
                            
                            return {
                                "generated_text": response_text,
                                "model": model_name,
                                "tokens_used": tokens_used,
                                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                                "success": True
                            }
                        except Exception as ollama_error:
                            logger.warning(f"Ollama API error: {str(ollama_error)}")
                            logger.warning(f"错误类型: {type(ollama_error).__name__}")
                            # 记录更多错误详情
                            import traceback
                            logger.warning(f"错误堆栈: {traceback.format_exc()}")
                            
                            # 继续执行，尝试其他模型或返回错误信息
                    else:
                        logger.warning("Ollama API端点未配置")
                        # 提供友好的错误消息
                        return {
                            "generated_text": "错误: Ollama API配置不完整。请在供应商设置中配置有效的API端点。",
                            "model": model_name,
                            "tokens_used": 0,
                            "error": "API配置不完整",
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": False
                        }
                elif model_name.startswith("deepseek-"):
                    # DeepSeek模型配置
                    api_key = None
                    api_base = None
                    
                    # 添加更多调试信息
                    logger.info(f"supplier_info: {supplier_info}")
                    logger.info(f"supplier_info.name: {supplier_info.name if supplier_info else 'None'}")
                    logger.info(f"supplier_info.api_endpoint: {supplier_info.api_endpoint if supplier_info else 'None'}")
                    logger.info(f"supplier_info.api_key_required: {supplier_info.api_key_required if supplier_info else 'None'}")
                    
                    # 优先从数据库获取
                    if supplier_info:
                        print(f"DEBUG: supplier_info属性: {dir(supplier_info)}")
                        # 获取解密后的API密钥
                        supplier_with_decrypted_key = ModelQueryService.get_supplier_with_decrypted_api_key(supplier_info)
                        print(f"DEBUG: supplier_with_decrypted_key类型: {type(supplier_with_decrypted_key)}")
                        print(f"DEBUG: supplier_with_decrypted_key: {supplier_with_decrypted_key}")
                        print(f"DEBUG: supplier_with_decrypted_key.keys(): {supplier_with_decrypted_key.keys()}")
                        api_key = supplier_with_decrypted_key['api_key']
                        # 为API端点设置默认值
                        api_base = supplier_info.api_endpoint if supplier_info.api_endpoint else "https://api.deepseek.com/v1"
                        logger.info(f"使用解密后的API密钥: {'None' if api_key is None else f'{api_key[:5]}...{api_key[-4:]}'}")
                        logger.info(f"使用的API端点: {api_base}")
                    # 回退到配置文件
                    elif hasattr(settings, 'deepseek_api_key') and settings.deepseek_api_key:
                        api_key = settings.deepseek_api_key
                        api_base = settings.deepseek_api_base
                    
                    # 添加更多调试信息
                    logger.info(f"最终的api_key: {api_key}")
                    logger.info(f"最终的api_base: {api_base}")
                    
                    if api_key and api_base:
                        try:
                            # 使用OpenAI客户端对象配置DeepSeek API，添加超时设置
                            deepseek_client = openai.OpenAI(
                                api_key=api_key,
                                base_url=api_base,
                                timeout=10  # 设置10秒超时
                            )
                            
                            logger.info("正在调用DeepSeek API...")
                            # 使用配置好的客户端调用DeepSeek
                            response = deepseek_client.chat.completions.create(
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
                            logger.warning(f"错误类型: {type(deepseek_error).__name__}")
                            # 记录更多错误详情
                            import traceback
                            logger.warning(f"错误堆栈: {traceback.format_exc()}")
                            
                            # 继续执行，尝试其他模型或返回错误信息
                    else:
                        logger.warning("DeepSeek API密钥或API端点未配置")
                        # 提供友好的错误消息
                        return {
                            "generated_text": "错误: DeepSeek API配置不完整。请在供应商设置中配置有效的API密钥和API端点。",
                            "model": model_name,
                            "tokens_used": 0,
                            "error": "API配置不完整",
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": False
                        }
                
                # OpenAI模型配置
                # 先从数据库查找OpenAI供应商和模型
                api_key = None
                api_base = None
                
                print(f"DEBUG: 处理OpenAI模型配置，supplier_info: {supplier_info}")
                if supplier_info:
                    api_key = supplier_info.api_key
                    api_base = supplier_info.api_endpoint
                elif hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-api-key-here":
                    api_key = settings.OPENAI_API_KEY
                    api_base = settings.OPENAI_API_BASE if hasattr(settings, 'OPENAI_API_BASE') else None
                
                if api_key:
                    try:
                        # 使用OpenAI客户端对象
                        openai_client = openai.OpenAI(
                            api_key=api_key,
                            base_url=api_base
                        )
                        
                        response = openai_client.chat.completions.create(
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
            
            # 如果所有API调用都失败，返回明确的错误信息而不是模拟响应
            logger.error(f"所有模型API调用失败: {model_name}")
            
            # 返回明确的错误信息
            error_response = "系统提示: 当前AI模型连接失败。\n\n"
            error_response += "可能的原因：\n"
            error_response += "1. API密钥无效或已过期\n"
            error_response += "2. 网络连接问题\n"
            error_response += "3. 模型服务暂时不可用\n\n"
            error_response += "请检查并更新您的API密钥配置。"
                
            return {
                "generated_text": error_response,
                "model": f"{model_name} (错误)",
                "tokens_used": 0,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "success": False,
                "simulated": False,
                "error": "API调用失败"
            }
        except Exception as e:
            logger.error(f"所有模型API调用失败: {model_name}")
            logger.error(f"错误详情: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            # 返回明确的错误信息
            error_response = "系统提示: 处理您的请求时发生异常。\n\n"
            error_response += "错误详情：" + str(e) + "\n\n"
            error_response += "可能的原因：\n"
            error_response += "1. API密钥无效或已过期\n"
            error_response += "2. 网络连接问题\n"
            error_response += "3. 模型服务暂时不可用\n\n"
            error_response += "请检查并更新您的API密钥配置。"
            
            return {
                "generated_text": error_response,
                "model": f"{model_name} (错误)",
                "tokens_used": 0,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "success": False,
                "simulated": False,
                "error": str(e)
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