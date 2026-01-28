"""
技能安装器服务
负责技能的安装、卸载和依赖管理
"""

import asyncio
import json
import os
import shutil
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import logging
from urllib.parse import urlparse

from app.schemas.skill_metadata import SkillMetadata
from app.skills.skill_registry import SkillRegistry
from app.services.dependency_manager import dependency_manager
from app.services.skill_cleaner import skill_cleaner

logger = logging.getLogger(__name__)


class SkillInstaller:
    """技能安装器类"""
    
    def __init__(self, skills_dir: str = None):
        """初始化安装器
        
        Args:
            skills_dir: 技能安装目录，默认为项目下的skills目录
        """
        self.skills_dir = Path(skills_dir) if skills_dir else Path(__file__).parent.parent / "skills"
        self.install_log_path = self.skills_dir / "install_log.json"
        self.registry = SkillRegistry()
        
        # 确保目录存在
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载安装日志
        self.install_log = self._load_install_log()
    
    def _load_install_log(self) -> Dict[str, Any]:
        """加载安装日志"""
        if self.install_log_path.exists():
            try:
                with open(self.install_log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载安装日志失败: {e}")
                return {}
        return {}
    
    def _save_install_log(self):
        """保存安装日志"""
        try:
            with open(self.install_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.install_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存安装日志失败: {e}")
    
    async def install_skill(self, skill_id: str, source: str, force: bool = False) -> Dict[str, Any]:
        """安装技能
        
        Args:
            skill_id: 技能ID
            source: 技能来源（本地路径、Git仓库、URL等）
            force: 是否强制重新安装
            
        Returns:
            安装结果信息
        """
        logger.info(f"开始安装技能: {skill_id}, 来源: {source}")
        
        # 检查技能是否已安装
        if not force and self.is_skill_installed(skill_id):
            return {
                "success": False,
                "error": f"技能 {skill_id} 已安装",
                "skill_id": skill_id
            }
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 下载或复制技能文件
            skill_path = await self._fetch_skill(source, temp_dir)
            
            # 验证技能元数据
            metadata = await self._validate_skill(skill_path)
            
            # 检查依赖
            dependency_check = await self._check_dependencies(metadata)
            
            # 检查是否有不兼容的依赖
            incompatible_deps = [
                dep_name for dep_name, status in dependency_check.items() 
                if not status.get('compatible', False)
            ]
            
            if incompatible_deps:
                logger.warning(f"发现不兼容的依赖: {', '.join(incompatible_deps)}")
            
            # 安装依赖
            dependency_install = await self._install_dependencies(metadata, upgrade=True)
            
            # 检查安装结果
            failed_installs = [
                dep_name for dep_name, result in dependency_install.items()
                if not result.get('success', False)
            ]
            
            if failed_installs:
                logger.warning(f"依赖安装失败: {', '.join(failed_installs)}")
            
            # 复制到技能目录
            target_path = self.skills_dir / skill_id
            await self._copy_skill_files(skill_path, target_path)
            
            # 更新安装日志
            self._update_install_log(skill_id, metadata, source)
            
            # 重新加载技能注册表
            await self.registry.reload_skills()
            
            logger.info(f"技能安装成功: {skill_id}")
            
            return {
                "success": True,
                "skill_id": skill_id,
                "metadata": metadata.dict(),
                "install_path": str(target_path),
                "message": "技能安装成功"
            }
            
        except Exception as e:
            logger.error(f"技能安装失败: {skill_id}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill_id": skill_id
            }
        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    async def _fetch_skill(self, source: str, temp_dir: str) -> str:
        """获取技能文件
        
        Args:
            source: 技能来源
            temp_dir: 临时目录
            
        Returns:
            技能文件路径
        """
        source_path = source.strip()
        
        # 判断来源类型
        if source_path.startswith('http://') or source_path.startswith('https://'):
            # 从URL下载
            return await self._download_from_url(source_path, temp_dir)
        elif source_path.startswith('git@') or source_path.endswith('.git'):
            # 从Git仓库克隆
            return await self._clone_from_git(source_path, temp_dir)
        elif os.path.exists(source_path):
            # 本地文件或目录
            return await self._copy_from_local(source_path, temp_dir)
        else:
            # 从技能市场获取（需要实现市场API）
            return await self._fetch_from_market(source_path, temp_dir)
    
    async def _download_from_url(self, url: str, temp_dir: str) -> str:
        """从URL下载技能"""
        import aiohttp
        import aiofiles
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"下载失败，HTTP状态码: {response.status}")
                
                # 获取文件名
                content_disposition = response.headers.get('content-disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                    parsed_url = urlparse(url)
                    filename = os.path.basename(parsed_url.path) or 'skill.zip'
                
                file_path = os.path.join(temp_dir, filename)
                
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                # 如果是压缩文件，解压
                if filename.endswith(('.zip', '.tar.gz', '.tar')):
                    return await self._extract_archive(file_path, temp_dir)
                
                return file_path
    
    async def _clone_from_git(self, repo_url: str, temp_dir: str) -> str:
        """从Git仓库克隆技能"""
        import subprocess
        
        # 使用git命令克隆仓库
        repo_dir = os.path.join(temp_dir, 'repo')
        
        try:
            result = await asyncio.create_subprocess_exec(
                'git', 'clone', repo_url, repo_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise Exception(f"Git克隆失败: {stderr.decode()}")
            
            return repo_dir
            
        except Exception as e:
            raise Exception(f"Git操作失败: {e}")
    
    async def _copy_from_local(self, source_path: str, temp_dir: str) -> str:
        """从本地路径复制技能"""
        target_path = os.path.join(temp_dir, 'skill')
        
        if os.path.isfile(source_path):
            # 如果是文件，直接复制
            shutil.copy2(source_path, target_path)
            
            # 如果是压缩文件，解压
            if source_path.endswith(('.zip', '.tar.gz', '.tar')):
                return await self._extract_archive(target_path, temp_dir)
            
            return target_path
        else:
            # 如果是目录，复制整个目录
            shutil.copytree(source_path, target_path)
            return target_path
    
    async def _fetch_from_market(self, skill_id: str, temp_dir: str) -> str:
        """从技能市场获取技能"""
        # 这里需要实现与技能市场的API交互
        # 暂时返回模拟数据
        raise Exception("技能市场功能暂未实现")
    
    async def _extract_archive(self, archive_path: str, temp_dir: str) -> str:
        """解压压缩文件"""
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        if archive_path.endswith('.zip'):
            import zipfile
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tar'):
            import tarfile
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_dir)
        else:
            raise Exception(f"不支持的压缩格式: {archive_path}")
        
        return extract_dir
    
    async def _validate_skill(self, skill_path: str) -> SkillMetadata:
        """验证技能元数据"""
        # 查找skill.json文件
        skill_json_path = None
        
        for root, dirs, files in os.walk(skill_path):
            if 'skill.json' in files:
                skill_json_path = os.path.join(root, 'skill.json')
                break
        
        if not skill_json_path:
            raise Exception("未找到skill.json文件")
        
        # 读取和验证元数据
        try:
            with open(skill_json_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            metadata = SkillMetadata(**metadata_dict)
            
            # 验证必需字段
            if not metadata.id:
                raise Exception("技能ID不能为空")
            if not metadata.name:
                raise Exception("技能名称不能为空")
            if not metadata.version:
                raise Exception("技能版本不能为空")
            
            return metadata
            
        except Exception as e:
            raise Exception(f"技能元数据验证失败: {e}")
    
    async def _check_dependencies(self, metadata: SkillMetadata) -> Dict[str, Dict[str, any]]:
        """检查技能依赖
        
        Args:
            metadata: 技能元数据
            
        Returns:
            依赖检查结果
        """
        if not metadata.dependencies:
            return {}
        
        return await dependency_manager.check_dependencies(metadata.dependencies)
    
    async def _install_dependencies(self, metadata: SkillMetadata, upgrade: bool = False) -> Dict[str, Dict[str, any]]:
        """安装技能依赖
        
        Args:
            metadata: 技能元数据
            upgrade: 是否升级已安装的包
            
        Returns:
            依赖安装结果
        """
        if not metadata.dependencies:
            return {}
        
        logger.info(f"开始安装依赖: {metadata.dependencies}")
        
        # 使用依赖管理器安装依赖
        return await dependency_manager.install_dependencies(metadata.dependencies, upgrade=upgrade)
    
    async def _copy_skill_files(self, source_path: str, target_path: Path):
        """复制技能文件到安装目录"""
        if target_path.exists():
            shutil.rmtree(target_path)
        
        if os.path.isfile(source_path):
            shutil.copy2(source_path, target_path)
        else:
            shutil.copytree(source_path, target_path)
    
    def _update_install_log(self, skill_id: str, metadata: SkillMetadata, source: str):
        """更新安装日志"""
        if 'installed_skills' not in self.install_log:
            self.install_log['installed_skills'] = {}
        
        self.install_log['installed_skills'][skill_id] = {
            'metadata': metadata.dict(),
            'source': source,
            'install_time': datetime.now().isoformat(),
            'install_path': str(self.skills_dir / skill_id)
        }
        
        self._save_install_log()
    
    async def uninstall_skill(self, skill_id: str, cleanup: bool = True) -> Dict[str, Any]:
        """卸载技能
        
        Args:
            skill_id: 技能ID
            cleanup: 是否清理配置和数据
            
        Returns:
            卸载结果信息
        """
        logger.info(f"开始卸载技能: {skill_id}, cleanup={cleanup}")
        
        if not self.is_skill_installed(skill_id):
            return {
                "success": False,
                "error": f"技能 {skill_id} 未安装",
                "skill_id": skill_id
            }
        
        try:
            # 获取技能信息
            skill_info = self.get_skill_info(skill_id)
            metadata = None
            
            if skill_info and 'metadata' in skill_info:
                metadata_dict = skill_info['metadata']
                metadata = SkillMetadata(**metadata_dict)
            
            # 清理技能相关文件和数据
            if cleanup and metadata:
                cleanup_result = await skill_cleaner.cleanup_skill(
                    skill_id=skill_id,
                    metadata=metadata,
                    cleanup_config=True,
                    cleanup_data=True,
                    cleanup_cache=True,
                    cleanup_logs=False
                )
                
                if not cleanup_result.get('success', False):
                    logger.warning(f"技能清理部分失败: {skill_id}, 错误: {cleanup_result.get('errors', [])}")
            
            # 获取技能路径
            skill_path = self.skills_dir / skill_id
            
            # 删除技能文件
            if skill_path.exists():
                if skill_path.is_file():
                    skill_path.unlink()
                else:
                    shutil.rmtree(skill_path)
            
            # 更新安装日志
            if 'installed_skills' in self.install_log:
                self.install_log['installed_skills'].pop(skill_id, None)
                self._save_install_log()
            
            # 重新加载技能注册表
            await self.registry.reload_skills()
            
            logger.info(f"技能卸载成功: {skill_id}")
            
            return {
                "success": True,
                "skill_id": skill_id,
                "message": "技能卸载成功",
                "cleanup_performed": cleanup,
                "cleanup_result": cleanup_result if cleanup else None
            }
            
        except Exception as e:
            logger.error(f"技能卸载失败: {skill_id}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill_id": skill_id
            }
    
    def is_skill_installed(self, skill_id: str) -> bool:
        """检查技能是否已安装"""
        # 检查安装日志
        if 'installed_skills' in self.install_log:
            if skill_id in self.install_log['installed_skills']:
                return True
        
        # 检查文件系统
        skill_path = self.skills_dir / skill_id
        return skill_path.exists()
    
    def get_installed_skills(self) -> List[Dict[str, Any]]:
        """获取已安装的技能列表"""
        installed_skills = []
        
        if 'installed_skills' in self.install_log:
            for skill_id, install_info in self.install_log['installed_skills'].items():
                installed_skills.append({
                    'skill_id': skill_id,
                    **install_info
                })
        
        return installed_skills
    
    def get_skill_info(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能详细信息"""
        if 'installed_skills' in self.install_log:
            return self.install_log['installed_skills'].get(skill_id)
        return None
    
    async def update_skill(self, skill_id: str) -> Dict[str, Any]:
        """更新技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            更新结果信息
        """
        skill_info = self.get_skill_info(skill_id)
        if not skill_info:
            return {
                "success": False,
                "error": f"技能 {skill_id} 未安装",
                "skill_id": skill_id
            }
        
        # 获取源信息
        source = skill_info.get('source')
        if not source:
            return {
                "success": False,
                "error": f"技能 {skill_id} 无源信息，无法更新",
                "skill_id": skill_id
            }
        
        # 先卸载旧版本
        uninstall_result = await self.uninstall_skill(skill_id)
        if not uninstall_result['success']:
            return uninstall_result
        
        # 安装新版本
        return await self.install_skill(skill_id, source, force=True)


# 创建全局安装器实例
skill_installer = SkillInstaller()