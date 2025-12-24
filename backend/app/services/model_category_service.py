"""模型分类服务层，包含CRUD逻辑"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.model_category import ModelCategory, ModelCategoryAssociation
from app.models.supplier_db import ModelDB as Model
from app.schemas.model_category import ModelCategoryCreate, ModelCategoryUpdate


class ModelCategoryService:
    """模型分类服务类"""
    
    @staticmethod
    def create_category(db: Session, category_data: Dict[str, Any]) -> ModelCategory:
        """创建模型分类"""
        # 检查名称是否已存在
        existing_category = db.query(ModelCategory).filter(
            ModelCategory.name == category_data['name']
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"模型分类 '{category_data['name']}' 已存在"
            )
        
        # 检查父分类是否存在
        parent_id = category_data.get('parent_id')
        if parent_id:
            parent_category = db.query(ModelCategory).filter(
                ModelCategory.id == parent_id
            ).first()
            
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"父分类 ID {parent_id} 不存在"
                )
            
            # 检查分类层级（最多支持四级分类：系统分类 + 三级子分类）
            level = 0
            current_category = parent_category
            while current_category:
                level += 1
                current_category = db.query(ModelCategory).filter(
                    ModelCategory.id == current_category.parent_id
                ).first()
            
            # level 是父分类的层级，新分类的层级是 level + 1
            # 系统分类是 level 1，新分类最多支持到 level 4
            if level + 1 > 4:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="分类层级最多支持四级（系统分类 + 三级子分类）"
                )
        
        # 确保只有系统分类可以作为一级分类
        if not parent_id and not category_data.get('is_system', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有系统分类可以作为一级分类"
            )
        
        # 创建新分类
        db_category = ModelCategory(**category_data)
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
        return db_category
    
    @staticmethod
    def get_category(db: Session, category_id: int) -> Optional[ModelCategory]:
        """获取单个模型分类"""
        category = db.query(ModelCategory).filter(
            ModelCategory.id == category_id
        ).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型分类 ID {category_id} 不存在"
            )
        
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
        category_type: Optional[str] = None,  # 保留参数但不使用，避免API调用错误
        is_active: Optional[bool] = None,
        parent_id: Optional[int] = None,
        dimension: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取模型分类列表"""
        query = db.query(ModelCategory)
        
        # 应用过滤条件
        if is_active is not None:
            query = query.filter(ModelCategory.is_active == is_active)
        if parent_id is not None:
            query = query.filter(ModelCategory.parent_id == parent_id)
        if dimension:
            query = query.filter(ModelCategory.dimension == dimension)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        categories = query.offset(skip).limit(limit).all()
        
        # 直接返回ORM对象，让Pydantic模型自动转换
        return {
            "categories": categories,
            "total": total
        }
    
    @staticmethod
    def update_category(
        db: Session,
        category_id: int,
        category_update: Dict[str, Any]
    ) -> ModelCategory:
        """更新模型分类"""
        db_category = ModelCategoryService.get_category(db, category_id)
        
        # 检查是否为系统分类
        if db_category.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统分类不允许修改"
            )
        
        # 更新非空字段
        update_data = category_update
        
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
        
        # 如果更新父分类，检查是否存在并验证层级限制
        if "parent_id" in update_data:
            new_parent_id = update_data["parent_id"]
            if new_parent_id:
                parent_category = db.query(ModelCategory).filter(
                    ModelCategory.id == new_parent_id
                ).first()
                
                if not parent_category:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"父分类 ID {new_parent_id} 不存在"
                    )
                
                # 检查分类层级（最多支持四级分类：系统分类 + 三级子分类）
                level = 0
                current_category = parent_category
                while current_category:
                    level += 1
                    if level >= 4:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="分类层级最多支持四级（系统分类 + 三级子分类）"
                        )
                    current_category = db.query(ModelCategory).filter(
                        ModelCategory.id == current_category.parent_id
                    ).first()
        
        # 执行更新
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        
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
        
        return True
    
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

                "parent_id": category.parent_id,
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
    def get_all_dimensions(db: Session) -> List[str]:
        """获取所有分类维度"""
        dimensions = db.query(ModelCategory.dimension).distinct().all()
        return [dim[0] for dim in dimensions]
    
    @staticmethod
    def get_categories_by_dimension(db: Session) -> Dict[str, List[ModelCategory]]:
        """按维度分组获取所有分类"""
        all_categories = db.query(ModelCategory).filter(
            ModelCategory.is_active == True
        ).all()
        
        dimension_dict = {}
        for category in all_categories:
            if category.dimension not in dimension_dict:
                dimension_dict[category.dimension] = []
            dimension_dict[category.dimension].append(category)
        
        return dimension_dict
    
    @staticmethod
    def add_category_to_model(db: Session, model_id: int, category_id: int) -> ModelCategoryAssociation:
        """为模型添加分类"""
        # 检查模型是否存在
        model = db.query(Model).filter(Model.id == model_id).first()
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
        
        db.delete(association)
        db.commit()
        
        return True
    
    @staticmethod
    def get_models_by_category(db: Session, category_id: int) -> List[Model]:
        """获取指定分类下的所有模型"""
        # 检查分类是否存在
        category = ModelCategoryService.get_category(db, category_id)
        
        # 查询关联的模型
        models = db.query(Model).join(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.category_id == category_id
        ).all()
        
        return models
    
    @staticmethod
    def get_categories_by_model(db: Session, model_id: int) -> List[ModelCategory]:
        """获取指定模型的所有分类"""
        # 检查模型是否存在
        model = db.query(Model).filter(Model.id == model_id).first()
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


# 创建服务实例
model_category_service = ModelCategoryService()