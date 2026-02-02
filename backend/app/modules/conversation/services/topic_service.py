"""话题管理服务类"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.conversation import Topic, Message, Conversation
from app.core.logging_config import logger


class TopicService:
    """话题管理服务"""
    
    @staticmethod
    def create_topic(db: Session, conversation_id: int, topic_name: str, topic_summary: Optional[str] = None) -> Topic:
        """
        创建新话题
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            topic_name: 话题名称
            topic_summary: 话题摘要
            
        Returns:
            创建的话题对象
        """
        try:
            topic = Topic(
                conversation_id=conversation_id,
                topic_name=topic_name,
                topic_summary=topic_summary,
                is_active=True,
                message_count=0
            )
            db.add(topic)
            db.commit()
            db.refresh(topic)
            
            logger.info(f"创建话题成功: topic_id={topic.id}, topic_name={topic_name}")
            return topic
        except Exception as e:
            db.rollback()
            logger.error(f"创建话题失败: {e}")
            raise
    
    @staticmethod
    def get_topic_by_id(db: Session, topic_id: int) -> Optional[Topic]:
        """
        根据ID获取话题
        
        Args:
            db: 数据库会话
            topic_id: 话题ID
            
        Returns:
            话题对象，如果不存在则返回None
        """
        return db.query(Topic).filter(Topic.id == topic_id).first()
    
    @staticmethod
    def get_conversation_topics(
        db: Session, 
        conversation_id: int, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = False
    ) -> List[Topic]:
        """
        获取对话的话题列表
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            skip: 跳过记录数
            limit: 返回记录数
            active_only: 是否只返回活跃话题
            
        Returns:
            话题列表
        """
        query = db.query(Topic).filter(Topic.conversation_id == conversation_id)
        
        if active_only:
            query = query.filter(Topic.is_active == True)
        
        return query.order_by(desc(Topic.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_topic_messages(
        db: Session, 
        topic_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Message]:
        """
        获取话题的消息列表
        
        Args:
            db: 数据库会话
            topic_id: 话题ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            消息列表
        """
        return db.query(Message).filter(
            Message.topic_id == topic_id
        ).order_by(Message.created_at).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_topic(
        db: Session, 
        topic_id: int, 
        topic_name: Optional[str] = None,
        topic_summary: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Topic]:
        """
        更新话题信息
        
        Args:
            db: 数据库会话
            topic_id: 话题ID
            topic_name: 新的话题名称
            topic_summary: 新的话题摘要
            is_active: 新的活跃状态
            
        Returns:
            更新后的话题对象，如果不存在则返回None
        """
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        
        if not topic:
            return None
        
        if topic_name is not None:
            topic.topic_name = topic_name
        if topic_summary is not None:
            topic.topic_summary = topic_summary
        if is_active is not None:
            topic.is_active = is_active
        
        db.commit()
        db.refresh(topic)
        
        logger.info(f"更新话题成功: topic_id={topic_id}")
        return topic
    
    @staticmethod
    def delete_topic(db: Session, topic_id: int, cascade_delete: bool = True) -> bool:
        """
        删除话题（支持级联删除消息）
        
        Args:
            db: 数据库会话
            topic_id: 话题ID
            cascade_delete: 是否级联删除消息
            
        Returns:
            是否删除成功
        """
        try:
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            
            if not topic:
                logger.warning(f"话题不存在: topic_id={topic_id}")
                return False
            
            if cascade_delete:
                # 级联删除该话题下的所有消息
                deleted_count = db.query(Message).filter(Message.topic_id == topic_id).delete()
                logger.info(f"级联删除消息: topic_id={topic_id}, deleted_count={deleted_count}")
            
            # 删除话题
            db.delete(topic)
            db.commit()
            
            logger.info(f"删除话题成功: topic_id={topic_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"删除话题失败: {e}")
            raise
    
    @staticmethod
    def increment_message_count(db: Session, topic_id: int, count: int = 1) -> bool:
        """
        增加话题的消息计数
        
        Args:
            db: 数据库会话
            topic_id: 话题ID
            count: 增加的数量
            
        Returns:
            是否更新成功
        """
        try:
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            
            if not topic:
                return False
            
            topic.message_count += count
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"更新消息计数失败: {e}")
            raise
    
    @staticmethod
    def update_end_message(db: Session, topic_id: int, message_id: int) -> bool:
        """
        更新话题的结束消息ID
        
        Args:
            db: 数据库会话
            topic_id: 话题ID
            message_id: 消息ID
            
        Returns:
            是否更新成功
        """
        try:
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            
            if not topic:
                return False
            
            topic.end_message_id = message_id
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"更新结束消息ID失败: {e}")
            raise
    
    @staticmethod
    def get_active_topic(db: Session, conversation_id: int) -> Optional[Topic]:
        """
        获取对话的活跃话题
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            
        Returns:
            活跃话题对象，如果不存在则返回None
        """
        return db.query(Topic).filter(
            and_(
                Topic.conversation_id == conversation_id,
                Topic.is_active == True
            )
        ).first()
    
    @staticmethod
    def set_active_topic(db: Session, conversation_id: int, topic_id: int) -> bool:
        """
        设置对话的活跃话题
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            topic_id: 话题ID
            
        Returns:
            是否设置成功
        """
        try:
            # 将该对话的所有话题设置为非活跃
            db.query(Topic).filter(
                Topic.conversation_id == conversation_id
            ).update({"is_active": False})
            
            # 设置指定话题为活跃
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            
            if not topic:
                return False
            
            topic.is_active = True
            db.commit()
            
            logger.info(f"设置活跃话题: conversation_id={conversation_id}, topic_id={topic_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"设置活跃话题失败: {e}")
            raise
    
    @staticmethod
    def search_topics(
        db: Session, 
        conversation_id: int, 
        keyword: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Topic]:
        """
        搜索话题
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            keyword: 搜索关键词
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            匹配的话题列表
        """
        return db.query(Topic).filter(
            and_(
                Topic.conversation_id == conversation_id,
                or_(
                    Topic.topic_name.like(f"%{keyword}%"),
                    Topic.topic_summary.like(f"%{keyword}%")
                )
            )
        ).order_by(desc(Topic.created_at)).offset(skip).limit(limit).all()
