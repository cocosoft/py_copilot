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
from app.models.supplier_db import ModelDB as Model, ModelParameter

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
    SetDefaultModelRequest,
    ModelParameterCreate, ModelParameterUpdate, ModelParameterResponse,
    ModelParameterListResponse
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
@router.get("/models", response_model=ModelListResponse)
async def get_all_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取所有模型列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        所有模型列表
    """
    print("收到获取所有模型列表的请求")
    
    # 查询数据库获取所有模型数据
    models = db.query(Model).offset(skip).limit(limit).all()
    total = db.query(Model).count()
    
    print(f"返回 {len(models)} 个模型，总计 {total} 个模型")
    
    # 返回数据库查询结果
    return ModelListResponse(
        models=models,
        total=total
    )

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
    print(f"收到获取供应商 {supplier_id} 模型列表的请求")
    
    # 查询数据库获取模型数据
    models = db.query(Model).filter(Model.supplier_id == supplier_id).offset(skip).limit(limit).all()
    total = db.query(Model).filter(Model.supplier_id == supplier_id).count()
    
    print(f"返回 {len(models)} 个模型，总计 {total} 个模型")
    
    # 返回数据库查询结果
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


# 模型参数相关路由
@router.get("/suppliers/{supplier_id}/models/{model_id}/parameters", response_model=ModelParameterListResponse)
async def get_model_parameters(
    supplier_id: int,
    model_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取指定模型的参数列表
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型参数列表
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
    
    # 查询指定模型的参数
    parameters = db.query(ModelParameter).filter(
        ModelParameter.model_id == model_id
    ).offset(skip).limit(limit).all()
    
    total = db.query(ModelParameter).filter(
        ModelParameter.model_id == model_id
    ).count()
    
    return ModelParameterListResponse(
        parameters=parameters,
        total=total
    )


@router.post("/suppliers/{supplier_id}/models/{model_id}/parameters", response_model=ModelParameterResponse)
async def create_model_parameter(
    supplier_id: int,
    model_id: int,
    parameter: ModelParameterCreate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    为指定模型创建新参数
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        parameter: 模型参数创建数据
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        创建的模型参数信息
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
    
    # 确保model_id一致
    parameter_data = parameter.model_dump()
    parameter_data['model_id'] = model_id
    
    try:
        # 创建新参数
        db_parameter = ModelParameter(**parameter_data)
        db.add(db_parameter)
        db.commit()
        db.refresh(db_parameter)
        return db_parameter
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建模型参数失败，请检查输入数据"
        )


@router.get("/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_id}", response_model=ModelParameterResponse)
async def get_model_parameter(
    supplier_id: int,
    model_id: int,
    parameter_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取指定的模型参数
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        parameter_id: 参数ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型参数信息
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
    
    # 查询指定参数
    parameter = db.query(ModelParameter).filter(
        ModelParameter.id == parameter_id,
        ModelParameter.model_id == model_id
    ).first()
    
    if not parameter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型参数不存在"
        )
    
    return parameter


@router.put("/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_id}", response_model=ModelParameterResponse)
async def update_model_parameter(
    supplier_id: int,
    model_id: int,
    parameter_id: int,
    parameter_update: ModelParameterUpdate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新模型参数
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        parameter_id: 参数ID
        parameter_update: 更新数据
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        更新后的模型参数信息
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
    
    # 查询指定参数
    parameter = db.query(ModelParameter).filter(
        ModelParameter.id == parameter_id,
        ModelParameter.model_id == model_id
    ).first()
    
    if not parameter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型参数不存在"
        )
    
    # 更新参数信息
    update_data = parameter_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(parameter, field, value)
    
    try:
        db.commit()
        db.refresh(parameter)
        return parameter
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新模型参数失败，请检查输入数据"
        )


@router.delete("/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_parameter(
    supplier_id: int,
    model_id: int,
    parameter_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> None:
    """
    删除模型参数
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        parameter_id: 参数ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
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
    
    # 查询指定参数
    parameter = db.query(ModelParameter).filter(
        ModelParameter.id == parameter_id,
        ModelParameter.model_id == model_id
    ).first()
    
    if not parameter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型参数不存在"
        )
    
    # 删除参数
    db.delete(parameter)
    db.commit()