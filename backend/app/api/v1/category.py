"""分类相关API路由"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.category_db import ModelCategoryDB
from app.schemas.category import ModelCategoryCreate, ModelCategoryResponse
from app.api.dependencies import get_db, get_current_user
import json

# 创建路由器
router = APIRouter()

@router.post("/model/categories")
async def create_model_category(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建新的模型分类"""
    try:
        # 获取请求体
        json_data = await request.json()
        
        # 手动处理所有字段
        name = json_data.get("name")
        display_name = json_data.get("display_name")
        description = json_data.get("description")
        category_type = json_data.get("category_type", "main")
        
        # 手动处理parent_id字段
        parent_id = json_data.get("parent_id")
        if parent_id == '':
            parent_id = None
        elif parent_id is not None:
            try:
                parent_id = int(parent_id)
            except ValueError:
                parent_id = None
                
        is_active = json_data.get("is_active", True)
        if isinstance(is_active, str):
            is_active = is_active.lower() == "true"
        
        # 验证必填字段
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        
        # 检查名称是否已存在
        existing = db.query(ModelCategoryDB).filter(ModelCategoryDB.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists")
        
        # 检查父分类是否存在
        if parent_id:
            parent = db.query(ModelCategoryDB).filter(ModelCategoryDB.id == parent_id).first()
            if not parent:
                raise HTTPException(status_code=400, detail="Parent category not found")
        
        # 创建分类对象
        db_category = ModelCategoryDB(
            name=name,
            display_name=display_name,
            description=description,
            category_type=category_type,
            parent_id=parent_id,
            is_active=is_active
        )
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
            "dimension": getattr(db_category, "dimension", "task_type"),
            "children": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            "dimension": getattr(cat, "dimension", "task_type"),
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
        "dimension": getattr(category, "dimension", "task_type"),
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

@router.put("/model/categories/{category_id}", response_model=ModelCategoryResponse)
def update_model_category(
    category_id: int,
    category_data: ModelCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新模型分类"""
    # 查找分类
    category = db.query(ModelCategoryDB).filter(ModelCategoryDB.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 处理parent_id，如果是空字符串则设为None
    if category_data.parent_id == '':
        category_data.parent_id = None
    
    # 检查名称是否与其他分类冲突（如果名称有更改）
    if category.name != category_data.name:
        existing = db.query(ModelCategoryDB).filter(ModelCategoryDB.name == category_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    # 检查父分类是否存在（如果提供了父分类ID）
    if category_data.parent_id is not None and category_data.parent_id != category.parent_id:
        # 确保不能将分类设置为自己的子分类
        if category_data.parent_id == category_id:
            raise HTTPException(status_code=400, detail="Category cannot be its own parent")
        
        # 检查父分类是否存在
        parent = db.query(ModelCategoryDB).filter(ModelCategoryDB.id == category_data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category not found")
    
    # 更新分类数据
    for key, value in category_data.dict().items():
        setattr(category, key, value)
    
    # 提交更改
    db.commit()
    db.refresh(category)
    
    # 构建响应
    return {
        "id": category.id,
        "name": category.name,
        "display_name": category.display_name,
        "description": category.description,
        "category_type": category.category_type,
        "parent_id": category.parent_id,
        "is_active": category.is_active,
        "dimension": getattr(category, "dimension", "task_type"),
        "children": []
    }

@router.delete("/model/categories/{category_id}")
def delete_model_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除模型分类"""
    # 查找分类
    category = db.query(ModelCategoryDB).filter(ModelCategoryDB.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 检查是否有子分类
    has_children = db.query(ModelCategoryDB).filter(
        ModelCategoryDB.parent_id == category_id
    ).first()
    if has_children:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category with subcategories. Please delete subcategories first."
        )
    
    # 删除分类
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}