"""
模型能力自动发现服务
根据模型名称、描述、供应商等信息自动推断模型的能力
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
import re
import logging

from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.supplier_db import ModelDB
from app.models.model_category import ModelCategory
from app.models.category_capability_association import CategoryCapabilityAssociation


class CapabilityDiscoveryService:
    """
    模型能力自动发现服务类
    
    根据模型名称、描述、供应商等信息自动推断模型的能力，
    并自动关联到相应的模型分类。
    """
    
    # 能力关键词映射表
    CAPABILITY_KEYWORDS = {
        "text_generation": {
            "keywords": ["text", "generation", "gpt", "llama", "claude", "chat", "completion", "instruct", "dialog", "conversation"],
            "display_name": "文本生成",
            "description": "生成自然语言文本的能力",
            "capability_dimension": "generation",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "text_understanding": {
            "keywords": ["understanding", "comprehension", "reading", "nlu", "understand"],
            "display_name": "文本理解",
            "description": "理解和分析自然语言文本的能力",
            "capability_dimension": "comprehension",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "code_generation": {
            "keywords": ["code", "programming", "coder", "developer", "python", "javascript", "java", "cpp", "coding"],
            "display_name": "代码生成",
            "description": "生成和补全程序代码的能力",
            "capability_dimension": "generation",
            "domain": "nlp",
            "input_types": ["text", "code"],
            "output_types": ["code", "text"],
            "base_strength": 3
        },
        "reasoning": {
            "keywords": ["reasoning", "logic", "math", "mathematical", "chain-of-thought", "cot", "think", "analysis"],
            "display_name": "逻辑推理",
            "description": "进行逻辑推理和数学计算的能力",
            "capability_dimension": "reasoning",
            "domain": "reasoning",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "image_generation": {
            "keywords": ["image", "picture", "photo", "visual", "diffusion", "gan", "vae", "stable-diffusion", "dall-e", "midjourney", "sd"],
            "display_name": "图像生成",
            "description": "根据文本描述生成图像的能力",
            "capability_dimension": "generation",
            "domain": "cv",
            "input_types": ["text"],
            "output_types": ["image"],
            "base_strength": 3
        },
        "image_understanding": {
            "keywords": ["vision", "visual", "image-understanding", "image-recognition", "object-detection", "ocr", "image-classification"],
            "display_name": "图像理解",
            "description": "理解和分析图像内容的能力",
            "capability_dimension": "comprehension",
            "domain": "cv",
            "input_types": ["image"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "audio_generation": {
            "keywords": ["audio", "speech", "voice", "tts", "sound", "music", "melody"],
            "display_name": "音频生成",
            "description": "生成语音或音频的能力",
            "capability_dimension": "generation",
            "domain": "audio",
            "input_types": ["text"],
            "output_types": ["audio"],
            "base_strength": 3
        },
        "audio_understanding": {
            "keywords": ["asr", "speech-recognition", "audio-understanding", "whisper", "transcription", "voice-recognition"],
            "display_name": "语音识别",
            "description": "识别和理解语音内容的能力",
            "capability_dimension": "comprehension",
            "domain": "audio",
            "input_types": ["audio"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "multimodal": {
            "keywords": ["multimodal", "vision-language", "vl", "llava", "gpt-4-vision", "gpt-4o", "gemini", "claude-3", "qwen-vl"],
            "display_name": "多模态理解",
            "description": "处理多种模态输入（文本、图像、音频等）的能力",
            "capability_dimension": "multimodal",
            "domain": "multimodal",
            "input_types": ["text", "image", "audio"],
            "output_types": ["text", "image"],
            "base_strength": 3
        },
        "embedding": {
            "keywords": ["embedding", "vector", "representation", "encode", "encoder"],
            "display_name": "文本嵌入",
            "description": "将文本转换为向量表示的能力",
            "capability_dimension": "comprehension",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["vector"],
            "base_strength": 4
        },
        "translation": {
            "keywords": ["translation", "translate", "multilingual", "cross-lingual"],
            "display_name": "机器翻译",
            "description": "在不同语言之间进行翻译的能力",
            "capability_dimension": "generation",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "summarization": {
            "keywords": ["summarization", "summary", "abstract", "digest"],
            "display_name": "文本摘要",
            "description": "对长文本进行摘要的能力",
            "capability_dimension": "generation",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "question_answering": {
            "keywords": ["qa", "question", "answer", "reading-comprehension"],
            "display_name": "问答系统",
            "description": "回答问题的能力",
            "capability_dimension": "reasoning",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "sentiment_analysis": {
            "keywords": ["sentiment", "emotion", "feeling", "opinion", "sentiment-analysis"],
            "display_name": "情感分析",
            "description": "分析文本情感倾向的能力",
            "capability_dimension": "comprehension",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 4
        },
        "named_entity_recognition": {
            "keywords": ["ner", "entity", "named-entity", "recognition"],
            "display_name": "命名实体识别",
            "description": "识别文本中命名实体的能力",
            "capability_dimension": "comprehension",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 4
        },
        "function_calling": {
            "keywords": ["function", "tool", "agent", "action", "api-call", "tool-use"],
            "display_name": "函数调用",
            "description": "调用外部函数和工具的能力",
            "capability_dimension": "interaction",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text", "json"],
            "base_strength": 3
        },
        "long_context": {
            "keywords": ["long-context", "long-context", "128k", "200k", "1m", "extended", "large-context"],
            "display_name": "长上下文处理",
            "description": "处理超长文本上下文的能力",
            "capability_dimension": "memory",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "video_understanding": {
            "keywords": ["video", "video-understanding", "video-analysis", "video-qa"],
            "display_name": "视频理解",
            "description": "理解和分析视频内容的能力",
            "capability_dimension": "comprehension",
            "domain": "multimodal",
            "input_types": ["video"],
            "output_types": ["text"],
            "base_strength": 3
        },
        "rag": {
            "keywords": ["rag", "retrieval", "knowledge", "search", "document"],
            "display_name": "检索增强生成",
            "description": "结合检索和生成的能力",
            "capability_dimension": "reasoning",
            "domain": "nlp",
            "input_types": ["text"],
            "output_types": ["text"],
            "base_strength": 3
        }
    }
    
    # 供应商特定能力映射
    PROVIDER_CAPABILITY_HINTS = {
        "openai": ["text_generation", "function_calling", "multimodal", "code_generation", "reasoning"],
        "anthropic": ["text_generation", "reasoning", "code_generation", "multimodal", "long_context"],
        "google": ["text_generation", "multimodal", "reasoning", "code_generation", "translation"],
        "meta": ["text_generation", "code_generation", "multimodal"],
        "mistral": ["text_generation", "code_generation", "function_calling"],
        "alibaba": ["text_generation", "multimodal", "code_generation", "translation"],
        "baidu": ["text_generation", "translation", "embedding", "image_generation"],
        "tencent": ["text_generation", "multimodal", "embedding"],
        "zhipu": ["text_generation", "code_generation", "multimodal", "embedding"],
        "moonshot": ["text_generation", "long_context"],
        "deepseek": ["text_generation", "code_generation", "reasoning"],
        "stability": ["image_generation"],
        "midjourney": ["image_generation"],
        "runway": ["video_understanding", "image_generation"],
        "elevenlabs": ["audio_generation"],
        "cohere": ["text_generation", "embedding", "rag"],
        "huggingface": ["embedding", "text_generation", "image_generation"]
    }
    
    # 模型分类能力映射
    CATEGORY_CAPABILITY_MAPPING = {
        "chat": ["text_generation", "question_answering", "summarization"],
        "code": ["code_generation", "text_generation", "reasoning"],
        "embedding": ["embedding"],
        "image_generation": ["image_generation"],
        "image_understanding": ["image_understanding", "image_generation"],
        "audio": ["audio_generation", "audio_understanding"],
        "multimodal": ["multimodal", "image_understanding", "text_generation"],
        "reasoning": ["reasoning", "question_answering", "text_generation"],
        "translation": ["translation", "text_generation"],
        "long_context": ["long_context", "text_generation", "rag"],
        "agent": ["function_calling", "text_generation", "reasoning", "rag"]
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def discover_capabilities_for_model(
        self, 
        db: Session, 
        model: ModelDB,
        auto_create: bool = False,
        auto_associate: bool = True
    ) -> Dict[str, Any]:
        """
        为单个模型发现能力
        
        Args:
            db: 数据库会话
            model: 模型对象
            auto_create: 是否自动创建不存在的能力
            auto_associate: 是否自动关联发现的能力
            
        Returns:
            包含发现结果的字典
        """
        discovered_capabilities = []
        confidence_scores = {}
        
        model_info = self._extract_model_info(model)
        
        for capability_name, capability_config in self.CAPABILITY_KEYWORDS.items():
            score = self._calculate_capability_score(model_info, capability_name, capability_config)
            
            if score > 0:
                confidence_scores[capability_name] = score
                
                capability = db.query(ModelCapability).filter(
                    ModelCapability.name == capability_name
                ).first()
                
                if capability:
                    discovered_capabilities.append({
                        "capability": capability,
                        "confidence": score,
                        "source": "discovered"
                    })
                elif auto_create:
                    new_capability = self._create_capability_from_config(
                        db, capability_name, capability_config
                    )
                    if new_capability:
                        discovered_capabilities.append({
                            "capability": new_capability,
                            "confidence": score,
                            "source": "created"
                        })
        
        provider_hints = self._get_provider_hints(model)
        for capability_name in provider_hints:
            if capability_name not in confidence_scores:
                capability = db.query(ModelCapability).filter(
                    ModelCapability.name == capability_name
                ).first()
                
                if capability:
                    discovered_capabilities.append({
                        "capability": capability,
                        "confidence": 0.7,
                        "source": "provider_hint"
                    })
        
        if auto_associate and discovered_capabilities:
            self._associate_capabilities(db, model, discovered_capabilities)
        
        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "discovered_capabilities": [
                {
                    "id": item["capability"].id,
                    "name": item["capability"].name,
                    "display_name": item["capability"].display_name,
                    "confidence": item["confidence"],
                    "source": item["source"]
                }
                for item in discovered_capabilities
            ],
            "total_discovered": len(discovered_capabilities)
        }
    
    def discover_capabilities_for_all_models(
        self, 
        db: Session,
        auto_create: bool = False,
        auto_associate: bool = True,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        为所有模型发现能力
        
        Args:
            db: 数据库会话
            auto_create: 是否自动创建不存在的能力
            auto_associate: 是否自动关联发现的能力
            force_update: 是否强制更新已有关联
            
        Returns:
            包含所有模型发现结果的字典
        """
        models = db.query(ModelDB).filter(ModelDB.is_active == True).all()
        results = []
        total_discovered = 0
        errors = []
        
        for model in models:
            try:
                if not force_update:
                    existing_associations = db.query(ModelCapabilityAssociation).filter(
                        ModelCapabilityAssociation.model_id == model.id
                    ).count()
                    
                    if existing_associations > 0:
                        results.append({
                            "model_id": model.id,
                            "model_name": model.model_name,
                            "skipped": True,
                            "reason": "已有能力关联"
                        })
                        continue
                
                result = self.discover_capabilities_for_model(
                    db, model, auto_create, auto_associate
                )
                results.append(result)
                total_discovered += result["total_discovered"]
                
            except Exception as e:
                self.logger.error(f"为模型 {model.model_name} 发现能力时出错: {str(e)}")
                errors.append({
                    "model_id": model.id,
                    "model_name": model.model_name,
                    "error": str(e)
                })
        
        return {
            "total_models": len(models),
            "processed_models": len(results),
            "total_discovered": total_discovered,
            "results": results,
            "errors": errors
        }
    
    def discover_capabilities_by_category(
        self,
        db: Session,
        category_id: int,
        auto_associate: bool = True
    ) -> Dict[str, Any]:
        """
        根据模型分类发现能力
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            auto_associate: 是否自动关联发现的能力
            
        Returns:
            包含发现结果的字典
        """
        category = db.query(ModelCategory).filter(ModelCategory.id == category_id).first()
        if not category:
            return {
                "success": False,
                "error": f"分类 ID {category_id} 不存在"
            }
        
        category_name = category.name.lower()
        capability_names = self.CATEGORY_CAPABILITY_MAPPING.get(category_name, [])
        
        discovered_capabilities = []
        for capability_name in capability_names:
            capability = db.query(ModelCapability).filter(
                ModelCapability.name == capability_name
            ).first()
            
            if capability:
                discovered_capabilities.append(capability)
        
        associated_capabilities = []
        if auto_associate and discovered_capabilities:
            for capability in discovered_capabilities:
                existing = db.query(CategoryCapabilityAssociation).filter(
                    and_(
                        CategoryCapabilityAssociation.category_id == category_id,
                        CategoryCapabilityAssociation.capability_id == capability.id
                    )
                ).first()
                
                if not existing:
                    association = CategoryCapabilityAssociation(
                        category_id=category_id,
                        capability_id=capability.id,
                        is_default=True,
                        weight=0
                    )
                    db.add(association)
                    associated_capabilities.append({
                        "id": capability.id,
                        "name": capability.name,
                        "display_name": capability.display_name
                    })
            
            db.commit()
        
        return {
            "success": True,
            "category_id": category_id,
            "category_name": category.name,
            "discovered_capabilities": [
                {
                    "id": cap.id,
                    "name": cap.name,
                    "display_name": cap.display_name
                }
                for cap in discovered_capabilities
            ],
            "associated_capabilities": associated_capabilities,
            "total_discovered": len(discovered_capabilities),
            "total_associated": len(associated_capabilities)
        }
    
    def get_capability_suggestions(
        self,
        db: Session,
        model_name: str,
        model_description: str = None,
        supplier_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取模型的能力建议（不自动关联）
        
        Args:
            db: 数据库会话
            model_name: 模型名称
            model_description: 模型描述
            supplier_name: 供应商名称
            
        Returns:
            能力建议列表
        """
        model_info = {
            "name": model_name.lower() if model_name else "",
            "description": model_description.lower() if model_description else "",
            "supplier": supplier_name.lower() if supplier_name else ""
        }
        
        suggestions = []
        
        for capability_name, capability_config in self.CAPABILITY_KEYWORDS.items():
            score = self._calculate_capability_score(model_info, capability_name, capability_config)
            
            if score > 0:
                capability = db.query(ModelCapability).filter(
                    ModelCapability.name == capability_name
                ).first()
                
                suggestions.append({
                    "capability_name": capability_name,
                    "display_name": capability_config["display_name"],
                    "description": capability_config["description"],
                    "confidence": score,
                    "exists": capability is not None,
                    "capability_id": capability.id if capability else None
                })
        
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return suggestions
    
    def _extract_model_info(self, model: ModelDB) -> Dict[str, str]:
        """
        提取模型信息用于能力推断
        """
        return {
            "name": (model.model_name or "").lower(),
            "model_id": (model.model_id or "").lower(),
            "description": (model.description or "").lower(),
            "supplier": (model.supplier.name if model.supplier else "").lower(),
            "category": (model.model_type.name if model.model_type else "").lower() if model.model_type else ""
        }
    
    def _calculate_capability_score(
        self,
        model_info: Dict[str, str],
        capability_name: str,
        capability_config: Dict[str, Any]
    ) -> float:
        """
        计算模型具备某能力的置信度分数
        """
        score = 0.0
        keywords = capability_config.get("keywords", [])
        
        combined_text = f"{model_info['name']} {model_info['model_id']} {model_info['description']}"
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            if keyword_lower in model_info["name"]:
                score += 0.5
            
            if keyword_lower in model_info["model_id"]:
                score += 0.4
            
            if keyword_lower in model_info["description"]:
                score += 0.2
        
        if score > 0:
            score = min(score, 1.0)
        
        return score
    
    def _get_provider_hints(self, model: ModelDB) -> List[str]:
        """
        获取供应商特定的能力提示
        """
        if not model.supplier:
            return []
        
        provider_name = model.supplier.name.lower()
        
        for key, hints in self.PROVIDER_CAPABILITY_HINTS.items():
            if key in provider_name:
                return hints
        
        return []
    
    def _create_capability_from_config(
        self,
        db: Session,
        capability_name: str,
        capability_config: Dict[str, Any]
    ) -> Optional[ModelCapability]:
        """
        根据配置创建能力
        """
        try:
            capability = ModelCapability(
                name=capability_name,
                display_name=capability_config.get("display_name", capability_name),
                description=capability_config.get("description", ""),
                capability_dimension=capability_config.get("capability_dimension", "generation"),
                domain=capability_config.get("domain", "nlp"),
                input_types=capability_config.get("input_types", ["text"]),
                output_types=capability_config.get("output_types", ["text"]),
                base_strength=capability_config.get("base_strength", 3),
                max_strength=5,
                is_active=True,
                is_system=False
            )
            db.add(capability)
            db.commit()
            db.refresh(capability)
            
            self.logger.info(f"自动创建能力: {capability_name}")
            return capability
            
        except Exception as e:
            self.logger.error(f"创建能力 {capability_name} 失败: {str(e)}")
            db.rollback()
            return None
    
    def _associate_capabilities(
        self,
        db: Session,
        model: ModelDB,
        discovered_capabilities: List[Dict[str, Any]]
    ) -> int:
        """
        关联发现的能力到模型
        """
        associated_count = 0
        
        for item in discovered_capabilities:
            capability = item["capability"]
            confidence = item["confidence"]
            
            existing = db.query(ModelCapabilityAssociation).filter(
                and_(
                    ModelCapabilityAssociation.model_id == model.id,
                    ModelCapabilityAssociation.capability_id == capability.id
                )
            ).first()
            
            if not existing:
                association = ModelCapabilityAssociation(
                    model_id=model.id,
                    capability_id=capability.id,
                    actual_strength=capability.base_strength,
                    confidence_score=int(confidence * 100),
                    assessment_method="automated",
                    is_default=False,
                    weight=0
                )
                db.add(association)
                associated_count += 1
        
        if associated_count > 0:
            db.commit()
        
        return associated_count


capability_discovery_service = CapabilityDiscoveryService()
