"""话题标题生成服务"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.conversation import Message
from app.core.logging_config import logger


class TopicTitleGenerator:
    """话题标题生成器"""
    
    @staticmethod
    def generate_title_from_messages(
        db: Session, 
        conversation_id: int,
        message_limit: int = 10
    ) -> str:
        """
        根据对话消息生成话题标题
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            message_limit: 用于生成标题的消息数量限制
            
        Returns:
            生成的话题标题
        """
        try:
            # 获取最近的对话消息（按创建时间升序排列）
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).limit(message_limit).all()
            
            if not messages:
                return "新对话"
            
            # 获取用户消息
            user_messages = [msg for msg in messages if msg.role == "user"]
            
            if not user_messages:
                return "新对话"
            
            # 使用第一条用户消息生成标题（最早的用户消息）
            first_user_message = user_messages[0]
            content = first_user_message.content.strip()
            
            # 尝试使用 LLM 生成标题
            llm_title = TopicTitleGenerator._generate_with_llm(content)
            if llm_title:
                return llm_title
            
            # LLM 生成失败，使用规则生成
            return TopicTitleGenerator._generate_with_rules(content)
            
        except Exception as e:
            logger.error(f"生成话题标题失败: {e}")
            return "新对话"
    
    @staticmethod
    def _generate_with_llm(content: str) -> Optional[str]:
        """
        使用 LLM 生成话题标题
        
        Args:
            content: 用户消息内容
            
        Returns:
            生成的话题标题，如果失败则返回None
        """
        try:
            # TODO: 集成 LLM 服务生成标题
            # 这里需要调用 LLM 服务，传入用户消息内容
            # 要求 LLM 生成一个简洁的话题标题（不超过20字）
            
            # 暂时返回 None，使用规则生成
            return None
            
        except Exception as e:
            logger.warning(f"LLM 生成话题标题失败: {e}")
            return None
    
    @staticmethod
    def _generate_with_rules(content: str) -> str:
        """
        使用规则生成话题标题
        
        Args:
            content: 用户消息内容
            
        Returns:
            生成的话题标题
        """
        # 移除多余的空白字符
        content = content.strip()
        
        # 截取前 20 个字符作为标题
        if len(content) <= 20:
            return content
        
        # 如果超过 20 字，截取并添加省略号
        title = content[:20]
        
        # 尝试在词边界处截断
        if "。" in title:
            title = title.split("。")[0]
        elif "？" in title:
            title = title.split("？")[0]
        elif "！" in title:
            title = title.split("！")[0]
        elif "，" in title:
            title = title.split("，")[0]
        elif " " in title:
            title = title.split(" ")[0]
        
        # 确保不超过 20 字
        if len(title) > 20:
            title = title[:20]
        
        return title
    
    @staticmethod
    def generate_summary_from_messages(
        db: Session,
        conversation_id: int,
        message_limit: int = 20
    ) -> Optional[str]:
        """
        根据对话消息生成话题摘要
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            message_limit: 用于生成摘要的消息数量限制
            
        Returns:
            生成的话题摘要，如果失败则返回None
        """
        try:
            # 获取最近的对话消息
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(message_limit).all()
            
            if not messages:
                return None
            
            # 合并消息内容
            content_list = []
            for msg in messages:
                role = "用户" if msg.role == "user" else "助手"
                content_list.append(f"{role}: {msg.content}")
            
            full_content = "\n".join(content_list)
            
            # 尝试使用 LLM 生成摘要
            summary = TopicTitleGenerator._generate_summary_with_llm(full_content)
            if summary:
                return summary
            
            # LLM 生成失败，返回 None
            return None
            
        except Exception as e:
            logger.error(f"生成话题摘要失败: {e}")
            return None
    
    @staticmethod
    def _generate_summary_with_llm(content: str) -> Optional[str]:
        """
        使用 LLM 生成话题摘要
        
        Args:
            content: 对话消息内容
            
        Returns:
            生成的话题摘要，如果失败则返回None
        """
        try:
            # TODO: 集成 LLM 服务生成摘要
            # 这里需要调用 LLM 服务，传入对话内容
            # 要求 LLM 生成一个简洁的对话摘要
            
            # 暂时返回 None
            return None
            
        except Exception as e:
            logger.warning(f"LLM 生成话题摘要失败: {e}")
            return None
