"""分类模板服务层，包含CRUD逻辑"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.category_template import CategoryTemplate
from app.schemas.category_template import CategoryTemplateCreate, CategoryTemplateUpdate


class CategoryTemplateService:
    """分类模板服务类"""
    
    @staticmethod
    def create_template(db: Session, template_data: CategoryTemplateCreate) -> CategoryTemplate:
        """创建分类模板"""
        # 检查名称是否已存在
        existing_template = db.query(CategoryTemplate).filter(
            CategoryTemplate.name == template_data.name
        ).first()
        
        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"分类模板 '{template_data.name}' 已存在"
            )
        
        # 创建新模板
        db_template = CategoryTemplate(**template_data.model_dump())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        return db_template
    
    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[CategoryTemplate]:
        """获取单个分类模板"""
        return db.query(CategoryTemplate).filter(
            CategoryTemplate.id == template_id
        ).first()
    
    @staticmethod
    def get_template_by_name(db: Session, template_name: str) -> Optional[CategoryTemplate]:
        """通过名称获取分类模板"""
        return db.query(CategoryTemplate).filter(
            CategoryTemplate.name == template_name
        ).first()
    
    @staticmethod
    def get_all_templates(db: Session, skip: int = 0, limit: int = 100) -> List[CategoryTemplate]:
        """获取所有分类模板"""
        return db.query(CategoryTemplate).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_template(db: Session, template_id: int, template_data: CategoryTemplateUpdate) -> CategoryTemplate:
        """更新分类模板"""
        db_template = CategoryTemplateService.get_template(db, template_id)
        
        if not db_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分类模板 ID {template_id} 不存在"
            )
        
        # 检查名称是否已存在（如果更新了名称）
        if template_data.name and template_data.name != db_template.name:
            existing_template = CategoryTemplateService.get_template_by_name(db, template_data.name)
            if existing_template:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"分类模板 '{template_data.name}' 已存在"
                )
        
        # 更新模板数据
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)
        
        db.commit()
        db.refresh(db_template)
        
        return db_template
    
    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        """删除分类模板"""
        db_template = CategoryTemplateService.get_template(db, template_id)
        
        if not db_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分类模板 ID {template_id} 不存在"
            )
        
        # 不允许删除系统模板
        if db_template.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统模板不允许删除"
            )
        
        db.delete(db_template)
        db.commit()
        
        return True
    
    @staticmethod
    def apply_template(db: Session, template_id: int, category_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """应用分类模板"""
        db_template = CategoryTemplateService.get_template(db, template_id)
        
        if not db_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分类模板 ID {template_id} 不存在"
            )
        
        # 获取模板数据
        template_content = db_template.template_data
        
        # 如果提供了分类数据，合并到模板中
        if category_data:
            template_content = {**template_content, **category_data}
        
        return template_content
    
    @staticmethod
    def export_templates(db: Session, template_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """导出分类模板"""
        if template_ids:
            # 导出指定ID的模板
            templates = db.query(CategoryTemplate).filter(
                CategoryTemplate.id.in_(template_ids)
            ).all()
        else:
            # 导出所有模板
            templates = db.query(CategoryTemplate).all()
        
        # 转换为导出格式
        exported_data = []
        for template in templates:
            exported_data.append({
                "id": template.id,
                "name": template.name,
                "display_name": template.display_name,
                "description": template.description,
                "template_data": template.template_data,
                "is_active": template.is_active,
                "is_system": template.is_system,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None
            })
        
        return exported_data
    
    @staticmethod
    def import_templates(db: Session, templates_data: List[Dict[str, Any]], overwrite: bool = False) -> Dict[str, Any]:
        """导入分类模板"""
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []
        
        for template_data in templates_data:
            try:
                # 检查模板是否已存在
                existing_template = CategoryTemplateService.get_template_by_name(db, template_data["name"])
                
                if existing_template:
                    if overwrite and not existing_template.is_system:
                        # 更新现有模板
                        update_data = {
                            "display_name": template_data.get("display_name", existing_template.display_name),
                            "description": template_data.get("description", existing_template.description),
                            "template_data": template_data.get("template_data", existing_template.template_data),
                            "is_active": template_data.get("is_active", existing_template.is_active)
                        }
                        # 转换为模板更新对象
                        update_obj = CategoryTemplateUpdate(**update_data)
                        CategoryTemplateService.update_template(db, existing_template.id, update_obj)
                        updated_count += 1
                    else:
                        # 跳过已存在的模板
                        skipped_count += 1
                        continue
                else:
                    # 创建新模板
                    create_data = {
                        "name": template_data["name"],
                        "display_name": template_data.get("display_name", template_data["name"]),
                        "description": template_data.get("description", ""),
                        "template_data": template_data.get("template_data", {}),
                        "is_active": template_data.get("is_active", True),
                        "is_system": False  # 导入的模板默认为非系统模板
                    }
                    # 转换为模板创建对象
                    create_obj = CategoryTemplateCreate(**create_data)
                    CategoryTemplateService.create_template(db, create_obj)
                    imported_count += 1
            except Exception as e:
                errors.append({
                    "template_name": template_data.get("name", "未知"),
                    "error": str(e)
                })
        
        return {
            "imported_count": imported_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "errors": errors
        }