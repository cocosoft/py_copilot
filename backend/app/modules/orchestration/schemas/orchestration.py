"""智能体编排系统API模型"""
from pydantic import BaseModel, Field
from typing import Optional

class OrchestrationRequest(BaseModel):
    """智能体编排请求模型"""
    query: str = Field(..., description="用户查询文本")
    conversation_id: Optional[str] = Field(None, description="会话ID")
    language: Optional[str] = Field(None, description="语言代码，如zh-CN")

class OrchestrationResponse(BaseModel):
    """智能体编排响应模型"""
    success: bool = Field(..., description="请求是否成功")
    result: Optional[dict] = Field(None, description="编排结果")
    intent: Optional[str] = Field(None, description="识别的意图类型")
    route: Optional[str] = Field(None, description="路由路径")
    error: Optional[str] = Field(None, description="错误信息")
    message: Optional[str] = Field(None, description="响应消息")
