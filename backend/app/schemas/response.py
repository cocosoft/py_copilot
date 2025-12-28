"""
统一API响应格式定义
"""

from typing import Optional, TypeVar, Generic
from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel):
    """基础响应模型"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="成功", description="响应消息")


class SuccessResponse(BaseResponse, Generic[T]):
    """成功响应模型"""
    data: Optional[T] = Field(default=None, description="响应数据")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    detail: Optional[str] = Field(default=None, description="错误详情")


class ListResponse(BaseResponse, Generic[T]):
    """列表响应模型"""
    data: list[T] = Field(default_factory=list, description="响应数据列表")
    total: int = Field(default=0, description="总记录数")
    page: Optional[int] = Field(default=None, description="当前页码")
    size: Optional[int] = Field(default=None, description="每页大小")


# 常用响应快捷方式
class SuccessData(SuccessResponse[T]):
    """包含数据的成功响应"""
    code: int = Field(default=200)
    message: str = Field(default="成功")
    data: T


class SuccessMessage(SuccessResponse):
    """仅包含消息的成功响应"""
    code: int = Field(default=200)
    message: str


class NotFoundError(ErrorResponse):
    """资源不存在错误响应"""
    code: int = Field(default=404)
    message: str = Field(default="资源不存在")


class BadRequestError(ErrorResponse):
    """请求参数错误响应"""
    code: int = Field(default=400)
    message: str = Field(default="请求参数错误")


class UnauthorizedError(ErrorResponse):
    """未授权错误响应"""
    code: int = Field(default=401)
    message: str = Field(default="未授权访问")


class ForbiddenError(ErrorResponse):
    """禁止访问错误响应"""
    code: int = Field(default=403)
    message: str = Field(default="禁止访问")


class ServerError(ErrorResponse):
    """服务器内部错误响应"""
    code: int = Field(default=500)
    message: str = Field(default="服务器内部错误")
