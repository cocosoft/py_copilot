"""供应商和模型相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import aiofiles

from app.core.dependencies import get_db
from app.models.model_management import ModelSupplier as SupplierDB, Model as ModelDB
from app.modules.supplier_model_management.schemas.supplier_model import (
    SupplierCreate, SupplierResponse,
    ModelCreate, ModelResponse, ModelListResponse
)

router = APIRouter()

# 文件上传配置
UPLOAD_DIR = "../../frontend/public/logos/providers"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg"}

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 如果更新name，检查是否已存在
    if name != supplier.name:
        existing_supplier = db.query(SupplierDB).filter(SupplierDB.name == name).first()
        if existing_supplier:
            raise HTTPException(status_code=400, detail="供应商名称已存在")
    
    # 保存新logo文件（如果有）
    update_data = {}
    if logo:
        logo_path = await save_upload_file(logo)
        update_data["logo"] = logo_path
    
    # 更新基础信息字段
    update_data.update({
        "name": name,
        "description": description,
        "website": website,
        "updated_at": datetime.utcnow()
    })
    
    db.query(SupplierDB).filter(SupplierDB.id == supplier_id).update(update_data)
    
    db.commit()
    db.refresh(supplier)
    
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
    
    db.delete(supplier)
    db.commit()
    
    return {"message": "供应商删除成功"}

# 模型相关路由
@router.get("/suppliers/{supplier_id}/models", response_model=ModelListResponse)
def get_supplier_models(supplier_id: int, db: Session = Depends(get_db)):
    """获取指定供应商的模型列表"""
    # 验证供应商是否存在
    from app.models.model_management import ModelSupplier, Model
    supplier = db.query(ModelSupplier).filter(ModelSupplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取该供应商的所有模型
    models = db.query(Model).filter(Model.supplier_id == supplier_id).all()
    total = len(models)
    
    # 转换为响应格式
    model_responses = [
        ModelResponse(
            id=str(model.id),
            name=str(model.name) if model.name is not None else "",
            display_name=str(getattr(model, "display_name", model.name)) if getattr(model, "display_name", model.name) is not None else "",
            description=str(model.description) if model.description is not None else None,
            supplier_id=int(model.supplier_id),
            context_window=int(model.context_window) if model.context_window is not None else None,
            max_tokens=int(getattr(model, "max_tokens", model.default_max_tokens)) if getattr(model, "max_tokens", model.default_max_tokens) is not None else None,
            is_default=bool(model.is_default),
            is_active=bool(model.is_active)
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
def create_model(supplier_id: int, model: ModelCreate, db: Session = Depends(get_db)):
    """创建新模型"""
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 检查模型名称是否已存在
    existing_model = db.query(ModelDB).filter(
        ModelDB.name == model.name,
        ModelDB.supplier_id == supplier_id
    ).first()
    if existing_model:
        raise HTTPException(status_code=400, detail="模型名称已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认
    if model.is_default:
        db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).update({"is_default": False})
    
    # 创建新模型
    # 只使用ModelDB中定义的字段
    db_model_data = {
        "name": model.name,
        "display_name": getattr(model, 'display_name', None),
        "description": getattr(model, 'description', None),
        "supplier_id": supplier_id,
        "context_window": getattr(model, 'context_window', None),
        "max_tokens": getattr(model, 'max_tokens', None),
        "is_default": model.is_default,
        "is_active": getattr(model, 'is_active', True)
    }
    db_model = ModelDB(**db_model_data)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model

@router.put("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
def update_model(supplier_id: int, model_id: int, model_update: ModelCreate, db: Session = Depends(get_db)):
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
    if model_update.name != model.name:
        existing_model = db.query(ModelDB).filter(
            ModelDB.name == model_update.name,
            ModelDB.supplier_id == supplier_id,
            ModelDB.id != model_id
        ).first()
        if existing_model:
            raise HTTPException(status_code=400, detail="模型名称已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认
    if model_update.is_default:
        db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).update({"is_default": False})
    
    # 更新模型数据
    update_data = model_update.dict(exclude_unset=True)
    for key, value in update_data.items():
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
