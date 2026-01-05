"""智能体模型调度器服务"""
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.supplier_db import ModelDB
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.default_model import DefaultModel, ModelPerformance
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
        self.logger = logging.getLogger(__name__)
    
    def schedule_models(self, task_id: str, criteria: ModelSelectionCriteria, 
                       strategy: SchedulingStrategy = SchedulingStrategy.BALANCED,
                       use_defaults: bool = True) -> SchedulingResult:
        """
        根据任务需求调度合适的模型
        
        Args:
            task_id: 任务ID
            criteria: 模型选择标准
            strategy: 调度策略
            use_defaults: 是否使用默认模型配置作为优先选择
            
        Returns:
            SchedulingResult: 调度结果
        """
        # 1. 获取所有可用模型
        available_models = self._get_available_models()
        
        # 2. 尝试获取默认模型配置
        primary_model = None
        fallback_models = []
        
        if use_defaults:
            try:
                # 尝试获取全局默认模型
                global_default = self._get_default_model(scope='global')
                
                # 获取场景特定默认模型（如果有）
                scene_default = None
                if criteria.required_capabilities:
                    scene_default = self._get_scene_default_model(criteria.required_capabilities[0])
                
                # 选择优先级更高的默认模型作为主模型
                if scene_default and scene_default.priority < global_default.priority:
                    primary_model = self._create_scheduled_model_from_default(scene_default, "primary")
                    self.logger.info(f"选择场景默认模型作为主模型: {primary_model.model_name}")
                else:
                    primary_model = self._create_scheduled_model_from_default(global_default, "primary")
                    self.logger.info(f"选择全局默认模型作为主模型: {primary_model.model_name}")
                
                # 如果有备用模型，将其添加到备用模型列表
                if primary_model and primary_model.fallback_model_id:
                    fallback_model_info = self._get_model_info(primary_model.fallback_model_id)
                    if fallback_model_info:
                        fallback_models.append(self._create_scheduled_model(fallback_model_info, "fallback"))
                        self.logger.info(f"配置备用模型: {fallback_models[0].model_name}")
            except Exception as e:
                self.logger.warning(f"获取默认模型配置失败: {str(e)}")
                primary_model = None
                fallback_models = []
        
        # 3. 如果没有默认模型或默认模型不可用，则根据策略筛选模型
        if not primary_model or not self._is_model_available(primary_model.model_id, available_models):
            self.logger.info("默认模型不可用，使用标准模型选择逻辑")
            filtered_models = self._filter_models_by_criteria(available_models, criteria)
            
            if not filtered_models:
                raise ValueError("没有找到满足条件的模型")
            
            # 根据策略排序模型
            sorted_models = self._sort_models_by_strategy(filtered_models, criteria, strategy)
            
            # 选择主模型和备用模型
            if sorted_models:
                primary_model, fallback_models = self._select_primary_and_fallback(sorted_models)
        
        # 4. 如果默认模型的备用模型不可用，添加其他符合条件的模型作为备用
        if fallback_models and not fallback_models[0].model_id in [m["model_id"] for m in available_models]:
            fallback_models = []
            for model_info in available_models[:2]:  # 最多添加两个备用模型
                if model_info["model_id"] != primary_model.model_id:
                    fallback_models.append(self._create_scheduled_model(model_info, "fallback"))
        
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
    
    def _get_default_model(self, scope: str) -> DefaultModel:
        """获取指定作用域的默认模型"""
        default_model = self.db.query(DefaultModel).filter(
            DefaultModel.scope == scope,
            DefaultModel.is_active == True
        ).first()
        
        if not default_model:
            raise ValueError(f"没有找到{scope}作用域的活跃默认模型")
            
        return default_model
    
    def _get_scene_default_model(self, scene: str) -> Optional[DefaultModel]:
        """获取指定场景的默认模型"""
        return self.db.query(DefaultModel).filter(
            DefaultModel.scope == 'scene',
            DefaultModel.scene == scene,
            DefaultModel.is_active == True
        ).first()
    
    def _create_scheduled_model_from_default(self, default_model: DefaultModel, role: str) -> ScheduledModel:
        """根据默认模型配置创建调度模型对象"""
        model = self.db.query(ModelDB).filter(ModelDB.id == default_model.model_id).first()
        
        if not model:
            raise ValueError(f"默认模型关联的模型不存在 (ID: {default_model.model_id})")
            
        # 获取模型能力
        capabilities = {}
        associations = self.db.query(ModelCapabilityAssociation).filter(
            ModelCapabilityAssociation.model_id == model.id
        ).all()
        
        for association in associations:
            capability = self.db.query(ModelCapability).filter(
                ModelCapability.id == association.capability_id
            ).first()
            
            if capability:
                capabilities[capability.name] = {
                    "strength": association.actual_strength,
                    "confidence": association.confidence_score
                }
        
        # 获取模型性能数据（用于成本和响应时间估算）
        model_performance = self.db.query(ModelPerformance).filter(
            ModelPerformance.model_id == model.id
        ).all()
        
        # 估算响应时间（如果没有性能数据，使用默认值）
        estimated_response_time = self._estimate_response_time(model)
        if model_performance and model_performance[0].avg_response_time:
            estimated_response_time = int(float(model_performance[0].avg_response_time) * 1000)  # 转换为毫秒
        
        # 估算成本（如果没有性能数据，使用默认值）
        estimated_cost = self._estimate_model_cost(model)
        
        # 设置角色和选择原因
        if role == "primary":
            selection_reason = f"基于默认模型配置选择为主模型"
        else:
            selection_reason = f"基于默认模型配置选择为备用模型"
        
        # 如果是备用模型，直接设置备用模型ID
        fallback_model_id = default_model.fallback_model_id if role == "primary" else None
        
        # 构建能力强度和置信度字典
        capability_strength = {}
        confidence_score = {}
        
        for capability_name, capability_data in capabilities.items():
            capability_strength[capability_name] = capability_data["strength"]
            confidence_score[capability_name] = capability_data["confidence"]
        
        # 创建ScheduledModel对象
        scheduled_model = ScheduledModel(
            model_id=model.id,
            model_name=model.model_name,
            supplier_name=model.supplier.name if model.supplier else "Unknown",
            capability_strength=capability_strength,
            confidence_score=confidence_score,
            estimated_cost=estimated_cost,
            estimated_response_time=estimated_response_time,
            selection_reason=selection_reason
        )
        
        # 如果有备用模型ID，设置到对象上（通过扩展属性）
        if fallback_model_id:
            scheduled_model.fallback_model_id = fallback_model_id
        
        return scheduled_model
    
    def _is_model_available(self, model_id: int, available_models: List[Dict[str, Any]]) -> bool:
        """检查模型是否在可用模型列表中"""
        for model in available_models:
            if model["model_id"] == model_id:
                return True
        return False
    
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
    
    def perform_fallback(self, scheduling_result: SchedulingResult, 
                        failed_model_id: int) -> SchedulingResult:
        """
        执行模型回退机制
        
        Args:
            scheduling_result: 原始调度结果
            failed_model_id: 失败模型的ID
            
        Returns:
            SchedulingResult: 回退后的调度结果
        """
        # 记录回退事件
        self.logger.warning(f"模型 {failed_model_id} 失败，开始执行回退机制")
        
        # 查找失败模型在结果中的位置
        model_index = None
        for i, model in enumerate(scheduling_result.selected_models):
            if model.model_id == failed_model_id:
                model_index = i
                break
        
        if model_index is None:
            self.logger.error(f"找不到失败模型 {failed_model_id} 在调度结果中")
            return scheduling_result
        
        # 如果是主模型失败，则选择第一个备用模型作为新主模型
        if scheduling_result.primary_model.model_id == failed_model_id:
            if scheduling_result.fallback_models:
                new_primary = scheduling_result.fallback_models[0]
                remaining_fallbacks = scheduling_result.fallback_models[1:]
                
                # 更新选择原因
                new_primary.selection_reason = f"回退机制：主模型 {failed_model_id} 失败，切换到备用模型"
                
                # 创建新的调度结果
                fallback_result = SchedulingResult(
                    task_id=scheduling_result.task_id,
                    selected_models=[new_primary] + remaining_fallbacks,
                    primary_model=new_primary,
                    fallback_models=remaining_fallbacks,
                    total_estimated_cost=scheduling_result.total_estimated_cost,
                    total_estimated_time=scheduling_result.total_estimated_time,
                    scheduling_strategy=scheduling_result.scheduling_strategy
                )
                
                # 记录回退成功的日志
                self.logger.info(f"回退成功：从主模型 {failed_model_id} 切换到备用模型 {new_primary.model_id}")
                
                # 更新模型性能数据
                self._update_model_performance(failed_model_id, success=False)
                self._update_model_performance(new_primary.model_id, success=True)
                
                return fallback_result
            else:
                self.logger.error(f"主模型 {failed_model_id} 失败，但无可用备用模型")
                return scheduling_result
        
        # 如果是备用模型失败，将其从列表中移除
        else:
            updated_fallback_models = [model for model in scheduling_result.fallback_models 
                                     if model.model_id != failed_model_id]
            
            # 创建新的调度结果
            fallback_result = SchedulingResult(
                task_id=scheduling_result.task_id,
                selected_models=[scheduling_result.primary_model] + updated_fallback_models,
                primary_model=scheduling_result.primary_model,
                fallback_models=updated_fallback_models,
                total_estimated_cost=scheduling_result.total_estimated_cost,
                total_estimated_time=scheduling_result.total_estimated_time,
                scheduling_strategy=scheduling_result.scheduling_strategy
            )
            
            # 记录回退日志
            self.logger.info(f"备用模型 {failed_model_id} 失败，已从备用模型列表中移除")
            
            # 更新模型性能数据
            self._update_model_performance(failed_model_id, success=False)
            
            return fallback_result
    
    def _update_model_performance(self, model_id: int, success: bool):
        """更新模型性能数据"""
        try:
            # 获取性能记录
            performance = self.db.query(ModelPerformance).filter(
                ModelPerformance.model_id == model_id
            ).first()
            
            # 如果没有性能记录，创建一个
            if not performance:
                performance = ModelPerformance(
                    model_id=model_id,
                    scene="general",
                    usage_count=0,
                    success_rate=0.0 if success else 100.0
                )
                self.db.add(performance)
            
            # 更新使用次数
            performance.usage_count += 1
            
            # 更新成功率
            if success:
                # 成功时，轻微增加成功率
                if performance.success_rate is None:
                    performance.success_rate = 100.0
                else:
                    # 成功时将成功率略微提高
                    performance.success_rate = min(100.0, performance.success_rate + 0.1)
            else:
                # 失败时，轻微降低成功率
                if performance.success_rate is None:
                    performance.success_rate = 0.0
                else:
                    # 失败时将成功率略微降低
                    performance.success_rate = max(0.0, performance.success_rate - 1.0)
            
            # 记录更新时间
            performance.last_updated = datetime.now()
            
            # 提交数据库更改
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"更新模型性能数据失败: {str(e)}")
            self.db.rollback()
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
                
                # 记录负载均衡日志
                self.logger.info(f"负载均衡：切换主模型 {scheduling_result.primary_model.model_name} 到备用模型 {new_primary.model_name}")
                
                return balanced_result
        
        return scheduling_result
                    total_estimated_time=scheduling_result.total_estimated_time,
                    scheduling_strategy=scheduling_result.scheduling_strategy
                )
                
                return balanced_result
        
        return scheduling_result