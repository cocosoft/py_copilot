"""参数模板相关API接口"""
from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.models.parameter_template import ParameterTemplate
from app.schemas.parameter_template import (
    ParameterTemplateCreate,
    ParameterTemplateUpdate,
    ParameterTemplateResponse,
    ParameterTemplateListResponse,
    MergedParametersResponse,
    ParameterTemplateLinkRequest,
    ParameterTemplateLinkResponse
)

from app.services.parameter_management.parameter_manager import ParameterManager
from app.services.parameter_management.parameter_normalizer import ParameterNormalizer

# 创建模拟用户类用于测试
class MockUser:
    def __init__(self):
        self.id = 1
        self.is_active = True
        self.is_superuser = True

def get_mock_user():
    return MockUser()

router = APIRouter()
parameter_templates_router = router


# 参数模板CRUD接口
@router.post("/parameter-templates", response_model=ParameterTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_parameter_template(
    template_data: ParameterTemplateCreate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    创建参数模板
    
    Args:
        template_data: 参数模板创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的参数模板信息
    """
    # 验证参数模板的有效性
    try:
        ParameterManager.validate_parameters(template_data.parameters)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"参数验证失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"参数处理失败: {str(e)}"
        )
    
    # 创建新参数模板
    try:
        db_template = ParameterTemplate(**template_data.model_dump())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建参数模板失败，请检查输入数据: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        import traceback
        print(f"创建参数模板时发生异常: {str(e)}")
        print(f"异常堆栈: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.get("/parameter-templates", response_model=ParameterTemplateListResponse)
def get_parameter_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取参数模板列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        参数模板列表
    """
    query = db.query(ParameterTemplate)
    
    templates = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return ParameterTemplateListResponse(
        templates=templates,
        total=total
    )


@router.get("/parameter-templates/{template_id}", response_model=ParameterTemplateResponse)
def get_parameter_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取单个参数模板
    
    Args:
        template_id: 参数模板ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        参数模板信息
    """
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数模板不存在"
        )
    return template


@router.put("/parameter-templates/{template_id}", response_model=ParameterTemplateResponse)
def update_parameter_template(
    template_id: int,
    template_data: ParameterTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    更新参数模板
    
    Args:
        template_id: 参数模板ID
        template_data: 参数模板更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的参数模板信息
    """
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数模板不存在"
        )
    
    # 更新模板字段
    update_data = template_data.model_dump(exclude_unset=True)
    
    # 如果更新了参数列表，需要验证参数的有效性
    if 'parameters' in update_data:
        try:
            ParameterManager.validate_parameters(update_data['parameters'])
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"参数验证失败: {str(e)}"
            )
    
    for field, value in update_data.items():
        setattr(template, field, value)
    
    try:
        db.commit()
        db.refresh(template)
        return template
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新参数模板失败，请检查输入数据"
        )


@router.delete("/parameter-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parameter_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> None:
    """
    删除参数模板
    
    Args:
        template_id: 参数模板ID
        db: 数据库会话
        current_user: 当前用户
    """
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数模板不存在"
        )
    
    # 检查是否有模型关联该模板
    from app.models.supplier_db import ModelDB
    associated_models = db.query(ModelDB).filter(ModelDB.parameter_template_id == template_id).count()
    if associated_models > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该模板已被模型使用，无法删除"
        )
    
    db.delete(template)
    db.commit()


@router.get("/parameter-templates/level/{level}", response_model=ParameterTemplateListResponse)
def get_parameter_templates_by_level(
    level: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取指定层级的所有参数模板
    
    Args:
        level: 模板层级（model_type|model|agent）
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        指定层级的参数模板列表
    """
    # 验证层级参数的有效性
    valid_levels = ["model_type", "model", "agent"]
    if level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的层级参数: {level}，有效值为: {', '.join(valid_levels)}"
        )
    
    query = db.query(ParameterTemplate).filter(ParameterTemplate.level == level)
    
    templates = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return ParameterTemplateListResponse(
        templates=templates,
        total=total
    )


@router.get("/parameter-templates/level/{level}/{level_id}", response_model=ParameterTemplateListResponse)
def get_parameter_templates_by_level_and_id(
    level: str,
    level_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取指定层级和ID的参数模板
    
    Args:
        level: 模板层级（model_type|model|agent）
        level_id: 层级特定ID（如模型类型ID、模型ID等）
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        指定层级和ID的参数模板列表
    """
    # 验证层级参数的有效性
    valid_levels = ["model_type", "model", "agent"]
    if level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的层级参数: {level}，有效值为: {', '.join(valid_levels)}"
        )
    
    query = db.query(ParameterTemplate).filter(
        ParameterTemplate.level == level,
        ParameterTemplate.level_id == level_id
    )
    
    templates = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return ParameterTemplateListResponse(
        templates=templates,
        total=total
    )


@router.get("/parameter-templates/{template_id}/merged-parameters", response_model=MergedParametersResponse)
def get_merged_parameters(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    获取合并后的参数配置
    
    Args:
        template_id: 参数模板ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        合并后的参数配置
    """
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="参数模板不存在"
        )
    
    # 使用ParameterManager中的统一实现获取合并参数
    merged_params = ParameterManager.get_merged_parameters(db, template_id)
    
    # 构建继承路径
    inheritance_path = []
    current_template = template
    while current_template:
        inheritance_path.insert(0, current_template.id)
        if current_template.parent_id:
            current_template = db.query(ParameterTemplate).filter(
                ParameterTemplate.id == current_template.parent_id
            ).first()
        else:
            # 检查是否有激活的系统模板
            system_template = db.query(ParameterTemplate).filter(
                ParameterTemplate.level == "system",
                ParameterTemplate.is_active == True
            ).first()
            if system_template:
                inheritance_path.insert(0, system_template.id)
            break
    
    return MergedParametersResponse(
        template_id=template_id,
        level=template.level,
        merged_parameters=merged_params,
        inheritance_path=inheritance_path
    )





@router.post("/suppliers/{supplier_id}/models/{model_id}/parameters/convert", response_model=Dict[str, Any])
def convert_model_parameters(
    supplier_id: int,
    model_id: int,
    raw_params: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    对模型参数进行转换处理
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        raw_params: 原始参数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        转换后的参数
    """
    from app.models.supplier_db import ModelDB
    
    # 验证模型是否存在
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        # 进行参数归一化
        normalized_params = ParameterManager.normalize_parameters(db, model_id, raw_params)
        
        return {
            "success": True,
            "model_id": model_id,
            "supplier_id": supplier_id,
            "normalized_parameters": normalized_params
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"归一化失败: {str(e)}"
        )


@router.post("/parameter-templates/{template_id}/apply-normalization", response_model=ParameterTemplateResponse)
def apply_normalization_to_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    对参数模板应用归一化规则
    
    Args:
        template_id: 参数模板ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的参数模板
    """
    try:
        # 应用归一化规则到模板
        updated_template = ParameterManager.apply_normalization_to_template(db, template_id)
        
        return updated_template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"应用归一化失败: {str(e)}"
        )


@router.post("/suppliers/{supplier_id}/models/{model_id}/denormalize-parameters", response_model=Dict[str, Any])
def denormalize_model_parameters(
    supplier_id: int,
    model_id: int,
    normalized_params: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    将归一化参数转换为供应商特定格式
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        normalized_params: 归一化参数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        供应商特定格式参数
    """
    from app.models.supplier_db import ModelDB
    
    # 验证模型是否存在
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        # 进行参数反归一化
        denormalized_params = ParameterManager.denormalize_parameters(db, model_id, normalized_params)
        
        return {
            "success": True,
            "model_id": model_id,
            "supplier_id": supplier_id,
            "denormalized_parameters": denormalized_params
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"反归一化失败: {str(e)}"
        )


class ModelParameterConversionRequest(BaseModel):
    """模型参数转换请求Schema"""
    parameters: Dict[str, Any]


class ModelParameterConversionResponse(BaseModel):
    """模型参数转换响应Schema"""
    success: bool
    normalized_parameters: Dict[str, Any]


@router.post("/suppliers/{supplier_id}/models/{model_id}/parameters/convert", response_model=ModelParameterConversionResponse)
def convert_model_parameters(
    supplier_id: int,
    model_id: int,
    request: ModelParameterConversionRequest,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    将供应商特定模型参数转换为标准参数
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        request: 参数转换请求数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        转换后的标准参数
    """
    from app.models.supplier_db import ModelDB
    
    # 验证模型是否存在
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        # 获取模型类型
        model_type = model.model_type
        
        # 调用参数归一化服务
        normalized_params = ParameterNormalizer.normalize_parameters(
            supplier_id=supplier_id,
            raw_params=request.parameters,
            model_type=model_type
        )
        
        return ModelParameterConversionResponse(
            success=True,
            normalized_parameters=normalized_params
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"参数转换失败: {str(e)}"
        )


@router.post("/suppliers/{supplier_id}/auto-convert-parameters", response_model=Dict[str, Any])
def auto_convert_parameters(
    supplier_id: int,
    conversion_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    自动转换参数格式
    
    Args:
        supplier_id: 供应商ID
        conversion_data: 转换数据，包含：
            - conversion_type: 转换类型（supplier_to_standard/standard_to_supplier）
            - model_type: 模型类型
            - source_params: 源参数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        转换后的参数
    """
    # 验证输入数据
    required_fields = ["conversion_type", "model_type", "source_params"]
    for field in required_fields:
        if field not in conversion_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必要字段: {field}"
            )
    
    conversion_type = conversion_data["conversion_type"]
    model_type = conversion_data["model_type"]
    source_params = conversion_data["source_params"]
    
    try:
        # 自动转换参数
        converted_params = ParameterManager.auto_convert_parameters(
            db=db,
            source_params=source_params,
            conversion_type=conversion_type,
            supplier_id=supplier_id,
            model_type=model_type
        )
        
        return {
            "success": True,
            "supplier_id": supplier_id,
            "model_type": model_type,
            "conversion_type": conversion_type,
            "converted_parameters": converted_params
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"参数转换失败: {str(e)}"
        )


@router.post("/suppliers/{supplier_id}/models/{model_id}/sync-parameters", response_model=Dict[str, Any])
def sync_model_parameters(
    supplier_id: int,
    model_id: int,
    sync_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: MockUser = Depends(get_mock_user)
) -> Any:
    """
    同步模型参数与参数模板
    
    Args:
        supplier_id: 供应商ID
        model_id: 模型ID
        sync_data: 同步数据（可选），包含：
            - template_id: 参数模板ID（可选，如果未提供则使用模型关联的模板）
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        同步结果
    """
    from app.models.supplier_db import ModelDB
    
    # 验证模型是否存在
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.supplier_id == supplier_id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    template_id = sync_data.get("template_id") if sync_data else None
    
    try:
        # 同步模型参数
        updated_model = ParameterManager.sync_model_parameters_with_template(
            db=db,
            model_id=model_id,
            template_id=template_id
        )
        
        return {
            "success": True,
            "model_id": model_id,
            "supplier_id": supplier_id,
            "template_id": updated_model.parameter_template_id,
            "message": "参数同步成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"参数同步失败: {str(e)}"
        )



