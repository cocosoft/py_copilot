"""基于能力的模型筛选服务"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.supplier_db import ModelDB
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation


class CapabilityBasedModelFilter:
    """基于能力的模型筛选器"""
    
    # 场景-能力映射表 - 只基于能力名称匹配，不关心强度
    SCENE_CAPABILITY_MAPPING = {
        "chat": ["chat", "multi_turn_conversation", "context_management", "text_generation"],
        "translate": ["translation", "language_translation", "text_generation"],
        "topic_title": ["text_summarization", "keyword_extraction"]
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_models_for_scene(self, scene: str) -> List[ModelDB]:
        """
        根据场景获取符合条件的模型（基于能力名称匹配）
        
        Args:
            scene: 场景名称
            
        Returns:
            符合条件的模型列表
        """
        # 获取场景对应的能力需求
        scene_capabilities = self._get_scene_capabilities(scene)
        
        if not scene_capabilities:
            # 如果没有特定能力要求，返回所有活跃模型
            return self.db.query(ModelDB).filter(ModelDB.is_active == True).all()
        
        # 使用SQL查询直接筛选具有指定能力的模型
        qualified_models = self.db.query(ModelDB).join(
            ModelCapabilityAssociation,
            ModelDB.id == ModelCapabilityAssociation.model_id
        ).join(
            ModelCapability,
            ModelCapabilityAssociation.capability_id == ModelCapability.id
        ).filter(
            ModelDB.is_active == True,
            ModelCapability.name.in_(scene_capabilities)
        ).distinct().all()
        
        return qualified_models
    
    def get_models_with_capability_scores(self, scene: str) -> List[Dict[str, Any]]:
        """
        获取模型及其能力匹配度评分（简化版本，只基于能力名称匹配）
        
        Args:
            scene: 场景名称
            
        Returns:
            包含模型和匹配度信息的列表
        """
        # 获取符合条件的模型
        qualified_models = self.get_models_for_scene(scene)
        
        result = []
        
        for model in qualified_models:
            # 简化匹配度计算：只要模型具有场景所需的能力，就认为是100%匹配
            result.append({
                "model": model,
                "match_score": 1.0,
                "match_percentage": 100,
                "satisfied_requirements": {capability: True for capability in self._get_scene_capabilities(scene)}
            })
        
        return result
    
    def _get_scene_capabilities(self, scene: str) -> List[str]:
        """获取场景对应的能力需求"""
        return self.SCENE_CAPABILITY_MAPPING.get(scene, [])
    
    def _get_model_has_capability(self, model_id: int, capability_name: str) -> bool:
        """检查模型是否具有特定能力"""
        association = self.db.query(ModelCapabilityAssociation).join(
            ModelCapability,
            ModelCapabilityAssociation.capability_id == ModelCapability.id
        ).filter(
            ModelCapabilityAssociation.model_id == model_id,
            ModelCapability.name == capability_name
        ).first()
        
        return association is not None
    
    def get_available_scenes(self) -> List[str]:
        """获取所有可用的场景"""
        return list(self.SCENE_CAPABILITY_MAPPING.keys())
    
    def calculate_capability_score(self, model: ModelDB, scene: str) -> float:
        """
        计算模型在指定场景下的能力匹配度
        
        Args:
            model: 模型对象
            scene: 场景名称
            
        Returns:
            能力匹配度分数（0.0-1.0）
        """
        scene_capabilities = self._get_scene_capabilities(scene)
        return self._calculate_capability_match_score(model, scene_capabilities)
    
    def _calculate_capability_match_score(self, model: ModelDB, scene_capabilities: List[str]) -> float:
        """
        计算模型与场景能力需求的匹配度分数
        
        Args:
            model: 模型对象
            scene_capabilities: 场景所需的能力列表
            
        Returns:
            能力匹配度分数（0.0-1.0）
        """
        if not scene_capabilities:
            return 1.0
        
        # 计算模型具有的场景所需能力数量
        matched_capabilities = 0
        for capability in scene_capabilities:
            if self._get_model_has_capability(model.id, capability):
                matched_capabilities += 1
        
        # 计算匹配度分数
        return matched_capabilities / len(scene_capabilities)