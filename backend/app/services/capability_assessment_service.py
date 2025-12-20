"""模型能力评估服务层，包含自动化评估框架"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
import json

from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.supplier_db import ModelDB as Model
from app.schemas.model_capability import CapabilityAssessmentRequest, CapabilityAssessmentResult


class CapabilityAssessmentService:
    """模型能力评估服务类"""
    
    # 预定义的评估指标和基准数据集
    ASSESSMENT_METRICS = {
        "text_generation": {
            "metrics": ["bleu_score", "rouge_score", "perplexity", "human_evaluation"],
            "benchmarks": ["MMLU", "GSM8K", "HumanEval", "TruthfulQA"]
        },
        "image_generation": {
            "metrics": ["fid_score", "inception_score", "clip_score", "human_evaluation"],
            "benchmarks": ["COCO", "ImageNet", "CelebA", "Custom"]
        },
        "speech_recognition": {
            "metrics": ["wer", "cer", "accuracy", "latency"],
            "benchmarks": ["LibriSpeech", "CommonVoice", "TIMIT"]
        },
        "code_generation": {
            "metrics": ["pass_rate", "code_quality", "efficiency", "security"],
            "benchmarks": ["HumanEval", "MBPP", "APPS", "CodeXGLUE"]
        }
    }
    
    @staticmethod
    def assess_capability_strength(
        db: Session,
        model_id: int,
        capability_id: int,
        assessment_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, int]:
        """
        评估模型在特定能力上的强度
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            capability_id: 能力ID
            assessment_data: 评估数据（可选）
            
        Returns:
            Tuple[实际强度, 置信度]
        """
        # 获取模型和能力
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {model_id} 不存在"
            )
        
        capability = db.query(ModelCapability).filter(ModelCapability.id == capability_id).first()
        if not capability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"能力 ID {capability_id} 不存在"
            )
        
        # 获取或创建关联
        association = db.query(ModelCapabilityAssociation).filter(
            and_(
                ModelCapabilityAssociation.model_id == model_id,
                ModelCapabilityAssociation.capability_id == capability_id
            )
        ).first()
        
        if not association:
            # 创建新的关联
            association = ModelCapabilityAssociation(
                model_id=model_id,
                capability_id=capability_id,
                actual_strength=capability.base_strength,
                confidence_score=50,  # 初始置信度较低
                last_assessment_date=datetime.now(),
                assessment_method="initial"
            )
            db.add(association)
        
        # 执行评估逻辑
        actual_strength, confidence_score = CapabilityAssessmentService._perform_assessment(
            model, capability, assessment_data
        )
        
        # 更新关联信息
        association.actual_strength = actual_strength
        association.confidence_score = confidence_score
        association.last_assessment_date = datetime.now()
        association.assessment_method = "automated"
        
        if assessment_data:
            association.assessment_data = assessment_data
        
        db.commit()
        db.refresh(association)
        
        return actual_strength, confidence_score
    
    @staticmethod
    def _perform_assessment(
        model: Model,
        capability: ModelCapability,
        assessment_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, int]:
        """执行具体的评估逻辑"""
        # 基础评估逻辑
        base_strength = capability.base_strength
        
        # 根据模型参数调整强度
        strength_adjustment = 0
        
        # 考虑模型大小
        if model.parameters:
            try:
                params = int(model.parameters.replace("B", "").replace("M", ""))
                if "B" in model.parameters:
                    params *= 1000000000
                elif "M" in model.parameters:
                    params *= 1000000
                
                if params > 10000000000:  # 100亿参数以上
                    strength_adjustment += 1
                elif params > 1000000000:  # 10亿参数以上
                    strength_adjustment += 0.5
            except:
                pass
        
        # 考虑模型参数规模（从描述中推断）
        if model.description:
            description_lower = model.description.lower()
            if "large" in description_lower or "175b" in description_lower or "gpt-4" in description_lower:
                strength_adjustment += 0.5
            elif "medium" in description_lower or "7b" in description_lower or "13b" in description_lower:
                strength_adjustment += 0.3
            elif "small" in description_lower or "1b" in description_lower:
                strength_adjustment += 0.1
        
        # 考虑上下文窗口大小
        if model.context_window:
            if model.context_window > 8000:
                strength_adjustment += 0.3
            elif model.context_window > 4000:
                strength_adjustment += 0.2
            elif model.context_window > 2000:
                strength_adjustment += 0.1
        
        # 应用外部评估数据
        if assessment_data:
            external_score = assessment_data.get("external_score", 0)
            strength_adjustment += external_score * 0.1
        
        # 计算最终强度（1-5级）
        actual_strength = min(max(1, round(base_strength + strength_adjustment)), 5)
        
        # 计算置信度（基于评估数据的完整性）
        confidence_score = 60  # 基础置信度
        
        if model.description and model.context_window:
            confidence_score += 20
        
        if assessment_data and assessment_data.get("benchmark_results"):
            confidence_score += 20
        
        confidence_score = min(confidence_score, 100)
        
        return actual_strength, confidence_score
    
    @staticmethod
    def run_benchmark_assessment(
        db: Session,
        model_id: int,
        capability_name: str,
        benchmark_name: str,
        test_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """运行基准测试评估"""
        # 获取能力
        capability = db.query(ModelCapability).filter(
            ModelCapability.name == capability_name
        ).first()
        
        if not capability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"能力 '{capability_name}' 不存在"
            )
        
        # 检查基准测试是否支持
        if capability_name in CapabilityAssessmentService.ASSESSMENT_METRICS:
            supported_benchmarks = CapabilityAssessmentService.ASSESSMENT_METRICS[capability_name]["benchmarks"]
            if benchmark_name not in supported_benchmarks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"基准测试 '{benchmark_name}' 不支持能力 '{capability_name}'"
                )
        
        # 模拟基准测试执行
        benchmark_results = CapabilityAssessmentService._simulate_benchmark(
            capability_name, benchmark_name, test_data
        )
        
        # 更新能力评估
        actual_strength, confidence_score = CapabilityAssessmentService.assess_capability_strength(
            db, model_id, capability.id, benchmark_results
        )
        
        return {
            "benchmark_name": benchmark_name,
            "capability_name": capability_name,
            "model_id": model_id,
            "actual_strength": actual_strength,
            "confidence_score": confidence_score,
            "results": benchmark_results,
            "assessment_date": datetime.now().isoformat()
        }
    
    @staticmethod
    def _simulate_benchmark(
        capability_name: str,
        benchmark_name: str,
        test_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """模拟基准测试执行（实际实现需要集成真实测试框架）"""
        # 这里模拟基准测试结果
        # 实际实现应该调用真实的基准测试框架
        
        results = {
            "benchmark_name": benchmark_name,
            "capability_name": capability_name,
            "external_score": 0.8,  # 模拟外部评分
            "benchmark_results": {},
            "execution_time": 120.5,  # 秒
            "status": "completed"
        }
        
        # 根据能力类型添加特定指标
        if capability_name == "text_generation":
            results["benchmark_results"] = {
                "bleu_score": 0.45,
                "rouge_score": 0.62,
                "perplexity": 15.3
            }
        elif capability_name == "image_generation":
            results["benchmark_results"] = {
                "fid_score": 12.5,
                "inception_score": 8.7,
                "clip_score": 0.75
            }
        elif capability_name == "code_generation":
            results["benchmark_results"] = {
                "pass_rate": 0.82,
                "code_quality": 0.78,
                "efficiency": 0.65
            }
        
        # 如果有测试数据，更新结果
        if test_data:
            results.update(test_data)
        
        return results
    
    @staticmethod
    def get_capability_assessment_history(
        db: Session,
        model_id: int,
        capability_id: int
    ) -> List[Dict[str, Any]]:
        """获取能力评估历史"""
        association = db.query(ModelCapabilityAssociation).filter(
            and_(
                ModelCapabilityAssociation.model_id == model_id,
                ModelCapabilityAssociation.capability_id == capability_id
            )
        ).first()
        
        if not association:
            return []
        
        # 这里可以扩展为存储完整的评估历史
        # 目前只返回当前评估信息
        return [{
            "assessment_date": association.last_assessment_date.isoformat() if association.last_assessment_date else None,
            "actual_strength": association.actual_strength,
            "confidence_score": association.confidence_score,
            "assessment_method": association.assessment_method,
            "assessment_data": association.assessment_data
        }]
    
    @staticmethod
    def compare_models_by_capability(
        db: Session,
        capability_id: int,
        model_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """比较多个模型在特定能力上的表现"""
        comparison_results = []
        
        for model_id in model_ids:
            # 获取模型能力关联
            association = db.query(ModelCapabilityAssociation).filter(
                and_(
                    ModelCapabilityAssociation.model_id == model_id,
                    ModelCapabilityAssociation.capability_id == capability_id
                )
            ).first()
            
            if association:
                model = db.query(Model).filter(Model.id == model_id).first()
                comparison_results.append({
                    "model_id": model_id,
                    "model_name": model.model_name if model else "Unknown",
                    "actual_strength": association.actual_strength,
                    "confidence_score": association.confidence_score,
                    "last_assessment": association.last_assessment_date.isoformat() if association.last_assessment_date else None
                })
        
        # 按强度排序
        comparison_results.sort(key=lambda x: x["actual_strength"], reverse=True)
        
        return comparison_results
    
    @staticmethod
    def get_recommended_models_for_task(
        db: Session,
        task_description: str,
        required_capabilities: List[str],
        min_strength: int = 3
    ) -> List[Dict[str, Any]]:
        """根据任务需求推荐合适的模型"""
        # 这里可以实现基于任务描述和所需能力的智能推荐
        # 目前实现基础版本
        
        recommended_models = []
        
        for capability_name in required_capabilities:
            # 获取能力
            capability = db.query(ModelCapability).filter(
                ModelCapability.name == capability_name
            ).first()
            
            if capability:
                # 获取具有该能力的模型
                models = db.query(Model).join(ModelCapabilityAssociation).filter(
                    and_(
                        ModelCapabilityAssociation.capability_id == capability.id,
                        ModelCapabilityAssociation.actual_strength >= min_strength
                    )
                ).all()
                
                for model in models:
                    # 获取模型在该能力上的评估
                    association = db.query(ModelCapabilityAssociation).filter(
                        and_(
                            ModelCapabilityAssociation.model_id == model.id,
                            ModelCapabilityAssociation.capability_id == capability.id
                        )
                    ).first()
                    
                    if association:
                        recommended_models.append({
                            "model_id": model.id,
                            "model_name": model.model_name,
                            "capability": capability_name,
                            "strength": association.actual_strength,
                            "confidence": association.confidence_score,
                            "recommendation_reason": f"在{capability.display_name}能力上表现优秀"
                        })
        
        # 去重并按强度排序
        unique_models = {}
        for model in recommended_models:
            model_id = model["model_id"]
            if model_id not in unique_models or model["strength"] > unique_models[model_id]["strength"]:
                unique_models[model_id] = model
        
        return sorted(unique_models.values(), key=lambda x: x["strength"], reverse=True)


capability_assessment_service = CapabilityAssessmentService()