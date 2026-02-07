"""默认模型管理API接口"""
from typing import Any, List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
import logging

from app.core.dependencies import get_db
from app.core.permission_dependencies import (
    get_current_active_user, get_current_active_superuser,
    require_superuser_permission, require_verified_user
)
from app.models.default_model import DefaultModel, ModelFeedback, ModelPerformance
from app.models.supplier_db import ModelDB
from app.services.default_model_cache_service import DefaultModelCacheService
from app.schemas.default_model import (
    DefaultModelCreate, DefaultModelUpdate, DefaultModelResponse,
    DefaultModelListResponse,
    SetGlobalDefaultRequest, SetSceneDefaultRequest,
    RecommendModelRequest, ModelRecommendationResponse
)
from app.schemas.model_management import ModelResponse

# 创建路由器
router = APIRouter()

# 获取默认模型列表
@router.get("/default-models", response_model=DefaultModelListResponse)
async def get_default_models(
    scope: Optional[str] = Query(None, description="过滤作用域：'global' 或 'scene'"),
    scene: Optional[str] = Query(None, description="场景名称，当scope为'scene'时使用"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(100, description="返回记录数限制"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取所有默认模型配置
    
    Args:
        scope: 过滤作用域，可选值为"global"或"scene"
        scene: 场景名称，当scope为"scene"时使用
        is_active: 是否激活
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        默认模型配置列表
    """
    query = db.query(DefaultModel)
    
    # 应用过滤条件
    if scope:
        query = query.filter(DefaultModel.scope == scope)
    if scene:
        query = query.filter(DefaultModel.scene == scene)
    if is_active is not None:
        query = query.filter(DefaultModel.is_active == is_active)
    
    # 执行查询
    total = query.count()
    default_models = query.offset(skip).limit(limit).all()
    
    return DefaultModelListResponse(
        items=default_models,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

# 获取全局默认模型
@router.get("/default-models/global", response_model=Optional[DefaultModelResponse])
async def get_global_default_model(db: Session = Depends(get_db)) -> Any:
    """
    获取全局默认模型
    
    Args:
        db: 数据库会话
    
    Returns:
        全局默认模型配置，如果没有设置则返回None
    """
    # 从数据库查询
    default_model = db.query(DefaultModel).filter(
        DefaultModel.scope == 'global',
        DefaultModel.is_active == True
    ).first()
    
    return default_model

# 获取指定场景的默认模型
@router.get("/default-models/scene/{scene}", response_model=Optional[DefaultModelResponse])
async def get_scene_default_model(
    scene: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取指定场景的默认模型
    
    Args:
        scene: 场景名称
        db: 数据库会话
    
    Returns:
        场景默认模型配置，如果没有设置则返回None
    """
    # 从数据库查询
    default_model = db.query(DefaultModel).filter(
        DefaultModel.scope == 'scene',
        DefaultModel.scene == scene,
        DefaultModel.is_active == True
    ).first()
    
    return default_model

# 设置全局默认模型
@router.post("/default-models/set-global", response_model=DefaultModelResponse)
async def set_global_default_model(
    request: SetGlobalDefaultRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    设置全局默认模型
    
    Args:
        request: 设置全局默认模型请求
        db: 数据库会话
    
    Returns:
        设置后的全局默认模型配置
    """
    # 验证模型ID是否存在
    model = db.query(ModelDB).filter(ModelDB.id == request.model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型 ID {request.model_id} 不存在"
        )
    
    # 如果提供了fallback_model_id，验证其是否存在
    if request.fallback_model_id:
        fallback_model = db.query(ModelDB).filter(ModelDB.id == request.fallback_model_id).first()
        if not fallback_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"备选模型 ID {request.fallback_model_id} 不存在"
            )
    
    # 先停用现有的全局默认模型
    db.query(DefaultModel).filter(
        DefaultModel.scope == 'global'
    ).update({'is_active': False})
    
    # 创建新的全局默认模型
    new_default_model = DefaultModel(
        scope='global',
        scene=None,
        model_id=request.model_id,
        priority=1,
        fallback_model_id=request.fallback_model_id,
        is_active=True
    )
    
    db.add(new_default_model)
    db.commit()
    db.refresh(new_default_model)
    
    # 更新缓存
    DefaultModelCacheService.invalidate_default_model_cache("global")
    DefaultModelCacheService.cache_global_default_models([new_default_model])
    
    return new_default_model

# 设置场景默认模型
@router.post("/default-models/set-scene", response_model=DefaultModelResponse)
async def set_scene_default_model(
    request: SetSceneDefaultRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    设置场景默认模型
    
    Args:
        request: 设置场景默认模型请求
        db: 数据库会话
    
    Returns:
        设置后的场景默认模型配置
    """
    # 验证模型ID是否存在
    model = db.query(ModelDB).filter(ModelDB.id == request.model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型 ID {request.model_id} 不存在"
        )
    
    # 如果提供了fallback_model_id，验证其是否存在
    if request.fallback_model_id:
        fallback_model = db.query(ModelDB).filter(ModelDB.id == request.fallback_model_id).first()
        if not fallback_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"备选模型 ID {request.fallback_model_id} 不存在"
            )
    
    # 检查是否已存在该场景的默认模型
    existing_default_model = db.query(DefaultModel).filter(
        and_(
            DefaultModel.scope == 'scene',
            DefaultModel.scene == request.scene
        )
    ).first()
    
    if existing_default_model:
        # 更新现有记录
        existing_default_model.model_id = request.model_id
        existing_default_model.priority = request.priority if request.priority else 1
        existing_default_model.fallback_model_id = request.fallback_model_id
        existing_default_model.is_active = True
        existing_default_model.updated_at = datetime.now()
        
        db.commit()
        db.refresh(existing_default_model)
        
        return existing_default_model
    else:
        # 创建新的场景默认模型
        new_default_model = DefaultModel(
            scope='scene',
            scene=request.scene,
            model_id=request.model_id,
            priority=request.priority if request.priority else 1,
            fallback_model_id=request.fallback_model_id,
            is_active=True
        )
        
        db.add(new_default_model)
        db.commit()
        db.refresh(new_default_model)
        
        return new_default_model

# 创建默认模型配置
@router.post("/default-models", response_model=DefaultModelResponse)
async def create_default_model(
    request: DefaultModelCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    创建新的默认模型配置
    
    Args:
        request: 创建默认模型请求
        db: 数据库会话
    
    Returns:
        创建的默认模型配置
    """
    # 验证模型ID是否存在
    model = db.query(ModelDB).filter(ModelDB.id == request.model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型 ID {request.model_id} 不存在"
        )
    
    # 如果提供了fallback_model_id，验证其是否存在
    if request.fallback_model_id:
        fallback_model = db.query(ModelDB).filter(ModelDB.id == request.fallback_model_id).first()
        if not fallback_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"备选模型 ID {request.fallback_model_id} 不存在"
            )
    
    # 创建默认模型
    default_model = DefaultModel(
        scope=request.scope,
        scene=request.scene,
        model_id=request.model_id,
        priority=request.priority if request.priority else 1,
        fallback_model_id=request.fallback_model_id,
        is_active=request.is_active if request.is_active is not None else True
    )
    
    db.add(default_model)
    db.commit()
    db.refresh(default_model)
    
    return default_model

# 更新默认模型配置
@router.put("/default-models/{default_model_id}", response_model=DefaultModelResponse)
async def update_default_model(
    default_model_id: int,
    request: DefaultModelUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    更新指定的默认模型配置
    
    Args:
        default_model_id: 默认模型配置ID
        request: 更新默认模型请求
        db: 数据库会话
    
    Returns:
        更新后的默认模型配置
    """
    # 获取现有默认模型
    default_model = db.query(DefaultModel).filter(DefaultModel.id == default_model_id).first()
    if not default_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"默认模型配置 ID {default_model_id} 不存在"
        )
    
    # 验证模型ID是否存在
    if request.model_id:
        model = db.query(ModelDB).filter(ModelDB.id == request.model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {request.model_id} 不存在"
            )
    
    # 如果提供了fallback_model_id，验证其是否存在
    if request.fallback_model_id:
        fallback_model = db.query(ModelDB).filter(ModelDB.id == request.fallback_model_id).first()
        if not fallback_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"备选模型 ID {request.fallback_model_id} 不存在"
            )
    
    # 更新字段
    if request.scope is not None:
        default_model.scope = request.scope
    if request.scene is not None:
        default_model.scene = request.scene
    if request.model_id is not None:
        default_model.model_id = request.model_id
    if request.priority is not None:
        default_model.priority = request.priority
    if request.fallback_model_id is not None:
        default_model.fallback_model_id = request.fallback_model_id
    if request.is_active is not None:
        default_model.is_active = request.is_active
    
    db.commit()
    db.refresh(default_model)
    
    return default_model

# 删除默认模型配置
@router.delete("/default-models/{default_model_id}")
async def delete_default_model(
    default_model_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    删除指定的默认模型配置
    
    Args:
        default_model_id: 默认模型配置ID
        db: 数据库会话
    
    Returns:
        删除成功响应
    """
    # 获取现有默认模型
    default_model = db.query(DefaultModel).filter(DefaultModel.id == default_model_id).first()
    if not default_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"默认模型配置 ID {default_model_id} 不存在"
        )
    
    # 执行软删除（设置is_active为False）
    default_model.is_active = False
    db.commit()
    
    return {"message": "默认模型配置删除成功"}

# 获取推荐的默认模型
@router.get("/default-models/recommend", response_model=List[ModelResponse])
async def recommend_default_models(
    scene: str = Query(..., description="场景名称"),
    model_type: Optional[str] = Query(None, description="模型类型，用于过滤"),
    db: Session = Depends(get_db)
) -> Any:
    """
    根据场景获取推荐的默认模型
    
    Args:
        scene: 场景名称
        model_type: 模型类型，用于过滤
        db: 数据库会话
    
    Returns:
        推荐的模型列表
    """
    # 获取场景默认模型
    scene_default = db.query(DefaultModel).filter(
        DefaultModel.scope == 'scene',
        DefaultModel.scene == scene,
        DefaultModel.is_active == True
    ).first()
    
    # 如果有场景默认模型，返回其关联的模型
    if scene_default:
        model = db.query(ModelDB).filter(ModelDB.id == scene_default.model_id).first()
        if model and model.is_active:
            # 如果指定了模型类型，验证匹配
            if model_type and model.model_type_id:
                from app.models.model_category import ModelCategory
                category = db.query(ModelCategory).filter(ModelCategory.id == model.model_type_id).first()
                if category and category.name.lower() != model_type.lower():
                    # 如果类型不匹配，返回全局默认模型
                    scene_default = None
    
    # 如果没有场景默认模型或类型不匹配，使用全局默认模型
    if not scene_default:
        global_default = db.query(DefaultModel).filter(
            DefaultModel.scope == 'global',
            DefaultModel.is_active == True
        ).first()
        
        if global_default:
            model = db.query(ModelDB).filter(ModelDB.id == global_default.model_id).first()
            if model and model.is_active:
                scene_default = global_default
    
    # 如果仍然没有默认模型，返回空列表
    if not scene_default:
        return []
    
    # 获取推荐模型
    recommended_model = db.query(ModelDB).filter(ModelDB.id == scene_default.model_id).first()
    
    # 如果指定了模型类型，尝试查找更多候选模型
    if model_type and recommended_model:
        from app.models.model_category import ModelCategory
        
        # 查找匹配的模型类型
        category = db.query(ModelCategory).filter(
            ModelCategory.name.ilike(f"%{model_type}%")
        ).first()
        
        if category:
            # 查找相同类型的其他模型
            similar_models = db.query(ModelDB).filter(
                ModelDB.model_type_id == category.id,
                ModelDB.id != recommended_model.id,
                ModelDB.is_active == True
            ).limit(3).all()
            
            # 添加备选模型（如果有）
            fallback_models = []
            if scene_default.fallback_model_id:
                fallback_model = db.query(ModelDB).filter(
                    ModelDB.id == scene_default.fallback_model_id,
                    ModelDB.is_active == True
                ).first()
                if fallback_model:
                    fallback_models.append(fallback_model)
            
            # 返回所有候选模型
            return [recommended_model] + fallback_models + similar_models
    
    # 如果指定了模型类型但找不到匹配的分类，返回主推荐模型
    if model_type and recommended_model:
        return [recommended_model]
    
    # 如果没有指定模型类型，返回主推荐模型和备选模型（如果有）
    result = [recommended_model]
    if scene_default.fallback_model_id:
        fallback_model = db.query(ModelDB).filter(
            ModelDB.id == scene_default.fallback_model_id,
            ModelDB.is_active == True
        ).first()
        if fallback_model:
            result.append(fallback_model)
    
    return result


# 获取本地模型配置
@router.get("/default-models/local", response_model=Optional[DefaultModelResponse])
async def get_local_model_config(
    db: Session = Depends(get_db)
) -> Any:
    """
    获取本地模型配置
    
    Args:
        db: 数据库会话
    
    Returns:
        本地模型配置，如果没有设置则返回None
    """
    # 从数据库查询本地模型配置
    local_model_config = db.query(DefaultModel).filter(
        DefaultModel.scope == 'local',
        DefaultModel.is_active == True
    ).first()
    
    return local_model_config


# 设置本地模型配置
@router.post("/default-models/set-local", response_model=DefaultModelResponse)
async def set_local_model_config(
    request: SetGlobalDefaultRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser_permission)
) -> Any:
    """
    设置本地模型配置
    
    Args:
        request: 设置本地模型配置请求
        db: 数据库会话
    
    Returns:
        设置后的本地模型配置
    """
    # 验证模型ID是否存在
    model = db.query(ModelDB).filter(ModelDB.id == request.model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型 ID {request.model_id} 不存在"
        )
    
    # 先停用现有的本地模型配置
    db.query(DefaultModel).filter(
        DefaultModel.scope == 'local'
    ).update({'is_active': False})
    
    # 创建新的本地模型配置
    new_local_config = DefaultModel(
        scope='local',
        scene=None,
        model_id=request.model_id,
        priority=1,
        fallback_model_id=request.fallback_model_id,
        is_active=True
    )
    
    db.add(new_local_config)
    db.commit()
    db.refresh(new_local_config)
    
    return new_local_config