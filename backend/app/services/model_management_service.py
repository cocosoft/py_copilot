"""
模型管理服务层

提供模型管理相关的业务逻辑，包括模型的CRUD操作、参数管理、分类管理等。
遵循分层架构原则，将业务逻辑从API层分离出来。
集成缓存功能，提高数据访问性能。
"""

import logging
from typing import Any, List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from fastapi import HTTPException, status

from app.models.supplier_db import ModelDB, ModelParameter, SupplierDB
from app.models.model_category import ModelCategory
from app.schemas.model_management import (
    ModelCreate, ModelUpdate, ModelResponse, ModelWithSupplierResponse,
    ModelParameterCreate, ModelParameterUpdate, ModelParameterResponse
)
from app.modules.model_management.utils.model_cache import (
    ModelCacheService, model_cache_service
)

logger = logging.getLogger(__name__)


class ModelManagementService:
    """
    模型管理服务类
    
    提供模型管理相关的业务逻辑，包括：
    - 模型的增删改查
    - 模型参数管理
    - 模型分类管理
    - 默认模型设置
    """
    
    def __init__(self, db: Session):
        """
        初始化模型管理服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    # ==================== 模型查询操作 ====================
    
    def get_all_models(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[ModelWithSupplierResponse], int]:
        """
        获取所有模型列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
        
        Returns:
            tuple: (模型列表, 总数)
        """
        # 查询数据库获取所有模型数据，包括供应商信息
        models = self.db.query(ModelDB).options(
            joinedload(ModelDB.supplier)
        ).offset(skip).limit(limit).all()
        
        total = self.db.query(ModelDB).count()
        
        # 转换为响应格式
        model_responses = []
        for model in models:
            model_response = self._convert_model_to_response(model)
            model_responses.append(model_response)
        
        return model_responses, total
    
    def get_models_by_supplier(
        self,
        supplier_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[ModelWithSupplierResponse], int]:
        """
        获取指定供应商的模型列表
        
        Args:
            supplier_id: 供应商ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
        
        Returns:
            tuple: (模型列表, 总数)
        
        Raises:
            HTTPException: 供应商不存在时抛出
        """
        # 验证供应商是否存在
        supplier = self.db.query(SupplierDB).filter(
            SupplierDB.id == supplier_id
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="供应商不存在"
            )
        
        # 查询模型列表
        models = self.db.query(ModelDB).options(
            joinedload(ModelDB.supplier)
        ).filter(
            ModelDB.supplier_id == supplier_id
        ).offset(skip).limit(limit).all()
        
        total = self.db.query(ModelDB).filter(
            ModelDB.supplier_id == supplier_id
        ).count()
        
        # 转换为响应格式
        model_responses = []
        for model in models:
            model_response = self._convert_model_to_response(model)
            model_responses.append(model_response)
        
        return model_responses, total
    
    def get_model_by_id(self, model_id: int) -> Optional[ModelWithSupplierResponse]:
        """
        根据ID获取模型详情
        
        Args:
            model_id: 模型ID
        
        Returns:
            模型详情，不存在时返回None
        """
        model = self.db.query(ModelDB).options(
            joinedload(ModelDB.supplier)
        ).filter(ModelDB.id == model_id).first()
        
        if not model:
            return None
        
        return self._convert_model_to_response(model)
    
    def get_model_by_model_id(self, model_id: str) -> Optional[ModelWithSupplierResponse]:
        """
        根据模型ID获取模型详情
        
        Args:
            model_id: 模型标识符
        
        Returns:
            模型详情，不存在时返回None
        """
        model = self.db.query(ModelDB).options(
            joinedload(ModelDB.supplier)
        ).filter(ModelDB.model_id == model_id).first()
        
        if not model:
            return None
        
        return self._convert_model_to_response(model)
    
    # ==================== 模型创建和更新 ====================
    
    def create_model(
        self,
        supplier_id: int,
        model_data: Dict[str, Any],
        logo_path: Optional[str] = None
    ) -> ModelDB:
        """
        创建新模型
        
        Args:
            supplier_id: 供应商ID
            model_data: 模型数据字典
            logo_path: Logo文件路径（可选）
        
        Returns:
            创建的模型对象
        
        Raises:
            HTTPException: 创建失败时抛出
        """
        # 确保supplier_id一致
        model_data['supplier_id'] = supplier_id
        
        # 如果提供了logo路径，更新到数据中
        if logo_path:
            model_data['logo'] = logo_path
        
        # 处理模型类型：验证分类是否存在
        if 'model_type_id' in model_data:
            category = self.db.query(ModelCategory).filter(
                ModelCategory.id == model_data['model_type_id']
            ).first()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模型分类ID {model_data['model_type_id']} 不存在"
                )
        
        # 如果存在旧的model_type字段（用于向后兼容），则删除
        if 'model_type' in model_data:
            del model_data['model_type']
        
        try:
            # 创建新模型
            db_model = ModelDB(**model_data)
            self.db.add(db_model)
            
            # 处理默认模型逻辑
            self._handle_default_model_logic(db_model, supplier_id)
            
            self.db.commit()
            self.db.refresh(db_model)
            
            # 使相关缓存失效
            self._invalidate_cache(supplier_id=supplier_id)
            
            logger.info(f"模型创建成功: ID={db_model.id}, 名称={db_model.model_name}")
            
            return db_model
            
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"创建模型失败: {str(e)}"
            )
    
    def update_model(
        self,
        model_id: int,
        model_data: Dict[str, Any],
        logo_path: Optional[str] = None
    ) -> ModelDB:
        """
        更新模型
        
        Args:
            model_id: 模型ID
            model_data: 模型数据字典
            logo_path: Logo文件路径（可选）
        
        Returns:
            更新后的模型对象
        
        Raises:
            HTTPException: 模型不存在或更新失败时抛出
        """
        # 查找模型
        db_model = self.db.query(ModelDB).filter(ModelDB.id == model_id).first()
        
        if not db_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )
        
        # 如果提供了logo路径，更新到数据中
        if logo_path:
            model_data['logo'] = logo_path
        
        # 验证分类是否存在
        if 'model_type_id' in model_data and model_data['model_type_id']:
            category = self.db.query(ModelCategory).filter(
                ModelCategory.id == model_data['model_type_id']
            ).first()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模型分类ID {model_data['model_type_id']} 不存在"
                )
        
        try:
            # 更新模型字段
            for key, value in model_data.items():
                if hasattr(db_model, key) and value is not None:
                    setattr(db_model, key, value)
            
            # 处理默认模型逻辑
            if model_data.get('is_default') is True:
                self._unset_other_default_models(
                    db_model.supplier_id,
                    db_model.id
                )
            
            self.db.commit()
            self.db.refresh(db_model)
            
            # 使相关缓存失效
            self._invalidate_cache(
                model_id=model_id,
                supplier_id=db_model.supplier_id
            )
            
            logger.info(f"模型更新成功: ID={db_model.id}, 名称={db_model.model_name}")
            
            return db_model
            
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"更新模型失败: {str(e)}"
            )
    
    def delete_model(self, model_id: int) -> None:
        """
        删除模型
        
        Args:
            model_id: 模型ID
        
        Raises:
            HTTPException: 模型不存在时抛出
        """
        # 查找模型
        db_model = self.db.query(ModelDB).filter(ModelDB.id == model_id).first()
        
        if not db_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )
        
        # 保存供应商ID用于缓存失效
        supplier_id = db_model.supplier_id
        
        # 删除模型（关联的参数会自动删除）
        self.db.delete(db_model)
        self.db.commit()
        
        # 使相关缓存失效
        self._invalidate_cache(
            model_id=model_id,
            supplier_id=supplier_id
        )
        
        logger.info(f"模型删除成功: ID={model_id}")
    
    # ==================== 默认模型管理 ====================
    
    def set_default_model(self, model_id: int) -> ModelDB:
        """
        设置默认模型
        
        Args:
            model_id: 模型ID
        
        Returns:
            设置为默认的模型对象
        
        Raises:
            HTTPException: 模型不存在时抛出
        """
        # 查找模型
        db_model = self.db.query(ModelDB).filter(ModelDB.id == model_id).first()
        
        if not db_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )
        
        # 取消该供应商的其他默认模型
        self._unset_other_default_models(db_model.supplier_id, model_id)
        
        # 设置当前模型为默认
        db_model.is_default = True
        self.db.commit()
        self.db.refresh(db_model)
        
        return db_model
    
    def get_default_model(self, supplier_id: Optional[int] = None) -> Optional[ModelDB]:
        """
        获取默认模型
        
        Args:
            supplier_id: 供应商ID（可选）
        
        Returns:
            默认模型对象，不存在时返回None
        """
        query = self.db.query(ModelDB).filter(ModelDB.is_default == True)
        
        if supplier_id:
            query = query.filter(ModelDB.supplier_id == supplier_id)
        
        return query.first()
    
    # ==================== 模型参数管理 ====================
    
    def get_model_parameters(
        self,
        model_id: int
    ) -> List[ModelParameterResponse]:
        """
        获取模型的参数列表
        
        Args:
            model_id: 模型ID
        
        Returns:
            参数列表
        """
        parameters = self.db.query(ModelParameter).filter(
            ModelParameter.model_id == model_id
        ).all()
        
        return [
            ModelParameterResponse.model_validate(param)
            for param in parameters
        ]
    
    def create_model_parameter(
        self,
        model_id: int,
        param_data: Dict[str, Any]
    ) -> ModelParameter:
        """
        创建模型参数
        
        Args:
            model_id: 模型ID
            param_data: 参数数据字典
        
        Returns:
            创建的参数对象
        
        Raises:
            HTTPException: 创建失败时抛出
        """
        # 验证模型是否存在
        model = self.db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )
        
        param_data['model_id'] = model_id
        
        try:
            db_param = ModelParameter(**param_data)
            self.db.add(db_param)
            self.db.commit()
            self.db.refresh(db_param)
            
            return db_param
            
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"创建参数失败: {str(e)}"
            )
    
    def update_model_parameter(
        self,
        param_id: int,
        param_data: Dict[str, Any]
    ) -> ModelParameter:
        """
        更新模型参数
        
        Args:
            param_id: 参数ID
            param_data: 参数数据字典
        
        Returns:
            更新后的参数对象
        
        Raises:
            HTTPException: 参数不存在或更新失败时抛出
        """
        # 查找参数
        db_param = self.db.query(ModelParameter).filter(
            ModelParameter.id == param_id
        ).first()
        
        if not db_param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="参数不存在"
            )
        
        # 更新参数字段
        for key, value in param_data.items():
            if hasattr(db_param, key) and value is not None:
                setattr(db_param, key, value)
        
        self.db.commit()
        self.db.refresh(db_param)
        
        return db_param
    
    def delete_model_parameter(self, param_id: int) -> None:
        """
        删除模型参数
        
        Args:
            param_id: 参数ID
        
        Raises:
            HTTPException: 参数不存在时抛出
        """
        # 查找参数
        db_param = self.db.query(ModelParameter).filter(
            ModelParameter.id == param_id
        ).first()
        
        if not db_param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="参数不存在"
            )
        
        self.db.delete(db_param)
        self.db.commit()
    
    # ==================== 私有辅助方法 ====================
    
    def _convert_model_to_response(
        self,
        model: ModelDB
    ) -> ModelWithSupplierResponse:
        """
        将模型数据库对象转换为响应对象
        
        Args:
            model: 模型数据库对象
        
        Returns:
            模型响应对象
        """
        # 确保logo字段包含完整路径
        logo = model.logo
        if logo and not logo.startswith("/logos/models/"):
            logo = f"/logos/models/{logo}"
        
        # 构建供应商响应
        from app.modules.supplier_model_management.schemas.supplier_model import (
            ModelSupplierResponse
        )
        
        supplier_response = ModelSupplierResponse(
            id=model.supplier.id,
            name=model.supplier.name or "",
            display_name=model.supplier.display_name or model.supplier.name or "",
            description=model.supplier.description,
            is_active=model.supplier.is_active,
            logo=model.supplier.logo,
            created_at=model.supplier.created_at or datetime.now(),
            updated_at=model.supplier.updated_at,
            api_endpoint=model.supplier.api_endpoint,
            api_key_required=model.supplier.api_key_required,
            category=model.supplier.category,
            website=model.supplier.website,
            api_docs=model.supplier.api_docs
        )
        
        # 构建模型响应
        return ModelWithSupplierResponse(
            id=model.id,
            model_id=model.model_id or str(model.id),
            model_name=model.model_name or model.model_id or "Unknown Model",
            description=model.description,
            type="chat",  # 默认类型
            supplier_id=model.supplier_id,
            context_window=model.context_window or 8000,
            default_temperature=0.7,
            default_max_tokens=model.max_tokens or 1000,
            default_top_p=1.0,
            default_frequency_penalty=0.0,
            default_presence_penalty=0.0,
            custom_params=None,
            is_default=model.is_default,
            is_active=model.is_active,
            logo=logo,
            created_at=model.created_at or datetime.now(),
            updated_at=model.updated_at,
            supplier=supplier_response
        )
    
    def _handle_default_model_logic(
        self,
        db_model: ModelDB,
        supplier_id: int
    ) -> None:
        """
        处理默认模型逻辑
        
        如果设置为默认模型，取消该供应商的其他默认模型。
        如果是第一个模型，自动设为默认。
        
        Args:
            db_model: 模型对象
            supplier_id: 供应商ID
        """
        if db_model.is_default is True:
            self._unset_other_default_models(supplier_id, db_model.id)
        elif self.db.query(ModelDB).filter(
            ModelDB.supplier_id == supplier_id
        ).count() == 0:
            # 如果是第一个模型，自动设为默认
            db_model.is_default = True
    
    def _unset_other_default_models(
        self,
        supplier_id: int,
        exclude_model_id: int
    ) -> None:
        """
        取消该供应商的其他默认模型
        
        Args:
            supplier_id: 供应商ID
            exclude_model_id: 要排除的模型ID
        """
        self.db.query(ModelDB).filter(
            ModelDB.supplier_id == supplier_id,
            ModelDB.id != exclude_model_id
        ).update({ModelDB.is_default: False})
    
    def _invalidate_cache(
        self,
        model_id: Optional[int] = None,
        supplier_id: Optional[int] = None
    ) -> None:
        """
        使相关缓存失效
        
        在数据变更后调用，确保缓存数据的一致性。
        
        Args:
            model_id: 模型ID（可选）
            supplier_id: 供应商ID（可选）
        """
        import asyncio
        
        try:
            # 获取事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 执行缓存失效
            if model_id:
                loop.run_until_complete(
                    model_cache_service.invalidate_model(model_id)
                )
            
            if supplier_id:
                loop.run_until_complete(
                    model_cache_service.invalidate_supplier_models(supplier_id)
                )
            
            # 使所有模型列表缓存失效
            loop.run_until_complete(
                model_cache_service.invalidate_all_models()
            )
            
        except Exception as e:
            logger.warning(f"缓存失效操作失败: {str(e)}")


# ==================== 依赖注入函数 ====================

def get_model_management_service(db: Session) -> ModelManagementService:
    """
    获取模型管理服务实例（用于依赖注入）
    
    Args:
        db: 数据库会话
    
    Returns:
        模型管理服务实例
    """
    return ModelManagementService(db)
