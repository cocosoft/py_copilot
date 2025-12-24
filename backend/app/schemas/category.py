"""分类相关Pydantic模型"""
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import Optional, List, Union

class ModelCategoryBase(BaseModel):
    """模型分类基础模型"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    category_type: str = "main"
    parent_id: Optional[Union[int, str]] = None
    is_active: bool = True
    dimension: str = "task_type"
    
    @model_validator(mode='before')
    def handle_empty_parent_id(cls, data):
        """在验证前处理parent_id，将空字符串转换为None"""
        if 'parent_id' in data and data['parent_id'] == '':
            data['parent_id'] = None
        return data
    
    @field_validator('parent_id')
    def validate_parent_id(cls, v):
        """验证parent_id，确保它是整数或None"""
        if v is not None:
            try:
                return int(v)
            except ValueError:
                return None
        return v

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