"""对话管理相关API路由（简化版）"""
import asyncio
import json
from datetime import datetime
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status, Body, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.modules.conversation.schemas.conversation import SendMessageRequest
from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service
from app.modules.llm.services.llm_tasks import llm_tasks
from app.models.supplier_db import SupplierDB, ModelDB
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation

# 导入思维链生成函数
def generate_thinking_chain_steps(content: str) -> List[str]:
    """根据消息内容生成思维链步骤"""
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['计算', '数学', '公式', '等于', '加', '减', '乘', '除']):
        return [
            "🧮 识别数学计算问题...",
            "🔢 解析数学表达式...",
            "📊 执行计算步骤...",
            "✅ 验证计算结果..."
        ]
    elif any(word in content_lower for word in ['解释', '什么是', '定义', '概念']):
        return [
            "📚 识别概念解释需求...",
            "🔍 检索相关知识库...",
            "💡 构建解释框架...",
            "📝 组织解释内容..."
        ]
    elif any(word in content_lower for word in ['代码', '编程', '函数', '变量']):
        return [
            "💻 分析编程问题...",
            "🔧 设计解决方案...",
            "📋 编写代码逻辑...",
            "✅ 验证代码正确性..."
        ]
    elif any(word in content_lower for word in ['翻译', '语言', '英文', '中文']):
        return [
            "🌐 识别翻译需求...",
            "📖 分析原文语义...",
            "🔄 构建翻译映射...",
            "✍️ 优化翻译表达..."
        ]
    else:
        return []

router = APIRouter()


# 模拟内存存储
class MockStorage:
    def __init__(self):
        self.conversations = []
        self.messages = []
        self.conversation_id_counter = 1
        self.message_id_counter = 1
        self.topics = []  # 话题列表
        self.topic_id_counter = 1
    
    def create_conversation(self, title: str = "新对话", description: str = "") -> Dict[str, Any]:
        conversation = {
            "id": self.conversation_id_counter,
            "title": title,
            "description": description,
            "is_active": True,
            "message_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_message_at": None
        }
        self.conversations.append(conversation)
        self.conversation_id_counter += 1
        return conversation
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        for conv in self.conversations:
            if conv["id"] == conversation_id:
                return conv
        return None
    
    def update_conversation(self, conversation_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        conv = self.get_conversation(conversation_id)
        if conv:
            for field, value in update_data.items():
                if field in conv:
                    conv[field] = value
            conv["updated_at"] = datetime.utcnow()
        return conv
    
    def delete_conversation(self, conversation_id: int) -> None:
        self.conversations = [conv for conv in self.conversations if conv["id"] != conversation_id]
        self.messages = [msg for msg in self.messages if msg["conversation_id"] != conversation_id]
    
    def create_message(self, conversation_id: int, content: str, role: str) -> Dict[str, Any]:
        message = {
            "id": self.message_id_counter,
            "conversation_id": conversation_id,
            "content": content,
            "role": role,
            "is_visible": True,
            "created_at": datetime.utcnow()
        }
        self.messages.append(message)
        self.message_id_counter += 1
        
        # 更新对话消息计数和最后消息时间
        conv = self.get_conversation(conversation_id)
        if conv:
            conv["message_count"] = sum(1 for msg in self.messages if msg["conversation_id"] == conversation_id)
            conv["last_message_at"] = datetime.utcnow()
        
        return message
    
    def get_conversation_messages(self, conversation_id: int, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        messages = [msg for msg in self.messages if msg["conversation_id"] == conversation_id and msg["is_visible"]]
        messages.sort(key=lambda x: x["created_at"])
        return messages[skip:skip+limit]
    
    def get_all_conversations(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        conversations = sorted(
            self.conversations,
            key=lambda x: (x["last_message_at"] or datetime.min, x["created_at"]),
            reverse=True
        )
        return conversations[skip:skip+limit]
    
    # 话题管理方法
    def create_topic(self, title: str, description: str = "", conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """创建话题"""
        topic = {
            "id": self.topic_id_counter,
            "title": title,
            "description": description,
            "conversation_id": conversation_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        self.topics.append(topic)
        self.topic_id_counter += 1
        return topic
    
    def get_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """获取话题"""
        for topic in self.topics:
            if topic["id"] == topic_id:
                return topic
        return None
    
    def get_topics_by_conversation(self, conversation_id: int) -> List[Dict[str, Any]]:
        """获取对话的所有话题"""
        return [topic for topic in self.topics if topic["conversation_id"] == conversation_id]
    
    def update_topic(self, topic_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新话题"""
        topic = self.get_topic(topic_id)
        if topic:
            for field, value in update_data.items():
                if field in topic:
                    topic[field] = value
            topic["updated_at"] = datetime.utcnow()
        return topic
    
    def delete_topic(self, topic_id: int) -> None:
        """删除话题"""
        self.topics = [topic for topic in self.topics if topic["id"] != topic_id]
    
    def switch_topic(self, conversation_id: int, topic_id: int) -> bool:
        """切换到指定话题"""
        # 将所有话题设置为非活跃状态
        for topic in self.topics:
            if topic["conversation_id"] == conversation_id:
                topic["is_active"] = False
        
        # 激活指定话题
        target_topic = self.get_topic(topic_id)
        if target_topic and target_topic["conversation_id"] == conversation_id:
            target_topic["is_active"] = True
            target_topic["updated_at"] = datetime.utcnow()
            return True
        return False
    
    def get_active_topic(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """获取当前活跃话题"""
        for topic in self.topics:
            if topic["conversation_id"] == conversation_id and topic["is_active"]:
                return topic
        return None

# 创建模拟存储实例
mock_storage = MockStorage()


@router.post("/")
async def create_conversation(
    title: str = "新对话",
    description: str = "",
    initial_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建新对话
    """
    conversation = mock_storage.create_conversation(title, description)
    
    # 如果提供了初始消息
    if initial_message:
        mock_storage.create_message(conversation["id"], initial_message, "user")
        conversation = mock_storage.get_conversation(conversation["id"])
    
    return conversation


@router.get("/")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    获取对话列表
    """
    offset = (page - 1) * page_size
    conversations = mock_storage.get_all_conversations(skip=offset, limit=page_size)
    total = len(mock_storage.conversations)
    
    return {
        "conversations": conversations,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{conversation_id}")
async def get_conversation_detail(conversation_id: int) -> Dict[str, Any]:
    """
    获取对话详情及消息历史
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取所有消息
    messages = mock_storage.get_conversation_messages(conversation_id, limit=1000)
    
    return {
        **conversation,
        "messages": messages
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Dict[str, Any]:
    """
    更新对话信息
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if is_active is not None:
        update_data["is_active"] = is_active
    
    updated_conversation = mock_storage.update_conversation(conversation_id, update_data)
    return updated_conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: int) -> None:
    """
    删除对话
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    mock_storage.delete_conversation(conversation_id)


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    在对话中发送消息
    """
    # 查询对话
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        # 如果对话不存在，自动创建一个新对话
        conversation = mock_storage.create_conversation(title=f"对话 {conversation_id}")
        print(f"已自动创建对话: {conversation}")
    
    if not conversation.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话已被关闭"
        )
    
    # 创建用户消息
    user_message = mock_storage.create_message(conversation_id, request.content, "user")
    
    # 如果需要使用LLM生成回复
    assistant_message = None
    if request.use_llm:
        try:
            # 获取对话历史
            conversation_history = mock_storage.get_conversation_messages(conversation_id)
            
            # 构建聊天消息列表
            chat_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation_history
            ]
            chat_messages.append({"role": "user", "content": request.content})
            
            # 使用LLM生成回复
            try:
                # 使用请求中的模型名称，如果没有则使用默认值
                model_name = request.model_name or "gpt-3.5-turbo"
                print(f"调用enhanced_llm_service.chat_completion，模型: {model_name}")
                print(f"聊天消息: {chat_messages}")
                print(f"传递的agent_id参数: {conversation.get('agent_id')}")
                llm_response = enhanced_llm_service.chat_completion(
                    messages=chat_messages,
                    model_name=model_name,
                    db=db,
                    agent_id=conversation.get("agent_id")
                )
                print(f"LLM响应: {llm_response}")
                
                # 检查LLM调用是否成功
                if llm_response.get("success", True):
                    ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
                    print(f"提取的AI内容: {ai_content}")
                else:
                    # 如果调用失败，使用失败原因作为回复
                    ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
                    print(f"LLM调用失败，返回错误信息: {ai_content}")
                    # 如果有详细的失败分析，也加入到回复中
                    if "failure_analysis" in llm_response:
                        ai_content += f"\n\n详细分析: {llm_response['failure_analysis']}"
            except (AttributeError, TypeError) as e:
                print(f"chat_completion调用失败: {str(e)}")
                # 使用错误信息作为回复
                ai_content = f"抱歉，LLM服务调用失败: {str(e)}"
            except Exception as e:
                print(f"chat_completion调用发生其他错误: {str(e)}")
                # 使用错误信息作为回复
                ai_content = f"抱歉，处理您的请求时发生异常: {str(e)}"
            
            # 创建助手回复消息
            print(f"创建助手消息，内容: {ai_content}")
            assistant_message = mock_storage.create_message(conversation_id, ai_content, "assistant")
            print(f"助手消息创建结果: {assistant_message}")
            
        except Exception as e:
            print(f"LLM生成回复失败: {str(e)}")
            # 即使发生异常，也要创建一个模拟回复
            ai_content = f"这是一条模拟回复，基于您的消息：{request.content[:50]}..."
            assistant_message = mock_storage.create_message(conversation_id, ai_content, "assistant")
    
    # 构建响应
    response = {
        "conversation_id": conversation_id,
        "user_message": user_message,
        "generated_at": datetime.utcnow()
    }
    
    print(f"构建响应，assistant_message存在: {assistant_message is not None}")
    if assistant_message:
        response["assistant_message"] = assistant_message
        print(f"响应中包含助手消息: {response['assistant_message']}")
    
    print(f"最终响应: {response}")
    return response


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    获取对话的消息历史（分页）
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 获取消息列表
    messages = mock_storage.get_conversation_messages(conversation_id, skip=offset, limit=page_size)
    total = sum(1 for msg in mock_storage.messages if msg["conversation_id"] == conversation_id and msg["is_visible"])
    
    return {
        "messages": messages,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: int,
    body: dict = Body(...),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    在对话中发送消息（流式响应版本）
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        # 如果对话不存在，自动创建一个新对话
        conversation = mock_storage.create_conversation(title=f"对话 {conversation_id}")
        print(f"已自动创建对话: {conversation}")
    
    if not conversation.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话已被关闭"
        )
    
    # 提取参数
    content = body.get("content", "")
    use_llm = body.get("use_llm", True)
    model_name = body.get("model_name")
    enable_thinking_chain = body.get("enable_thinking_chain", False)
    
    # 创建用户消息
    user_message = mock_storage.create_message(conversation_id, content, "user")
    
    async def stream_generator():
        try:
            # 发送用户消息确认
            yield "data: {\"type\": \"user_message\", \"content\": \"消息已收到\", \"message_id\": 1}\n\n"
            
            if use_llm:
                # 首先获取对话历史
                conversation_history = mock_storage.get_conversation_messages(conversation_id)
                
                # 构建聊天消息列表
                chat_messages = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in conversation_history
                ]
                chat_messages.append({"role": "user", "content": content})
                
                # 使用LLM生成回复
                ai_content = ""
                reasoning_content = ""
                try:
                    # 使用请求中的模型名称，如果没有则使用默认值
                    llm_model_name = model_name or "gpt-3.5-turbo"
                    print(f"调用enhanced_llm_service.chat_completion，模型: {llm_model_name}")
                    print(f"聊天消息: {chat_messages}")
                    
                    llm_response = enhanced_llm_service.chat_completion(
                        messages=chat_messages,
                        model_name=llm_model_name,
                        db=db,
                        agent_id=conversation.get("agent_id")
                    )
                    
                    print(f"LLM响应类型: {type(llm_response)}")
                    
                    # 检查是否是流式响应生成器
                    if hasattr(llm_response, '__iter__') and not isinstance(llm_response, (list, dict)):
                        print("检测到流式响应生成器")
                        full_ai_content = ""
                        full_reasoning_content = ""
                        
                        # 实时转发流式响应块，避免等待时间加倍
                        for chunk in llm_response:
                            print(f"实时转发流式块: {chunk}")
                            
                            if chunk["type"] == "thinking":
                                # 累积思维链信息并实时转发
                                full_reasoning_content += chunk['content']
                                # 实时发送累积的思维链信息
                                yield f"data: {json.dumps({'type': 'thinking', 'content': full_reasoning_content})}\n\n"
                            elif chunk["type"] == "content":
                                # 累积内容信息并实时转发
                                full_ai_content += chunk['content']
                                # 实时发送累积的内容信息
                                yield f"data: {json.dumps({'type': 'content', 'content': full_ai_content})}\n\n"
                            
                            # 控制发送速度
                            await asyncio.sleep(0.05)
                        
                        ai_content = full_ai_content
                    else:
                        # 处理非流式响应
                        print(f"LLM响应: {llm_response}")
                        
                        # 检查LLM调用是否成功
                        if llm_response.get("success", True):
                            ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
                            print(f"提取的AI内容: {ai_content}")
                            
                            # 检查是否有思维链信息
                            reasoning_content = llm_response.get("reasoning_content", "")
                            print(f"提取的思维链内容: {reasoning_content}")
                        else:
                            # 如果调用失败，使用失败原因作为回复
                            ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
                            print(f"LLM调用失败，返回错误信息: {ai_content}")
                            # 如果有详细的失败分析，也加入到回复中
                            if "failure_analysis" in llm_response:
                                ai_content += f"\n\n详细分析: {llm_response['failure_analysis']}"
                        
                        # 检查是否启用了思维链，如果启用则发送思维链信息
                        if enable_thinking_chain and reasoning_content:
                            # 如果有思维链信息，发送给前端
                            yield f"data: {json.dumps({'type': 'thinking', 'content': reasoning_content})}\n\n"
                            await asyncio.sleep(0.5)  # 缩短等待时间，提高响应速度
                        
                        # 如果获取到了回复，逐字符流式发送
                        if ai_content:
                            # 等待一小段时间后再开始发送内容
                            await asyncio.sleep(0.5)
                            
                            # 逐字符发送回复内容
                            if len(ai_content) < 10:
                                # 非常短的回复
                                yield f"data: {json.dumps({'type': 'content', 'content': ai_content})}\n\n"
                                await asyncio.sleep(0.2)
                            else:
                                # 按字符逐个发送，确保分块正确
                                for i in range(1, len(ai_content) + 1):
                                    current_text = ai_content[:i]
                                    yield f"data: {json.dumps({'type': 'content', 'content': current_text})}\n\n"
                                    # 控制发送速度
                                    await asyncio.sleep(0.05)
                except (AttributeError, TypeError) as e:
                    print(f"chat_completion调用失败: {str(e)}")
                    # 使用错误信息作为回复
                    ai_content = f"抱歉，LLM服务调用失败: {str(e)}"
                    yield f"data: {json.dumps({'type': 'content', 'content': ai_content})}\n\n"
                except Exception as e:
                    print(f"chat_completion调用发生其他错误: {str(e)}")
                    # 使用错误信息作为回复
                    ai_content = f"抱歉，处理您的请求时发生异常: {str(e)}"
                    yield f"data: {json.dumps({'type': 'content', 'content': ai_content})}\n\n"
                
                # 创建最终的助手消息
                if ai_content:
                    mock_storage.create_message(conversation_id, ai_content, "assistant")
                
                # 发送完成信号
                yield "data: {\"type\": \"complete\", \"content\": \"\"}\n\n"
        except Exception as e:
            # 发送错误信息
            error_msg = f"流式响应生成失败: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control, Content-Type",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/models/conversation")
async def get_conversation_models(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    获取已启用的供应商的对话模型列表
    
    返回具有对话能力的模型列表，包括模型ID、名称、供应商信息等
    """
    try:
        # 获取所有已启用的供应商
        enabled_suppliers = db.query(SupplierDB).filter(SupplierDB.is_active == True).all()
        enabled_supplier_ids = [s.id for s in enabled_suppliers]
        
        # 获取所有已启用的供应商的模型
        enabled_models = db.query(ModelDB).filter(
            ModelDB.supplier_id.in_(enabled_supplier_ids),
            ModelDB.is_active == True
        ).all()
        
        # 检查对话相关能力
        conversation_capabilities = db.query(ModelCapability).filter(
            ModelCapability.name.ilike("%conversation%") | 
            ModelCapability.name.ilike("%chat%") |
            ModelCapability.name.ilike("%对话%") |
            ModelCapability.display_name.ilike("%对话%")
        ).all()
        
        conversation_capability_ids = [c.id for c in conversation_capabilities]
        
        # 筛选具有对话能力的模型
        conversation_models = []
        
        for model in enabled_models:
            # 检查模型的能力关联
            associations = db.query(ModelCapabilityAssociation).filter(
                ModelCapabilityAssociation.model_id == model.id
            ).all()
            
            # 获取模型对应的能力
            model_capabilities = []
            for assoc in associations:
                capability = db.query(ModelCapability).filter(
                    ModelCapability.id == assoc.capability_id
                ).first()
                if capability:
                    model_capabilities.append(capability)
            
            # 检查是否有对话相关能力
            has_conversation = False
            for capability in model_capabilities:
                if any(keyword in capability.name.lower() for keyword in ['conversation', 'chat', '对话']) or \
                   any(keyword in capability.display_name.lower() for keyword in ['对话']):
                    has_conversation = True
                    break
            
            # 如果模型没有明确的能力关联，假设所有语言模型都有对话能力
            if not model_capabilities and model.model_name and any(keyword in model.model_name.lower() for keyword in ['chat', '对话', 'conversation']):
                has_conversation = True
            
            # 如果没有明确的能力关联，但模型是语言模型，也假设有对话能力
            if not model_capabilities and not has_conversation:
                # 检查模型名称是否包含常见语言模型关键词
                language_model_keywords = ['gpt', 'claude', 'gemini', 'llama', 'qwen', 'deepseek', 'glm', 'kimi', 'moonshot', 'baidu', 'tencent', '360', 'xunfei', 'jd', 'kuaishou', 'doubao', 'abab']
                if any(keyword in model.model_name.lower() for keyword in language_model_keywords):
                    has_conversation = True
            
            supplier = db.query(SupplierDB).filter(SupplierDB.id == model.supplier_id).first()
            
            if has_conversation:
                # 构建模型LOGO路径
                model_logo = None
                if model.logo:
                    if model.logo.startswith('http'):
                        model_logo = model.logo
                    elif model.logo.startswith('/'):
                        # 如果是绝对路径，保持原样
                        model_logo = model.logo
                    else:
                        # 相对路径，添加完整路径
                        model_logo = f"/logos/models/{model.logo}"
                
                # 构建供应商LOGO路径
                supplier_logo = None
                if supplier and supplier.logo:
                    if supplier.logo.startswith('http'):
                        supplier_logo = supplier.logo
                    elif supplier.logo.startswith('/'):
                        # 如果是绝对路径，保持原样
                        supplier_logo = supplier.logo
                    else:
                        # 相对路径，添加完整路径
                        supplier_logo = f"/logos/providers/{supplier.logo}"
                
                conversation_models.append({
                    'id': model.id,
                    'model_id': model.model_id,
                    'model_name': model.model_name,
                    'description': model.description,
                    'logo': model_logo,
                    'supplier_id': model.supplier_id,
                    'supplier_name': supplier.name if supplier else "未知供应商",
                    'supplier_display_name': supplier.display_name if supplier else "未知供应商",
                    'supplier_logo': supplier_logo,
                    'is_default': model.is_default,
                    'capabilities': [{
                        'id': c.id,
                        'name': c.name,
                        'display_name': c.display_name
                    } for c in model_capabilities]
                })
        
        # 按模型名称排序
        conversation_models.sort(key=lambda x: x['model_name'])
        
        return {
            "status": "success",
            "message": f"成功获取 {len(conversation_models)} 个对话模型",
            "models": conversation_models,
            "total": len(conversation_models)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话模型列表失败: {str(e)}"
        )


# 话题管理API
@router.post("/{conversation_id}/topics")
async def create_topic(
    conversation_id: int,
    title: str = Body(..., description="话题标题"),
    description: str = Body("", description="话题描述")
) -> Dict[str, Any]:
    """
    为对话创建新话题
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 创建话题
    topic = mock_storage.create_topic(title, description, conversation_id)
    return {
        "status": "success",
        "topic": topic
    }


@router.get("/{conversation_id}/topics")
async def list_topics(conversation_id: int) -> Dict[str, Any]:
    """
    获取对话的所有话题
    """
    # 即使对话不存在，也返回空话题列表而不是404
    # 获取话题列表
    topics = mock_storage.get_topics_by_conversation(conversation_id)
    return {
        "status": "success",
        "topics": topics
    }


@router.put("/{conversation_id}/topics/{topic_id}")
async def update_topic(
    conversation_id: int,
    topic_id: int,
    title: Optional[str] = Body(None, description="新标题"),
    description: Optional[str] = Body(None, description="新描述")
) -> Dict[str, Any]:
    """
    更新话题信息
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 验证话题存在且属于该对话
    topic = mock_storage.get_topic(topic_id)
    if not topic or topic["conversation_id"] != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    # 更新话题
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    
    updated_topic = mock_storage.update_topic(topic_id, update_data)
    return {
        "status": "success",
        "topic": updated_topic
    }


@router.delete("/{conversation_id}/topics/{topic_id}")
async def delete_topic(conversation_id: int, topic_id: int) -> Dict[str, Any]:
    """
    删除话题
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 验证话题存在且属于该对话
    topic = mock_storage.get_topic(topic_id)
    if not topic or topic["conversation_id"] != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    # 删除话题
    mock_storage.delete_topic(topic_id)
    return {
        "status": "success",
        "message": "话题删除成功"
    }


@router.post("/{conversation_id}/topics/{topic_id}/switch")
async def switch_topic(conversation_id: int, topic_id: int) -> Dict[str, Any]:
    """
    切换到指定话题
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 验证话题存在且属于该对话
    topic = mock_storage.get_topic(topic_id)
    if not topic or topic["conversation_id"] != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    # 切换话题
    success = mock_storage.switch_topic(conversation_id, topic_id)
    if success:
        return {
            "status": "success",
            "message": "话题切换成功",
            "active_topic": mock_storage.get_active_topic(conversation_id)
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="话题切换失败"
        )


@router.get("/{conversation_id}/active_topic")
async def get_active_topic(conversation_id: int) -> Dict[str, Any]:
    """
    获取当前活跃话题
    """
    # 即使对话不存在，也返回None而不是404
    # 获取活跃话题
    active_topic = mock_storage.get_active_topic(conversation_id)
    return {
        "status": "success",
        "active_topic": active_topic
    }