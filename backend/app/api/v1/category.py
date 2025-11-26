"""分类相关API路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.category_db import ModelCategoryDB
from app.schemas.category import ModelCategoryCreate, ModelCategoryResponse
from app.api.dependencies import get_db, get_current_user

# 创建路由器
router = APIRouter()

@router.post("/model/categories", response_model=ModelCategoryResponse)
def create_model_category(
    category: ModelCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建新的模型分类"""
    # 检查名称是否已存在
    existing = db.query(ModelCategoryDB).filter(ModelCategoryDB.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    # 检查父分类是否存在
    if category.parent_id:
        parent = db.query(ModelCategoryDB).filter(ModelCategoryDB.id == category.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category not found")
    
    # 创建分类对象
    db_category = ModelCategoryDB(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    # 构建响应（包括空的children列表）
    return {
        "id": db_category.id,
        "name": db_category.name,
        "display_name": db_category.display_name,
        "description": db_category.description,
        "category_type": db_category.category_type,
        "parent_id": db_category.parent_id,
        "is_active": db_category.is_active,
        "children": []
    }

@router.get("/model/categories", response_model=List[ModelCategoryResponse])
def get_all_model_categories(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取所有模型分类，构建树形结构"""
    # 获取所有分类
    categories = db.query(ModelCategoryDB).all()
    
    # 构建分类字典
    category_dict = {}
    root_categories = []
    
    # 先创建所有分类对象
    for cat in categories:
        category_dict[cat.id] = {
            "id": cat.id,
            "name": cat.name,
            "display_name": cat.display_name,
            "description": cat.description,
            "category_type": cat.category_type,
            "parent_id": cat.parent_id,
            "is_active": cat.is_active,
            "children": []
        }
    
    # 构建树形结构
    for cat in categories:
        if cat.parent_id is None or cat.parent_id not in category_dict:
            root_categories.append(category_dict[cat.id])
        else:
            category_dict[cat.parent_id]["children"].append(category_dict[cat.id])
    
    return root_categories

@router.get("/model/categories/{category_id}", response_model=ModelCategoryResponse)
def get_model_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取单个模型分类"""
    category = db.query(ModelCategoryDB).filter(ModelCategoryDB.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 构建响应（包括空的children列表）
    return {
        "id": category.id,
        "name": category.name,
        "display_name": category.display_name,
        "description": category.description,
        "category_type": category.category_type,
        "parent_id": category.parent_id,
        "is_active": category.is_active,
        "children": []
    }

@router.get("/model/categories/tree/all", response_model=List[ModelCategoryResponse])
def get_category_tree(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取分类树形结构，与get_all_model_categories相同"""
    # 直接调用获取所有分类的方法
    return get_all_model_categories(db, current_user)