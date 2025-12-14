"""模型管理相关API接口"""
from typing import Any, List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.supplier_db import ModelDB, ModelParameter
from app.models.model_category import ModelCategory
from app.services.parameter_management.parameter_manager import ParameterManager

# 从core导入数据库依赖
from app.core.dependencies import get_db
from app.modules.supplier_model_management.schemas.model_management import (
    ModelCreate, ModelUpdate, ModelResponse,
    ModelListResponse,
    SetDefaultModelRequest
)
from app.schemas.model_management import (
    ModelParameterCreate, ModelParameterUpdate, ModelParameterResponse,
    ModelParameterListResponse
)

# 创建上传目录
# 使用绝对路径确保文件能正确保存
# 获取项目根目录（backend的父目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # backend/app
BASE_DIR = os.path.dirname(BASE_DIR)  # backend
BASE_DIR = os.path.dirname(BASE_DIR)  # 项目根目录
UPLOAD_DIR = os.path.join(BASE_DIR, "frontend/public/logos/models")
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

# 为了与导入语句保持一致，创建一个别名
model_management_v1_router = router


















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
    
    # 查询数据库获取所有模型数据，包括供应商信息
    from sqlalchemy.orm import joinedload
    models = db.query(ModelDB).options(joinedload(ModelDB.supplier)).offset(skip).limit(limit).all()
    total = db.query(ModelDB).count()
    
    # 确保logo字段包含完整路径
    for model in models:
        if model.logo and not model.logo.startswith("/logos/models/"):
            model.logo = f"/logos/models/{model.logo}"
    
    print(f"返回 {len(models)} 个模型，总计 {total} 个模型")
    
    # 返回数据库查询结果
    return ModelListResponse(
        models=models,
        total=total
    )

@router.post("/suppliers/{supplier_id}/models", response_model=ModelResponse)
async def create_model(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user),
    model_data: str = Form(None),
    logo: UploadFile = File(None)
) -> Any:
    """
    为指定供应商创建新模型
    
    Args:
        supplier_id: 供应商ID
        request: 请求对象
        db: 数据库会话
        current_user: 当前活跃的超级用户
        model_data: 模型数据JSON字符串
        logo: 模型logo文件
    
    Returns:
        创建的模型信息
    """
    # 处理FormData格式请求
    import json
    if model_data:
        model_dict = json.loads(model_data)
    else:
        # 尝试从JSON请求体获取数据
        model_dict = await request.json()
    
    # 确保supplier_id一致
    model_dict['supplier_id'] = supplier_id
    
    # 保存logo文件（如果有）
    if logo:
        logo_filename = await save_upload_file(logo)
        model_dict["logo"] = f"/logos/models/{logo_filename}"
    
    try:
        # 处理模型类型：验证前端发送的model_type_id是否存在
        if 'model_type_id' in model_dict:
            # 验证分类是否存在
            category = db.query(ModelCategory).filter(ModelCategory.id == model_dict['model_type_id']).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model category with id {model_dict['model_type_id']} not found"
                )
        # 如果存在旧的model_type字段（用于向后兼容），则删除
        if 'model_type' in model_dict:
            del model_dict['model_type']
        
        # 创建新模型
        db_model = ModelDB(**model_dict)
        db.add(db_model)
        
        # 如果是第一个模型或者设置为默认模型，将其他模型的is_default设置为False
        if db_model.is_default is True:
            db.query(ModelDB).filter(
                ModelDB.supplier_id == supplier_id,
                ModelDB.id != db_model.id
            ).update({ModelDB.is_default: False})
        elif db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).count() == 0:
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
    models = db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).offset(skip).limit(limit).all()
    total = db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).count()
    
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
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 确保logo字段包含完整路径
    if model.logo and not model.logo.startswith("/logos/models/"):
        model.logo = f"/logos/models/{model.logo}"
    
    return model


@router.put("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
async def update_model(
    supplier_id: int,
    model_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user),
    model_data: str = Form(None),
    logo: UploadFile = File(None)
) -> Any:
    """
    更新模型信息
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
        model_data: 模型数据JSON字符串
        logo: 模型logo文件
    
    Returns:
        更新后的模型信息
    """
    import json
    from fastapi import Request
    
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 处理FormData格式请求
    if model_data:
        update_data = json.loads(model_data)
    else:
        # 保留对JSON格式请求的兼容性支持
        update_data = await request.json()
    
    # 确保supplier_id和model_id一致
    update_data['supplier_id'] = supplier_id
    update_data['id'] = model_id
    
    # 处理模型类型：验证前端发送的model_type_id是否存在
    if 'model_type_id' in update_data:
        # 验证分类是否存在
        category = db.query(ModelCategory).filter(ModelCategory.id == update_data['model_type_id']).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model category with id {update_data['model_type_id']} not found"
            )
    # 如果存在旧的model_type字段（用于向后兼容），则删除
    if 'model_type' in update_data:
        del update_data['model_type']
    
    # 保存logo文件（如果有）
    if logo:
        logo_filename = await save_upload_file(logo)
        update_data["logo"] = f"/logos/models/{logo_filename}"
    
    # 如果更新了is_default为True，需要将其他模型的is_default设置为False
    if 'is_default' in update_data and update_data['is_default']:
        db.query(ModelDB).filter(
            ModelDB.supplier_id == supplier_id,
            ModelDB.id != model_id
        ).update({ModelDB.is_default: False})
    
    for field, value in update_data.items():
        setattr(model, field, value)
    
    try:
        db.commit()
        db.refresh(model)
        # 创建符合ModelResponse格式的响应
        response = {
            "id": model.id,
            "supplier_id": model.supplier_id,
            "model_id": model.model_id,
            "model_name": model.model_name,
            "description": model.description,
            "model_type_id": model.model_type_id,
            "model_type_name": model.model_type.name if model.model_type else None,
            "context_window": model.context_window,
            "max_tokens": model.max_tokens,
            "is_default": model.is_default,
            "is_active": model.is_active,
            "logo": model.logo,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        return response
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
        first_model = db.query(ModelDB).filter(
            ModelDB.supplier_id == supplier_id
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
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 将所有模型的is_default设置为False
    db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).update({ModelDB.is_default: False})
    
    # 将指定模型设为默认
    setattr(model, 'is_default', True)
    
    db.commit()
    db.refresh(model)
    return model


# 模型参数相关路由
@router.get("/suppliers/{supplier_id}/models/{model_id}/parameters", response_model=ModelParameterListResponse)
def get_model_parameters(
    supplier_id: int,
    model_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
):
    """获取模型参数"""
    print(f"[API V1] 调用get_model_parameters: supplier_id={supplier_id}, model_id={model_id}")
    # 验证模型是否存在
    try:
        # 直接使用SQL语句测试
        from sqlalchemy import text
        result = db.execute(text("SELECT * FROM models WHERE id=:model_id AND supplier_id=:supplier_id"), 
                          {"model_id": model_id, "supplier_id": supplier_id})
        sql_result = result.fetchone()
        print(f"[API V1] SQL直接查询结果: {sql_result}")
        
        # 使用ORM查询
        model = db.query(ModelDB).filter(
            ModelDB.id == model_id,
            ModelDB.supplier_id == supplier_id
        ).first()
        print(f"[API V1] ORM查询结果: {model}")
        
        if not model:
            print(f"[API V1] 模型不存在: supplier_id={supplier_id}, model_id={model_id}")
            raise HTTPException(status_code=404, detail="模型不存在")
    except Exception as e:
        print(f"[API V1] 查询异常: {str(e)}")
        raise HTTPException(status_code=500, detail="查询异常")
    
    # 获取模型参数，包括参数模板的继承
    parameters = ParameterManager.get_model_parameters_with_templates(db, model_id)
    
    return ModelParameterListResponse(
        model_id=model_id,
        supplier_id=supplier_id,
        parameters=parameters
    )


@router.post("/suppliers/{supplier_id}/models/{model_id}/parameters", response_model=Dict[str, Any])
def create_model_parameter(
    supplier_id: int,
    model_id: int,
    param_data: ModelParameterCreate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
):
    """创建模型参数"""
    # 验证模型是否存在
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        # 创建或更新参数
        param = ParameterManager.create_or_update_model_parameter(db, model_id, param_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 获取完整参数并返回
    model_params = ParameterManager.get_model_parameters(db, model_id)
    return {
        "model_id": model_id,
        "supplier_id": supplier_id,
        "parameters": model_params
    }


@router.put("/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_name}", response_model=Dict[str, Any])
def update_model_parameter(
    supplier_id: int,
    model_id: int,
    parameter_name: str,
    param_data: ModelParameterUpdate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
):
    """更新模型参数"""
    # 验证模型是否存在
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 查找现有参数
    param = db.query(ModelParameter).filter(
        ModelParameter.model_id == model_id,
        ModelParameter.parameter_name == parameter_name
    ).first()
    
    if not param:
        raise HTTPException(status_code=404, detail="参数不存在")
    
    try:
        # 更新参数字段
        for field, value in param_data.model_dump(exclude_unset=True).items():
            setattr(param, field, value)
        
        # 如果更新了参数值和类型，进行验证
        if param_data.parameter_value is not None and param_data.parameter_type is not None:
            ParameterManager._convert_parameter_value(param_data.parameter_value, param_data.parameter_type)
        elif param_data.parameter_value is not None:
            ParameterManager._convert_parameter_value(param_data.parameter_value, param.parameter_type)
        elif param_data.parameter_type is not None:
            ParameterManager._convert_parameter_value(param.parameter_value, param_data.parameter_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    db.commit()
    db.refresh(param)
    
    # 获取完整参数并返回
    model_params = ParameterManager.get_model_parameters(db, model_id)
    return {
        "model_id": model_id,
        "supplier_id": supplier_id,
        "parameters": model_params
    }


@router.delete("/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_name}", response_model=Dict[str, Any])
def delete_model_parameter(
    supplier_id: int,
    model_id: int,
    parameter_name: str,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
):
    """删除模型参数"""
    # 验证模型是否存在
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.supplier_id == supplier_id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 删除参数
    deleted = ParameterManager.delete_model_parameter(db, model_id, parameter_name)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="参数不存在")
    
    # 返回更新后的所有参数
    parameters = ParameterManager.get_model_parameters(db, model_id)
    
    return {
        "model_id": model_id,
        "supplier_id": supplier_id,
        "parameters": parameters
    }