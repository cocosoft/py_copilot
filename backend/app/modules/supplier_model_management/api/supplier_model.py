"""供应商和模型相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import aiofiles
import requests

# 导入项目配置的日志记录器
from app.core.logging_config import logger

from app.core.dependencies import get_db
from app.models.supplier_db import SupplierDB, ModelDB
from app.models.model_category import ModelCategory
from app.modules.supplier_model_management.schemas.supplier_model import (
    SupplierCreate, SupplierResponse,
    ModelCreate, ModelResponse, ModelListResponse
)

router = APIRouter()

# 文件上传配置
# 获取项目根目录（backend的父目录）
CURRENT_FILE = os.path.abspath(__file__)
# 从当前文件开始向上导航到项目根目录
BASE_DIR = os.path.dirname(CURRENT_FILE)  # api
BASE_DIR = os.path.dirname(BASE_DIR)  # supplier_model_management
BASE_DIR = os.path.dirname(BASE_DIR)  # modules
BASE_DIR = os.path.dirname(BASE_DIR)  # app
BASE_DIR = os.path.dirname(BASE_DIR)  # backend
UPLOAD_DIR = os.path.join(BASE_DIR, "../frontend/public/logos/providers")
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
        display_name=name,  # display_name与name保持一致
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
# 注意：固定路径路由必须放在带参数的路由之前
@router.get("/suppliers")
def get_all_suppliers(db: Session = Depends(get_db)):
    """获取所有供应商"""
    suppliers = db.query(SupplierDB).all()
    # 返回包含display_name字段的供应商信息列表
    return [{
        "id": supplier.id,
        "name": supplier.name,
        "display_name": supplier.display_name,
        "description": supplier.description,
        "logo": supplier.logo,
        "website": supplier.website,
        "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
        "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
        "is_active": supplier.is_active
    } for supplier in suppliers]

@router.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """获取单个供应商"""
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    # 返回包含display_name字段的供应商信息
    return {
        "id": supplier.id,
        "name": supplier.name,
        "display_name": supplier.display_name,
        "description": supplier.description,
        "logo": supplier.logo,
        "website": supplier.website,
        "created_at": supplier.created_at,
        "updated_at": supplier.updated_at,
        "is_active": supplier.is_active
    }

@router.get("/suppliers/all")
def get_all_suppliers_legacy(db: Session = Depends(get_db)):
    """获取所有供应商（兼容旧版端点）"""
    return get_all_suppliers(db)

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

@router.patch("/suppliers/{supplier_id}/status", response_model=dict)
def update_supplier_status(supplier_id: int, status_update: dict, db: Session = Depends(get_db)):
    """更新供应商状态"""
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 从请求体中获取is_active字段
    is_active = status_update.get("is_active", supplier.is_active)
    
    # 更新供应商状态
    supplier.is_active = is_active
    supplier.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(supplier)
    
    # 返回包含display_name字段的供应商信息
    return {
        "id": supplier.id,
        "name": supplier.name,
        "display_name": supplier.display_name,
        "description": supplier.description,
        "logo": supplier.logo,
        "website": supplier.website,
        "created_at": supplier.created_at,
        "updated_at": supplier.updated_at,
        "is_active": supplier.is_active
    }



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
            id=str(model.id),
            model_id=str(model.model_id) if model.model_id is not None else "",
            model_name=str(getattr(model, "model_name", model.model_id)) if getattr(model, "model_name", model.model_id) is not None else "",
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
async def create_model(supplier_id: int, model_data: str = Form(...), logo: UploadFile = File(None), db: Session = Depends(get_db)):
    """创建新模型，支持LOGO上传"""
    import json
    
    # 解析JSON数据
    try:
        model = json.loads(model_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的JSON格式")
    
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 检查模型ID是否已存在
    existing_model = db.query(ModelDB).filter(
        ModelDB.model_id == model['model_id'],
        ModelDB.supplier_id == supplier_id
    ).first()
    if existing_model:
        raise HTTPException(status_code=400, detail="模型ID已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认
    if model.get('is_default', False):
        db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).update({"is_default": False})
    
    # 保存LOGO文件（如果有）
    logo_path = None
    if logo:
        logo_path = await save_upload_file(logo)
    
    # 处理模型类型字段
    model_type_id = None
    if 'model_type' in model:
        # 获取或创建模型分类
        model_category = db.query(ModelCategory).filter(
            ModelCategory.name == model['model_type']
        ).first()
        if model_category:
            model_type_id = model_category.id
    elif 'model_type_id' in model:
        # 验证模型分类是否存在
        model_category = db.query(ModelCategory).filter(
            ModelCategory.id == model['model_type_id']
        ).first()
        if not model_category:
            raise HTTPException(
                status_code=400,
                detail=f"Model category with id {model['model_type_id']} not found"
            )
        model_type_id = model['model_type_id']
    
    # 创建新模型
    # 只使用ModelDB中定义的字段
    db_model_data = {
        "model_id": model['model_id'],
        "model_name": model.get('model_name'),
        "description": model.get('description'),
        "supplier_id": supplier_id,
        "context_window": model.get('context_window'),
        "max_tokens": model.get('max_tokens'),
        "logo": logo_path,
        "is_default": model.get('is_default', False),
        "is_active": model.get('is_active', True)
    }
    
    # 如果设置了模型类型ID，添加到数据中
    if model_type_id is not None:
        db_model_data['model_type_id'] = model_type_id
    
    db_model = ModelDB(**db_model_data)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model

@router.put("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
async def update_model(supplier_id: int, model_id: int, request: Request, db: Session = Depends(get_db)):
    """更新模型信息，支持LOGO上传"""
    import json
    
    content_type = request.headers.get('content-type')
    
    if content_type and 'multipart/form-data' in content_type:
        # 处理包含文件上传的请求
        form_data = await request.form()
        
        # 解析JSON数据
        model_json = form_data.get('model_data')
        if not model_json:
            raise HTTPException(
                status_code=400,
                detail="缺少模型数据"
            )
            
        model_update = json.loads(model_json)
        
        # 保存LOGO文件（如果有）
        logo_path = None
        logo_file = form_data.get('logo')
        if logo_file and logo_file.filename:
            logo_path = await save_upload_file(logo_file)
            model_update['logo'] = logo_path
        elif 'logo' in model_update and model_update['logo'] is None:
            # 如果明确设置logo为None，则删除logo
            model_update['logo'] = None
    else:
        # 处理普通JSON请求
        model_update = await request.json()
    
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
    if 'model_id' in model_update and model_update['model_id'] != model.model_id:
        existing_model = db.query(ModelDB).filter(
            ModelDB.model_id == model_update['model_id'],
            ModelDB.supplier_id == supplier_id,
            ModelDB.id != model_id
        ).first()
        if existing_model:
            raise HTTPException(status_code=400, detail="模型ID已存在")
    
    # 如果设置为默认模型，先将其他模型设为非默认
    if model_update.get('is_default', False):
        db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).update({"is_default": False})
    
    # 处理模型类型字段
    if 'model_type' in model_update:
        # 获取或创建模型分类
        model_category = db.query(ModelCategory).filter(
            ModelCategory.name == model_update['model_type']
        ).first()
        if model_category:
            model_update['model_type_id'] = model_category.id
        # 删除原来的model_type字段
        del model_update['model_type']
    elif 'model_type_id' in model_update:
        # 验证模型分类是否存在
        model_category = db.query(ModelCategory).filter(
            ModelCategory.id == model_update['model_type_id']
        ).first()
        if not model_category:
            raise HTTPException(
                status_code=400,
                detail=f"Model category with id {model_update['model_type_id']} not found"
            )
    
    # 更新模型数据
    for key, value in model_update.items():
        setattr(model, key, value)
    
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

@router.get("/models", response_model=ModelListResponse)
def get_all_models(db: Session = Depends(get_db)):
    """获取所有模型（通用接口）"""
    # 获取所有模型
    models = db.query(ModelDB).all()
    total = len(models)
    
    # 转换为响应格式
    model_responses = [
        ModelResponse(
            id=str(model.id),
            model_id=str(model.model_id) if model.model_id is not None else "",
            model_name=str(getattr(model, "model_name", model.model_id)) if getattr(model, "model_name", model.model_id) is not None else "",
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


@router.post("/suppliers/{supplier_id}/test-api")
def test_api_config(
    supplier_id: int,
    request_data: dict,
    db: Session = Depends(get_db)
):
    """测试供应商API配置的有效性"""
    try:
        logger.info(f"开始测试供应商API配置，供应商ID: {supplier_id}")
        
        # 验证供应商是否存在
        supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
        if not supplier:
            logger.error(f"测试API配置失败：供应商ID {supplier_id} 不存在")
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "供应商不存在"}
            )
        
        logger.info(f"找到供应商：{supplier.name}")
        
        # 获取API配置
        api_endpoint = request_data.get("api_endpoint")
        api_key = request_data.get("api_key")
        
        logger.info(f"获取API配置：endpoint={api_endpoint}, api_key={'已提供' if api_key else '未提供'}")
        
        if not api_endpoint:
            logger.error(f"测试API配置失败：未提供API端点")
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "API端点不能为空"}
            )
        
        try:
            # 设置请求头
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            logger.info(f"发送测试请求到：{api_endpoint}, 头信息: {headers}")
            
            # 发送GET请求测试API连接
            response = requests.get(api_endpoint, headers=headers, timeout=10)
            
            logger.info(f"API请求成功，状态码: {response.status_code}, 响应内容: {response.text[:200]}...")
            
            # 检查响应状态码
            if response.status_code == 200:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "API测试成功",
                        "status_code": response.status_code,
                        "response_text": response.text
                    }
                )
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": f"API测试失败，返回状态码: {response.status_code}",
                        "status_code": response.status_code,
                        "response_text": response.text
                    }
                )
        except requests.exceptions.ConnectionError:
            logger.error(f"API测试失败：无法连接到 {api_endpoint}，连接错误")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "无法连接到API端点，请检查地址是否正确。",
                    "status_code": 0,
                    "response_text": "连接错误"
                }
            )
        except requests.exceptions.Timeout:
            logger.error(f"API测试失败：请求 {api_endpoint} 超时")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "API请求超时，请检查网络连接或尝试调整超时设置。",
                    "status_code": 0,
                    "response_text": "请求超时"
                }
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"API测试失败：请求异常 - {str(e)}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"API请求异常：{str(e)}",
                    "status_code": 0,
                    "response_text": str(e)
                }
            )
    except Exception as e:
        logger.error(f"测试API配置时发生未知错误：{str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"测试失败：{str(e)}"}
        )
