"""模型管理相关API接口"""
from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.supplier_db import SupplierDB, ModelDB as Model

# 从core导入数据库依赖
from app.core.dependencies import get_db
from app.modules.supplier_model_management.schemas.model_management import (
    ModelSupplierCreate, ModelSupplierUpdate, ModelSupplierResponse,
    ModelCreate, ModelUpdate, ModelResponse,
    ModelSupplierListResponse, ModelListResponse,
    SetDefaultModelRequest
)

# 创建上传目录
# 使用绝对路径确保文件能正确保存
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "../frontend/public/logos/providers")
UPLOAD_DIR = os.path.normpath(UPLOAD_DIR)  # 规范化路径
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"文件上传目录: {UPLOAD_DIR}")  # 添加日志以便调试

# 支持的图片扩展名
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# 模拟用户相关定义已在其他地方声明

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def save_upload_file(upload_file: UploadFile) -> Optional[str]:
    """保存上传的文件并返回文件名"""
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
        print(f"尝试保存文件到: {file_path}")  # 添加日志
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
        print(f"文件保存成功: {unique_filename}")  # 添加成功日志
        # 返回文件名
        return unique_filename
    except Exception as e:
        print(f"文件保存失败: {str(e)}")  # 添加错误日志
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
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
@router.post("/suppliers")
async def create_model_supplier(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    api_endpoint: Optional[str] = Form(None),
    api_key_required: Optional[bool] = Form(False),
    is_active: bool = Form(True),
    logo: Optional[UploadFile] = File(None),
    category: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    api_docs: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    创建新的模型供应商（支持图片上传）
    
    Args:
        name: 供应商名称
        description: 供应商描述
        api_endpoint: API端点
        api_key_required: 是否需要API密钥
        is_active: 是否激活
        logo: 供应商logo图片
        category: 供应商类别
        website: 供应商网站
        api_docs: API文档链接
        api_key: API密钥
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        创建的模型供应商信息
    """
    try:
        # 检查供应商名称是否已存在
        existing_supplier = db.query(SupplierDB).filter(
        SupplierDB.name == name
        ).first()
        if existing_supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="供应商名称已存在"
            )
        
        # 处理logo上传
        logo_url = None
        if logo:
            logo_url = await save_upload_file(logo)
        
        # 创建新供应商
        now = datetime.utcnow()
        db_supplier = SupplierDB(
            name=name,
            description=description,
            api_endpoint=api_endpoint,
            api_key_required=api_key_required,
            is_active=is_active,
            logo=logo_url,
            category=category,
            website=website,
            api_docs=api_docs,
            api_key=api_key,
            created_at=now,
            updated_at=now
        )
        
        db.add(db_supplier)
        db.commit()
        db.refresh(db_supplier)
        
        # 返回响应 - 使用name作为display_name
        return {
            "id": db_supplier.id,
            "name": db_supplier.name,
            "display_name": db_supplier.name,  # 使用name作为display_name
            "description": db_supplier.description,
            "api_endpoint": db_supplier.api_endpoint,
            "api_key_required": db_supplier.api_key_required,
            "is_active": db_supplier.is_active,
            "logo": db_supplier.logo,
            "category": db_supplier.category,
            "website": db_supplier.website,
            "api_docs": db_supplier.api_docs,
            "api_key": db_supplier.api_key,
            "created_at": db_supplier.created_at,
            "updated_at": db_supplier.updated_at
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建供应商失败，请检查输入数据"
        )


@router.get("/suppliers", response_model=ModelSupplierListResponse)
async def get_suppliers(
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
    # 查询所有供应商，包括非激活的
    suppliers = db.query(SupplierDB).offset(skip).limit(limit).all()
    total = db.query(SupplierDB).count()
    
    # 为每个供应商添加display_name字段，使用name作为默认值
    suppliers_with_display_name = []
    for supplier in suppliers:
        # 创建一个带有display_name属性的对象
        supplier_dict = {
            "id": supplier.id,
            "name": supplier.name,
            "display_name": supplier.name,  # 使用name作为display_name
            "description": supplier.description,
            "api_endpoint": supplier.api_endpoint,
            "api_key_required": supplier.api_key_required,
            "is_active": supplier.is_active,
            "logo": supplier.logo,
            "category": supplier.category,
            "website": supplier.website,
            "api_docs": supplier.api_docs,
            "api_key": supplier.api_key,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at
        }
        suppliers_with_display_name.append(supplier_dict)
    
    return ModelSupplierListResponse(
        suppliers=suppliers_with_display_name,
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
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    return supplier


@router.put("/suppliers/{supplier_id}")
async def update_model_supplier(
    supplier_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    api_endpoint: Optional[str] = Form(None),
    api_key_required: Optional[bool] = Form(None),
    is_active: Optional[bool] = Form(None),
    logo: Optional[UploadFile] = File(None),
    existing_logo: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    api_docs: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新模型供应商信息（支持图片上传）
    
    Args:
        supplier_id: 供应商ID
        name: 供应商名称（可选）
        description: 供应商描述（可选）
        api_endpoint: API端点（可选）
        api_key_required: 是否需要API密钥（可选）
        is_active: 是否激活（可选）
        logo: 供应商logo图片（可选）
        existing_logo: 现有logo路径（可选）
        category: 供应商类别（可选）
        website: 供应商网站（可选）
        api_docs: API文档链接（可选）
        api_key: API密钥（可选）
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        更新后的模型供应商信息
    """
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    # 检查名称是否重复
    if name and name != supplier.name:
        existing_supplier = db.query(SupplierDB).filter(
            SupplierDB.name == name
        ).first()
        if existing_supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="供应商名称已存在"
            )
    
    # 更新字段
    if name is not None:
        setattr(supplier, 'name', name)
    if description is not None:
        setattr(supplier, 'description', description)
    if api_endpoint is not None:
        setattr(supplier, 'api_endpoint', api_endpoint)
    if api_key_required is not None:
        setattr(supplier, 'api_key_required', api_key_required)
    if is_active is not None:
        setattr(supplier, 'is_active', is_active)
    if category is not None:
        setattr(supplier, 'category', category)
    if website is not None:
        setattr(supplier, 'website', website)
    if api_docs is not None:
        setattr(supplier, 'api_docs', api_docs)
    if api_key is not None:
        setattr(supplier, 'api_key', api_key)
    
    # 处理logo上传
    if logo:
        # 如果有新的logo文件上传，保存它
        logo_path = await save_upload_file(logo)
        setattr(supplier, 'logo', logo_path)
        print(f"已更新logo为新上传的文件: {logo_path}")
    elif existing_logo is not None:
        # 如果提供了existing_logo，使用它
        setattr(supplier, 'logo', existing_logo)
        print(f"保留现有logo: {supplier.logo}")
    # 否则，保持原有logo不变
    
    # 更新时间戳
    setattr(supplier, 'updated_at', datetime.utcnow())
    
    try:
        db.commit()
        db.refresh(supplier)
        
        # 返回响应 - 使用name作为display_name
        return {
            "id": supplier.id,
            "name": supplier.name,
            "display_name": supplier.name,  # 使用name作为display_name
            "description": supplier.description,
            "api_endpoint": supplier.api_endpoint,
            "api_key_required": supplier.api_key_required,
            "is_active": supplier.is_active,
            "logo": supplier.logo,
            "category": supplier.category,
            "website": supplier.website,
            "api_docs": supplier.api_docs,
            "api_key": supplier.api_key,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at
        }
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
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
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
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
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
        if db_model.is_default is True:
            db.query(Model).filter(
                Model.supplier_id == supplier_id,
                Model.id != db_model.id
            ).update({Model.is_default: False})
        elif db.query(Model).filter(Model.supplier_id == supplier_id).count() == 0:
            # 如果是第一个模型，自动设为默认
            setattr(db_model, 'is_default', True)
        
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
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    models = db.query(Model).filter(
        Model.supplier_id == supplier_id
    ).offset(skip).limit(limit).all()
    total = db.query(Model).filter(Model.supplier_id == supplier_id).count()
    
    model_responses = [
        ModelResponse(
            id=model.id,
            name=model.name,
            display_name=getattr(model, "display_name", model.name),
            description=model.description,
            supplier_id=model.supplier_id,
            context_window=model.context_window,
            max_tokens=getattr(model, "max_tokens", None),
            is_default=model.is_default,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        for model in models
    ]
    
    return ModelListResponse(
        models=model_responses,
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
    if was_default is True:
        first_model = db.query(Model).filter(
            Model.supplier_id == supplier_id
        ).first()
        if first_model:
            setattr(first_model, 'is_default', True)
    
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
    setattr(model, 'is_default', True)
    
    db.commit()
    db.refresh(model)
    return model