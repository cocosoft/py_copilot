"""模型能力相关的API路由"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from app.services.model_capability_service import model_capability_service
from app.services.capability_assessment_service import capability_assessment_service

# 创建路由器
router = APIRouter(prefix="/capabilities", tags=["model_capabilities"])


# 模拟用户认证依赖
async def get_current_user():
    """获取当前用户"""
    # 实际项目中应该有真实的认证逻辑
    return {"id": 1, "username": "admin"}


@router.post("/", response_model=ModelCapabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_capability(
    capability: ModelCapabilityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新的模型能力"""
    db_capability = model_capability_service.create_capability(db, capability)
    return db_capability


@router.get("/{capability_id}", response_model=ModelCapabilityResponse)
async def get_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个模型能力"""
    db_capability = model_capability_service.get_capability(db, capability_id)
    return db_capability


@router.get("/", response_model=ModelCapabilityListResponse)
async def get_capabilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    capability_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取模型能力列表"""
    result = model_capability_service.get_capabilities(
        db=db,
        skip=skip,
        limit=limit,
        capability_type=capability_type,
        is_active=is_active
    )
    return result


@router.put("/{capability_id}", response_model=ModelCapabilityResponse)
async def update_capability(
    capability_id: int,
    capability_update: ModelCapabilityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新模型能力"""
    updated_capability = model_capability_service.update_capability(
        db, capability_id, capability_update
    )
    return updated_capability


@router.delete("/{capability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除模型能力（软删除）"""
    model_capability_service.delete_capability(db, capability_id)
    return None


@router.post("/associations", response_model=ModelCapabilityAssociationResponse, status_code=status.HTTP_201_CREATED)
async def create_model_capability_association(
    association: ModelCapabilityAssociationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建模型和能力的关联"""
    db_association = model_capability_service.add_capability_to_model(db, association)
    return db_association


@router.put("/associations/model/{model_id}/capability/{capability_id}", response_model=ModelCapabilityAssociationResponse)
async def update_model_capability_association(
    model_id: int,
    capability_id: int,
    association_update: ModelCapabilityAssociationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新模型和能力的关联"""
    db_association = model_capability_service.update_model_capability_association(
        db, model_id, capability_id, association_update
    )
    return db_association


@router.delete("/associations/model/{model_id}/capability/{capability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_capability_association(
    model_id: int,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除模型和能力的关联"""
    model_capability_service.remove_capability_from_model(db, model_id, capability_id)
    return None


@router.get("/{capability_id}/models", response_model=List[ModelWithCapabilitiesResponse])
async def get_models_by_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取具有指定能力的模型列表"""
    models = model_capability_service.get_models_by_capability(db, capability_id)
    return models


@router.get("/model/{model_id}/capabilities", response_model=List[ModelCapabilityResponse])
async def get_capabilities_by_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取指定模型的所有能力"""
    capabilities = model_capability_service.get_capabilities_by_model(db, model_id)
    return capabilities


# 能力评估相关API端点
@router.post("/assessments/assess", response_model=CapabilityAssessmentResult)
async def assess_capability(
    assessment_request: CapabilityAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """评估模型在特定能力上的强度"""
    actual_strength, confidence_score = capability_assessment_service.assess_capability_strength(
        db, assessment_request.model_id, assessment_request.capability_id, assessment_request.assessment_data
    )
    
    return CapabilityAssessmentResult(
        model_id=assessment_request.model_id,
        capability_id=assessment_request.capability_id,
        actual_strength=actual_strength,
        confidence_score=confidence_score,
        assessment_date=datetime.now(),
        assessment_method="automated",
        assessment_data=assessment_request.assessment_data
    )


@router.post("/assessments/benchmark", response_model=BenchmarkAssessmentResult)
async def run_benchmark_assessment(
    benchmark_request: BenchmarkAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """运行基准测试评估"""
    result = capability_assessment_service.run_benchmark_assessment(
        db, 
        benchmark_request.model_id, 
        benchmark_request.capability_name, 
        benchmark_request.benchmark_name,
        benchmark_request.test_data
    )
    
    return BenchmarkAssessmentResult(**result)


@router.post("/assessments/compare", response_model=ModelComparisonResult)
async def compare_models_by_capability(
    comparison_request: ModelComparisonRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """比较多个模型在特定能力上的表现"""
    comparison_results = capability_assessment_service.compare_models_by_capability(
        db, comparison_request.capability_id, comparison_request.model_ids
    )
    
    return ModelComparisonResult(
        capability_id=comparison_request.capability_id,
        comparison_results=comparison_results
    )


@router.post("/assessments/recommend", response_model=TaskRecommendationResult)
async def get_recommended_models_for_task(
    recommendation_request: TaskRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """根据任务需求推荐合适的模型"""
    recommended_models = capability_assessment_service.get_recommended_models_for_task(
        db, 
        recommendation_request.task_description,
        recommendation_request.required_capabilities,
        recommendation_request.min_strength
    )
    
    return TaskRecommendationResult(
        task_description=recommendation_request.task_description,
        required_capabilities=recommendation_request.required_capabilities,
        recommended_models=recommended_models
    )


@router.get("/assessments/history/model/{model_id}/capability/{capability_id}", response_model=AssessmentHistoryResponse)
async def get_capability_assessment_history(
    model_id: int,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取能力评估历史"""
    assessment_history = capability_assessment_service.get_capability_assessment_history(
        db, model_id, capability_id
    )
    
    return AssessmentHistoryResponse(
        model_id=model_id,
        capability_id=capability_id,
        assessment_history=assessment_history
    )