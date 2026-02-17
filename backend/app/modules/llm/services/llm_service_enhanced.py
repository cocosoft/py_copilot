"""增强版LLM服务模块 - 支持数据库配置的真实大模型调用"""
import os
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings
from app.models.supplier_db import ModelDB, SupplierDB
from sqlalchemy.orm import Session
from app.core.encryption import decrypt_string

logger = logging.getLogger(__name__)


class EnhancedLLMService:
    """增强版LLM服务类，支持数据库配置的真实大模型调用"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.llm_cache = {}
        self.default_model = getattr(settings, 'DEFAULT_MODEL', "gpt-3.5-turbo")
        self.default_chat_model = getattr(settings, 'DEFAULT_CHAT_MODEL', "gpt-3.5-turbo")
        
        # 配置OpenAI客户端（兼容性）
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            if hasattr(settings, 'OPENAI_API_BASE') and settings.OPENAI_API_BASE:
                openai.api_base = settings.OPENAI_API_BASE
    
    def _get_model_and_supplier_from_db(self, db: Session, model_name: str) -> tuple:
        """从数据库获取模型和供应商信息"""
        try:
            logger.info(f"=== 开始从数据库查询模型: {model_name} ===")
            # 查询模型信息
            model = db.query(ModelDB).filter(
                (ModelDB.model_id == model_name) | 
                (ModelDB.model_name == model_name)
            ).first()
            
            if not model:
                logger.warning(f"数据库中未找到模型: {model_name}")
                return None, None
            
            logger.info(f"找到模型: {model.model_id} (ID: {model.id}), 供应商ID: {model.supplier_id}")
            # 查询供应商信息
            supplier = db.query(SupplierDB).filter(
                SupplierDB.id == model.supplier_id,
                SupplierDB.is_active == True
            ).first()
            
            if not supplier:
                logger.warning(f"模型 {model_name} 的供应商不存在或未激活")
                return model, None
            
            logger.info(f"找到供应商: {supplier.name} (显示名称: {supplier.display_name}), 活跃状态: {supplier.is_active}")
            
            # 解密API密钥
            if supplier._api_key:
                try:
                    supplier.api_key = decrypt_string(supplier._api_key)
                except Exception as e:
                    logger.warning(f"解密API密钥失败: {e}")
                    supplier.api_key = None
            else:
                supplier.api_key = None
            
            return model, supplier
            
        except Exception as e:
            logger.error(f"查询数据库失败: {e}")
            return None, None
    
    def _get_api_config_from_db(self, db: Session, model_name: str) -> Dict[str, Any]:
        """从数据库获取API配置"""
        model, supplier = self._get_model_and_supplier_from_db(db, model_name)
        
        if not model or not supplier:
            return {}
        
        config = {
            "model": model.model_id,
            "supplier_name": supplier.name,
            "api_endpoint": supplier.api_endpoint,
            "api_key": supplier.api_key,
            "api_key_required": supplier.api_key_required,
            "supplier_display_name": supplier.display_name
        }
        
        logger.info(f"从数据库获取配置: {supplier.display_name} - {model.model_name}")
        return config
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 1.0,
        n: int = 1,
        stop: Optional[List[str]] = None,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        db: Optional[Session] = None,
        fallback_models: Optional[List[str]] = None,
        agent_id: Optional[int] = None,
        enable_thinking_chain: bool = False,
        file_upload_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """聊天补全功能 - 支持数据库配置的多种大模型和智能回退机制"""
        start_time = time.time()
        model_name = model_name or self.default_chat_model
        
        logger.info(f"=== 开始调用模型: {model_name} ===")
        logger.info(f"消息数量: {len(messages)}")
        logger.info(f"使用数据库配置: {db is not None}")
        logger.info(f"回退模型列表: {fallback_models}")
        logger.info(f"代理ID: {agent_id}")
        logger.info(f"启用思考链: {enable_thinking_chain}")
        logger.info(f"文件上传数据: {file_upload_data is not None}")
        
        # 如果没有提供回退模型列表，使用默认回退策略
        if fallback_models is None:
            fallback_models = self._get_fallback_models(model_name, db)
        
        # 记录尝试的模型列表
        logger.info(f"回退模型列表: {fallback_models}")
        
        # 尝试所有可用的模型，包括回退模型
        models_to_try = [model_name] + fallback_models
        
        # 记录尝试历史
        attempt_history = []
        
        for current_model in models_to_try:
            logger.info(f"尝试模型: {current_model}")
            
            # 为每个模型最多重试2次
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    # 检查是否有openai模块
                    import importlib.util
                    has_openai = importlib.util.find_spec('openai') is not None
                    
                    if not has_openai:
                        logger.warning(f"未安装openai库，跳过模型 {current_model}")
                        attempt_history.append({
                            "model": current_model,
                            "status": "skipped",
                            "reason": "未安装openai库"
                        })
                        break
                    
                    import openai
                    
                    # 优先使用数据库配置
                    if db:
                        db_config = self._get_api_config_from_db(db, current_model)
                        if db_config:
                            response = self._call_api_with_db_config(
                                openai, messages, db_config, max_tokens, temperature, 
                                top_p, n, stop, frequency_penalty, presence_penalty, start_time,
                                enable_thinking_chain, file_upload_data
                            )
                            
                            # 检查是否是流式响应（生成器）
                            if hasattr(response, '__iter__') and not isinstance(response, (list, dict)):
                                # 直接返回流式响应生成器
                                logger.info(f"模型 {current_model} 返回流式响应")
                                return response
                            elif response.get("success", False):
                                # 记录回退信息
                                if current_model != model_name:
                                    response["fallback_info"] = f"从 {model_name} 回退到 {current_model}"
                                    response["attempt_history"] = attempt_history
                                    logger.info(f"回退成功: {model_name} -> {current_model}")
                                return response
                            else:
                                error_info = response.get('error', '未知错误')
                                logger.warning(f"模型 {current_model} 数据库配置调用失败，错误: {error_info}")
                                attempt_history.append({
                                    "model": current_model,
                                    "attempt": attempt + 1,
                                    "status": "failed",
                                    "error": error_info,
                                    "config_type": "database"
                                })
                                # 数据库配置失败后，直接尝试下一个模型，不再尝试环境变量配置
                                break
                    
                    # 只有当数据库配置不存在时，才使用环境变量配置
                    response = self._call_api_with_env_config(
                        openai, messages, current_model, max_tokens, temperature, 
                        top_p, n, stop, frequency_penalty, presence_penalty, start_time
                    )
                    
                    # 检查是否是流式响应（生成器）
                    if hasattr(response, '__iter__') and not isinstance(response, (list, dict)):
                        # 直接返回流式响应生成器
                        logger.info(f"模型 {current_model} 返回流式响应")
                        return response
                    elif response.get("success", False):
                        # 记录回退信息
                        if current_model != model_name:
                            response["fallback_info"] = f"从 {model_name} 回退到 {current_model}"
                            response["attempt_history"] = attempt_history
                            logger.info(f"回退成功: {model_name} -> {current_model}")
                        return response
                    else:
                        error_info = response.get('error', '未知错误')
                        logger.warning(f"模型 {current_model} 环境变量配置调用失败")
                        attempt_history.append({
                            "model": current_model,
                            "attempt": attempt + 1,
                            "status": "failed",
                            "error": error_info,
                            "config_type": "environment"
                        })
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"模型 {current_model} 调用异常 (尝试 {attempt + 1}): {error_msg}")
                    import traceback
                    logger.error(f"错误堆栈: {traceback.format_exc()}")
                    
                    attempt_history.append({
                        "model": current_model,
                        "attempt": attempt + 1,
                        "status": "exception",
                        "error": error_msg,
                        "config_type": "unknown"
                    })
                    
                    # 如果是最后一次尝试，继续下一个模型
                    if attempt == max_retries - 1:
                        continue
                    
                    # 等待一段时间后重试
                    wait_time = 1.0 * (attempt + 1)  # 指数退避
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
        
        # 所有模型都失败，返回详细的错误信息
        logger.error(f"所有模型调用失败: {models_to_try}")
        return self._get_all_models_failed_response(models_to_try, start_time, attempt_history)
    
    def _call_api_with_db_config(self, openai, messages, db_config, max_tokens, temperature, 
                                top_p, n, stop, frequency_penalty, presence_penalty, start_time,
                                enable_thinking_chain=False, file_upload_data=None):
        """使用数据库配置调用API"""
        model_name = db_config["model"]
        supplier_name = db_config["supplier_name"]
        api_endpoint = db_config["api_endpoint"]
        api_key = db_config["api_key"]
        api_key_required = db_config["api_key_required"]
        supplier_display_name = db_config["supplier_display_name"]
        
        # 检查API密钥
        if api_key_required and (not api_key or api_key == "your-api-key-here"):
            return self._get_db_config_error_response(supplier_display_name, model_name, start_time)
        
        # 特殊处理Ollama API（直接使用HTTP请求）
        if supplier_display_name == "Ollama" and api_endpoint and "localhost" in api_endpoint:
            return self._call_ollama_api_directly(messages, model_name, api_endpoint, max_tokens, 
                                                temperature, supplier_display_name, start_time)
        
        # 对于其他API，使用直接HTTP请求绕过OpenAI客户端
        result = self._call_api_directly(messages, model_name, api_endpoint, api_key, 
                                     max_tokens, temperature, supplier_display_name, start_time,
                                     enable_thinking_chain, file_upload_data)
        
        # 如果是生成器（流式响应），直接实时返回流式数据
        if hasattr(result, '__iter__') and not isinstance(result, (list, dict)):
            # 直接返回生成器，实现实时流式响应
            return result
        else:
            return result
    
    def _call_api_directly(self, messages, model_name, api_endpoint, api_key, 
                          max_tokens, temperature, supplier_display_name, start_time,
                          enable_thinking_chain=False, file_upload_data=None):
        """直接调用API（绕过OpenAI客户端）"""
        try:
            # 额外检查模型名称，确保正确识别硅基流动的DeepSeek模型
            if "deepseek-ai" in model_name.lower() and supplier_display_name != "硅基流动":
                logger.error(f"配置错误：检测到硅基流动DeepSeek模型 {model_name}，但供应商显示名称为 {supplier_display_name}")
                return self._get_api_error_response(supplier_display_name, f"模型 {model_name} 配置错误，硅基流动模型必须使用硅基流动供应商", model_name, start_time)
            elif "moonshotai" in model_name.lower() and supplier_display_name != "硅基流动":
                logger.error(f"配置错误：检测到硅基流动MoonshotAI模型 {model_name}，但供应商显示名称为 {supplier_display_name}")
                return self._get_api_error_response(supplier_display_name, f"模型 {model_name} 配置错误，硅基流动模型必须使用硅基流动供应商", model_name, start_time)
            elif "siliconflow" in model_name.lower() and supplier_display_name != "硅基流动":
                logger.error(f"配置错误：检测到硅基流动模型 {model_name}，但供应商显示名称为 {supplier_display_name}")
                return self._get_api_error_response(supplier_display_name, f"模型 {model_name} 配置错误，硅基流动模型必须使用硅基流动供应商", model_name, start_time)
            
            # 如果有文件上传数据且供应商支持文件上传，使用文件上传方式
            if file_upload_data and file_upload_data.get('use_upload') and file_upload_data.get('files'):
                logger.info(f"使用文件上传方式处理 {len(file_upload_data['files'])} 个文件")
                return self._call_api_with_file_upload(
                    messages, model_name, api_endpoint, api_key,
                    max_tokens, temperature, supplier_display_name, start_time,
                    file_upload_data
                )
            
            # 根据供应商选择API调用方式
            if supplier_display_name == "硅基流动":
                return self._call_siliconflow_api(
                    messages, model_name, api_endpoint, api_key, 
                    max_tokens, temperature, start_time,
                    enable_thinking_chain=enable_thinking_chain
                )
            elif supplier_display_name in ["DeepSeek", "深度求索"]:
                return self._call_deepseek_api_directly(
                    messages, model_name, api_endpoint, api_key, 
                    max_tokens, temperature, start_time,
                    enable_thinking_chain=enable_thinking_chain
                )
            elif supplier_display_name == "OpenAI":
                return self._call_openai_api_directly(
                    messages, model_name, api_endpoint, api_key, 
                    max_tokens, temperature, start_time
                )
            elif supplier_display_name == "Ollama":
                return self._call_ollama_api_directly(
                    messages, model_name, api_endpoint, 
                    max_tokens, temperature, supplier_display_name, start_time
                )
            elif "dashscope" in supplier_display_name.lower() or "阿里" in supplier_display_name or "aliyun" in supplier_display_name.lower():
                return self._call_dashscope_api(
                    messages, model_name, api_endpoint, api_key, 
                    max_tokens, temperature, supplier_display_name, start_time
                )
            else:
                # 默认使用通用API调用方式
                return self._call_generic_api(
                    messages, model_name, api_endpoint, api_key, 
                    max_tokens, temperature, supplier_display_name, start_time
                )
                
        except Exception as e:
            logger.error(f"API直接调用失败: {str(e)}")
            return self._get_api_error_response(supplier_display_name, str(e), model_name, start_time)
    
    def _call_siliconflow_api(self, messages, model_name, api_endpoint, api_key, 
                             max_tokens, temperature, start_time, retry_without_thinking=False,
                             enable_thinking_chain=False):
        """调用硅基流动API（支持流式响应）"""
        import requests
        import json
        
        logger.info(f"调用硅基流动API: {model_name}，端点: {api_endpoint}，启用思考链: {enable_thinking_chain}")
        
        # 准备请求数据（兼容OpenAI API格式）
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        # 检查是否需要开启思考模式
        # 注意：硅基流动的 API 不支持 enable_thinking 参数，即使模型名称包含 deepseek
        # 硅基流动的 DeepSeek 模型与官方 DeepSeek API 不同，不支持 enable_thinking
        # 所以这里完全禁用 enable_thinking 参数，避免 400 错误
        thinking_enabled = False
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key and api_key != "dummy-key":
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 发送请求，使用stream=True参数处理流式响应
        # 增加超时时间，特别是启用思考模式时
        timeout = 120 if thinking_enabled else 60
        
        try:
            # 检查api_endpoint是否存在
            if not api_endpoint:
                logger.error("硅基流动API端点未配置")
                raise Exception("硅基流动API端点未配置")
            
            logger.info(f"发送硅基流动流式请求，超时时间: {timeout}秒")
            with requests.post(
                f"{api_endpoint}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout
            ) as response:
                
                if response.status_code != 200:
                    error_text = response.text[:200]
                    logger.error(f"硅基流动API调用失败，状态码: {response.status_code}，响应: {error_text}")
                    
                    # 如果是因为不支持 thinking 参数导致的错误，并且这是第一次尝试，则重试不使用 thinking 参数
                    if thinking_enabled and not retry_without_thinking and "does not support parameter enable_thinking" in error_text:
                        logger.warning(f"模型 {model_name} 不支持 thinking 参数，重试不使用 thinking 参数")
                        return self._call_siliconflow_api(messages, model_name, api_endpoint, api_key, 
                                                       max_tokens, temperature, start_time, retry_without_thinking=True)
                    
                    raise Exception(f"硅基流动API调用失败，状态码: {response.status_code}, 响应: {error_text}")
                
                # 确保响应是流式的
                if 'text/event-stream' not in response.headers.get('Content-Type', ''):
                    logger.warning(f"硅基流动API未返回流式响应，Content-Type: {response.headers.get('Content-Type')}")
                    # 尝试解析为普通JSON响应
                    response_data = response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        message = response_data["choices"][0].get("message", {})
                        response_text = message.get("content", "")
                        reasoning_content = message.get("reasoning_content", "")
                        
                        result = {
                            "generated_text": response_text.strip(),
                            "model": model_name,
                            "supplier": "硅基流动",
                            "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": True
                        }
                        if reasoning_content:
                            result["reasoning_content"] = reasoning_content.strip()
                        return result
                    else:
                        raise Exception(f"硅基流动API响应格式不正确")
                
                # 处理流式响应
                full_response = ""
                full_reasoning = ""
                reasoning_sent = False
                
                logger.info(f"开始处理硅基流动流式响应")
                for line in response.iter_lines():
                    if line:
                        # 解码行并移除前缀
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]
                            
                            if line == '[DONE]':
                                logger.info(f"硅基流动流式响应结束")
                                break
                            
                            try:
                                chunk = json.loads(line)
                                
                                # 提取choices部分
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    
                                    # 提取思维链信息
                                    if "reasoning_content" in delta:
                                        reasoning_chunk = delta["reasoning_content"]
                                        if reasoning_chunk is not None:
                                            full_reasoning += reasoning_chunk
                                            
                                            # 实时发送每个思维链信息块，确保前端能够逐步显示
                                            logger.info(f"获取到思维链信息: {reasoning_chunk[:50]}...")
                                            yield {
                                                "type": "thinking",
                                                "content": reasoning_chunk,
                                                "model": model_name,
                                                "supplier": "硅基流动"
                                            }
                                    
                                    # 提取内容信息
                                    if "content" in delta:
                                        content_chunk = delta["content"]
                                        if content_chunk is not None:
                                            full_response += content_chunk
                                            
                                            logger.debug(f"获取到内容块: {content_chunk[:50]}...")
                                            yield {
                                                "type": "content",
                                                "content": content_chunk,
                                                "model": model_name,
                                                "supplier": "硅基流动"
                                            }
                                    
                                    # 检查是否完成
                                    finish_reason = choices[0].get("finish_reason")
                                    if finish_reason:
                                        logger.info(f"硅基流动响应完成，finish_reason: {finish_reason}")
                                        break
                                        
                            except json.JSONDecodeError as e:
                                logger.error(f"解析硅基流动流式响应块失败: {e}，行内容: {line[:100]}...")
                                continue
                
                # 构建最终响应
                execution_time = round((time.time() - start_time) * 1000, 2)
                
                # 记录完整的模型响应信息到日志
                full_response_stripped = full_response.strip()
                full_reasoning_stripped = full_reasoning.strip()
                
                # 记录完整的内容信息
                logger.info(f"硅基流动API调用成功，执行时间: {execution_time}ms")
                logger.info(f"模型: {model_name}，完整生成内容: {full_response_stripped}")
                
                # 记录完整的思维链信息（如果有）
                if full_reasoning_stripped:
                    logger.info(f"模型: {model_name}，完整思维链信息: {full_reasoning_stripped}")
                
                final_response = {
                    "generated_text": full_response_stripped,
                    "model": model_name,
                    "supplier": "硅基流动",
                    "execution_time_ms": execution_time,
                    "success": True
                }
                
                # 如果有思维链信息，添加到响应中
                if full_reasoning_stripped:
                    final_response["reasoning_content"] = full_reasoning_stripped
                
                return final_response
                
        except requests.exceptions.Timeout:
            logger.error(f"硅基流动API调用超时（{timeout}秒）")
            raise Exception(f"硅基流动API调用超时，请检查网络连接或尝试更简单的问题")
        except requests.exceptions.RequestException as e:
            logger.error(f"硅基流动API请求异常: {e}")
            raise Exception(f"硅基流动API请求异常: {e}")
        except Exception as e:
            logger.error(f"硅基流动API调用失败: {e}")
            raise Exception(f"硅基流动API调用失败: {e}")
    
    def _call_deepseek_api_directly(self, messages, model_name, api_endpoint, api_key, 
                                   max_tokens, temperature, start_time, retry_without_thinking=False,
                                   enable_thinking_chain=False):
        """直接调用DeepSeek API（支持流式响应）"""
        import requests
        import json
        
        logger.info(f"调用DeepSeek API: {model_name}，端点: {api_endpoint}，启用思考链: {enable_thinking_chain}")
        
        # 准备请求数据（兼容OpenAI API格式）
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        # 检查是否需要开启思考模式
        # 如果是重试且禁用 thinking，则不启用
        thinking_enabled = False
        if not retry_without_thinking:
            # 只有在非重试情况下才考虑启用思考模式
            if enable_thinking_chain:
                # 如果前端明确启用了思考链，则启用
                payload["enable_thinking"] = True
                thinking_enabled = True
                logger.info(f"为DeepSeek模型 {model_name} 启用思考模式（前端请求）")
            elif "deepseek" in model_name.lower():
                # DeepSeek模型支持thinking参数
                payload["enable_thinking"] = True
                thinking_enabled = True
                logger.info(f"为DeepSeek模型 {model_name} 启用思考模式（自动检测）")
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key and api_key != "dummy-key":
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 发送请求，使用stream=True参数处理流式响应
        timeout = 120 if thinking_enabled else 60
        
        try:
            # 检查api_endpoint是否存在
            if not api_endpoint:
                logger.error("DeepSeek API端点未配置")
                raise Exception("DeepSeek API端点未配置")
            
            logger.info(f"发送DeepSeek流式请求，超时时间: {timeout}秒")
            with requests.post(
                f"{api_endpoint}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout
            ) as response:
                
                if response.status_code != 200:
                    error_text = response.text[:200]
                    logger.error(f"DeepSeek API调用失败，状态码: {response.status_code}，响应: {error_text}")
                    
                    # 如果是因为不支持 thinking 参数导致的错误，并且这是第一次尝试，则重试不使用 thinking 参数
                    if thinking_enabled and not retry_without_thinking and "does not support parameter enable_thinking" in error_text:
                        logger.warning(f"模型 {model_name} 不支持 thinking 参数，重试不使用 thinking 参数")
                        return self._call_deepseek_api_directly(messages, model_name, api_endpoint, api_key, 
                                                             max_tokens, temperature, start_time, retry_without_thinking=True)
                    
                    raise Exception(f"DeepSeek API调用失败，状态码: {response.status_code}, 响应: {error_text}")
                
                # 确保响应是流式的
                if 'text/event-stream' not in response.headers.get('Content-Type', ''):
                    logger.warning(f"DeepSeek API未返回流式响应，Content-Type: {response.headers.get('Content-Type')}")
                    # 尝试解析为普通JSON响应
                    response_data = response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        message = response_data["choices"][0].get("message", {})
                        response_text = message.get("content", "")
                        reasoning_content = message.get("reasoning_content", "")
                        
                        result = {
                            "generated_text": response_text.strip(),
                            "model": model_name,
                            "supplier": "DeepSeek",
                            "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": True
                        }
                        if reasoning_content:
                            result["reasoning_content"] = reasoning_content.strip()
                        return result
                    else:
                        raise Exception(f"DeepSeek API响应格式不正确")
                
                # 处理流式响应
                full_response = ""
                full_reasoning = ""
                reasoning_sent = False
                
                logger.info(f"开始处理DeepSeek流式响应")
                for line in response.iter_lines():
                    if line:
                        # 解码行并移除前缀
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]
                            
                            if line == '[DONE]':
                                logger.info(f"DeepSeek流式响应结束")
                                break
                            
                            try:
                                chunk = json.loads(line)
                                
                                # 提取choices部分
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    
                                    # 提取思维链信息
                                    if "reasoning_content" in delta:
                                        reasoning_chunk = delta["reasoning_content"]
                                        if reasoning_chunk is not None:
                                            full_reasoning += reasoning_chunk
                                            
                                            # 实时发送每个思维链信息块，确保前端能够逐步显示
                                            logger.info(f"获取到思维链信息: {reasoning_chunk[:50]}...")
                                            yield {
                                                "type": "thinking",
                                                "content": reasoning_chunk,
                                                "model": model_name,
                                                "supplier": "DeepSeek"
                                            }
                                    
                                    # 提取内容信息
                                    if "content" in delta:
                                        content_chunk = delta["content"]
                                        if content_chunk is not None:
                                            full_response += content_chunk
                                            
                                            logger.debug(f"获取到内容块: {content_chunk[:50]}...")
                                            yield {
                                                "type": "content",
                                                "content": content_chunk,
                                                "model": model_name,
                                                "supplier": "DeepSeek"
                                            }
                                    
                                    # 检查是否完成
                                    finish_reason = choices[0].get("finish_reason")
                                    if finish_reason:
                                        logger.info(f"DeepSeek响应完成，finish_reason: {finish_reason}")
                                        break
                                        
                            except json.JSONDecodeError as e:
                                logger.error(f"解析DeepSeek流式响应块失败: {e}，行内容: {line[:100]}...")
                                continue
                
                # 构建最终响应
                execution_time = round((time.time() - start_time) * 1000, 2)
                
                # 记录完整的模型响应信息到日志
                full_response_stripped = full_response.strip()
                full_reasoning_stripped = full_reasoning.strip()
                
                # 记录完整的内容信息
                logger.info(f"DeepSeek API调用成功，执行时间: {execution_time}ms")
                logger.info(f"模型: {model_name}，完整生成内容: {full_response_stripped}")
                
                # 记录完整的思维链信息（如果有）
                if full_reasoning_stripped:
                    logger.info(f"模型: {model_name}，完整思维链信息: {full_reasoning_stripped}")
                
                final_response = {
                    "generated_text": full_response_stripped,
                    "model": model_name,
                    "supplier": "DeepSeek",
                    "execution_time_ms": execution_time,
                    "success": True
                }
                
                # 如果有思维链信息，添加到响应中
                if full_reasoning_stripped:
                    final_response["reasoning_content"] = full_reasoning_stripped
                
                return final_response
                
        except requests.exceptions.Timeout:
            logger.error(f"DeepSeek API调用超时（{timeout}秒）")
            raise Exception(f"DeepSeek API调用超时，请检查网络连接或尝试更简单的问题")
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API请求异常: {e}")
            raise Exception(f"DeepSeek API请求异常: {e}")
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            raise Exception(f"DeepSeek API调用失败: {e}")
    
    def _call_openai_api_directly(self, messages, model_name, api_endpoint, api_key, 
                                 max_tokens, temperature, start_time):
        """直接调用OpenAI API（支持流式响应）"""
        import requests
        import json
        
        logger.info(f"调用OpenAI API: {model_name}，端点: {api_endpoint}")
        
        # 准备请求数据
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key and api_key != "dummy-key":
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 发送请求，使用stream=True参数处理流式响应
        timeout = 60
        
        try:
            # 检查api_endpoint是否存在
            if not api_endpoint:
                logger.error("OpenAI API端点未配置")
                raise Exception("OpenAI API端点未配置")
            
            logger.info(f"发送OpenAI流式请求，超时时间: {timeout}秒")
            with requests.post(
                f"{api_endpoint}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"OpenAI API调用失败，状态码: {response.status_code}，响应: {response.text[:200]}")
                    raise Exception(f"OpenAI API调用失败，状态码: {response.status_code}, 响应: {response.text[:200]}")
                
                # 确保响应是流式的
                if 'text/event-stream' not in response.headers.get('Content-Type', ''):
                    logger.warning(f"OpenAI API未返回流式响应，Content-Type: {response.headers.get('Content-Type')}")
                    # 尝试解析为普通JSON响应
                    response_data = response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        message = response_data["choices"][0].get("message", {})
                        response_text = message.get("content", "")
                        
                        result = {
                            "generated_text": response_text.strip(),
                            "model": model_name,
                            "supplier": "OpenAI",
                            "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": True
                        }
                        return result
                    else:
                        raise Exception(f"OpenAI API响应格式不正确")
                
                # 处理流式响应
                full_response = ""
                
                logger.info(f"开始处理OpenAI流式响应")
                for line in response.iter_lines():
                    if line:
                        # 解码行并移除前缀
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]
                            
                            if line == '[DONE]':
                                logger.info(f"OpenAI流式响应结束")
                                break
                            
                            try:
                                chunk = json.loads(line)
                                
                                # 提取choices部分
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    
                                    # 提取内容信息
                                    if "content" in delta:
                                        content_chunk = delta["content"]
                                        full_response += content_chunk
                                        
                                        logger.debug(f"获取到内容块: {content_chunk[:50]}...")
                                        yield {
                                            "type": "content",
                                            "content": content_chunk,
                                            "model": model_name,
                                            "supplier": "OpenAI"
                                        }
                                    
                                    # 检查是否完成
                                    finish_reason = choices[0].get("finish_reason")
                                    if finish_reason:
                                        logger.info(f"OpenAI响应完成，finish_reason: {finish_reason}")
                                        break
                                        
                            except json.JSONDecodeError as e:
                                logger.error(f"解析OpenAI流式响应块失败: {e}，行内容: {line[:100]}...")
                                continue
                
                # 构建最终响应
                execution_time = round((time.time() - start_time) * 1000, 2)
                logger.info(f"OpenAI API调用成功，执行时间: {execution_time}ms")
                
                return {
                    "generated_text": full_response.strip(),
                    "model": model_name,
                    "supplier": "OpenAI",
                    "execution_time_ms": execution_time,
                    "success": True
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"OpenAI API调用超时（{timeout}秒）")
            raise Exception(f"OpenAI API调用超时，请检查网络连接或尝试更简单的问题")
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API请求异常: {e}")
            raise Exception(f"OpenAI API请求异常: {e}")
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise Exception(f"OpenAI API调用失败: {e}")
    
    def _call_generic_api(self, messages, model_name, api_endpoint, api_key, 
                         max_tokens, temperature, supplier_display_name, start_time):
        """通用API调用方式（支持流式响应）"""
        import requests
        import json
        
        logger.info(f"调用通用API: {supplier_display_name}，模型: {model_name}，端点: {api_endpoint}")
        
        # 准备请求数据（兼容OpenAI API格式）
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key and api_key != "dummy-key":
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 发送请求，使用stream=True参数处理流式响应
        timeout = 60
        
        try:
            # 检查api_endpoint是否存在
            if not api_endpoint:
                logger.error(f"{supplier_display_name} API端点未配置")
                raise Exception(f"{supplier_display_name} API端点未配置")
            
            logger.info(f"发送通用API流式请求，超时时间: {timeout}秒")
            with requests.post(
                f"{api_endpoint}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"通用API调用失败，状态码: {response.status_code}，响应: {response.text[:200]}")
                    raise Exception(f"通用API调用失败，状态码: {response.status_code}, 响应: {response.text[:200]}")
                
                # 确保响应是流式的
                if 'text/event-stream' not in response.headers.get('Content-Type', ''):
                    logger.warning(f"通用API未返回流式响应，Content-Type: {response.headers.get('Content-Type')}")
                    # 尝试解析为普通JSON响应
                    response_data = response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        message = response_data["choices"][0].get("message", {})
                        response_text = message.get("content", "")
                        
                        result = {
                            "generated_text": response_text.strip(),
                            "model": model_name,
                            "supplier": supplier_display_name,
                            "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": True
                        }
                        return result
                    else:
                        raise Exception(f"通用API响应格式不正确")
                
                # 处理流式响应
                full_response = ""
                
                logger.info(f"开始处理通用API流式响应")
                for line in response.iter_lines():
                    if line:
                        # 解码行并移除前缀
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]
                            
                            if line == '[DONE]':
                                logger.info(f"通用API流式响应结束")
                                break
                            
                            try:
                                chunk = json.loads(line)
                                
                                # 提取choices部分
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    
                                    # 提取内容信息
                                    if "content" in delta:
                                        content_chunk = delta["content"]
                                        full_response += content_chunk
                                        
                                        logger.debug(f"获取到内容块: {content_chunk[:50]}...")
                                        yield {
                                            "type": "content",
                                            "content": content_chunk,
                                            "model": model_name,
                                            "supplier": supplier_display_name
                                        }
                                    
                                    # 检查是否完成
                                    finish_reason = choices[0].get("finish_reason")
                                    if finish_reason:
                                        logger.info(f"通用API响应完成，finish_reason: {finish_reason}")
                                        break
                                        
                            except json.JSONDecodeError as e:
                                logger.error(f"解析通用API流式响应块失败: {e}，行内容: {line[:100]}...")
                                continue
                
                # 构建最终响应
                execution_time = round((time.time() - start_time) * 1000, 2)
                logger.info(f"通用API调用成功: {supplier_display_name} - {model_name}")
                
                return {
                    "generated_text": full_response.strip(),
                    "model": model_name,
                    "supplier": supplier_display_name,
                    "execution_time_ms": execution_time,
                    "success": True
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"通用API调用超时（{timeout}秒）")
            raise Exception(f"通用API调用超时，请检查网络连接或尝试更简单的问题")
        except requests.exceptions.RequestException as e:
            logger.error(f"通用API请求异常: {e}")
            raise Exception(f"通用API请求异常: {e}")
        except Exception as e:
            logger.error(f"通用API调用失败: {e}")
            raise Exception(f"通用API调用失败: {e}")
    
    def _call_dashscope_api(self, messages, model_name, api_endpoint, api_key, 
                           max_tokens, temperature, supplier_display_name, start_time):
        """调用阿里云百炼（DashScope）API（支持流式响应）"""
        import requests
        import json
        
        logger.info(f"调用阿里云百炼API: {model_name}，端点: {api_endpoint}")
        
        # 准备请求数据（阿里云百炼API格式）
        payload = {
            "model": model_name,
            "input": {
                "messages": messages
            },
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "result_format": "message"
            }
        }
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 发送请求，使用stream=True参数处理流式响应
        timeout = 60
        
        try:
            # 检查api_endpoint是否存在
            if not api_endpoint:
                logger.error("阿里云百炼API端点未配置")
                raise Exception("阿里云百炼API端点未配置")
            
            # 构建正确的API端点URL
            # 阿里云百炼使用 /compatible-mode/v1/chat/completions 端点
            if api_endpoint.endswith('/v1'):
                chat_endpoint = api_endpoint.rstrip('/') + "/compatible-mode/v1/chat/completions"
            else:
                chat_endpoint = api_endpoint.rstrip('/') + "/compatible-mode/v1/chat/completions"
            
            logger.info(f"发送阿里云百炼流式请求，端点: {chat_endpoint}，超时时间: {timeout}秒")
            with requests.post(
                chat_endpoint,
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"阿里云百炼API调用失败，状态码: {response.status_code}，响应: {response.text[:200]}")
                    raise Exception(f"阿里云百炼API调用失败，状态码: {response.status_code}, 响应: {response.text[:200]}")
                
                # 确保响应是流式的
                if 'text/event-stream' not in response.headers.get('Content-Type', ''):
                    logger.warning(f"阿里云百炼API未返回流式响应，Content-Type: {response.headers.get('Content-Type')}")
                    # 尝试解析为普通JSON响应
                    response_data = response.json()
                    if "output" in response_data:
                        output = response_data["output"]
                        if "choices" in output and len(output["choices"]) > 0:
                            message = output["choices"][0].get("message", {})
                            response_text = message.get("content", "")
                            
                            result = {
                                "generated_text": response_text.strip(),
                                "model": model_name,
                                "supplier": supplier_display_name,
                                "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
                                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                                "success": True
                            }
                            return result
                    raise Exception(f"阿里云百炼API响应格式不正确")
                
                # 处理流式响应
                full_response = ""
                
                logger.info(f"开始处理阿里云百炼API流式响应")
                for line in response.iter_lines():
                    if line:
                        # 解码行并移除前缀
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]
                            
                            if line == '[DONE]':
                                logger.info(f"阿里云百炼API流式响应结束")
                                break
                            
                            try:
                                chunk = json.loads(line)
                                
                                # 提取output部分
                                output = chunk.get("output", {})
                                choices = output.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    
                                    # 提取内容信息
                                    if "content" in delta:
                                        content_chunk = delta["content"]
                                        full_response += content_chunk
                                        
                                        logger.debug(f"获取到内容块: {content_chunk[:50]}...")
                                        
                                    # 检查是否完成
                                    finish_reason = choices[0].get("finish_reason")
                                    if finish_reason:
                                        logger.info(f"阿里云百炼API响应完成，finish_reason: {finish_reason}")
                                        break
                                        
                            except json.JSONDecodeError as e:
                                logger.error(f"解析阿里云百炼API流式响应块失败: {e}，行内容: {line[:100]}...")
                                continue
                
                # 构建最终响应
                execution_time = round((time.time() - start_time) * 1000, 2)
                logger.info(f"阿里云百炼API调用成功: {supplier_display_name} - {model_name}")
                
                return {
                    "generated_text": full_response.strip(),
                    "model": model_name,
                    "supplier": supplier_display_name,
                    "execution_time_ms": execution_time,
                    "success": True
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"阿里云百炼API调用超时（{timeout}秒）")
            raise Exception(f"阿里云百炼API调用超时，请检查网络连接或尝试更简单的问题")
        except requests.exceptions.RequestException as e:
            logger.error(f"阿里云百炼API请求异常: {e}")
            raise Exception(f"阿里云百炼API请求异常: {e}")
        except Exception as e:
            logger.error(f"阿里云百炼API调用失败: {e}")
            raise Exception(f"阿里云百炼API调用失败: {e}")
    
    def _call_ollama_api_directly(self, messages, model_name, api_endpoint, max_tokens, 
                                 temperature, supplier_display_name, start_time):
        """直接调用Ollama API（绕过OpenAI客户端）"""
        try:
            import requests
            import json
            
            # 准备请求数据
            payload = {
                "model": model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # 检查api_endpoint是否存在
            if not api_endpoint:
                logger.error("Ollama API端点未配置")
                raise Exception("Ollama API端点未配置")
            
            # 发送请求到Ollama API
            url = f"{api_endpoint}/chat"
            logger.info(f"直接调用Ollama API: {url}")
            
            response = requests.post(
                url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                # 添加详细的调试信息
                logger.info(f"Ollama API响应状态码: {response.status_code}")
                
                try:
                    response_data = response.json()
                    response_text = response_data.get("message", {}).get("content", "")
                    
                    if not response_text:
                        # 尝试不同的响应格式
                        response_text = response_data.get("response", "")
                    
                    logger.info(f"Ollama API调用成功: {model_name}")
                    
                    return {
                        "generated_text": response_text.strip(),
                        "model": model_name,
                        "supplier": supplier_display_name,
                        "tokens_used": 0,  # Ollama不返回token使用信息
                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                        "success": True
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Ollama API响应JSON解析失败: {e}")
                    # 尝试解析流式响应
                    response_text = ""
                    for line in response.text.strip().split('\n'):
                        if line.strip():
                            try:
                                line_data = json.loads(line)
                                if "message" in line_data and "content" in line_data["message"]:
                                    response_text += line_data["message"]["content"]
                                elif "response" in line_data:
                                    response_text += line_data["response"]
                            except json.JSONDecodeError:
                                continue
                    
                    if response_text:
                        logger.info(f"Ollama API流式响应解析成功: {model_name}")
                        return {
                            "generated_text": response_text.strip(),
                            "model": model_name,
                            "supplier": supplier_display_name,
                            "tokens_used": 0,
                            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                            "success": True
                        }
                    else:
                        raise Exception(f"无法解析Ollama API响应: {response.text[:200]}")
            else:
                logger.error(f"Ollama API调用失败，状态码: {response.status_code}")
                raise Exception(f"Ollama API调用失败，状态码: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama API直接调用失败: {str(e)}")
            return self._get_api_error_response(supplier_display_name, str(e), model_name, start_time)
    
    def _call_api_with_env_config(self, openai, messages, model_name, max_tokens, temperature, 
                                 top_p, n, stop, frequency_penalty, presence_penalty, start_time):
        """使用环境变量配置调用API"""
        # 根据模型类型选择API配置
        
        logger.info(f"环境变量配置调用API，模型名称: {model_name}")
        
        # 首先检查是否是硅基流动的模型（通过模型名称中的前缀识别）
        if "deepseek-ai/" in model_name:
            logger.warning(f"检测到硅基流动DeepSeek模型 {model_name}，环境变量配置下不支持，请使用数据库配置")
            # 硅基流动的DeepSeek模型需要通过数据库配置调用
            return self._get_api_error_response("硅基流动", "DeepSeek模型需要通过数据库配置调用", model_name, start_time)
        elif "moonshotai/" in model_name:
            logger.warning(f"检测到硅基流动MoonshotAI模型 {model_name}，环境变量配置下不支持，请使用数据库配置")
            # 硅基流动的月之暗面模型需要通过数据库配置调用
            return self._get_api_error_response("硅基流动", "MoonshotAI模型需要通过数据库配置调用", model_name, start_time)
        elif "siliconflow" in model_name.lower() or "硅基流动" in model_name:
            logger.warning(f"检测到硅基流动模型 {model_name}，环境变量配置下不支持，请使用数据库配置")
            # 硅基流动模型需要通过数据库配置调用
            return self._get_api_error_response("硅基流动", "模型需要通过数据库配置调用", model_name, start_time)
        elif "deepseek" in model_name.lower():
            # DeepSeek官方模型
            logger.info(f"识别为DeepSeek官方模型 {model_name}")
            return self._call_deepseek_api(
                openai, messages, model_name, max_tokens, temperature, 
                top_p, n, stop, frequency_penalty, presence_penalty, start_time
            )
        elif model_name.startswith("gpt-") or model_name in ["gpt-3.5-turbo", "gpt-4"]:
            # OpenAI模型
            logger.info(f"识别为OpenAI模型 {model_name}")
            return self._call_openai_api(
                openai, messages, model_name, max_tokens, temperature, 
                top_p, n, stop, frequency_penalty, presence_penalty, start_time
            )
        elif model_name.startswith("claude-"):
            # Anthropic模型
            logger.info(f"识别为Anthropic模型 {model_name}")
            return self._call_anthropic_api(
                messages, model_name, max_tokens, temperature, start_time
            )
        elif "moonshot" in model_name.lower():
            # Moonshot官方模型
            logger.info(f"识别为Moonshot官方模型 {model_name}")
            # 暂时使用通用API调用方式
            return self._call_openai_api(
                openai, messages, model_name, max_tokens, temperature, 
                top_p, n, stop, frequency_penalty, presence_penalty, start_time
            )
        else:
            # 默认尝试OpenAI API
            logger.info(f"无法识别模型 {model_name}，默认使用OpenAI API调用")
            return self._call_openai_api(
                openai, messages, model_name, max_tokens, temperature, 
                top_p, n, stop, frequency_penalty, presence_penalty, start_time
            )
    
    def _call_deepseek_api(self, openai, messages, model_name, max_tokens, temperature, 
                          top_p, n, stop, frequency_penalty, presence_penalty, start_time):
        """调用DeepSeek API（环境变量配置）"""
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        api_base = getattr(settings, 'DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
        
        if not api_key or api_key == "your-deepseek-api-key-here":
            return self._get_config_error_response("DeepSeek", model_name, start_time)
        
        # 使用直接API调用
        result = self._call_api_directly(messages, model_name, api_base, api_key, 
                                     max_tokens, temperature, "DeepSeek", start_time)
        
        # 如果是生成器，收集所有块
        if hasattr(result, '__iter__') and not isinstance(result, (list, dict)):
            full_response = ""
            full_reasoning = ""
            
            for chunk in result:
                if chunk["type"] == "thinking":
                    full_reasoning += chunk["content"]
                elif chunk["type"] == "content":
                    full_response += chunk["content"]
            
            # 构建最终响应
            execution_time = round((time.time() - start_time) * 1000, 2)
            response = {
                "generated_text": full_response.strip(),
                "model": model_name,
                "supplier": "DeepSeek",
                "execution_time_ms": execution_time,
                "success": True
            }
            
            if full_reasoning:
                response["reasoning_content"] = full_reasoning.strip()
            
            return response
        else:
            return result
    
    def _call_openai_api(self, openai, messages, model_name, max_tokens, temperature, 
                        top_p, n, stop, frequency_penalty, presence_penalty, start_time):
        """调用OpenAI API（环境变量配置）"""
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        api_base = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1')
        
        if not api_key or api_key == "your-openai-api-key-here":
            return self._get_config_error_response("OpenAI", model_name, start_time)
        
        # 使用直接API调用
        result = self._call_api_directly(messages, model_name, api_base, api_key, 
                                     max_tokens, temperature, "OpenAI", start_time)
        
        # 如果是生成器，收集所有块
        if hasattr(result, '__iter__') and not isinstance(result, (list, dict)):
            full_response = ""
            
            for chunk in result:
                if chunk["type"] == "content":
                    full_response += chunk["content"]
            
            # 构建最终响应
            execution_time = round((time.time() - start_time) * 1000, 2)
            response = {
                "generated_text": full_response.strip(),
                "model": model_name,
                "supplier": "OpenAI",
                "execution_time_ms": execution_time,
                "success": True
            }
            
            return response
        else:
            return result
    
    def _call_anthropic_api(self, messages, model_name, max_tokens, temperature, start_time):
        """调用Anthropic API（环境变量配置）"""
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
    
    def _get_db_config_error_response(self, supplier_name, model_name, start_time):
        """获取数据库配置错误响应"""
        error_msg = f"""系统提示: {supplier_name} API配置不完整。

请检查以下配置：
1. 在供应商管理界面设置有效的API密钥
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
        # 智能错误诊断
        error_type = "未知错误"
        suggested_actions = []
        
        # 分析错误类型
        if "timeout" in error_detail.lower() or "timed out" in error_detail.lower():
            error_type = "网络超时"
            suggested_actions = ["检查网络连接", "增加超时时间", "重试请求"]
        elif "unauthorized" in error_detail.lower() or "invalid" in error_detail.lower():
            error_type = "认证失败"
            suggested_actions = ["检查API密钥有效性", "重新配置API密钥", "联系供应商支持"]
        elif "not found" in error_detail.lower():
            error_type = "资源未找到"
            suggested_actions = ["检查模型名称是否正确", "确认模型是否可用", "检查API端点"]
        elif "rate limit" in error_detail.lower():
            error_type = "频率限制"
            suggested_actions = ["等待一段时间后重试", "检查API配额", "联系供应商增加配额"]
        elif "connection" in error_detail.lower():
            error_type = "连接错误"
            suggested_actions = ["检查网络连接", "确认API服务可用", "检查防火墙设置"]
        
        error_msg = f"""系统提示: {provider} API调用失败。

错误类型: {error_type}
错误详情: {error_detail}

可能的原因：
1. API密钥无效或已过期
2. 网络连接问题
3. 模型服务暂时不可用
4. 请求参数不正确

建议操作：
{chr(10).join(f"{i+1}. {action}" for i, action in enumerate(suggested_actions)) if suggested_actions else "1. 检查API配置和网络连接"}

当前模型: {model_name}"""
        
        return {
            "generated_text": error_msg,
            "model": f"{model_name} (API错误)",
            "tokens_used": 0,
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "success": False,
            "error": error_detail,
            "error_type": error_type,
            "suggested_actions": suggested_actions
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

    def _get_fallback_models(self, model_name: str, db: Optional[Session]) -> List[str]:
        """获取回退模型列表"""
        fallback_models = []
        
        # 默认回退模型
        default_fallbacks = ["gpt-3.5-turbo", "gpt-4", "deepseek-chat"]
        
        # 如果提供了数据库连接，尝试从数据库获取可用的模型
        if db:
            try:
                # 查询所有活跃的模型
                active_models = db.query(ModelDB).join(SupplierDB).filter(
                    SupplierDB.is_active == True,
                    ModelDB.model_id != model_name
                ).all()
                
                db_models = [model.model_id for model in active_models]
                # 将数据库中的模型添加到回退列表
                fallback_models.extend(db_models)
            except Exception as e:
                logger.warning(f"从数据库获取回退模型失败: {e}")
        
        # 添加默认回退模型，但排除当前模型和已存在的模型
        for fallback in default_fallbacks:
            if fallback != model_name and fallback not in fallback_models:
                fallback_models.append(fallback)
        
        # 限制回退模型数量，避免无限尝试
        return fallback_models[:5]

    def _get_all_models_failed_response(self, models_tried: List[str], start_time: float, attempt_history: List[Dict] = None) -> Dict[str, Any]:
        """获取所有模型都失败的响应"""
        
        # 分析失败原因
        error_summary = self._analyze_failures(attempt_history)
        
        error_msg = f"""系统提示: 所有尝试的模型都调用失败。

已尝试的模型: {', '.join(models_tried)}

失败分析:
{error_summary}

可能的原因：
1. 所有模型配置都不完整
2. 网络连接问题
3. API服务暂时不可用
4. 所有API密钥都无效或已过期

建议：
1. 检查模型配置和API密钥
2. 验证网络连接
3. 稍后重试
4. 联系技术支持"""
        
        return {
            "generated_text": error_msg,
            "model": f"{models_tried[0]} (所有模型失败)",
            "tokens_used": 0,
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "success": False,
            "error": "所有模型调用失败",
            "models_tried": models_tried,
            "attempt_history": attempt_history,
            "failure_analysis": error_summary
        }
    
    def _call_api_with_file_upload(self, messages, model_name, api_endpoint, api_key,
                                  max_tokens, temperature, supplier_display_name, start_time,
                                  file_upload_data):
        """
        使用文件上传方式调用API
        
        Args:
            messages: 消息列表
            model_name: 模型名称
            api_endpoint: API端点
            api_key: API密钥
            max_tokens: 最大token数
            temperature: 温度参数
            supplier_display_name: 供应商显示名称
            start_time: 开始时间
            file_upload_data: 文件上传数据
            
        Returns:
            API响应
        """
        import requests
        import base64
        import json
        from pathlib import Path
        
        logger.info(f"使用文件上传方式调用API: {model_name}")
        
        try:
            # 准备消息内容，添加文件信息
            enhanced_messages = []
            for msg in messages:
                enhanced_messages.append(msg)
            
            # 添加文件信息到最后一条用户消息
            if file_upload_data and file_upload_data.get('files'):
                files_info = []
                for file_info in file_upload_data['files']:
                    file_path = Path(file_info['path'])
                    if file_path.exists():
                        # 读取文件内容并编码为base64
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                            file_base64 = base64.b64encode(file_content).decode('utf-8')
                        
                        files_info.append({
                            'name': file_info['name'],
                            'type': file_info['mime_type'],
                            'size': file_info['size'],
                            'content': file_base64
                        })
                
                # 将文件信息添加到消息中
                if enhanced_messages and enhanced_messages[-1]['role'] == 'user':
                    last_message = enhanced_messages[-1].copy()
                    last_message['files'] = files_info
                    enhanced_messages[-1] = last_message
            
            # 准备请求数据
            payload = {
                "model": model_name,
                "messages": enhanced_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json"
            }
            
            if api_key and api_key != "dummy-key":
                headers["Authorization"] = f"Bearer {api_key}"
            
            # 发送请求
            timeout = 60
            logger.info(f"发送带文件上传的流式请求，超时时间: {timeout}秒")
            
            with requests.post(
                f"{api_endpoint}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout
            ) as response:
                
                if response.status_code != 200:
                    error_text = response.text[:200]
                    logger.error(f"文件上传API调用失败，状态码: {response.status_code}，响应: {error_text}")
                    raise Exception(f"API调用失败，状态码: {response.status_code}, 响应: {error_text}")
                
                # 确保响应是流式的
                if 'text/event-stream' not in response.headers.get('Content-Type', ''):
                    logger.warning("响应不是流式格式，尝试解析完整响应")
                    full_response = response.json()
                    return self._parse_non_streaming_response(full_response, model_name, start_time)
                
                # 处理流式响应
                def stream_generator():
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str.strip() == '[DONE]':
                                    break
                                
                                try:
                                    data = json.loads(data_str)
                                    if 'choices' in data and len(data['choices']) > 0:
                                        delta = data['choices'][0].get('delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            yield {
                                                'content': content,
                                                'model': model_name,
                                                'success': True
                                            }
                                except json.JSONDecodeError as e:
                                    logger.warning(f"解析流式响应失败: {e}")
                                    continue
                
                return stream_generator()
                
        except Exception as e:
            logger.error(f"文件上传API调用异常: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            # 如果文件上传失败，降级到文本解析方式
            logger.info("文件上传失败，降级到文本解析方式")
            return self._fallback_to_text_parsing(messages, model_name, api_endpoint, api_key,
                                               max_tokens, temperature, supplier_display_name, start_time,
                                               file_upload_data)
    
    def _fallback_to_text_parsing(self, messages, model_name, api_endpoint, api_key,
                                 max_tokens, temperature, supplier_display_name, start_time,
                                 file_upload_data):
        """
        降级到文本解析方式
        
        Args:
            messages: 原始消息列表
            model_name: 模型名称
            api_endpoint: API端点
            api_key: API密钥
            max_tokens: 最大token数
            temperature: 温度参数
            supplier_display_name: 供应商显示名称
            start_time: 开始时间
            file_upload_data: 文件上传数据
            
        Returns:
            API响应
        """
        from app.modules.file.services.file_processor import file_processor_service
        from pathlib import Path
        
        logger.info("降级到文本解析方式")
        
        try:
            # 处理文件内容
            enhanced_messages = []
            for msg in messages:
                enhanced_messages.append(msg)
            
            # 如果有文件，解析文件内容并添加到消息中
            if file_upload_data and file_upload_data.get('files'):
                file_contents = []
                for file_info in file_upload_data['files']:
                    try:
                        file_path = Path(file_info['path'])
                        result = file_processor_service.process_file(
                            file_path=file_path,
                            file_name=file_info['name'],
                            file_type=file_info['type']
                        )
                        file_contents.append(result)
                    except Exception as e:
                        logger.error(f"解析文件 {file_info['name']} 失败: {str(e)}")
                
                # 将文件内容添加到用户消息中
                if file_contents and enhanced_messages and enhanced_messages[-1]['role'] == 'user':
                    last_message = enhanced_messages[-1].copy()
                    file_info_text = "\n\n[附件文件信息]\n"
                    for fc in file_contents:
                        file_info_text += f"\n文件名: {fc['filename']}\n"
                        file_info_text += f"类型: {fc['type']}\n"
                        if fc['type'] in ['text', 'pdf', 'word', 'excel', 'ppt']:
                            content = fc['content']
                            if len(content) > 5000:
                                content = content[:5000] + "\n... (内容过长，已截断)"
                            file_info_text += f"内容:\n{content}\n"
                        else:
                            file_info_text += f"说明: {fc['content']}\n"
                    
                    last_message['content'] += file_info_text
                    enhanced_messages[-1] = last_message
            
            # 使用普通API调用
            if supplier_display_name == "硅基流动":
                return self._call_siliconflow_api(
                    enhanced_messages, model_name, api_endpoint, api_key,
                    max_tokens, temperature, start_time
                )
            elif supplier_display_name == "OpenAI":
                return self._call_openai_api_directly(
                    enhanced_messages, model_name, api_endpoint, api_key,
                    max_tokens, temperature, start_time
                )
            else:
                return self._call_generic_api(
                    enhanced_messages, model_name, api_endpoint, api_key,
                    max_tokens, temperature, supplier_display_name, start_time
                )
                
        except Exception as e:
            logger.error(f"降级到文本解析方式失败: {str(e)}")
            return self._get_api_error_response(supplier_display_name, str(e), model_name, start_time)
    
    def _parse_non_streaming_response(self, response, model_name, start_time):
        """解析非流式响应"""
        try:
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0].get('message', {}).get('content', '')
                return {
                    'generated_text': content,
                    'model': model_name,
                    'tokens_used': response.get('usage', {}).get('total_tokens', 0),
                    'execution_time_ms': round((time.time() - start_time) * 1000, 2),
                    'success': True
                }
            else:
                return self._get_api_error_response(model_name, "响应格式错误", model_name, start_time)
        except Exception as e:
            return self._get_api_error_response(model_name, str(e), model_name, start_time)
    
    def _analyze_failures(self, attempt_history: List[Dict]) -> str:
        """分析失败原因"""
        if not attempt_history:
            return "无详细的失败记录"
        
        # 统计失败类型
        error_types = {}
        config_issues = []
        
        for attempt in attempt_history:
            error = attempt.get('error', '')
            config_type = attempt.get('config_type', '')
            
            # 分析错误类型
            if 'timeout' in error.lower():
                error_types['timeout'] = error_types.get('timeout', 0) + 1
            elif 'unauthorized' in error.lower() or 'invalid' in error.lower():
                error_types['auth'] = error_types.get('auth', 0) + 1
            elif 'not found' in error.lower():
                error_types['not_found'] = error_types.get('not_found', 0) + 1
            elif 'connection' in error.lower():
                error_types['connection'] = error_types.get('connection', 0) + 1
            else:
                error_types['other'] = error_types.get('other', 0) + 1
            
            # 分析配置问题
            if config_type == 'database' and '配置不完整' in error:
                config_issues.append('数据库配置不完整')
            elif config_type == 'environment' and '配置不完整' in error:
                config_issues.append('环境变量配置不完整')
        
        # 生成分析报告
        analysis = []
        if error_types:
            analysis.append("错误类型统计:")
            for error_type, count in error_types.items():
                type_name = {
                    'timeout': '超时错误',
                    'auth': '认证错误', 
                    'not_found': '资源未找到',
                    'connection': '连接错误',
                    'other': '其他错误'
                }.get(error_type, error_type)
                analysis.append(f"  - {type_name}: {count}次")
        
        if config_issues:
            analysis.append("配置问题:")
            for issue in set(config_issues):
                analysis.append(f"  - {issue}")
        
        return '\n'.join(analysis) if analysis else "无法确定具体失败原因"
    
    # 兼容性方法
    def chat(self, messages, **kwargs):
        """兼容chat方法"""
        return self.chat_completion(messages, **kwargs)
    
    def generate_text(self, prompt, **kwargs):
        """兼容generate_text方法"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, **kwargs)


# 创建全局实例
enhanced_llm_service = EnhancedLLMService()