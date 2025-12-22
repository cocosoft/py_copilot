"""智能体分类API路由"""
from typing import Any, Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.schemas.agent_category import AgentCategoryCreate, AgentCategoryUpdate, AgentCategoryResponse, AgentCategoryListResponse
from app.services.agent_category_service import agent_category_service

router = APIRouter()


# 树形结构响应模型
class CategoryTreeNode(BaseModel):
    """分类树节点"""
    id: int
    name: str
    logo: Optional[str]
    is_system: bool
    is_root: bool
    is_leaf: bool
    children: List["CategoryTreeNode"]


class CategoryTreeResponse(BaseModel):
    """分类树响应"""
    categories: List[CategoryTreeNode]


class CategoryPathResponse(BaseModel):
    """分类路径响应"""
    path: List[AgentCategoryResponse]


CategoryTreeNode.update_forward_refs()


@router.post("/", response_model=AgentCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_agent_category_api(
    category_in: AgentCategoryCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    创建智能体分类接口
    
    Args:
        category_in: 智能体分类创建信息
        db: 数据库会话
    
    Returns:
        创建成功的智能体分类信息
    """
    category = agent_category_service.create_category(db=db, category_data=category_in)
    return category


@router.get("/{category_id}", response_model=AgentCategoryResponse)
def get_agent_category_api(
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    根据ID获取智能体分类接口
    
    Args:
        category_id: 智能体分类ID
        db: 数据库会话
    
    Returns:
        智能体分类信息
    """
    return agent_category_service.get_category(db=db, category_id=category_id)


@router.get("/", response_model=AgentCategoryListResponse)
def get_agent_categories_api(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_system: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取智能体分类列表接口
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        is_system: 是否系统分类（可选）
        db: 数据库会话
    
    Returns:
        智能体分类列表信息
    """
    result = agent_category_service.get_categories(db=db, skip=skip, limit=limit, is_system=is_system)
    return result


@router.put("/{category_id}", response_model=AgentCategoryResponse)
def update_agent_category_api(
    category_id: int,
    category_in: AgentCategoryUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """
    更新智能体分类接口
    
    Args:
        category_id: 智能体分类ID
        category_in: 智能体分类更新信息
        db: 数据库会话
    
    Returns:
        更新后的智能体分类信息
    """
    return agent_category_service.update_category(db=db, category_id=category_id, category_update=category_in)


@router.delete("/{category_id}")
def delete_agent_category_api(
    category_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    删除智能体分类接口
    
    Args:
        category_id: 智能体分类ID
        db: 数据库会话
    
    Returns:
        删除成功的消息
    """
    success = agent_category_service.delete_category(db=db, category_id=category_id)
    if success:
        return {"message": "智能体分类删除成功"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="智能体分类不存在"
    )


# 树形结构相关API端点

@router.get("/tree/", response_model=CategoryTreeResponse)
def get_agent_category_tree_api(db: Session = Depends(get_db)) -> Any:
    """
    获取智能体分类树结构接口
    
    Args:
        db: 数据库会话
    
    Returns:
        完整的智能体分类树结构
    """
    tree_data = agent_category_service.get_category_tree(db=db)
    return {"categories": tree_data}


@router.get("/roots/", response_model=AgentCategoryListResponse)
def get_root_agent_categories_api(db: Session = Depends(get_db)) -> Any:
    """
    获取所有根分类接口
    
    Args:
        db: 数据库会话
    
    Returns:
        根分类列表信息
    """
    root_categories = agent_category_service.get_root_categories(db=db)
    return {"categories": root_categories, "total": len(root_categories)}


@router.get("/{category_id}/children/", response_model=AgentCategoryListResponse)
def get_agent_category_children_api(
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取指定分类的子分类接口
    
    Args:
        category_id: 智能体分类ID
        db: 数据库会话
    
    Returns:
        子分类列表信息
    """
    children = agent_category_service.get_category_children(db=db, category_id=category_id)
    return {"categories": children, "total": len(children)}


@router.get("/{category_id}/path/", response_model=CategoryPathResponse)
def get_agent_category_path_api(
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取分类路径接口
    
    Args:
        category_id: 智能体分类ID
        db: 数据库会话
    
    Returns:
        从根分类到当前分类的完整路径
    """
    path = agent_category_service.get_category_path(db=db, category_id=category_id)
    return {"path": path}


@router.get("/level/{level}/", response_model=AgentCategoryListResponse)
def get_agent_categories_by_level_api(
    level: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取指定层级的分类接口
    
    Args:
        level: 层级（0表示根分类）
        db: 数据库会话
    
    Returns:
        指定层级的分类列表信息
    """
    categories = agent_category_service.get_categories_by_level(db=db, level=level)
    return {"categories": categories, "total": len(categories)}