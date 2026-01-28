"""
技能管理API路由
提供技能的安装、卸载、更新和管理功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
import logging

from app.schemas.skill_metadata import (
    SkillInstallRequest, SkillUninstallRequest, SkillUpdateRequest,
    SkillOperationResponse, SkillListResponse, SkillSearchRequest,
    SkillSearchResponse, SkillDependencyCheckResponse
)
from app.services.skill_installer import skill_installer
from app.skills.skill_registry import SkillRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/skills", tags=["技能管理"])


@router.get("/installed", response_model=SkillListResponse)
async def get_installed_skills():
    """获取已安装的技能列表"""
    try:
        registry = SkillRegistry()
        skills = await registry.get_all_skills()
        
        installed_skills = [skill for skill in skills if skill.get('installed', False)]
        
        return SkillListResponse(
            skills=installed_skills,
            total_count=len(skills),
            installed_count=len(installed_skills)
        )
    except Exception as e:
        logger.error(f"获取已安装技能失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取技能列表失败: {str(e)}")


@router.get("/market", response_model=SkillListResponse)
async def get_market_skills(
    category: Optional[str] = Query(None, description="分类筛选"),
    official: Optional[bool] = Query(None, description="是否官方技能"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="最低评分"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取技能市场中的技能列表"""
    try:
        from app.core.database import get_db
        from app.models.skill import Skill, RemoteSkill
        from sqlalchemy.orm import Session
        
        db: Session = next(get_db())
        
        # 获取本地技能
        local_skills = db.query(Skill).all()
        
        # 获取远程技能
        remote_skills = db.query(RemoteSkill).all()
        
        # 构建技能市场数据
        market_skills = []
        
        # 添加本地技能
        for skill in local_skills:
            # 从tags中提取分类
            skill_category = None
            if skill.tags:
                # 尝试从tags中获取分类
                for tag in skill.tags:
                    if isinstance(tag, dict) and tag.get('type') == 'category':
                        skill_category = tag.get('value')
                        break
                    elif isinstance(tag, str):
                        # 简单处理：使用第一个标签作为分类
                        skill_category = tag
                        break
            
            # 计算评分（基于使用次数和执行成功次数）
            usage_count = skill.usage_count or 0
            rating = min(5.0, 3.0 + (usage_count / 100))  # 基础3分，每100次使用加1分，最高5分
            
            market_skills.append({
                "id": skill.name,
                "name": skill.display_name or skill.name,
                "description": skill.description or "",
                "category": skill_category or "其他",
                "rating": round(rating, 1),
                "downloads": usage_count,
                "version": skill.version,
                "author": skill.author or "未知",
                "official": skill.is_system,
                "popular": usage_count > 10,  # 使用次数超过10次视为热门
                "installed": True,  # 本地技能已安装
                "last_updated": skill.updated_at.isoformat() if skill.updated_at else skill.created_at.isoformat(),
                "icon": skill.icon
            })
        
        # 添加远程技能
        for remote_skill in remote_skills:
            # 从tags中提取分类
            skill_category = None
            if remote_skill.tags:
                # 尝试从tags中获取分类
                for tag in remote_skill.tags:
                    if isinstance(tag, dict) and tag.get('type') == 'category':
                        skill_category = tag.get('value')
                        break
                    elif isinstance(tag, str):
                        # 简单处理：使用第一个标签作为分类
                        skill_category = tag
                        break
            
            market_skills.append({
                "id": remote_skill.remote_id or remote_skill.name,
                "name": remote_skill.display_name or remote_skill.name,
                "description": remote_skill.description or "",
                "category": skill_category or "其他",
                "rating": 4.0,  # 默认评分
                "downloads": 0,  # 远程技能下载次数未知
                "version": remote_skill.version or "1.0.0",
                "author": remote_skill.author or "未知",
                "official": False,
                "popular": False,
                "installed": remote_skill.is_installed,
                "last_updated": remote_skill.updated_at.isoformat() if remote_skill.updated_at else remote_skill.created_at.isoformat(),
                "icon": remote_skill.icon_url
            })
        
        # 应用筛选条件
        filtered_skills = market_skills
        
        if category:
            filtered_skills = [s for s in filtered_skills if s['category'] == category]
        
        if official is not None:
            filtered_skills = [s for s in filtered_skills if s['official'] == official]
        
        if min_rating is not None:
            filtered_skills = [s for s in filtered_skills if s['rating'] >= min_rating]
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_skills = filtered_skills[start_idx:end_idx]
        
        # 计算已安装技能数量
        installed_count = sum(1 for skill in filtered_skills if skill['installed'])
        
        return SkillListResponse(
            skills=paginated_skills,
            total_count=len(filtered_skills),
            installed_count=installed_count
        )
        
    except Exception as e:
        logger.error(f"获取技能市场数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取市场数据失败: {str(e)}")


@router.post("/install", response_model=SkillOperationResponse)
async def install_skill(install_request: SkillInstallRequest):
    """安装技能"""
    try:
        result = await skill_installer.install_skill(
            skill_id=install_request.skill_id,
            source=install_request.source,
            force=install_request.force
        )
        
        if result['success']:
            return SkillOperationResponse(
                success=True,
                skill_id=result['skill_id'],
                message=result['message'],
                metadata=result.get('metadata'),
                install_path=result.get('install_path')
            )
        else:
            return SkillOperationResponse(
                success=False,
                skill_id=result['skill_id'],
                error=result['error']
            )
            
    except Exception as e:
        logger.error(f"安装技能失败: {install_request.skill_id}, 错误: {e}")
        return SkillOperationResponse(
            success=False,
            skill_id=install_request.skill_id,
            error=f"安装失败: {str(e)}"
        )


@router.post("/uninstall", response_model=SkillOperationResponse)
async def uninstall_skill(uninstall_request: SkillUninstallRequest):
    """卸载技能"""
    try:
        result = await skill_installer.uninstall_skill(
            uninstall_request.skill_id, 
            cleanup=uninstall_request.cleanup
        )
        
        if result['success']:
            response = SkillOperationResponse(
                success=True,
                skill_id=result['skill_id'],
                message=result['message']
            )
            
            # 添加清理相关信息
            if result.get('cleanup_performed'):
                response.details = {
                    'cleanup_performed': True,
                    'cleanup_result': result.get('cleanup_result')
                }
            
            return response
        else:
            return SkillOperationResponse(
                success=False,
                skill_id=result['skill_id'],
                error=result['error']
            )
            
    except Exception as e:
        logger.error(f"卸载技能失败: {uninstall_request.skill_id}, 错误: {e}")
        return SkillOperationResponse(
            success=False,
            skill_id=uninstall_request.skill_id,
            error=f"卸载失败: {str(e)}"
        )


@router.post("/update", response_model=SkillOperationResponse)
async def update_skill(update_request: SkillUpdateRequest):
    """更新技能"""
    try:
        # 如果提供了新的源，使用新源更新，否则使用原来的源
        source = update_request.source
        if not source:
            skill_info = skill_installer.get_skill_info(update_request.skill_id)
            if not skill_info:
                return SkillOperationResponse(
                    success=False,
                    skill_id=update_request.skill_id,
                    error="技能未安装，无法获取源信息"
                )
            source = skill_info.get('source')
        
        result = await skill_installer.update_skill(update_request.skill_id)
        
        if result['success']:
            return SkillOperationResponse(
                success=True,
                skill_id=result['skill_id'],
                message=result['message']
            )
        else:
            return SkillOperationResponse(
                success=False,
                skill_id=result['skill_id'],
                error=result['error']
            )
            
    except Exception as e:
        logger.error(f"更新技能失败: {update_request.skill_id}, 错误: {e}")
        return SkillOperationResponse(
            success=False,
            skill_id=update_request.skill_id,
            error=f"更新失败: {str(e)}"
        )


@router.get("/{skill_id}/info")
async def get_skill_info(skill_id: str):
    """获取技能详细信息"""
    try:
        # 首先检查是否已安装
        skill_info = skill_installer.get_skill_info(skill_id)
        if skill_info:
            return skill_info
        
        # 如果未安装，从市场获取信息
        # 这里应该调用技能市场API
        # 暂时返回模拟数据
        mock_skill_info = {
            "id": skill_id,
            "name": f"技能 {skill_id}",
            "description": "这是一个技能描述",
            "category": "通用",
            "rating": 4.0,
            "downloads": 100,
            "version": "1.0.0",
            "author": "未知作者",
            "official": False,
            "popular": False,
            "installed": False,
            "last_updated": "2024-01-01T00:00:00"
        }
        
        return mock_skill_info
        
    except Exception as e:
        logger.error(f"获取技能信息失败: {skill_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取技能信息失败: {str(e)}")


@router.get("/{skill_id}/dependencies", response_model=SkillDependencyCheckResponse)
async def check_skill_dependencies(skill_id: str):
    """检查技能依赖"""
    try:
        # 这里应该实现依赖检查逻辑
        # 暂时返回模拟数据
        mock_dependencies = [
            {
                "name": "pandas",
                "version": ">=1.5.0",
                "installed": True,
                "installed_version": "1.5.3",
                "compatible": True
            },
            {
                "name": "matplotlib",
                "version": ">=3.6.0",
                "installed": True,
                "installed_version": "3.7.0",
                "compatible": True
            }
        ]
        
        return SkillDependencyCheckResponse(
            skill_id=skill_id,
            dependencies=mock_dependencies,
            all_installed=True,
            missing_dependencies=[]
        )
        
    except Exception as e:
        logger.error(f"检查技能依赖失败: {skill_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"检查依赖失败: {str(e)}")


@router.post("/search", response_model=SkillSearchResponse)
async def search_skills(search_request: SkillSearchRequest):
    """搜索技能"""
    try:
        # 这里应该实现搜索逻辑，结合已安装技能和市场技能
        # 暂时返回模拟数据
        mock_skills = [
            {
                "id": "data-analysis",
                "name": "数据分析助手",
                "description": "强大的数据分析工具，支持多种数据格式和可视化",
                "category": "数据分析",
                "rating": 4.8,
                "downloads": 2560,
                "version": "1.2.3",
                "author": "Py Copilot团队",
                "official": True,
                "popular": True,
                "installed": False,
                "last_updated": "2024-01-15T00:00:00"
            },
            {
                "id": "web-scraping",
                "name": "网页爬虫",
                "description": "自动化网页数据采集工具，支持多种网站和反爬机制",
                "category": "数据采集",
                "rating": 4.5,
                "downloads": 1870,
                "version": "2.1.0",
                "author": "WebTools Inc.",
                "official": False,
                "popular": True,
                "installed": False,
                "last_updated": "2024-01-10T00:00:00"
            }
        ]
        
        # 应用搜索条件
        filtered_skills = mock_skills
        
        if search_request.query:
            query = search_request.query.lower()
            filtered_skills = [
                s for s in filtered_skills 
                if query in s['name'].lower() or query in s['description'].lower()
            ]
        
        if search_request.category:
            filtered_skills = [s for s in filtered_skills if s['category'] == search_request.category]
        
        if search_request.official is not None:
            filtered_skills = [s for s in filtered_skills if s['official'] == search_request.official]
        
        if search_request.installed is not None:
            filtered_skills = [s for s in filtered_skills if s['installed'] == search_request.installed]
        
        if search_request.min_rating is not None:
            filtered_skills = [s for s in filtered_skills if s['rating'] >= search_request.min_rating]
        
        # 排序
        if search_request.sort_by == "popularity":
            filtered_skills.sort(key=lambda x: x['downloads'], reverse=True)
        elif search_request.sort_by == "rating":
            filtered_skills.sort(key=lambda x: x['rating'], reverse=True)
        elif search_request.sort_by == "name":
            filtered_skills.sort(key=lambda x: x['name'])
        elif search_request.sort_by == "recent":
            filtered_skills.sort(key=lambda x: x['last_updated'], reverse=True)
        
        # 分页
        start_idx = (search_request.page - 1) * search_request.page_size
        end_idx = start_idx + search_request.page_size
        paginated_skills = filtered_skills[start_idx:end_idx]
        
        return SkillSearchResponse(
            skills=paginated_skills,
            total_count=len(filtered_skills),
            page=search_request.page,
            page_size=search_request.page_size,
            total_pages=(len(filtered_skills) + search_request.page_size - 1) // search_request.page_size
        )
        
    except Exception as e:
        logger.error(f"搜索技能失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/{skill_id}/health")
async def check_skill_health(skill_id: str):
    """检查技能健康状态"""
    try:
        # 这里应该实现健康检查逻辑
        # 暂时返回模拟数据
        return {
            "skill_id": skill_id,
            "healthy": True,
            "last_check": "2024-01-27T00:00:00",
            "issues": [],
            "dependencies_ok": True,
            "permissions_ok": True,
            "config_valid": True
        }
        
    except Exception as e:
        logger.error(f"检查技能健康状态失败: {skill_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/categories")
async def get_categories():
    """获取技能分类列表"""
    try:
        # 这里应该从技能数据中提取分类
        # 暂时返回模拟数据
        categories = [
            "数据分析",
            "数据采集", 
            "文档处理",
            "自动化",
            "开发工具",
            "多媒体",
            "网络",
            "安全",
            "机器学习",
            "通用"
        ]
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")