"""
技能数据模型

定义技能相关的数据结构和模型
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SkillStatus(str, Enum):
    """技能状态"""
    INSTALLED = "installed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"


class SkillSource(str, Enum):
    """技能来源"""
    CLAWHUB = "clawhub"
    LOCAL = "local"
    CUSTOM = "custom"


class SkillMetadata(BaseModel):
    """技能元数据"""
    name: str = Field(..., description="技能名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="技能描述")
    version: str = Field(default="1.0.0", description="版本号")
    author: str = Field(default="", description="作者")
    category: str = Field(default="utility", description="类别")
    tags: List[str] = Field(default_factory=list, description="标签")
    icon: str = Field(default="🔧", description="图标")
    source: SkillSource = Field(default=SkillSource.CLAWHUB, description="来源")
    repository_url: Optional[str] = Field(default=None, description="仓库地址")
    
    class Config:
        use_enum_values = True


class SkillConfig(BaseModel):
    """技能配置"""
    entry_point: str = Field(..., description="入口文件")
    runtime: str = Field(default="node", description="运行环境")
    dependencies: List[str] = Field(default_factory=list, description="依赖列表")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    timeout: int = Field(default=30, description="超时时间（秒）")


class SkillInfo(BaseModel):
    """技能信息"""
    metadata: SkillMetadata
    config: SkillConfig
    status: SkillStatus
    installed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0
    error_count: int = 0


class SkillExecutionRequest(BaseModel):
    """技能执行请求"""
    skill_name: str = Field(..., description="技能名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    timeout: Optional[int] = Field(default=None, description="超时时间")


class SkillExecutionResult(BaseModel):
    """技能执行结果"""
    success: bool = Field(..., description="是否成功")
    skill_name: str = Field(..., description="技能名称")
    output: Any = Field(default=None, description="输出结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    execution_time: float = Field(..., description="执行时间（秒）")
    stdout: Optional[str] = Field(default=None, description="标准输出")
    stderr: Optional[str] = Field(default=None, description="标准错误")


class SkillMarketItem(BaseModel):
    """技能市场项目"""
    name: str = Field(..., description="技能名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="描述")
    version: str = Field(..., description="版本")
    author: str = Field(..., description="作者")
    category: str = Field(..., description="类别")
    tags: List[str] = Field(default_factory=list, description="标签")
    repository_url: str = Field(..., description="仓库地址")
    download_count: int = Field(default=0, description="下载次数")
    rating: float = Field(default=0.0, description="评分")
    updated_at: datetime = Field(..., description="更新时间")


class SkillInstallRequest(BaseModel):
    """技能安装请求"""
    skill_name: str = Field(..., description="技能名称或URL")
    version: Optional[str] = Field(default=None, description="指定版本")
    force: bool = Field(default=False, description="强制重新安装")


class SkillInstallResult(BaseModel):
    """技能安装结果"""
    success: bool = Field(..., description="是否成功")
    skill_name: str = Field(..., description="技能名称")
    message: str = Field(..., description="结果消息")
    installed_path: Optional[str] = Field(default=None, description="安装路径")
    error: Optional[str] = Field(default=None, description="错误信息")


class SkillSearchResult(BaseModel):
    """技能搜索结果"""
    skills: List[SkillMarketItem] = Field(default_factory=list, description="技能列表")
    total: int = Field(..., description="总数")
    query: str = Field(..., description="查询词")
