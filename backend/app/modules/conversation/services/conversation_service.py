"""对话服务层，处理对话业务逻辑"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message, Topic
from app.modules.conversation.schemas.conversation import SendMessageRequest


class ConversationService:
    """对话服务类"""
    
    @staticmethod
    def get_conversation(db: Session, conversation_id: int) -> Optional[Conversation]:
        """获取对话"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    @staticmethod
    def create_conversation(db: Session, user_id: int, title: str, description: str = "") -> Conversation:
        """创建对话"""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            description=description
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def update_conversation(db: Session, conversation: Conversation, **kwargs) -> Conversation:
        """更新对话信息"""
        for key, value in kwargs.items():
            setattr(conversation, key, value)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def delete_conversation(db: Session, conversation_id: int) -> bool:
        """删除对话"""
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_conversation_messages(db: Session, conversation_id: int, skip: int = 0, limit: int = 50) -> List[Message]:
        """获取对话消息"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_user_message(db: Session, conversation_id: int, content: str, topic_id: Optional[int] = None) -> Message:
        """创建用户消息"""
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            topic_id=topic_id
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        return user_message
    
    @staticmethod
    def create_assistant_message(db: Session, conversation_id: int, content: str, topic_id: Optional[int] = None) -> Message:
        """创建助手消息"""
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            topic_id=topic_id
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        return assistant_message