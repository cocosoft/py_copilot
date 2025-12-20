"""模型能力相关的数据校验模型"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ModelCapability 相关schemas
class ModelCapabilityBase(BaseModel):
    """模型能力基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    
    # 能力维度（根据文档定义）
    capability_dimension: str = Field(default="generation", pattern="^(comprehension|generation|reasoning|memory|interaction|professional)$")
    capability_subdimension: Optional[str] = Field(None, max_length=50)
    
    # 能力强度量化
    base_strength: int = Field(default=3, ge=1, le=5)
    max_strength: int = Field(default=5, ge=1, le=5)
    
    # 评估指标和基准
    assessment_metrics: Optional[Dict[str, Any]] = None
    benchmark_datasets: Optional[Dict[str, Any]] = None
    
    # 能力依赖关系
    dependencies: Optional[Dict[str, Any]] = None
    
    capability_type: str = Field(default="standard", pattern="^(standard|advanced|specialized|domain_specific|creative|special)$")
    input_types: Optional[str] = None
    output_types: Optional[str] = None
    domain: str = Field(default="nlp", pattern="^(nlp|cv|audio|multimodal|data_analysis|reasoning|system_integration|advanced_ai|healthcare|finance|legal|education|customer_service|content_creation|special_features)$")
    is_active: bool = True
    is_system: bool = False
    logo: Optional[str] = None


class ModelCapabilityCreate(ModelCapabilityBase):
    """创建模型能力请求模型"""
    pass


class ModelCapabilityUpdate(BaseModel):
    """更新模型能力请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    capability_type: Optional[str] = Field(None, pattern="^[a-zA-Z0-9_]+$")
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None


class ModelCapabilityResponse(ModelCapabilityBase):
    """模型能力响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_system: bool
    
    model_config = ConfigDict(from_attributes=True)


class ModelCapabilityListResponse(BaseModel):
    """模型能力列表响应模型"""
    capabilities: List[ModelCapabilityResponse]
    total: int


# 模型能力关联相关schemas
class ModelCapabilityAssociationCreate(BaseModel):
    """创建模型能力关联请求模型"""
    model_id: int = Field(..., gt=0)
    capability_id: int = Field(..., gt=0)
    
    # 能力评估信息
    actual_strength: Optional[int] = Field(None, ge=1, le=5)
    confidence_score: Optional[int] = Field(None, ge=0, le=100)
    assessment_method: Optional[str] = Field(None, pattern="^(automated|manual|hybrid)$")
    assessment_data: Optional[Dict[str, Any]] = None
    
    # 能力配置
    config: Optional[str] = Field(None, max_length=255)
    config_json: Optional[str] = None
    
    # 关联权重
    weight: Optional[int] = Field(None, ge=0)
    is_default: Optional[bool] = None


class ModelCapabilityAssociationUpdate(BaseModel):
    """更新模型能力关联请求模型"""
    # 能力评估信息
    actual_strength: Optional[int] = Field(None, ge=1, le=5)
    confidence_score: Optional[int] = Field(None, ge=0, le=100)
    assessment_method: Optional[str] = Field(None, pattern="^(automated|manual|hybrid)$")
    assessment_data: Optional[Dict[str, Any]] = None
    
    # 能力配置
    config: Optional[str] = Field(None, max_length=255)
    config_json: Optional[str] = None
    
    # 关联权重
    weight: Optional[int] = Field(None, ge=0)
    is_default: Optional[bool] = None


class ModelCapabilityAssociationResponse(BaseModel):
    """模型能力关联响应模型"""
    id: int
    model_id: int
    capability_id: int
    
    # 能力评估信息
    actual_strength: int
    confidence_score: int
    last_assessment_date: Optional[datetime] = None
    assessment_method: Optional[str] = None
    assessment_data: Optional[Dict[str, Any]] = None
    
    # 能力配置
    config: Optional[str] = None
    config_json: Optional[str] = None
    
    # 关联属性
    is_default: bool
    weight: int
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ModelWithCapabilitiesResponse(BaseModel):
    """包含能力信息的模型响应模型"""
    id: int
    name: str
    model_id: str
    capabilities: List[ModelCapabilityResponse]
    
    model_config = ConfigDict(from_attributes=True)


class CapabilityWithModelsResponse(BaseModel):
    """包含模型信息的能力响应模型"""
    id: int
    name: str
    display_name: str
    models: List[Dict[str, Any]]  # 简化的模型信息
    
    model_config = ConfigDict(from_attributes=True)


# 能力评估相关schemas
class CapabilityAssessmentRequest(BaseModel):
    """能力评估请求模型"""
    model_id: int = Field(..., gt=0)
    capability_id: int = Field(..., gt=0)
    assessment_data: Optional[Dict[str, Any]] = None
    benchmark_name: Optional[str] = Field(None, max_length=100)
    

class BenchmarkAssessmentRequest(BaseModel):
    """基准测试评估请求模型"""
    model_id: int = Field(..., gt=0)
    capability_name: str = Field(..., min_length=1, max_length=100)
    benchmark_name: str = Field(..., min_length=1, max_length=100)
    test_data: Optional[Dict[str, Any]] = None
    

class CapabilityAssessmentResult(BaseModel):
    """能力评估结果模型"""
    model_id: int
    capability_id: int
    actual_strength: int = Field(..., ge=1, le=5)
    confidence_score: int = Field(..., ge=0, le=100)
    assessment_date: datetime
    assessment_method: str
    assessment_data: Optional[Dict[str, Any]] = None


class BenchmarkAssessmentResult(BaseModel):
    """基准测试评估结果模型"""
    benchmark_name: str
    capability_name: str
    model_id: int
    actual_strength: int = Field(..., ge=1, le=5)
    confidence_score: int = Field(..., ge=0, le=100)
    results: Dict[str, Any]
    assessment_date: datetime


class ModelComparisonRequest(BaseModel):
    """模型比较请求模型"""
    capability_id: int = Field(..., gt=0)
    model_ids: List[int] = Field(..., min_items=2)


class ModelComparisonResult(BaseModel):
    """模型比较结果模型"""
    capability_id: int
    comparison_results: List[Dict[str, Any]]


class TaskRecommendationRequest(BaseModel):
    """任务推荐请求模型"""
    task_description: str = Field(..., min_length=1)
    required_capabilities: List[str] = Field(..., min_items=1)
    min_strength: int = Field(default=3, ge=1, le=5)


class TaskRecommendationResult(BaseModel):
    """任务推荐结果模型"""
    task_description: str
    required_capabilities: List[str]
    recommended_models: List[Dict[str, Any]]


class AssessmentHistoryResponse(BaseModel):
    """评估历史响应模型"""
    model_id: int
    capability_id: int
    assessment_history: List[Dict[str, Any]]