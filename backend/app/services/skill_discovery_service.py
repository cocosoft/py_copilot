"""
技能发现服务

负责协调技能发现全流程，提供统一的技能发现接口。
整合目录扫描、元数据解析、技能注册和索引构建功能。
"""

import os
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.logging_config import logger
from app.schemas.skill_metadata import SkillMetadata
from app.services.skill_directory_scanner import SkillDirectoryScanner, create_scanner
from app.services.skill_metadata_parser import SkillMetadataParser, create_parser
from app.services.skill_registry import SkillRegistry, create_registry, ConflictResolution


class SkillDiscoveryService:
    """技能发现服务"""
    
    def __init__(
        self,
        base_directory: Optional[str] = None,
        conflict_resolution: ConflictResolution = ConflictResolution.SKIP,
        max_workers: int = 4
    ):
        """
        初始化技能发现服务
        
        Args:
            base_directory: 基础目录路径
            conflict_resolution: 冲突解决策略
            max_workers: 最大工作线程数
        """
        self.base_directory = base_directory or os.getcwd()
        self.max_workers = max_workers
        
        # 初始化组件
        self.scanner = create_scanner(self.base_directory)
        self.parser = create_parser()
        self.registry = create_registry(conflict_resolution)
        
        # 统计信息
        self.discovery_stats = {
            "total_discoveries": 0,
            "successful_discoveries": 0,
            "failed_discoveries": 0,
            "last_discovery_time": None,
            "average_discovery_time": 0.0,
        }
        
        # 缓存
        self._cache = {}
        self._cache_ttl = 300  # 5分钟
        
    def discover_skills(
        self, 
        directories: Optional[List[str]] = None,
        force_refresh: bool = False
    ) -> Tuple[List[SkillMetadata], Dict[str, Any]]:
        """
        发现技能
        
        Args:
            directories: 要扫描的目录列表
            force_refresh: 是否强制刷新缓存
            
        Returns:
            (技能列表, 发现统计信息)
        """
        start_time = time.time()
        
        # 检查缓存
        cache_key = self._generate_cache_key(directories)
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.info("使用缓存中的技能发现结果")
            return self._cache[cache_key]['skills'], self._cache[cache_key]['stats']
        
        try:
            # 1. 扫描目录
            logger.info("开始扫描技能目录...")
            skill_files = self.scanner.scan_directories(directories, max_workers=self.max_workers)
            
            if not skill_files:
                logger.warning("没有找到技能文件")
                return [], self._get_discovery_stats()
            
            logger.info(f"找到 {len(skill_files)} 个技能文件")
            
            # 2. 并行解析技能文件
            logger.info("开始解析技能文件...")
            skills_metadata = self._parse_skill_files(skill_files)
            
            if not skills_metadata:
                logger.warning("没有成功解析任何技能文件")
                return [], self._get_discovery_stats()
            
            logger.info(f"成功解析 {len(skills_metadata)} 个技能")
            
            # 3. 注册技能
            logger.info("开始注册技能...")
            registration_results = self._register_skills(skills_metadata)
            
            # 4. 更新统计信息
            discovery_time = time.time() - start_time
            self._update_discovery_stats(len(skills_metadata), registration_results, discovery_time)
            
            # 5. 更新缓存
            self._update_cache(cache_key, skills_metadata, self._get_discovery_stats())
            
            logger.info(f"技能发现完成，耗时 {discovery_time:.2f} 秒")
            
            return skills_metadata, self._get_discovery_stats()
            
        except Exception as e:
            logger.error(f"技能发现过程出错: {e}")
            self.discovery_stats["failed_discoveries"] += 1
            return [], self._get_discovery_stats()
    
    def _parse_skill_files(self, skill_files: List[str]) -> List[SkillMetadata]:
        """并行解析技能文件"""
        skills_metadata = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.parser.parse_skill_file, file_path): file_path
                for file_path in skill_files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    metadata = future.result()
                    if metadata:
                        skills_metadata.append(metadata)
                    else:
                        logger.warning(f"解析技能文件失败: {file_path}")
                except Exception as e:
                    logger.error(f"解析技能文件时出错 {file_path}: {e}")
        
        return skills_metadata
    
    def _register_skills(self, skills_metadata: List[SkillMetadata]) -> Dict[str, int]:
        """注册技能并统计结果"""
        results = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
        }
        
        for metadata in skills_metadata:
            success, message = self.registry.register_skill(metadata)
            
            if success:
                results["successful"] += 1
            elif "跳过" in message or "已存在" in message:
                results["skipped"] += 1
            else:
                results["failed"] += 1
                logger.warning(f"注册技能失败 {metadata.name}: {message}")
        
        return results
    
    def get_skills(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SkillMetadata], int]:
        """
        获取技能列表
        
        Args:
            filters: 过滤条件
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            (技能列表, 总数量)
        """
        return self.registry.list_skills(filters, skip, limit)
    
    def search_skills(
        self, 
        query: str,
        fields: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SkillMetadata], int]:
        """
        搜索技能
        
        Args:
            query: 搜索查询
            fields: 搜索字段列表
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            (技能列表, 总数量)
        """
        return self.registry.search_skills(query, fields, skip, limit)
    
    def get_skill(self, skill_id: str) -> Optional[SkillMetadata]:
        """获取单个技能"""
        return self.registry.get_skill(skill_id)
    
    def get_skill_by_name(self, name: str) -> Optional[SkillMetadata]:
        """根据名称获取技能"""
        return self.registry.get_skill_by_name(name)
    
    def enable_skill(self, skill_id: str) -> bool:
        """启用技能"""
        return self.registry.enable_skill(skill_id)
    
    def disable_skill(self, skill_id: str) -> bool:
        """禁用技能"""
        return self.registry.disable_skill(skill_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        registry_stats = self.registry.get_statistics()
        discovery_stats = self._get_discovery_stats()
        
        return {
            "registry": registry_stats,
            "discovery": discovery_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def validate_directories(self, directories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        验证技能目录结构
        
        Args:
            directories: 要验证的目录列表
            
        Returns:
            验证结果
        """
        if directories is None:
            directories = self.scanner.get_skill_directories()
        
        validation_results = {}
        
        for directory in directories:
            result = self.scanner.validate_directory(directory)
            validation_results[directory] = result
        
        return validation_results
    
    def watch_directories(
        self, 
        directories: Optional[List[str]] = None,
        callback: Optional[Callable[[List[SkillMetadata]], None]] = None,
        poll_interval: int = 30
    ) -> None:
        """
        监听目录变化（简化实现）
        
        Args:
            directories: 要监听的目录列表
            callback: 变化回调函数
            poll_interval: 轮询间隔（秒）
        """
        if directories is None:
            directories = self.scanner.get_skill_directories()
        
        if not callback:
            callback = self._default_watch_callback
        
        logger.info(f"开始监听技能目录变化: {directories}")
        
        # 简化实现：定期重新发现
        import threading
        
        def watch_loop():
            last_skills = set()
            
            while True:
                try:
                    skills, _ = self.discover_skills(directories, force_refresh=True)
                    current_skills = set(skill.skill_id for skill in skills)
                    
                    # 检测变化
                    if last_skills and current_skills != last_skills:
                        added = current_skills - last_skills
                        removed = last_skills - current_skills
                        
                        if added or removed:
                            logger.info(f"检测到技能变化: 新增 {len(added)} 个, 删除 {len(removed)} 个")
                            callback(skills)
                    
                    last_skills = current_skills
                    time.sleep(poll_interval)
                    
                except Exception as e:
                    logger.error(f"监听目录变化时出错: {e}")
                    time.sleep(poll_interval)
        
        thread = threading.Thread(target=watch_loop, daemon=True)
        thread.start()
    
    def _default_watch_callback(self, skills: List[SkillMetadata]) -> None:
        """默认监听回调函数"""
        logger.info(f"技能目录发生变化，当前共有 {len(skills)} 个技能")
    
    def _update_discovery_stats(self, total_skills: int, registration_results: Dict[str, int], discovery_time: float):
        """更新发现统计信息"""
        self.discovery_stats["total_discoveries"] += 1
        self.discovery_stats["successful_discoveries"] += registration_results["successful"]
        self.discovery_stats["failed_discoveries"] += registration_results["failed"]
        self.discovery_stats["last_discovery_time"] = datetime.now().isoformat()
        
        # 计算平均发现时间
        total_time = self.discovery_stats["average_discovery_time"] * (self.discovery_stats["total_discoveries"] - 1)
        self.discovery_stats["average_discovery_time"] = (total_time + discovery_time) / self.discovery_stats["total_discoveries"]
    
    def _get_discovery_stats(self) -> Dict[str, Any]:
        """获取发现统计信息"""
        return self.discovery_stats.copy()
    
    def _generate_cache_key(self, directories: Optional[List[str]]) -> str:
        """生成缓存键"""
        import hashlib
        
        if directories is None:
            directories = self.scanner.DEFAULT_SCAN_DIRECTORIES
        
        key_string = ":".join(sorted(directories))
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache:
            return False
        
        cache_time = self._cache[cache_key].get('timestamp', 0)
        current_time = time.time()
        
        return current_time - cache_time < self._cache_ttl
    
    def _update_cache(self, cache_key: str, skills: List[SkillMetadata], stats: Dict[str, Any]):
        """更新缓存"""
        self._cache[cache_key] = {
            'skills': skills,
            'stats': stats,
            'timestamp': time.time()
        }
        
        # 清理过期缓存
        current_time = time.time()
        expired_keys = [
            key for key, value in self._cache.items()
            if current_time - value['timestamp'] > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]


def create_discovery_service(
    base_directory: Optional[str] = None,
    conflict_resolution: ConflictResolution = ConflictResolution.SKIP,
    max_workers: int = 4
) -> SkillDiscoveryService:
    """
    创建技能发现服务实例
    
    Args:
        base_directory: 基础目录路径
        conflict_resolution: 冲突解决策略
        max_workers: 最大工作线程数
        
    Returns:
        技能发现服务实例
    """
    return SkillDiscoveryService(base_directory, conflict_resolution, max_workers)


# 测试函数
def test_discovery_service():
    """测试发现服务功能"""
    service = SkillDiscoveryService()
    
    # 测试目录验证
    validation_results = service.validate_directories()
    print("目录验证结果:")
    for directory, result in validation_results.items():
        print(f"  {directory}: {result['valid']} (技能数量: {result['skill_count']})")
    
    # 测试技能发现
    skills, stats = service.discover_skills()
    print(f"\n技能发现结果: 找到 {len(skills)} 个技能")
    print(f"发现统计: {stats}")
    
    # 测试技能查询
    if skills:
        all_skills, total = service.get_skills()
        print(f"\n技能查询结果: {total} 个技能")
        
        # 测试搜索
        search_results, search_total = service.search_skills("算法")
        print(f"搜索 '算法' 结果: {search_total} 个匹配技能")
        
        # 测试统计
        statistics = service.get_statistics()
        print(f"\n统计信息: {statistics}")


if __name__ == "__main__":
    test_discovery_service()