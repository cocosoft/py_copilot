"""搜索管理服务（仅联网搜索配置）"""
from sqlalchemy.orm import Session
from typing import Optional
from app.models.search_settings import SearchSetting


class SearchManagementService:
    """搜索管理服务（仅联网搜索配置）"""
    
    def get_search_settings(self, db: Session, user_id: Optional[int] = None) -> Optional[SearchSetting]:
        """获取搜索设置
        
        Args:
            db: 数据库会话
            user_id: 用户ID（可选），如果提供则获取用户级设置，否则获取全局设置
            
        Returns:
            搜索设置对象
        """
        if user_id:
            # 优先获取用户级设置，如果没有则获取全局设置
            return db.query(SearchSetting).filter(
                (SearchSetting.user_id == user_id) | (SearchSetting.user_id.is_(None))
            ).order_by(SearchSetting.user_id.desc()).first()
        # 获取全局设置
        return db.query(SearchSetting).filter(SearchSetting.user_id.is_(None)).first()
    
    def update_search_settings(self, db: Session, settings_data: dict, user_id: Optional[int] = None) -> SearchSetting:
        """更新搜索设置
        
        Args:
            db: 数据库会话
            settings_data: 要更新的设置数据
            user_id: 用户ID（可选），如果提供则更新用户级设置，否则更新全局设置
            
        Returns:
            更新后的搜索设置对象
        """
        settings = self.get_search_settings(db, user_id)
        
        if not settings:
            # 如果设置不存在，则创建新的设置
            settings = SearchSetting(user_id=user_id, **settings_data)
            db.add(settings)
        else:
            # 更新现有设置
            for key, value in settings_data.items():
                setattr(settings, key, value)
        
        db.commit()
        db.refresh(settings)
        return settings
