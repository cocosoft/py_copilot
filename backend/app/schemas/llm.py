"""LLM相关的Schema定义"""
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    """LLM基础请求模型"""
    prompt: str
    model_name: Optional[str] = None
    max_tokens: int = Field(default=1000, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=5)


class LLMTextCompletionRequest(LLMRequest):
    """文本补全请求模型"""
    stop: Optional[List[str]] = None
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    agent_id: Optional[int] = None


class LLMMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class LLMChatCompletionRequest(BaseModel):
    """聊天补全请求模型"""
    messages: List[LLMMessage]
    model_name: Optional[str] = None
    max_tokens: int = Field(default=1000, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=5)
    stop: Optional[List[str]] = None
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    agent_id: Optional[int] = None


class LLMResponse(BaseModel):
    """LLM响应基础模型"""
    model: str
    generated_text: str
    tokens_used: int
    execution_time_ms: float


class LLMTextCompletionResponse(LLMResponse):
    """文本补全响应模型"""
    original_prompt: str


class LLMChatCompletionResponse(LLMResponse):
    """聊天补全响应模型"""
    conversation_history: List[LLMMessage]


class TaskRequest(BaseModel):
    """任务处理请求模型"""
    task_type: str = Field(..., pattern="^(summarize|generate_code|translate|sentiment|qa|extract_info|expand|paraphrase|classify|generate_ideas|generate_content|correct_grammar)$")
    text: str
    options: Optional[Dict[str, Any]] = None


class ParaphraseRequest(BaseModel):
    """文本改写请求模型"""
    text: str
    options: Optional[Dict[str, Any]] = None


class ClassifyRequest(BaseModel):
    """文本分类请求模型"""
    text: str
    options: Optional[Dict[str, Any]] = None


class ExtractInfoRequest(BaseModel):
    """信息提取请求模型"""
    text: str
    options: Optional[Dict[str, Any]] = None


class ExpandTextRequest(BaseModel):
    """文本扩写请求模型"""
    text: str
    options: Optional[Dict[str, Any]] = None


class IdeasRequest(BaseModel):
    """创意生成请求模型"""
    topic: str
    options: Optional[Dict[str, Any]] = None


class ContentRequest(BaseModel):
    """内容生成请求模型"""
    topic: str
    options: Optional[Dict[str, Any]] = None


class GrammarRequest(BaseModel):
    """语法纠正请求模型"""
    text: str
    options: Optional[Dict[str, Any]] = None


class ConversationCreateRequest(BaseModel):
    """创建对话请求模型"""
    options: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """消息响应模型"""
    role: str
    content: str


class ConversationCreateResponse(BaseModel):
    """创建对话响应模型"""
    conversation_id: str
    system_role: Optional[str] = None
    model: str
    created_at: str


class ConversationProcessRequest(BaseModel):
    """处理对话请求模型"""
    messages: List[LLMMessage]
    options: Optional[Dict[str, Any]] = None


class ConversationProcessResponse(BaseModel):
    """处理对话响应模型"""
    response: MessageResponse
    execution_time_ms: float
    tokens_used: int
    model: str


class TaskResponse(BaseModel):
    """任务处理响应模型"""
    task_type: str
    result: Union[str, Dict, List]
    execution_time_ms: float
    tokens_used: int


class ModelInfoResponse(BaseModel):
    """模型信息响应模型"""
    name: str
    provider: str
    type: str
    max_tokens: int
    description: Optional[str] = None
    is_default: bool


class AvailableModelsResponse(BaseModel):
    """可用模型列表响应模型"""
    models: List[ModelInfoResponse]
    total: int