"""
依赖管理器
负责自动解决和安装技能所需的Python包依赖
"""

import asyncio
import subprocess
import sys
import pkg_resources
import logging
from typing import Dict, List, Optional, Tuple
from packaging import version
from packaging.requirements import Requirement

logger = logging.getLogger(__name__)


class DependencyManager:
    """依赖管理器类"""
    
    def __init__(self):
        """初始化依赖管理器"""
        self.installed_packages = {}
        self._load_installed_packages()
    
    def _load_installed_packages(self):
        """加载已安装的包信息"""
        try:
            # 获取所有已安装的包
            installed_packages = {}
            for dist in pkg_resources.working_set:
                installed_packages[dist.project_name.lower()] = {
                    'version': dist.version,
                    'location': dist.location
                }
            
            self.installed_packages = installed_packages
            logger.info(f"已加载 {len(installed_packages)} 个已安装包")
            
        except Exception as e:
            logger.error(f"加载已安装包信息失败: {e}")
            self.installed_packages = {}
    
    async def check_dependencies(self, dependencies: Dict[str, str]) -> Dict[str, Dict[str, any]]:
        """检查依赖状态
        
        Args:
            dependencies: 依赖字典，格式为 {包名: 版本要求}
            
        Returns:
            依赖检查结果
        """
        results = {}
        
        for package_name, version_spec in dependencies.items():
            package_name_lower = package_name.lower()
            
            # 检查是否已安装
            if package_name_lower in self.installed_packages:
                installed_version = self.installed_packages[package_name_lower]['version']
                compatible = self._check_version_compatibility(installed_version, version_spec)
                
                results[package_name] = {
                    'installed': True,
                    'installed_version': installed_version,
                    'required_version': version_spec,
                    'compatible': compatible,
                    'needs_upgrade': not compatible,
                    'needs_downgrade': False  # 需要更复杂的逻辑来确定
                }
            else:
                results[package_name] = {
                    'installed': False,
                    'installed_version': None,
                    'required_version': version_spec,
                    'compatible': False,
                    'needs_upgrade': False,
                    'needs_downgrade': False
                }
        
        return results
    
    def _check_version_compatibility(self, installed_version: str, required_spec: str) -> bool:
        """检查版本兼容性
        
        Args:
            installed_version: 已安装版本
            required_spec: 版本要求规范
            
        Returns:
            是否兼容
        """
        try:
            # 创建Requirement对象
            req = Requirement(f"dummy{required_spec}")
            
            # 检查版本兼容性
            installed_ver = version.parse(installed_version)
            
            # 检查所有版本规范
            for spec in req.specifier:
                if not spec.contains(installed_ver):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"版本兼容性检查失败: {e}")
            return False
    
    async def install_dependencies(self, dependencies: Dict[str, str], 
                                 upgrade: bool = False) -> Dict[str, Dict[str, any]]:
        """安装依赖
        
        Args:
            dependencies: 依赖字典
            upgrade: 是否升级已安装的包
            
        Returns:
            安装结果
        """
        results = {}
        
        # 首先检查依赖状态
        dependency_status = await self.check_dependencies(dependencies)
        
        # 确定需要安装或升级的包
        packages_to_install = []
        packages_to_upgrade = []
        
        for package_name, status in dependency_status.items():
            if not status['installed']:
                packages_to_install.append(f"{package_name}{status['required_version']}")
            elif status['needs_upgrade'] and upgrade:
                packages_to_upgrade.append(f"{package_name}{status['required_version']}")
        
        # 安装新包
        if packages_to_install:
            install_results = await self._install_packages(packages_to_install)
            results.update(install_results)
        
        # 升级现有包
        if packages_to_upgrade:
            upgrade_results = await self._upgrade_packages(packages_to_upgrade)
            results.update(upgrade_results)
        
        # 重新加载已安装包信息
        self._load_installed_packages()
        
        # 最终检查
        final_status = await self.check_dependencies(dependencies)
        
        # 合并结果
        for package_name, status in final_status.items():
            if package_name in results:
                results[package_name].update(status)
            else:
                results[package_name] = status
        
        return results
    
    async def _install_packages(self, package_specs: List[str]) -> Dict[str, Dict[str, any]]:
        """安装包列表
        
        Args:
            package_specs: 包规范列表
            
        Returns:
            安装结果
        """
        results = {}
        
        for package_spec in package_specs:
            try:
                # 解析包名
                package_name = self._extract_package_name(package_spec)
                
                logger.info(f"开始安装包: {package_spec}")
                
                # 使用pip安装
                result = await asyncio.create_subprocess_exec(
                    sys.executable, '-m', 'pip', 'install', package_spec,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    results[package_name] = {
                        'success': True,
                        'message': f"包 {package_spec} 安装成功",
                        'output': stdout.decode()
                    }
                    logger.info(f"包安装成功: {package_spec}")
                else:
                    results[package_name] = {
                        'success': False,
                        'message': f"包 {package_spec} 安装失败",
                        'error': stderr.decode()
                    }
                    logger.error(f"包安装失败: {package_spec}, 错误: {stderr.decode()}")
                
            except Exception as e:
                results[package_name] = {
                    'success': False,
                    'message': f"包 {package_spec} 安装异常",
                    'error': str(e)
                }
                logger.error(f"包安装异常: {package_spec}, 错误: {e}")
        
        return results
    
    async def _upgrade_packages(self, package_specs: List[str]) -> Dict[str, Dict[str, any]]:
        """升级包列表
        
        Args:
            package_specs: 包规范列表
            
        Returns:
            升级结果
        """
        results = {}
        
        for package_spec in package_specs:
            try:
                # 解析包名
                package_name = self._extract_package_name(package_spec)
                
                logger.info(f"开始升级包: {package_spec}")
                
                # 使用pip升级
                result = await asyncio.create_subprocess_exec(
                    sys.executable, '-m', 'pip', 'install', '--upgrade', package_spec,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    results[package_name] = {
                        'success': True,
                        'message': f"包 {package_spec} 升级成功",
                        'output': stdout.decode()
                    }
                    logger.info(f"包升级成功: {package_spec}")
                else:
                    results[package_name] = {
                        'success': False,
                        'message': f"包 {package_spec} 升级失败",
                        'error': stderr.decode()
                    }
                    logger.error(f"包升级失败: {package_spec}, 错误: {stderr.decode()}")
                
            except Exception as e:
                results[package_name] = {
                    'success': False,
                    'message': f"包 {package_spec} 升级异常",
                    'error': str(e)
                }
                logger.error(f"包升级异常: {package_spec}, 错误: {e}")
        
        return results
    
    def _extract_package_name(self, package_spec: str) -> str:
        """从包规范中提取包名
        
        Args:
            package_spec: 包规范字符串
            
        Returns:
            包名
        """
        # 移除版本规范部分
        for op in ['==', '>=', '<=', '>', '<', '~=']:
            if op in package_spec:
                return package_spec.split(op)[0].strip()
        
        return package_spec.strip()
    
    async def uninstall_package(self, package_name: str) -> Dict[str, any]:
        """卸载包
        
        Args:
            package_name: 包名
            
        Returns:
            卸载结果
        """
        try:
            # 检查包是否已安装
            if package_name.lower() not in self.installed_packages:
                return {
                    'success': False,
                    'message': f"包 {package_name} 未安装"
                }
            
            logger.info(f"开始卸载包: {package_name}")
            
            # 使用pip卸载
            result = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'uninstall', '-y', package_name,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                # 重新加载已安装包信息
                self._load_installed_packages()
                
                return {
                    'success': True,
                    'message': f"包 {package_name} 卸载成功",
                    'output': stdout.decode()
                }
            else:
                return {
                    'success': False,
                    'message': f"包 {package_name} 卸载失败",
                    'error': stderr.decode()
                }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"包 {package_name} 卸载异常",
                'error': str(e)
            }
    
    async def resolve_conflicts(self, dependencies: Dict[str, str]) -> Dict[str, Dict[str, any]]:
        """解决依赖冲突
        
        Args:
            dependencies: 依赖字典
            
        Returns:
            冲突解决结果
        """
        conflicts = {}
        
        # 检查依赖冲突
        for package_name, version_spec in dependencies.items():
            if package_name.lower() in self.installed_packages:
                installed_version = self.installed_packages[package_name.lower()]['version']
                
                if not self._check_version_compatibility(installed_version, version_spec):
                    conflicts[package_name] = {
                        'installed_version': installed_version,
                        'required_version': version_spec,
                        'conflict_type': 'version_mismatch'
                    }
        
        # 解决冲突
        resolution_results = {}
        
        for package_name, conflict_info in conflicts.items():
            # 尝试升级包来解决冲突
            upgrade_result = await self._upgrade_packages([f"{package_name}{conflict_info['required_version']}"])
            
            if package_name in upgrade_result and upgrade_result[package_name]['success']:
                resolution_results[package_name] = {
                    'resolved': True,
                    'method': 'upgrade',
                    'message': f"通过升级解决了 {package_name} 的版本冲突"
                }
            else:
                resolution_results[package_name] = {
                    'resolved': False,
                    'method': 'manual',
                    'message': f"需要手动解决 {package_name} 的版本冲突"
                }
        
        return resolution_results
    
    async def create_requirements_file(self, dependencies: Dict[str, str], 
                                     file_path: str) -> bool:
        """创建requirements.txt文件
        
        Args:
            dependencies: 依赖字典
            file_path: 文件路径
            
        Returns:
            是否成功创建
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for package_name, version_spec in dependencies.items():
                    f.write(f"{package_name}{version_spec}\n")
            
            logger.info(f"requirements文件创建成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建requirements文件失败: {e}")
            return False
    
    async def install_from_requirements(self, requirements_file: str) -> Dict[str, Dict[str, any]]:
        """从requirements文件安装依赖
        
        Args:
            requirements_file: requirements文件路径
            
        Returns:
            安装结果
        """
        try:
            # 读取requirements文件
            dependencies = {}
            with open(requirements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 解析每行
                        package_spec = line
                        package_name = self._extract_package_name(package_spec)
                        
                        # 提取版本规范
                        version_spec = line.replace(package_name, '').strip()
                        dependencies[package_name] = version_spec
            
            # 安装依赖
            return await self.install_dependencies(dependencies)
            
        except Exception as e:
            logger.error(f"从requirements文件安装依赖失败: {e}")
            return {
                'overall': {
                    'success': False,
                    'error': str(e)
                }
            }
    
    def get_package_info(self, package_name: str) -> Optional[Dict[str, any]]:
        """获取包信息
        
        Args:
            package_name: 包名
            
        Returns:
            包信息
        """
        package_name_lower = package_name.lower()
        
        if package_name_lower in self.installed_packages:
            return self.installed_packages[package_name_lower]
        
        return None
    
    async def search_package(self, package_name: str) -> Dict[str, any]:
        """搜索包信息
        
        Args:
            package_name: 包名
            
        Returns:
            包搜索信息
        """
        try:
            # 使用pip搜索包信息
            result = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'search', package_name,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'package_name': package_name,
                    'search_results': stdout.decode()
                }
            else:
                return {
                    'success': False,
                    'package_name': package_name,
                    'error': stderr.decode()
                }
            
        except Exception as e:
            return {
                'success': False,
                'package_name': package_name,
                'error': str(e)
            }


# 创建全局依赖管理器实例
dependency_manager = DependencyManager()