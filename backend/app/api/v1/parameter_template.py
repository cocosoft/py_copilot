"""参数模板API"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permission_dependencies import (
    get_current_active_user, get_current_active_superuser,
    require_superuser_permission, require_verified_user
)
from app.models.parameter_template import ParameterTemplate, ParameterTemplateVersion
from app.models.default_model import DefaultModel
from app.schemas.parameter_template import (
    ParameterTemplateResponse, ParameterTemplateCreate, ParameterTemplateUpdate, 
    ParameterTemplateListResponse, ParameterTemplateVersionResponse,
    ParameterTemplateVersionCreate, ParameterTemplateVersionListResponse
)
from app.services.default_model_cache_service import DefaultModelCacheService
from datetime import datetime


router = APIRouter()


@router.get("/parameter-templates", response_model=ParameterTemplateListResponse)
async def get_parameter_templates(
    scene: Optional[str] = Query(None, description="过滤场景"),
    is_active: Optional[bool] = Query(None, description="过滤是否激活"),
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(100, description="返回记录数限制"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取参数模板列表
    
    Args:
        scene: 过滤场景
        is_active: 过滤是否激活
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        参数模板列表
    """
    # 生成缓存键
    cache_key_suffix = f"list:{scene or 'all'}:{is_active is not None}:{skip}:{limit}"
    
    # 尝试从缓存获取
    cached_templates = DefaultModelCacheService.get_cached_parameter_templates_list(cache_key_suffix)
    
    if cached_templates:
        return cached_templates
    
    query = db.query(ParameterTemplate)
    
    # 应用过滤条件
    if scene:
        query = query.filter(ParameterTemplate.scene == scene)
    if is_active is not None:
        query = query.filter(ParameterTemplate.is_active == is_active)
    
    # 执行查询
    total = query.count()
    templates = query.offset(skip).limit(limit).all()
    
    response = ParameterTemplateListResponse(
        items=templates,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )
    
    # 缓存结果
    DefaultModelCacheService.cache_parameter_templates_list(response, cache_key_suffix)
    
    return response


@router.get("/parameter-templates/{template_id}", response_model=ParameterTemplateResponse)
async def get_parameter_template(
    template_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取指定ID的参数模板
    
    Args:
        template_id: 参数模板ID
        db: 数据库会话
    
    Returns:
        参数模板详情
    """
    # 尝试从缓存获取
    cached_template = DefaultModelCacheService.get_cached_parameter_template(template_id)
    
    if cached_template:
        return cached_template
    
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"参数模板 ID {template_id} 不存在"
        )
    
    # 缓存结果
    DefaultModelCacheService.cache_parameter_template(template)
    
    return template


@router.post("/parameter-templates", response_model=ParameterTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_parameter_template(
    request: ParameterTemplateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    创建参数模板
    
    Args:
        request: 创建参数模板请求
        db: 数据库会话
    
    Returns:
        创建的参数模板
    """
    # 如果设置为默认模板，先将同一场景的其他默认模板取消
    if request.is_default:
        db.query(ParameterTemplate).filter(
            ParameterTemplate.scene == request.scene,
            ParameterTemplate.is_default == True
        ).update({ParameterTemplate.is_default: False})
    
    # 创建新模板
    new_template = ParameterTemplate(
        name=request.name,
        description=request.description,
        scene=request.scene,
        parameters=request.parameters,
        is_default=request.is_default
    )
    
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    # 创建模板版本记录
    version = ParameterTemplateVersion(
        template_id=new_template.id,
        version=1,
        parameters=request.parameters,
        changelog="初始版本"
    )
    
    db.add(version)
    db.commit()
    
    # 使参数模板列表缓存失效
    DefaultModelCacheService.invalidate_parameter_templates_cache("list")
    # 缓存新创建的模板
    DefaultModelCacheService.cache_parameter_template(new_template)
    
    return new_template


@router.put("/parameter-templates/{template_id}", response_model=ParameterTemplateResponse)
async def update_parameter_template(
    template_id: int,
    request: ParameterTemplateUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    更新参数模板
    
    Args:
        template_id: 参数模板ID
        request: 更新参数模板请求
        db: 数据库会话
    
    Returns:
        更新后的参数模板
    """
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"参数模板 ID {template_id} 不存在"
        )
    
    # 如果设置为默认模板，先将同一场景的其他默认模板取消
    if request.is_default is not None and request.is_default and not template.is_default:
        db.query(ParameterTemplate).filter(
            ParameterTemplate.scene == template.scene,
            ParameterTemplate.is_default == True,
            ParameterTemplate.id != template_id
        ).update({ParameterTemplate.is_default: False})
    
    # 更新字段
    if request.name is not None:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.scene is not None:
        template.scene = request.scene
    if request.parameters is not None:
        # 如果参数发生变更，创建新版本
        if template.parameters != request.parameters:
            # 获取当前版本号
            last_version = db.query(ParameterTemplateVersion).filter(
                ParameterTemplateVersion.template_id == template_id
            ).order_by(ParameterTemplateVersion.version.desc()).first()
            
            new_version_num = last_version.version + 1 if last_version else 1
            
            # 创建新版本记录
            version = ParameterTemplateVersion(
                template_id=template_id,
                version=new_version_num,
                parameters=request.parameters,
                changelog=f"更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            db.add(version)
        
        template.parameters = request.parameters
    if request.is_default is not None:
        template.is_default = request.is_default
    if request.is_active is not None:
        template.is_active = request.is_active
    
    template.updated_at = datetime.now()
    
    db.commit()
    db.refresh(template)
    
    # 更新缓存
    DefaultModelCacheService.invalidate_parameter_template_cache(template_id)
    DefaultModelCacheService.invalidate_parameter_templates_cache("list")
    DefaultModelCacheService.cache_parameter_template(template)
    
    return template


@router.delete("/parameter-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parameter_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> None:
    """
    删除参数模板
    
    Args:
        template_id: 参数模板ID
        db: 数据库会话
    """
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"参数模板 ID {template_id} 不存在"
        )
    
    # 检查是否有默认模型引用了这个模板
    referenced_models = db.query(DefaultModel).filter(
        DefaultModel.parameter_template_id == template_id
    ).all()
    
    if referenced_models:
        # 清空引用，但不移除默认模型
        db.query(DefaultModel).filter(
            DefaultModel.parameter_template_id == template_id
        ).update({DefaultModel.parameter_template_id: None})
    
    db.delete(template)
    db.commit()
    
    # 使缓存失效
    DefaultModelCacheService.invalidate_parameter_template_cache(template_id)
    DefaultModelCacheService.invalidate_parameter_templates_cache("list")


@router.get("/parameter-templates/{template_id}/versions", response_model=ParameterTemplateVersionListResponse)
async def get_parameter_template_versions(
    template_id: int,
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(100, description="返回记录数限制"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取参数模板的版本历史
    
    Args:
        template_id: 参数模板ID
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        参数模板版本列表
    """
    # 生成缓存键
    cache_key_suffix = f"versions:{template_id}:{skip}:{limit}"
    
    # 尝试从缓存获取
    cached_versions = DefaultModelCacheService.get_cached_parameter_template_versions_list(cache_key_suffix)
    
    if cached_versions:
        return cached_versions
    
    # 检查模板是否存在
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"参数模板 ID {template_id} 不存在"
        )
    
    # 获取版本历史
    query = db.query(ParameterTemplateVersion).filter(
        ParameterTemplateVersion.template_id == template_id
    )
    
    total = query.count()
    versions = query.order_by(ParameterTemplateVersion.version.desc()).offset(skip).limit(limit).all()
    
    response = ParameterTemplateVersionListResponse(
        items=versions,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )
    
    # 缓存结果
    DefaultModelCacheService.cache_parameter_template_versions_list(response, cache_key_suffix)
    
    return response


@router.post("/parameter-templates/{template_id}/versions", response_model=ParameterTemplateVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_parameter_template_version(
    template_id: int,
    request: ParameterTemplateVersionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    创建参数模板新版本
    
    Args:
        template_id: 参数模板ID
        request: 创建参数模板版本请求
        db: 数据库会话
    
    Returns:
        创建的参数模板版本
    """
    # 检查模板是否存在
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"参数模板 ID {template_id} 不存在"
        )
    
    # 获取当前版本号
    last_version = db.query(ParameterTemplateVersion).filter(
        ParameterTemplateVersion.template_id == template_id
    ).order_by(ParameterTemplateVersion.version.desc()).first()
    
    new_version_num = last_version.version + 1 if last_version else 1
    
    # 创建新版本记录
    version = ParameterTemplateVersion(
        template_id=template_id,
        version=new_version_num,
        parameters=request.parameters,
        changelog=request.changelog
    )
    
    db.add(version)
    
    # 更新模板当前参数
    template.parameters = request.parameters
    template.updated_at = datetime.now()
    
    db.commit()
    db.refresh(version)
    
    # 更新缓存
    DefaultModelCacheService.invalidate_parameter_template_cache(template_id)
    DefaultModelCacheService.invalidate_parameter_templates_cache("versions")
    DefaultModelCacheService.cache_parameter_template(template)
    
    return version


@router.get("/parameter-templates/scenes", response_model=List[str])
async def get_parameter_template_scenes(
    db: Session = Depends(get_db)
) -> Any:
    """
    获取所有参数模板场景列表
    
    Args:
        db: 数据库会话
    
    Returns:
        参数模板场景列表
    """
    # 尝试从缓存获取
    cached_scenes = DefaultModelCacheService.get_cached_parameter_template_scenes()
    
    if cached_scenes:
        return cached_scenes
    
    scenes = db.query(ParameterTemplate.scene).distinct().all()
    result = [scene[0] for scene in scenes]
    
    # 缓存结果
    DefaultModelCacheService.cache_parameter_template_scenes(result)
    
    return result


@router.get("/parameter-templates/{template_id}/apply", response_model=Dict[str, Any])
async def apply_parameter_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    应用参数模板到默认模型
    
    Args:
        template_id: 参数模板ID
        db: 数据库会话
    
    Returns:
        应用结果
    """
    # 检查模板是否存在
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"参数模板 ID {template_id} 不存在"
        )
    
    # 获取默认模型
    default_models = db.query(DefaultModel).filter(
        DefaultModel.scene == template.scene
    ).all()
    
    if not default_models:
        return {
            "success": False,
            "message": f"场景 '{template.scene}' 没有找到默认模型"
        }
    
    # 将模板应用到默认模型
    for model in default_models:
        model.parameter_template_id = template_id
        model.updated_at = datetime.now()
    
    db.commit()
    
    # 使相关缓存失效
    DefaultModelCacheService.invalidate_default_model_cache("scene", template.scene)
    DefaultModelCacheService.invalidate_parameter_template_cache(template_id)
    
    return {
        "success": True,
        "message": f"参数模板 '{template.name}' 已成功应用到 {len(default_models)} 个默认模型",
        "applied_count": len(default_models)
    }