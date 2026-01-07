"""技能管理 Pydantic Schema"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SkillBase(BaseModel):
    """技能基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="技能名称")
    display_name: Optional[str] = Field(None, min_length=1, max_length=200, description="技能显示名称")
    description: str = Field(..., min_length=10, description="技能描述")
    version: str = Field("1.0.0", min_length=1, max_length=50, pattern=r"^\d+\.\d+\.\d+$", description="版本号")
    license: Optional[str] = Field(None, max_length=100, description="许可证")
    tags: List[str] = Field(default_factory=list, max_items=10, description="标签列表")
    source: str = Field("local", max_length=50, description="来源")
    source_url: Optional[str] = Field(None, max_length=500, description="来源URL")
    remote_id: Optional[str] = Field(None, max_length=100, description="远程ID")
    content: Optional[str] = Field(None, description="技能内容")
    parameters_schema: Optional[Dict[str, Any]] = Field(None, description="参数Schema")
    status: str = Field("disabled", max_length=20, description="状态")
    is_system: bool = Field(False, description="是否系统技能")
    icon: Optional[str] = Field(None, max_length=255, description="图标URL")
    author: Optional[str] = Field(None, max_length=200, description="作者")
    documentation_url: Optional[str] = Field(None, max_length=500, description="文档URL")
    requirements: List[Dict[str, Any]] = Field(default_factory=list, description="依赖要求")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置")


class SkillCreate(SkillBase):
    """创建技能模型"""
    pass


class SkillUpdate(BaseModel):
    """更新技能模型"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    version: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r"^\d+\.\d+\.\d+$")
    license: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(None, max_items=10)
    content: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=200)
    documentation_url: Optional[str] = Field(None, max_length=500)
    requirements: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None


class SkillResponse(SkillBase):
    """技能响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    installed_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """技能列表响应模型"""
    skills: List[SkillResponse]
    total: int
    skip: int
    limit: int


class SkillExecuteRequest(BaseModel):
    """技能执行请求模型"""
    skill_id: int
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = Field(None, description="执行上下文")


class SkillExecuteResponse(BaseModel):
    """技能执行响应模型"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    output_format: Optional[str] = None


class SkillModelBindingCreate(BaseModel):
    """技能模型绑定创建模型"""
    skill_id: int
    model_id: Optional[int] = None
    model_type_id: Optional[int] = None
    priority: int = Field(0, ge=0)
    config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class SkillModelBindingResponse(BaseModel):
    """技能模型绑定响应模型"""
    id: int
    skill_id: int
    model_id: Optional[int] = None
    model_type_id: Optional[int] = None
    priority: int
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SkillExecutionLogResponse(BaseModel):
    """技能执行日志响应模型"""
    id: int
    skill_id: int
    session_id: Optional[int] = None
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    task_description: Optional[str] = None
    input_params: Dict[str, Any]
    output_result: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    token_usage: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SkillStatisticsResponse(BaseModel):
    """技能统计响应模型"""
    total_skills: int
    enabled_skills: int
    disabled_skills: int
    total_executions: int
    average_execution_time_ms: float
    top_skills: List[Dict[str, Any]]


class RepositoryCreate(BaseModel):
    """仓库创建模型"""
    name: str = Field(..., max_length=200, description="仓库名称")
    url: str = Field(..., max_length=500, description="仓库URL")
    description: Optional[str] = Field(None, description="仓库描述")
    branch: str = Field("main", max_length=100, description="分支名称")
    is_enabled: bool = Field(True, description="是否启用")
    sync_interval_hours: int = Field(24, ge=1, le=168, description="同步间隔（小时）")
    credentials: Optional[Dict[str, Any]] = Field(None, description="认证信息")


class RepositoryResponse(BaseModel):
    """仓库响应模型"""
    id: int
    name: str
    url: str
    description: Optional[str] = None
    branch: str
    is_enabled: bool
    sync_interval_hours: int
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RepositoryListResponse(BaseModel):
    """仓库列表响应模型"""
    repositories: List[RepositoryResponse]
    total: int
    skip: int
    limit: int


class RemoteSkillResponse(BaseModel):
    """远程技能响应模型"""
    id: int
    repository_id: int
    remote_id: str
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    license: Optional[str] = None
    tags: List[str]
    author: Optional[str] = None
    documentation_url: Optional[str] = None
    icon_url: Optional[str] = None
    requirements: List[Dict[str, Any]]
    file_path: Optional[str] = None
    local_path: Optional[str] = None
    is_installed: bool
    is_update_available: bool
    last_checked_at: Optional[datetime] = None
    skill_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RemoteSkillListResponse(BaseModel):
    """远程技能列表响应模型"""
    skills: List[RemoteSkillResponse]
    total: int
    skip: int
    limit: int


class RepositorySyncResponse(BaseModel):
    """仓库同步响应模型"""
    repository_id: int
    status: str
    message: str
    synced_at: datetime
