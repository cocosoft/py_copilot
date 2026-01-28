"""
技能注册器

负责管理技能注册表，提供技能注册、查询、更新和删除功能。
支持技能冲突解决、状态管理和版本控制。
"""

import threading
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
from enum import Enum

from app.core.logging_config import logger
from app.schemas.skill_metadata import SkillMetadata


class ConflictResolution(Enum):
    """冲突解决策略"""
    SKIP = "skip"           # 跳过冲突技能
    OVERWRITE = "overwrite" # 覆盖现有技能
    RENAME = "rename"       # 重命名新技能
    MERGE = "merge"         # 合并技能元数据


class SkillStatus(Enum):
    """技能状态"""
    ENABLED = "enabled"     # 已启用
    DISABLED = "disabled"   # 已禁用
    PENDING = "pending"     # 待审核
    DEPRECATED = "deprecated" # 已废弃


class SkillRegistry:
    """技能注册器"""
    
    def __init__(self, conflict_resolution: ConflictResolution = ConflictResolution.SKIP):
        """
        初始化技能注册器
        
        Args:
            conflict_resolution: 冲突解决策略
        """
        self.registry: Dict[str, SkillMetadata] = {}
        self.conflict_resolution = conflict_resolution
        self._lock = threading.RLock()
        self._index: Dict[str, Set[str]] = {
            "name": set(),
            "category": set(),
            "tags": set(),
        }
    
    def register_skill(self, metadata: SkillMetadata) -> Tuple[bool, Optional[str]]:
        """
        注册技能到注册表
        
        Args:
            metadata: 技能元数据
            
        Returns:
            (是否成功, 错误消息或技能ID)
        """
        with self._lock:
            try:
                # 检查技能ID冲突
                existing_skill = self.registry.get(metadata.skill_id)
                
                if existing_skill:
                    return self._handle_conflict(existing_skill, metadata)
                
                # 检查名称冲突
                name_conflict = self._find_skill_by_name(metadata.name)
                if name_conflict and name_conflict.skill_id != metadata.skill_id:
                    return self._handle_name_conflict(name_conflict, metadata)
                
                # 注册技能
                self.registry[metadata.skill_id] = metadata
                
                # 更新索引
                self._update_index(metadata)
                
                logger.info(f"成功注册技能: {metadata.name} ({metadata.skill_id})")
                return True, metadata.skill_id
                
            except Exception as e:
                logger.error(f"注册技能失败 {metadata.name}: {e}")
                return False, str(e)
    
    def unregister_skill(self, skill_id: str) -> bool:
        """
        从注册表移除技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if skill_id not in self.registry:
                logger.warning(f"技能不存在: {skill_id}")
                return False
            
            skill = self.registry[skill_id]
            
            # 从注册表移除
            del self.registry[skill_id]
            
            # 更新索引
            self._remove_from_index(skill)
            
            logger.info(f"成功移除技能: {skill.name} ({skill_id})")
            return True
    
    def get_skill(self, skill_id: str) -> Optional[SkillMetadata]:
        """
        根据ID获取技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            技能元数据对象
        """
        with self._lock:
            return self.registry.get(skill_id)
    
    def get_skill_by_name(self, name: str) -> Optional[SkillMetadata]:
        """
        根据名称获取技能
        
        Args:
            name: 技能名称
            
        Returns:
            技能元数据对象
        """
        with self._lock:
            for skill in self.registry.values():
                if skill.name == name:
                    return skill
            return None
    
    def list_skills(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SkillMetadata], int]:
        """
        列出所有技能，支持过滤
        
        Args:
            filters: 过滤条件
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            (技能列表, 总数量)
        """
        with self._lock:
            skills = list(self.registry.values())
            
            # 应用过滤
            if filters:
                skills = self._apply_filters(skills, filters)
            
            total = len(skills)
            
            # 应用分页
            skills = skills[skip:skip + limit]
            
            return skills, total
    
    def search_skills(
        self, 
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SkillMetadata], int]:
        """
        搜索技能
        
        Args:
            query: 搜索查询
            fields: 搜索字段列表，如果为None则搜索所有字段
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            (技能列表, 总数量)
        """
        with self._lock:
            if fields is None:
                fields = ["name", "description", "tags"]
            
            query = query.lower()
            matched_skills = []
            
            for skill in self.registry.values():
                if self._matches_query(skill, query, fields):
                    matched_skills.append(skill)
            
            total = len(matched_skills)
            matched_skills = matched_skills[skip:skip + limit]
            
            return matched_skills, total
    
    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新技能信息
        
        Args:
            skill_id: 技能ID
            updates: 更新字段字典
            
        Returns:
            是否成功更新
        """
        with self._lock:
            if skill_id not in self.registry:
                logger.warning(f"技能不存在: {skill_id}")
                return False
            
            skill = self.registry[skill_id]
            
            # 移除旧索引
            self._remove_from_index(skill)
            
            # 应用更新
            for key, value in updates.items():
                if hasattr(skill, key):
                    setattr(skill, key, value)
            
            # 更新更新时间
            skill.updated_at = datetime.now()
            
            # 更新索引
            self._update_index(skill)
            
            logger.info(f"成功更新技能: {skill.name} ({skill_id})")
            return True
    
    def enable_skill(self, skill_id: str) -> bool:
        """启用技能"""
        return self.update_skill(skill_id, {"enabled": True})
    
    def disable_skill(self, skill_id: str) -> bool:
        """禁用技能"""
        return self.update_skill(skill_id, {"enabled": False})
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        with self._lock:
            total_skills = len(self.registry)
            enabled_skills = len([s for s in self.registry.values() if s.enabled])
            
            # 分类统计
            category_stats = {}
            for skill in self.registry.values():
                category = skill.category
                if category not in category_stats:
                    category_stats[category] = 0
                category_stats[category] += 1
            
            # 标签统计
            tag_stats = {}
            for skill in self.registry.values():
                for tag in skill.tags:
                    if tag not in tag_stats:
                        tag_stats[tag] = 0
                    tag_stats[tag] += 1
            
            return {
                "total_skills": total_skills,
                "enabled_skills": enabled_skills,
                "disabled_skills": total_skills - enabled_skills,
                "category_distribution": category_stats,
                "tag_distribution": dict(sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                "last_updated": datetime.now().isoformat()
            }
    
    def clear_registry(self) -> None:
        """清空注册表"""
        with self._lock:
            self.registry.clear()
            for key in self._index:
                self._index[key].clear()
            logger.info("注册表已清空")
    
    def _handle_conflict(self, existing: SkillMetadata, new: SkillMetadata) -> Tuple[bool, Optional[str]]:
        """处理技能ID冲突"""
        if self.conflict_resolution == ConflictResolution.SKIP:
            logger.warning(f"跳过冲突技能 (已存在): {new.name}")
            return False, f"技能已存在: {existing.name}"
        
        elif self.conflict_resolution == ConflictResolution.OVERWRITE:
            logger.info(f"覆盖现有技能: {existing.name} -> {new.name}")
            self.registry[new.skill_id] = new
            self._update_index(new)
            return True, new.skill_id
        
        elif self.conflict_resolution == ConflictResolution.RENAME:
            # 生成新的技能ID
            import hashlib
            import time
            new_id = hashlib.md5(f"{new.name}:{time.time()}".encode()).hexdigest()[:16]
            new.skill_id = new_id
            
            self.registry[new_id] = new
            self._update_index(new)
            
            logger.info(f"重命名并注册技能: {new.name} ({new_id})")
            return True, new_id
        
        elif self.conflict_resolution == ConflictResolution.MERGE:
            # 合并元数据
            merged = self._merge_metadata(existing, new)
            self.registry[new.skill_id] = merged
            self._update_index(merged)
            
            logger.info(f"合并技能元数据: {new.name}")
            return True, new.skill_id
        
        return False, "未知的冲突解决策略"
    
    def _handle_name_conflict(self, existing: SkillMetadata, new: SkillMetadata) -> Tuple[bool, Optional[str]]:
        """处理技能名称冲突"""
        if self.conflict_resolution == ConflictResolution.SKIP:
            logger.warning(f"跳过名称冲突技能: {new.name}")
            return False, f"技能名称已存在: {new.name}"
        
        elif self.conflict_resolution == ConflictResolution.RENAME:
            # 生成新的技能名称
            import hashlib
            import time
            new_name = f"{new.name}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
            new.name = new_name
            
            self.registry[new.skill_id] = new
            self._update_index(new)
            
            logger.info(f"重命名并注册技能: {new_name} ({new.skill_id})")
            return True, new.skill_id
        
        # 其他策略不适用于名称冲突
        return False, f"技能名称冲突: {new.name}"
    
    def _merge_metadata(self, existing: SkillMetadata, new: SkillMetadata) -> SkillMetadata:
        """合并技能元数据"""
        # 创建合并后的元数据
        merged = existing.copy()
        
        # 优先使用新版本的字段
        for field in ["description", "version", "author", "category"]:
            if getattr(new, field) != getattr(existing, field):
                setattr(merged, field, getattr(new, field))
        
        # 合并标签（去重）
        merged.tags = list(set(existing.tags + new.tags))
        
        # 合并依赖（去重）
        merged.dependencies = list(set(existing.dependencies + new.dependencies))
        
        # 使用新的配置模式（如果提供）
        if new.config_schema:
            merged.config_schema = new.config_schema
        
        # 更新更新时间
        merged.updated_at = datetime.now()
        
        return merged
    
    def _update_index(self, metadata: SkillMetadata) -> None:
        """更新索引"""
        # 名称索引
        self._index["name"].add(metadata.name.lower())
        
        # 分类索引
        self._index["category"].add(metadata.category)
        
        # 标签索引
        for tag in metadata.tags:
            self._index["tags"].add(tag.lower())
    
    def _remove_from_index(self, metadata: SkillMetadata) -> None:
        """从索引移除"""
        # 名称索引
        self._index["name"].discard(metadata.name.lower())
        
        # 分类索引
        self._index["category"].discard(metadata.category)
        
        # 标签索引
        for tag in metadata.tags:
            self._index["tags"].discard(tag.lower())
    
    def _apply_filters(self, skills: List[SkillMetadata], filters: Dict[str, Any]) -> List[SkillMetadata]:
        """应用过滤条件"""
        filtered_skills = skills
        
        for field, value in filters.items():
            if field == "enabled":
                filtered_skills = [s for s in filtered_skills if s.enabled == value]
            elif field == "category":
                filtered_skills = [s for s in filtered_skills if s.category == value]
            elif field == "tags":
                if isinstance(value, list):
                    filtered_skills = [s for s in filtered_skills if any(tag in s.tags for tag in value)]
                else:
                    filtered_skills = [s for s in filtered_skills if value in s.tags]
            elif field == "author":
                filtered_skills = [s for s in filtered_skills if s.author == value]
            elif field == "version":
                filtered_skills = [s for s in filtered_skills if s.version == value]
        
        return filtered_skills
    
    def _matches_query(self, skill: SkillMetadata, query: str, fields: List[str]) -> bool:
        """检查技能是否匹配查询"""
        for field in fields:
            if field == "name":
                if query in skill.name.lower():
                    return True
            elif field == "description":
                if query in skill.description.lower():
                    return True
            elif field == "tags":
                for tag in skill.tags:
                    if query in tag.lower():
                        return True
        
        return False
    
    def _find_skill_by_name(self, name: str) -> Optional[SkillMetadata]:
        """根据名称查找技能"""
        for skill in self.registry.values():
            if skill.name == name:
                return skill
        return None


def create_registry(conflict_resolution: ConflictResolution = ConflictResolution.SKIP) -> SkillRegistry:
    """
    创建技能注册器实例
    
    Args:
        conflict_resolution: 冲突解决策略
        
    Returns:
        技能注册器实例
    """
    return SkillRegistry(conflict_resolution)


# 测试函数
def test_registry():
    """测试注册器功能"""
    registry = SkillRegistry()
    
    # 创建测试技能
    from app.schemas.skill_metadata import SkillMetadata, SkillCategory
    
    test_skill = SkillMetadata(
        skill_id="test_skill_001",
        name="测试技能",
        display_name="测试技能",
        description="这是一个测试技能",
        category=SkillCategory.UTILITY.value,
        version="1.0.0",
        author="测试作者",
        tags=["测试", "工具"],
        dependencies=[],
        enabled=True,
        file_path="/path/to/skill.md",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        config_schema=None,
        content="",
        parameters_schema=None
    )
    
    # 测试注册
    success, result = registry.register_skill(test_skill)
    print(f"注册结果: {success}, {result}")
    
    # 测试查询
    skill = registry.get_skill("test_skill_001")
    print(f"查询结果: {skill.name if skill else 'None'}")
    
    # 测试列表
    skills, total = registry.list_skills()
    print(f"技能列表: {total} 个技能")
    
    # 测试统计
    stats = registry.get_statistics()
    print(f"统计信息: {stats}")


if __name__ == "__main__":
    test_registry()