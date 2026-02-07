"""对话管理相关API路由"""
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, status, Body, Depends
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
    
    # 如果需要使用LLM生成回复
    if request.use_llm:
        assistant_message = MessageProcessingService.process_message_with_llm(
            db, conversation, user_message, active_topic, request
        )
        return {
            "user_message": user_message,
            "assistant_message": assistant_message
        }
    
    return {"user_message": user_message}


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