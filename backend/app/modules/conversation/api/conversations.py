"""对话管理相关API路由（简化版）"""
import asyncio
import json
from datetime import datetime
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status, Body, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.security_utils import (
    validate_message_content,
    validate_file,
    sanitize_input
)
from app.modules.conversation.schemas.conversation import SendMessageRequest
from app.schemas.conversation import (
    TopicCreate,
    TopicUpdate,
    TopicResponse,
    TopicListResponse,
    SwitchTopicRequest,
    SwitchTopicResponse
)
from app.modules.conversation.services.topic_service import TopicService
from app.modules.conversation.services.topic_title_generator import TopicTitleGenerator
from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service
from app.modules.llm.services.llm_tasks import llm_tasks
from app.models.supplier_db import SupplierDB, ModelDB
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.conversation import Conversation, Message, Topic

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
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    # 如果对话不存在，自动创建一个新对话
    if not conversation:
        conversation = Conversation(
            id=conversation_id,
            user_id=1,  # 默认用户ID，实际应该从认证中获取
            title=f"对话 {conversation_id}",
            description=""
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        print(f"已自动创建对话: {conversation}")
    
    # 验证消息内容
    validation_result = validate_message_content(request.content)
    if not validation_result['is_valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result['message']
        )
    
    # 使用清理后的内容
    sanitized_content = validation_result['sanitized_content']
    
    # 获取或创建活跃话题
    active_topic = TopicService.get_active_topic(db, conversation_id)
    
    # 如果请求中指定了话题ID，使用指定的话题
    if request.topic_id:
        topic = TopicService.get_topic_by_id(db, request.topic_id)
        if topic:
            active_topic = topic
            # 设置为活跃话题
            TopicService.set_active_topic(db, conversation_id, topic.id)
    
    # 如果没有活跃话题，创建一个新话题
    if not active_topic:
        # 使用默认标题创建话题
        topic_name = "新话题"
        active_topic = TopicService.create_topic(db, conversation_id, topic_name)
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=sanitized_content,
        topic_id=active_topic.id,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 如果话题标题是默认的"新话题"，立即生成更好的标题
    if active_topic.topic_name == "新话题":
        topic_title = TopicTitleGenerator.generate_title_from_messages(db, conversation_id)
        if topic_title != "新话题":
            TopicService.update_topic(db, active_topic.id, topic_name=topic_title)
            active_topic.topic_name = topic_title
    
    # 如果需要使用LLM生成回复
    assistant_message = None
    
    if request.use_llm:
        try:
            # 只获取当前活跃话题的消息作为上下文，而不是整个对话的消息
            conversation_history = db.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.topic_id == active_topic.id
            ).order_by(Message.created_at.asc()).all()
            
            # 构建聊天消息列表
            chat_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation_history
            ]
            chat_messages.append({"role": "user", "content": sanitized_content})
            
            # 使用LLM生成回复
            try:
                # 使用请求中的模型名称，如果没有则使用默认值
                model_name = request.model_name or "gpt-3.5-turbo"
                print(f"调用enhanced_llm_service.chat_completion，模型: {model_name}")
                print(f"聊天消息: {chat_messages}")
                print(f"传递的agent_id参数: {conversation.agent_id}")
                llm_response = enhanced_llm_service.chat_completion(
                    messages=chat_messages,
                    model_name=model_name,
                    db=db,
                    agent_id=conversation.agent_id
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
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_content,
                topic_id=active_topic.id,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            print(f"助手消息创建结果: {assistant_message}")
            
            # 保存思维链信息（如果有）
            reasoning_content = llm_response.get("reasoning_content", "") if isinstance(llm_response, dict) else ""
            if reasoning_content:
                from app.models.chat_enhancements import ChainOfThought
                
                # 分割思维链内容为步骤
                reasoning_steps = reasoning_content.split('\n')
                reasoning_steps = [step.strip() for step in reasoning_steps if step.strip()]
                
                # 创建思维链记录
                chain_of_thought = ChainOfThought(
                    message_id=assistant_message.id,
                    chain_type="step_by_step",
                    reasoning_steps=reasoning_steps,
                    final_answer=ai_content,
                    is_visible=True
                )
                db.add(chain_of_thought)
                db.commit()
                print(f"已保存思维链信息，共 {len(reasoning_steps)} 个步骤")
            
            # 更新话题的消息计数和结束消息ID
            TopicService.increment_message_count(db, active_topic.id, count=2)
            TopicService.update_end_message(db, active_topic.id, assistant_message.id)
            
            # 如果话题标题是默认的"新话题"，尝试生成更好的标题
            if active_topic.topic_name == "新话题":
                topic_title = TopicTitleGenerator.generate_title_from_messages(db, conversation_id)
                if topic_title != "新话题":
                    TopicService.update_topic(db, active_topic.id, topic_name=topic_title)
                    active_topic.topic_name = topic_title
            
        except Exception as e:
            print(f"LLM生成回复失败: {str(e)}")
            # 即使发生异常，也要创建一个模拟回复
            ai_content = f"这是一条模拟回复，基于您的消息：{request.content[:50]}..."
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_content,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
    
    # 构建响应
    response = {
        "conversation_id": conversation_id,
        "user_message": {
            "id": user_message.id,
            "content": user_message.content,
            "role": user_message.role,
            "created_at": user_message.created_at.isoformat() if user_message.created_at else None
        },
        "generated_at": datetime.utcnow().isoformat(),
        "status": "success"
    }
    
    print(f"构建响应，assistant_message存在: {assistant_message is not None}")
    if assistant_message:
        response["assistant_message"] = {
            "id": assistant_message.id,
            "content": assistant_message.content,
            "role": assistant_message.role,
            "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else None
        }
        print(f"响应中包含助手消息: {response['assistant_message']}")
    
    print(f"最终响应: {response}")
    return response


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取对话的消息历史（分页）
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 构建查询
    query = db.query(Message).filter(Message.conversation_id == conversation_id)
    
    # 计算偏移量和总数
    offset = (page - 1) * page_size
    total = query.count()
    
    # 获取消息列表
    messages = query.order_by(Message.created_at.asc()).offset(offset).limit(page_size).all()
    
    # 构建返回数据
    messages_data = []
    for msg in messages:
        messages_data.append({
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        })
    
    return {
        "status": "success",
        "messages": messages_data,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    在对话中发送消息（流式响应版本）
    """
    from app.core.streaming_optimizer import (
        StreamingOptimizer,
        StreamingStrategy,
        StreamingConfig
    )
    
    # 查询对话
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    # 如果对话不存在，自动创建一个新对话
    if not conversation:
        conversation = Conversation(
            id=conversation_id,
            user_id=1,
            title=f"对话 {conversation_id}",
            description=""
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        print(f"已自动创建对话: {conversation}")
    
    # 提取参数
    content = request.content
    use_llm = request.use_llm
    model_name = request.model_name
    enable_thinking_chain = request.enable_thinking_chain
    streaming_strategy = "balanced"
    topic_id = request.topic_id
    
    # 验证消息内容
    validation_result = validate_message_content(content)
    if not validation_result['is_valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result['message']
        )
    
    # 使用清理后的内容
    sanitized_content = validation_result['sanitized_content']
    
    # 获取或创建活跃话题
    active_topic = TopicService.get_active_topic(db, conversation_id)
    
    # 如果请求中指定了话题ID，使用指定的话题
    if topic_id:
        topic = TopicService.get_topic_by_id(db, topic_id)
        if topic:
            active_topic = topic
            # 设置为活跃话题
            TopicService.set_active_topic(db, conversation_id, topic.id)
    
    # 如果没有活跃话题，创建一个新话题
    if not active_topic:
        # 使用默认标题创建话题
        topic_name = "新话题"
        active_topic = TopicService.create_topic(db, conversation_id, topic_name)
    
    # 创建流式响应优化器
    strategy_mapping = {
        "fast": StreamingStrategy.FAST,
        "balanced": StreamingStrategy.BALANCED,
        "smooth": StreamingStrategy.SMOOTH,
        "adaptive": StreamingStrategy.ADAPTIVE
    }
    strategy = strategy_mapping.get(streaming_strategy, StreamingStrategy.BALANCED)
    config = StreamingConfig(strategy=strategy)
    optimizer = StreamingOptimizer(config)
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=sanitized_content,
        topic_id=active_topic.id,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 如果话题标题是默认的"新话题"，立即生成更好的标题
    if active_topic.topic_name == "新话题":
        topic_title = TopicTitleGenerator.generate_title_from_messages(db, conversation_id)
        if topic_title != "新话题":
            TopicService.update_topic(db, active_topic.id, topic_name=topic_title)
            active_topic.topic_name = topic_title
    
    async def stream_generator():
        import json
        
        # 使用同一个数据库会话，避免事务隔离的问题
        stream_db = db
        try:
            # 重新查询对话对象，确保获取最新的对话信息
            conversation = stream_db.query(Conversation).filter(Conversation.id == conversation_id).first()
            
            # 重新查询活跃话题，确保获取最新的话题信息
            active_topic = TopicService.get_active_topic(stream_db, conversation_id)
            
            # 发送话题信息
            topic_data = {
                "type": "topic",
                "topic": {
                    "id": active_topic.id,
                    "title": active_topic.topic_name,
                    "conversation_id": active_topic.conversation_id,
                    "message_count": active_topic.message_count,
                    "created_at": active_topic.created_at.isoformat() if active_topic.created_at else None
                }
            }
            yield f"data: {json.dumps(topic_data, ensure_ascii=False)}\n\n"
            
            # 发送用户消息确认
            user_msg_data = {
                "type": "user_message",
                "content": "消息已收到",
                "message_id": 1
            }
            yield f"data: {json.dumps(user_msg_data, ensure_ascii=False)}\n\n"
            
            if use_llm:
                # 只获取当前活跃话题的消息作为上下文，而不是整个对话的消息
                conversation_history = stream_db.query(Message).filter(
                    Message.conversation_id == conversation_id,
                    Message.topic_id == active_topic.id
                ).order_by(Message.created_at.asc()).all()
                
                # 构建聊天消息列表
                chat_messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in conversation_history
                ]
                chat_messages.append({"role": "user", "content": sanitized_content})
                
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
                        db=stream_db,
                        agent_id=conversation.agent_id
                    )
                    
                    print(f"LLM响应类型: {type(llm_response)}")
                    
                    # 检查是否是流式响应生成器
                    if hasattr(llm_response, '__iter__') and not isinstance(llm_response, (list, dict)):
                        print("检测到流式响应生成器")
                        full_ai_content = ""
                        full_reasoning_content = ""
                        
                        # 直接转发流式响应块，不使用优化器重新生成
                        for chunk in llm_response:
                            print(f"实时转发流式块: {chunk}")
                            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                            
                            if chunk["type"] == "thinking":
                                # 累积思维链信息
                                full_reasoning_content += chunk['content']
                            elif chunk["type"] == "content":
                                # 累积内容信息
                                full_ai_content += chunk['content']
                            
                            # 使用优化器的延迟控制
                            await asyncio.sleep(optimizer.current_delay)
                        
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
                            # 使用优化器生成流式响应
                            async for chunk in optimizer.generate_streaming_chunks(
                                reasoning_content,
                                chunk_type="thinking",
                                metadata={"strategy": strategy.value}
                            ):
                                yield f"data: {json.dumps(chunk)}\n\n"
                        
                        # 如果获取到了回复，使用优化器生成流式响应
                        if ai_content:
                            # 使用优化器生成逐字符流式响应
                            async for chunk in optimizer.generate_character_streaming(
                                ai_content,
                                chunk_type="content",
                                metadata={"strategy": strategy.value}
                            ):
                                yield f"data: {json.dumps(chunk)}\n\n"
                except (AttributeError, TypeError) as e:
                    print(f"chat_completion调用失败: {str(e)}")
                    # 使用错误信息作为回复
                    ai_content = f"抱歉，LLM服务调用失败: {str(e)}"
                    # 直接发送完整的错误消息，不使用optimizer分割
                    error_data = {"type": "content", "content": ai_content}
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                except Exception as e:
                    print(f"chat_completion调用发生其他错误: {str(e)}")
                    # 使用错误信息作为回复
                    ai_content = f"抱歉，处理您的请求时发生异常: {str(e)}"
                    # 直接发送完整的错误消息，不使用optimizer分割
                    error_data = {"type": "content", "content": ai_content}
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                
                # 创建最终的助手消息
                if ai_content:
                    # 重新查询活跃话题，确保获取最新的话题信息
                    active_topic = TopicService.get_active_topic(stream_db, conversation_id)
                    
                    assistant_message = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=ai_content,
                        topic_id=active_topic.id if active_topic else None,
                        created_at=datetime.utcnow()
                    )
                    stream_db.add(assistant_message)
                    stream_db.commit()
                    stream_db.refresh(assistant_message)
                    
                    # 保存思维链信息（如果有）
                    reasoning_content_to_save = full_reasoning_content if 'full_reasoning_content' in locals() else reasoning_content if 'reasoning_content' in locals() else ''
                    if reasoning_content_to_save:
                        from app.models.chat_enhancements import ChainOfThought
                        
                        # 分割思维链内容为步骤
                        reasoning_steps = reasoning_content_to_save.split('\n')
                        reasoning_steps = [step.strip() for step in reasoning_steps if step.strip()]
                        
                        # 创建思维链记录
                        chain_of_thought = ChainOfThought(
                            message_id=assistant_message.id,
                            chain_type="step_by_step",
                            reasoning_steps=reasoning_steps,
                            final_answer=ai_content,
                            is_visible=True
                        )
                        stream_db.add(chain_of_thought)
                        stream_db.commit()
                        print(f"已保存思维链信息，共 {len(reasoning_steps)} 个步骤")
                    
                    # 更新话题的消息计数和结束消息ID
                    if active_topic:
                        TopicService.increment_message_count(stream_db, active_topic.id, count=2)
                        TopicService.update_end_message(stream_db, active_topic.id, assistant_message.id)
                        
                        # 如果话题标题是默认的"新话题"，尝试生成更好的标题
                        if active_topic.topic_name == "新话题":
                            topic_title = TopicTitleGenerator.generate_title_from_messages(stream_db, conversation_id)
                            if topic_title != "新话题":
                                TopicService.update_topic(stream_db, active_topic.id, topic_name=topic_title)
                                active_topic.topic_name = topic_title
                                
                                # 发送话题更新信息
                                topic_data = {
                                    "type": "topic",
                                    "topic": {
                                        "id": active_topic.id,
                                        "title": active_topic.topic_name,
                                        "conversation_id": active_topic.conversation_id,
                                        "message_count": active_topic.message_count,
                                        "created_at": active_topic.created_at.isoformat() if active_topic.created_at else None
                                    }
                                }
                                yield f"data: {json.dumps(topic_data, ensure_ascii=False)}\n\n"
                
                # 发送完成信号
                yield "data: {\"type\": \"complete\", \"content\": \"\"}\n\n"
        except Exception as e:
            # 发送错误信息
            error_msg = f"流式响应生成失败: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
        finally:
            # 不要关闭数据库会话，因为我们使用的是外部传入的 db 会话
            pass
    
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
        # 捕获所有异常，返回友好的错误信息
        return {
            "status": "error",
            "message": f"获取对话模型列表失败: {str(e)}",
            "models": [],
            "total": 0
        }


# ============ 话题管理 API ============

@router.post("/{conversation_id}/topics")
async def create_topic(
    conversation_id: int,
    topic_name: str = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> TopicResponse:
    """
    创建新话题
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 创建话题
    topic = TopicService.create_topic(db, conversation_id, topic_name)
    
    return TopicResponse(
        id=topic.id,
        conversation_id=topic.conversation_id,
        topic_name=topic.topic_name,
        topic_summary=topic.topic_summary,
        is_active=topic.is_active,
        message_count=topic.message_count,
        created_at=topic.created_at,
        updated_at=topic.updated_at
    )


@router.get("/{conversation_id}/topics")
async def list_topics(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
) -> TopicListResponse:
    """
    获取对话的话题列表
    """
    # 查询对话
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    # 如果对话不存在，自动创建一个新对话
    if not conversation:
        conversation = Conversation(
            id=conversation_id,
            user_id=1,  # 默认用户ID，实际应该从认证中获取
            title=f"对话 {conversation_id}",
            description=""
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        print(f"已自动创建对话: {conversation}")
    
    # 获取话题列表
    offset = (page - 1) * page_size
    topics = TopicService.get_conversation_topics(
        db, conversation_id, skip=offset, limit=page_size, active_only=active_only
    )
    
    # 获取总数
    total = db.query(Topic).filter(Topic.conversation_id == conversation_id).count()
    
    return TopicListResponse(
        topics=[
            TopicResponse(
                id=topic.id,
                conversation_id=topic.conversation_id,
                topic_name=topic.topic_name,
                topic_summary=topic.topic_summary,
                is_active=topic.is_active,
                message_count=topic.message_count,
                created_at=topic.created_at,
                updated_at=topic.updated_at
            )
            for topic in topics
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{conversation_id}/topics/{topic_id}")
async def get_topic(
    conversation_id: int,
    topic_id: int,
    db: Session = Depends(get_db)
) -> TopicResponse:
    """
    获取话题详情
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取话题
    topic = TopicService.get_topic_by_id(db, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    return TopicResponse(
        id=topic.id,
        conversation_id=topic.conversation_id,
        topic_name=topic.topic_name,
        topic_summary=topic.topic_summary,
        is_active=topic.is_active,
        message_count=topic.message_count,
        created_at=topic.created_at,
        updated_at=topic.updated_at
    )


@router.put("/{conversation_id}/topics/{topic_id}")
async def update_topic(
    conversation_id: int,
    topic_id: int,
    topic_name: Optional[str] = Body(None, embed=True),
    topic_summary: Optional[str] = Body(None, embed=True),
    is_active: Optional[bool] = Body(None, embed=True),
    db: Session = Depends(get_db)
) -> TopicResponse:
    """
    更新话题信息
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 更新话题
    topic = TopicService.update_topic(
        db, topic_id, topic_name=topic_name, topic_summary=topic_summary, is_active=is_active
    )
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    return TopicResponse(
        id=topic.id,
        conversation_id=topic.conversation_id,
        topic_name=topic.topic_name,
        topic_summary=topic.topic_summary,
        is_active=topic.is_active,
        message_count=topic.message_count,
        created_at=topic.created_at,
        updated_at=topic.updated_at
    )


@router.delete("/{conversation_id}/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    conversation_id: int,
    topic_id: int,
    cascade_delete: bool = Query(True, description="是否级联删除消息"),
    db: Session = Depends(get_db)
) -> None:
    """
    删除话题（支持级联删除消息）
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 删除话题
    success = TopicService.delete_topic(db, topic_id, cascade_delete=cascade_delete)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )


@router.post("/{conversation_id}/topics/{topic_id}/switch")
async def switch_topic(
    conversation_id: int,
    topic_id: int,
    db: Session = Depends(get_db)
) -> SwitchTopicResponse:
    """
    切换到指定话题
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 设置活跃话题
    success = TopicService.set_active_topic(db, conversation_id, topic_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    # 获取话题和消息
    topic = TopicService.get_topic_by_id(db, topic_id)
    messages = TopicService.get_topic_messages(db, topic_id, limit=100)
    
    # 获取所有消息ID
    message_ids = [msg.id for msg in messages]
    
    # 批量查询思维链信息
    chain_of_thoughts = {}
    if message_ids:
        from app.models.chat_enhancements import ChainOfThought
        cot_records = db.query(ChainOfThought).filter(
            ChainOfThought.message_id.in_(message_ids)
        ).all()
        
        # 将思维链信息按消息ID组织
        for cot in cot_records:
            reasoning_steps = []
            try:
                if cot.reasoning_steps:
                    # 尝试解析 JSON 字符串
                    if isinstance(cot.reasoning_steps, str):
                        reasoning_steps = json.loads(cot.reasoning_steps)
                    else:
                        # 如果已经是对象，直接使用
                        reasoning_steps = cot.reasoning_steps
            except (json.JSONDecodeError, TypeError):
                # 如果解析失败，使用空列表
                reasoning_steps = []
            
            chain_of_thoughts[cot.message_id] = {
                "chain_type": cot.chain_type,
                "reasoning_steps": reasoning_steps,
                "final_answer": cot.final_answer,
                "is_visible": cot.is_visible
            }
    
    return SwitchTopicResponse(
        active_topic=TopicResponse(
            id=topic.id,
            conversation_id=topic.conversation_id,
            topic_name=topic.topic_name,
            topic_summary=topic.topic_summary,
            is_active=topic.is_active,
            message_count=topic.message_count,
            created_at=topic.created_at,
            updated_at=topic.updated_at
        ),
        messages=[
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "thinking": chain_of_thoughts.get(msg.id, None)
            }
            for msg in messages
        ]
    )


@router.get("/{conversation_id}/topics/{topic_id}/messages")
async def get_topic_messages(
    conversation_id: int,
    topic_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取话题的消息列表
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取话题
    topic = TopicService.get_topic_by_id(db, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    # 获取消息列表
    offset = (page - 1) * page_size
    messages = TopicService.get_topic_messages(db, topic_id, skip=offset, limit=page_size)
    
    # 获取总数
    total = db.query(Message).filter(Message.topic_id == topic_id).count()
    
    return {
        "status": "success",
        "messages": [
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{conversation_id}/topics/search")
async def search_topics(
    conversation_id: int,
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> TopicListResponse:
    """
    搜索话题
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 搜索话题
    offset = (page - 1) * page_size
    topics = TopicService.search_topics(db, conversation_id, keyword, skip=offset, limit=page_size)
    
    return TopicListResponse(
        topics=[
            TopicResponse(
                id=topic.id,
                conversation_id=topic.conversation_id,
                topic_name=topic.topic_name,
                topic_summary=topic.topic_summary,
                is_active=topic.is_active,
                message_count=topic.message_count,
                created_at=topic.created_at,
                updated_at=topic.updated_at
            )
            for topic in topics
        ],
        total=len(topics),
        page=page,
        page_size=page_size
    )
