"""能力中心API路由

统一管理工具、技能和MCP能力的接口
"""
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.skill import Skill
from app.models.tool import Tool
from app.models.agent import Agent
from app.models.agent_tool_association import AgentToolAssociation

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== 请求/响应模型 ====================

class CapabilityListRequest(BaseModel):
    """能力列表请求参数"""
    type: Optional[str] = Field(None, description="类型筛选: tool/skill/all")
    source: Optional[str] = Field(None, description="来源筛选: official/user/marketplace")
    status: Optional[str] = Field(None, description="状态筛选: active/disabled")
    category: Optional[str] = Field(None, description="分类筛选")
    search: Optional[str] = Field(None, description="搜索关键词")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class CapabilityToggleRequest(BaseModel):
    """能力启用/禁用请求"""
    enabled: bool


class AgentCapabilityAssignment(BaseModel):
    """智能体能力分配请求"""
    agent_id: int
    capability_id: int
    capability_type: str  # skill/tool
    priority: int = 0
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class CapabilityResponse(BaseModel):
    """能力响应模型"""
    id: int
    type: str  # skill/tool
    name: str
    display_name: str
    description: Optional[str]
    category: str
    version: str
    icon: str
    tags: List[str]
    source: str
    is_official: bool
    is_builtin: bool
    official_badge: Optional[str]
    is_protected: bool
    allow_disable: bool
    allow_edit: bool
    status: str
    is_active: bool
    author: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    usage_count: int

    class Config:
        from_attributes = True


# ==================== 工具函数 ====================

import json

def skill_to_dict(skill: Skill) -> Dict[str, Any]:
    """将Skill模型转换为字典"""
    # 处理tags字段，确保它是列表
    tags = skill.tags
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            tags = []
    
    return {
        "id": skill.id,
        "type": "skill",
        "name": skill.name,
        "display_name": skill.display_name or skill.name,
        "description": skill.description,
        "category": "skill",
        "version": skill.version or "1.0.0",
        "icon": skill.icon or "📝",
        "tags": tags,
        "source": skill.source or "local",
        "is_official": skill.is_official or False,
        "is_builtin": skill.is_builtin or False,
        "official_badge": skill.official_badge,
        "is_protected": skill.is_protected or False,
        "allow_disable": skill.allow_disable if skill.allow_disable is not None else True,
        "allow_edit": skill.allow_edit if skill.allow_edit is not None else True,
        "status": skill.status or "disabled",
        "is_active": skill.status == "active",
        "author": skill.author,
        "created_at": skill.created_at.isoformat() if skill.created_at else None,
        "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
        "usage_count": skill.usage_count or 0
    }


def tool_to_dict(tool: Tool) -> Dict[str, Any]:
    """将Tool模型转换为字典"""
    # 处理tags字段，确保它是列表
    tags = tool.tags
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            tags = []
    
    return {
        "id": tool.id,
        "type": "tool",
        "name": tool.name,
        "display_name": tool.display_name or tool.name,
        "description": tool.description,
        "category": tool.category or "general",
        "version": tool.version or "1.0.0",
        "icon": tool.icon or "🔧",
        "tags": tags,
        "source": tool.source or "user",
        "is_official": tool.is_official or False,
        "is_builtin": tool.is_builtin or False,
        "official_badge": tool.official_badge,
        "is_protected": tool.is_protected or False,
        "allow_disable": tool.allow_disable if tool.allow_disable is not None else True,
        "allow_edit": tool.allow_edit if tool.allow_edit is not None else True,
        "status": tool.status or "disabled",
        "is_active": tool.is_active if tool.is_active is not None else True,
        "author": tool.author,
        "created_at": tool.created_at.isoformat() if tool.created_at else None,
        "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
        "usage_count": tool.usage_count or 0
    }


# ==================== API端点 ====================

@router.get("/capabilities", response_model=Dict[str, Any])
async def list_capabilities(
    type: Optional[str] = Query(None, description="类型筛选: tool/skill/all"),
    source: Optional[str] = Query(None, description="来源筛选: official/user/marketplace"),
    status_filter: Optional[str] = Query(None, description="状态筛选: active/disabled", alias="status"),
    category: Optional[str] = Query(None, description="分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取统一的能力列表
    
    支持分页、筛选和搜索功能
    """
    try:
        items = []
        
        # 获取技能
        if type in (None, "all", "skill"):
            skill_query = db.query(Skill)
            
            # 应用筛选
            if source:
                skill_query = skill_query.filter(Skill.source == source)
            if status_filter:
                skill_query = skill_query.filter(Skill.status == status_filter)
            if search:
                skill_query = skill_query.filter(
                    or_(
                        Skill.name.contains(search),
                        Skill.display_name.contains(search),
                        Skill.description.contains(search)
                    )
                )
            
            skills = skill_query.all()
            items.extend([skill_to_dict(skill) for skill in skills])
        
        # 获取工具（不包括MCP工具，除非type为all）
        if type in (None, "all", "tool"):
            tool_query = db.query(Tool)
            
            # 应用筛选
            if source:
                tool_query = tool_query.filter(Tool.source == source)
            if status_filter:
                tool_query = tool_query.filter(Tool.status == status_filter)
            if category:
                tool_query = tool_query.filter(Tool.category == category)
            if search:
                tool_query = tool_query.filter(
                    or_(
                        Tool.name.contains(search),
                        Tool.display_name.contains(search),
                        Tool.description.contains(search)
                    )
                )
            # 如果不是查询所有类型，排除MCP工具（MCP工具单独显示）
            if type == "tool":
                tool_query = tool_query.filter(Tool.tool_type != "mcp")
            
            tools = tool_query.all()
            items.extend([tool_to_dict(tool) for tool in tools])
        
        # 获取MCP工具
        if type in (None, "all", "mcp"):
            mcp_query = db.query(Tool).filter(Tool.tool_type == "mcp")
            
            # 应用筛选
            if source:
                mcp_query = mcp_query.filter(Tool.source == source)
            if status_filter:
                mcp_query = mcp_query.filter(Tool.status == status_filter)
            if search:
                mcp_query = mcp_query.filter(
                    or_(
                        Tool.name.contains(search),
                        Tool.display_name.contains(search),
                        Tool.description.contains(search)
                    )
                )
            
            mcp_tools = mcp_query.all()
            items.extend([tool_to_dict(tool) for tool in mcp_tools])
        
        # 排序：官方优先，然后按名称
        items.sort(key=lambda x: (not x["is_official"], x["display_name"]))
        
        # 分页
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = items[start:end]
        
        return {
            "success": True,
            "data": {
                "items": paginated_items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        import traceback
        import sys
        error_detail = f"获取能力列表失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)  # 使用logger记录错误
        # 同时输出到stderr
        print(error_detail, file=sys.stderr, flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取能力列表失败: {str(e)}"
        )


@router.get("/capabilities/categories")
async def get_capability_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取能力分类列表"""
    try:
        # 获取工具分类
        tool_categories = db.query(Tool.category).distinct().all()
        
        categories = []
        for (cat,) in tool_categories:
            if cat:
                categories.append({
                    "id": cat,
                    "name": cat,
                    "type": "tool"
                })
        
        # 添加技能分类
        categories.append({
            "id": "skill",
            "name": "技能",
            "type": "skill"
        })
        
        return {
            "success": True,
            "data": categories
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类失败: {str(e)}"
        )


@router.post("/capabilities/{capability_type}/{capability_id}/toggle")
async def toggle_capability(
    capability_type: str,
    capability_id: int,
    request: CapabilityToggleRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    启用/禁用能力
    
    - capability_type: skill 或 tool
    - capability_id: 能力ID
    """
    try:
        if capability_type == "skill":
            item = db.query(Skill).filter(Skill.id == capability_id).first()
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="技能不存在"
                )
            
            # 检查是否允许禁用
            if not request.enabled and item.is_protected:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="该技能受保护，无法禁用"
                )
            
            item.status = "active" if request.enabled else "disabled"
            
        elif capability_type == "tool":
            item = db.query(Tool).filter(Tool.id == capability_id).first()
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="工具不存在"
                )
            
            # 检查是否允许禁用
            if not request.enabled and item.is_protected:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="该工具受保护，无法禁用"
                )
            
            item.status = "active" if request.enabled else "disabled"
            item.is_active = request.enabled
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的能力类型: {capability_type}"
            )
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{'启用' if request.enabled else '禁用'}成功",
            "data": {
                "id": capability_id,
                "type": capability_type,
                "enabled": request.enabled
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"操作失败: {str(e)}"
        )


@router.delete("/capabilities/{capability_type}/{capability_id}")
async def delete_capability(
    capability_type: str,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除能力（仅支持用户创建的能力）"""
    try:
        if capability_type == "skill":
            item = db.query(Skill).filter(Skill.id == capability_id).first()
        elif capability_type == "tool":
            item = db.query(Tool).filter(Tool.id == capability_id).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的能力类型: {capability_type}"
            )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="能力不存在"
            )
        
        # 检查是否允许删除
        if item.is_protected or item.is_official:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="官方能力无法删除"
            )
        
        db.delete(item)
        db.commit()
        
        return {
            "success": True,
            "message": "删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


# ==================== 智能体能力管理 ====================

@router.get("/agents/{agent_id}/capabilities")
async def get_agent_capabilities(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取智能体的能力分配"""
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="智能体不存在"
            )
        
        # 获取技能关联
        skills = []
        for assoc in agent.skill_associations:
            if assoc.skill:
                skills.append({
                    "id": assoc.skill.id,
                    "type": "skill",
                    "name": assoc.skill.name,
                    "display_name": assoc.skill.display_name,
                    "priority": assoc.priority,
                    "enabled": assoc.enabled,
                    "config": assoc.config
                })
        
        # 获取工具关联
        tools = []
        for assoc in agent.tool_associations:
            if assoc.tool:
                tools.append({
                    "id": assoc.tool.id,
                    "type": "tool",
                    "name": assoc.tool.name,
                    "display_name": assoc.tool.display_name,
                    "priority": assoc.priority,
                    "enabled": assoc.enabled,
                    "config": assoc.config
                })
        
        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "agent_type": agent.agent_type,
                "primary_capability_id": agent.primary_capability_id,
                "primary_capability_type": agent.primary_capability_type,
                "skills": skills,
                "tools": tools
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.post("/agents/{agent_id}/capabilities/assign")
async def assign_capability_to_agent(
    agent_id: int,
    assignment: AgentCapabilityAssignment,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """为智能体分配能力"""
    try:
        # 验证智能体
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="智能体不存在"
            )
        
        # 验证能力
        if assignment.capability_type == "skill":
            # TODO: 技能关联功能需要使用其他方式实现（如task_skills表）
            # 暂时返回错误提示
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="技能关联功能暂未实现，请使用工具关联"
            )
                
        elif assignment.capability_type == "tool":
            capability = db.query(Tool).filter(Tool.id == assignment.capability_id).first()
            if not capability:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="工具不存在"
                )
            
            # 检查是否已关联
            existing = db.query(AgentToolAssociation).filter(
                AgentToolAssociation.agent_id == agent_id,
                AgentToolAssociation.tool_id == assignment.capability_id
            ).first()
            
            if existing:
                existing.priority = assignment.priority
                existing.enabled = assignment.enabled
                existing.config = assignment.config
            else:
                new_assoc = AgentToolAssociation(
                    agent_id=agent_id,
                    tool_id=assignment.capability_id,
                    priority=assignment.priority,
                    enabled=assignment.enabled,
                    config=assignment.config
                )
                db.add(new_assoc)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的能力类型: {assignment.capability_type}"
            )
        
        # 更新智能体主能力（如果是单一功能智能体）
        if agent.agent_type == "single":
            agent.primary_capability_id = assignment.capability_id
            agent.primary_capability_type = assignment.capability_type
        
        db.commit()
        
        return {
            "success": True,
            "message": "能力分配成功",
            "data": {
                "agent_id": agent_id,
                "capability_id": assignment.capability_id,
                "capability_type": assignment.capability_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配失败: {str(e)}"
        )


@router.post("/agents/{agent_id}/capabilities/remove")
async def remove_capability_from_agent(
    agent_id: int,
    capability_type: str,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """从智能体移除能力"""
    try:
        if capability_type == "skill":
            # TODO: 技能关联功能暂未实现
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="技能关联功能暂未实现，请使用工具关联"
            )
        elif capability_type == "tool":
            assoc = db.query(AgentToolAssociation).filter(
                AgentToolAssociation.agent_id == agent_id,
                AgentToolAssociation.tool_id == capability_id
            ).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的能力类型: {capability_type}"
            )
        
        if not assoc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联不存在"
            )
        
        db.delete(assoc)
        db.commit()
        
        return {
            "success": True,
            "message": "能力已移除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除失败: {str(e)}"
        )
