"""模型管理相关API接口"""
from typing import Any, List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import json

# 导入参数管理服务
from app.services.parameter_management.parameter_manager import ParameterManager

# 导入日志记录器
from app.core.logging_config import logger
import uuid
from datetime import datetime

from sqlalchemy import create_engine, text
from app.core.encryption import encrypt_string, decrypt_string
from sqlalchemy.orm import sessionmaker
from app.models.supplier_db import SupplierDB, ModelDB
from app.models.model_management import Model
from app.models.model_category import ModelCategory
from sqlalchemy import inspect

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
# 设置模型logo保存路径为frontend/public/logos/models
# 获取当前文件所在目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 从当前目录向上导航到backend目录
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../../../"))
# 项目根目录是backend的父目录 (包含项目文件夹名称)
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
# 构建模型logo保存路径
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "frontend", "public", "logos", "models")
UPLOAD_DIR = os.path.normpath(UPLOAD_DIR)  # 规范化路径
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"模型logo保存目录: {UPLOAD_DIR}")  # 添加日志以便调试

# 支持的图片扩展名
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# 模拟用户相关定义已在其他地方声明

# 移除重复函数定义

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def save_upload_file(upload_file: UploadFile) -> str:
    """保存上传的文件并返回相对路径"""
    print(f"[文件上传] 开始处理文件: {upload_file.filename}")
    print(f"[文件上传] ALLOWED_EXTENSIONS: {ALLOWED_EXTENSIONS}")
    print(f"[文件上传] UPLOAD_DIR: {UPLOAD_DIR}")
    
    if not allowed_file(upload_file.filename):
        print(f"[文件上传] 不支持的文件类型: {upload_file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，请上传图片文件 (png, jpg, jpeg, gif, webp)"
        )
    
    # 生成唯一文件名
    if not upload_file.filename:
        print(f"[文件上传] 文件名不能为空")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    # 检查文件名是否有扩展名
    if '.' not in upload_file.filename:
        print(f"[文件上传] 文件名必须包含扩展名: {upload_file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名必须包含扩展名"
        )
    file_ext = upload_file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        print(f"[文件上传] 准备保存文件到: {file_path}")
        # 确保上传目录存在
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        print(f"[文件上传] 目录存在检查通过")
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await upload_file.read()
            print(f"[文件上传] 读取文件内容，大小: {len(content)} bytes")
            buffer.write(content)
        
        print(f"[文件上传] 文件保存成功: {unique_filename}")
        
        # 返回前端可访问的路径格式
        frontend_path = f"/logos/models/{unique_filename}"
        print(f"[文件上传] 返回前端路径: {frontend_path}")
        return frontend_path
    except Exception as e:
        print(f"[文件上传] 文件保存失败: {str(e)}")
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

# 测试路由
@router.get("/test-route")
async def test_route():
    return {"message": "Test route is working"}
@router.get("/test")
async def test_route():
    """测试路由是否正常工作"""
    return {"message": "Test route is working!"}


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
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # 使用原始SQL插入供应商记录，避免ORM的关系映射问题
        from sqlalchemy import text
        
        # 加密API密钥
        encrypted_api_key = None
        if api_key is not None:
            from app.core.encryption import encrypt_string
            encrypted_api_key = encrypt_string(api_key)
        
        # 构建插入SQL
        insert_sql = text("""
            INSERT INTO suppliers (
                name, display_name, description, api_endpoint, api_key_required, 
                is_active, logo, category, website, api_docs, api_key, 
                created_at, updated_at
            ) VALUES (
                :name, :display_name, :description, :api_endpoint, :api_key_required, 
                :is_active, :logo, :category, :website, :api_docs, :api_key, 
                :created_at, :updated_at
            )
        """)
        
        # 执行插入
        db.execute(insert_sql, {
            "name": name,
            "display_name": name,
            "description": description,
            "api_endpoint": api_endpoint,
            "api_key_required": api_key_required,
            "is_active": is_active,
            "logo": logo_url,
            "category": category,
            "website": website,
            "api_docs": api_docs,
            "api_key": encrypted_api_key,
            "created_at": now,
            "updated_at": now
        })
        db.commit()
        
        # 获取新插入的供应商ID
        result = db.execute(text("SELECT last_insert_rowid()"))
        supplier_id = result.scalar()
        
        # 解密API密钥用于返回
        decrypted_api_key = None
        if api_key is not None:
            decrypted_api_key = api_key
        
        # 返回响应
        return {
            "id": supplier_id,
            "name": name,
            "display_name": name,
            "description": description,
            "api_endpoint": api_endpoint,
            "api_key_required": api_key_required,
            "is_active": is_active,
            "logo": logo_url,
            "category": category,
            "website": website,
            "api_docs": api_docs,
            "api_key": decrypted_api_key,
            "created_at": now,
            "updated_at": now
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建供应商失败，请检查输入数据"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建供应商失败: {str(e)}"
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


# 重命名路由以避免与参数化路由冲突
@router.get("/suppliers-list")
async def get_all_suppliers(
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取所有模型供应商
    
    Args:
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        所有模型供应商列表
    """
    try:
        # 查询所有供应商，包括非激活的
        suppliers = db.query(SupplierDB).all()
        total = len(suppliers)
        
        # 构建响应数据
        supplier_responses = []
        for supplier in suppliers:
            # 安全地获取API密钥（如果解密失败，返回None）
            api_key_required = False
            try:
                api_key_required = supplier.api_key_required if supplier.api_key_required is not None else False
            except Exception as e:
                print(f"Error accessing api_key_required for supplier {supplier.id}: {e}")
                api_key_required = False
            
            supplier_responses.append({
                "id": supplier.id,
                "name": supplier.name,
                "display_name": supplier.display_name if supplier.display_name is not None else supplier.name,
                "description": supplier.description,
                "logo": supplier.logo,
                "website": supplier.website,
                "api_key_required": api_key_required,
                "is_active": supplier.is_active
            })
        
        return {
            "suppliers": supplier_responses,
            "total": total
        }
    except Exception as e:
        # 添加详细的错误日志
        print(f"Error in get_all_suppliers: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取供应商列表失败: {str(e)}"
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
    
    # 解密API密钥（如果有）
    if supplier.api_key:
        try:
            from app.core.encryption import decrypt_string
            supplier.api_key = decrypt_string(supplier.api_key)
        except Exception as e:
            # 如果解密失败，记录错误但不中断请求
            import logging
            logging.error(f"解密供应商 {supplier.id} 的API密钥失败 (重新加载检查): {str(e)}")
            supplier.api_key = None
    
    return supplier


@router.put("/suppliers/{supplier_id}")
async def update_model_supplier(
    supplier_id: int,
    request: Request,
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
    try:
        # 检查供应商是否存在
        result = db.execute(text("SELECT id FROM suppliers WHERE id = :supplier_id"), {
            "supplier_id": supplier_id
        })
        if result.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="供应商不存在"
            )
        
        # 获取Content-Type
        content_type = request.headers.get("Content-Type", "")
        logger.info(f"[更新供应商] Content-Type: {content_type}")
        
        # 初始化更新数据
        update_data = {
            "supplier_id": supplier_id,
            "updated_at": datetime.utcnow()
        }
        
        # 处理logo上传
        logo_path = None
        
        # 处理JSON格式请求
        if "application/json" in content_type:
            # 解析JSON数据
            try:
                json_data = await request.json()
                logger.info(f"[更新供应商] JSON数据: {json_data}")
                
                # 检查名称是否重复
                if "name" in json_data and json_data["name"] is not None:
                    result = db.execute(text("SELECT id FROM suppliers WHERE name = :name AND id != :supplier_id"), {
                        "name": json_data["name"],
                        "supplier_id": supplier_id
                    })
                    if result.fetchone() is not None:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="供应商名称已存在"
                        )
                
                # 构建更新数据
                if "name" in json_data and json_data["name"] is not None:
                    update_data["name"] = json_data["name"]
                if "description" in json_data and json_data["description"] is not None:
                    update_data["description"] = json_data["description"]
                if "api_endpoint" in json_data and json_data["api_endpoint"] is not None:
                    update_data["api_endpoint"] = json_data["api_endpoint"]
                if "api_key_required" in json_data:
                    update_data["api_key_required"] = json_data["api_key_required"]
                if "is_active" in json_data:
                    update_data["is_active"] = json_data["is_active"]
                if "category" in json_data and json_data["category"] is not None:
                    update_data["category"] = json_data["category"]
                if "website" in json_data and json_data["website"] is not None:
                    update_data["website"] = json_data["website"]
                if "api_docs" in json_data and json_data["api_docs"] is not None:
                    update_data["api_docs"] = json_data["api_docs"]
                if "api_key" in json_data and json_data["api_key"] is not None:
                    # 加密API密钥
                    update_data["api_key"] = encrypt_string(json_data["api_key"])
            except Exception as e:
                logger.error(f"[更新供应商] 解析JSON数据失败: {str(e)}")
                raise HTTPException(status_code=400, detail="无效的JSON数据")
        
        # 处理FormData格式请求
        else:
            # 检查名称是否重复
            if name is not None:
                result = db.execute(text("SELECT id FROM suppliers WHERE name = :name AND id != :supplier_id"), {
                    "name": name,
                    "supplier_id": supplier_id
                })
                if result.fetchone() is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="供应商名称已存在"
                    )
            
            # 处理logo上传
            if logo:
                # 如果有新的logo文件上传，保存它
                logo_path = await save_upload_file(logo)
                print(f"已更新logo为新上传的文件: {logo_path}")
            elif existing_logo is not None:
                # 如果提供了existing_logo，使用它
                logo_path = existing_logo
                print(f"保留现有logo: {logo_path}")
            
            # 构建更新数据
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if api_endpoint is not None:
                update_data["api_endpoint"] = api_endpoint
            if api_key_required is not None:
                update_data["api_key_required"] = api_key_required
            if is_active is not None:
                update_data["is_active"] = is_active
            if category is not None:
                update_data["category"] = category
            if website is not None:
                update_data["website"] = website
            if api_docs is not None:
                update_data["api_docs"] = api_docs
            if logo_path is not None:
                update_data["logo"] = logo_path
            if api_key is not None:
                # 加密API密钥
                update_data["api_key"] = encrypt_string(api_key)
        
        # 构建更新SQL语句
        set_clause = ", ".join([f"{key} = :{key}" for key in update_data.keys() if key != "supplier_id"])
        update_query = text(f"UPDATE suppliers SET {set_clause} WHERE id = :supplier_id")
        
        # 执行更新
        db.execute(update_query, update_data)
        
        # 查询更新后的供应商信息
        result = db.execute(text("""
            SELECT id, name, description, api_endpoint, api_key_required, 
                   is_active, logo, category, website, api_docs, api_key, 
                   created_at, updated_at
            FROM suppliers WHERE id = :supplier_id
        """), {"supplier_id": supplier_id})
        supplier = result.fetchone()
        
        db.commit()
        
        # 检查供应商是否存在
        if supplier is None:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        # 返回响应 - 使用name作为display_name，确保API密钥是解密后的
        decrypted_api_key = None
        if supplier.api_key_required and supplier.api_key:
            try:
                decrypted_api_key = decrypt_string(supplier.api_key)
            except Exception as e:
                import logging
                logging.error(f"解密供应商API密钥失败: {str(e)}")
        
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
            "api_key": decrypted_api_key,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新供应商失败: {str(e)}"
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
    
    # 检查是否有相关模型 - 使用查询方式避免直接访问关系属性
    from app.models.supplier_db import ModelDB
    model_count = db.query(ModelDB).filter(ModelDB.supplier_id == supplier_id).count()
    if model_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除包含模型的供应商，请先删除相关模型"
        )
    
    # 使用原始SQL删除供应商记录，避免ORM关系映射问题
    from sqlalchemy import text
    db.execute(text("DELETE FROM suppliers WHERE id = :id"), {"id": supplier_id})
    db.commit()


import requests
from fastapi import Body, HTTPException, status
from pydantic import BaseModel

# 定义API测试请求体的Pydantic模型
class TestApiConfigRequest(BaseModel):
    api_endpoint: str | None = None
    api_key: str | None = None

@router.post("/suppliers/{supplier_id}/test-api")
async def test_supplier_api_config(
    supplier_id: int,
    request_data: TestApiConfigRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    # 添加调试信息
    logger.info(f"接收到的请求体: {request_data}")
    
    # 首先验证供应商是否存在并获取供应商信息
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        logger.error(f"供应商不存在: supplier_id={supplier_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    # 始终使用数据库中的API端点
    api_endpoint = supplier.api_endpoint
    
    # 验证数据库中的API端点是否存在且有效
    if not api_endpoint:
        logger.error(f"数据库中的API端点不能为空。供应商ID: {supplier_id}, 供应商名称: {supplier.name}")
        return {
            "status": "error",
            "message": "数据库中的API端点不能为空",
            "status_code": 0,
            "response_text": ""
        }
    
    # 验证API端点格式是否正确（必须包含http://或https://）
    if not (api_endpoint.startswith('http://') or api_endpoint.startswith('https://')):
        logger.error(f"API端点格式不正确，必须包含http://或https://。数据库中的api_endpoint: {api_endpoint}")
        return {
            "status": "error",
            "message": f"API端点格式不正确，必须包含http://或https://。当前配置: {api_endpoint}",
            "status_code": 0,
            "response_text": ""
        }
    
    # 从请求体中获取API密钥
    api_key = request_data.api_key
    
    """
    测试供应商API配置
    
    Args:
        supplier_id: 供应商ID
        api_endpoint: API端点（始终使用数据库中的值）
        api_key: API密钥（来自请求体）
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        测试结果
    """
    try:
        # 添加更多调试信息
        logger.info(f"测试API配置: supplier_id={supplier_id}, supplier_name={supplier.name}, api_endpoint={api_endpoint}, api_key_provided={api_key is not None}")
        
        # 构建测试请求
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 根据供应商类型使用不同的测试端点
        test_endpoint = api_endpoint
        # 为不同供应商添加特定端点处理
        if supplier.name in ["深度求索", "deepseek", "硅基流动", "siliconflow"]:
            # 这些API需要使用具体的路径
            if not test_endpoint.endswith("/"):
                test_endpoint += "/"
            # 确保路径包含v1版本
            if not test_endpoint.endswith("v1/"):
                test_endpoint += "v1/"
            # 使用models端点进行测试
            test_endpoint += "models"
        elif supplier.name.lower() == "ollama":
            # Ollama API需要使用特定的路径
            if not test_endpoint.endswith("/"):
                test_endpoint += "/"
            # Ollama API路径格式为 /api/tags（用于列出模型）
            if not test_endpoint.endswith("api/"):
                test_endpoint += "api/"
            test_endpoint += "tags"
            # Ollama通常不需要API密钥，移除Authorization头
            if "Authorization" in headers:
                del headers["Authorization"]
        
        logger.info(f"发送请求: URL={test_endpoint}, Headers={headers}")
        
        # 发送测试请求
        response = requests.get(test_endpoint, headers=headers, timeout=10)
        
        logger.info(f"收到响应: Status={response.status_code}, Content-Type={response.headers.get('content-type')}")
        
        # 检查响应
        if response.status_code == 200:
            return {
                "status": "success",
                "message": "API配置测试成功！",
                "status_code": response.status_code,
                "response_text": response.text[:500]  # 只返回前500个字符
            }
        else:
            error_msg = f"API配置测试失败！服务器返回状态码: {response.status_code}"
            logger.error(f"响应错误: {error_msg}, Response={response.text[:200]}...")
            # 直接返回错误响应，而不是抛出HTTPException
            return {
                "status": "error",
                "message": error_msg,
                "status_code": response.status_code,
                "response_text": response.text[:500]
            }
    except requests.exceptions.ConnectionError as e:
        error_msg = "无法连接到API端点，请检查地址是否正确。"
        logger.error(f"连接错误: {error_msg}, Exception={str(e)}")
        return {
            "status": "error",
            "message": error_msg,
            "status_code": 0,
            "response_text": str(e)
        }
    except requests.exceptions.Timeout as e:
        error_msg = "API请求超时，请检查网络连接和API端点。"
        logger.error(f"超时错误: {error_msg}, Exception={str(e)}")
        return {
            "status": "error",
            "message": error_msg,
            "status_code": 0,
            "response_text": str(e)
        }
    except Exception as e:
        # 捕获所有其他异常，提供更详细的错误信息
        error_msg = f"测试API配置时发生错误：{str(e)}"
        logger.error(f"未捕获的异常: {error_msg}, 异常类型: {type(e).__name__}")
        return {
            "status": "error",
            "message": error_msg,
            "status_code": 0,
            "response_text": str(e)
        }

# 模型管理相关路由
@router.post("/suppliers/{supplier_id}/models", response_model=ModelResponse)
async def create_model(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    为指定供应商创建新模型，支持LOGO上传
    
    Args:
        supplier_id: 供应商ID
        request: 请求对象，用于处理文件上传
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
    
    try:
        form_data = await request.form()
        
        # 解析JSON数据
        model_json = form_data.get('model_data')
        if not model_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少模型数据"
            )
            
        model_data = json.loads(model_json)
        
        # 确保supplier_id一致
        model_data['supplier_id'] = supplier_id
        
        # 处理LOGO上传
        logo_file = form_data.get('logo')
        if logo_file and logo_file.filename:
            # 验证文件类型
            if not allowed_file(logo_file.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不支持的文件类型，仅支持 PNG, JPG, JPEG, GIF, WEBP 格式"
                )
            
            # 保存LOGO文件
            logo_filename = await save_upload_file(logo_file)
            model_data['logo'] = logo_filename
        
        # 处理模型类型：将前端发送的model_type（分类ID）转换为model_type_id
        if 'model_type' in model_data:
            try:
                # 尝试将model_type转换为整数（分类ID）
                category_id = int(model_data['model_type'])
                # 验证分类是否存在
                category = db.query(ModelCategory).filter(ModelCategory.id == category_id).first()
                if category:
                    # 使用分类ID作为model_type_id
                    model_data['model_type_id'] = category_id
                else:
                    # 如果分类不存在，设为None
                    model_data['model_type_id'] = None
                # 删除原来的model_type字段
                del model_data['model_type']
            except ValueError:
                # 如果无法转换为整数，设为None
                model_data['model_type_id'] = None
                del model_data['model_type']
        
        # 创建新模型
        db_model = ModelDB(**model_data)
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
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的JSON格式"
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
    获取指定供应商的所有模型
    
    Args:
        supplier_id: 供应商ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型列表
    """
    # 从数据库中查询指定供应商的模型，预加载categories和model_type关系
    from sqlalchemy.orm import joinedload
    models = db.query(Model).options(
        joinedload(Model.categories),
        joinedload(Model.model_type)
    ).filter(Model.supplier_id == supplier_id).offset(skip).limit(limit).all()
    total = db.query(Model).filter(Model.supplier_id == supplier_id).count()
    
    # 手动构建模型响应数据，填充完整的模型分类信息
    model_responses = []
    for model in models:
        model_data = ModelResponse.from_orm(model)
        
        # 如果模型有模型类型，填充完整的分类信息
        if model.model_type:
            model_data.model_type_name = model.model_type.name  # 英文名称
            model_data.model_type_display_name = model.model_type.display_name  # 中文显示名称
            model_data.model_type_logo = model.model_type.logo  # logo
        
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
    # 预加载model_type关系
    from sqlalchemy.orm import joinedload
    model = db.query(Model).options(joinedload(Model.model_type)).filter(
        Model.id == model_id,
        Model.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 手动构建模型响应数据，填充完整的模型分类信息
    model_data = ModelResponse.from_orm(model)
    
    # 如果模型有模型类型，填充完整的分类信息
    if model.model_type:
        model_data.model_type_name = model.model_type.name  # 英文名称
        model_data.model_type_display_name = model.model_type.display_name  # 中文显示名称
        model_data.model_type_logo = model.model_type.logo  # logo
    
    return model_data


from fastapi import Request
import json

@router.put("/suppliers/{supplier_id}/models/{model_id}", response_model=ModelResponse)
async def update_model(
    supplier_id: int,
    model_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新指定供应商的模型信息，支持LOGO上传
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        request: 请求对象，用于处理文件上传
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        更新后的模型信息
    """
    # 验证供应商是否存在
    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    # 验证模型是否存在且属于该供应商
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.supplier_id == supplier_id
    ).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    try:
        content_type = request.headers.get('content-type')
        
        if content_type and 'multipart/form-data' in content_type:
            # 处理包含文件上传的请求
            form_data = await request.form()
            
            # 解析JSON数据
            model_json = form_data.get('model_data')
            if not model_json:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="缺少模型数据"
                )
                
            update_data = json.loads(model_json)
            
            # 处理LOGO上传
            logo_file = form_data.get('logo')
            if logo_file and logo_file.filename:
                # 保存LOGO文件
                logo_filename = await save_upload_file(logo_file)
                update_data['logo'] = logo_filename
            elif 'logo' in update_data and update_data['logo'] is None:
                # 如果明确设置logo为None，则删除logo
                update_data['logo'] = None
        else:
            # 处理普通JSON请求
            update_data = await request.json()
        
        # 如果设置了is_default为True，将其他模型的is_default设置为False
        if 'is_default' in update_data and update_data['is_default'] is True:
            db.query(Model).filter(
                Model.supplier_id == supplier_id,
                Model.id != model_id
            ).update({Model.is_default: False})
        
        # 处理模型类型字段
        if 'model_type' in update_data:
            # 获取或创建模型分类
            model_category = db.query(ModelCategory).filter(
                ModelCategory.name == update_data['model_type']
            ).first()
            if model_category:
                update_data['model_type_id'] = model_category.id
            # 删除原来的model_type字段
            del update_data['model_type']
        elif 'model_type_id' in update_data:
            # 验证模型分类是否存在
            model_category = db.query(ModelCategory).filter(
                ModelCategory.id == update_data['model_type_id']
            ).first()
            if not model_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model category with id {update_data['model_type_id']} not found"
                )
        
        # 更新模型
        for field, value in update_data.items():
            setattr(model, field, value)
        
        db.commit()
        db.refresh(model)
        return model
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新模型失败，请检查输入数据"
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的JSON格式"
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


@router.get("/models", response_model=ModelListResponse)
async def get_all_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取所有模型（通用接口）
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        所有模型列表
    """
    # 查询数据库获取所有模型数据，包括供应商和分类信息
    from sqlalchemy.orm import joinedload
    models = db.query(ModelDB).options(joinedload(ModelDB.supplier), joinedload(ModelDB.categories)).offset(skip).limit(limit).all()
    total = db.query(ModelDB).count()
    
    # 将ModelDB实例转换为ModelResponse实例
    model_responses = [ModelResponse.from_orm(model) for model in models]
    
    return ModelListResponse(
        models=model_responses,
        total=total
    )


# 参数管理相关接口
@router.get("/suppliers/{supplier_id}/models/{model_id}/parameters")
async def get_model_parameters(
    supplier_id: int,
    model_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取模型的完整参数配置，包括继承的模型类型参数和模型自身的参数
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型的完整参数配置
    """
    print(f"[模块] 调用get_model_parameters: supplier_id={supplier_id}, model_id={model_id}")
    # 验证供应商和模型是否存在且关联
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    
    if not model:
        print(f"[模块] 模型不存在或不属于该供应商: supplier_id={supplier_id}, model_id={model_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在或不属于该供应商"
        )
    
    # 使用参数管理服务获取完整参数配置
    parameters = ParameterManager.get_model_parameters(db, model_id)
    
    return {
        "model_id": model_id,
        "supplier_id": supplier_id,
        "parameters": parameters
    }


@router.put("/suppliers/{supplier_id}/models/{model_id}/parameters")
async def update_model_parameters(
    supplier_id: int,
    model_id: int,
    parameters: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新模型的参数配置
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        parameters: 要更新的参数配置
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        更新后的参数配置
    """
    # 验证供应商和模型是否存在且关联
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在或不属于该供应商"
        )
    
    # 使用参数管理服务更新模型参数
    updated_parameters = ParameterManager.update_model_parameters(db, model_id, parameters)
    
    return {
        "model_id": model_id,
        "supplier_id": supplier_id,
        "parameters": updated_parameters,
        "message": "参数更新成功"
    }


@router.get("/categories/{category_id}/default-parameters")
async def get_model_type_default_parameters(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取模型类型（分类）的默认参数配置
    
    Args:
        category_id: 模型类型ID
        db: 数据库会话
        current_user: 当前活跃的超级用户
    
    Returns:
        模型类型的默认参数配置
    """
    # 验证模型类型是否存在
    category = db.query(ModelCategory).filter(ModelCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型类型不存在"
        )
    
    # 获取模型类型的默认参数
    default_params = category.default_parameters or {}
    
    return {
        "category_id": category_id,
        "category_name": category.name,
        "default_parameters": default_params
    }