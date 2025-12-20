"""智能体模型调度器服务"""
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.supplier_db import ModelDB
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.services.capability_assessment_service import CapabilityAssessmentService


class SchedulingStrategy(Enum):
    """调度策略枚举"""
    CAPABILITY_FIRST = "capability_first"  # 能力优先
    COST_EFFECTIVE = "cost_effective"  # 成本优先
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # 性能优先
    BALANCED = "balanced"  # 平衡策略


class ModelSelectionCriteria(BaseModel):
    """模型选择标准"""
    required_capabilities: List[str]
    min_strength: int = 3
    max_cost: Optional[float] = None
    max_response_time: Optional[int] = None
    preferred_suppliers: Optional[List[str]] = None
    excluded_models: Optional[List[str]] = None


class ScheduledModel(BaseModel):
    """调度结果中的模型信息"""
    model_id: int
    model_name: str
    supplier_name: str
    capability_strength: Dict[str, int]  # 能力名称 -> 强度
    confidence_score: Dict[str, int]  # 能力名称 -> 置信度
    estimated_cost: float
    estimated_response_time: int
    selection_reason: str


class SchedulingResult(BaseModel):
    """调度结果"""
    task_id: str
    selected_models: List[ScheduledModel]
    primary_model: ScheduledModel
    fallback_models: List[ScheduledModel]
    total_estimated_cost: float
    total_estimated_time: int
    scheduling_strategy: SchedulingStrategy


class AgentModelScheduler:
    """智能体模型调度器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.capability_service = CapabilityAssessmentService()
    
    def schedule_models(self, task_id: str, criteria: ModelSelectionCriteria, 
                       strategy: SchedulingStrategy = SchedulingStrategy.BALANCED) -> SchedulingResult:
        """
        根据任务需求调度合适的模型
        
        Args:
            task_id: 任务ID
            criteria: 模型选择标准
            strategy: 调度策略
            
        Returns:
            SchedulingResult: 调度结果
        """
        # 1. 获取所有可用模型
        available_models = self._get_available_models()
        
        # 2. 根据策略筛选模型
        filtered_models = self._filter_models_by_criteria(available_models, criteria)
        
        if not filtered_models:
            raise ValueError("没有找到满足条件的模型")
        
        # 3. 根据策略排序模型
        sorted_models = self._sort_models_by_strategy(filtered_models, criteria, strategy)
        
        # 4. 选择主模型和备用模型
        primary_model, fallback_models = self._select_primary_and_fallback(sorted_models)
        
        # 5. 计算总成本和预估时间
        total_cost = self._calculate_total_cost([primary_model] + fallback_models)
        total_time = self._calculate_total_time([primary_model] + fallback_models)
        
        # 6. 生成调度结果
        result = SchedulingResult(
            task_id=task_id,
            selected_models=[primary_model] + fallback_models,
            primary_model=primary_model,
            fallback_models=fallback_models,
            total_estimated_cost=total_cost,
            total_estimated_time=total_time,
            scheduling_strategy=strategy
        )
        
        return result
    
    def _get_available_models(self) -> List[Dict[str, Any]]:
        """获取所有可用模型及其能力信息"""
        models = self.db.query(ModelDB).filter(ModelDB.is_active == True).all()
        
        available_models = []
        for model in models:
            model_info = {
                "model_id": model.id,
                "model_name": model.model_name,
                "supplier_name": model.supplier.name if model.supplier else "Unknown",
                "capabilities": {},
                "estimated_cost": self._estimate_model_cost(model),
                "estimated_response_time": self._estimate_response_time(model)
            }
            
            # 获取模型的能力关联
            associations = self.db.query(ModelCapabilityAssociation).filter(
                ModelCapabilityAssociation.model_id == model.id
            ).all()
            
            for association in associations:
                capability = self.db.query(ModelCapability).filter(
                    ModelCapability.id == association.capability_id
                ).first()
                
                if capability:
                    model_info["capabilities"][capability.name] = {
                        "strength": association.actual_strength,
                        "confidence": association.confidence_score
                    }
            
            available_models.append(model_info)
        
        return available_models
    
    def _filter_models_by_criteria(self, models: List[Dict[str, Any]], 
                                 criteria: ModelSelectionCriteria) -> List[Dict[str, Any]]:
        """根据选择标准筛选模型"""
        filtered_models = []
        
        for model in models:
            # 检查是否在排除列表中
            if criteria.excluded_models and model["model_name"] in criteria.excluded_models:
                continue
            
            # 检查供应商偏好
            if criteria.preferred_suppliers and model["supplier_name"] not in criteria.preferred_suppliers:
                continue
            
            # 检查能力要求
            meets_capability_requirements = True
            for capability in criteria.required_capabilities:
                if capability not in model["capabilities"]:
                    meets_capability_requirements = False
                    break
                
                capability_info = model["capabilities"][capability]
                if capability_info["strength"] < criteria.min_strength:
                    meets_capability_requirements = False
                    break
            
            if not meets_capability_requirements:
                continue
            
            # 检查成本限制
            if criteria.max_cost and model["estimated_cost"] > criteria.max_cost:
                continue
            
            # 检查响应时间限制
            if criteria.max_response_time and model["estimated_response_time"] > criteria.max_response_time:
                continue
            
            filtered_models.append(model)
        
        return filtered_models
    
    def _sort_models_by_strategy(self, models: List[Dict[str, Any]], 
                               criteria: ModelSelectionCriteria, 
                               strategy: SchedulingStrategy) -> List[Dict[str, Any]]:
        """根据策略对模型进行排序"""
        if strategy == SchedulingStrategy.CAPABILITY_FIRST:
            # 能力优先：按能力强度排序
            return sorted(models, key=lambda x: self._calculate_capability_score(x, criteria), reverse=True)
        
        elif strategy == SchedulingStrategy.COST_EFFECTIVE:
            # 成本优先：按成本排序
            return sorted(models, key=lambda x: x["estimated_cost"])
        
        elif strategy == SchedulingStrategy.PERFORMANCE_OPTIMIZED:
            # 性能优先：按响应时间排序
            return sorted(models, key=lambda x: x["estimated_response_time"])
        
        else:  # BALANCED
            # 平衡策略：综合考虑能力、成本、性能
            return sorted(models, key=lambda x: self._calculate_balanced_score(x, criteria))
    
    def _calculate_capability_score(self, model: Dict[str, Any], criteria: ModelSelectionCriteria) -> float:
        """计算模型能力得分"""
        total_score = 0
        capability_count = 0
        
        for capability in criteria.required_capabilities:
            if capability in model["capabilities"]:
                capability_info = model["capabilities"][capability]
                # 考虑强度（权重0.7）和置信度（权重0.3）
                score = (capability_info["strength"] * 0.7) + (capability_info["confidence"] / 100 * 0.3)
                total_score += score
                capability_count += 1
        
        return total_score / capability_count if capability_count > 0 else 0
    
    def _calculate_balanced_score(self, model: Dict[str, Any], criteria: ModelSelectionCriteria) -> float:
        """计算平衡得分"""
        # 能力得分（权重0.5）
        capability_score = self._calculate_capability_score(model, criteria)
        
        # 成本得分（权重0.3）
        max_cost = max(m["estimated_cost"] for m in self._get_available_models()) if self._get_available_models() else 1
        cost_score = 1 - (model["estimated_cost"] / max_cost) if max_cost > 0 else 1
        
        # 性能得分（权重0.2）
        max_time = max(m["estimated_response_time"] for m in self._get_available_models()) if self._get_available_models() else 1
        performance_score = 1 - (model["estimated_response_time"] / max_time) if max_time > 0 else 1
        
        return (capability_score * 0.5) + (cost_score * 0.3) + (performance_score * 0.2)
    
    def _select_primary_and_fallback(self, sorted_models: List[Dict[str, Any]]) -> Tuple[ScheduledModel, List[ScheduledModel]]:
        """选择主模型和备用模型"""
        if not sorted_models:
            raise ValueError("没有可用的模型")
        
        # 主模型：排序第一的模型
        primary_model_info = sorted_models[0]
        primary_model = self._create_scheduled_model(primary_model_info, "primary")
        
        # 备用模型：排序第二和第三的模型
        fallback_models = []
        for i, model_info in enumerate(sorted_models[1:3]):  # 最多选择2个备用模型
            fallback_model = self._create_scheduled_model(model_info, f"fallback_{i+1}")
            fallback_models.append(fallback_model)
        
        return primary_model, fallback_models
    
    def _create_scheduled_model(self, model_info: Dict[str, Any], role: str) -> ScheduledModel:
        """创建调度模型对象"""
        capability_strength = {}
        confidence_score = {}
        
        for capability_name, capability_data in model_info["capabilities"].items():
            capability_strength[capability_name] = capability_data["strength"]
            confidence_score[capability_name] = capability_data["confidence"]
        
        selection_reason = f"基于能力评估选择为{role}模型"
        
        return ScheduledModel(
            model_id=model_info["model_id"],
            model_name=model_info["model_name"],
            supplier_name=model_info["supplier_name"],
            capability_strength=capability_strength,
            confidence_score=confidence_score,
            estimated_cost=model_info["estimated_cost"],
            estimated_response_time=model_info["estimated_response_time"],
            selection_reason=selection_reason
        )
    
    def _estimate_model_cost(self, model: ModelDB) -> float:
        """估算模型使用成本"""
        # 基于模型类型和供应商的简单成本估算
        cost_mapping = {
            "gpt-4": 0.03,  # 每千token
            "gpt-3.5-turbo": 0.002,
            "claude-3": 0.025,
            "codellama": 0.001,  # 本地模型成本较低
            "llama": 0.001
        }
        
        model_name_lower = model.model_name.lower()
        for key, cost in cost_mapping.items():
            if key in model_name_lower:
                return cost
        
        return 0.01  # 默认成本
    
    def _estimate_response_time(self, model: ModelDB) -> int:
        """估算模型响应时间（毫秒）"""
        # 基于模型类型和上下文的简单响应时间估算
        time_mapping = {
            "gpt-4": 2000,
            "gpt-3.5-turbo": 1000,
            "claude-3": 1500,
            "codellama": 5000,  # 本地模型可能较慢
            "llama": 4000
        }
        
        model_name_lower = model.model_name.lower()
        for key, time in time_mapping.items():
            if key in model_name_lower:
                return time
        
        return 2000  # 默认响应时间
    
    def _calculate_total_cost(self, models: List[ScheduledModel]) -> float:
        """计算总成本"""
        return sum(model.estimated_cost for model in models)
    
    def _calculate_total_time(self, models: List[ScheduledModel]) -> int:
        """计算总预估时间"""
        return sum(model.estimated_response_time for model in models)
    
    def load_balance(self, current_workload: Dict[str, int], 
                    scheduling_result: SchedulingResult) -> SchedulingResult:
        """
        基于当前负载进行负载均衡
        
        Args:
            current_workload: 当前各模型的负载情况
            scheduling_result: 原始调度结果
            
        Returns:
            SchedulingResult: 负载均衡后的调度结果
        """
        # 简单的负载均衡策略：如果主模型负载过高，切换到备用模型
        primary_model_name = scheduling_result.primary_model.model_name
        
        if primary_model_name in current_workload and current_workload[primary_model_name] > 10:
            # 主模型负载过高，切换到第一个备用模型
            if scheduling_result.fallback_models:
                new_primary = scheduling_result.fallback_models[0]
                remaining_fallbacks = scheduling_result.fallback_models[1:] + [scheduling_result.primary_model]
                
                # 更新选择原因
                new_primary.selection_reason = "负载均衡：原主模型负载过高"
                
                # 创建新的调度结果
                balanced_result = SchedulingResult(
                    task_id=scheduling_result.task_id,
                    selected_models=[new_primary] + remaining_fallbacks,
                    primary_model=new_primary,
                    fallback_models=remaining_fallbacks,
                    total_estimated_cost=scheduling_result.total_estimated_cost,
                    total_estimated_time=scheduling_result.total_estimated_time,
                    scheduling_strategy=scheduling_result.scheduling_strategy
                )
                
                return balanced_result
        
        return scheduling_result