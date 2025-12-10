"""模型分类相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.model_category import (
    ModelCategoryCreate,
    ModelCategoryUpdate,
    ModelCategoryResponse,
    ModelCategoryListResponse,
    ModelCategoryAssociationCreate,
    ModelCategoryAssociationResponse,
    ModelCategoryWithChildrenResponse,
    ModelWithCategoriesResponse,
    CategoryWithModelsResponse
)
from app.services.model_category_service import model_category_service

# 创建路由器
router = APIRouter(prefix="/categories", tags=["model_categories"])


# 模拟用户认证依赖
async def get_current_user():
    """获取当前用户"""
    # 实际项目中应该有真实的认证逻辑
    return {"id": 1, "username": "admin"}


@router.post("/", response_model=ModelCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: ModelCategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新的模型分类"""
    db_category = model_category_service.create_category(db, category)
    return db_category


@router.get("/{category_id}", response_model=ModelCategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个模型分类"""
    db_category = model_category_service.get_category(db, category_id)
    return db_category


@router.get("/")
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_type: Optional[str] = Query(None, regex="^(main|secondary)$"),
    is_active: Optional[bool] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取模型分类列表"""
    query = db.query(ModelCategory)
    
    # 应用过滤条件
    if category_type:
        query = query.filter(ModelCategory.category_type == category_type)
    if is_active is not None:
        query = query.filter(ModelCategory.is_active == is_active)
    if parent_id is not None:
        query = query.filter(ModelCategory.parent_id == parent_id)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    categories = query.offset(skip).limit(limit).all()
    
    # 手动构建响应，确保所有字段都被包含
    categories_list = []
    for category in categories:
        categories_list.append({
            "id": category.id,
            "name": category.name,
            "display_name": category.display_name,
            "description": category.description,
            "category_type": category.category_type,
            "parent_id": category.parent_id,
            "is_active": category.is_active,
            "is_system": category.is_system,
            "logo": category.logo,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "updated_at": category.updated_at.isoformat() if category.updated_at else None
        })
    
    return {
        "categories": categories_list,
        "total": total
    }


@router.put("/{category_id}", response_model=ModelCategoryResponse)
async def update_category(
    category_id: int,
    category_update: ModelCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新模型分类"""
    updated_category = model_category_service.update_category(
        db, category_id, category_update
    )
    return updated_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除模型分类（软删除）"""
    model_category_service.delete_category(db, category_id)
    return None


@router.get("/tree/all", response_model=List[ModelCategoryWithChildrenResponse])
async def get_category_tree(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取模型分类的树形结构"""
    tree = model_category_service.get_category_tree(db)
    return tree


@router.post("/associations", response_model=ModelCategoryAssociationResponse, status_code=status.HTTP_201_CREATED)
async def create_model_category_association(
    association: ModelCategoryAssociationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建模型和分类的关联"""
    db_association = model_category_service.add_category_to_model(
        db, association.model_id, association.category_id
    )
    return db_association


@router.delete("/associations/model/{model_id}/category/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_category_association(
    model_id: int,
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除模型和分类的关联"""
    model_category_service.remove_category_from_model(db, model_id, category_id)
    return None


@router.get("/{category_id}/models", response_model=List[ModelWithCategoriesResponse])
async def get_models_by_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取指定分类下的所有模型"""
    models = model_category_service.get_models_by_category(db, category_id)
    return models


@router.get("/model/{model_id}/categories", response_model=List[ModelCategoryResponse])
async def get_categories_by_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取指定模型的所有分类"""
    categories = model_category_service.get_categories_by_model(db, model_id)
    return categories