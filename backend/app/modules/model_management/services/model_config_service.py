"""
模型配置管理服务

提供模型配置的管理功能，包括：
- 配置中心集成（Apollo/Nacos）
- 应用配置、模型配置集中管理
- 配置热更新支持
- 多环境配置分离
- 配置变更审计日志
"""

import logging
import json
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON

from app.models.base import Base
from app.core.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConfigEnvironment(Enum):
    """配置环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigType(Enum):
    """配置类型枚举"""
    APPLICATION = "application"    # 应用配置
    MODEL = "model"                # 模型配置
    SYSTEM = "system"              # 系统配置
    FEATURE = "feature"            # 功能开关


@dataclass
class ConfigChange:
    """配置变更记录"""
    config_key: str
    old_value: Any
    new_value: Any
    changed_by: int
    changed_at: datetime
    reason: Optional[str] = None


class ModelConfig(Base):
    """模型配置数据库模型"""
    __tablename__ = "model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(200), nullable=False, index=True)
    config_value = Column(Text)
    config_type = Column(String(50), nullable=False)  # application, model, system, feature
    environment = Column(String(50), nullable=False, default="production")
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConfigVersionHistory(Base):
    """配置版本历史数据库模型"""
    __tablename__ = "config_version_history"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, nullable=False, index=True)
    config_key = Column(String(200), nullable=False)
    config_value = Column(Text)
    version = Column(Integer, nullable=False)
    changed_by = Column(Integer, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_reason = Column(Text)


class ConfigAuditLog(Base):
    """配置审计日志数据库模型"""
    __tablename__ = "config_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(200), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # create, update, delete
    old_value = Column(Text)
    new_value = Column(Text)
    performed_by = Column(Integer, nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50))
    user_agent = Column(String(500))


class ModelConfigService:
    """
    模型配置服务类
    
    提供完整的配置管理功能，包括：
    - 配置的CRUD操作
    - 配置版本管理
    - 配置变更审计
    - 配置热更新
    - 多环境支持
    """
    
    # 缓存键前缀
    CACHE_PREFIX = "model_config"
    
    # 配置变更回调
    _change_callbacks: Dict[str, List[Callable]] = {}
    
    def __init__(self, db: Session):
        """
        初始化配置服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.redis_client = get_redis()
        self._load_configs()
    
    # ==================== 配置CRUD操作 ====================
    
    def create_config(
        self,
        config_key: str,
        config_value: Any,
        config_type: ConfigType,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION,
        description: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> ModelConfig:
        """
        创建配置
        
        Args:
            config_key: 配置键
            config_value: 配置值
            config_type: 配置类型
            environment: 环境
            description: 描述
            created_by: 创建者ID
        
        Returns:
            配置对象
        """
        # 检查是否已存在
        existing = self.db.query(ModelConfig).filter(
            ModelConfig.config_key == config_key,
            ModelConfig.environment == environment.value
        ).first()
        
        if existing:
            raise ValueError(f"配置已存在: {config_key}")
        
        # 序列化配置值
        value_str = json.dumps(config_value, ensure_ascii=False)
        
        config = ModelConfig(
            config_key=config_key,
            config_value=value_str,
            config_type=config_type.value,
            environment=environment.value,
            description=description,
            created_by=created_by,
            version=1
        )
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        # 记录审计日志
        self._log_audit(
            config_key=config_key,
            action="create",
            new_value=value_str,
            performed_by=created_by
        )
        
        # 更新缓存
        self._update_cache(config_key, config_value, environment.value)
        
        logger.info(f"配置创建成功: {config_key}")
        
        return config
    
    def update_config(
        self,
        config_key: str,
        config_value: Any,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION,
        updated_by: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Optional[ModelConfig]:
        """
        更新配置
        
        Args:
            config_key: 配置键
            config_value: 新配置值
            environment: 环境
            updated_by: 更新者ID
            reason: 变更原因
        
        Returns:
            更新后的配置对象，不存在时返回None
        """
        config = self.db.query(ModelConfig).filter(
            ModelConfig.config_key == config_key,
            ModelConfig.environment == environment.value
        ).first()
        
        if not config:
            return None
        
        # 保存旧值
        old_value = config.config_value
        
        # 序列化新值
        new_value_str = json.dumps(config_value, ensure_ascii=False)
        
        # 更新配置
        config.config_value = new_value_str
        config.version += 1
        config.updated_by = updated_by
        config.updated_at = datetime.utcnow()
        
        # 保存版本历史
        history = ConfigVersionHistory(
            config_id=config.id,
            config_key=config_key,
            config_value=old_value,
            version=config.version - 1,
            changed_by=updated_by or config.created_by,
            change_reason=reason
        )
        self.db.add(history)
        
        self.db.commit()
        self.db.refresh(config)
        
        # 记录审计日志
        self._log_audit(
            config_key=config_key,
            action="update",
            old_value=old_value,
            new_value=new_value_str,
            performed_by=updated_by
        )
        
        # 更新缓存
        self._update_cache(config_key, config_value, environment.value)
        
        # 触发变更回调
        self._trigger_change_callbacks(
            config_key,
            json.loads(old_value) if old_value else None,
            config_value
        )
        
        logger.info(f"配置更新成功: {config_key}, Version={config.version}")
        
        return config
    
    def get_config(
        self,
        config_key: str,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION,
        default: Any = None
    ) -> Any:
        """
        获取配置值
        
        Args:
            config_key: 配置键
            environment: 环境
            default: 默认值
        
        Returns:
            配置值，不存在时返回默认值
        """
        # 尝试从缓存获取
        cached_value = self._get_from_cache(config_key, environment.value)
        if cached_value is not None:
            return cached_value
        
        # 从数据库获取
        config = self.db.query(ModelConfig).filter(
            ModelConfig.config_key == config_key,
            ModelConfig.environment == environment.value,
            ModelConfig.is_active == True
        ).first()
        
        if not config:
            return default
        
        # 解析配置值
        try:
            value = json.loads(config.config_value)
        except json.JSONDecodeError:
            value = config.config_value
        
        # 更新缓存
        self._update_cache(config_key, value, environment.value)
        
        return value
    
    def delete_config(
        self,
        config_key: str,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION,
        deleted_by: Optional[int] = None
    ) -> bool:
        """
        删除配置
        
        Args:
            config_key: 配置键
            environment: 环境
            deleted_by: 删除者ID
        
        Returns:
            是否删除成功
        """
        config = self.db.query(ModelConfig).filter(
            ModelConfig.config_key == config_key,
            ModelConfig.environment == environment.value
        ).first()
        
        if not config:
            return False
        
        old_value = config.config_value
        
        # 软删除
        config.is_active = False
        config.updated_at = datetime.utcnow()
        config.updated_by = deleted_by
        
        self.db.commit()
        
        # 记录审计日志
        self._log_audit(
            config_key=config_key,
            action="delete",
            old_value=old_value,
            performed_by=deleted_by
        )
        
        # 清除缓存
        self._clear_cache(config_key, environment.value)
        
        logger.info(f"配置删除成功: {config_key}")
        
        return True
    
    def get_configs_by_type(
        self,
        config_type: ConfigType,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION
    ) -> List[ModelConfig]:
        """
        获取指定类型的所有配置
        
        Args:
            config_type: 配置类型
            environment: 环境
        
        Returns:
            配置列表
        """
        return self.db.query(ModelConfig).filter(
            ModelConfig.config_type == config_type.value,
            ModelConfig.environment == environment.value,
            ModelConfig.is_active == True
        ).all()
    
    # ==================== 版本管理 ====================
    
    def get_config_history(
        self,
        config_key: str,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION,
        limit: int = 10
    ) -> List[ConfigVersionHistory]:
        """
        获取配置版本历史
        
        Args:
            config_key: 配置键
            environment: 环境
            limit: 返回的最大数量
        
        Returns:
            版本历史列表
        """
        return self.db.query(ConfigVersionHistory).filter(
            ConfigVersionHistory.config_key == config_key
        ).order_by(
            ConfigVersionHistory.changed_at.desc()
        ).limit(limit).all()
    
    def rollback_config(
        self,
        config_key: str,
        version: int,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION,
        performed_by: Optional[int] = None
    ) -> Optional[ModelConfig]:
        """
        回滚配置到指定版本
        
        Args:
            config_key: 配置键
            version: 目标版本号
            environment: 环境
            performed_by: 执行者ID
        
        Returns:
            回滚后的配置对象，不存在时返回None
        """
        # 获取指定版本的历史记录
        history = self.db.query(ConfigVersionHistory).filter(
            ConfigVersionHistory.config_key == config_key,
            ConfigVersionHistory.version == version
        ).first()
        
        if not history:
            return None
        
        # 解析历史值
        try:
            old_value = json.loads(history.config_value)
        except json.JSONDecodeError:
            old_value = history.config_value
        
        # 更新配置
        return self.update_config(
            config_key=config_key,
            config_value=old_value,
            environment=environment,
            updated_by=performed_by,
            reason=f"回滚到版本 {version}"
        )
    
    # ==================== 审计日志 ====================
    
    def get_audit_logs(
        self,
        config_key: Optional[str] = None,
        action: Optional[str] = None,
        performed_by: Optional[int] = None,
        limit: int = 100
    ) -> List[ConfigAuditLog]:
        """
        获取审计日志
        
        Args:
            config_key: 配置键过滤器（可选）
            action: 操作类型过滤器（可选）
            performed_by: 执行者ID过滤器（可选）
            limit: 返回的最大数量
        
        Returns:
            审计日志列表
        """
        query = self.db.query(ConfigAuditLog)
        
        if config_key:
            query = query.filter(ConfigAuditLog.config_key == config_key)
        
        if action:
            query = query.filter(ConfigAuditLog.action == action)
        
        if performed_by:
            query = query.filter(ConfigAuditLog.performed_by == performed_by)
        
        return query.order_by(
            ConfigAuditLog.performed_at.desc()
        ).limit(limit).all()
    
    def _log_audit(
        self,
        config_key: str,
        action: str,
        performed_by: Optional[int],
        old_value: Optional[str] = None,
        new_value: Optional[str] = None
    ) -> None:
        """
        记录审计日志
        
        Args:
            config_key: 配置键
            action: 操作类型
            performed_by: 执行者ID
            old_value: 旧值
            new_value: 新值
        """
        log = ConfigAuditLog(
            config_key=config_key,
            action=action,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by or 0
        )
        
        self.db.add(log)
        self.db.commit()
    
    # ==================== 配置热更新 ====================
    
    def register_change_callback(
        self,
        config_key: str,
        callback: Callable[[Any, Any], None]
    ) -> None:
        """
        注册配置变更回调
        
        Args:
            config_key: 配置键
            callback: 回调函数，接收(old_value, new_value)参数
        """
        if config_key not in self._change_callbacks:
            self._change_callbacks[config_key] = []
        
        self._change_callbacks[config_key].append(callback)
    
    def _trigger_change_callbacks(
        self,
        config_key: str,
        old_value: Any,
        new_value: Any
    ) -> None:
        """
        触发配置变更回调
        
        Args:
            config_key: 配置键
            old_value: 旧值
            new_value: 新值
        """
        callbacks = self._change_callbacks.get(config_key, [])
        
        for callback in callbacks:
            try:
                callback(old_value, new_value)
            except Exception as e:
                logger.error(f"配置变更回调执行失败: {str(e)}")
    
    # ==================== 缓存操作 ====================
    
    def _get_cache_key(self, config_key: str, environment: str) -> str:
        """获取缓存键"""
        return f"{self.CACHE_PREFIX}:{environment}:{config_key}"
    
    def _get_from_cache(
        self,
        config_key: str,
        environment: str
    ) -> Optional[Any]:
        """从缓存获取配置"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(config_key, environment)
            value_str = self.redis_client.get(cache_key)
            
            if value_str:
                return json.loads(value_str)
            
            return None
        except Exception as e:
            logger.warning(f"从缓存获取配置失败: {str(e)}")
            return None
    
    def _update_cache(
        self,
        config_key: str,
        value: Any,
        environment: str
    ) -> None:
        """更新缓存"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(config_key, environment)
            value_str = json.dumps(value, ensure_ascii=False)
            # 缓存1小时
            self.redis_client.setex(cache_key, 3600, value_str)
        except Exception as e:
            logger.warning(f"更新配置缓存失败: {str(e)}")
    
    def _clear_cache(self, config_key: str, environment: str) -> None:
        """清除缓存"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(config_key, environment)
            self.redis_client.delete(cache_key)
        except Exception as e:
            logger.warning(f"清除配置缓存失败: {str(e)}")
    
    def _load_configs(self) -> None:
        """加载配置到缓存"""
        configs = self.db.query(ModelConfig).filter(
            ModelConfig.is_active == True
        ).all()
        
        for config in configs:
            try:
                value = json.loads(config.config_value)
                self._update_cache(
                    config.config_key,
                    value,
                    config.environment
                )
            except Exception as e:
                logger.warning(f"加载配置到缓存失败: {config.config_key}, {str(e)}")
    
    # ==================== 环境配置 ====================
    
    def get_environment_configs(
        self,
        environment: ConfigEnvironment
    ) -> Dict[str, Any]:
        """
        获取指定环境的所有配置
        
        Args:
            environment: 环境
        
        Returns:
            配置字典
        """
        configs = self.db.query(ModelConfig).filter(
            ModelConfig.environment == environment.value,
            ModelConfig.is_active == True
        ).all()
        
        result = {}
        for config in configs:
            try:
                result[config.config_key] = json.loads(config.config_value)
            except json.JSONDecodeError:
                result[config.config_key] = config.config_value
        
        return result
    
    def clone_environment(
        self,
        source_env: ConfigEnvironment,
        target_env: ConfigEnvironment,
        cloned_by: Optional[int] = None
    ) -> int:
        """
        克隆环境配置
        
        Args:
            source_env: 源环境
            target_env: 目标环境
            cloned_by: 执行者ID
        
        Returns:
            克隆的配置数量
        """
        source_configs = self.db.query(ModelConfig).filter(
            ModelConfig.environment == source_env.value,
            ModelConfig.is_active == True
        ).all()
        
        count = 0
        for config in source_configs:
            # 检查目标环境是否已存在
            existing = self.db.query(ModelConfig).filter(
                ModelConfig.config_key == config.config_key,
                ModelConfig.environment == target_env.value
            ).first()
            
            if existing:
                continue
            
            # 创建新配置
            new_config = ModelConfig(
                config_key=config.config_key,
                config_value=config.config_value,
                config_type=config.config_type,
                environment=target_env.value,
                description=f"从 {source_env.value} 克隆: {config.description or ''}",
                created_by=cloned_by,
                version=1
            )
            
            self.db.add(new_config)
            count += 1
        
        self.db.commit()
        
        logger.info(f"环境配置克隆成功: {source_env.value} -> {target_env.value}, 数量={count}")
        
        return count


# ==================== 依赖注入函数 ====================

def get_model_config_service(db: Session) -> ModelConfigService:
    """
    获取模型配置服务实例（用于依赖注入）
    
    Args:
        db: 数据库会话
    
    Returns:
        模型配置服务实例
    """
    return ModelConfigService(db)
