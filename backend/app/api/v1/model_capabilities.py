"""模型能力相关的API路由"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.model_capability import (
    ModelCapabilityCreate,
    ModelCapabilityUpdate,
    ModelCapabilityResponse,
    ModelCapabilityListResponse,
    ModelCapabilityAssociationCreate,
    ModelCapabilityAssociationUpdate,
    ModelCapabilityAssociationResponse,
    ModelWithCapabilitiesResponse,
    CapabilityWithModelsResponse,
    CapabilityAssessmentRequest,
    CapabilityAssessmentResult,
    BenchmarkAssessmentRequest,
    BenchmarkAssessmentResult,
    ModelComparisonRequest,
    ModelComparisonResult,
    TaskRecommendationRequest,
    TaskRecommendationResult,
    AssessmentHistoryResponse
)
from app.schemas.response import SuccessResponse, SuccessData, ListResponse
from app.utils.response_utils import (
    success_with_data,
    success_with_message,
    list_response,
    raise_http_exception
)
from app.services.model_capability_service import model_capability_service
from app.services.capability_assessment_service import capability_assessment_service

# 创建路由器
router = APIRouter(prefix="/capabilities", tags=["model_capabilities"])


# 从api.deps导入实际的认证依赖
from app.api.deps import get_current_user
from app.models.user import User


@router.post("/", response_model=SuccessData[ModelCapabilityResponse], status_code=status.HTTP_201_CREATED)
async def create_capability(
    capability: ModelCapabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的模型能力"""
    try:
        db_capability = model_capability_service.create_capability(db, capability)
        return success_with_data(db_capability, message="能力创建成功", code=201)
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="创建能力失败",
            detail=str(e)
        )


@router.get("/{capability_id}", response_model=SuccessData[ModelCapabilityResponse])
async def get_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个模型能力"""
    try:
        db_capability = model_capability_service.get_capability(db, capability_id)
        return success_with_data(db_capability, message="获取能力成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_404_NOT_FOUND,
            message="获取能力失败",
            detail=str(e)
        )


@router.get("/", response_model=ListResponse[ModelCapabilityResponse])
async def get_capabilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    capability_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模型能力列表"""
    try:
        result = model_capability_service.get_capabilities(
            db=db,
            skip=skip,
            limit=limit,
            capability_type=capability_type,
            is_active=is_active
        )
        return list_response(
            data=result["capabilities"],
            total=result["total"],
            page=skip // limit + 1 if limit > 0 else None,
            size=limit,
            message="获取能力列表成功"
        )
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取能力列表失败",
            detail=str(e)
        )


@router.put("/{capability_id}", response_model=SuccessData[ModelCapabilityResponse])
async def update_capability(
    capability_id: int,
    capability_update: ModelCapabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模型能力"""
    try:
        updated_capability = model_capability_service.update_capability(
            db, capability_id, capability_update
        )
        return success_with_data(updated_capability, message="能力更新成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="更新能力失败",
            detail=str(e)
        )


@router.delete("/{capability_id}", response_model=SuccessResponse)
async def delete_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模型能力（软删除）"""
    try:
        model_capability_service.delete_capability(db, capability_id)
        return success_with_message("能力删除成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="删除能力失败",
            detail=str(e)
        )


@router.post("/associations", response_model=SuccessData[ModelCapabilityAssociationResponse], status_code=status.HTTP_201_CREATED)
async def create_model_capability_association(
    association: ModelCapabilityAssociationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建模型和能力的关联"""
    try:
        db_association = model_capability_service.add_capability_to_model(db, association)
        return success_with_data(db_association, message="模型能力关联创建成功", code=201)
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="创建模型能力关联失败",
            detail=str(e)
        )


@router.put("/associations/model/{model_id}/capability/{capability_id}", response_model=SuccessData[ModelCapabilityAssociationResponse])
async def update_model_capability_association(
    model_id: int,
    capability_id: int,
    association_update: ModelCapabilityAssociationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模型和能力的关联"""
    try:
        db_association = model_capability_service.update_model_capability_association(
            db, model_id, capability_id, association_update
        )
        return success_with_data(db_association, message="模型能力关联更新成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="更新模型能力关联失败",
            detail=str(e)
        )


@router.delete("/associations/model/{model_id}/capability/{capability_id}", response_model=SuccessResponse)
async def delete_model_capability_association(
    model_id: int,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模型和能力的关联"""
    try:
        model_capability_service.remove_capability_from_model(db, model_id, capability_id)
        return success_with_message("模型能力关联删除成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="删除模型能力关联失败",
            detail=str(e)
        )


@router.post("/batch", response_model=SuccessData[List[ModelCapabilityResponse]], status_code=status.HTTP_201_CREATED)
async def create_capabilities_batch(
    capabilities: List[ModelCapabilityCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建模型能力"""
    try:
        created_capabilities = model_capability_service.create_capabilities_batch(db, capabilities)
        return success_with_data(created_capabilities, message="能力批量创建成功", code=201)
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="批量创建能力失败",
            detail=str(e)
        )


@router.put("/batch", response_model=SuccessData[List[ModelCapabilityResponse]])
async def update_capabilities_batch(
    updates: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新模型能力"""
    try:
        updated_capabilities = model_capability_service.update_capabilities_batch(db, updates)
        return success_with_data(updated_capabilities, message="能力批量更新成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="批量更新能力失败",
            detail=str(e)
        )


@router.delete("/batch", response_model=SuccessResponse)
async def delete_capabilities_batch(
    capability_ids: List[int] = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量删除模型能力（软删除）"""
    try:
        model_capability_service.delete_capabilities_batch(db, capability_ids)
        return success_with_message("能力批量删除成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="批量删除能力失败",
            detail=str(e)
        )


@router.post("/associations/batch", response_model=SuccessData[List[ModelCapabilityAssociationResponse]], status_code=status.HTTP_201_CREATED)
async def create_associations_batch(
    associations: List[ModelCapabilityAssociationCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建模型能力关联"""
    try:
        created_associations = model_capability_service.create_associations_batch(db, associations)
        return success_with_data(created_associations, message="模型能力关联批量创建成功", code=201)
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="批量创建模型能力关联失败",
            detail=str(e)
        )


@router.delete("/associations/batch", response_model=SuccessResponse)
async def delete_associations_batch(
    associations: List[Dict[str, int]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量删除模型能力关联"""
    try:
        model_capability_service.delete_associations_batch(db, associations)
        return success_with_message("模型能力关联批量删除成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="批量删除模型能力关联失败",
            detail=str(e)
        )


@router.put("/associations/batch", response_model=SuccessData[List[ModelCapabilityAssociationResponse]])
async def update_associations_batch(
    updates: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新模型能力关联"""
    try:
        updated_associations = model_capability_service.update_associations_batch(db, updates)
        return success_with_data(updated_associations, message="模型能力关联批量更新成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="批量更新模型能力关联失败",
            detail=str(e)
        )


@router.get("/{capability_id}/models", response_model=ListResponse[ModelWithCapabilitiesResponse])
async def get_models_by_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取具有指定能力的模型列表"""
    try:
        models = model_capability_service.get_models_by_capability(db, capability_id)
        return list_response(
            data=models,
            total=len(models),
            message="获取具有指定能力的模型列表成功"
        )
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取模型列表失败",
            detail=str(e)
        )


@router.get("/model/{model_id}/capabilities", response_model=ListResponse[Dict[str, Any]])
async def get_capabilities_by_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定模型的所有能力"""
    try:
        # 统一返回格式，确保返回的是关联对象数组
        capabilities = model_capability_service.get_capabilities_by_model(db, model_id)
        
        # 验证返回数据格式，确保包含能力信息
        if not capabilities:
            # 如果没有能力，返回空数组
            return list_response(
                data=[],
                total=0,
                message="模型暂无能力"
            )
        
        # 转换为统一格式（如果后端返回的不是期望的格式）
        formatted_capabilities = []
        for capability in capabilities:
            # 确保每个元素都包含capability字段
            if 'capability' not in capability:
                # 如果没有capability字段，尝试包装
                formatted_capabilities.append({
                    'id': capability.get('id', None),
                    'model_id': capability.get('model_id', model_id),
                    'capability_id': capability.get('capability_id', None),
                    'capability': capability  # 将整个对象作为capability
                })
            else:
                # 已经是期望格式
                formatted_capabilities.append(capability)
        
        return list_response(
            data=formatted_capabilities,
            total=len(formatted_capabilities),
            message="获取模型能力列表成功"
        )
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取能力列表失败",
            detail=str(e)
        )


@router.get("/{capability_id}/parameter-templates", response_model=SuccessData[List[Dict[str, Any]]])
async def get_parameter_templates_by_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取与能力关联的参数模板"""
    try:
        templates = model_capability_service.get_parameter_templates_by_capability(db, capability_id)
        return success_with_data(templates, message="获取能力关联的参数模板成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取参数模板失败",
            detail=str(e)
        )


# 能力评估相关API端点
@router.post("/assessments/assess", response_model=SuccessData[CapabilityAssessmentResult])
async def assess_capability(
    assessment_request: CapabilityAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """评估模型在特定能力上的强度"""
    try:
        actual_strength, confidence_score = capability_assessment_service.assess_capability_strength(
            db, assessment_request.model_id, assessment_request.capability_id, assessment_request.assessment_data
        )
        
        result = CapabilityAssessmentResult(
            model_id=assessment_request.model_id,
            capability_id=assessment_request.capability_id,
            actual_strength=actual_strength,
            confidence_score=confidence_score,
            assessment_date=datetime.now(),
            assessment_method="automated",
            assessment_data=assessment_request.assessment_data
        )
        
        return success_with_data(result, message="能力评估成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="能力评估失败",
            detail=str(e)
        )


@router.post("/assessments/benchmark", response_model=SuccessData[BenchmarkAssessmentResult])
async def run_benchmark_assessment(
    benchmark_request: BenchmarkAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行基准测试评估"""
    try:
        result = capability_assessment_service.run_benchmark_assessment(
            db, 
            benchmark_request.model_id, 
            benchmark_request.capability_name, 
            benchmark_request.benchmark_name,
            benchmark_request.test_data
        )
        
        return success_with_data(BenchmarkAssessmentResult(**result), message="基准测试评估成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="基准测试评估失败",
            detail=str(e)
        )


@router.post("/assessments/compare", response_model=SuccessData[ModelComparisonResult])
async def compare_models_by_capability(
    comparison_request: ModelComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """比较多个模型在特定能力上的表现"""
    try:
        comparison_results = capability_assessment_service.compare_models_by_capability(
            db, comparison_request.capability_id, comparison_request.model_ids
        )
        
        result = ModelComparisonResult(
            capability_id=comparison_request.capability_id,
            comparison_results=comparison_results
        )
        
        return success_with_data(result, message="模型比较成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="模型比较失败",
            detail=str(e)
        )


@router.post("/assessments/recommend", response_model=SuccessData[TaskRecommendationResult])
async def get_recommended_models_for_task(
    recommendation_request: TaskRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据任务需求推荐合适的模型"""
    try:
        recommended_models = capability_assessment_service.get_recommended_models_for_task(
            db, 
            recommendation_request.task_description,
            recommendation_request.required_capabilities,
            recommendation_request.min_strength
        )
        
        result = TaskRecommendationResult(
            task_description=recommendation_request.task_description,
            required_capabilities=recommendation_request.required_capabilities,
            recommended_models=recommended_models
        )
        
        return success_with_data(result, message="模型推荐成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="模型推荐失败",
            detail=str(e)
        )


@router.get("/assessments/history/model/{model_id}/capability/{capability_id}", response_model=SuccessData[AssessmentHistoryResponse])
async def get_capability_assessment_history(
    model_id: int,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取能力评估历史"""
    try:
        assessment_history = capability_assessment_service.get_capability_assessment_history(
            db, model_id, capability_id
        )
        
        result = AssessmentHistoryResponse(
            model_id=model_id,
            capability_id=capability_id,
            assessment_history=assessment_history
        )
        
        return success_with_data(result, message="获取评估历史成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取评估历史失败",
            detail=str(e)
        )


# 能力版本管理相关API端点
@router.post("/{capability_id}/versions", response_model=SuccessData[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
async def create_capability_version(
    capability_id: int,
    version_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建能力版本"""
    try:
        db_version = model_capability_service.create_capability_version(db, capability_id, version_data)
        return success_with_data(db_version, message="版本创建成功", code=201)
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="创建版本失败",
            detail=str(e)
        )


@router.get("/{capability_id}/versions", response_model=SuccessData[List[Dict[str, Any]]])
async def get_capability_versions(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取能力的所有版本"""
    try:
        versions = model_capability_service.get_capability_versions(db, capability_id)
        return success_with_data(versions, message="获取版本列表成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取版本列表失败",
            detail=str(e)
        )


@router.get("/{capability_id}/versions/{version_id}", response_model=SuccessData[Dict[str, Any]])
async def get_capability_version(
    capability_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取特定版本的能力"""
    try:
        version = model_capability_service.get_capability_version(db, capability_id, version_id)
        return success_with_data(version, message="获取版本成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_404_NOT_FOUND,
            message="获取版本失败",
            detail=str(e)
        )


@router.put("/{capability_id}/versions/{version_id}/set-current", response_model=SuccessData[Dict[str, Any]])
async def set_current_version(
    capability_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将版本设置为当前版本"""
    try:
        version = model_capability_service.set_current_version(db, capability_id, version_id)
        return success_with_data(version, message="设置当前版本成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="设置当前版本失败",
            detail=str(e)
        )


@router.put("/{capability_id}/versions/{version_id}/set-stable", response_model=SuccessData[Dict[str, Any]])
async def set_stable_version(
    capability_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将版本设置为稳定版本"""
    try:
        version = model_capability_service.set_stable_version(db, capability_id, version_id)
        return success_with_data(version, message="设置稳定版本成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="设置稳定版本失败",
            detail=str(e)
        )