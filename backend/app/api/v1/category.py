"""分类相关API路由"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.model_category import ModelCategory
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
        existing = db.query(ModelCategory).filter(ModelCategory.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists")
        
        # 检查父分类是否存在
        if parent_id:
            parent = db.query(ModelCategory).filter(ModelCategory.id == parent_id).first()
            if not parent:
                raise HTTPException(status_code=400, detail="Parent category not found")
        
        # 创建分类对象
        db_category = ModelCategory(
            name=name,
            display_name=display_name,
            description=description,
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
            "category_type": category_type,
            "parent_id": db_category.parent_id,
            "is_active": db_category.is_active,
            "dimension": getattr(db_category, "dimension", "task_type"),
            "children": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/categories")
def get_all_model_categories(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取所有模型分类，构建树形结构"""
    try:
        # 获取所有分类
        categories = db.query(ModelCategory).all()
        
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
                "category_type": getattr(cat, "category_type", "main"),
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
    except Exception as e:
        # 直接返回错误信息，避免日志记录可能带来的额外问题
        raise HTTPException(status_code=500, detail=f"错误: {str(e)}")

@router.get("/model/categories/{category_id}")
def get_model_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取单个模型分类"""
    try:
        category = db.query(ModelCategory).filter(ModelCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # 构建响应（包括空的children列表）
        return {
            "id": category.id,
            "name": category.name,
            "display_name": category.display_name,
            "description": category.description,
            "category_type": getattr(category, "category_type", "main"),
            "parent_id": category.parent_id,
            "is_active": category.is_active,
            "dimension": getattr(category, "dimension", "task_type"),
            "children": []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"错误: {str(e)}")

@router.get("/model/categories/tree/all")
def get_category_tree(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取完整的分类树形结构"""
    # 获取所有分类
    categories = db.query(ModelCategory).all()
    
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
            "category_type": getattr(cat, "category_type", "main"),
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

@router.get("/model/categories/primary")
def get_primary_categories(
    dimension: Optional[str] = "task_type",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取所有主分类（原模型类型）
    
    参数:
    - dimension: 分类维度，默认为"task_type"
    
    返回:
    - 指定维度的顶级分类列表
    """
    try:
        primary_categories = db.query(ModelCategory).filter(
            ModelCategory.dimension == dimension,
            ModelCategory.parent_id.is_(None),
            ModelCategory.is_active == True
        ).all()
        
        return [{
            "id": cat.id,
            "name": cat.name,
            "display_name": cat.display_name,
            "description": cat.description,
            "dimension": cat.dimension,
            "is_active": cat.is_active,
            "logo": cat.logo,
            "children": []
        } for cat in primary_categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"错误: {str(e)}")

@router.put("/model/categories/{category_id}")
async def update_model_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新模型分类"""
    try:
        # 获取请求体
        json_data = await request.json()
        
        # 查找分类
        category = db.query(ModelCategory).filter(ModelCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # 更新字段
        if "name" in json_data and json_data["name"] != category.name:
            # 检查新名称是否已存在
            existing = db.query(ModelCategory).filter(ModelCategory.name == json_data["name"]).first()
            if existing:
                raise HTTPException(status_code=400, detail="Category with this name already exists")
            category.name = json_data["name"]
        
        if "display_name" in json_data:
            category.display_name = json_data["display_name"]
        
        if "description" in json_data:
            category.description = json_data["description"]
        
        # 处理parent_id字段
        if "parent_id" in json_data:
            parent_id = json_data["parent_id"]
            if parent_id == '':
                parent_id = None
            elif parent_id is not None:
                try:
                    parent_id = int(parent_id)
                except ValueError:
                    parent_id = None
            
            # 检查父分类是否存在
            if parent_id:
                parent = db.query(ModelCategory).filter(ModelCategory.id == parent_id).first()
                if not parent:
                    raise HTTPException(status_code=400, detail="Parent category not found")
            
            category.parent_id = parent_id
        
        if "is_active" in json_data:
            is_active = json_data["is_active"]
            if isinstance(is_active, str):
                is_active = is_active.lower() == "true"
            category.is_active = is_active
        
        # 提交更改
        db.commit()
        db.refresh(category)
        
        # 构建响应（包括空的children列表）
        return {
            "id": category.id,
            "name": category.name,
            "display_name": category.display_name,
            "description": category.description,
            "category_type": getattr(category, "category_type", "main"),
            "parent_id": category.parent_id,
            "is_active": category.is_active,
            "dimension": getattr(category, "dimension", "task_type"),
            "children": []
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/model/categories/{category_id}")
def delete_model_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除模型分类"""
    # 查找分类
    category = db.query(ModelCategory).filter(ModelCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 检查是否有子分类
    children = db.query(ModelCategory).filter(ModelCategory.parent_id == category_id).first()
    if children:
        raise HTTPException(status_code=400, detail="Cannot delete category with children")
    
    # 删除分类
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}

