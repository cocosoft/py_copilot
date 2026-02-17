"""对话相关的Schema定义"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """消息基础模型"""
    content: str
    role: str = Field(..., pattern="^(user|assistant|system)$")
    is_visible: bool = True


class MessageCreate(MessageBase):
    """创建消息请求模型"""
    pass


class MessageResponse(MessageBase):
    """消息响应模型"""
    id: int
    created_at: datetime
    conversation_id: int
    
    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """对话基础模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class ConversationCreate(ConversationBase):
    """创建对话请求模型"""
    initial_message: Optional[str] = None


class ConversationUpdate(BaseModel):
    """更新对话请求模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ConversationResponse(ConversationBase):
    """对话响应模型"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """对话详情响应模型，包含消息列表"""
    messages: List[MessageResponse] = []


class MessageListResponse(BaseModel):
    """消息列表响应模型"""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int


class ConversationListResponse(BaseModel):
    """对话列表响应模型"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


class SendMessageRequest(BaseModel):
    """发送消息请求模型"""
    content: str
    use_llm: bool = True
    model_name: Optional[str] = None
    enable_thinking_chain: bool = False
    topic_id: Optional[int] = None
    attached_files: Optional[List[int]] = Field(default_factory=list, description="附件文件ID列表")
    use_file_upload: Optional[bool] = Field(default=None, description="是否使用文件上传方式（None表示自动选择）")


class SendMessageResponse(BaseModel):
    """发送消息响应模型"""
    conversation_id: int
    user_message: MessageResponse
    assistant_message: Optional[MessageResponse] = None
    generated_at: datetime


class TopicBase(BaseModel):
    """话题基础模型"""
    topic_name: str
    topic_summary: Optional[str] = None
    is_active: bool = True


class TopicCreate(TopicBase):
    """创建话题请求模型"""
    pass


class TopicUpdate(BaseModel):
    """更新话题请求模型"""
    topic_name: Optional[str] = None
    topic_summary: Optional[str] = None
    is_active: Optional[bool] = None


class TopicResponse(TopicBase):
    """话题响应模型"""
    id: int
    conversation_id: int
    message_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    """话题列表响应模型"""
    topics: List[TopicResponse]
    total: int
    conversation_id: int


class TopicMessagesResponse(BaseModel):
    """话题消息列表响应模型"""
    messages: List[MessageResponse]
    total: int
    topic_id: int
    conversation_id: int