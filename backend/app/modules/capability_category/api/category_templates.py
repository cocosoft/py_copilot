"""分类模板相关的API路由"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.category_template import (
    CategoryTemplateCreate,
    CategoryTemplateUpdate,
    CategoryTemplateResponse,
    ApplyTemplateResponse
)
from app.modules.capability_category.services.category_template_service import CategoryTemplateService

# 创建路由器
router = APIRouter(prefix="/category_templates", tags=["category_templates"])

# 导入实际的认证依赖
from app.api.deps import get_current_user
from app.models.user import User


# 分类模板概念说明
"""
## 分类模板功能

### 概念定义
- **分类模板**：预定义的分类结构和参数配置，用于快速创建标准化的分类
- **模板数据**：包含分类的基本信息、层级结构、默认参数等

### 使用场景
1. 快速创建标准化的分类体系
2. 确保不同项目间分类结构的一致性
3. 简化复杂分类的创建流程

### 模板数据结构
```json
{
  "categories": [
    {
      "name": "main_category",
      "display_name": "主分类",
      "description": "示例主分类",
      "dimension": "task_type",
      "parent_id": null,
      "weight": 100,
      "default_parameters": {
        "param1": {"value": "default_value", "type": "string", "description": "参数描述"}
      },
      "children": [
        {
          "name": "sub_category",
          "display_name": "子分类",
          "description": "示例子分类",
          "dimension": "task_type",
          "weight": 50,
          "default_parameters": {}
        }
      ]
    }
  ]
}
```
"""


@router.post("/", response_model=CategoryTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_category_template(
    template_data: CategoryTemplateCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的分类模板"""
    return CategoryTemplateService.create_template(db, template_data)


@router.get("/{template_id}", response_model=CategoryTemplateResponse)
def get_category_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个分类模板"""
    template = CategoryTemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"分类模板 ID {template_id} 不存在"
        )
    return template


@router.get("/", response_model=List[CategoryTemplateResponse])
def get_all_category_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有分类模板"""
    return CategoryTemplateService.get_all_templates(db, skip=skip, limit=limit)


@router.put("/{template_id}", response_model=CategoryTemplateResponse)
def update_category_template(
    template_id: int,
    template_data: CategoryTemplateUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新分类模板"""
    return CategoryTemplateService.update_template(db, template_id, template_data)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除分类模板"""
    CategoryTemplateService.delete_template(db, template_id)
    return None


@router.post("/{template_id}/apply", response_model=ApplyTemplateResponse)
def apply_category_template(
    template_id: int,
    category_data: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """应用分类模板"""
    template_content = CategoryTemplateService.apply_template(db, template_id, category_data)
    return ApplyTemplateResponse(
        success=True,
        message="模板应用成功",
        template_data=template_content,
        category_data=category_data
    )


@router.get("/export", response_model=List[Dict[str, Any]])
def export_category_templates(
    template_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出分类模板
    
    参数:
    - template_ids: 可选，要导出的模板ID列表
    
    返回:
    - 导出的模板数据列表
    """
    return CategoryTemplateService.export_templates(db, template_ids)


@router.post("/import", response_model=Dict[str, Any])
def import_category_templates(
    templates_data: List[Dict[str, Any]] = Body(...),
    overwrite: bool = Body(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导入分类模板
    
    参数:
    - templates_data: 要导入的模板数据列表
    - overwrite: 是否覆盖已存在的模板（系统模板不能被覆盖）
    
    返回:
    - 导入结果统计信息
    """
    return CategoryTemplateService.import_templates(db, templates_data, overwrite)