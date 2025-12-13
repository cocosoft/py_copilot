"""模型分类相关的API路由"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request
from fastapi.datastructures import FormData
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile
from datetime import datetime
import os

from app.core.dependencies import get_db
from app.modules.capability_category.schemas.model_category import (
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
from app.modules.capability_category.services.model_category_service import model_category_service

# 创建路由器
router = APIRouter(prefix="/categories", tags=["model_categories"])


# 模拟用户认证依赖
async def get_current_user():
    """获取当前用户"""
    # 实际项目中应该有真实的认证逻辑
    return {"id": 1, "username": "admin"}


# 文件上传配置
# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 当前文件目录
BASE_DIR = os.path.dirname(BASE_DIR)  # 项目根目录
UPLOAD_DIR = os.path.join(BASE_DIR, "frontend/public/logos/categories")
UPLOAD_DIR = os.path.normpath(UPLOAD_DIR)  # 规范化路径
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "webp"}

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"分类LOGO上传目录: {UPLOAD_DIR}")  # 添加日志以便调试


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


async def save_upload_file(upload_file: UploadFile) -> str:
    """保存上传的文件并返回相对路径"""
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    if not allowed_file(upload_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，请上传图片文件 (png, jpg, jpeg, gif, svg, webp)"
        )
    
    # 生成唯一文件名
    file_ext = upload_file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
        
        # 返回前端可访问的路径格式
        return f"/logos/categories/{unique_filename}"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )


# 移除了create_category_raw函数，因为它可能导致请求处理问题

# 同时支持JSON和multipart/form-data请求的路由
@router.post("/", response_class=JSONResponse)
async def create_category(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新的模型分类，支持JSON和multipart/form-data请求"""
    # 根据Content-Type决定如何处理请求
    content_type = request.headers.get("Content-Type", "")
    
    # 初始化变量
    name = None
    display_name = None
    description = None
    category_type = "main"
    parent_id = None
    is_active = True
    logo_path = None
    
    try:
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
            logo_path = form_data.get("logo")
            
            # 处理文件上传（如果有文件，则优先使用文件上传的logo）
            logo_file = form_data.get("logo_file")
            if logo_file:
                try:
                    # 保存LOGO文件
                    logo_path = await save_upload_file(logo_file)
                except Exception as e:
                    return JSONResponse(
                        status_code=500,
                        content={"detail": f"文件上传失败: {str(e)}"}
                    )
        else:
            # 不支持的Content-Type
            return JSONResponse(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                content={"detail": "Unsupported media type. Please use application/json or multipart/form-data."}
            )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"detail": f"请求解析失败: {str(e)}"}
        )
    
    # 构建分类数据
    category_data = {
        "name": name,
        "display_name": display_name,
        "description": description,
        "category_type": category_type,
        "parent_id": parent_id,
        "is_active": is_active,
        "logo": logo_path
    }
    
    try:
        # 创建分类
        db_category = model_category_service.create_category(db, ModelCategoryCreate(**category_data))
        
        # 手动构建响应
        return JSONResponse(
            status_code=201,
            content={
                "id": db_category.id,
                "name": db_category.name,
                "display_name": db_category.display_name,
                "description": db_category.description,
                "category_type": db_category.category_type,
                "parent_id": db_category.parent_id,
                "is_active": db_category.is_active,
                "is_system": db_category.is_system,
                "logo": db_category.logo,
                "created_at": db_category.created_at,
                "updated_at": db_category.updated_at
            }
        )
    except HTTPException as e:
        # 处理已知的HTTP异常
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    except Exception as e:
        # 处理未知异常
        return JSONResponse(
            status_code=500,
            content={"detail": f"创建分类失败: {str(e)}"}
        )


@router.get("/{category_id}", response_model=ModelCategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个模型分类"""
    db_category = model_category_service.get_category(db, category_id)
    return db_category


@router.get("/", response_model=ModelCategoryListResponse)
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
    result = model_category_service.get_categories(
        db=db,
        skip=skip,
        limit=limit,
        category_type=category_type,
        is_active=is_active,
        parent_id=parent_id
    )
    return result


@router.put("/{category_id}", status_code=status.HTTP_200_OK)
async def update_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新模型分类信息，支持JSON请求"""
    # 检查分类是否存在
    existing_category = model_category_service.get_category_by_id(db, category_id)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 初始化变量
    name = None
    display_name = None
    description = None
    category_type = None
    parent_id = None
    is_active = None
    logo_path = None
    default_parameters = None
    
    try:
        # 获取Content-Type
        content_type = request.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            # 处理普通JSON请求
            json_data = await request.json()
            
            name = json_data.get("name")
            display_name = json_data.get("display_name")
            description = json_data.get("description")
            category_type = json_data.get("category_type")
            parent_id = json_data.get("parent_id")
            is_active = json_data.get("is_active")
            logo_path = json_data.get("logo")
            default_parameters = json_data.get("default_parameters")
        else:
            # 对于所有非JSON请求，直接返回错误
            raise HTTPException(status_code=415, detail="Unsupported media type")
    except Exception as e:
        # 如果解析失败，直接返回错误信息
        raise HTTPException(status_code=400, detail=f"请求解析失败: {str(e)}")
    
    # 构建更新数据
    update_data = {}
    if name: update_data["name"] = name
    if display_name: update_data["display_name"] = display_name
    if description is not None: update_data["description"] = description
    if category_type: update_data["category_type"] = category_type
    if parent_id is not None: update_data["parent_id"] = parent_id
    if is_active is not None: update_data["is_active"] = is_active
    if logo_path is not None: update_data["logo"] = logo_path
    if default_parameters is not None: update_data["default_parameters"] = default_parameters
    
    # 更新分类
    updated_category = model_category_service.update_category(db, category_id, ModelCategoryUpdate(**update_data))
    
    # 手动构建响应，避免FastAPI自动转换可能导致的问题
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
        "created_at": updated_category.created_at,
        "updated_at": updated_category.updated_at
    }


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


# 类型参数管理API
@router.get("/{category_id}/parameters", response_model=Dict[str, Any])
async def get_category_parameters(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取分类默认参数"""
    category = model_category_service.get_category(db, category_id)
    # 返回default_parameters，确保总是返回字典类型
    return category.default_parameters or {}


@router.post("/{category_id}/parameters", response_model=Dict[str, Any])
async def set_category_parameters(
    category_id: int,
    parameters: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """设置分类默认参数"""
    # 获取现有分类
    category = model_category_service.get_category(db, category_id)
    
    # 检查是否为系统分类
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统分类不允许修改参数"
        )
    
    # 更新参数
    updated_category = model_category_service.update_category(
        db, 
        category_id, 
        ModelCategoryUpdate(default_parameters=parameters)
    )
    
    # 返回更新后的参数
    return updated_category.default_parameters or {}


@router.delete("/{category_id}/parameters/{param_name}", response_model=Dict[str, Any])
async def delete_category_parameter(
    category_id: int,
    param_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除分类默认参数"""
    # 获取现有分类
    category = model_category_service.get_category(db, category_id)
    
    # 检查是否为系统分类
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统分类不允许修改参数"
        )
    
    # 删除指定参数
    parameters = category.default_parameters or {}
    if param_name in parameters:
        del parameters[param_name]
    
    # 更新分类参数
    updated_category = model_category_service.update_category(
        db, 
        category_id, 
        ModelCategoryUpdate(default_parameters=parameters)
    )
    
    # 返回更新后的参数
    return updated_category.default_parameters or {}