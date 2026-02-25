"""配置导出导入服务模块"""
import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.setting_service import SettingService
from app.core.logging_config import logger


# 配置文件存放目录（项目根目录）
CONFIG_FILE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONFIG_FILE_NAME = "app_config.json"


class ConfigExportService:
    """配置导出导入服务"""

    # 支持的配置类型
    SUPPORTED_CONFIG_TYPES = [
        'general',
        'personalization',
        'emotion',
        'learning',
        'relationship'
    ]

    def __init__(self, db: Session):
        """初始化服务"""
        self.db = db
        self.config_file_path = os.path.join(CONFIG_FILE_DIR, CONFIG_FILE_NAME)

    def get_config_file_path(self) -> str:
        """获取配置文件路径"""
        return self.config_file_path

    def get_all_settings_from_db(self, user_id: int = 1) -> Dict[str, Any]:
        """从数据库获取所有设置"""
        try:
            settings = SettingService.get_user_settings(self.db, user_id)
            return settings
        except Exception as e:
            logger.error(f"从数据库获取设置失败: {str(e)}")
            return {}

    def export_config(self, config_types: List[str] = None, user_id: int = 1) -> Dict[str, Any]:
        """导出配置到文件

        Args:
            config_types: 要导出的配置类型列表，None表示全部
            user_id: 用户ID

        Returns:
            导出结果字典
        """
        try:
            # 确定要导出的配置类型
            if config_types is None:
                config_types = self.SUPPORTED_CONFIG_TYPES

            # 过滤有效的配置类型
            valid_types = [t for t in config_types if t in self.SUPPORTED_CONFIG_TYPES]

            if not valid_types:
                return {
                    "success": False,
                    "message": "没有有效的配置类型"
                }

            # 备份现有配置文件
            backup_file = None
            if os.path.exists(self.config_file_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{self.config_file_path}.backup_{timestamp}"
                shutil.copy2(self.config_file_path, backup_file)
                logger.info(f"已备份配置文件到: {backup_file}")

            # 获取数据库中的配置
            all_settings = self.get_all_settings_from_db(user_id)

            # 构建导出数据
            exported_config = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "config": {}
            }

            for config_type in valid_types:
                if config_type in all_settings:
                    exported_config["config"][f"{config_type}_settings"] = all_settings[config_type]

            # 写入配置文件
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(exported_config, f, ensure_ascii=False, indent=2)

            logger.info(f"配置导出成功: {self.config_file_path}")

            return {
                "success": True,
                "message": "配置导出成功",
                "file_path": self.config_file_path,
                "backup_file": backup_file,
                "exported_types": valid_types,
                "exported_count": len(valid_types)
            }

        except Exception as e:
            logger.error(f"配置导出失败: {str(e)}")
            return {
                "success": False,
                "message": f"配置导出失败: {str(e)}"
            }

    def import_config(self, file_path: str = None, mode: str = 'merge',
                      config_types: List[str] = None, user_id: int = 1) -> Dict[str, Any]:
        """从文件导入配置

        Args:
            file_path: 配置文件路径，None表示使用默认路径
            mode: 导入模式，merge增量合并，replace全量替换
            config_types: 要导入的配置类型列表，None表示全部
            user_id: 用户ID

        Returns:
            导入结果字典
        """
        try:
            # 确定配置文件路径
            config_file = file_path if file_path else self.config_file_path

            if not os.path.exists(config_file):
                return {
                    "success": False,
                    "message": f"配置文件不存在: {config_file}"
                }

            # 读取配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)

            # 验证配置文件格式
            if "config" not in file_config:
                return {
                    "success": False,
                    "message": "配置文件格式错误，缺少config字段"
                }

            # 确定要导入的配置类型
            if config_types is None:
                config_types = list(file_config.get("config", {}).keys())

            # 过滤有效的配置类型
            valid_types = [t for t in config_types if t in file_config.get("config", {})]

            imported_types = []
            errors = []

            for config_type in valid_types:
                setting_type = config_type.replace("_settings", "")

                # 全量替换模式
                if mode == 'replace':
                    setting_data = file_config["config"][config_type]
                else:
                    # 增量合并模式
                    existing_settings = self.get_all_settings_from_db(user_id)
                    existing_data = existing_settings.get(setting_type, {})
                    new_data = file_config["config"].get(config_type, {})
                    setting_data = self._merge_settings(existing_data, new_data)

                # 保存到数据库
                try:
                    SettingService.create_or_update_setting(
                        self.db,
                        user_id,
                        setting_type,
                        setting_data
                    )
                    imported_types.append(config_type)
                except Exception as e:
                    errors.append(f"{config_type}: {str(e)}")

            logger.info(f"配置导入成功，导入类型: {imported_types}")

            return {
                "success": True,
                "message": "配置导入成功",
                "imported_types": imported_types,
                "imported_count": len(imported_types),
                "errors": errors
            }

        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON解析失败: {str(e)}")
            return {
                "success": False,
                "message": f"配置文件JSON解析失败: {str(e)}"
            }
        except Exception as e:
            logger.error(f"配置导入失败: {str(e)}")
            return {
                "success": False,
                "message": f"配置导入失败: {str(e)}"
            }

    def _merge_settings(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """合并设置配置

        Args:
            existing: 现有配置
            new: 新配置

        Returns:
            合并后的配置
        """
        result = existing.copy()

        for key, value in new.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value

        return result

    def get_status(self) -> Dict[str, Any]:
        """获取配置状态

        Returns:
            配置状态字典
        """
        file_exists = os.path.exists(self.config_file_path)
        file_size = 0
        last_modified = None

        if file_exists:
            file_size = os.path.getsize(self.config_file_path)
            last_modified = datetime.fromtimestamp(
                os.path.getmtime(self.config_file_path)
            ).isoformat()

        # 读取文件中的配置类型
        loaded_types = []
        if file_exists:
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    loaded_types = list(file_config.get("config", {}).keys())
            except Exception:
                pass

        return {
            "file_exists": file_exists,
            "file_path": self.config_file_path,
            "file_size": file_size,
            "last_modified": last_modified,
            "loaded_config_types": loaded_types,
            "merge_strategy": "db_first"
        }

    def load_config_on_startup(self, user_id: int = 1) -> Dict[str, Any]:
        """启动时加载配置

        Args:
            user_id: 用户ID

        Returns:
            加载结果字典
        """
        start_time = datetime.now()

        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file_path):
                logger.info(f"配置文件不存在，跳过加载: {self.config_file_path}")
                return {
                    "success": True,
                    "message": "配置文件不存在，跳过加载",
                    "loaded_from": "none",
                    "loaded_types": [],
                    "load_time_ms": 0
                }

            # 读取配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)

            # 获取数据库中的配置
            db_config = self.get_all_settings_from_db(user_id)

            # 合并配置（数据库优先级高于文件）
            merged_config = self._merge_configs(
                file_config.get("config", {}),
                db_config
            )

            # 记录加载的配置文件类型
            loaded_types = list(file_config.get("config", {}).keys())

            # 计算加载时间
            load_time = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(f"配置文件加载成功，加载类型: {loaded_types}, 耗时: {load_time}ms")

            return {
                "success": True,
                "message": "配置加载成功",
                "loaded_from": "file_and_db",
                "loaded_types": loaded_types,
                "load_time_ms": load_time
            }

        except Exception as e:
            logger.error(f"配置文件加载失败: {str(e)}")
            return {
                "success": False,
                "message": f"配置加载失败: {str(e)}",
                "loaded_from": "error",
                "loaded_types": [],
                "load_time_ms": 0
            }

    def _merge_configs(self, file_config: Dict[str, Any], db_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置文件和数据库配置

        优先级：数据库 > 配置文件 > 默认值

        Args:
            file_config: 配置文件中的配置
            db_config: 数据库中的配置

        Returns:
            合并后的配置
        """
        result = {}

        # 1. 加载配置文件
        for key, value in file_config.items():
            result[key] = value

        # 2. 合并数据库配置（覆盖文件配置）
        for key, value in db_config.items():
            if value is not None:
                setting_key = f"{key}_settings"
                if setting_key in result:
                    # 递归合并
                    result[setting_key] = self._merge_settings(result[setting_key], value)
                else:
                    result[setting_key] = value

        return result
