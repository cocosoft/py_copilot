"""模型分类服务层，包含CRUD逻辑"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

# ModelCategoryDB导入已移除，使用统一的ModelCategory
from app.models.model_category import ModelCategory, ModelCategoryAssociation
from app.models.supplier_db import ModelDB
from app.schemas.model_category import ModelCategoryCreate, ModelCategoryUpdate

# 导入必要的SQLAlchemy函数
from sqlalchemy import func, distinct

# 导入扩展点管理器
from app.modules.capability_category.extensions.extension_manager import extension_manager


class ModelCategoryService:
    """模型分类服务类"""
    
    @staticmethod
    def create_category(db: Session, category_data: ModelCategoryCreate) -> ModelCategory:
        """创建模型分类"""
        # 执行创建前扩展
        extension_manager.execute_extensions('before_create_category', db=db, category_data=category_data)
        
        # 执行参数验证扩展
        validation_results = extension_manager.execute_extensions('validate_category_params', category_data=category_data)
        # 检查验证结果
        for result in validation_results:
            if result and isinstance(result, dict) and 'error' in result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result['error']
                )
        
        # 检查名称是否已存在
        existing_category = db.query(ModelCategory).filter(
            ModelCategory.name == category_data.name
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"模型分类 '{category_data.name}' 已存在"
            )
        
        # 检查父分类是否存在
        if category_data.parent_id:
            parent_category = db.query(ModelCategory).filter(
                ModelCategory.id == category_data.parent_id
            ).first()
            
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"父分类 ID {category_data.parent_id} 不存在"
                )
        
        # 创建分类对象
        db_category = ModelCategory(**category_data.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
        # 执行创建后扩展
        extension_manager.execute_extensions('after_create_category', db=db, category=db_category)
        
        return db_category
    
    @staticmethod
    def get_category(db: Session, category_id: int) -> Optional[ModelCategory]:
        """获取单个模型分类"""
        # 执行查询前扩展
        extension_manager.execute_extensions('before_get_category', db=db, category_id=category_id)
        
        category = db.query(ModelCategory).filter(
            ModelCategory.id == category_id
        ).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型分类 ID {category_id} 不存在"
            )
        
        # 执行查询后扩展
        extension_manager.execute_extensions('after_get_category', db=db, category=category)
        
        return category
    
    @staticmethod
    def get_category_by_name(db: Session, name: str) -> Optional[ModelCategory]:
        """根据名称获取模型分类"""
        return db.query(ModelCategory).filter(
            ModelCategory.name == name
        ).first()
    
    @staticmethod
    def get_categories(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        parent_id: Optional[int] = None,
        dimension: Optional[str] = None,
        keyword: Optional[str] = None,
        is_system: Optional[bool] = None,
        sort_by: str = "name",  # 默认按名称排序，因为weight字段可能不存在
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """获取模型分类列表 - 支持高级查询功能"""
        # 执行查询前扩展
        extension_manager.execute_extensions('before_get_categories', db=db, 
                                            is_active=is_active, parent_id=parent_id, 
                                            dimension=dimension, keyword=keyword, 
                                            is_system=is_system, sort_by=sort_by, 
                                            sort_order=sort_order)
        
        query = db.query(ModelCategory)
        
        # 应用过滤条件
        if is_active is not None:
            query = query.filter(ModelCategory.is_active == is_active)
        if parent_id is not None:
            query = query.filter(ModelCategory.parent_id == parent_id)
        if dimension:
            query = query.filter(ModelCategory.dimension == dimension)
        if is_system is not None:
            query = query.filter(ModelCategory.is_system == is_system)
        
        # 关键词搜索（支持名称、显示名称、描述）
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    ModelCategory.name.ilike(keyword_pattern),
                    ModelCategory.display_name.ilike(keyword_pattern),
                    ModelCategory.description.ilike(keyword_pattern)
                )
            )
        
        # 排序 - 使用安全的方式访问可能不存在的字段
        if sort_by == "weight":
            # 使用getattr安全访问weight字段，如果不存在则使用0作为默认值
            try:
                if sort_order == "desc":
                    query = query.order_by(getattr(ModelCategory, "weight", 0).desc())
                else:
                    query = query.order_by(getattr(ModelCategory, "weight", 0).asc())
            except Exception:
                # 如果weight字段不存在，回退到按ID排序
                if sort_order == "desc":
                    query = query.order_by(ModelCategory.id.desc())
                else:
                    query = query.order_by(ModelCategory.id.asc())
        elif sort_by == "name":
            if sort_order == "desc":
                query = query.order_by(ModelCategory.name.desc())
            else:
                query = query.order_by(ModelCategory.name.asc())
        elif sort_by == "display_name":
            if sort_order == "desc":
                query = query.order_by(ModelCategory.display_name.desc())
            else:
                query = query.order_by(ModelCategory.display_name.asc())
        elif sort_by == "created_at":
            try:
                if sort_order == "desc":
                    query = query.order_by(getattr(ModelCategory, "created_at", None).desc())
                else:
                    query = query.order_by(getattr(ModelCategory, "created_at", None).asc())
            except Exception:
                # 如果created_at字段不存在，回退到按ID排序
                if sort_order == "desc":
                    query = query.order_by(ModelCategory.id.desc())
                else:
                    query = query.order_by(ModelCategory.id.asc())
        elif sort_by == "updated_at":
            try:
                if sort_order == "desc":
                    query = query.order_by(getattr(ModelCategory, "updated_at", None).desc())
                else:
                    query = query.order_by(getattr(ModelCategory, "updated_at", None).asc())
            except Exception:
                # 如果updated_at字段不存在，回退到按ID排序
                if sort_order == "desc":
                    query = query.order_by(ModelCategory.id.desc())
                else:
                    query = query.order_by(ModelCategory.id.asc())
        else:
            # 默认按ID排序
            if sort_order == "desc":
                query = query.order_by(ModelCategory.id.desc())
            else:
                query = query.order_by(ModelCategory.id.asc())
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        categories = query.offset(skip).limit(limit).all()
        
        # 构建结果
        result = {
            "categories": categories,
            "total": total,
            "filter_params": {
                "is_active": is_active,
                "parent_id": parent_id,
                "dimension": dimension,
                "keyword": keyword,
                "is_system": is_system,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
        # 执行查询后扩展
        extension_manager.execute_extensions_with_result('after_get_categories', result, db=db)
        
        return result
    
    @staticmethod
    def update_category(
        db: Session,
        category_id: int,
        category_update: ModelCategoryUpdate
    ) -> ModelCategory:
        """更新模型分类"""
        db_category = ModelCategoryService.get_category(db, category_id)
        
        # 检查是否为系统分类
        if db_category.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统分类不允许修改"
            )
        
        # 执行更新前扩展
        extension_manager.execute_extensions('before_update_category', db=db, category=db_category, update_data=category_update)
        
        # 执行参数验证扩展
        validation_results = extension_manager.execute_extensions('validate_category_params', category_data=category_update)
        # 检查验证结果
        for result in validation_results:
            if result and isinstance(result, dict) and 'error' in result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result['error']
                )
        
        # 更新非空字段
        update_data = category_update.model_dump(exclude_unset=True)
        
        # 如果更新名称，检查是否重复
        if "name" in update_data:
            existing_category = db.query(ModelCategory).filter(
                and_(
                    ModelCategory.name == update_data["name"],
                    ModelCategory.id != category_id
                )
            ).first()
            
            if existing_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模型分类名称 '{update_data['name']}' 已存在"
                )
        
        # 如果更新父分类，检查是否存在
        if "parent_id" in update_data:
            if update_data["parent_id"]:
                parent_category = db.query(ModelCategory).filter(
                    ModelCategory.id == update_data["parent_id"]
                ).first()
                
                if not parent_category:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"父分类 ID {update_data['parent_id']} 不存在"
                    )
        
        # 执行更新
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        
        # 执行更新后扩展
        extension_manager.execute_extensions('after_update_category', db=db, category=db_category)
        
        return db_category
    
    @staticmethod
    def delete_category(db: Session, category_id: int) -> bool:
        """删除模型分类（软删除）"""
        db_category = ModelCategoryService.get_category(db, category_id)
        
        # 检查是否为系统分类
        if db_category.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统分类不允许删除"
            )
        
        # 执行删除前扩展
        extension_manager.execute_extensions('before_delete_category', db=db, category=db_category)
        
        # 检查是否有子分类
        child_categories = db.query(ModelCategory).filter(
            ModelCategory.parent_id == category_id
        ).count()
        
        if child_categories > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该分类下有子分类，无法删除"
            )
        
        # 检查是否有模型关联
        model_associations = db.query(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.category_id == category_id
        ).count()
        
        if model_associations > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该分类下有模型关联，无法删除"
            )
        
        # 软删除
        db_category.is_active = False
        db.commit()
        
        # 执行删除后扩展
        extension_manager.execute_extensions('after_delete_category', db=db, category_id=category_id)
        
        return True
    
    @staticmethod
    def batch_create_categories(db: Session, categories_data: List[ModelCategoryCreate]) -> List[ModelCategory]:
        """批量创建模型分类"""
        created_categories = []
        
        for category_data in categories_data:
            try:
                # 使用现有的create_category方法创建单个分类
                category = ModelCategoryService.create_category(db, category_data)
                created_categories.append(category)
            except Exception as e:
                # 回滚整个批量操作
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"批量创建分类失败: {str(e)}"
                )
        
        return created_categories
    
    @staticmethod
    def batch_delete_categories(db: Session, category_ids: List[int]) -> Dict[str, Any]:
        """批量删除模型分类"""
        deleted_count = 0
        errors = []
        
        for category_id in category_ids:
            try:
                # 使用现有的delete_category方法删除单个分类
                success = ModelCategoryService.delete_category(db, category_id)
                if success:
                    deleted_count += 1
            except HTTPException as e:
                errors.append({
                    "category_id": category_id,
                    "error": str(e.detail)
                })
            except Exception as e:
                errors.append({
                    "category_id": category_id,
                    "error": f"删除分类失败: {str(e)}"
                })
        
        return {
            "deleted_count": deleted_count,
            "total_count": len(category_ids),
            "errors": errors
        }
    
    @staticmethod
    def get_category_tree(db: Session) -> List[Dict[str, Any]]:
        """获取模型分类的树形结构"""
        # 获取所有分类
        all_categories = db.query(ModelCategory).filter(
            ModelCategory.is_active == True
        ).all()
        
        # 构建分类字典
        category_dict = {cat.id: cat for cat in all_categories}
        
        # 构建树形结构
        root_categories = []
        
        def build_tree(category_id: int) -> Dict[str, Any]:
            category = category_dict[category_id]
            return {
                "id": category.id,
                "name": category.name,
                "display_name": category.display_name,
                "description": category.description,
                "category_type": getattr(category, "category_type", "default"),
                "parent_id": category.parent_id,
                "created_at": category.created_at.isoformat() if category.created_at is not None else None,
                "updated_at": category.updated_at.isoformat() if category.updated_at is not None else None,
                "is_active": category.is_active,
                "children": [
                    build_tree(child_id)
                    for child_id in category_dict
                    if category_dict[child_id].parent_id == category_id
                ]
            }
        
        # 查找根分类并构建树
        for category in all_categories:
            if not category.parent_id:
                root_categories.append(build_tree(category.id))
        
        return root_categories
    
    @staticmethod
    def add_category_to_model(db: Session, model_id: int, category_id: int) -> ModelCategoryAssociation:
        """为模型添加分类"""
        # 执行关联前扩展
        extension_manager.execute_extensions('before_add_category_to_model', db=db, model_id=model_id, category_id=category_id)
        
        # 检查模型是否存在
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {model_id} 不存在"
            )
        
        # 检查分类是否存在
        category = ModelCategoryService.get_category(db, category_id)
        
        # 检查关联是否已存在
        existing_association = db.query(ModelCategoryAssociation).filter(
            and_(
                ModelCategoryAssociation.model_id == model_id,
                ModelCategoryAssociation.category_id == category_id
            )
        ).first()
        
        if existing_association:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模型与分类的关联已存在"
            )
        
        # 创建关联
        association = ModelCategoryAssociation(
            model_id=model_id,
            category_id=category_id
        )
        db.add(association)
        db.commit()
        db.refresh(association)
        
        # 执行关联后扩展
        extension_manager.execute_extensions('after_add_category_to_model', db=db, association=association, model=model, category=category)
        
        return association
    
    @staticmethod
    def remove_category_from_model(db: Session, model_id: int, category_id: int) -> bool:
        """从模型中移除分类"""
        association = db.query(ModelCategoryAssociation).filter(
            and_(
                ModelCategoryAssociation.model_id == model_id,
                ModelCategoryAssociation.category_id == category_id
            )
        ).first()
        
        if not association:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型与分类的关联不存在"
            )
        
        # 执行移除前扩展
        extension_manager.execute_extensions('before_remove_category_from_model', db=db, association=association)
        
        db.delete(association)
        db.commit()
        
        # 执行移除后扩展
        extension_manager.execute_extensions('after_remove_category_from_model', db=db, model_id=model_id, category_id=category_id)
        
        return True
    
    @staticmethod
    def get_models_by_category(db: Session, category_id: int) -> List[ModelDB]:
        """获取指定分类下的所有模型"""
        # 检查分类是否存在
        category = ModelCategoryService.get_category(db, category_id)
        
        # 查询关联的模型
        models = db.query(ModelDB).join(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.category_id == category_id
        ).all()
        
        return models
    
    @staticmethod
    def get_categories_by_model(db: Session, model_id: int) -> List[ModelCategory]:
        """获取指定模型的所有分类"""
        # 检查模型是否存在
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {model_id} 不存在"
            )
        
        # 查询关联的分类
        categories = db.query(ModelCategory).join(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.model_id == model_id
        ).all()
        
        return categories

    @staticmethod
    def get_categories_by_dimension(db: Session, dimension: str) -> List[ModelCategory]:
        """根据维度获取分类"""
        categories = db.query(ModelCategory).filter(
            ModelCategory.dimension == dimension,
            ModelCategory.is_active == True
        ).order_by(getattr(ModelCategory, "weight", 0).desc()).all()
        
        return categories

    @staticmethod
    def get_all_dimensions(db: Session) -> List[str]:
        """获取所有分类维度"""
        # 获取所有唯一的维度值
        dimensions = db.query(ModelCategory.dimension).distinct().all()
        
        # 将结果转换为字符串列表
        return [dim[0] for dim in dimensions]

    @staticmethod
    def get_all_categories_by_dimension(db: Session) -> Dict[str, List[ModelCategory]]:
        """按维度分组获取所有分类"""
        try:
            # 获取所有分类（包括非激活的）
            all_categories = db.query(ModelCategory).all()
            
            # 按维度分组
            categories_by_dim = {}
            for category in all_categories:
                if category.dimension not in categories_by_dim:
                    categories_by_dim[category.dimension] = []
                categories_by_dim[category.dimension].append(category)
            
            return categories_by_dim
        except Exception as e:
            import logging
            logging.error(f"get_all_categories_by_dimension 方法出错: {str(e)}")
            logging.exception("错误堆栈:")
            raise

    @staticmethod
    def get_model_parameters_by_category_hierarchy(
        db: Session, 
        model_id: int
    ) -> Dict[str, Any]:
        """根据模型分类层级获取参数（六级继承体系）"""
        # 获取模型的所有分类
        categories = ModelCategoryService.get_categories_by_model(db, model_id)
        
        if not categories:
            return {}
        
        # 构建参数继承层级
        parameter_hierarchy = {}
        
        for category in categories:
            # 获取分类的默认参数
            if category.default_parameters:
                parameter_hierarchy[f"category_{category.id}"] = {
                    "source": f"category_{category.name}",
                    "parameters": category.default_parameters,
                    "weight": category.weight
                }
            
            # 获取父分类的参数（递归）
            parent_params = ModelCategoryService._get_parent_category_parameters(
                db, category, parameter_hierarchy
            )
            parameter_hierarchy.update(parent_params)
        
        # 合并参数（按权重排序）
        merged_parameters = ModelCategoryService._merge_parameters_by_weight(parameter_hierarchy)
        
        return merged_parameters

    @staticmethod
    def _get_parent_category_parameters(
        db: Session, 
        category: ModelCategory, 
        parameter_hierarchy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """递归获取父分类参数"""
        parent_params = {}
        
        if category.parent_id:
            parent_category = db.query(ModelCategory).filter(
                ModelCategory.id == category.parent_id
            ).first()
            
            if parent_category and parent_category.default_parameters:
                parent_key = f"category_{parent_category.id}"
                if parent_key not in parameter_hierarchy:
                    parent_params[parent_key] = {
                        "source": f"category_{parent_category.name}",
                        "parameters": parent_category.default_parameters,
                        "weight": parent_category.weight
                    }
                    
                    # 递归获取父分类的参数
                    grandparent_params = ModelCategoryService._get_parent_category_parameters(
                        db, parent_category, parameter_hierarchy
                    )
                    parent_params.update(grandparent_params)
        
        return parent_params

    @staticmethod
    def _merge_parameters_by_weight(parameter_hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """根据权重合并参数"""
        # 按权重排序
        sorted_sources = sorted(
            parameter_hierarchy.items(), 
            key=lambda x: x[1]["weight"], 
            reverse=True
        )
        
        merged_parameters = {}
        
        for source_key, source_data in sorted_sources:
            for param_name, param_value in source_data["parameters"].items():
                # 高权重参数覆盖低权重参数
                if param_name not in merged_parameters:
                    merged_parameters[param_name] = {
                        "value": param_value,
                        "source": source_data["source"]
                    }
        
        return merged_parameters

    @staticmethod
    def get_models_by_multiple_categories(
        db: Session,
        category_ids: List[int],
        match_all: bool = True
    ) -> List[ModelDB]:
        """根据多个分类获取模型（支持AND/OR逻辑）"""
        if not category_ids:
            return []
        
        if match_all:
            # AND逻辑：模型必须包含所有指定分类
            query = db.query(ModelDB)
            for category_id in category_ids:
                query = query.filter(
                    ModelDB.id.in_(
                        db.query(ModelCategoryAssociation.model_id).filter(
                            ModelCategoryAssociation.category_id == category_id
                        )
                    )
                )
        else:
            # OR逻辑：模型包含任意一个指定分类
            query = db.query(ModelDB).join(ModelCategoryAssociation).filter(
                ModelCategoryAssociation.category_id.in_(category_ids)
            ).distinct()
        
        return query.all()
    
    @staticmethod
    def get_default_capabilities_by_category(
        db: Session,
        category_id: int
    ) -> List:
        """获取分类的默认能力"""
        from app.models.category_capability_association import CategoryCapabilityAssociation
        from app.models.model_capability import ModelCapability
        
        # 检查分类是否存在
        ModelCategoryService.get_category(db, category_id)
        
        # 查询该分类的默认能力
        default_capabilities = db.query(ModelCapability).join(
            CategoryCapabilityAssociation
        ).filter(
            and_(
                CategoryCapabilityAssociation.category_id == category_id,
                CategoryCapabilityAssociation.is_default == True
            )
        ).all()
        
        return default_capabilities
    
    @staticmethod
    def set_default_capabilities(
        db: Session,
        category_id: int,
        capability_ids: List[int]
    ) -> bool:
        """设置分类的默认能力"""
        from app.models.category_capability_association import CategoryCapabilityAssociation
        from app.models.model_capability import ModelCapability
        
        # 检查分类是否存在
        ModelCategoryService.get_category(db, category_id)
        
        # 检查所有能力是否存在
        for capability_id in capability_ids:
            capability = db.query(ModelCapability).filter(
                ModelCapability.id == capability_id
            ).first()
            if not capability:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"能力 ID {capability_id} 不存在"
                )
        
        # 开始事务
        try:
            # 1. 先将该分类的所有默认能力设置为非默认
            db.query(CategoryCapabilityAssociation).filter(
                and_(
                    CategoryCapabilityAssociation.category_id == category_id,
                    CategoryCapabilityAssociation.is_default == True
                )
            ).update({CategoryCapabilityAssociation.is_default: False})
            
            # 2. 为指定的能力创建或更新关联，并设置为默认
            for capability_id in capability_ids:
                # 查找是否已有关联
                association = db.query(CategoryCapabilityAssociation).filter(
                    and_(
                        CategoryCapabilityAssociation.category_id == category_id,
                        CategoryCapabilityAssociation.capability_id == capability_id
                    )
                ).first()
                
                if association:
                    # 更新现有关联
                    association.is_default = True
                else:
                    # 创建新关联
                    new_association = CategoryCapabilityAssociation(
                        category_id=category_id,
                        capability_id=capability_id,
                        is_default=True
                    )
                    db.add(new_association)
            
            # 提交事务
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"设置默认能力失败: {str(e)}"
            )
    
    @staticmethod
    def get_category_statistics(
        db: Session,
        dimension: Optional[str] = None,
        include_children: bool = False
    ) -> Dict[str, Any]:
        """获取分类使用统计信息
        
        参数:
        - db: 数据库会话
        - dimension: 可选，按维度筛选统计
        - include_children: 是否包含子分类的统计数据
        
        返回:
        - 分类统计信息
        """
        # 主查询：统计每个分类的模型数量
        category_query = db.query(
            ModelCategory.id,
            ModelCategory.name,
            ModelCategory.display_name,
            ModelCategory.dimension,
            ModelCategory.parent_id,
            ModelCategory.is_system,
            ModelCategory.is_active,
            func.count(distinct(ModelCategoryAssociation.model_id)).label('model_count')
        ).outerjoin(
            ModelCategoryAssociation, ModelCategory.id == ModelCategoryAssociation.category_id
        ).group_by(
            ModelCategory.id
        )
        
        # 应用维度过滤
        if dimension:
            category_query = category_query.filter(ModelCategory.dimension == dimension)
        
        # 执行查询获取分类统计数据
        category_stats = category_query.all()
        
        # 按维度分组统计
        dimension_stats = {}
        for stat in category_stats:
            dim = stat.dimension
            if dim not in dimension_stats:
                dimension_stats[dim] = {
                    "total_categories": 0,
                    "total_models": 0,
                    "active_categories": 0,
                    "system_categories": 0
                }
            
            dimension_stats[dim]["total_categories"] += 1
            dimension_stats[dim]["total_models"] += stat.model_count
            if stat.is_active:
                dimension_stats[dim]["active_categories"] += 1
            if stat.is_system:
                dimension_stats[dim]["system_categories"] += 1
        
        # 总统计
        total_categories = sum(stats["total_categories"] for stats in dimension_stats.values())
        total_models = sum(stats["total_models"] for stats in dimension_stats.values())
        total_active = sum(stats["active_categories"] for stats in dimension_stats.values())
        total_system = sum(stats["system_categories"] for stats in dimension_stats.values())
        
        # 简化返回结果，只包含基本统计信息
        return {
            "total_categories": total_categories,
            "total_models": total_models,
            "total_active_categories": total_active,
            "total_system_categories": total_system,
            "dimension_stats": dimension_stats
        }


# 创建服务实例
model_category_service = ModelCategoryService()