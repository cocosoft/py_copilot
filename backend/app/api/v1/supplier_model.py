"""供应商和模型相关的API路由"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import aiofiles

from app.core.dependencies import get_db
from app.models.supplier_db import SupplierDB, ModelDB
from app.schemas.supplier_model import (
    SupplierCreate, SupplierResponse,
    ModelCreate
)
from app.schemas.model_management import (
    ModelResponse, ModelListResponse, ModelWithSupplierResponse, ModelSupplierResponse
)
from app.services.capability_model_filter import CapabilityBasedModelFilter

router = APIRouter()

# 文件上传配置
# 获取项目根目录（backend的父目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 当前文件目录
BASE_DIR = os.path.dirname(BASE_DIR)  # api/v1
BASE_DIR = os.path.dirname(BASE_DIR)  # api
BASE_DIR = os.path.dirname(BASE_DIR)  # app
BASE_DIR = os.path.dirname(BASE_DIR)  # backend
BASE_DIR = os.path.dirname(BASE_DIR)  # 项目根目录
UPLOAD_DIR = os.path.join(BASE_DIR, "frontend/public/logos/providers")
UPLOAD_DIR = os.path.normpath(UPLOAD_DIR)  # 规范化路径
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg"}

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"文件上传目录: {UPLOAD_DIR}")  # 添加日志以便调试

# 供应商相关路由
async def save_upload_file(file: UploadFile) -> str:
    """保存上传的文件并返回相对路径"""
    # 检查文件扩展名
    filename = file.filename
    if not (filename and "." in filename):
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    extension = filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    # 生成唯一文件名
    unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # 返回前端可访问的路径格式
    return f"/logos/providers/{unique_filename}"

@router.post("/suppliers")
async def create_supplier(
    name: str = Form(...),
    description: str = Form(...),
    website: str = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """创建新的供应商（支持文件上传）"""
    # 检查name是否已存在 - 使用原始SQL查询避免ORM关系映射错误
    from sqlalchemy import text
    result = db.execute(text("SELECT id FROM suppliers WHERE name = :name"), {"name": name})
    existing_supplier = result.fetchone()
    if existing_supplier:
        raise HTTPException(status_code=400, detail="供应商名称已存在")
    
    # 保存logo文件（如果有）
    logo_path = None
    if logo:
        logo_path = await save_upload_file(logo)
    
    # 创建新供应商 - 使用原始SQL插入避免ORM关系映射错误
    now = datetime.utcnow()
    
    # 插入新供应商并直接返回所有字段
    insert_sql = """
        INSERT INTO suppliers (name, description, logo, website, created_at, updated_at)
        VALUES (:name, :description, :logo, :website, :created_at, :updated_at)
        RETURNING id, name, description, logo, website, created_at, updated_at, is_active
    """
    
    try:
        result = db.execute(text(insert_sql), {
            "name": name,
            "description": description,
            "logo": logo_path,
            "website": website,
            "created_at": now,
            "updated_at": now
        })
        
        # 获取新创建的供应商信息
        new_supplier = result.fetchone()
        
        # 提交事务
        db.commit()
        
        # 返回供应商信息
        return {
            "id": new_supplier.id,
            "name": new_supplier.name,
            "description": new_supplier.description,
            "logo": new_supplier.logo,
            "website": new_supplier.website,
            "created_at": new_supplier.created_at,
            "updated_at": new_supplier.updated_at,
            "is_active": new_supplier.is_active
        }
    except Exception as e:
        # 发生错误时回滚事务
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建供应商失败: {str(e)}")

# 供应商相关路由
@router.get("/suppliers-list", response_model=List[SupplierResponse])
def get_all_suppliers(db: Session = Depends(get_db)):
    """获取所有供应商"""
    # 使用ORM模型查询，确保API密钥正确解密
    suppliers = db.query(SupplierDB).all()
    
    # 构建响应数据列表，包含所有API相关字段
    supplier_responses = []
    for supplier in suppliers:
        # 创建响应字典，包含所有字段
        supplier_dict = {
            "id": supplier.id,
            "name": supplier.name,
            "display_name": supplier.display_name if supplier.display_name is not None else supplier.name,
            "description": supplier.description,
            "logo": supplier.logo,
            "website": supplier.website,
            "api_endpoint": supplier.api_endpoint,
            "api_key": supplier.api_key,  # 使用属性获取器，自动解密
            "api_key_required": supplier.api_key_required if supplier.api_key_required is not None else False,
            "category": supplier.category,
            "api_docs": supplier.api_docs,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at,
            "is_active": supplier.is_active if supplier.is_active is not None else True
        }
        supplier_responses.append(supplier_dict)
    
    return supplier_responses

# 将获取单个供应商的路由移到获取所有供应商路由之后
@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """获取单个供应商"""
    # 使用ORM模型查询，确保API密钥正确解密
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 转换为字典格式返回，包含所有API相关字段
    return {
        "id": supplier.id,
        "name": supplier.name,
        "display_name": supplier.display_name if supplier.display_name is not None else supplier.name,
        "description": supplier.description,
        "logo": supplier.logo,
        "website": supplier.website,
        "api_endpoint": supplier.api_endpoint,
        "api_key": supplier.api_key,  # 使用属性获取器，自动解密
        "api_key_required": supplier.api_key_required if supplier.api_key_required is not None else False,
        "category": supplier.category,
        "api_docs": supplier.api_docs,
        "created_at": supplier.created_at,
        "updated_at": supplier.updated_at,
        "is_active": supplier.is_active
    }

# 添加兼容性端点：/suppliers/all 作为 /suppliers-list 的别名
@router.get("/suppliers/all", response_model=List[SupplierResponse])
def get_all_suppliers_alias(db: Session = Depends(get_db)):
    """获取所有供应商（兼容性端点）"""
    return get_all_suppliers(db)

from sqlalchemy import text

@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    request: Request,
    name: str = Form(None),
    description: str = Form(None),
    website: str = Form(None),
    api_key: str = Form(None),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """更新供应商信息（支持文件上传和JSON格式）"""
    try:
        import logging
        logger = logging.getLogger()
        
        # 检查供应商是否存在 - 使用原始SQL查询避免ORM关系映射错误
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT id, name, display_name, description, logo, website, 
                   api_key_required, created_at, updated_at, is_active
            FROM suppliers 
            WHERE id = :supplier_id
        """), {"supplier_id": supplier_id})
        supplier_row = result.fetchone()
        if not supplier_row:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        # 将查询结果转换为字典格式
        supplier = {
            "id": supplier_row.id,
            "name": supplier_row.name,
            "display_name": supplier_row.display_name,
            "description": supplier_row.description,
            "logo": supplier_row.logo,
            "website": supplier_row.website,
            "api_key_required": supplier_row.api_key_required,
            "created_at": supplier_row.created_at,
            "updated_at": supplier_row.updated_at,
            "is_active": supplier_row.is_active
        }
        
        # 初始化更新数据
        update_data = {}
        
        # 获取Content-Type
        content_type = request.headers.get("Content-Type", "")
        logger.info(f"[更新供应商] Content-Type: {content_type}")
        logger.info(f"[更新供应商] 请求头: {dict(request.headers)}")
        
        # 处理JSON格式请求
        if "application/json" in content_type:
            # 解析JSON数据
            try:
                json_data = await request.json()
                update_data = json_data
                logger.info(f"[更新供应商] JSON数据: {update_data}")
                logger.info(f"[更新供应商] JSON数据类型: {type(update_data)}")
                logger.info(f"[更新供应商] JSON数据中是否包含api_key: {'api_key' in update_data}")
                if 'api_key' in update_data:
                    logger.info(f"[更新供应商] JSON数据中的api_key: {update_data['api_key']}")
            except Exception as e:
                logger.error(f"[更新供应商] 解析JSON数据失败: {str(e)}")
                raise HTTPException(status_code=400, detail="无效的JSON数据")
        # 处理FormData格式请求
        else:
            # 收集表单数据
            if name:
                update_data["name"] = name
            if description:
                update_data["description"] = description
            if website:
                update_data["website"] = website
            if api_key is not None:
                update_data["api_key"] = api_key
            logger.info(f"[更新供应商] Form数据: {update_data}")
            logger.info(f"[更新供应商] api_key表单参数: {api_key}")
        
        # 检查名称是否重复（如果更新了名称）
        if "name" in update_data and update_data["name"] != supplier["name"]:
            result = db.execute(text("""
                SELECT id FROM suppliers 
                WHERE name = :name AND id != :supplier_id
            """), {"name": update_data["name"], "supplier_id": supplier_id})
            existing_supplier = result.fetchone()
            if existing_supplier:
                raise HTTPException(status_code=400, detail="供应商名称已存在")
        
        # 保存新logo文件（如果有）
        if logo:
            logo_path = await save_upload_file(logo)
            update_data["logo"] = logo_path
        
        # 使用ORM模型更新供应商，确保API密钥自动加密
        supplier_obj = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
        if not supplier_obj:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        # 更新供应商字段
        for key, value in update_data.items():
            if value is not None:
                if hasattr(supplier_obj, key):
                    setattr(supplier_obj, key, value)
        
        # 设置更新时间
        supplier_obj.updated_at = datetime.utcnow()
        
        # 提交更改
        db.commit()
        db.refresh(supplier_obj)
        logger.info(f"[更新供应商] 更新成功")
        
        # 使用ORM模型获取更新后的供应商数据，确保API密钥正确解密
        updated_supplier_obj = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
        
        # 构建响应数据
        response_data = {
            "id": updated_supplier_obj.id,
            "name": updated_supplier_obj.name,
            "display_name": updated_supplier_obj.display_name,
            "description": updated_supplier_obj.description,
            "logo": updated_supplier_obj.logo,
            "website": updated_supplier_obj.website,
            "api_endpoint": updated_supplier_obj.api_endpoint,
            "api_key_required": updated_supplier_obj.api_key_required,
            "category": updated_supplier_obj.category,
            "api_docs": updated_supplier_obj.api_docs,
            "is_active": updated_supplier_obj.is_active,
            "created_at": updated_supplier_obj.created_at,
            "updated_at": updated_supplier_obj.updated_at,
            "api_key": updated_supplier_obj.api_key  # 使用属性获取器，自动解密
        }
        return response_data
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新供应商失败: {str(e)}")

@router.patch("/suppliers/{supplier_id}/status")
def update_supplier_status(supplier_id: int, is_active: bool, db: Session = Depends(get_db)):
    """更新供应商状态"""
    # 检查供应商是否存在 - 使用ORM模型查询
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 更新供应商状态
    supplier.is_active = is_active
    supplier.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(supplier)
    
    # 返回更新后的供应商信息，包含所有API相关字段
    return {
        "id": supplier.id,
        "name": supplier.name,
        "display_name": supplier.display_name,
        "description": supplier.description,
        "logo": supplier.logo,
        "website": supplier.website,
        "api_endpoint": supplier.api_endpoint,
        "api_key": supplier.api_key,  # 使用属性获取器，自动解密
        "api_key_required": supplier.api_key_required,
        "category": supplier.category,
        "api_docs": supplier.api_docs,
        "is_active": supplier.is_active,
        "created_at": supplier.created_at,
        "updated_at": supplier.updated_at
    }

@router.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """删除供应商"""
    # 检查供应商是否存在 - 使用原始SQL查询避免ORM关系映射错误
    from sqlalchemy import text
    result = db.execute(text("SELECT id FROM suppliers WHERE id = :supplier_id"), {
        "supplier_id": supplier_id
    })
    supplier = result.fetchone()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 检查是否有相关模型 - 使用原始SQL查询避免ORM关系映射错误
    result = db.execute(text("SELECT COUNT(*) as count FROM models WHERE supplier_id = :supplier_id"), {
        "supplier_id": supplier_id
    })
    model_count = result.fetchone().count
    if model_count > 0:
        raise HTTPException(
            status_code=400,
            detail="无法删除包含模型的供应商，请先删除相关模型"
        )
    
    # 删除供应商 - 使用原始SQL删除
    delete_sql = "DELETE FROM suppliers WHERE id = :supplier_id"
    db.execute(text(delete_sql), {"supplier_id": supplier_id})
    db.commit()
    
    return {"message": "供应商删除成功"}

# 模型相关路由
@router.get("/models", response_model=ModelListResponse)
def get_all_models(db: Session = Depends(get_db)):
    """获取所有模型（通用接口）"""
    try:
        import logging
        logger = logging.getLogger()
        # 获取所有模型，包括供应商信息
        from sqlalchemy.orm import joinedload
        from app.models.supplier_db import ModelDB
        
        models = db.query(ModelDB).options(joinedload(ModelDB.supplier)).all()
        total = len(models)
        
        # 转换为响应格式
        model_responses = []
        for model in models:
            # 创建ModelWithSupplierResponse对象
            model_response = ModelWithSupplierResponse(
                id=str(model.id),
                model_id=str(model.model_id) if model.model_id is not None else "",
                model_name=str(getattr(model, "model_name", model.model_id)) if getattr(model, "model_name", model.model_id) is not None else "",
                description=str(model.description) if model.description is not None else None,
                supplier_id=int(model.supplier_id),
                type=getattr(model, "type", "chat"),  # 添加type字段，默认为chat
                context_window=int(model.context_window) if model.context_window is not None else None,
                max_tokens=int(model.max_tokens) if model.max_tokens is not None else None,
                is_default=bool(model.is_default),
                is_active=bool(model.is_active),
                created_at=model.created_at if hasattr(model, 'created_at') else datetime.now(),  # 添加created_at字段
                supplier=ModelSupplierResponse(
                    id=model.supplier.id,
                    name=model.supplier.name,
                    display_name=model.supplier.display_name,
                    description=model.supplier.description,
                    is_active=model.supplier.is_active,
                    logo=model.supplier.logo,
                    api_endpoint=model.supplier.api_endpoint,
                    api_key_required=model.supplier.api_key_required,
                    category=model.supplier.category,
                    website=model.supplier.website,
                    api_docs=model.supplier.api_docs,
                    created_at=model.supplier.created_at,
                    updated_at=model.supplier.updated_at
                )
            )
            model_responses.append(model_response)
        
        return ModelListResponse(models=model_responses, total=total)
    except Exception as e:
        logger.error(f"获取所有模型失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取所有模型失败: {str(e)}"
        )

@router.get("/suppliers/{supplier_id}/models", response_model=ModelListResponse)
def get_supplier_models(supplier_id: int, db: Session = Depends(get_db)):
    """获取指定供应商的模型列表"""
    # 验证供应商是否存在
    from sqlalchemy import text, join, select
    from app.models.supplier_db import ModelDB, SupplierDB
    from app.models.model_category import ModelCategoryAssociation, ModelCategory
    
    # 获取供应商信息
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 使用ORM查询获取模型及其分类
    models = db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).all()
    
    if not models:
        return ModelListResponse(models=[], total=0)
    
    # 为每个模型获取分类
    model_responses = []
    for model in models:
        # 获取模型关联的所有分类
        categories = db.query(ModelCategory).join(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.model_id == model.id
        ).all()
        
        # 转换为响应格式
        model_response = ModelWithSupplierResponse(
            id=model.id,
            model_id=model.model_id,
            model_name=model.model_name,
            description=model.description,
            type="chat",  # 默认值，因为数据库中没有此字段
            context_window=model.context_window or 8000,
            default_temperature=0.7,
            default_max_tokens=model.max_tokens or 1000,
            default_top_p=1.0,
            default_frequency_penalty=0.0,
            default_presence_penalty=0.0,
            custom_params=None,
            is_active=model.is_active,
            is_default=model.is_default,
            logo=model.logo,
            supplier_id=model.supplier_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            categories=categories,
            supplier=SupplierResponse(
                id=supplier.id,
                name=supplier.name,
                display_name=supplier.display_name if supplier.display_name is not None else supplier.name,
                description=supplier.description,
                logo=supplier.logo,
                website=supplier.website,
                api_endpoint=supplier.api_endpoint,
                api_key_required=supplier.api_key_required if supplier.api_key_required is not None else False,
                category=supplier.category,
                api_docs=supplier.api_docs,
                created_at=supplier.created_at,
                updated_at=supplier.updated_at,
                is_active=supplier.is_active
            )
        )
        model_responses.append(model_response)
    
    return ModelListResponse(models=model_responses, total=len(model_responses))

@router.get("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
def get_model(supplier_id: int, model_id: int, db: Session = Depends(get_db)):
    """获取单个模型"""
    # 验证供应商是否存在 - 使用原始SQL查询避免ORM关系映射问题
    from sqlalchemy import text
    result = db.execute(text("SELECT id FROM suppliers WHERE id = :supplier_id"), {
        "supplier_id": supplier_id
    })
    supplier = result.fetchone()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取模型 - 使用原始SQL查询避免ORM关系映射错误
    result = db.execute(text("""
        SELECT id, model_id, model_name, description, supplier_id, 
               context_window, max_tokens, is_default, is_active
        FROM models 
        WHERE id = :model_id AND supplier_id = :supplier_id
    """), {"model_id": model_id, "supplier_id": supplier_id})
    model = result.fetchone()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 转换为ModelResponse格式
    return ModelResponse(
        id=model.id,
        model_id=model.model_id,
        model_name=model.model_name,
        description=model.description,
        supplier_id=model.supplier_id,
        context_window=model.context_window,
        max_tokens=model.max_tokens,
        is_default=model.is_default,
        is_active=model.is_active
    )

@router.post("/suppliers/{supplier_id}/models", response_model=ModelResponse, status_code=201)
def create_model(supplier_id: int, model: dict, db: Session = Depends(get_db)):
    """创建新模型"""
    # 验证供应商是否存在 - 使用原始SQL查询避免ORM关系映射错误
    from sqlalchemy import text
    result = db.execute(text("SELECT id FROM suppliers WHERE id = :supplier_id"), {
        "supplier_id": supplier_id
    })
    supplier = result.fetchone()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 检查模型ID是否已存在 - 使用原始SQL查询避免ORM关系映射错误
    result = db.execute(text("""
        SELECT id FROM models 
        WHERE model_id = :model_id AND supplier_id = :supplier_id
    """), {
        "model_id": model.get('model_id'),
        "supplier_id": supplier_id
    })
    existing_model = result.fetchone()
    if existing_model:
        raise HTTPException(status_code=400, detail="模型ID已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认 - 使用原始SQL更新
    if model.get('is_default'):
        db.execute(text("""
            UPDATE models SET is_default = false 
            WHERE supplier_id = :supplier_id
        """), {"supplier_id": supplier_id})
    
    # 创建新模型 - 使用原始SQL插入避免ORM关系映射错误
    now = datetime.utcnow()
    insert_sql = """
        INSERT INTO models (model_id, model_name, description, supplier_id, 
                           context_window, max_tokens, is_default, is_active, created_at, updated_at)
        VALUES (:model_id, :model_name, :description, :supplier_id, 
                :context_window, :max_tokens, :is_default, :is_active, :created_at, :updated_at)
        RETURNING id
    """
    result = db.execute(text(insert_sql), {
        "model_id": model.get('model_id'),
        "model_name": model.get('model_name'),
        "description": model.get('description'),
        "supplier_id": supplier_id,
        "context_window": model.get('context_window'),
        "max_tokens": model.get('max_tokens'),
        "is_default": model.get('is_default'),
        "is_active": model.get('is_active', True),
        "created_at": now,
        "updated_at": now
    })
    db.commit()
    
    # 获取新创建的模型ID
    new_model_id = result.fetchone()[0]
    
    # 查询新创建的模型信息
    select_sql = """
        SELECT id, model_id, model_name, description, supplier_id, 
               context_window, max_tokens, is_default, is_active
        FROM models WHERE id = :model_id
    """
    result = db.execute(text(select_sql), {"model_id": new_model_id})
    new_model = result.fetchone()
    
    # 转换为ModelResponse格式
    return ModelResponse(
        id=new_model.id,
        model_id=new_model.model_id,
        model_name=new_model.model_name,
        description=new_model.description,
        supplier_id=new_model.supplier_id,
        context_window=new_model.context_window,
        max_tokens=new_model.max_tokens,
        is_default=new_model.is_default,
        is_active=new_model.is_active
    )

@router.put("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
def update_model(supplier_id: int, model_id: int, model_update: dict, db: Session = Depends(get_db)):
    """更新模型信息"""
    # 验证供应商是否存在 - 使用原始SQL查询避免ORM关系映射错误
    from sqlalchemy import text
    result = db.execute(text("SELECT id FROM suppliers WHERE id = :supplier_id"), {
        "supplier_id": supplier_id
    })
    supplier = result.fetchone()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取模型 - 使用原始SQL查询避免ORM关系映射错误
    result = db.execute(text("""
        SELECT id, model_id, model_name, description, supplier_id, 
               context_window, max_tokens, is_default, is_active
        FROM models 
        WHERE id = :model_id AND supplier_id = :supplier_id
    """), {"model_id": model_id, "supplier_id": supplier_id})
    model = result.fetchone()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 检查模型ID是否被其他模型使用 - 使用原始SQL查询避免ORM关系映射错误
    update_model_id = model_update.get('model_id')
    if update_model_id is not None and update_model_id != model.model_id:
        result = db.execute(text("""
            SELECT id FROM models 
            WHERE model_id = :model_id AND supplier_id = :supplier_id AND id != :model_id
        """), {
            "model_id": update_model_id,
            "supplier_id": supplier_id,
            "model_id": model_id
        })
        existing_model = result.fetchone()
        if existing_model:
            raise HTTPException(status_code=400, detail="模型ID已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认 - 使用原始SQL更新
    if model_update.get('is_default'):
        db.execute(text("""
            UPDATE models SET is_default = false 
            WHERE supplier_id = :supplier_id
        """), {"supplier_id": supplier_id})
    
    # 构建SQL更新语句
    update_fields = []
    update_params = {"model_id": model_id, "supplier_id": supplier_id}
    
    # 处理更新字段
    for key, value in model_update.items():
        if value is not None:
            update_fields.append(f"{key} = :{key}")
            update_params[key] = value
    
    # 添加更新时间
    update_fields.append("updated_at = :updated_at")
    update_params["updated_at"] = datetime.utcnow()
    
    if update_fields:
        # 执行SQL更新
        update_sql = f"""
            UPDATE models 
            SET {', '.join(update_fields)}
            WHERE id = :model_id AND supplier_id = :supplier_id
        """
        db.execute(text(update_sql), update_params)
        db.commit()
    
    # 查询更新后的模型信息
    result = db.execute(text("""
        SELECT id, model_id, model_name, description, supplier_id, 
               context_window, max_tokens, is_default, is_active
        FROM models 
        WHERE id = :model_id AND supplier_id = :supplier_id
    """), {"model_id": model_id, "supplier_id": supplier_id})
    updated_model = result.fetchone()
    
    # 转换为ModelResponse格式
    return ModelResponse(
        id=updated_model.id,
        model_id=updated_model.model_id,
        model_name=updated_model.model_name,
        description=updated_model.description,
        supplier_id=updated_model.supplier_id,
        context_window=updated_model.context_window,
        max_tokens=updated_model.max_tokens,
        is_default=updated_model.is_default,
        is_active=updated_model.is_active
    )

@router.delete("/suppliers/{supplier_id}/models/{model_id}")
def delete_model(supplier_id: int, model_id: int, db: Session = Depends(get_db)):
    """
    删除模型
    """
    # 验证供应商是否存在 - 使用原始SQL查询避免ORM关系映射错误
    from sqlalchemy import text
    result = db.execute(text("SELECT id FROM suppliers WHERE id = :supplier_id"), {
        "supplier_id": supplier_id
    })
    supplier = result.fetchone()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取模型 - 使用原始SQL查询避免ORM关系映射错误
    result = db.execute(text("""
        SELECT id FROM models 
        WHERE id = :model_id AND supplier_id = :supplier_id
    """), {"model_id": model_id, "supplier_id": supplier_id})
    model = result.fetchone()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 删除模型 - 使用原始SQL删除
    delete_sql = "DELETE FROM models WHERE id = :model_id AND supplier_id = :supplier_id"
    db.execute(text(delete_sql), {"model_id": model_id, "supplier_id": supplier_id})
    db.commit()
    
    return {"message": "模型删除成功"}

@router.post("/suppliers/{supplier_id}/fetch-models")
async def fetch_models_from_api(supplier_id: int, api_config: dict, db: Session = Depends(get_db)):
    """
    从供应商API获取模型列表
    
    Args:
        supplier_id: 供应商ID
        api_config: API配置信息，包含api_endpoint和api_key
        db: 数据库会话
    
    Returns:
        获取的模型列表
    """
    import requests
    import logging
    # 使用根日志记录器
    logger = logging.getLogger()
    
    # 记录请求开始
    logger.info(f"[获取模型] 请求开始 - 供应商ID: {supplier_id}, API配置: {api_config}")
    
    # 验证供应商是否存在 - 使用原始SQL查询避免ORM关系映射错误
    from sqlalchemy import text
    result = db.execute(text("""
        SELECT id, api_endpoint FROM suppliers WHERE id = :supplier_id
    """), {"supplier_id": supplier_id})
    supplier = result.fetchone()
    if not supplier:
        logger.error(f"[获取模型] 供应商不存在 - 供应商ID: {supplier_id}")
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 提取API配置 - 优先使用前端传递的API端点，如果未提供则使用数据库中的
    api_endpoint = api_config.get("apiUrl") or supplier.api_endpoint
    # 使用前端传递的API密钥
    api_key = api_config.get("apiKey") or api_config.get("api_key")
    
    logger.info(f"[获取模型] 提取的API配置 - 端点: {api_endpoint}, 密钥长度: {len(api_key) if api_key else 0}")
    
    if not api_endpoint:
        logger.error(f"[获取模型] API端点为空 - 供应商ID: {supplier_id}")
        raise HTTPException(status_code=400, detail="API端点不能为空")
    
    try:
        # 根据供应商类型选择不同的获取模型方法
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else ""
        }
        
        models = []
        
        # 检查API端点类型，使用不同的获取方法
        if "siliconflow" in api_endpoint.lower():
            # 硅基流动API - 使用/models端点获取模型列表
            models_endpoint = api_endpoint.rstrip('/') + "/models"
            logger.info(f"[获取模型] 硅基流动API - 方法: GET, 端点: {models_endpoint}")
            response = requests.get(models_endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[获取模型] 硅基流动API响应: {data}")
                
                # 硅基流动返回格式：直接是模型数组
                if isinstance(data, list):
                    for model_data in data:
                        models.append({
                            "model_id": model_data.get("id"),
                            "model_name": model_data.get("id"),  # 使用id作为名称
                            "description": f"硅基流动模型: {model_data.get('id')}",
                            "context_window": 8000,
                            "max_tokens": 1000,
                            "is_default": False,
                            "is_active": True
                        })
                elif isinstance(data, dict) and "data" in data:
                    # 备用格式处理
                    for model_data in data["data"]:
                        models.append({
                            "model_id": model_data.get("id"),
                            "model_name": model_data.get("name", model_data.get("id")),
                            "description": model_data.get("description", ""),
                            "context_window": model_data.get("context_length", 8000),
                            "max_tokens": model_data.get("max_tokens", 1000),
                            "is_default": False,
                            "is_active": True
                        })
                else:
                    logger.warning(f"[获取模型] 硅基流动API返回格式未知: {type(data)}")
        elif "ollama" in api_endpoint.lower() or "localhost:11434" in api_endpoint.lower():
            # Ollama API - 使用/api/tags获取模型列表
            # 对于Ollama，API端点通常是基础URL，需要构建正确的模型列表端点
            base_url = api_endpoint.rstrip('/')
            # 如果端点已经是完整的API路径，需要去掉重复的/api部分
            if base_url.endswith('/api'):
                base_url = base_url[:-4]  # 去掉最后的/api
            models_endpoint = base_url.rstrip('/') + "/api/tags"
            logger.info(f"[获取模型] Ollama API - 方法: GET, 端点: {models_endpoint}")
            response = requests.get(models_endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "models" in data:
                    for model_data in data["models"]:
                        models.append({
                            "model_id": model_data.get("name"),
                            "model_name": model_data.get("name"),
                            "description": f"Ollama模型: {model_data.get('name')}",
                            "context_window": 8000,
                            "max_tokens": 1000,
                            "is_default": False,
                            "is_active": True
                        })
        elif "deepseek" in api_endpoint.lower():
            # DeepSeek API - 使用/models端点获取模型列表
            # 修复端点构建逻辑，避免重复的/v1路径
            base_url = api_endpoint.rstrip('/')
            if base_url.endswith('/v1'):
                base_url = base_url[:-3]  # 去掉最后的/v1
            models_endpoint = base_url.rstrip('/') + "/v1/models"
            logger.info(f"[获取模型] DeepSeek API - 方法: GET, 端点: {models_endpoint}")
            response = requests.get(models_endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    for model_data in data["data"]:
                        models.append({
                            "model_id": model_data.get("id"),
                            "model_name": model_data.get("name", model_data.get("id")),
                            "description": model_data.get("description", ""),
                            "context_window": model_data.get("context_window", 8000),
                            "max_tokens": model_data.get("max_tokens", 1000),
                            "is_default": False,
                            "is_active": True
                        })
        elif "dashscope" in api_endpoint.lower() or "aliyun" in api_endpoint.lower():
            # 阿里云百炼API - 使用/models端点获取模型列表
            # 阿里云百炼的模型列表端点通常是 /v1/models
            base_url = api_endpoint.rstrip('/')
            # 如果端点已经包含完整的路径，需要调整
            if base_url.endswith('/v1'):
                base_url = base_url[:-3]  # 去掉最后的/v1
            models_endpoint = base_url.rstrip('/') + "/v1/models"
            logger.info(f"[获取模型] 阿里云百炼API - 方法: GET, 端点: {models_endpoint}")
            
            # 阿里云百炼需要特定的认证头
            aliyun_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}" if api_key else "",
                "X-DashScope-Async": "enable"  # 阿里云特定的头
            }
            
            response = requests.get(models_endpoint, headers=aliyun_headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[获取模型] 阿里云百炼API响应: {data}")
                
                # 阿里云百炼返回格式：包含data数组
                if "data" in data and isinstance(data["data"], list):
                    for model_data in data["data"]:
                        models.append({
                            "model_id": model_data.get("model_id", model_data.get("id")),
                            "model_name": model_data.get("model_name", model_data.get("name", model_data.get("model_id"))),
                            "description": model_data.get("description", f"阿里云模型: {model_data.get('model_name', model_data.get('model_id'))}"),
                            "context_window": model_data.get("context_window", 8000),
                            "max_tokens": model_data.get("max_tokens", 1000),
                            "is_default": False,
                            "is_active": True
                        })
                else:
                    # 如果标准格式不匹配，尝试其他可能的格式
                    logger.warning(f"[获取模型] 阿里云百炼API返回格式未知，尝试备用解析: {type(data)}")
                    # 备用方案：返回一些常见的阿里云模型
                    common_aliyun_models = [
                        {
                            "model_id": "qwen-max",
                            "model_name": "通义千问Max",
                            "description": "阿里云通义千问Max模型，支持128K上下文",
                            "context_window": 128000,
                            "max_tokens": 4000,
                            "is_default": True,
                            "is_active": True
                        },
                        {
                            "model_id": "qwen-plus",
                            "model_name": "通义千问Plus",
                            "description": "阿里云通义千问Plus模型",
                            "context_window": 32000,
                            "max_tokens": 2000,
                            "is_default": False,
                            "is_active": True
                        },
                        {
                            "model_id": "qwen-turbo",
                            "model_name": "通义千问Turbo",
                            "description": "阿里云通义千问Turbo模型，响应速度快",
                            "context_window": 8000,
                            "max_tokens": 1500,
                            "is_default": False,
                            "is_active": True
                        }
                    ]
                    models.extend(common_aliyun_models)
        else:
            # 通用API - 尝试使用/models端点
            models_endpoint = api_endpoint.rstrip('/') + "/v1/models"
            logger.info(f"[获取模型] 通用API - 方法: GET, 端点: {models_endpoint}")
            response = requests.get(models_endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    for model_data in data["data"]:
                        models.append({
                            "model_id": model_data.get("id"),
                            "model_name": model_data.get("name", model_data.get("id")),
                            "description": model_data.get("description", ""),
                            "context_window": model_data.get("context_window", 8000),
                            "max_tokens": model_data.get("max_tokens", 1000),
                            "is_default": False,
                            "is_active": True
                        })
        
        logger.info(f"[获取模型] 获取成功 - 供应商ID: {supplier_id}, 获取到 {len(models)} 个模型")
        
        return {
            "status": "success",
            "message": f"成功获取 {len(models)} 个模型",
            "models": models,
            "total": len(models)
        }
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[获取模型] 连接错误 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 错误: {str(e)}")
        return {
            "status": "error",
            "message": "无法连接到API端点，请检查地址是否正确。",
            "models": [],
            "total": 0
        }
    except requests.exceptions.Timeout as e:
        logger.error(f"[获取模型] 请求超时 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 错误: {str(e)}")
        return {
            "status": "error",
            "message": "API请求超时，请检查网络连接或端点响应时间。",
            "models": [],
            "total": 0
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"[获取模型] 请求异常 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 错误: {str(e)}")
        return {
            "status": "error",
            "message": f"获取模型失败: {str(e)}",
            "models": [],
            "total": 0
        }
    except Exception as e:
        logger.error(f"[获取模型] 未知错误 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 错误: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"获取模型过程中发生错误: {str(e)}",
            "models": [],
            "total": 0
        }

@router.post("/suppliers/{supplier_id}/test-api")
async def test_api_config(supplier_id: int, api_config: dict, db: Session = Depends(get_db)):
    import requests
    import logging
    # 使用根日志记录器
    logger = logging.getLogger()
    
    # 记录请求开始
    logger.info(f"[API测试] 请求开始 - 供应商ID: {supplier_id}, API配置: {api_config}")
    
    # 验证供应商是否存在 - 使用原始SQL查询避免ORM关系映射错误
    from sqlalchemy import text
    result = db.execute(text("""
        SELECT id, api_endpoint FROM suppliers WHERE id = :supplier_id
    """), {"supplier_id": supplier_id})
    supplier = result.fetchone()
    if not supplier:
        logger.error(f"[API测试] 供应商不存在 - 供应商ID: {supplier_id}")
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 提取API配置 - 优先使用前端传递的API端点，如果未提供则使用数据库中的
    api_endpoint = api_config.get("apiUrl") or supplier.api_endpoint
    # 使用前端传递的API密钥
    api_key = api_config.get("apiKey") or api_config.get("api_key")
    
    logger.info(f"[API测试] 提取的API配置 - 端点: {api_endpoint}, 密钥长度: {len(api_key) if api_key else 0}")
    
    if not api_endpoint:
        logger.error(f"[API测试] API端点为空 - 供应商ID: {supplier_id}")
        raise HTTPException(status_code=400, detail="API端点不能为空")
    
    try:
        # 根据供应商类型选择不同的测试方法
        # 对于DeepSeek等需要特定端点的API，使用更智能的测试方法
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 检查API端点类型，如果是DeepSeek或硅基流动，使用特定的测试端点
        if "deepseek" in api_endpoint.lower():
            # DeepSeek API需要POST请求到/chat/completions
            # 如果API端点已经包含/v1，则直接使用/chat/completions
            if api_endpoint.endswith('/v1'):
                test_endpoint = api_endpoint.rstrip('/') + "/chat/completions"
            else:
                test_endpoint = api_endpoint.rstrip('/') + "/v1/chat/completions"
            test_payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, please respond with a short test message to confirm the API is working."
                    }
                ],
                "max_tokens": 50
            }
            logger.info(f"[API测试] DeepSeek API测试 - 方法: POST, 端点: {test_endpoint}")
            response = requests.post(test_endpoint, headers=headers, json=test_payload, timeout=10)
        elif "siliconflow" in api_endpoint.lower():
            # 硅基流动API需要POST请求到/chat/completions
            # 如果API端点已经包含/v1，则直接使用/chat/completions
            if api_endpoint.endswith('/v1'):
                test_endpoint = api_endpoint.rstrip('/') + "/chat/completions"
            else:
                test_endpoint = api_endpoint.rstrip('/') + "/v1/chat/completions"
            test_payload = {
                "model": "deepseek-ai/DeepSeek-V3.2",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, please respond with a short test message to confirm the API is working."
                    }
                ],
                "max_tokens": 50
            }
            logger.info(f"[API测试] 硅基流动API测试 - 方法: POST, 端点: {test_endpoint}")
            response = requests.post(test_endpoint, headers=headers, json=test_payload, timeout=10)
        elif "dashscope" in api_endpoint.lower() or "aliyun" in api_endpoint.lower():
            # 阿里云百炼API需要POST请求到特定的生成端点
            # 如果API端点已经包含完整的生成路径，则直接使用
            if "generation" in api_endpoint.lower():
                test_endpoint = api_endpoint
            else:
                # 否则使用标准的生成端点
                test_endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            
            test_payload = {
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "你好，请介绍一下你自己"
                        }
                    ]
                }
            }
            logger.info(f"[API测试] 阿里云百炼API测试 - 方法: POST, 端点: {test_endpoint}")
            response = requests.post(test_endpoint, headers=headers, json=test_payload, timeout=10)
        elif "ollama" in api_endpoint.lower() or "localhost:11434" in api_endpoint.lower():
            # Ollama API需要GET请求到/api/tags来获取模型列表
            test_endpoint = api_endpoint.rstrip('/') + "/tags"
            logger.info(f"[API测试] Ollama API测试 - 方法: GET, 端点: {test_endpoint}")
            response = requests.get(test_endpoint, headers=headers, timeout=10)
        else:
            # 其他API使用简单的GET请求测试
            logger.info(f"[API测试] 通用API测试 - 方法: GET, 端点: {api_endpoint}")
            response = requests.get(api_endpoint, headers=headers, timeout=10)
        
        logger.info(f"[API测试] 请求结果 - 状态码: {response.status_code}, 响应头: {response.headers}, 响应内容: {response.text[:200]}...")
        
        if response.status_code == 200:
            logger.info(f"[API测试] 测试成功 - 供应商ID: {supplier_id}, API端点: {api_endpoint}")
            return {
                "status": "success",
                "message": "API连接成功",
                "status_code": response.status_code,
                "response_text": response.text[:500]
            }
        else:
            logger.warning(f"[API测试] 测试失败 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 状态码: {response.status_code}")
            return {
                "status": "error",
                "message": f"API连接失败，状态码: {response.status_code}",
                "status_code": response.status_code,
                "response_text": response.text
            }
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[API测试] 连接错误 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 错误: {str(e)}")
        return {
            "status": "error",
            "message": f"无法连接到API端点，请检查地址是否正确。",
            "status_code": 0,
            "response_text": str(e)
        }
    except requests.exceptions.Timeout as e:
        logger.error(f"[API测试] 请求超时 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 错误: {str(e)}")
        return {
            "status": "error",
            "message": f"API请求超时，请检查网络连接或端点响应时间。",
            "status_code": 0,
            "response_text": str(e)
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"[API测试] 请求异常 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 错误: {str(e)}")
        return {
            "status": "error",
            "message": f"API连接失败: {str(e)}",
            "status_code": 0,
            "response_text": str(e)
        }
    except Exception as e:
        logger.error(f"[API测试] 未知错误 - 供应商ID: {supplier_id}, API端点: {api_endpoint}, 错误: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"测试过程中发生错误: {str(e)}",
            "status_code": 0,
            "response_text": str(e)
        }


# 基于场景的模型查询API
@router.get("/models/by-scene/{scene}")
def get_models_by_scene(
    scene: str,
    include_match_score: bool = Query(False, description="是否包含能力匹配度评分"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    根据场景获取符合条件的模型列表
    
    Args:
        scene: 场景名称（chat、translate等）
        include_match_score: 是否包含能力匹配度评分
        db: 数据库会话
        
    Returns:
        包含模型列表和匹配度信息的响应
    """
    try:
        # 创建能力筛选器
        filter_service = CapabilityBasedModelFilter(db)
        
        # 获取可用的场景列表
        available_scenes = filter_service.get_available_scenes()
        
        if scene not in available_scenes:
            return {
                "status": "error",
                "message": f"场景 '{scene}' 不支持。支持的场景: {', '.join(available_scenes)}",
                "available_scenes": available_scenes
            }
        
        if include_match_score:
            # 包含匹配度评分
            models_with_scores = filter_service.get_models_with_capability_scores(scene)
            
            # 转换为前端友好的格式，包含完整的供应商信息
            result_models = []
            for item in models_with_scores:
                model = item["model"]
                # 获取供应商信息
                supplier = db.query(SupplierDB).filter(SupplierDB.id == model.supplier_id).first()
                
                result_models.append({
                    "id": model.id,
                    "model_id": model.model_id,
                    "model_name": model.model_name,
                    "description": model.description,
                    "supplier_id": model.supplier_id,
                    "supplier": {
                        "id": supplier.id if supplier else None,
                        "name": supplier.name if supplier else "未知供应商",
                        "display_name": supplier.display_name if supplier else None,
                        "logo": supplier.logo if supplier else None
                    },
                    "context_window": model.context_window,
                    "max_tokens": model.max_tokens,
                    "is_default": model.is_default,
                    "is_active": model.is_active,
                    "match_score": item["match_score"],
                    "match_percentage": item["match_percentage"],
                    "satisfied_requirements": item["satisfied_requirements"]
                })
            
            return {
                "status": "success",
                "message": f"成功获取 {len(result_models)} 个模型",
                "scene": scene,
                "models": result_models,
                "total": len(result_models)
            }
        else:
            # 仅返回模型列表
            models = filter_service.get_models_for_scene(scene)
            
            # 转换为前端友好的格式，包含完整的供应商信息
            result_models = []
            for model in models:
                # 获取供应商信息
                supplier = db.query(SupplierDB).filter(SupplierDB.id == model.supplier_id).first()
                
                result_models.append({
                    "id": model.id,
                    "model_id": model.model_id,
                    "model_name": model.model_name,
                    "description": model.description,
                    "supplier_id": model.supplier_id,
                    "supplier": {
                        "id": supplier.id if supplier else None,
                        "name": supplier.name if supplier else "未知供应商",
                        "display_name": supplier.display_name if supplier else None,
                        "logo": supplier.logo if supplier else None
                    },
                    "context_window": model.context_window,
                    "max_tokens": model.max_tokens,
                    "is_default": model.is_default,
                    "is_active": model.is_active
                })
            
            return {
                "status": "success",
                "message": f"成功获取 {len(result_models)} 个模型",
                "scene": scene,
                "models": result_models,
                "total": len(result_models)
            }
    
    except Exception as e:
        import logging
        logger = logging.getLogger()
        logger.error(f"[场景模型查询] 错误 - 场景: {scene}, 错误: {str(e)}", exc_info=True)
        
        return {
            "status": "error",
            "message": f"查询模型失败: {str(e)}",
            "scene": scene,
            "models": [],
            "total": 0
        }


@router.get("/models/available-scenes")
def get_available_scenes(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    获取所有可用的场景列表
    
    Args:
        db: 数据库会话
        
    Returns:
        包含可用场景列表的响应
    """
    try:
        filter_service = CapabilityBasedModelFilter(db)
        available_scenes = filter_service.get_available_scenes()
        
        return {
            "status": "success",
            "message": f"成功获取 {len(available_scenes)} 个可用场景",
            "available_scenes": available_scenes
        }
    
    except Exception as e:
        import logging
        logger = logging.getLogger()
        logger.error(f"[获取可用场景] 错误: {str(e)}", exc_info=True)
        
        return {
            "status": "error",
            "message": f"获取可用场景失败: {str(e)}",
            "available_scenes": []
        }


@router.get("/models/{model_id}/capability-scores/{scene}")
def get_model_capability_scores(
    model_id: int,
    scene: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定模型在特定场景下的能力匹配度评分
    
    Args:
        model_id: 模型ID
        scene: 场景名称
        db: 数据库会话
        
    Returns:
        包含能力匹配度评分的响应
    """
    try:
        filter_service = CapabilityBasedModelFilter(db)
        
        # 获取模型
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            return {
                "status": "error",
                "message": f"模型 ID {model_id} 不存在",
                "score": 0.0
            }
        
        # 计算模型在指定场景下的能力匹配度
        score = filter_service.calculate_capability_score(model, scene)
        
        return {
            "status": "success",
            "message": f"成功获取模型 {model.model_name} 在场景 {scene} 的能力匹配度",
            "score": score,
            "model_id": model_id,
            "model_name": model.model_name,
            "scene": scene
        }
    
    except Exception as e:
        import logging
        logger = logging.getLogger()
        logger.error(f"[获取模型能力评分] 错误: {str(e)}", exc_info=True)
        
        return {
            "status": "error",
            "message": f"获取模型能力评分失败: {str(e)}",
            "score": 0.0
        }
