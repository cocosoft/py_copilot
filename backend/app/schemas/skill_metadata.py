"""
技能元数据模式定义
定义技能的基本信息和配置
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SkillDependency(BaseModel):
    """技能依赖定义"""
    name: str = Field(..., description="依赖包名称")
    version: str = Field(..., description="版本要求")
    optional: bool = Field(False, description="是否为可选依赖")


class SkillExample(BaseModel):
    """技能使用示例"""
    title: str = Field(..., description="示例标题")
    description: str = Field(..., description="示例描述")
    code: str = Field(..., description="示例代码")


class SkillReview(BaseModel):
    """技能用户评价"""
    author: str = Field(..., description="评价作者")
    rating: float = Field(..., ge=0, le=5, description="评分（0-5）")
    date: datetime = Field(..., description="评价日期")
    content: str = Field(..., description="评价内容")


class SkillMetadata(BaseModel):
    """技能元数据模型"""
    
    # 基本信息
    id: str = Field(..., description="技能唯一标识符")
    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能描述")
    long_description: Optional[str] = Field(None, description="详细描述")
    version: str = Field(..., description="技能版本")
    
    # 分类信息
    category: str = Field(..., description="技能分类")
    tags: List[str] = Field(default_factory=list, description="技能标签")
    
    # 作者信息
    author: str = Field(..., description="技能作者")
    author_email: Optional[str] = Field(None, description="作者邮箱")
    author_url: Optional[str] = Field(None, description="作者网站")
    
    # 技能属性
    official: bool = Field(False, description="是否为官方技能")
    popular: bool = Field(False, description="是否为热门技能")
    installed: bool = Field(False, description="是否已安装")
    
    # 统计信息
    rating: Optional[float] = Field(None, ge=0, le=5, description="平均评分")
    review_count: int = Field(0, description="评价数量")
    downloads: int = Field(0, description="下载次数")
    
    # 技术信息
    size: Optional[str] = Field(None, description="技能大小")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    compatibility: str = Field("Py Copilot 1.0+", description="兼容性要求")
    license: str = Field("MIT", description="许可证")
    
    # 依赖关系
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Python包依赖")
    skill_dependencies: List[str] = Field(default_factory=list, description="其他技能依赖")
    
    # 图标和资源
    icon: Optional[str] = Field(None, description="技能图标路径")
    screenshots: List[str] = Field(default_factory=list, description="技能截图")
    
    # 使用信息
    examples: List[SkillExample] = Field(default_factory=list, description="使用示例")
    reviews: List[SkillReview] = Field(default_factory=list, description="用户评价")
    
    # 配置信息
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置模式定义")
    default_config: Optional[Dict[str, Any]] = Field(None, description="默认配置")
    
    # 执行信息
    entry_point: Optional[str] = Field(None, description="技能入口点")
    main_file: Optional[str] = Field(None, description="主文件路径")
    
    # 权限要求
    permissions: List[str] = Field(default_factory=list, description="所需权限")
    
    # 市场信息
    marketplace_id: Optional[str] = Field(None, description="市场ID")
    marketplace_url: Optional[str] = Field(None, description="市场页面URL")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SkillInstallRequest(BaseModel):
    """技能安装请求"""
    skill_id: str = Field(..., description="技能ID")
    source: str = Field(..., description="技能来源（URL、路径等）")
    force: bool = Field(False, description="是否强制重新安装")
    install_dependencies: bool = Field(True, description="是否安装依赖")


class SkillUninstallRequest(BaseModel):
    """技能卸载请求"""
    skill_id: str = Field(..., description="技能ID")
    cleanup: bool = Field(True, description="是否清理配置和数据")


class SkillUpdateRequest(BaseModel):
    """技能更新请求"""
    skill_id: str = Field(..., description="技能ID")
    source: Optional[str] = Field(None, description="新的技能来源")


class SkillOperationResponse(BaseModel):
    """技能操作响应"""
    success: bool = Field(..., description="操作是否成功")
    skill_id: str = Field(..., description="技能ID")
    message: str = Field(..., description="操作结果消息")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="技能元数据")
    install_path: Optional[str] = Field(None, description="安装路径")


class SkillListResponse(BaseModel):
    """技能列表响应"""
    skills: List[SkillMetadata] = Field(..., description="技能列表")
    total_count: int = Field(..., description="总技能数量")
    installed_count: int = Field(..., description="已安装技能数量")


class SkillDependencyInfo(BaseModel):
    """依赖信息"""
    name: str = Field(..., description="依赖名称")
    version: str = Field(..., description="版本要求")
    installed: bool = Field(..., description="是否已安装")
    installed_version: Optional[str] = Field(None, description="已安装版本")
    compatible: bool = Field(..., description="版本是否兼容")


class SkillDependencyCheckResponse(BaseModel):
    """依赖检查响应"""
    skill_id: str = Field(..., description="技能ID")
    dependencies: List[SkillDependencyInfo] = Field(..., description="依赖信息列表")
    all_installed: bool = Field(..., description="所有依赖是否已安装")
    missing_dependencies: List[str] = Field(..., description="缺失的依赖")


class SkillSearchRequest(BaseModel):
    """技能搜索请求"""
    query: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[str] = Field(None, description="分类筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    official: Optional[bool] = Field(None, description="是否官方技能")
    installed: Optional[bool] = Field(None, description="是否已安装")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="最低评分")
    sort_by: str = Field("popularity", description="排序方式")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class SkillSearchResponse(BaseModel):
    """技能搜索响应"""
    skills: List[SkillMetadata] = Field(..., description="搜索结果")
    total_count: int = Field(..., description="总结果数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")


class SkillMarketplaceInfo(BaseModel):
    """技能市场信息"""
    marketplace_id: str = Field(..., description="市场ID")
    name: str = Field(..., description="市场名称")
    url: str = Field(..., description="市场URL")
    description: str = Field(..., description="市场描述")
    skill_count: int = Field(..., description="技能数量")
    last_updated: datetime = Field(..., description="最后更新时间")


class SkillInstallationProgress(BaseModel):
    """技能安装进度"""
    skill_id: str = Field(..., description="技能ID")
    status: str = Field(..., description="安装状态")
    progress: float = Field(..., ge=0, le=100, description="安装进度（0-100）")
    current_step: str = Field(..., description="当前步骤")
    message: str = Field(..., description="进度消息")
    estimated_time: Optional[int] = Field(None, description="预计剩余时间（秒）")


class SkillHealthCheck(BaseModel):
    """技能健康检查"""
    skill_id: str = Field(..., description="技能ID")
    healthy: bool = Field(..., description="是否健康")
    last_check: datetime = Field(..., description="最后检查时间")
    issues: List[str] = Field(default_factory=list, description="问题列表")
    dependencies_ok: bool = Field(..., description="依赖是否正常")
    permissions_ok: bool = Field(..., description="权限是否正常")
    config_valid: bool = Field(..., description="配置是否有效")