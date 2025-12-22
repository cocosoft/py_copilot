"""智能体分类服务层"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.agent_category import AgentCategory
from app.schemas.agent_category import AgentCategoryCreate, AgentCategoryUpdate


class AgentCategoryService:
    """智能体分类服务类"""
    
    @staticmethod
    def create_category(db: Session, category_data: AgentCategoryCreate) -> AgentCategory:
        """创建智能体分类"""
        # 检查父分类是否存在
        if category_data.parent_id:
            parent_category = db.query(AgentCategory).filter(
                AgentCategory.id == category_data.parent_id
            ).first()
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"父分类 ID {category_data.parent_id} 不存在"
                )
        
        # 检查同级分类中名称是否已存在
        existing_category = db.query(AgentCategory).filter(
            AgentCategory.name == category_data.name,
            AgentCategory.parent_id == category_data.parent_id
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"智能体分类 '{category_data.name}' 已存在"
            )
        
        # 创建新分类
        db_category = AgentCategory(**category_data.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
        return db_category
    
    @staticmethod
    def get_category(db: Session, category_id: int) -> Optional[AgentCategory]:
        """获取单个智能体分类"""
        category = db.query(AgentCategory).filter(
            AgentCategory.id == category_id
        ).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"智能体分类 ID {category_id} 不存在"
            )
        
        return category
    
    @staticmethod
    def get_category_by_name(db: Session, name: str) -> Optional[AgentCategory]:
        """根据名称获取智能体分类"""
        return db.query(AgentCategory).filter(
            AgentCategory.name == name
        ).first()
    
    @staticmethod
    def get_categories(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_system: Optional[bool] = None
    ) -> Dict[str, Any]:
        """获取智能体分类列表"""
        query = db.query(AgentCategory)
        
        # 应用过滤条件
        if is_system is not None:
            query = query.filter(AgentCategory.is_system == is_system)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        categories = query.offset(skip).limit(limit).all()
        
        return {
            "categories": categories,
            "total": total
        }
    
    @staticmethod
    def update_category(
        db: Session,
        category_id: int,
        category_update: AgentCategoryUpdate
    ) -> AgentCategory:
        """更新智能体分类"""
        db_category = AgentCategoryService.get_category(db, category_id)
        
        # 检查是否为系统分类
        if db_category.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统分类不允许修改"
            )
        
        # 更新非空字段
        update_data = category_update.model_dump(exclude_unset=True)
        
        # 如果更新名称，检查是否重复
        if "name" in update_data:
            existing_category = db.query(AgentCategory).filter(
                and_(
                    AgentCategory.name == update_data["name"],
                    AgentCategory.id != category_id
                )
            ).first()
            
            if existing_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"智能体分类名称 '{update_data['name']}' 已存在"
                )
        
        # 执行更新
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        
        return db_category
    
    @staticmethod
    def delete_category(db: Session, category_id: int) -> bool:
        """删除智能体分类"""
        db_category = AgentCategoryService.get_category(db, category_id)
        
        # 检查是否为系统分类
        if db_category.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统分类不允许删除"
            )
        
        # 硬删除
        db.delete(db_category)
        db.commit()
        
        return True

    # 树形结构相关方法
    
    @staticmethod
    def get_root_categories(db: Session) -> List[AgentCategory]:
        """获取所有根分类（没有父分类的分类）"""
        return db.query(AgentCategory).filter(
            AgentCategory.parent_id.is_(None)
        ).options(joinedload(AgentCategory.children)).all()
    
    @staticmethod
    def get_category_tree(db: Session) -> List[Dict[str, Any]]:
        """获取完整的分类树结构"""
        root_categories = db.query(AgentCategory).filter(
            AgentCategory.parent_id.is_(None)
        ).options(joinedload(AgentCategory.children)).all()
        
        def build_tree(category):
            """递归构建树结构"""
            return {
                "id": category.id,
                "name": category.name,
                "logo": category.logo,
                "is_system": category.is_system,
                "is_root": category.is_root,
                "is_leaf": category.is_leaf,
                "children": [build_tree(child) for child in category.children]
            }
        
        return [build_tree(category) for category in root_categories]
    
    @staticmethod
    def get_category_children(db: Session, category_id: int) -> List[AgentCategory]:
        """获取指定分类的所有子分类"""
        return db.query(AgentCategory).filter(
            AgentCategory.parent_id == category_id
        ).all()
    
    @staticmethod
    def get_category_path(db: Session, category_id: int) -> List[AgentCategory]:
        """获取分类的完整路径（从根分类到当前分类）"""
        path = []
        current_category = AgentCategoryService.get_category(db, category_id)
        
        while current_category:
            path.insert(0, current_category)
            if current_category.parent_id:
                current_category = AgentCategoryService.get_category(db, current_category.parent_id)
            else:
                current_category = None
        
        return path
    
    @staticmethod
    def get_categories_by_level(db: Session, level: int = 0) -> List[AgentCategory]:
        """获取指定层级的分类"""
        if level == 0:
            return AgentCategoryService.get_root_categories(db)
        
        # 对于层级大于0的情况，需要递归查询
        categories = []
        
        def find_categories_at_level(current_level, parent_id=None):
            """递归查找指定层级的分类"""
            if current_level == level:
                # 到达目标层级，获取该层级的所有分类
                return db.query(AgentCategory).filter(
                    AgentCategory.parent_id == parent_id
                ).all()
            
            # 获取下一层级的分类
            next_level_categories = db.query(AgentCategory).filter(
                AgentCategory.parent_id == parent_id
            ).all()
            
            result = []
            for category in next_level_categories:
                result.extend(find_categories_at_level(current_level + 1, category.id))
            
            return result
        
        return find_categories_at_level(0)


# 创建服务实例
agent_category_service = AgentCategoryService()