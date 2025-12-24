"""分类相关Pydantic模型"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class ModelCategoryBase(BaseModel):
    """模型分类基础模型"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None

    parent_id: Optional[int] = None
    is_active: bool = True

class ModelCategoryCreate(ModelCategoryBase):
    """创建模型分类请求模型"""
    pass

class ModelCategoryResponse(ModelCategoryBase):
    """模型分类响应模型"""
    id: int
    children: List['ModelCategoryResponse'] = []
    
    model_config = ConfigDict(from_attributes=True)

# 解决循环引用
ModelCategoryResponse.update_forward_refs()