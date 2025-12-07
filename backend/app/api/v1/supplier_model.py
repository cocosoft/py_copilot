"""供应商和模型相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import aiofiles

from app.api.dependencies import get_db
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
    # 检查name是否已存在
    existing_supplier = db.query(SupplierDB).filter(SupplierDB.name == name).first()
    if existing_supplier:
        raise HTTPException(status_code=400, detail="供应商名称已存在")
    
    # 保存logo文件（如果有）
    logo_path = None
    if logo:
        logo_path = await save_upload_file(logo)
    
    # 创建新供应商
    now = datetime.utcnow()
    db_supplier = SupplierDB(
        name=name,
        description=description,
        logo=logo_path,
        website=website,
        created_at=now,
        updated_at=now
    )
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    
    # 返回供应商信息
    return {
        "id": db_supplier.id,
        "name": db_supplier.name,
        "description": db_supplier.description,
        "logo": db_supplier.logo,
        "website": db_supplier.website,
        "created_at": db_supplier.created_at,
        "updated_at": db_supplier.updated_at,
        "is_active": db_supplier.is_active
    }

# 供应商相关路由
@router.get("/suppliers/all", response_model=List[SupplierResponse])
def get_all_suppliers(db: Session = Depends(get_db)):
    """获取所有供应商"""
    return db.query(SupplierDB).all()

@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """获取单个供应商"""
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return supplier

from sqlalchemy import text

@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    name: str = Form(...),
    description: str = Form(...),
    website: str = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """更新供应商信息（支持文件上传）"""
    try:
        # 检查供应商是否存在
        result = db.execute(text("SELECT id FROM suppliers WHERE id = :supplier_id"), {
            "supplier_id": supplier_id
        })
        if result.fetchone() is None:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        # 如果更新name，检查是否已存在
        result = db.execute(text("SELECT id FROM suppliers WHERE name = :name AND id != :supplier_id"), {
            "name": name,
            "supplier_id": supplier_id
        })
        if result.fetchone() is not None:
            raise HTTPException(status_code=400, detail="供应商名称已存在")
        
        # 保存新logo文件（如果有）
        logo_path = None
        if logo:
            logo_path = await save_upload_file(logo)
        
        # 更新基础信息字段
        update_data = {
            "name": name,
            "description": description,
            "website": website,
            "updated_at": datetime.utcnow()
        }
        
        # 如果有logo更新，添加到更新数据
        if logo_path:
            update_data["logo"] = logo_path
        
        # 构建更新SQL
        set_clause = ", ".join([f"{key} = :{key}" for key in update_data.keys()])
        update_query = text(f"UPDATE suppliers SET {set_clause} WHERE id = :supplier_id")
        
        # 执行更新
        db.execute(update_query, {**update_data, "supplier_id": supplier_id})
        
        # 查询更新后的供应商信息
        result = db.execute(text("""
            SELECT id, name, description, logo, website, created_at, updated_at, is_active
            FROM suppliers WHERE id = :supplier_id
        """), {"supplier_id": supplier_id})
        supplier = result.fetchone()
        
        db.commit()
        
        # 检查供应商是否存在
        if supplier is None:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        # 返回供应商信息
        return {
            "id": supplier.id,
            "name": supplier.name,
            "description": supplier.description,
            "logo": supplier.logo,
            "website": supplier.website,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at,
            "is_active": supplier.is_active
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新供应商失败: {str(e)}")

@router.patch("/suppliers/{supplier_id}/status")
def update_supplier_status(supplier_id: int, is_active: bool, db: Session = Depends(get_db)):
    """更新供应商状态"""
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 更新供应商状态
    db.query(SupplierDB).filter(SupplierDB.id == supplier_id).update({
        "is_active": is_active,
        "updated_at": datetime.utcnow()
    })
    
    db.commit()
    db.refresh(supplier)
    
    return supplier

@router.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """删除供应商"""
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 检查是否有相关模型
    model_count = db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).count()
    if model_count > 0:
        raise HTTPException(
            status_code=400,
            detail="无法删除包含模型的供应商，请先删除相关模型"
        )
    
    db.delete(supplier)
    db.commit()
    
    return {"message": "供应商删除成功"}

# 模型相关路由
@router.get("/suppliers/{supplier_id}/models", response_model=ModelListResponse)
def get_supplier_models(supplier_id: int, db: Session = Depends(get_db)):
    """获取指定供应商的模型列表"""
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取该供应商的所有模型
    models = db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).all()
    total = len(models)
    
    # 转换为响应格式
    model_responses = [
        ModelResponse(
            id=model.id,
            name=model.name,
            display_name=getattr(model, "display_name", model.name),
            description=getattr(model, "description", None),
            supplier_id=model.supplier_id,
            context_window=getattr(model, "context_window", None),
            max_tokens=getattr(model, "max_tokens", getattr(model, "default_max_tokens", None)),
            is_default=model.is_default,
            is_active=model.is_active
        )
        for model in models
    ]
    
    return ModelListResponse(models=model_responses, total=total)

@router.get("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
def get_model(supplier_id: int, model_id: int, db: Session = Depends(get_db)):
    """获取单个模型"""
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取模型
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    return model

@router.post("/suppliers/{supplier_id}/models", response_model=ModelResponse, status_code=201)
def create_model(supplier_id: int, model: dict, db: Session = Depends(get_db)):
    """创建新模型"""
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 检查模型名称是否已存在
    existing_model = db.query(ModelDB).filter(
        ModelDB.name == model.get('name'),
        ModelDB.supplier_id == supplier_id
    ).first()
    if existing_model:
        raise HTTPException(status_code=400, detail="模型名称已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认
    if model.get('is_default'):
        db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).update({"is_default": False})
    
    # 创建新模型
    # 只使用ModelDB中定义的字段
    db_model_data = {
        "name": model.get('name'),
        "display_name": model.get('display_name'),
        "description": model.get('description'),
        "supplier_id": supplier_id,
        "context_window": model.get('context_window'),
        "max_tokens": model.get('max_tokens'),
        "is_default": model.get('is_default'),
        "is_active": model.get('is_active', True)
    }
    db_model = ModelDB(**db_model_data)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model

@router.put("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
def update_model(supplier_id: int, model_id: int, model_update: dict, db: Session = Depends(get_db)):
    """更新模型信息"""
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取模型
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 检查模型名称是否被其他模型使用
    update_name = model_update.get('name')
    if update_name is not None and update_name != model.name:
        existing_model = db.query(ModelDB).filter(
            ModelDB.name == update_name,
            ModelDB.supplier_id == supplier_id,
            ModelDB.id != model_id
        ).first()
        if existing_model:
            raise HTTPException(status_code=400, detail="模型名称已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认
    if model_update.get('is_default'):
        db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).update({"is_default": False})
    
    # 更新模型数据
    for key, value in model_update.items():
        setattr(model, key, value)
    
    # 移除时间戳更新，因为ModelDB不包含此字段
    
    db.commit()
    db.refresh(model)
    
    return model

@router.delete("/suppliers/{supplier_id}/models/{model_id}")
def delete_model(supplier_id: int, model_id: int, db: Session = Depends(get_db)):
    """删除模型"""
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取模型
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    db.delete(model)
    db.commit()
    
    return {"message": "模型删除成功"}
