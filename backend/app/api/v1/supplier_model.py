"""供应商和模型相关的API路由"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.dependencies import get_db
from app.models.supplier_db import SupplierDB, ModelDB
from app.schemas.supplier_model import (
    SupplierCreate, SupplierResponse,
    ModelCreate, ModelResponse, ModelListResponse
)

router = APIRouter()

# 供应商相关路由
@router.post("/suppliers", response_model=SupplierResponse)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    """创建新的供应商"""
    # 检查name是否已存在
    existing_supplier = db.query(SupplierDB).filter(SupplierDB.name == supplier.name).first()
    if existing_supplier:
        raise HTTPException(status_code=400, detail="供应商名称已存在")
    
    # 创建新供应商，添加时间戳
    now = datetime.utcnow().isoformat()
    db_supplier = SupplierDB(
        **supplier.dict(),
        created_at=now,
        updated_at=now
    )
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    
    return db_supplier

@router.get("/suppliers", response_model=List[SupplierResponse])
def get_suppliers(db: Session = Depends(get_db)):
    """获取所有供应商"""
    return db.query(SupplierDB).all()

@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """获取单个供应商"""
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return supplier

@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: int, supplier_update: SupplierCreate, db: Session = Depends(get_db)):
    """更新供应商信息"""
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 如果更新name，检查是否已存在
    if supplier_update.name is not None and supplier_update.name != supplier.name:
        existing_supplier = db.query(SupplierDB).filter(SupplierDB.name == supplier_update.name).first()
        if existing_supplier:
            raise HTTPException(status_code=400, detail="供应商名称已存在")
    
    # 更新供应商数据
    update_data = supplier_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(supplier, key, value)
    
    # 更新时间戳
    supplier.updated_at = datetime.utcnow().isoformat()
    
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
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 获取该供应商的所有模型
    models = db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).all()
    total = len(models)
    
    # 转换为响应格式
    model_responses = [
        {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "description": model.description,
            "supplier_id": model.supplier_id,
            "context_window": model.context_window,
            "max_tokens": model.max_tokens,
            "is_default": model.is_default,
            "is_active": model.is_active
        }
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
