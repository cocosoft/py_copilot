from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.setting import UserSetting
from app.schemas.setting import SettingCreate, SettingUpdate


class SettingService:
    """设置服务类"""
    
    @staticmethod
    def get_user_settings(db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户所有设置"""
        settings = db.query(UserSetting).filter(UserSetting.user_id == user_id).all()
        
        # 构建设置字典
        settings_dict = {
            "general": {
                "language": "zh-CN",
                "theme": "light"
            },
            "personalization": {
                "assistantName": "智能助手",
                "personalityTraits": {
                    "friendly": 0.8,
                    "professional": 0.7,
                    "humorous": 0.5,
                    "empathetic": 0.7,
                    "creative": 0.6
                },
                "communicationStyle": "balanced",
                "responseSpeed": "medium"
            },
            "emotion": {
                "emotionRecognition": True,
                "emotionResponse": True,
                "emotionMemory": True
            },
            "learning": {
                "adaptiveLearning": True,
                "patternRecognition": True,
                "predictiveSuggestions": True
            },
            "relationship": {
                "relationshipMemory": True,
                "milestoneReminders": True,
                "relationshipInsights": True
            }
        }
        
        # 更新为用户自定义设置
        for setting in settings:
            settings_dict[setting.setting_type] = setting.setting_data
        
        return settings_dict
    
    @staticmethod
    def get_user_setting(db: Session, user_id: int, setting_type: str) -> Optional[UserSetting]:
        """获取用户特定类型的设置"""
        return db.query(UserSetting).filter(
            UserSetting.user_id == user_id,
            UserSetting.setting_type == setting_type
        ).first()
    
    @staticmethod
    def create_or_update_setting(db: Session, user_id: int, setting_type: str, setting_data: Dict[str, Any]) -> UserSetting:
        """创建或更新设置"""
        # 查找现有设置
        existing_setting = SettingService.get_user_setting(db, user_id, setting_type)
        
        if existing_setting:
            # 更新现有设置
            existing_setting.setting_data = setting_data
            db.commit()
            db.refresh(existing_setting)
            return existing_setting
        else:
            # 创建新设置
            new_setting = UserSetting(
                user_id=user_id,
                setting_type=setting_type,
                setting_data=setting_data
            )
            db.add(new_setting)
            db.commit()
            db.refresh(new_setting)
            return new_setting
    
    @staticmethod
    def delete_setting(db: Session, user_id: int, setting_type: str) -> bool:
        """删除设置"""
        setting = SettingService.get_user_setting(db, user_id, setting_type)
        if setting:
            db.delete(setting)
            db.commit()
            return True
        return False