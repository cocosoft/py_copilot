"""维度层次关系API端点"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.dimension_hierarchy_service import DimensionHierarchyService

router = APIRouter()

# 请求和响应模型
class DimensionCategoryRequest(BaseModel):
    weight: int = 0
    association_type: str = 'primary'
    
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/hierarchy", 
           response_model=Dict[str, Any],
           responses={
               200: {"description": "成功获取维度层次结构"},
               500: {"description": "服务器内部错误", "model": ErrorResponse}
           })
async def get_dimension_hierarchy(db: Session = Depends(get_db)):
    """
    获取完整的维度层次结构
    
    Returns:
        包含所有维度、类型和模型关系的层次结构
    """
    try:
        hierarchy = DimensionHierarchyService.get_dimension_hierarchy(db)
        
        if not hierarchy or not hierarchy.get('dimensions'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到维度层次结构数据"
            )
            
        return hierarchy
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "dimension_hierarchy_error",
                "message": "获取维度层次结构失败",
                "details": {"error": str(e)}
            }
        )


@router.get("/dimensions/{dimension}/categories/{category_id}/models",
           response_model=Dict[str, Any],
           responses={
               200: {"description": "成功获取模型列表"},
               400: {"description": "请求参数错误", "model": ErrorResponse},
               404: {"description": "维度或分类不存在", "model": ErrorResponse},
               500: {"description": "服务器内部错误", "model": ErrorResponse}
           })
async def get_models_by_dimension_and_category(
    dimension: str = ...,
    category_id: int = ...,
    db: Session = Depends(get_db)
):
    """
    根据维度和分类获取模型列表
    
    Args:
        dimension: 维度标识
        category_id: 分类ID
        
    Returns:
        模型列表
    """
    # 参数验证
    valid_dimensions = ['tasks', 'languages', 'licenses', 'technologies']
    if dimension not in valid_dimensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_dimension",
                "message": f"无效的维度标识: {dimension}",
                "details": {"valid_dimensions": valid_dimensions}
            }
        )
    
    try:
        models = DimensionHierarchyService.get_models_by_dimension_and_category(
            db, dimension, category_id
        )
        
        if not models:
            return {"models": [], "message": "该分类下暂无模型"}
            
        return {"models": models, "count": len(models)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "category_not_found",
                "message": str(e),
                "details": {"dimension": dimension, "category_id": category_id}
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "models_retrieval_error",
                "message": "获取模型列表失败",
                "details": {"error": str(e), "dimension": dimension, "category_id": category_id}
            }
        )


@router.get("/model-management/models/{model_id}/dimensions",
           response_model=Dict[str, Any],
           responses={
               200: {"description": "成功获取模型维度信息"},
               400: {"description": "请求参数错误", "model": ErrorResponse},
               404: {"description": "模型不存在", "model": ErrorResponse},
               500: {"description": "服务器内部错误", "model": ErrorResponse}
           })
async def get_model_dimensions(
    model_id: int = ...,
    db: Session = Depends(get_db)
):
    """
    获取模型所属的所有维度和分类
    
    Args:
        model_id: 模型ID
        
    Returns:
        模型的多维度分类信息
    """
    try:
        dimensions_data = DimensionHierarchyService.get_model_dimensions(db, model_id)
        
        if not dimensions_data or not dimensions_data.get('dimensions'):
            return {
                "model_id": model_id,
                "dimensions": {},
                "message": "该模型尚未关联到任何维度分类"
            }
            
        return dimensions_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "model_not_found",
                "message": str(e),
                "details": {"model_id": model_id}
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "model_dimensions_error",
                "message": "获取模型维度信息失败",
                "details": {"error": str(e), "model_id": model_id}
            }
        )


@router.post("/model-management/models/{model_id}/dimensions/{dimension}/categories/{category_id}",
           response_model=Dict[str, Any],
           responses={
               200: {"description": "成功添加模型到维度分类"},
               400: {"description": "请求参数错误", "model": ErrorResponse},
               404: {"description": "模型或分类不存在", "model": ErrorResponse},
               409: {"description": "关联已存在", "model": ErrorResponse},
               500: {"description": "服务器内部错误", "model": ErrorResponse}
           })
async def add_model_to_dimension_category(
    model_id: int = ...,
    dimension: str = ...,
    category_id: int = ...,
    weight: int = Query(0, description="关联权重", ge=0, le=100),
    association_type: str = Query('primary', description="关联类型", regex="^[a-z_]+$"),
    db: Session = Depends(get_db)
):
    """
    将模型添加到指定维度的分类中
    
    Args:
        model_id: 模型ID
        dimension: 维度标识
        category_id: 分类ID
        weight: 关联权重
        association_type: 关联类型
        
    Returns:
        创建的关联信息
    """
    # 参数验证
    valid_dimensions = ['tasks', 'languages', 'licenses', 'technologies']
    valid_association_types = ['primary', 'secondary', 'custom']
    
    if dimension not in valid_dimensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_dimension",
                "message": f"无效的维度标识: {dimension}",
                "details": {"valid_dimensions": valid_dimensions}
            }
        )
    
    if association_type not in valid_association_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_association_type",
                "message": f"无效的关联类型: {association_type}",
                "details": {"valid_association_types": valid_association_types}
            }
        )
    
    try:
        association = DimensionHierarchyService.add_model_to_dimension_category(
            db, model_id, dimension, category_id, weight, association_type
        )
        
        return {
            "success": True,
            "message": "模型成功添加到维度分类",
            "data": {
                "association": {
                    "id": association.id,
                    "model_id": association.model_id,
                    "category_id": association.category_id,
                    "weight": association.weight,
                    "association_type": association.association_type,
                    "dimension": dimension
                }
            }
        }
    except ValueError as e:
        error_message = str(e)
        if "已存在" in error_message or "already exists" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "association_exists",
                    "message": error_message,
                    "details": {"model_id": model_id, "dimension": dimension, "category_id": category_id}
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "resource_not_found",
                    "message": error_message,
                    "details": {"model_id": model_id, "dimension": dimension, "category_id": category_id}
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "association_creation_error",
                "message": "添加模型到维度分类失败",
                "details": {
                    "error": str(e), 
                    "model_id": model_id, 
                    "dimension": dimension, 
                    "category_id": category_id
                }
            }
        )


@router.delete("/model-management/models/{model_id}/categories/{category_id}",
           response_model=Dict[str, Any],
           responses={
               200: {"description": "成功移除模型关联"},
               400: {"description": "请求参数错误", "model": ErrorResponse},
               404: {"description": "关联不存在", "model": ErrorResponse},
               500: {"description": "服务器内部错误", "model": ErrorResponse}
           })
async def remove_model_from_dimension_category(
    model_id: int = ...,
    category_id: int = ...,
    db: Session = Depends(get_db)
):
    """
    从指定维度的分类中移除模型
    
    Args:
        model_id: 模型ID
        category_id: 分类ID
        
    Returns:
        移除结果
    """
    try:
        success = DimensionHierarchyService.remove_model_from_dimension_category(
            db, model_id, category_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "association_not_found",
                    "message": "未找到模型与分类的关联关系",
                    "details": {"model_id": model_id, "category_id": category_id}
                }
            )
        
        return {
            "success": True,
            "message": "模型成功从维度分类中移除",
            "data": {"model_id": model_id, "category_id": category_id}
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "association_not_found",
                "message": str(e),
                "details": {"model_id": model_id, "category_id": category_id}
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "association_removal_error",
                "message": "从维度分类中移除模型失败",
                "details": {"error": str(e), "model_id": model_id, "category_id": category_id}
            }
        )


@router.delete("/model-management/models/{model_id}/categories",
           response_model=Dict[str, Any],
           responses={
               200: {"description": "成功删除所有模型关联"},
               400: {"description": "请求参数错误", "model": ErrorResponse},
               404: {"description": "模型不存在", "model": ErrorResponse},
               500: {"description": "服务器内部错误", "model": ErrorResponse}
           })
async def remove_all_model_category_associations(
    model_id: int = ...,
    db: Session = Depends(get_db)
):
    """
    删除模型的所有分类关联
    
    Args:
        model_id: 模型ID
        
    Returns:
        删除结果
    """
    try:
        success = DimensionHierarchyService.remove_all_model_category_associations(
            db, model_id
        )
        
        return {
            "success": True,
            "message": "成功删除模型的所有分类关联",
            "data": {"model_id": model_id}
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "model_not_found",
                "message": str(e),
                "details": {"model_id": model_id}
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "associations_removal_error",
                "message": "删除模型所有分类关联失败",
                "details": {"error": str(e), "model_id": model_id}
            }
        )


@router.get("/dimensions/{dimension}/constraints/{model_id}")
async def validate_dimension_constraints(
    dimension: str = ...,
    model_id: int = ...,
    db: Session = Depends(get_db)
):
    """
    验证模型在指定维度下的约束条件
    
    Args:
        dimension: 维度标识
        model_id: 模型ID
        
    Returns:
        约束验证结果
    """
    try:
        valid = DimensionHierarchyService.validate_dimension_constraints(db, model_id, dimension)
        
        return {
            "dimension": dimension,
            "model_id": model_id,
            "constraints_valid": valid,
            "message": "约束验证通过" if valid else "约束验证失败"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"约束验证失败: {str(e)}"
        )