"""供应商和模型相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
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
@router.get("/suppliers-list", response_model=List[SupplierResponse])
def get_all_suppliers(db: Session = Depends(get_db)):
    """获取所有供应商"""
    suppliers = db.query(SupplierDB).all()
    
    # 构建响应数据列表，确保所有字段都有合适的值
    supplier_responses = []
    for supplier in suppliers:
        # 创建响应字典
        supplier_dict = {
            "id": supplier.id,
            "name": supplier.name,
            "display_name": supplier.display_name if supplier.display_name is not None else supplier.name,
            "description": supplier.description,
            "logo": supplier.logo,
            "website": supplier.website,
            "api_key_required": supplier.api_key_required if supplier.api_key_required is not None else False,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at,
            "is_active": supplier.is_active
        }
        supplier_responses.append(supplier_dict)
    
    return supplier_responses

# 将获取单个供应商的路由移到获取所有供应商路由之后
@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """获取单个供应商"""
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 解密API密钥（如果有）
    if supplier.api_key:
        try:
            from app.core.encryption import decrypt_string
            supplier.api_key = decrypt_string(supplier.api_key)
        except Exception as e:
            # 如果解密失败，记录错误但不中断请求
            import logging
            logging.error(f"解密供应商 {supplier.id} 的API密钥失败: {str(e)}")
            supplier.api_key = None
    
    return supplier

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
        
        # 检查供应商是否存在
        supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
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
        if "name" in update_data and update_data["name"] != supplier.name:
            existing_supplier = db.query(SupplierDB).filter(
                SupplierDB.name == update_data["name"],
                SupplierDB.id != supplier_id
            ).first()
            if existing_supplier:
                raise HTTPException(status_code=400, detail="供应商名称已存在")
        
        # 保存新logo文件（如果有）
        if logo:
            logo_path = await save_upload_file(logo)
            update_data["logo"] = logo_path
        
        # 更新基本信息
        logger.info(f"[更新供应商] 要更新的字段: {list(update_data.keys())}")
        for key, value in update_data.items():
            if hasattr(supplier, key) and value is not None:
                if key == "api_key":
                    logger.info(f"[更新供应商] 直接设置API密钥: {value}")
                    supplier.api_key = value
                else:
                    logger.info(f"[更新供应商] 更新字段: {key} = {value} (类型: {type(value)})")
                    setattr(supplier, key, value)
        
        # 检查API密钥是否被正确设置
        if hasattr(supplier, 'api_key'):
            logger.info(f"[更新供应商] API密钥设置后: {supplier.api_key}")
            logger.info(f"[更新供应商] API密钥加密后: {supplier._api_key}")
        
        # 更新时间
        supplier.updated_at = datetime.utcnow()
        
        logger.info(f"[更新供应商] 准备提交到数据库")
        db.commit()
        db.refresh(supplier)
        logger.info(f"[更新供应商] 更新成功")
        
        # 返回供应商信息
        # 显式解密API密钥，确保返回解密后的值
        response_data = {
            "id": supplier.id,
            "name": supplier.name,
            "display_name": supplier.display_name,
            "description": supplier.description,
            "logo": supplier.logo,
            "website": supplier.website,
            "api_endpoint": supplier.api_endpoint,
            "api_key_required": supplier.api_key_required,
            "category": supplier.category,
            "api_docs": supplier.api_docs,
            "is_active": supplier.is_active,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at,
            "api_key": supplier.api_key  # 这会自动调用getter方法获取解密后的值
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
            model_id=model.model_id,
            model_name=model.model_name,
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
    
    # 检查模型ID是否已存在
    existing_model = db.query(ModelDB).filter(
        ModelDB.model_id == model.get('model_id'),
        ModelDB.supplier_id == supplier_id
    ).first()
    if existing_model:
        raise HTTPException(status_code=400, detail="模型ID已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认
    if model.get('is_default'):
        db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).update({"is_default": False})
    
    # 创建新模型
    # 只使用ModelDB中定义的字段
    db_model_data = {
        "model_id": model.get('model_id'),
        "model_name": model.get('model_name'),
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
    
    # 检查模型ID是否被其他模型使用
    update_model_id = model_update.get('model_id')
    if update_model_id is not None and update_model_id != model.model_id:
        existing_model = db.query(ModelDB).filter(
            ModelDB.model_id == update_model_id,
            ModelDB.supplier_id == supplier_id,
            ModelDB.id != model_id
        ).first()
        if existing_model:
            raise HTTPException(status_code=400, detail="模型ID已存在")
    
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
    """
    删除模型
    """
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
    
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        logger.error(f"[API测试] 供应商不存在 - 供应商ID: {supplier_id}")
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 提取API配置 - 始终使用数据库中的API端点
    api_endpoint = supplier.api_endpoint
    # 使用前端传递的API密钥
    api_key = api_config.get("api_key")
    
    logger.info(f"[API测试] 提取的API配置 - 端点: {api_endpoint}, 密钥长度: {len(api_key) if api_key else 0}")
    
    if not api_endpoint:
        logger.error(f"[API测试] API端点为空 - 供应商ID: {supplier_id}")
        raise HTTPException(status_code=400, detail="API端点不能为空")
    
    try:
        # 根据供应商类型选择不同的测试方法
        # 这里提供一个通用的测试方法，具体可以根据不同供应商类型进行扩展
        headers = {"Authorization": f"Bearer {api_key}"}
        logger.info(f"[API测试] 发送请求 - 方法: GET, 端点: {api_endpoint}, 头信息: {headers.keys()}")
        
        # 发送简单的GET请求测试连接
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
