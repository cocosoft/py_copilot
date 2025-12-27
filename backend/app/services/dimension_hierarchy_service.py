"""维度层次关系服务 - 处理维度限定类型、类型限定模型的三层关系"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.model_category import ModelCategory, ModelCategoryAssociation
from app.models.supplier_db import ModelDB


class DimensionHierarchyService:
    """维度层次关系服务类"""
    
    # 支持的维度列表
    SUPPORTED_DIMENSIONS = ['tasks', 'languages', 'licenses', 'technologies']
    
    @staticmethod
    def get_dimension_hierarchy(db: Session) -> Dict[str, Any]:
        """
        获取完整的维度层次结构
        
        Returns:
            包含所有维度、类型和模型关系的层次结构
        """
        hierarchy = {
            'dimensions': {},
            'statistics': {
                'total_dimensions': 0,
                'total_categories': 0,
                'total_models': 0
            }
        }
        
        # 获取所有维度下的分类
        for dimension in DimensionHierarchyService.SUPPORTED_DIMENSIONS:
            categories = db.query(ModelCategory).filter(
                ModelCategory.dimension == dimension,
                ModelCategory.is_active == True
            ).all()
            
            dimension_data = {
                'name': dimension,
                'display_name': DimensionHierarchyService.get_dimension_display_name(dimension),
                'categories': [],
                'category_count': len(categories),
                'model_count': 0
            }
            
            # 获取每个分类下的模型
            for category in categories:
                # 获取该分类下的模型关联
                associations = db.query(ModelCategoryAssociation).filter(
                    ModelCategoryAssociation.category_id == category.id
                ).all()
                
                category_models = []
                for association in associations:
                    model = db.query(ModelDB).filter(ModelDB.id == association.model_id).first()
                    if model and model.is_active:
                        category_models.append({
                            'id': model.id,
                            'model_id': model.model_id,
                            'model_name': model.model_name,
                            'supplier_id': model.supplier_id
                        })
                
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'display_name': category.display_name,
                    'models': category_models,
                    'model_count': len(category_models)
                }
                
                dimension_data['categories'].append(category_data)
                dimension_data['model_count'] += len(category_models)
            
            hierarchy['dimensions'][dimension] = dimension_data
        
        # 计算统计信息
        hierarchy['statistics']['total_dimensions'] = len(hierarchy['dimensions'])
        hierarchy['statistics']['total_categories'] = sum(
            len(dim_data['categories']) for dim_data in hierarchy['dimensions'].values()
        )
        hierarchy['statistics']['total_models'] = sum(
            dim_data['model_count'] for dim_data in hierarchy['dimensions'].values()
        )
        
        return hierarchy
    
    @staticmethod
    def get_dimension_display_name(dimension: str) -> str:
        """获取维度的显示名称"""
        display_names = {
            'tasks': '任务类',
            'languages': '语言类',
            'licenses': '协议类',
            'technologies': '技术类'
        }
        return display_names.get(dimension, dimension)
    
    @staticmethod
    def get_models_by_dimension_and_category(db: Session, dimension: str, category_id: int) -> List[Dict[str, Any]]:
        """
        根据维度和分类获取模型列表
        
        Args:
            dimension: 维度标识
            category_id: 分类ID
            
        Returns:
            模型列表
        """
        # 验证维度是否支持
        if dimension not in DimensionHierarchyService.SUPPORTED_DIMENSIONS:
            raise ValueError(f"不支持的维度: {dimension}")
        
        # 验证分类是否存在且属于指定维度
        category = db.query(ModelCategory).filter(
            and_(
                ModelCategory.id == category_id,
                ModelCategory.dimension == dimension,
                ModelCategory.is_active == True
            )
        ).first()
        
        if not category:
            raise ValueError(f"分类ID {category_id} 在维度 {dimension} 下不存在")
        
        # 获取该分类下的模型关联
        associations = db.query(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.category_id == category_id
        ).all()
        
        models = []
        for association in associations:
            model = db.query(ModelDB).filter(
                and_(
                    ModelDB.id == association.model_id,
                    ModelDB.is_active == True
                )
            ).first()
            
            if model:
                models.append({
                    'id': model.id,
                    'model_id': model.model_id,
                    'model_name': model.model_name,
                    'supplier_id': model.supplier_id,
                    'context_window': model.context_window,
                    'max_tokens': model.max_tokens,
                    'is_default': model.is_default
                })
        
        return models
    
    @staticmethod
    def get_model_dimensions(db: Session, model_id: int) -> Dict[str, Any]:
        """
        获取模型所属的所有维度和分类
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型的多维度分类信息
        """
        # 验证模型是否存在
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 获取模型的分类关联
        associations = db.query(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.model_id == model_id
        ).all()
        
        dimensions_data = {}
        
        for association in associations:
            category = db.query(ModelCategory).filter(
                ModelCategory.id == association.category_id
            ).first()
            
            if category and category.is_active:
                dimension = category.dimension
                
                if dimension not in dimensions_data:
                    dimensions_data[dimension] = {
                        'dimension': dimension,
                        'display_name': DimensionHierarchyService.get_dimension_display_name(dimension),
                        'categories': []
                    }
                
                dimensions_data[dimension]['categories'].append({
                    'id': category.id,
                    'name': category.name,
                    'display_name': category.display_name,
                    'association_id': association.id,
                    'weight': association.weight,
                    'association_type': association.association_type
                })
        
        return {
            'model_id': model.id,
            'model_name': model.model_name,
            'dimensions': list(dimensions_data.values())
        }
    
    @staticmethod
    def add_model_to_dimension_category(db: Session, model_id: int, dimension: str, category_id: int, 
                                      weight: int = 0, association_type: str = 'primary') -> ModelCategoryAssociation:
        """
        将模型添加到指定维度的分类中
        
        Args:
            model_id: 模型ID
            dimension: 维度标识
            category_id: 分类ID
            weight: 关联权重
            association_type: 关联类型
            
        Returns:
            创建的关联对象
        """
        # 验证维度是否支持
        if dimension not in DimensionHierarchyService.SUPPORTED_DIMENSIONS:
            raise ValueError(f"不支持的维度: {dimension}")
        
        # 验证模型是否存在
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 验证分类是否存在且属于指定维度
        category = db.query(ModelCategory).filter(
            and_(
                ModelCategory.id == category_id,
                ModelCategory.dimension == dimension,
                ModelCategory.is_active == True
            )
        ).first()
        
        if not category:
            raise ValueError(f"分类ID {category_id} 在维度 {dimension} 下不存在")
        
        # 检查关联是否已存在
        existing_association = db.query(ModelCategoryAssociation).filter(
            and_(
                ModelCategoryAssociation.model_id == model_id,
                ModelCategoryAssociation.category_id == category_id
            )
        ).first()
        
        if existing_association:
            raise ValueError(f"模型 {model_id} 与分类 {category_id} 的关联已存在")
        
        # 创建关联
        association = ModelCategoryAssociation(
            model_id=model_id,
            category_id=category_id,
            weight=weight,
            association_type=association_type
        )
        
        db.add(association)
        db.commit()
        db.refresh(association)
        
        return association
    
    @staticmethod
    def remove_model_from_dimension_category(db: Session, model_id: int, category_id: int) -> bool:
        """
        从指定维度的分类中移除模型
        
        Args:
            model_id: 模型ID
            category_id: 分类ID
            
        Returns:
            是否成功移除
        """
        # 查找关联
        association = db.query(ModelCategoryAssociation).filter(
            and_(
                ModelCategoryAssociation.model_id == model_id,
                ModelCategoryAssociation.category_id == category_id
            )
        ).first()
        
        if not association:
            raise ValueError(f"模型 {model_id} 与分类 {category_id} 的关联不存在")
        
        db.delete(association)
        db.commit()
        
        return True
    
    @staticmethod
    def validate_dimension_constraints(db: Session, model_id: int, dimension: str) -> bool:
        """
        验证模型在指定维度下的约束条件
        
        Args:
            model_id: 模型ID
            dimension: 维度标识
            
        Returns:
            是否满足约束条件
        """
        # 获取模型在指定维度下的所有分类
        associations = db.query(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.model_id == model_id
        ).all()
        
        dimension_categories = []
        for association in associations:
            category = db.query(ModelCategory).filter(
                and_(
                    ModelCategory.id == association.category_id,
                    ModelCategory.dimension == dimension
                )
            ).first()
            
            if category:
                dimension_categories.append(category)
        
        # 约束条件：同一维度下最多只能有一个主要关联
        primary_associations = [
            assoc for assoc in associations 
            if assoc.association_type == 'primary' and 
            any(cat.dimension == dimension for cat in dimension_categories)
        ]
        
        return len(primary_associations) <= 1
    
    @staticmethod
    def remove_all_model_category_associations(db: Session, model_id: int) -> bool:
        """
        删除模型的所有分类关联
        
        Args:
            model_id: 模型ID
            
        Returns:
            是否成功删除
        """
        # 验证模型是否存在
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 删除所有关联
        db.query(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.model_id == model_id
        ).delete()
        
        db.commit()
        return True