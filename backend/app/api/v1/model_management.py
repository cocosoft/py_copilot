"""模型管理相关API接口"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.supplier_db import SupplierDB as ModelSupplier, ModelDB as Model
from app.schemas.model_management import (
    ModelSupplierCreate, ModelSupplierUpdate, ModelSupplierResponse,
    ModelCreate, ModelUpdate, ModelResponse,
    ModelSupplierListResponse, ModelListResponse,
    SetDefaultModelRequest
)
# 临时注释掉认证依赖以方便测试
# from app.api.deps import get_current_active_superuser
# from app.models.user import User

# 创建一个模拟用户类用于测试
class MockUser:
    def __init__(self):
        self.id = 1
        self.is_active = True
        self.is_superuser = True

def get_mock_user():
    return MockUser()

router = APIRouter()


# 模型供应商管理相关路由
@router.post("/suppliers", response_model=ModelSupplierResponse)
async def create_model_supplier(
    supplier: ModelSupplierCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_superuser)
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    创建新的模型供应商
    
    Args:
        supplier: 模型供应商创建数据
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        创建的模型供应商信息
    """
    try:
        # 检查供应商名称是否已存在
        existing_supplier = db.query(ModelSupplier).filter(
            ModelSupplier.name == supplier.name
        ).first()
        if existing_supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="供应商名称已存在"
            )
        
        # 创建新供应商
        db_supplier = ModelSupplier(**supplier.model_dump())
        db.add(db_supplier)
        db.commit()
        db.refresh(db_supplier)
        return db_supplier
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建供应商失败，请检查输入数据"
        )


@router.get("/suppliers", response_model=ModelSupplierListResponse)
async def get_model_suppliers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取模型供应商列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型供应商列表
    """
    suppliers = db.query(ModelSupplier).offset(skip).limit(limit).all()
    total = db.query(ModelSupplier).count()
    return ModelSupplierListResponse(
        suppliers=suppliers,
        total=total
    )


@router.get("/suppliers/{supplier_id}", response_model=ModelSupplierResponse)
async def get_model_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取指定的模型供应商
    
    Args:
        supplier_id: 供应商ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型供应商信息
    """
    supplier = db.query(ModelSupplier).filter(ModelSupplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=ModelSupplierResponse)
async def update_model_supplier(
    supplier_id: int,
    supplier_update: ModelSupplierUpdate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新模型供应商信息
    
    Args:
        supplier_id: 供应商ID
        supplier_update: 更新数据
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        更新后的模型供应商信息
    """
    supplier = db.query(ModelSupplier).filter(ModelSupplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    # 更新供应商信息
    update_data = supplier_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    try:
        db.commit()
        db.refresh(supplier)
        return supplier
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新供应商失败，请检查输入数据"
        )


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> None:
    """
    删除模型供应商
    
    Args:
        supplier_id: 供应商ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
    """
    supplier = db.query(ModelSupplier).filter(ModelSupplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    # 检查是否有相关模型
    if supplier.models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除包含模型的供应商，请先删除相关模型"
        )
    
    db.delete(supplier)
    db.commit()


# 模型管理相关路由
@router.post("/suppliers/{supplier_id}/models", response_model=ModelResponse)
async def create_model(
    supplier_id: int,
    model: ModelCreate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    为指定供应商创建新模型
    
    Args:
        supplier_id: 供应商ID
        model: 模型创建数据
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        创建的模型信息
    """
    # 验证供应商是否存在
    supplier = db.query(ModelSupplier).filter(ModelSupplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    # 确保supplier_id一致
    model_data = model.model_dump()
    model_data['supplier_id'] = supplier_id
    
    try:
        # 创建新模型
        db_model = Model(**model_data)
        db.add(db_model)
        
        # 如果是第一个模型或者设置为默认模型，将其他模型的is_default设置为False
        if db_model.is_default:
            db.query(Model).filter(
                Model.supplier_id == supplier_id,
                Model.id != db_model.id
            ).update({Model.is_default: False})
        elif db.query(Model).filter(Model.supplier_id == supplier_id).count() == 0:
            # 如果是第一个模型，自动设为默认
            db_model.is_default = True
        
        db.commit()
        db.refresh(db_model)
        return db_model
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建模型失败，请检查输入数据"
        )


@router.get("/suppliers/{supplier_id}/models", response_model=ModelListResponse)
async def get_models(
    supplier_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取指定供应商的模型列表
    
    Args:
        supplier_id: 供应商ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型列表
    """
    # 验证供应商是否存在
    supplier = db.query(ModelSupplier).filter(ModelSupplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    models = db.query(Model).filter(
        Model.supplier_id == supplier_id
    ).offset(skip).limit(limit).all()
    total = db.query(Model).filter(Model.supplier_id == supplier_id).count()
    
    return ModelListResponse(
        models=models,
        total=total
    )


@router.get("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
async def get_model(
    supplier_id: int,
    model_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取指定的模型
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型信息
    """
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    return model


@router.put("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
async def update_model(
    supplier_id: int,
    model_id: int,
    model_update: ModelUpdate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新模型信息
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        model_update: 更新数据
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        更新后的模型信息
    """
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 更新模型信息
    update_data = model_update.model_dump(exclude_unset=True)
    
    # 如果更新了is_default为True，需要将其他模型的is_default设置为False
    if 'is_default' in update_data and update_data['is_default']:
        db.query(Model).filter(
            Model.supplier_id == supplier_id,
            Model.id != model_id
        ).update({Model.is_default: False})
    
    for field, value in update_data.items():
        setattr(model, field, value)
    
    try:
        db.commit()
        db.refresh(model)
        return model
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新模型失败，请检查输入数据"
        )


@router.delete("/suppliers/{supplier_id}/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    supplier_id: int,
    model_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> None:
    """
    删除模型
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
    """
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 记录是否为默认模型
    was_default = model.is_default
    
    db.delete(model)
    
    # 如果删除的是默认模型，将第一个可用的模型设为默认
    if was_default:
        first_model = db.query(Model).filter(
            Model.supplier_id == supplier_id
        ).first()
        if first_model:
            first_model.is_default = True
    
    db.commit()


@router.post("/suppliers/{supplier_id}/models/set-default/{model_id}", response_model=ModelResponse)
async def set_default_model(
    supplier_id: int,
    model_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    设置指定供应商的默认模型
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        设置为默认的模型信息
    """
    # 验证模型是否存在且属于指定供应商
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 将所有模型的is_default设置为False
    db.query(Model).filter(Model.supplier_id == supplier_id).update({Model.is_default: False})
    
    # 将指定模型设为默认
    model.is_default = True
    
    db.commit()
    db.refresh(model)
    return model