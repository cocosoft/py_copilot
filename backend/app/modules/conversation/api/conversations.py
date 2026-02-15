"""对话管理相关API路由"""
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator
import json
import asyncio

from fastapi import APIRouter, HTTPException, Query, status, Body, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security_utils import validate_message_content
from app.modules.conversation.schemas.conversation import (
    SendMessageRequest, 
    TopicCreate, 
    TopicUpdate, 
    TopicResponse, 
    TopicListResponse, 
    TopicMessagesResponse,
    MessageResponse
)
from app.modules.conversation.services.conversation_service import ConversationService
from app.modules.conversation.services.topic_service import TopicService
from app.modules.conversation.services.message_processing_service import MessageProcessingService
from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service
from app.models.conversation import Conversation, Message, Topic

router = APIRouter()


@router.post("/")
async def create_conversation(
    title: str = "新对话",
    description: str = "",
    initial_message: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    创建新对话
    """
    # TODO: 这里应该从认证信息中获取真实的用户ID
    user_id = 1
    
    conversation = ConversationService.create_conversation(
        db, 
        user_id=user_id, 
        title=title, 
        description=description
    )
    
    # 如果提供了初始消息
    if initial_message:
        ConversationService.create_user_message(
            db,
            conversation_id=conversation.id,
            content=initial_message
        )
    
    return conversation


@router.get("/")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取对话列表
    """
    offset = (page - 1) * page_size
    
    # 查询对话列表
    conversations = db.query(Conversation).offset(offset).limit(page_size).all()
    total = db.query(Conversation).count()
    
    # 将 SQLAlchemy 对象转换为字典
    conversations_data = []
    for conv in conversations:
        conversations_data.append({
            "id": conv.id,
            "user_id": conv.user_id,
            "title": conv.title,
            "description": conv.description,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
        })
    
    return {
        "conversations": conversations_data,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{conversation_id}")
async def get_conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取对话详情及消息历史
    """
    conversation = ConversationService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取所有消息
    messages = ConversationService.get_conversation_messages(db, conversation_id, limit=1000)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "description": conversation.description,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": messages
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    更新对话信息
    """
    conversation = ConversationService.get_conversation(db, conversation_id)
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
    
    updated_conversation = ConversationService.update_conversation(db, conversation, **update_data)
    return updated_conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    删除对话
    """
    success = ConversationService.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )


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
    conversation = ConversationService.get_conversation(db, conversation_id)
    
    # 如果对话不存在，自动创建一个新对话
    if not conversation:
        # TODO: 这里应该从认证信息中获取真实的用户ID
        user_id = 1
        conversation = ConversationService.create_conversation(
            db, user_id, f"对话 {conversation_id}", ""
        )
    
    # 验证消息内容
    validation_result = validate_message_content(request.content)
    if not validation_result['is_valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result['message']
        )
    
    # 使用清理后的内容
    sanitized_content = validation_result['sanitized_content']
    
    # 处理附件文件
    file_info = MessageProcessingService.process_attached_files(db, request)
    if file_info:
        sanitized_content = sanitized_content + file_info
    
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
    user_message = ConversationService.create_user_message(
        db, conversation_id, sanitized_content, active_topic.id
    )
    
    # 将用户消息转换为可序列化的字典
    user_message_dict = {
        "id": user_message.id,
        "conversation_id": user_message.conversation_id,
        "role": user_message.role,
        "content": user_message.content,
        "token_count": user_message.token_count,
        "model_used": user_message.model_used,
        "response_time": user_message.response_time,
        "topic_id": user_message.topic_id,
        "created_at": user_message.created_at.isoformat() if user_message.created_at else None
    }
    
    # 如果需要使用LLM生成回复
    if request.use_llm:
        assistant_message = MessageProcessingService.process_message_with_llm(
            db, conversation, user_message, active_topic, request
        )
        
        # 将助手消息转换为可序列化的字典
        assistant_message_dict = None
        if assistant_message:
            assistant_message_dict = {
                "id": assistant_message.id,
                "conversation_id": assistant_message.conversation_id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "token_count": assistant_message.token_count,
                "model_used": assistant_message.model_used,
                "response_time": assistant_message.response_time,
                "topic_id": assistant_message.topic_id,
                "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else None
            }
        
        return {
            "user_message": user_message_dict,
            "assistant_message": assistant_message_dict
        }
    
    return {"user_message": user_message_dict}


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    在对话中发送消息（流式响应）
    """
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        conversation = ConversationService.get_conversation(db, conversation_id)
        
        if not conversation:
            user_id = 1
            conversation = ConversationService.create_conversation(
                db, user_id, f"对话 {conversation_id}", ""
            )
        
        validation_result = validate_message_content(request.content)
        if not validation_result['is_valid']:
            yield f"data: {json.dumps({'status': 'error', 'error': validation_result['message']})}\n\n"
            return
        
        sanitized_content = validation_result['sanitized_content']
        
        file_info = MessageProcessingService.process_attached_files(db, request)
        if file_info:
            sanitized_content = sanitized_content + file_info
        
        active_topic = TopicService.get_active_topic(db, conversation_id)
        
        if request.topic_id:
            topic = TopicService.get_topic_by_id(db, request.topic_id)
            if topic:
                active_topic = topic
                TopicService.set_active_topic(db, conversation_id, topic.id)
        
        if not active_topic:
            topic_name = "新话题"
            active_topic = TopicService.create_topic(db, conversation_id, topic_name)
        
        user_message = ConversationService.create_user_message(
            db, conversation_id, sanitized_content, active_topic.id
        )
        
        conversation_history = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.topic_id == active_topic.id
        ).order_by(Message.created_at.asc()).all()
        
        chat_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history
        ]
        
        model_name = request.model_name or "gpt-3.5-turbo"
        
        try:
            llm_response = enhanced_llm_service.chat_completion(
                messages=chat_messages,
                model_name=model_name,
                db=db,
                agent_id=getattr(conversation, 'agent_id', None),
                enable_thinking_chain=request.enable_thinking_chain
            )
            
            full_response = ""
            full_reasoning = ""
            last_reasoning_len = 0  # 记录上次发送的思维链长度
            
            # 缓冲区设置：合并小的数据块以提高性能
            content_buffer = ""
            thinking_buffer = ""
            buffer_size = 20  # 缓冲区大小：累积20个字符后发送
            
            if hasattr(llm_response, '__iter__') and not isinstance(llm_response, (list, dict)):
                for chunk in llm_response:
                    if isinstance(chunk, dict):
                        # 处理 type: "thinking" 格式的思维链数据
                        if chunk.get("type") == "thinking":
                            thinking_content = chunk.get("content", "")
                            if thinking_content:
                                full_reasoning += thinking_content
                                thinking_buffer += thinking_content
                                # 缓冲区满时发送
                                if len(thinking_buffer) >= buffer_size:
                                    yield f"data: {json.dumps({'status': 'streaming', 'thinking': thinking_buffer})}\n\n"
                                    thinking_buffer = ""
                        
                        # 处理 type: "content" 格式的内容数据
                        elif chunk.get("type") == "content":
                            content = chunk.get("content", "")
                            if content:
                                full_response += content
                                content_buffer += content
                                # 缓冲区满时发送
                                if len(content_buffer) >= buffer_size:
                                    yield f"data: {json.dumps({'status': 'streaming', 'chunk': content_buffer})}\n\n"
                                    content_buffer = ""
                        
                        # 处理 success 格式的最终响应
                        elif chunk.get("success", False):
                            text = chunk.get("generated_text", "")
                            reasoning = chunk.get("reasoning_content", "")
                            if text:
                                full_response = text
                            if reasoning:
                                new_reasoning = reasoning[last_reasoning_len:]
                                if new_reasoning:
                                    full_reasoning = reasoning
                                    last_reasoning_len = len(reasoning)
                                    thinking_buffer += new_reasoning
                        
                        # 处理 content 字段格式
                        elif "content" in chunk and chunk.get("type") != "thinking":
                            content = chunk.get("content", "")
                            if content:
                                full_response += content
                                content_buffer += content
                                # 缓冲区满时发送
                                if len(content_buffer) >= buffer_size:
                                    yield f"data: {json.dumps({'status': 'streaming', 'chunk': content_buffer})}\n\n"
                                    content_buffer = ""
                        
                        # 处理 reasoning_content 字段（增量发送）
                        reasoning = chunk.get("reasoning_content", "")
                        if reasoning and len(reasoning) > last_reasoning_len:
                            new_reasoning = reasoning[last_reasoning_len:]
                            full_reasoning = reasoning
                            last_reasoning_len = len(reasoning)
                            thinking_buffer += new_reasoning
                    
                    elif isinstance(chunk, str):
                        full_response += chunk
                        content_buffer += chunk
                        # 缓冲区满时发送
                        if len(content_buffer) >= buffer_size:
                            yield f"data: {json.dumps({'status': 'streaming', 'chunk': content_buffer})}\n\n"
                            content_buffer = ""
                    
                    await asyncio.sleep(0)
                
                # 流结束时发送剩余缓冲区数据
                if thinking_buffer:
                    yield f"data: {json.dumps({'status': 'streaming', 'thinking': thinking_buffer})}\n\n"
                if content_buffer:
                    yield f"data: {json.dumps({'status': 'streaming', 'chunk': content_buffer})}\n\n"
            elif isinstance(llm_response, dict):
                if llm_response.get("success", False):
                    full_response = llm_response.get("generated_text", "")
                    reasoning = llm_response.get("reasoning_content", "")
                    
                    if reasoning:
                        yield f"data: {json.dumps({'status': 'streaming', 'thinking': reasoning})}\n\n"
                    
                    if full_response:
                        chunk_size = 50
                        for i in range(0, len(full_response), chunk_size):
                            chunk = full_response[i:i+chunk_size]
                            yield f"data: {json.dumps({'status': 'streaming', 'chunk': chunk})}\n\n"
                            await asyncio.sleep(0.01)
                else:
                    error_msg = llm_response.get("error", "LLM调用失败")
                    yield f"data: {json.dumps({'status': 'error', 'error': error_msg})}\n\n"
                    return
            else:
                full_response = str(llm_response) if llm_response else "抱歉，无法生成回复。"
                yield f"data: {json.dumps({'status': 'streaming', 'chunk': full_response})}\n\n"
            
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
                topic_id=active_topic.id,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            
            assistant_message_dict = {
                "id": assistant_message.id,
                "conversation_id": assistant_message.conversation_id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "token_count": assistant_message.token_count,
                "model_used": assistant_message.model_used,
                "response_time": assistant_message.response_time,
                "topic_id": assistant_message.topic_id,
                "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else None
            }
            
            yield f"data: {json.dumps({'status': 'completed', 'assistant_message': assistant_message_dict})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{conversation_id}/topics")
async def get_conversation_topics(
    conversation_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
) -> TopicListResponse:
    """
    获取对话的话题列表
    """
    topics = TopicService.get_conversation_topics(
        db, 
        conversation_id, 
        skip=skip, 
        limit=limit,
        active_only=active_only
    )
    
    topic_responses = [TopicResponse.model_validate(topic) for topic in topics]
    
    return TopicListResponse(
        topics=topic_responses,
        total=len(topic_responses),
        conversation_id=conversation_id
    )


@router.post("/{conversation_id}/topics")
async def create_topic(
    conversation_id: int,
    topic_data: TopicCreate,
    db: Session = Depends(get_db)
) -> TopicResponse:
    """
    创建新话题
    """
    topic = TopicService.create_topic(
        db,
        conversation_id,
        topic_data.topic_name,
        topic_data.topic_summary
    )
    
    return TopicResponse.model_validate(topic)


@router.get("/{conversation_id}/topics/{topic_id}")
async def get_topic_detail(
    conversation_id: int,
    topic_id: int,
    db: Session = Depends(get_db)
) -> TopicResponse:
    """
    获取话题详情
    """
    topic = TopicService.get_topic_by_id(db, topic_id)
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    if topic.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="话题不属于该对话"
        )
    
    return TopicResponse.model_validate(topic)


@router.put("/{conversation_id}/topics/{topic_id}")
async def update_topic(
    conversation_id: int,
    topic_id: int,
    topic_data: TopicUpdate,
    db: Session = Depends(get_db)
) -> TopicResponse:
    """
    更新话题信息
    """
    topic = TopicService.get_topic_by_id(db, topic_id)
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    if topic.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="话题不属于该对话"
        )
    
    updated_topic = TopicService.update_topic(
        db,
        topic_id,
        topic_name=topic_data.topic_name,
        topic_summary=topic_data.topic_summary,
        is_active=topic_data.is_active
    )
    
    return TopicResponse.model_validate(updated_topic)


@router.delete("/{conversation_id}/topics/{topic_id}")
async def delete_topic(
    conversation_id: int,
    topic_id: int,
    cascade_delete: bool = Query(True),
    db: Session = Depends(get_db)
) -> None:
    """
    删除话题
    """
    topic = TopicService.get_topic_by_id(db, topic_id)
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    if topic.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="话题不属于该对话"
        )
    
    success = TopicService.delete_topic(db, topic_id, cascade_delete)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除话题失败"
        )


@router.post("/{conversation_id}/topics/{topic_id}/switch")
async def switch_topic(
    conversation_id: int,
    topic_id: int,
    db: Session = Depends(get_db)
) -> TopicResponse:
    """
    切换对话的活跃话题
    """
    topic = TopicService.get_topic_by_id(db, topic_id)
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    if topic.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="话题不属于该对话"
        )
    
    success = TopicService.set_active_topic(db, conversation_id, topic_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换话题失败"
        )
    
    updated_topic = TopicService.get_topic_by_id(db, topic_id)
    return TopicResponse.model_validate(updated_topic)


@router.get("/{conversation_id}/topics/{topic_id}/messages")
async def get_topic_messages(
    conversation_id: int,
    topic_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> TopicMessagesResponse:
    """
    获取话题的消息列表
    """
    topic = TopicService.get_topic_by_id(db, topic_id)
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    if topic.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="话题不属于该对话"
        )
    
    messages = TopicService.get_topic_messages(db, topic_id, skip=skip, limit=limit)
    
    message_responses = [
        MessageResponse.model_validate(msg) for msg in messages
    ]
    
    return TopicMessagesResponse(
        messages=message_responses,
        total=len(message_responses),
        topic_id=topic_id,
        conversation_id=conversation_id
    )


@router.get("/{conversation_id}/topics/search")
async def search_topics(
    conversation_id: int,
    keyword: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> TopicListResponse:
    """
    搜索话题
    """
    topics = TopicService.search_topics(
        db,
        conversation_id,
        keyword,
        skip=skip,
        limit=limit
    )
    
    topic_responses = [TopicResponse.model_validate(topic) for topic in topics]
    
    return TopicListResponse(
        topics=topic_responses,
        total=len(topic_responses),
        conversation_id=conversation_id
    )