from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.setting_service import SettingService
from app.schemas.setting import SettingResponse, SettingsResponse

router = APIRouter(tags=["settings"])


@router.get("", response_model=Dict[str, Any])
def get_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取用户所有设置"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        settings = SettingService.get_user_settings(db, user_id)
        return {"success": True, "data": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设置失败: {str(e)}")


@router.get("/{setting_type}", response_model=Dict[str, Any])
def get_setting(
    setting_type: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取特定类型的设置"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        settings = SettingService.get_user_settings(db, user_id)
        if setting_type in settings:
            return {"success": True, "data": settings[setting_type]}
        raise HTTPException(status_code=404, detail="设置类型不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设置失败: {str(e)}")


@router.post("", response_model=Dict[str, Any])
def save_setting(
    setting_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """保存设置"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        setting_type = setting_data.get("type")
        data = setting_data.get("data")
        
        if not setting_type or not data:
            raise HTTPException(status_code=400, detail="设置类型和数据不能为空")
        
        # 验证设置类型
        valid_types = ["general", "personalization", "emotion", "learning", "relationship"]
        if setting_type not in valid_types:
            raise HTTPException(status_code=400, detail="无效的设置类型")
        
        # 保存设置
        SettingService.create_or_update_setting(db, user_id, setting_type, data)
        return {"success": True, "message": "设置保存成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存设置失败: {str(e)}")


@router.delete("/{setting_type}", response_model=Dict[str, Any])
def delete_setting(
    setting_type: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除设置"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        success = SettingService.delete_setting(db, user_id, setting_type)
        if success:
            return {"success": True, "message": "设置删除成功"}
        else:
            return {"success": False, "message": "设置不存在"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除设置失败: {str(e)}")
