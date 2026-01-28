"""
技能清理器
负责技能卸载时的配置和数据清理工作
"""

import os
import shutil
import json
import logging
from typing import Dict, List, Optional, Set
from pathlib import Path

from app.schemas.skill_metadata import SkillMetadata

logger = logging.getLogger(__name__)


class SkillCleaner:
    """技能清理器类"""
    
    def __init__(self, config_dir: str = None, data_dir: str = None):
        """初始化清理器
        
        Args:
            config_dir: 配置目录路径
            data_dir: 数据目录路径
        """
        # 配置目录
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent / "config"
        self.skill_config_dir = self.config_dir / "skills"
        
        # 数据目录
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent / "data"
        self.skill_data_dir = self.data_dir / "skills"
        
        # 缓存目录
        self.cache_dir = Path(__file__).parent.parent / "cache"
        self.skill_cache_dir = self.cache_dir / "skills"
        
        # 日志目录
        self.log_dir = Path(__file__).parent.parent / "logs"
        self.skill_log_dir = self.log_dir / "skills"
        
        # 确保目录存在
        self.skill_config_dir.mkdir(parents=True, exist_ok=True)
        self.skill_data_dir.mkdir(parents=True, exist_ok=True)
        self.skill_cache_dir.mkdir(parents=True, exist_ok=True)
        self.skill_log_dir.mkdir(parents=True, exist_ok=True)
    
    async def cleanup_skill(self, skill_id: str, metadata: SkillMetadata, 
                          cleanup_config: bool = True, cleanup_data: bool = True,
                          cleanup_cache: bool = True, cleanup_logs: bool = False) -> Dict[str, any]:
        """清理技能相关文件和数据
        
        Args:
            skill_id: 技能ID
            metadata: 技能元数据
            cleanup_config: 是否清理配置
            cleanup_data: 是否清理数据
            cleanup_cache: 是否清理缓存
            cleanup_logs: 是否清理日志
            
        Returns:
            清理结果
        """
        logger.info(f"开始清理技能: {skill_id}")
        
        results = {
            'skill_id': skill_id,
            'cleanup_config': cleanup_config,
            'cleanup_data': cleanup_data,
            'cleanup_cache': cleanup_cache,
            'cleanup_logs': cleanup_logs,
            'removed_files': [],
            'removed_directories': [],
            'errors': []
        }
        
        try:
            # 清理配置
            if cleanup_config:
                config_result = await self._cleanup_config(skill_id, metadata)
                results['config_cleanup'] = config_result
                results['removed_files'].extend(config_result.get('removed_files', []))
                results['removed_directories'].extend(config_result.get('removed_directories', []))
                results['errors'].extend(config_result.get('errors', []))
            
            # 清理数据
            if cleanup_data:
                data_result = await self._cleanup_data(skill_id, metadata)
                results['data_cleanup'] = data_result
                results['removed_files'].extend(data_result.get('removed_files', []))
                results['removed_directories'].extend(data_result.get('removed_directories', []))
                results['errors'].extend(data_result.get('errors', []))
            
            # 清理缓存
            if cleanup_cache:
                cache_result = await self._cleanup_cache(skill_id, metadata)
                results['cache_cleanup'] = cache_result
                results['removed_files'].extend(cache_result.get('removed_files', []))
                results['removed_directories'].extend(cache_result.get('removed_directories', []))
                results['errors'].extend(cache_result.get('errors', []))
            
            # 清理日志
            if cleanup_logs:
                log_result = await self._cleanup_logs(skill_id, metadata)
                results['log_cleanup'] = log_result
                results['removed_files'].extend(log_result.get('removed_files', []))
                results['removed_directories'].extend(log_result.get('removed_directories', []))
                results['errors'].extend(log_result.get('errors', []))
            
            # 清理数据库记录
            db_result = await self._cleanup_database_records(skill_id, metadata)
            results['database_cleanup'] = db_result
            results['errors'].extend(db_result.get('errors', []))
            
            # 清理临时文件
            temp_result = await self._cleanup_temp_files(skill_id, metadata)
            results['temp_cleanup'] = temp_result
            results['removed_files'].extend(temp_result.get('removed_files', []))
            results['errors'].extend(temp_result.get('errors', []))
            
            logger.info(f"技能清理完成: {skill_id}")
            results['success'] = True
            results['message'] = f"技能 {skill_id} 清理完成"
            
        except Exception as e:
            logger.error(f"技能清理失败: {skill_id}, 错误: {e}")
            results['success'] = False
            results['error'] = str(e)
            results['errors'].append(str(e))
        
        return results
    
    async def _cleanup_config(self, skill_id: str, metadata: SkillMetadata) -> Dict[str, any]:
        """清理技能配置"""
        result = {
            'skill_id': skill_id,
            'removed_files': [],
            'removed_directories': [],
            'errors': []
        }
        
        try:
            # 技能配置目录
            skill_config_path = self.skill_config_dir / skill_id
            
            if skill_config_path.exists():
                if skill_config_path.is_file():
                    skill_config_path.unlink()
                    result['removed_files'].append(str(skill_config_path))
                else:
                    shutil.rmtree(skill_config_path)
                    result['removed_directories'].append(str(skill_config_path))
                logger.info(f"清理配置目录: {skill_config_path}")
            
            # 全局配置文件中的技能配置
            global_config_path = self.config_dir / "global_config.json"
            if global_config_path.exists():
                await self._remove_skill_from_config(global_config_path, skill_id, result)
            
            # 用户配置文件中的技能配置
            user_config_path = self.config_dir / "user_config.json"
            if user_config_path.exists():
                await self._remove_skill_from_config(user_config_path, skill_id, result)
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"配置清理失败: {str(e)}")
            result['success'] = False
        
        return result
    
    async def _remove_skill_from_config(self, config_path: Path, skill_id: str, result: Dict[str, any]):
        """从配置文件中移除技能配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 检查是否有技能相关配置
            modified = False
            
            # 移除技能配置节
            if 'skills' in config_data and skill_id in config_data['skills']:
                del config_data['skills'][skill_id]
                modified = True
            
            # 移除技能依赖配置
            if 'dependencies' in config_data and skill_id in config_data['dependencies']:
                del config_data['dependencies'][skill_id]
                modified = True
            
            # 移除技能权限配置
            if 'permissions' in config_data and skill_id in config_data['permissions']:
                del config_data['permissions'][skill_id]
                modified = True
            
            if modified:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                result['removed_files'].append(f"配置项从 {config_path}")
                logger.info(f"从配置文件移除技能配置: {skill_id}")
            
        except Exception as e:
            result['errors'].append(f"配置文件处理失败 {config_path}: {str(e)}")
    
    async def _cleanup_data(self, skill_id: str, metadata: SkillMetadata) -> Dict[str, any]:
        """清理技能数据"""
        result = {
            'skill_id': skill_id,
            'removed_files': [],
            'removed_directories': [],
            'errors': []
        }
        
        try:
            # 技能数据目录
            skill_data_path = self.skill_data_dir / skill_id
            
            if skill_data_path.exists():
                if skill_data_path.is_file():
                    skill_data_path.unlink()
                    result['removed_files'].append(str(skill_data_path))
                else:
                    shutil.rmtree(skill_data_path)
                    result['removed_directories'].append(str(skill_data_path))
                logger.info(f"清理数据目录: {skill_data_path}")
            
            # 数据库数据清理（在数据库清理方法中处理）
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"数据清理失败: {str(e)}")
            result['success'] = False
        
        return result
    
    async def _cleanup_cache(self, skill_id: str, metadata: SkillMetadata) -> Dict[str, any]:
        """清理技能缓存"""
        result = {
            'skill_id': skill_id,
            'removed_files': [],
            'removed_directories': [],
            'errors': []
        }
        
        try:
            # 技能缓存目录
            skill_cache_path = self.skill_cache_dir / skill_id
            
            if skill_cache_path.exists():
                if skill_cache_path.is_file():
                    skill_cache_path.unlink()
                    result['removed_files'].append(str(skill_cache_path))
                else:
                    shutil.rmtree(skill_cache_path)
                    result['removed_directories'].append(str(skill_cache_path))
                logger.info(f"清理缓存目录: {skill_cache_path}")
            
            # 清理内存缓存（如果有）
            await self._cleanup_memory_cache(skill_id, result)
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"缓存清理失败: {str(e)}")
            result['success'] = False
        
        return result
    
    async def _cleanup_memory_cache(self, skill_id: str, result: Dict[str, any]):
        """清理内存缓存"""
        try:
            # 这里可以清理应用级别的内存缓存
            # 例如：清理技能执行结果的缓存
            # 需要根据具体的缓存实现来编写
            
            # 示例：清理全局缓存字典中的技能相关数据
            if hasattr(self, '_memory_cache') and isinstance(self._memory_cache, dict):
                keys_to_remove = [key for key in self._memory_cache.keys() if key.startswith(f"{skill_id}_")]
                for key in keys_to_remove:
                    del self._memory_cache[key]
                    result['removed_files'].append(f"内存缓存键: {key}")
            
            logger.info(f"清理内存缓存: {skill_id}")
            
        except Exception as e:
            result['errors'].append(f"内存缓存清理失败: {str(e)}")
    
    async def _cleanup_logs(self, skill_id: str, metadata: SkillMetadata) -> Dict[str, any]:
        """清理技能日志"""
        result = {
            'skill_id': skill_id,
            'removed_files': [],
            'removed_directories': [],
            'errors': []
        }
        
        try:
            # 技能日志目录
            skill_log_path = self.skill_log_dir / skill_id
            
            if skill_log_path.exists():
                if skill_log_path.is_file():
                    skill_log_path.unlink()
                    result['removed_files'].append(str(skill_log_path))
                else:
                    shutil.rmtree(skill_log_path)
                    result['removed_directories'].append(str(skill_log_path))
                logger.info(f"清理日志目录: {skill_log_path}")
            
            # 清理主日志文件中的技能相关日志
            main_log_path = self.log_dir / "app.log"
            if main_log_path.exists():
                await self._clean_skill_logs_from_file(main_log_path, skill_id, result)
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"日志清理失败: {str(e)}")
            result['success'] = False
        
        return result
    
    async def _clean_skill_logs_from_file(self, log_path: Path, skill_id: str, result: Dict[str, any]):
        """从日志文件中清理技能相关日志"""
        try:
            # 这里可以实现日志文件的清理逻辑
            # 由于日志文件通常很大，建议保留日志，只标记清理
            
            # 示例：创建清理标记文件
            cleanup_marker = log_path.parent / f"{log_path.name}.{skill_id}.cleaned"
            cleanup_marker.touch()
            
            result['removed_files'].append(f"日志清理标记: {cleanup_marker}")
            logger.info(f"创建日志清理标记: {cleanup_marker}")
            
        except Exception as e:
            result['errors'].append(f"日志文件处理失败 {log_path}: {str(e)}")
    
    async def _cleanup_database_records(self, skill_id: str, metadata: SkillMetadata) -> Dict[str, any]:
        """清理数据库记录"""
        result = {
            'skill_id': skill_id,
            'removed_records': 0,
            'errors': []
        }
        
        try:
            # 这里需要实现数据库记录的清理
            # 需要根据具体的数据库模型来编写
            
            # 示例：清理技能相关的数据库表
            removed_count = await self._cleanup_skill_database_tables(skill_id)
            result['removed_records'] = removed_count
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"数据库清理失败: {str(e)}")
            result['success'] = False
        
        return result
    
    async def _cleanup_skill_database_tables(self, skill_id: str) -> int:
        """清理技能相关的数据库表"""
        # 这里需要根据具体的数据库模型实现
        # 返回删除的记录数
        
        # 示例实现（需要根据实际数据库结构调整）
        try:
            # 导入数据库模型
            from app.database import get_db_session
            from app.models.skill_models import SkillConfig, SkillExecutionLog
            
            removed_count = 0
            
            async with get_db_session() as session:
                # 删除技能配置记录
                config_records = await session.execute(
                    SkillConfig.__table__.delete().where(SkillConfig.skill_id == skill_id)
                )
                removed_count += config_records.rowcount
                
                # 删除技能执行日志
                log_records = await session.execute(
                    SkillExecutionLog.__table__.delete().where(SkillExecutionLog.skill_id == skill_id)
                )
                removed_count += log_records.rowcount
                
                await session.commit()
            
            logger.info(f"清理数据库记录: {skill_id}, 删除 {removed_count} 条记录")
            return removed_count
            
        except Exception as e:
            logger.error(f"数据库清理失败: {skill_id}, 错误: {e}")
            return 0
    
    async def _cleanup_temp_files(self, skill_id: str, metadata: SkillMetadata) -> Dict[str, any]:
        """清理临时文件"""
        result = {
            'skill_id': skill_id,
            'removed_files': [],
            'errors': []
        }
        
        try:
            import tempfile
            
            # 清理系统临时目录中的技能相关文件
            temp_dir = Path(tempfile.gettempdir())
            
            # 查找技能相关的临时文件
            skill_temp_patterns = [
                f"*{skill_id}*",
                f"*py_copilot_skill_{skill_id}*",
                f"*skill_{skill_id}_*"
            ]
            
            removed_count = 0
            for pattern in skill_temp_patterns:
                for temp_file in temp_dir.glob(pattern):
                    try:
                        if temp_file.is_file():
                            temp_file.unlink()
                        else:
                            shutil.rmtree(temp_file)
                        
                        result['removed_files'].append(str(temp_file))
                        removed_count += 1
                        
                    except Exception as e:
                        result['errors'].append(f"临时文件清理失败 {temp_file}: {str(e)}")
            
            logger.info(f"清理临时文件: {skill_id}, 删除 {removed_count} 个文件")
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"临时文件清理失败: {str(e)}")
            result['success'] = False
        
        return result
    
    async def get_skill_files(self, skill_id: str) -> Dict[str, List[str]]:
        """获取技能相关的所有文件列表
        
        Args:
            skill_id: 技能ID
            
        Returns:
            文件列表
        """
        files = {
            'config_files': [],
            'data_files': [],
            'cache_files': [],
            'log_files': [],
            'temp_files': []
        }
        
        # 配置文件
        config_path = self.skill_config_dir / skill_id
        if config_path.exists():
            if config_path.is_file():
                files['config_files'].append(str(config_path))
            else:
                files['config_files'].extend([str(p) for p in config_path.rglob('*')])
        
        # 数据文件
        data_path = self.skill_data_dir / skill_id
        if data_path.exists():
            if data_path.is_file():
                files['data_files'].append(str(data_path))
            else:
                files['data_files'].extend([str(p) for p in data_path.rglob('*')])
        
        # 缓存文件
        cache_path = self.skill_cache_dir / skill_id
        if cache_path.exists():
            if cache_path.is_file():
                files['cache_files'].append(str(cache_path))
            else:
                files['cache_files'].extend([str(p) for p in cache_path.rglob('*')])
        
        # 日志文件
        log_path = self.skill_log_dir / skill_id
        if log_path.exists():
            if log_path.is_file():
                files['log_files'].append(str(log_path))
            else:
                files['log_files'].extend([str(p) for p in log_path.rglob('*')])
        
        # 临时文件
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        skill_temp_patterns = [f"*{skill_id}*", f"*py_copilot_skill_{skill_id}*"]
        
        for pattern in skill_temp_patterns:
            files['temp_files'].extend([str(p) for p in temp_dir.glob(pattern)])
        
        return files
    
    async def preview_cleanup(self, skill_id: str, metadata: SkillMetadata) -> Dict[str, any]:
        """预览清理操作
        
        Args:
            skill_id: 技能ID
            metadata: 技能元数据
            
        Returns:
            预览结果
        """
        preview = {
            'skill_id': skill_id,
            'files_to_remove': await self.get_skill_files(skill_id),
            'database_records': await self._preview_database_cleanup(skill_id),
            'total_size': await self._calculate_total_size(skill_id),
            'warnings': []
        }
        
        # 检查是否有重要数据
        data_files_count = len(preview['files_to_remove']['data_files'])
        if data_files_count > 0:
            preview['warnings'].append(f"将删除 {data_files_count} 个数据文件")
        
        db_records_count = preview['database_records'].get('total_records', 0)
        if db_records_count > 0:
            preview['warnings'].append(f"将删除 {db_records_count} 条数据库记录")
        
        return preview
    
    async def _preview_database_cleanup(self, skill_id: str) -> Dict[str, any]:
        """预览数据库清理"""
        # 这里需要根据具体的数据库模型实现
        # 返回将删除的记录统计
        
        try:
            from app.database import get_db_session
            from app.models.skill_models import SkillConfig, SkillExecutionLog
            
            preview = {'tables': {}, 'total_records': 0}
            
            async with get_db_session() as session:
                # 统计技能配置记录
                config_count = await session.execute(
                    SkillConfig.__table__.select().where(SkillConfig.skill_id == skill_id)
                )
                preview['tables']['skill_configs'] = len(config_count.fetchall())
                
                # 统计技能执行日志
                log_count = await session.execute(
                    SkillExecutionLog.__table__.select().where(SkillExecutionLog.skill_id == skill_id)
                )
                preview['tables']['skill_execution_logs'] = len(log_count.fetchall())
            
            preview['total_records'] = sum(preview['tables'].values())
            return preview
            
        except Exception as e:
            logger.error(f"数据库预览失败: {skill_id}, 错误: {e}")
            return {'tables': {}, 'total_records': 0, 'error': str(e)}
    
    async def _calculate_total_size(self, skill_id: str) -> int:
        """计算技能相关文件的总大小"""
        total_size = 0
        
        files = await self.get_skill_files(skill_id)
        
        for category, file_list in files.items():
            for file_path in file_list:
                path = Path(file_path)
                if path.exists():
                    if path.is_file():
                        total_size += path.stat().st_size
                    else:
                        total_size += sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        
        return total_size


# 创建全局清理器实例
skill_cleaner = SkillCleaner()