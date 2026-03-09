"""
模型管理API路由

提供模型管理相关的RESTful API端点，包括：
- 模型的增删改查
- 模型参数管理
- 默认模型设置
- 模型Logo上传

所有端点都使用服务层处理业务逻辑，遵循分层架构原则。
"""

from typing import Any, Optional
from datetime import datetime
from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File, Form, Request
)
from sqlalchemy.orm import Session
import json
import os

# 导入数据库依赖
from app.core.dependencies import get_db

# 导入认证依赖
from app.api.deps import get_current_active_superuser, get_current_active_user
from app.models.user import User

# 导入服务层
from app.modules.model_management.services import ModelManagementService

# 导入数据校验模型
from app.modules.model_management.schemas import (
    ModelCreate, ModelUpdate, ModelResponse,
    ModelWithSupplierResponse, ModelListResponse,
    SetDefaultModelRequest,
    ModelParameterCreate, ModelParameterUpdate,
    ModelParameterResponse, ModelParameterListResponse
)

# 导入供应商模型（用于兼容现有代码）
from app.modules.supplier_model_management.schemas.supplier_model import (
    ModelCreate as SupplierModelCreate,
    ModelResponse as SupplierModelResponse
)

# 创建路由
router = APIRouter()

# 文件上传配置
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
    )
)  # 项目根目录
UPLOAD_DIR = os.path.join(BASE_DIR, "frontend", "public", "logos", "models")
UPLOAD_DIR = os.path.normpath(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 支持的图片扩展名
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    """
    检查文件扩展名是否允许
    
    Args:
        filename: 文件名
    
    Returns:
        是否允许上传
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


async def save_upload_file(upload_file: UploadFile) -> Optional[str]:
    """
    保存上传的文件并返回文件名
    
    Args:
        upload_file: 上传的文件对象
    
    Returns:
        保存后的文件名，失败时返回None
    
    Raises:
        HTTPException: 文件类型不支持或保存失败时抛出
    """
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
    
    if '.' not in upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名必须包含扩展名"
        )
    
    file_ext = upload_file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
        
        # 返回文件名
        return unique_filename
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )


# ==================== 模型管理API ====================

@router.get("/models", response_model=ModelListResponse)
async def get_all_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    获取所有模型列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        所有模型列表
    """
    service = ModelManagementService(db)
    models, total = service.get_all_models(skip=skip, limit=limit)
    
    return ModelListResponse(models=models, total=total)


@router.get("/suppliers/{supplier_id}/models", response_model=ModelListResponse)
async def get_models_by_supplier(
    supplier_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    获取指定供应商的模型列表
    
    Args:
        supplier_id: 供应商ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        模型列表
    """
    service = ModelManagementService(db)
    models, total = service.get_models_by_supplier(
        supplier_id=supplier_id,
        skip=skip,
        limit=limit
    )
    
    return ModelListResponse(models=models, total=total)


@router.get("/models/{model_id}", response_model=ModelWithSupplierResponse)
async def get_model_by_id(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    根据ID获取模型详情
    
    Args:
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        模型详情
    """
    service = ModelManagementService(db)
    model = service.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    return model


@router.post(
    "/suppliers/{supplier_id}/models",
    response_model=SupplierModelResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_model(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    model_data: str = Form(None),
    logo: UploadFile = File(None)
) -> Any:
    """
    为指定供应商创建新模型
    
    Args:
        supplier_id: 供应商ID
        request: 请求对象
        db: 数据库会话
        current_user: 当前用户
        model_data: 模型数据JSON字符串
        logo: 模型logo文件
    
    Returns:
        创建的模型信息
    """
    # 处理FormData格式请求
    if model_data:
        model_dict = json.loads(model_data)
    else:
        # 尝试从JSON请求体获取数据
        model_dict = await request.json()
    
    # 保存logo文件（如果有）
    logo_path = None
    if logo:
        logo_filename = await save_upload_file(logo)
        logo_path = f"/logos/models/{logo_filename}"
    
    # 使用服务层创建模型
    service = ModelManagementService(db)
    db_model = service.create_model(
        supplier_id=supplier_id,
        model_data=model_dict,
        logo_path=logo_path
    )
    
    # 执行智能能力发现
    try:
        from app.services.model_capability_service import (
            intelligent_capability_discovery
        )
        
        discovery_result = intelligent_capability_discovery.discover_capabilities(
            db, db_model.id
        )
        
        # 自动关联高置信度的能力（置信度 >= 50）
        auto_capabilities = intelligent_capability_discovery.auto_associate_discovered_capabilities(
            db, db_model.id, min_confidence=50
        )
        
    except Exception as e:
        # 不影响模型创建，只记录警告
        print(f"[WARNING] 智能能力发现失败: {str(e)}")
    
    return db_model


@router.put("/models/{model_id}", response_model=SupplierModelResponse)
async def update_model(
    model_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    model_data: str = Form(None),
    logo: UploadFile = File(None)
) -> Any:
    """
    更新模型
    
    Args:
        model_id: 模型ID
        request: 请求对象
        db: 数据库会话
        current_user: 当前用户
        model_data: 模型数据JSON字符串
        logo: 模型logo文件
    
    Returns:
        更新后的模型信息
    """
    # 处理FormData格式请求
    if model_data:
        model_dict = json.loads(model_data)
    else:
        # 尝试从JSON请求体获取数据
        model_dict = await request.json()
    
    # 保存logo文件（如果有）
    logo_path = None
    if logo:
        logo_filename = await save_upload_file(logo)
        logo_path = f"/logos/models/{logo_filename}"
    
    # 使用服务层更新模型
    service = ModelManagementService(db)
    db_model = service.update_model(
        model_id=model_id,
        model_data=model_dict,
        logo_path=logo_path
    )
    
    return db_model


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> None:
    """
    删除模型
    
    Args:
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前用户
    """
    service = ModelManagementService(db)
    service.delete_model(model_id)


@router.post("/models/{model_id}/set-default", response_model=SupplierModelResponse)
async def set_default_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    设置默认模型
    
    Args:
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        设置为默认的模型信息
    """
    service = ModelManagementService(db)
    db_model = service.set_default_model(model_id)
    
    return db_model


# ==================== 模型参数管理API ====================

@router.get("/models/{model_id}/parameters", response_model=ModelParameterListResponse)
async def get_model_parameters(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    获取模型的参数列表
    
    Args:
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        参数列表
    """
    service = ModelManagementService(db)
    
    # 验证模型是否存在
    model = service.get_model_by_id(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    parameters = service.get_model_parameters(model_id)
    
    return ModelParameterListResponse(
        model_id=model_id,
        supplier_id=model.supplier_id,
        parameters=parameters
    )


@router.post(
    "/models/{model_id}/parameters",
    response_model=ModelParameterResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_model_parameter(
    model_id: int,
    param_data: ModelParameterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    创建模型参数
    
    Args:
        model_id: 模型ID
        param_data: 参数数据
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        创建的参数信息
    """
    service = ModelManagementService(db)
    db_param = service.create_model_parameter(
        model_id=model_id,
        param_data=param_data.model_dump()
    )
    
    return db_param


@router.put("/parameters/{param_id}", response_model=ModelParameterResponse)
async def update_model_parameter(
    param_id: int,
    param_data: ModelParameterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    更新模型参数
    
    Args:
        param_id: 参数ID
        param_data: 参数数据
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        更新后的参数信息
    """
    service = ModelManagementService(db)
    db_param = service.update_model_parameter(
        param_id=param_id,
        param_data=param_data.model_dump(exclude_unset=True)
    )
    
    return db_param


@router.delete("/parameters/{param_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_parameter(
    param_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> None:
    """
    删除模型参数
    
    Args:
        param_id: 参数ID
        db: 数据库会话
        current_user: 当前用户
    """
    service = ModelManagementService(db)
    service.delete_model_parameter(param_id)
