"""模型分类相关的API路由"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime
from sqlalchemy import text

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.model_category import ModelCategory
from app.schemas.model_category import (
    ModelCategoryResponse,
    ModelCategoryListResponse,
    ModelCategoryAssociationCreate,
    ModelCategoryAssociationResponse,
    ModelCategoryWithChildrenResponse,
    ModelWithCategoriesResponse,
    CategoryWithModelsResponse
)
from app.services.model_category_service import model_category_service

# 创建分类LOGO的上传目录
# 使用绝对路径定义UPLOAD_DIR
import os
UPLOAD_DIR = "E:\\PY\\CODES\\py copilot IV\\frontend\\public\\logos\\categories"
UPLOAD_DIR = os.path.normpath(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"分类LOGO上传目录: {UPLOAD_DIR}")  # 添加日志以便调试

# 支持的图片扩展名
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# 检查文件扩展名是否允许
def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def save_category_logo(upload_file: UploadFile) -> Optional[str]:
    """保存上传的分类LOGO文件并返回文件名"""
    if not allowed_file(upload_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，请上传图片文件 (png, jpg, jpeg, gif, webp)"
        )
    
    # 生成唯一文件名
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    # 检查文件名是否有扩展名
    if '.' not in upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名必须包含扩展名"
        )
    file_ext = upload_file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        print(f"尝试保存分类LOGO到: {file_path}")  # 添加日志
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
        print(f"分类LOGO保存成功: {unique_filename}")  # 添加成功日志
        # 返回文件名
        return unique_filename
    except Exception as e:
        print(f"分类LOGO保存失败: {str(e)}")  # 添加错误日志
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )

# 创建路由器
router = APIRouter(prefix="/categories", tags=["model_categories"])


# 模拟用户认证依赖
async def get_current_user():
    """获取当前用户"""
    # 实际项目中应该有真实的认证逻辑
    return {"id": 1, "username": "admin"}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新的模型分类，支持JSON和表单请求"""
    logo_path = None
    try:
        # 根据Content-Type处理不同类型的请求
        content_type = request.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            # 处理JSON请求
            json_data = await request.json()
            name = json_data.get("name")
            display_name = json_data.get("display_name")
            description = json_data.get("description")
            category_type = json_data.get("category_type", "main")
            parent_id = json_data.get("parent_id")
            is_active = json_data.get("is_active", True)
            logo_path = json_data.get("logo")
        elif "multipart/form-data" in content_type:
            # 处理表单请求
            form_data = await request.form()
            name = form_data.get("name")
            display_name = form_data.get("display_name")
            description = form_data.get("description")
            category_type = form_data.get("category_type", "main")
            parent_id = form_data.get("parent_id")
            is_active = form_data.get("is_active", True)
            if isinstance(is_active, str):
                is_active = is_active.lower() == "true"
            
            # 处理文件上传
            logo_file = None
            if "logo_file" in form_data:
                logo_file = form_data["logo_file"]
            elif "logo" in form_data and hasattr(form_data["logo"], "file"):
                logo_file = form_data["logo"]
            
            logo_path = form_data.get("logo")  # Font Awesome图标
            if logo_file:
                # 如果上传了文件，优先使用文件
                logo_filename = await save_category_logo(logo_file)
                logo_path = f"/logos/categories/{logo_filename}"
        else:
            # 不支持的Content-Type
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported media type. Please use application/json or multipart/form-data."
            )
        
        # 验证必填字段
        if not name or not display_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name and display_name are required."
            )
        
        # 创建分类数据
        category_data = {
            "name": name,
            "display_name": display_name,
            "description": description,
            "category_type": category_type,
            "parent_id": parent_id,
            "is_active": is_active,
            "is_system": False,
            "logo": logo_path
        }
        
        # 调用服务创建分类
        db_category = model_category_service.create_category(db, category_data)
        
        # 手动构建响应，确保datetime对象转换为ISO格式字符串
        return {
            "id": db_category.id,
            "name": db_category.name,
            "display_name": db_category.display_name,
            "description": db_category.description,
            "category_type": db_category.category_type,
            "parent_id": db_category.parent_id,
            "is_active": db_category.is_active,
            "is_system": db_category.is_system,
            "logo": db_category.logo,
            "created_at": db_category.created_at.isoformat() if db_category.created_at else None,
            "updated_at": db_category.updated_at.isoformat() if db_category.updated_at else None
        }
    except HTTPException:
        # 如果创建失败，删除已上传的LOGO文件
        if logo_path and logo_file:
            try:
                os.remove(os.path.join(UPLOAD_DIR, logo_path.split("/")[-1]))
            except:
                pass
        raise


@router.get("/{category_id}", response_model=ModelCategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个模型分类"""
    db_category = model_category_service.get_category(db, category_id)
    
    # 手动构建响应，将datetime转换为ISO格式
    return {
        "id": db_category.id,
        "name": db_category.name,
        "display_name": db_category.display_name,
        "description": db_category.description,
        "category_type": db_category.category_type,
        "parent_id": db_category.parent_id,
        "is_active": db_category.is_active,
        "is_system": db_category.is_system,
        "logo": db_category.logo,
        "created_at": db_category.created_at.isoformat() if db_category.created_at is not None else None,
        "updated_at": db_category.updated_at.isoformat() if db_category.updated_at is not None else None
    }


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
    # 获取分类列表
    result = model_category_service.get_categories(
        db, skip, limit, category_type, is_active, parent_id
    )
    
    # 手动构建响应，将datetime对象转换为ISO格式
    categories_list = []
    for category in result["categories"]:
        categories_list.append({
            "id": category.id,
            "name": category.name,
            "display_name": category.display_name,
            "description": category.description,
            "category_type": category.category_type,
            "parent_id": category.parent_id,
            "is_active": category.is_active,
            "is_system": getattr(category, "is_system", False),
            "logo": getattr(category, "logo", None),
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "updated_at": category.updated_at.isoformat() if category.updated_at else None
        })
    
    return {
        "categories": categories_list,
        "total": result["total"]
    }


@router.put("/{category_id}", response_model=ModelCategoryResponse)
async def update_category(
    category_id: int,
    request: Request,
    name: Optional[str] = Form(None),
    display_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_type: Optional[str] = Form(None),
    parent_id: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    logo: Optional[UploadFile] = File(None),
    existing_logo: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新模型分类"""
    # 处理LOGO上传
    logo_path = None
    uploaded_logo = False
    if logo:
        logo_filename = await save_category_logo(logo)
        logo_path = f"/logos/categories/{logo_filename}"
        uploaded_logo = True
    elif existing_logo:
        # 如果没有上传新LOGO，但提供了现有LOGO路径，使用现有路径
        logo_path = existing_logo
    
    # 创建更新数据
    update_data = {
        "name": name,
        "display_name": display_name,
        "description": description,
        "category_type": category_type,
        "parent_id": parent_id,
        "is_active": is_active,
        "logo": logo_path
    }
    
    # 过滤掉None值
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    try:
        # 调用服务更新分类
        updated_category = model_category_service.update_category(
            db, category_id, update_data
        )
        
        # 手动构建响应，将datetime转换为ISO格式
        return {
            "id": updated_category.id,
            "name": updated_category.name,
            "display_name": updated_category.display_name,
            "description": updated_category.description,
            "category_type": updated_category.category_type,
            "parent_id": updated_category.parent_id,
            "is_active": updated_category.is_active,
            "is_system": updated_category.is_system,
            "logo": updated_category.logo,
            "created_at": updated_category.created_at.isoformat() if updated_category.created_at is not None else None,
            "updated_at": updated_category.updated_at.isoformat() if updated_category.updated_at is not None else None
        }
    except HTTPException:
        # 如果更新失败，删除已上传的LOGO文件
        if uploaded_logo and logo_path:
            try:
                os.remove(os.path.join(UPLOAD_DIR, logo_path.split("/")[-1]))
            except:
                pass
        raise


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除模型分类（软删除）"""
    model_category_service.delete_category(db, category_id)
    return None


def serialize_category_with_children(category):
    """递归序列化分类及其子分类，将datetime转换为ISO格式"""
    serialized = {
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
    }
    
    # 递归处理子分类
    if hasattr(category, 'children') and category.children:
        serialized["children"] = [serialize_category_with_children(child) for child in category.children]
    
    return serialized

@router.get("/tree/all", response_model=List[ModelCategoryWithChildrenResponse])
async def get_category_tree(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取模型分类的树形结构"""
    tree = model_category_service.get_category_tree(db)
    
    # 序列化树形结构，将datetime转换为ISO格式
    serialized_tree = [serialize_category_with_children(category) for category in tree]
    return serialized_tree


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
    
    # 手动构建响应，将datetime转换为ISO格式
    serialized_association = {
        "id": db_association.id,
        "model_id": db_association.model_id,
        "category_id": db_association.category_id,
        "created_at": db_association.created_at.isoformat() if db_association.created_at is not None else None,
        "updated_at": db_association.updated_at.isoformat() if db_association.updated_at is not None else None
    }
    
    return serialized_association


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
    
    # 序列化模型列表，将datetime转换为ISO格式
    serialized_models = []
    for model in models:
        # 序列化模型基本信息
        serialized_model = {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "description": model.description,
            "created_at": model.created_at.isoformat() if model.created_at is not None else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at is not None else None
        }
        
        # 添加分类信息（如果有）
        if hasattr(model, 'categories') and model.categories:
            serialized_categories = []
            for category in model.categories:
                serialized_category = {
                    "id": category.id,
                    "name": category.name,
                    "display_name": category.display_name,
                    "description": category.description,
                    "category_type": category.category_type,
                    "parent_id": category.parent_id,
                    "is_active": category.is_active,
                    "is_system": getattr(category, 'is_system', False),
                    "logo": getattr(category, 'logo', None),
                    "created_at": category.created_at.isoformat() if category.created_at is not None else None,
                    "updated_at": category.updated_at.isoformat() if category.updated_at is not None else None
                }
                serialized_categories.append(serialized_category)
            serialized_model["categories"] = serialized_categories
        
        serialized_models.append(serialized_model)
    
    return serialized_models


@router.get("/model/{model_id}/categories", response_model=List[ModelCategoryResponse])
async def get_categories_by_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取指定模型的所有分类"""
    categories = model_category_service.get_categories_by_model(db, model_id)
    
    # 序列化分类列表，将datetime转换为ISO格式
    serialized_categories = []
    for category in categories:
        serialized = {
            "id": category.id,
            "name": category.name,
            "display_name": category.display_name,
            "description": category.description,
            "category_type": category.category_type,
            "parent_id": category.parent_id,
            "is_active": category.is_active,
            "is_system": getattr(category, 'is_system', False),
            "logo": getattr(category, 'logo', None),
            "created_at": category.created_at.isoformat() if category.created_at is not None else None,
            "updated_at": category.updated_at.isoformat() if category.updated_at is not None else None
        }
        serialized_categories.append(serialized)
    
    return serialized_categories