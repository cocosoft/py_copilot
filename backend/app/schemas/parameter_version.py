"""参数版本相关的数据校验模型"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ParameterVersionBase(BaseModel):
    """参数版本基础模型"""
    version_name: str = Field(..., min_length=1, max_length=100, description="版本名称")
    version_description: Optional[str] = Field(None, description="版本描述")


class ParameterVersionCreate(ParameterVersionBase):
    """创建参数版本请求模型"""
    pass


class ParameterVersionResponse(ParameterVersionBase):
    """参数版本响应模型"""
    id: int
    model_id: int
    parameters_snapshot: List[Dict[str, Any]] = Field(..., description="参数快照")
    created_by: Optional[str] = Field(None, description="创建人")
    created_at: datetime
    is_active: bool = Field(..., description="是否活跃")


class ParameterChangeLog(BaseModel):
    """参数变更日志"""
    version_id: int = Field(..., description="版本ID")
    version_name: str = Field(..., description="版本名称")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[str] = Field(None, description="创建人")
    changes_summary: Dict[str, int] = Field(..., description="变更摘要")
    changes_details: Dict[str, List[Dict[str, Any]]] = Field(..., description="变更详情")


class VersionComparisonResult(BaseModel):
    """版本比较结果"""
    version1: Dict[str, Any] = Field(..., description="版本1信息")
    version2: Dict[str, Any] = Field(..., description="版本2信息")
    differences: Dict[str, List[Dict[str, Any]]] = Field(..., description="差异列表")
    summary: Dict[str, int] = Field(..., description="差异摘要")


class VersionRestoreResult(BaseModel):
    """版本恢复结果"""
    version_id: int = Field(..., description="版本ID")
    version_name: str = Field(..., description="版本名称")
    model_id: int = Field(..., description="模型ID")
    restored_parameters_count: int = Field(..., description="恢复的参数数量")
    restore_version_id: int = Field(..., description="恢复操作创建的版本ID")


class VersionExportData(BaseModel):
    """版本导出数据"""
    version_id: int = Field(..., description="版本ID")
    version_name: str = Field(..., description="版本名称")
    version_description: Optional[str] = Field(None, description="版本描述")
    model_id: int = Field(..., description="模型ID")
    model_name: str = Field(..., description="模型名称")
    created_by: Optional[str] = Field(None, description="创建人")
    created_at: str = Field(..., description="创建时间")
    parameters: List[Dict[str, Any]] = Field(..., description="参数列表")
    exported_at: str = Field(..., description="导出时间")


class VersionImportRequest(BaseModel):
    """版本导入请求"""
    version_name: str = Field(..., description="版本名称")
    version_description: Optional[str] = Field(None, description="版本描述")
    model_id: int = Field(..., description="模型ID")
    parameters: List[Dict[str, Any]] = Field(..., description="参数列表")
    created_by: Optional[str] = Field(None, description="创建人")


class VersionListResponse(BaseModel):
    """版本列表响应"""
    versions: List[ParameterVersionResponse]
    total: int
    model_id: int
    model_name: str