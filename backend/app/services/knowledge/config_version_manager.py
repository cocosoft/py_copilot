#!/usr/bin/env python3
"""
配置版本管理器

提供配置的版本控制功能，包括：
1. 版本创建和保存
2. 版本回滚
3. 版本比较
4. 版本历史管理
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class ConfigVersion:
    """配置版本信息"""
    version_id: str
    name: str
    description: str
    created_at: str
    created_by: str
    knowledge_base_id: Optional[int]
    config_hash: str
    config_path: str
    is_active: bool = False


class ConfigVersionManager:
    """
    配置版本管理器

    管理知识图谱配置的版本历史，支持版本回滚和比较。
    """

    def __init__(self, knowledge_base_id: Optional[int] = None):
        self.knowledge_base_id = knowledge_base_id
        self.versions_dir = Path("config/versions")
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        # 版本历史文件
        if knowledge_base_id:
            self.history_file = self.versions_dir / f"kb_{knowledge_base_id}_history.json"
        else:
            self.history_file = self.versions_dir / "global_history.json"

        # 加载版本历史
        self._version_history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """加载版本历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载版本历史失败: {e}")
                return []
        return []

    def _save_history(self):
        """保存版本历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._version_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存版本历史失败: {e}")

    def _compute_config_hash(self, config: Dict[str, Any]) -> str:
        """计算配置的哈希值"""
        config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(config_str.encode()).hexdigest()[:16]

    def create_version(
        self,
        config: Dict[str, Any],
        name: str,
        description: str = "",
        created_by: str = "system"
    ) -> ConfigVersion:
        """
        创建新版本

        Args:
            config: 配置数据
            name: 版本名称
            description: 版本描述
            created_by: 创建者

        Returns:
            版本信息
        """
        # 生成版本ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_id = f"v_{timestamp}_{self._compute_config_hash(config)[:8]}"

        # 计算配置哈希
        config_hash = self._compute_config_hash(config)

        # 保存配置文件
        config_filename = f"{version_id}.json"
        config_path = self.versions_dir / config_filename

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise

        # 创建版本信息
        version = ConfigVersion(
            version_id=version_id,
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            knowledge_base_id=self.knowledge_base_id,
            config_hash=config_hash,
            config_path=str(config_path),
            is_active=True
        )

        # 更新版本历史
        # 将之前的版本标记为非活动
        for v in self._version_history:
            v['is_active'] = False

        # 添加新版本
        self._version_history.append(asdict(version))
        self._save_history()

        logger.info(f"创建配置版本: {version_id}")
        return version

    def get_versions(self, limit: int = 50) -> List[ConfigVersion]:
        """
        获取版本列表

        Args:
            limit: 返回的最大版本数

        Returns:
            版本信息列表
        """
        versions = []
        for v_data in self._version_history[-limit:]:
            versions.append(ConfigVersion(**v_data))

        # 按时间倒序
        versions.reverse()
        return versions

    def get_version(self, version_id: str) -> Optional[ConfigVersion]:
        """
        获取指定版本信息

        Args:
            version_id: 版本ID

        Returns:
            版本信息，如果不存在则返回None
        """
        for v_data in self._version_history:
            if v_data['version_id'] == version_id:
                return ConfigVersion(**v_data)
        return None

    def load_version_config(self, version_id: str) -> Optional[Dict[str, Any]]:
        """
        加载指定版本的配置

        Args:
            version_id: 版本ID

        Returns:
            配置数据，如果不存在则返回None
        """
        version = self.get_version(version_id)
        if not version:
            return None

        try:
            with open(version.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载版本配置失败: {e}")
            return None

    def rollback_to_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """
        回滚到指定版本

        Args:
            version_id: 版本ID

        Returns:
            回滚的配置数据
        """
        config = self.load_version_config(version_id)
        if not config:
            return None

        # 更新版本历史中的活动状态
        for v in self._version_history:
            v['is_active'] = (v['version_id'] == version_id)

        self._save_history()

        logger.info(f"回滚到版本: {version_id}")
        return config

    def compare_versions(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """
        比较两个版本

        Args:
            version_id1: 第一个版本ID
            version_id2: 第二个版本ID

        Returns:
            比较结果
        """
        config1 = self.load_version_config(version_id1)
        config2 = self.load_version_config(version_id2)

        if not config1 or not config2:
            return {
                'success': False,
                'error': '无法加载版本配置'
            }

        # 比较配置
        differences = self._compare_dicts(config1, config2)

        version1 = self.get_version(version_id1)
        version2 = self.get_version(version_id2)

        return {
            'success': True,
            'version1': {
                'id': version_id1,
                'name': version1.name if version1 else 'Unknown',
                'created_at': version1.created_at if version1 else ''
            },
            'version2': {
                'id': version_id2,
                'name': version2.name if version2 else 'Unknown',
                'created_at': version2.created_at if version2 else ''
            },
            'differences': differences,
            'summary': {
                'added': len(differences.get('added', [])),
                'removed': len(differences.get('removed', [])),
                'modified': len(differences.get('modified', []))
            }
        }

    def _compare_dicts(self, dict1: Dict, dict2: Dict, path: str = "") -> Dict[str, List]:
        """递归比较两个字典"""
        differences = {
            'added': [],
            'removed': [],
            'modified': []
        }

        all_keys = set(dict1.keys()) | set(dict2.keys())

        for key in all_keys:
            current_path = f"{path}.{key}" if path else key

            if key not in dict1:
                differences['added'].append({
                    'path': current_path,
                    'value': dict2[key]
                })
            elif key not in dict2:
                differences['removed'].append({
                    'path': current_path,
                    'value': dict1[key]
                })
            elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                # 递归比较嵌套字典
                nested_diff = self._compare_dicts(dict1[key], dict2[key], current_path)
                differences['added'].extend(nested_diff['added'])
                differences['removed'].extend(nested_diff['removed'])
                differences['modified'].extend(nested_diff['modified'])
            elif dict1[key] != dict2[key]:
                differences['modified'].append({
                    'path': current_path,
                    'old_value': dict1[key],
                    'new_value': dict2[key]
                })

        return differences

    def delete_version(self, version_id: str) -> bool:
        """
        删除版本

        Args:
            version_id: 版本ID

        Returns:
            是否删除成功
        """
        version = self.get_version(version_id)
        if not version:
            return False

        # 不能删除活动版本
        if version.is_active:
            logger.warning(f"不能删除活动版本: {version_id}")
            return False

        try:
            # 删除配置文件
            config_path = Path(version.config_path)
            if config_path.exists():
                config_path.unlink()

            # 从历史中移除
            self._version_history = [
                v for v in self._version_history
                if v['version_id'] != version_id
            ]
            self._save_history()

            logger.info(f"删除版本: {version_id}")
            return True

        except Exception as e:
            logger.error(f"删除版本失败: {e}")
            return False

    def get_version_stats(self) -> Dict[str, Any]:
        """获取版本统计信息"""
        total_versions = len(self._version_history)
        active_versions = sum(1 for v in self._version_history if v.get('is_active', False))

        # 计算存储大小
        total_size = 0
        for v in self._version_history:
            config_path = Path(v['config_path'])
            if config_path.exists():
                total_size += config_path.stat().st_size

        return {
            'total_versions': total_versions,
            'active_versions': active_versions,
            'storage_size_bytes': total_size,
            'storage_size_mb': round(total_size / (1024 * 1024), 2),
            'knowledge_base_id': self.knowledge_base_id
        }

    def cleanup_old_versions(self, keep_count: int = 20) -> int:
        """
        清理旧版本

        Args:
            keep_count: 保留的版本数

        Returns:
            删除的版本数
        """
        if len(self._version_history) <= keep_count:
            return 0

        # 保留最新的keep_count个版本
        versions_to_keep = self._version_history[-keep_count:]
        versions_to_delete = self._version_history[:-keep_count]

        deleted_count = 0
        for v in versions_to_delete:
            if not v.get('is_active', False):  # 不删除活动版本
                if self.delete_version(v['version_id']):
                    deleted_count += 1

        logger.info(f"清理旧版本: 删除 {deleted_count} 个，保留 {len(versions_to_keep)} 个")
        return deleted_count


# ============== 版本管理API ==============

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

version_router = APIRouter(prefix="/kg-config/versions", tags=["config-versions"])


class VersionCreateRequest(BaseModel):
    name: str
    description: str = ""


class VersionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


@version_router.get("", response_model=VersionResponse)
async def list_versions(
    knowledge_base_id: Optional[int] = None,
    limit: int = 50
):
    """获取版本列表"""
    try:
        manager = ConfigVersionManager(knowledge_base_id)
        versions = manager.get_versions(limit)

        return VersionResponse(
            success=True,
            message="获取版本列表成功",
            data={
                'total': len(versions),
                'versions': [asdict(v) for v in versions]
            }
        )
    except Exception as e:
        logger.error(f"获取版本列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@version_router.post("", response_model=VersionResponse)
async def create_version(
    request: VersionCreateRequest,
    knowledge_base_id: Optional[int] = None
):
    """创建新版本"""
    try:
        from app.services.knowledge.entity_config_manager import EntityConfigManager

        # 获取当前配置
        config_manager = EntityConfigManager(knowledge_base_id)
        current_config = config_manager.config

        # 创建版本
        version_manager = ConfigVersionManager(knowledge_base_id)
        version = version_manager.create_version(
            config=current_config,
            name=request.name,
            description=request.description
        )

        return VersionResponse(
            success=True,
            message=f"成功创建版本: {version.version_id}",
            data=asdict(version)
        )
    except Exception as e:
        logger.error(f"创建版本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@version_router.post("/{version_id}/rollback", response_model=VersionResponse)
async def rollback_version(
    version_id: str,
    knowledge_base_id: Optional[int] = None
):
    """回滚到指定版本"""
    try:
        from app.services.knowledge.entity_config_manager import EntityConfigManager

        # 回滚配置
        version_manager = ConfigVersionManager(knowledge_base_id)
        config = version_manager.rollback_to_version(version_id)

        if not config:
            raise HTTPException(status_code=404, detail=f"版本不存在: {version_id}")

        # 应用配置
        config_manager = EntityConfigManager(knowledge_base_id)
        config_manager.config = config
        config_manager._save_config()

        return VersionResponse(
            success=True,
            message=f"成功回滚到版本: {version_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回滚版本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@version_router.get("/{version_id}/compare", response_model=VersionResponse)
async def compare_versions(
    version_id: str,
    target_version_id: str,
    knowledge_base_id: Optional[int] = None
):
    """比较两个版本"""
    try:
        manager = ConfigVersionManager(knowledge_base_id)
        result = manager.compare_versions(version_id, target_version_id)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        return VersionResponse(
            success=True,
            message="版本比较成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"比较版本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@version_router.delete("/{version_id}", response_model=VersionResponse)
async def delete_version(
    version_id: str,
    knowledge_base_id: Optional[int] = None
):
    """删除版本"""
    try:
        manager = ConfigVersionManager(knowledge_base_id)
        success = manager.delete_version(version_id)

        if success:
            return VersionResponse(
                success=True,
                message=f"成功删除版本: {version_id}"
            )
        else:
            raise HTTPException(status_code=400, detail="删除版本失败，可能是活动版本")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除版本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@version_router.get("/stats", response_model=VersionResponse)
async def get_version_stats(
    knowledge_base_id: Optional[int] = None
):
    """获取版本统计信息"""
    try:
        manager = ConfigVersionManager(knowledge_base_id)
        stats = manager.get_version_stats()

        return VersionResponse(
            success=True,
            message="获取版本统计成功",
            data=stats
        )
    except Exception as e:
        logger.error(f"获取版本统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
