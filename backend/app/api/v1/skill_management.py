"""
技能管理API接口

基于技能发现机制，提供技能注册表查询、分类管理、搜索等功能
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

# 修复导入路径问题
import sys
from pathlib import Path

# 添加父目录到Python路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.skills.skill_registry import get_skill_registry, refresh_skill_registry
from app.schemas.skill_metadata import SkillMetadata, SkillCategory, SkillStatus, SkillSearchFilter

router = APIRouter()


class SkillListResponse(BaseModel):
    """技能列表响应模型"""
    skills: List[SkillMetadata]
    total: int
    categories: List[str]
    tags: List[str]


class SkillStatsResponse(BaseModel):
    """技能统计响应模型"""
    total_skills: int
    categories: Dict[str, int]
    active_skills: int
    disabled_skills: int
    deprecated_skills: int
    experimental_skills: int


class SkillSearchRequest(BaseModel):
    """技能搜索请求模型"""
    query: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[SkillCategory] = Field(None, description="按分类过滤")
    tags: Optional[List[str]] = Field(None, description="按标签过滤")
    status: Optional[SkillStatus] = Field(None, description="按状态过滤")
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="最低评分")
    limit: int = Field(10, ge=1, le=100, description="返回数量限制")
    offset: int = Field(0, ge=0, description="偏移量")


class SkillUsageUpdateRequest(BaseModel):
    """技能使用统计更新请求模型"""
    skill_id: str = Field(..., description="技能ID")
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="评分")


class SkillRefreshResponse(BaseModel):
    """技能刷新响应模型"""
    success: bool
    message: str
    skills_added: int
    skills_removed: int
    total_skills: int


@router.get("/skills", response_model=SkillListResponse)
async def list_skills(
    category: Optional[SkillCategory] = Query(None, description="按分类过滤"),
    tag: Optional[str] = Query(None, description="按标签过滤"),
    status: Optional[SkillStatus] = Query(None, description="按状态过滤"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """获取技能列表"""
    registry = get_skill_registry()
    
    # 获取所有技能
    all_skills = registry.get_all_skills()
    
    # 应用过滤器
    filtered_skills = all_skills
    
    if category:
        filtered_skills = [s for s in filtered_skills if s.category == category]
    
    if tag:
        filtered_skills = [s for s in filtered_skills if tag in s.tags]
    
    if status:
        filtered_skills = [s for s in filtered_skills if s.status == status]
    
    # 应用分页
    paginated_skills = filtered_skills[offset:offset + limit]
    
    return SkillListResponse(
        skills=paginated_skills,
        total=len(filtered_skills),
        categories=[cat.value for cat in registry.get_categories()],
        tags=registry.get_tags()
    )


@router.get("/skills/{skill_id}", response_model=SkillMetadata)
async def get_skill(skill_id: str):
    """获取指定技能详情"""
    registry = get_skill_registry()
    skill = registry.get_skill(skill_id)
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"技能 {skill_id} 不存在"
        )
    
    return skill


@router.get("/skills/categories/{category}", response_model=SkillListResponse)
async def get_skills_by_category(category: SkillCategory):
    """按分类获取技能列表"""
    registry = get_skill_registry()
    skills = registry.get_skills_by_category(category)
    
    return SkillListResponse(
        skills=skills,
        total=len(skills),
        categories=[cat.value for cat in registry.get_categories()],
        tags=registry.get_tags()
    )


@router.get("/skills/tags/{tag}", response_model=SkillListResponse)
async def get_skills_by_tag(tag: str):
    """按标签获取技能列表"""
    registry = get_skill_registry()
    skills = registry.get_skills_by_tag(tag)
    
    return SkillListResponse(
        skills=skills,
        total=len(skills),
        categories=[cat.value for cat in registry.get_categories()],
        tags=registry.get_tags()
    )


@router.post("/skills/search", response_model=SkillListResponse)
async def search_skills(request: SkillSearchRequest):
    """搜索技能"""
    registry = get_skill_registry()
    
    # 获取所有技能
    all_skills = registry.get_all_skills()
    
    # 应用过滤器
    filtered_skills = all_skills
    
    # 关键词搜索
    if request.query:
        filtered_skills = registry.search_skills(request.query)
    
    # 分类过滤
    if request.category:
        filtered_skills = [s for s in filtered_skills if s.category == request.category]
    
    # 标签过滤
    if request.tags:
        for tag in request.tags:
            filtered_skills = [s for s in filtered_skills if tag in s.tags]
    
    # 状态过滤
    if request.status:
        filtered_skills = [s for s in filtered_skills if s.status == request.status]
    
    # 评分过滤
    if request.min_rating is not None:
        filtered_skills = [s for s in filtered_skills if s.avg_rating >= request.min_rating]
    
    # 应用分页
    paginated_skills = filtered_skills[request.offset:request.offset + request.limit]
    
    return SkillListResponse(
        skills=paginated_skills,
        total=len(filtered_skills),
        categories=[cat.value for cat in registry.get_categories()],
        tags=registry.get_tags()
    )


@router.get("/skills/stats", response_model=SkillStatsResponse)
async def get_skill_stats():
    """获取技能统计信息"""
    registry = get_skill_registry()
    
    category_stats = registry.get_category_stats()
    
    # 按状态统计
    active_skills = len(registry.get_skills_by_status(SkillStatus.ACTIVE))
    disabled_skills = len(registry.get_skills_by_status(SkillStatus.DISABLED))
    deprecated_skills = len(registry.get_skills_by_status(SkillStatus.DEPRECATED))
    experimental_skills = len(registry.get_skills_by_status(SkillStatus.EXPERIMENTAL))
    
    return SkillStatsResponse(
        total_skills=registry.get_skill_count(),
        categories={cat.value: count for cat, count in category_stats.items()},
        active_skills=active_skills,
        disabled_skills=disabled_skills,
        deprecated_skills=deprecated_skills,
        experimental_skills=experimental_skills
    )


@router.post("/skills/{skill_id}/usage")
async def update_skill_usage(request: SkillUsageUpdateRequest):
    """更新技能使用统计"""
    registry = get_skill_registry()
    
    success = registry.update_skill_usage(request.skill_id, request.rating)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"技能 {request.skill_id} 不存在"
        )
    
    return {"success": True, "message": "使用统计更新成功"}


@router.post("/skills/refresh", response_model=SkillRefreshResponse)
async def refresh_skills():
    """刷新技能注册表"""
    # 获取刷新前的技能数量
    registry = get_skill_registry()
    before_count = registry.get_skill_count()
    
    # 执行刷新
    success = refresh_skill_registry()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="技能注册表刷新失败"
        )
    
    # 获取刷新后的技能数量
    after_count = registry.get_skill_count()
    
    skills_added = max(0, after_count - before_count)
    skills_removed = max(0, before_count - after_count)
    
    return SkillRefreshResponse(
        success=True,
        message="技能注册表刷新成功",
        skills_added=skills_added,
        skills_removed=skills_removed,
        total_skills=after_count
    )


@router.get("/skills/categories")
async def get_categories():
    """获取所有分类"""
    registry = get_skill_registry()
    return {"categories": [cat.value for cat in registry.get_categories()]}


@router.get("/skills/tags")
async def get_tags():
    """获取所有标签"""
    registry = get_skill_registry()
    return {"tags": registry.get_tags()}


@router.get("/skills/export")
async def export_skills():
    """导出技能注册表"""
    registry = get_skill_registry()
    
    # 构建导出数据
    export_data = {
        "export_time": "2026-01-27T14:17:02",  # 这里应该使用实际时间
        "skill_count": registry.get_skill_count(),
        "skills": {}
    }
    
    for skill_id, skill in registry.skills.items():
        export_data["skills"][skill_id] = skill.dict()
    
    return export_data


# 技能推荐API
@router.get("/skills/recommendations")
async def get_recommendations(
    based_on: str = Query(..., description="推荐依据：usage, rating, category"),
    limit: int = Query(5, ge=1, le=20, description="推荐数量")
):
    """获取技能推荐"""
    registry = get_skill_registry()
    all_skills = registry.get_all_skills()
    
    if based_on == "usage":
        # 按使用次数推荐
        recommended = sorted(all_skills, key=lambda s: s.usage_count, reverse=True)[:limit]
    elif based_on == "rating":
        # 按评分推荐
        recommended = sorted(all_skills, key=lambda s: s.avg_rating, reverse=True)[:limit]
    elif based_on == "category":
        # 按分类分布推荐
        category_stats = registry.get_category_stats()
        recommended = []
        for category, count in category_stats.items():
            category_skills = registry.get_skills_by_category(category)
            if category_skills:
                # 从每个分类中取一个技能
                top_skill = max(category_skills, key=lambda s: s.usage_count + s.avg_rating)
                recommended.append(top_skill)
        recommended = recommended[:limit]
    else:
        # 默认按综合评分推荐
        recommended = sorted(
            all_skills, 
            key=lambda s: s.usage_count * 0.3 + s.avg_rating * 0.7, 
            reverse=True
        )[:limit]
    
    return {"recommended_skills": recommended}