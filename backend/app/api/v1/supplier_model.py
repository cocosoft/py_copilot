"""供应商和模型相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import aiofiles

from app.core.dependencies import get_db
from app.models.supplier_db import SupplierDB, ModelDB
from app.schemas.supplier_model import (
    SupplierCreate, SupplierResponse,
    ModelCreate, ModelResponse, ModelListResponse
)

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
@router.get("/suppliers/{supplier_id}/models", response_model=ModelListResponse)
def get_supplier_models(supplier_id: int, db: Session = Depends(get_db)):
    """获取指定供应商的模型列表"""
    # 验证供应商是否存在 - 使用原始SQL查询避免ORM关系映射问题
    from sqlalchemy import text
    result = db.execute(text("SELECT id FROM suppliers WHERE id = :supplier_id"), {
        "supplier_id": supplier_id
    })
    supplier = result.fetchone()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取该供应商的所有模型 - 使用原始SQL查询避免ORM关系映射错误
    result = db.execute(text("""
        SELECT id, model_id, model_name, description, supplier_id, 
               context_window, max_tokens, is_default, is_active
        FROM models 
        WHERE supplier_id = :supplier_id
    """), {"supplier_id": supplier_id})
    models = result.fetchall()
    total = len(models)
    
    # 转换为响应格式
    model_responses = [
        ModelResponse(
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
        for model in models
    ]
    
    return ModelListResponse(models=model_responses, total=total)

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

@router.post("/suppliers/{supplier_id}/test-api")
async def test_api_config(supplier_id: int, api_config: dict, db: Session = Depends(get_db)):
    """
    测试供应商的API配置
    
    Args:
        supplier_id: 供应商ID
        api_config: API配置信息，包含api_endpoint和api_key
        db: 数据库会话
    
    Returns:
        测试结果
    """
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
