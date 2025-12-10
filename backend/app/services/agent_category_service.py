"""智能体分类服务层"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.agent_category import AgentCategory
from app.schemas.agent_category import AgentCategoryCreate, AgentCategoryUpdate


class AgentCategoryService:
    """智能体分类服务类"""
    
    @staticmethod
    def create_category(db: Session, category_data: AgentCategoryCreate) -> AgentCategory:
        """创建智能体分类"""
        # 检查名称是否已存在
        existing_category = db.query(AgentCategory).filter(
            AgentCategory.name == category_data.name
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


# 创建服务实例
agent_category_service = AgentCategoryService()