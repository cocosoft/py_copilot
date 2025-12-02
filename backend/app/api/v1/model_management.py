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
from app.models.supplier_db import ModelDB as Model

# 创建直接连接到py_copilot.db的数据库会话
def get_db():
    engine = create_engine('sqlite:///./py_copilot.db')
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from app.schemas.model_management import (
    ModelCreate, ModelUpdate, ModelResponse,
    ModelListResponse,
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
    # 供应商验证已移除，现在使用数据库中的suppliers表
    
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
    # 供应商验证已移除，现在使用数据库中的suppliers表
    
    models = db.query(Model).filter(
        Model.supplier_id == supplier_id
    ).offset(skip).limit(limit).all()
    total = db.query(Model).filter(Model.supplier_id == supplier_id).count()
    
    # 转换模型数据为响应格式
    model_responses = []
    for model in models:
        # 创建符合ModelResponse结构的字典，为缺少的字段提供默认值
        model_data = {
            "id": model.id,
            "supplier_id": model.supplier_id,
            "model_id": getattr(model, "model_id", str(model.id)),  # 使用id作为默认model_id
            "name": getattr(model, "name", ""),
            "description": getattr(model, "description", None),
            "type": getattr(model, "type", "chat"),  # 默认类型为chat
            "context_window": getattr(model, "context_window", 8000),
            "default_temperature": getattr(model, "default_temperature", 0.7),
            "default_max_tokens": getattr(model, "max_tokens", 1000) or getattr(model, "default_max_tokens", 1000),
            "default_top_p": getattr(model, "default_top_p", 1.0),
            "default_frequency_penalty": getattr(model, "default_frequency_penalty", 0.0),
            "default_presence_penalty": getattr(model, "default_presence_penalty", 0.0),
            "custom_params": getattr(model, "custom_params", None),
            "is_active": getattr(model, "is_active", True),
            "is_default": getattr(model, "is_default", False),
            "created_at": getattr(model, "created_at", datetime.now()),
            "updated_at": getattr(model, "updated_at", None),
            "categories": []
        }
        model_responses.append(model_data)
    
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