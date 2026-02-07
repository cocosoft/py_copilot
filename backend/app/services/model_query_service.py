"""模型查询服务模块"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.supplier_db import ModelDB as Model, SupplierDB as ModelSupplier
from app.core.encryption import encryption_tool


class ModelQueryService:
    """模型查询服务类"""
    
    # 本地模型推荐服务实例
    _local_model_recommendation_service = None
    
    @classmethod
    def get_local_model_recommendation_service(cls):
        """获取本地模型推荐服务实例"""
        if cls._local_model_recommendation_service is None:
            from app.services.local_llm.model_recommendation import LocalModelRecommendationService
            cls._local_model_recommendation_service = LocalModelRecommendationService()
        return cls._local_model_recommendation_service
    
    @staticmethod
    def get_all_models(db: Session, is_active: bool = None) -> List[Model]:
        """
        获取所有模型
        
        Args:
            db: 数据库会话
            is_active: 是否只获取激活的模型
            
        Returns:
            模型列表
        """
        query = db.query(Model)
        
        if is_active is not None:
            query = query.filter(Model.is_active == is_active)
            
        return query.all()
    
    @staticmethod
    def get_model_by_id(db: Session, model_id: int) -> Optional[Model]:
        """
        根据ID获取模型
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            模型对象或None
        """
        return db.query(Model).filter(Model.id == model_id).first()
    
    @staticmethod
    def get_model_by_model_id(db: Session, model_id: str) -> Optional[Model]:
        """
        根据模型ID获取模型
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            模型对象或None
        """
        return db.query(Model).filter(Model.model_id == model_id).first()
    
    @staticmethod
    def get_default_model(db: Session, model_type: str = "chat") -> Optional[Model]:
        """
        获取默认模型
        
        Args:
            db: 数据库会话
            model_type: 模型类型（chat, completion, embedding等）
            
        Returns:
            默认模型对象或None
        """
        return db.query(Model).filter(
            Model.is_default == True,
            Model.model_type == model_type,
            Model.is_active == True
        ).first()
    
    @staticmethod
    def get_models_by_supplier(db: Session, supplier_id: int, is_active: bool = None) -> List[Model]:
        """
        根据供应商获取模型
        
        Args:
            db: 数据库会话
            supplier_id: 供应商ID
            is_active: 是否只获取激活的模型
            
        Returns:
            模型列表
        """
        query = db.query(Model).filter(Model.supplier_id == supplier_id)
        
        if is_active is not None:
            query = query.filter(Model.is_active == is_active)
            
        return query.all()
    
    @staticmethod
    def get_supplier_by_id(db: Session, supplier_id: int) -> Optional[ModelSupplier]:
        """
        根据ID获取供应商
        
        Args:
            db: 数据库会话
            supplier_id: 供应商ID
            
        Returns:
            供应商对象或None
        """
        return db.query(ModelSupplier).filter(ModelSupplier.id == supplier_id).first()
    
    @staticmethod
    def get_supplier_with_decrypted_api_key(supplier: ModelSupplier) -> Dict[str, Any]:
        """
        获取带有解密后API密钥的供应商信息
        
        Args:
            supplier: 供应商对象
            
        Returns:
            包含解密后API密钥的供应商信息
        """
        supplier_info = {
            "id": supplier.id,
            "name": supplier.name,
            "api_endpoint": supplier.api_endpoint,
            "api_key_required": supplier.api_key_required,
            "is_active": supplier.is_active,
            "api_key": None  # 确保始终包含api_key键
        }
        
        # API密钥已经通过属性方法自动解密
        if supplier.api_key_required and supplier.api_key:
            supplier_info["api_key"] = supplier.api_key
        
        return supplier_info
    
    @staticmethod
    def get_model_with_supplier(db: Session, model_id: int) -> Optional[Dict[str, Any]]:
        """
        获取模型及其供应商信息（包含解密后的API密钥）
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            包含模型和供应商信息的字典或None
        """
        model = db.query(Model).filter(Model.id == model_id).first()
        
        if not model:
            return None
        
        try:
            supplier_info = ModelQueryService.get_supplier_with_decrypted_api_key(model.supplier)
        except Exception as e:
            print(f"获取供应商信息失败: {e}")
            supplier_info = None
        
        return {
            "model": model,
            "supplier": supplier_info
        }
    
    @staticmethod
    def get_available_models_with_suppliers(db: Session, model_type: str = None) -> List[Dict[str, Any]]:
        """
        获取所有可用模型及其供应商信息
        
        Args:
            db: 数据库会话
            model_type: 模型类型（可选）
            
        Returns:
            包含模型和供应商信息的列表
        """
        query = db.query(Model).filter(Model.is_active == True)
        
        if model_type:
            query = query.filter(Model.model_type == model_type)
            
        models = query.all()
        
        result = []
        for model in models:
            supplier_info = ModelQueryService.get_supplier_with_decrypted_api_key(model.supplier)
            result.append({
                "model": model,
                "supplier": supplier_info
            })
        
        return result
    
    @staticmethod
    def get_available_models_dict(db: Session, model_type: str = None) -> List[Dict[str, Any]]:
        """
        获取可用模型的字典列表，用于前端展示
        
        Args:
            db: 数据库会话
            model_type: 模型类型（可选）
            
        Returns:
            模型字典列表
        """
        models_with_suppliers = ModelQueryService.get_available_models_with_suppliers(db, model_type)
        
        return [
            {
                "id": item["model"].id,
                "model_id": item["model"].model_id,
                "model_name": item["model"].model_name or item["model"].model_id,
                "model_type": item["model"].model_type,
                "supplier_name": item["supplier"]["name"],
                "supplier_id": item["supplier"]["id"],
                "context_window": item["model"].context_window,
                "max_tokens": item["model"].max_tokens,
                "is_default": item["model"].is_default
            }
            for item in models_with_suppliers
        ]
    
    @staticmethod
    async def get_recommended_model(db: Session, task_type: str, task_description: str = None, 
                                   model_type: str = "chat", max_context_window: int = None) -> Optional[Dict[str, Any]]:
        """
        获取推荐的模型
        
        Args:
            db: 数据库会话
            task_type: 任务类型
            task_description: 任务描述（可选）
            model_type: 模型类型（默认chat）
            max_context_window: 最大上下文窗口（可选）
            
        Returns:
            推荐的模型信息字典或None
        """
        try:
            # 获取本地模型推荐服务实例
            recommendation_service = ModelQueryService.get_local_model_recommendation_service()
            
            # 获取所有可用模型
            available_models = ModelQueryService.get_available_models_dict(db, model_type)
            
            # 使用本地模型推荐服务评估和推荐模型
            recommendation_result = await recommendation_service.evaluate_models(
                models=available_models,
                task_type=task_type,
                task_description=task_description,
                db=db
            )
            
            if recommendation_result.get('recommended_model'):
                # 获取推荐模型的详细信息
                recommended_model_info = recommendation_result['recommended_model']
                model_id = recommended_model_info.get('id')
                if model_id:
                    model_with_supplier = ModelQueryService.get_model_with_supplier(db, model_id)
                    if model_with_supplier:
                        # 添加推荐理由和分数
                        model_with_supplier['recommendation_reason'] = recommendation_result.get('reason')
                        model_with_supplier['recommendation_score'] = recommendation_result.get('score')
                        return model_with_supplier
            
            # 如果没有推荐模型，返回默认模型
            default_model = ModelQueryService.get_default_model(db, model_type)
            if default_model:
                return {
                    "model": default_model,
                    "supplier": ModelQueryService.get_supplier_with_decrypted_api_key(default_model.supplier),
                    "recommendation_reason": "使用默认模型",
                    "recommendation_score": 0.5
                }
            
        except Exception as e:
            print(f"获取推荐模型失败: {str(e)}")
        
        return None
    
    @staticmethod
    async def optimize_model_config(db: Session, model_id: int, task_type: str, 
                                   task_description: str = None) -> Dict[str, Any]:
        """
        优化模型配置参数
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            task_type: 任务类型
            task_description: 任务描述（可选）
            
        Returns:
            优化后的配置参数
        """
        try:
            # 获取本地模型推荐服务实例
            recommendation_service = ModelQueryService.get_local_model_recommendation_service()
            
            # 获取模型信息
            model_with_supplier = ModelQueryService.get_model_with_supplier(db, model_id)
            if not model_with_supplier:
                return {"error": "模型不存在"}
            
            # 使用本地模型推荐服务优化配置参数
            optimization_result = await recommendation_service.optimize_config(
                model_name=model_with_supplier["model"].model_id,
                task_type=task_type,
                task_description=task_description,
                db=db
            )
            
            return optimization_result
            
        except Exception as e:
            print(f"优化模型配置失败: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    async def analyze_model_performance(db: Session, model_id: int, 
                                       performance_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分析模型性能数据
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            performance_data: 性能数据（可选）
            
        Returns:
            性能分析结果
        """
        try:
            # 获取本地模型推荐服务实例
            recommendation_service = ModelQueryService.get_local_model_recommendation_service()
            
            # 获取模型信息
            model_with_supplier = ModelQueryService.get_model_with_supplier(db, model_id)
            if not model_with_supplier:
                return {"error": "模型不存在"}
            
            # 使用本地模型推荐服务分析性能数据
            analysis_result = await recommendation_service.analyze_performance_data(
                model_name=model_with_supplier["model"].model,
                performance_data=performance_data,
                db=db
            )
            
            return analysis_result
            
        except Exception as e:
            print(f"分析模型性能失败: {str(e)}")
            return {"error": str(e)}


# 创建全局模型查询服务实例
model_query_service = ModelQueryService()
