"""
技能市场 API 端点

提供技能市场的 RESTful API 接口
支持技能安装、管理、执行等功能
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.modules.skills import skill_manager
from app.modules.skills.skill_models import (
    SkillInfo,
    SkillInstallRequest,
    SkillInstallResult,
    SkillExecutionRequest,
    SkillExecutionResult,
    SkillSearchResult,
    SkillMarketItem
)

router = APIRouter()


# 请求模型
class SkillInstallFromNPMRequest(BaseModel):
    """从 NPM 安装技能请求"""
    package_name: str = Field(..., description="NPM 包名")
    version: Optional[str] = Field(default=None, description="版本号")


class SkillInstallFromGitRequest(BaseModel):
    """从 Git 安装技能请求"""
    git_url: str = Field(..., description="Git 仓库地址")
    skill_name: Optional[str] = Field(default=None, description="技能名称")


class SkillExecuteRequest(BaseModel):
    """技能执行请求"""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    timeout: Optional[int] = Field(default=None, description="超时时间")


class SkillEnableRequest(BaseModel):
    """技能启用/禁用请求"""
    enable: bool = Field(..., description="是否启用")


# 响应模型
class SkillListResponse(BaseModel):
    """技能列表响应"""
    skills: List[SkillInfo]
    total: int


class SkillCategoriesResponse(BaseModel):
    """技能类别响应"""
    categories: List[str]
    category_counts: Dict[str, int]


class SkillStatisticsResponse(BaseModel):
    """技能统计响应"""
    total_skills: int
    active_skills: int
    inactive_skills: int
    category_distribution: Dict[str, int]
    execution_statistics: Dict[str, Any]


@router.get("/skills-market", response_model=SkillListResponse)
async def list_skills(
    category: Optional[str] = Query(None, description="按类别过滤"),
    active_only: bool = Query(False, description="仅返回激活的技能")
):
    """
    获取已安装的技能列表
    
    Args:
        category: 技能类别过滤
        active_only: 是否仅返回激活的技能
        
    Returns:
        SkillListResponse: 技能列表
    """
    if category:
        skills = skill_manager.get_skills_by_category(category)
    elif active_only:
        skills = skill_manager.get_active_skills()
    else:
        skills = skill_manager.get_all_skills()
    
    return SkillListResponse(
        skills=skills,
        total=len(skills)
    )


@router.get("/skills-market/{skill_name}", response_model=SkillInfo)
async def get_skill(skill_name: str):
    """
    获取技能详细信息
    
    Args:
        skill_name: 技能名称
        
    Returns:
        SkillInfo: 技能信息
        
    Raises:
        HTTPException: 技能不存在时返回404
    """
    skill = skill_manager.get_skill(skill_name)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 不存在")
    
    return skill


@router.post("/skills-market/install/npm", response_model=SkillInstallResult)
async def install_skill_from_npm(request: SkillInstallFromNPMRequest):
    """
    从 NPM 安装技能
    
    Args:
        request: 安装请求
        
    Returns:
        SkillInstallResult: 安装结果
    """
    result = skill_manager.install_skill(
        skill_source=request.package_name,
        source_type="npm",
        version=request.version
    )
    
    return result


@router.post("/skills-market/install/git", response_model=SkillInstallResult)
async def install_skill_from_git(request: SkillInstallFromGitRequest):
    """
    从 Git 仓库安装技能
    
    Args:
        request: 安装请求
        
    Returns:
        SkillInstallResult: 安装结果
    """
    result = skill_manager.install_skill(
        skill_source=request.git_url,
        source_type="git"
    )
    
    return result


@router.delete("/skills-market/{skill_name}")
async def uninstall_skill(skill_name: str):
    """
    卸载技能
    
    Args:
        skill_name: 技能名称
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    success = skill_manager.uninstall_skill(skill_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 不存在或卸载失败")
    
    return {
        "success": True,
        "message": f"技能 '{skill_name}' 已卸载"
    }


@router.post("/skills-market/{skill_name}/execute", response_model=SkillExecutionResult)
async def execute_skill(skill_name: str, request: SkillExecuteRequest):
    """
    执行技能
    
    Args:
        skill_name: 技能名称
        request: 执行请求
        
    Returns:
        SkillExecutionResult: 执行结果
    """
    result = await skill_manager.execute_skill(
        skill_name=skill_name,
        parameters=request.parameters,
        timeout=request.timeout
    )
    
    return result


@router.get("/skills-market/categories", response_model=SkillCategoriesResponse)
async def list_categories():
    """
    获取技能类别列表
    
    Returns:
        SkillCategoriesResponse: 类别列表
    """
    skills = skill_manager.get_all_skills()
    
    categories = list(set(skill.metadata.category for skill in skills))
    
    category_counts = {}
    for skill in skills:
        category = skill.metadata.category
        category_counts[category] = category_counts.get(category, 0) + 1
    
    return SkillCategoriesResponse(
        categories=categories,
        category_counts=category_counts
    )


@router.get("/skills-market/statistics", response_model=SkillStatisticsResponse)
async def get_statistics():
    """
    获取技能统计信息
    
    Returns:
        SkillStatisticsResponse: 统计信息
    """
    stats = skill_manager.get_statistics()
    return SkillStatisticsResponse(**stats)


@router.post("/skills-market/{skill_name}/enable")
async def enable_skill(skill_name: str, request: SkillEnableRequest):
    """
    启用或禁用技能
    
    Args:
        skill_name: 技能名称
        request: 启用/禁用请求
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    if request.enable:
        success = skill_manager.enable_skill(skill_name)
    else:
        success = skill_manager.disable_skill(skill_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 不存在")
    
    return {
        "success": True,
        "skill_name": skill_name,
        "enabled": request.enable
    }


@router.get("/skills-market/search", response_model=SkillSearchResult)
async def search_skills(query: str = Query(..., description="搜索关键词")):
    """
    搜索已安装的技能
    
    Args:
        query: 搜索关键词
        
    Returns:
        SkillSearchResult: 搜索结果
    """
    result = skill_manager.search_skills(query)
    return result


@router.get("/skills-market/{skill_name}/info")
async def get_skill_detailed_info(skill_name: str):
    """
    获取技能的详细信息（包括适配器信息）
    
    Args:
        skill_name: 技能名称
        
    Returns:
        Dict[str, Any]: 详细信息
    """
    skill = skill_manager.get_skill(skill_name)
    adapter = skill_manager.get_skill_adapter(skill_name)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 不存在")
    
    info = {
        "skill_info": skill.dict(),
        "adapter_info": adapter.get_skill_info() if adapter else None
    }
    
    return info


# 模拟技能市场（远程）
MOCK_MARKET_SKILLS = [
    SkillMarketItem(
        name="web-scraper",
        display_name="网页爬虫",
        description="自动抓取网页内容，支持多种选择器",
        version="1.2.0",
        author="OpenClaw Community",
        category="browser",
        tags=["scraping", "automation", "web"],
        repository_url="https://github.com/openclaw-skills/web-scraper",
        download_count=1523,
        rating=4.5,
        updated_at=datetime.now()
    ),
    SkillMarketItem(
        name="pdf-processor",
        display_name="PDF处理器",
        description="PDF文档处理、转换和提取",
        version="2.0.1",
        author="PDF Tools Inc",
        category="productivity",
        tags=["pdf", "document", "conversion"],
        repository_url="https://github.com/openclaw-skills/pdf-processor",
        download_count=2341,
        rating=4.8,
        updated_at=datetime.now()
    ),
    SkillMarketItem(
        name="code-reviewer",
        display_name="代码审查助手",
        description="自动审查代码质量，提供改进建议",
        version="1.5.0",
        author="Code Quality Team",
        category="coding",
        tags=["code", "review", "quality"],
        repository_url="https://github.com/openclaw-skills/code-reviewer",
        download_count=892,
        rating=4.3,
        updated_at=datetime.now()
    ),
    SkillMarketItem(
        name="data-analyzer",
        display_name="数据分析器",
        description="数据分析和可视化工具",
        version="1.1.0",
        author="Data Science Lab",
        category="data",
        tags=["data", "analysis", "visualization"],
        repository_url="https://github.com/openclaw-skills/data-analyzer",
        download_count=1234,
        rating=4.6,
        updated_at=datetime.now()
    ),
    SkillMarketItem(
        name="email-automation",
        display_name="邮件自动化",
        description="自动发送和管理邮件",
        version="1.0.5",
        author="Automation Tools",
        category="productivity",
        tags=["email", "automation", "communication"],
        repository_url="https://github.com/openclaw-skills/email-automation",
        download_count=756,
        rating=4.2,
        updated_at=datetime.now()
    )
]

from datetime import datetime


@router.get("/skills-market-remote", response_model=List[SkillMarketItem])
async def list_remote_skills(
    category: Optional[str] = Query(None, description="按类别过滤"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """
    获取远程技能市场的技能列表（模拟）
    
    Args:
        category: 技能类别过滤
        search: 搜索关键词
        
    Returns:
        List[SkillMarketItem]: 技能列表
    """
    skills = MOCK_MARKET_SKILLS
    
    if category:
        skills = [s for s in skills if s.category == category]
    
    if search:
        search = search.lower()
        skills = [
            s for s in skills
            if search in s.name.lower() or
               search in s.description.lower() or
               any(search in tag.lower() for tag in s.tags)
        ]
    
    return skills


@router.get("/skills-market-remote/{skill_name}", response_model=SkillMarketItem)
async def get_remote_skill(skill_name: str):
    """
    获取远程技能的详细信息
    
    Args:
        skill_name: 技能名称
        
    Returns:
        SkillMarketItem: 技能信息
    """
    for skill in MOCK_MARKET_SKILLS:
        if skill.name == skill_name:
            return skill
    
    raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 不存在")
