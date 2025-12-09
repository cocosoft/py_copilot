"""智能体数据验证模式"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, computed_field


class AgentBase(BaseModel):
    """智能体基础信息"""
    name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    avatar: Optional[str] = Field(None, description="智能体头像")
    prompt: str = Field(..., description="智能体提示词")
    knowledge_base: Optional[str] = Field(None, description="关联的知识库")
    is_public: Optional[bool] = Field(False, description="是否公开")
    is_recommended: Optional[bool] = Field(False, description="是否推荐")
    is_favorite: Optional[bool] = Field(False, description="是否收藏")


class AgentCreate(AgentBase):
    """创建智能体请求"""
    pass


class AgentUpdate(AgentBase):
    """更新智能体请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="智能体名称")
    prompt: Optional[str] = Field(None, description="智能体提示词")


class AgentResponse(BaseModel):
    """智能体响应"""
    name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    avatar: Optional[str] = Field(None, exclude=True, description="智能体头像")
    prompt: str = Field(..., description="智能体提示词")
    knowledge_base: Optional[str] = Field(None, description="关联的知识库")
    is_public: Optional[bool] = Field(False, description="是否公开")
    is_recommended: Optional[bool] = Field(False, description="是否推荐")
    is_favorite: Optional[bool] = Field(False, description="是否收藏")
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def avatar_url(self) -> Optional[str]:
        """获取完整的头像URL"""
        if self.avatar:
            # 如果已经是完整URL，直接返回
            if self.avatar.startswith(('http://', 'https://')):
                return self.avatar
            # 否则转换为完整URL路径
            return f"/logos/agents/{self.avatar}"
        return None
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class AgentListResponse(BaseModel):
    """智能体列表响应"""
    agents: list[AgentResponse]
    total: int