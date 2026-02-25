"""配置管理 API 模块"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.config_export_service import ConfigExportService


router = APIRouter(tags=["config-management"])


class ImportConfigRequest(BaseModel):
    """导入配置请求"""
    file_path: Optional[str] = None
    mode: str = 'merge'
    config_types: Optional[List[str]] = None


class LoadConfigRequest(BaseModel):
    """加载配置请求"""
    force_reload: bool = False


@router.get("/config/export")
async def export_config(
    types: Optional[str] = Query(None, description="逗号分隔的配置类型，如: general,personalization"),
    db: Session = Depends(get_db)
):
    """导出配置到文件

    Args:
        types: 逗号分隔的配置类型，不传则导出全部
        db: 数据库会话

    Returns:
        导出结果
    """
    # 解析配置类型
    config_types = None
    if types:
        config_types = [t.strip() for t in types.split(',')]

    service = ConfigExportService(db)
    result = service.export_config(config_types=config_types)

    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/config/import")
async def import_config(
    request: ImportConfigRequest,
    db: Session = Depends(get_db)
):
    """从文件导入配置

    Args:
        request: 导入请求
        db: 数据库会话

    Returns:
        导入结果
    """
    service = ConfigExportService(db)
    result = service.import_config(
        file_path=request.file_path,
        mode=request.mode,
        config_types=request.config_types
    )

    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.get("/config/status")
async def get_config_status(db: Session = Depends(get_db)):
    """获取配置状态

    Args:
        db: 数据库会话

    Returns:
        配置状态
    """
    service = ConfigExportService(db)
    return service.get_status()


@router.post("/config/load")
async def load_config(
    request: LoadConfigRequest,
    db: Session = Depends(get_db)
):
    """手动加载配置

    Args:
        request: 加载请求
        db: 数据库会话

    Returns:
        加载结果
    """
    service = ConfigExportService(db)
    result = service.load_config_on_startup()

    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result
