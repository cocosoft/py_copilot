"""LLM服务模块"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
from app.core.config import settings
from app.services.model_query_service import model_query_service
from app.models.model_management import ModelSupplier
from app.services.search_management_service import SearchManagementService
from app.services.web_search_service import WebSearchService

# 导入自定义日志配置
from app.core.logging_config import logger


class LLMService:
    """简化版LLM服务类，移除了对LangChain的依赖"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.llm_cache = {}
        # 默认模型配置
        self.default_model = getattr(settings, 'DEFAULT_MODEL', "text-davinci-003")
        self.default_chat_model = getattr(settings, 'DEFAULT_CHAT_MODEL', "gpt-3.5-turbo")
        
        # 初始化搜索服务
        self.search_management_service = SearchManagementService()
        self.web_search_service = WebSearchService()
        
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
            # OpenAI 1.0+版本使用客户端对象
            from openai import OpenAI
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE if hasattr(settings, 'OPENAI_API_BASE') and settings.OPENAI_API_BASE else "https://api.openai.com/v1"
            )
    
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
        presence_penalty: float = 0.0,
        db: Optional[Any] = None
    ) -> Dict[str, Any]:
        """聊天补全功能 - 支持OpenAI和DeepSeek模型，优先使用数据库中的模型配置"""
        start_time = time.time()
        
        # 添加详细的调试日志
        logger.info(f"chat_completion方法调用开始")
        logger.info(f"参数: model_name={model_name}, db={db is not None}")
        logger.info(f"messages: {messages}")
        
        # 优先从数据库获取默认模型
        if not model_name and db:
            logger.info(f"没有提供model_name，尝试从数据库获取默认模型")
            default_model = model_query_service.get_default_model(db, "chat")
            if default_model:
                model_name = default_model.model_id
                logger.info(f"从数据库获取到默认模型: {model_name}")
        
        # 如果数据库中没有默认模型或db参数未提供，使用服务默认值
        model_name = model_name or self.default_chat_model
        
        # 保存原始配置
        original_api_key = None
        original_api_base = None
        
        try:
            # 检查是否有openai模块
            import importlib.util
            has_openai = importlib.util.find_spec('openai') is not None
            
            # 从数据库获取模型和供应商配置
            db_model_info = None
            if db:
                logger.info(f"数据库连接可用，开始查询模型: {model_name}")
                
                if model_name:
                    logger.info(f"尝试从数据库获取模型: {model_name}")
                    model = model_query_service.get_model_by_model_id(db, model_name)
                    if model:
                        logger.info(f"找到模型: {model.model_id}, ID: {model.id}, 供应商ID: {model.supplier_id}")
                        db_model_info = model_query_service.get_model_with_supplier(db, model.id)
                        logger.info(f"db_model_info内容: {db_model_info}")
                        if db_model_info:
                            logger.info(f"model信息: {db_model_info['model'].model_id}")
                            logger.info(f"supplier信息: {db_model_info['supplier']}")
                    else:
                        logger.warning(f"未找到模型: {model_name}")
                        # 使用model_query_service列出所有模型
                        all_models = model_query_service.get_all_models(db)
                        logger.info(f"数据库中所有模型: {[model.model_id for model in all_models]}")
            
            if has_openai:
                import openai
                
                # 如果从数据库获取到模型信息，使用数据库中的配置
                if db_model_info:
                    model = db_model_info["model"]
                    supplier = db_model_info["supplier"]
                    
                    logger.info(f"使用数据库中的模型配置: {model.model_id} (供应商: {supplier['name']})")
                    logger.info(f"supplier字典完整内容: {supplier}")
                    logger.info(f"supplier['api_key']存在: {supplier['api_key'] is not None}")
                    logger.info(f"supplier['api_key']长度: {len(supplier['api_key']) if supplier['api_key'] else 0}")
                    logger.info(f"supplier['api_key']: {supplier['api_key']}")
                    logger.info(f"supplier['api_key_required']: {supplier['api_key_required']}")
                    # 记录完整的API密钥（仅用于调试）
                    logger.info(f"完整的API密钥: {supplier['api_key']}")
                    logger.info(f"API密钥最后4位: {supplier['api_key'][-4:] if supplier['api_key'] else 'None'}")
                    
                    # 根据供应商类型选择不同的客户端配置
                    if supplier['name'].lower() == 'ollama':
                        # Ollama API处理
                        logger.info("使用Ollama客户端配置")
                        
                        # 构建Ollama客户端
                        try:
                            from langchain_ollama import ChatOllama
                            
                            # 设置Ollama客户端参数
                            ollama_params = {
                                "model": model.model_id,
                                "temperature": temperature,
                                "top_p": top_p,
                                "stop": stop,
                            }
                            
                            # 添加API端点配置（如果提供）
                            if supplier["api_endpoint"]:
                                # Ollama API端点需要是OpenAI兼容格式，即 http://localhost:11434/v1
                                ollama_url = supplier["api_endpoint"]
                                logger.info(f"原始Ollama API端点: {ollama_url}")
                                
                                # 修复URL格式：如果以/api结尾，替换为/v1；否则确保以/v1结尾
                                if ollama_url.endswith('/api'):
                                    ollama_url = ollama_url[:-4] + '/v1'  # 将/api替换为/v1
                                elif ollama_url.endswith('/api/'):
                                    ollama_url = ollama_url[:-5] + '/v1'  # 将/api/替换为/v1
                                elif not ollama_url.endswith('/v1'):
                                    ollama_url += '/v1'  # 如果没有/v1后缀，添加它
                                
                                ollama_params["base_url"] = ollama_url
                                logger.info(f"修复后的Ollama API端点: {ollama_url}")
                            
                            logger.info(f"Ollama客户端参数: {ollama_params}")
                            
                            # 创建Ollama客户端
                            ollama_client = ChatOllama(**ollama_params)
                            
                            # 调用Ollama API
                            response = ollama_client.invoke(messages)
                            
                            # 处理Ollama响应
                            response_text = response.content.strip() if hasattr(response, 'content') else ""
                            tokens_used = response.response_metadata.get('token_usage', {}).get('total_tokens', 0) if hasattr(response, 'response_metadata') else 0
                            
                            logger.info(f"Ollama模型API调用成功: {model.model_id}")
                            
                            return {
                                "generated_text": response_text,
                                "model": model.model_id,
                                "tokens_used": tokens_used,
                                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                                "success": True,
                                "supplier": supplier["name"]
                            }
                        except Exception as ollama_error:
                            logger.warning(f"Ollama API调用失败: {str(ollama_error)}")
                            raise
                    else:
                        # 使用OpenAI 1.0+客户端
                        from openai import OpenAI
                        
                        # 创建客户端实例，设置API密钥和端点
                        # 只使用数据库中的API密钥，不回退到环境变量
                        logger.info("只使用数据库中的API密钥，不回退到环境变量")
                        
                        client_params = {
                            "api_key": supplier["api_key"],
                            "base_url": supplier["api_endpoint"] if supplier["api_endpoint"] else "https://api.deepseek.com/v1"
                        }
                        
                        logger.info(f"最终使用的API密钥: {client_params['api_key'][:5]}...{client_params['api_key'][-4:]}" if client_params['api_key'] else "最终使用的API密钥: None")
                        logger.info(f"使用的API端点: {client_params['base_url']}")
                        
                        logger.info(f"客户端参数: {client_params}")
                        
                        client = OpenAI(**client_params)
                        
                        # 使用客户端调用模型
                        try:
                            response = client.chat.completions.create(
                                model=model.model_id,
                                messages=messages,
                                max_tokens=max_tokens if max_tokens else model.max_tokens,
                                temperature=temperature,
                                top_p=top_p,
                                n=n,
                                stop=stop,
                                frequency_penalty=frequency_penalty,
                                presence_penalty=presence_penalty
                            )
                            
                            response_text = response.choices[0].message.content.strip() if response.choices else ""
                            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
                        except Exception as openai_error:
                            logger.warning(f"OpenAI API调用失败: {str(openai_error)}")
                            raise
                        
                        logger.info(f"数据库模型API调用成功: {model.model_id}")
                        
                        return {
                            "generated_text": response_text,
                            "model": model.model_id,
                            "tokens_used": tokens_used,
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": True,
                            "supplier": supplier["name"]
                        }
                
                # 根据模型名称选择API配置（传统方式）
                if model_name.startswith("deepseek-"):
                    # 首先尝试直接从数据库获取DeepSeek供应商配置
                    if db:
                        try:
                            logger.info("尝试从数据库获取DeepSeek供应商配置")
                            # 添加更多调试信息，检查数据库连接和查询结果
                            all_suppliers = db.query(ModelSupplier).all()
                            logger.info(f"所有供应商: {[s.name for s in all_suppliers]}")
                            
                            deepseek_supplier = db.query(ModelSupplier).filter(ModelSupplier.name == "DeepSeek").first()
                            if deepseek_supplier:
                                logger.info(f"找到供应商配置: {deepseek_supplier.name}")
                                logger.info(f"API端点: {deepseek_supplier.api_endpoint}")
                                
                                # 使用model_query_service获取解密后的API密钥
                                supplier_info = model_query_service.get_supplier_with_decrypted_api_key(deepseek_supplier)
                                api_key = supplier_info.get('api_key')
                                logger.info(f"解密后的API密钥: {api_key[:10]}...{api_key[-4:]}" if api_key else "解密后的API密钥: None")  # 显示部分密钥用于调试
                                logger.info(f"解密后的API密钥长度: {len(api_key)}" if api_key else "解密后的API密钥长度: 0")
                                
                                if api_key:
                                    logger.info("使用数据库中的DeepSeek供应商配置")
                                    from openai import OpenAI
                                    
                                    logger.info("使用数据库配置创建DeepSeek客户端")
                                    deepseek_client = OpenAI(
                                        api_key=supplier_info['api_key'],
                                        base_url=deepseek_supplier.api_endpoint
                                    )
                                    
                                    # 检查客户端配置
                                    logger.info(f"客户端API密钥: {deepseek_client.api_key[:10]}...{deepseek_client.api_key[-4:]}")
                                    logger.info(f"客户端API端点: {deepseek_client.base_url}")
                                    
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
                                    
                                    logger.info(f"DeepSeek API调用成功(数据库配置): {model_name}")
                                    
                                    return {
                                        "generated_text": response_text,
                                        "model": model_name,
                                        "tokens_used": tokens_used,
                                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                                        "success": True
                                    }
                                else:
                                    logger.warning("DeepSeek供应商API密钥为空")
                            else:
                                logger.warning("数据库中未找到DeepSeek供应商配置")
                        except Exception as db_deepseek_error:
                            logger.warning(f"从数据库获取DeepSeek配置失败: {str(db_deepseek_error)}")
                            import traceback
                            logger.warning(f"错误堆栈: {traceback.format_exc()}")
                    
                    # 不再回退到环境变量配置，只使用数据库配置
                    logger.info("已跳过环境配置的DeepSeek API密钥，仅使用数据库配置")
                
                # OpenAI模型配置
                if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-api-key-here":
                    try:
                        # 使用已经初始化的客户端或创建新客户端
                        if hasattr(self, 'openai_client'):
                            response = self.openai_client.chat.completions.create(
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
                        else:
                            # 如果没有初始化客户端，创建一个新的
                            from openai import OpenAI
                            client = OpenAI(
                                api_key=settings.OPENAI_API_KEY,
                                base_url=settings.OPENAI_API_BASE if hasattr(settings, 'OPENAI_API_BASE') and settings.OPENAI_API_BASE else "https://api.openai.com/v1"
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
                "generated_text": f"系统提示: 当前AI模型连接失败。可能是API密钥无效或网络问题。请联系管理员检查API配置。",
                "model": model_name,
                "tokens_used": 0,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "success": False,
                "error": "所有模型API调用失败"
            }
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            # 恢复原始配置
            if 'openai' in locals() and original_api_key:
                openai.api_key = original_api_key
                openai.api_base = original_api_base
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
    
    def perform_web_search(self, query: str, db: Optional[Any] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        使用配置的搜索引擎执行联网搜索
        
        Args:
            query: 搜索查询词
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            搜索结果
        """
        if not db:
            # 如果没有数据库会话，创建一个临时的
            from app.core.database import get_db
            db = next(get_db())
            
        try:
            # 获取搜索设置
            search_settings = self.search_management_service.get_search_settings(db, user_id)
            
            # 如果没有设置，使用默认设置
            if not search_settings:
                search_settings = self.search_management_service.update_search_settings(db, {}, user_id)
            
            # 执行搜索
            search_result = self.web_search_service.search(
                query=query,
                engine=search_settings.default_search_engine,
                safe_search=search_settings.safe_search
            )
            
            return search_result
        except Exception as e:
            logger.error(f"搜索执行失败: {str(e)}")
            return {
                "query": query,
                "results": [],
                "success": False,
                "error": str(e)
            }
    def get_available_models(self, db: Optional[Any] = None, model_type: str = None) -> List[Dict[str, Any]]:
        """
        获取可用的LLM模型列表
        
        Args:
            db: 数据库会话（可选）
            model_type: 模型类型过滤（可选）
            
        Returns:
            可用模型列表
        """
        # 如果提供了数据库会话，从数据库获取模型列表
        if db:
            try:
                db_models = model_query_service.get_available_models_dict(db, model_type)
                
                # 转换为与旧格式兼容的结构
                result = []
                for item in db_models:
                    result.append({
                        "name": item.get("model_id", "unknown"),
                        "display_name": item.get("model_name", item.get("model_id", "unknown")),
                        "model_type": item.get("model_type", "chat"),
                        "provider": item.get("supplier_name", "unknown"),
                        "max_tokens": item.get("max_tokens", 4096),
                        "description": f"{item.get('model_name', item.get('model_id', 'unknown'))} - {item.get('supplier_name', 'unknown')}模型",
                        "is_default": item.get("is_default", False)
                    })
                
                return result
            except Exception as e:
                logger.error(f"从数据库获取模型列表失败: {e}")
                # 失败时回退到默认模型列表
                pass
        
        # 默认模型列表（兼容旧版本）
        default_models = [
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
        
        if model_type:
            return [model for model in default_models if model["type"] == model_type]
        
        return default_models
    
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