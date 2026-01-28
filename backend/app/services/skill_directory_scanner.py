"""
技能目录扫描器

负责扫描指定目录，发现技能文件并返回文件路径列表。
支持多目录扫描、递归扫描、文件过滤和目录排除功能。
"""

import os
import re
from typing import List, Optional, Callable, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.logging_config import logger


class SkillDirectoryScanner:
    """技能目录扫描器"""
    
    # 默认配置
    DEFAULT_SCAN_DIRECTORIES = [
        "app/skills/skills",           # 主技能目录
        "app/skills/custom",           # 自定义技能目录
        "app/skills/third_party",      # 第三方技能目录
    ]
    
    # 有效技能文件模式
    VALID_SKILL_FILES = [
        "SKILL.md",                    # 标准技能文件
        "skill.yaml",                  # YAML格式技能文件
        "skill.json",                  # JSON格式技能文件
        "skill.yml",                   # YML格式技能文件
    ]
    
    # 排除目录模式
    EXCLUDE_DIRECTORIES = [
        "__pycache__",
        ".git",
        "node_modules",
        "temp",
        "tmp",
        ".cache",
        "logs",
        "build",
        "dist",
    ]
    
    # 排除文件模式
    EXCLUDE_FILES = [
        r'\.pyc$',                     # Python编译文件
        r'\.log$',                     # 日志文件
        r'\.tmp$',                     # 临时文件
        r'\.bak$',                     # 备份文件
        r'~$',                         # 备份文件
    ]
    
    def __init__(self, base_directory: Optional[str] = None):
        """
        初始化技能目录扫描器
        
        Args:
            base_directory: 基础目录路径，用于解析相对路径
        """
        self.base_directory = base_directory or os.getcwd()
        self._compiled_exclude_patterns = [
            re.compile(pattern) for pattern in self.EXCLUDE_FILES
        ]
        
    def scan_directories(
        self, 
        directories: Optional[List[str]] = None,
        recursive: bool = True,
        max_workers: int = 4
    ) -> List[str]:
        """
        扫描指定目录，发现技能文件
        
        Args:
            directories: 要扫描的目录列表，如果为None则使用默认目录
            recursive: 是否递归扫描子目录
            max_workers: 最大工作线程数
            
        Returns:
            技能文件路径列表
        """
        if directories is None:
            directories = self.DEFAULT_SCAN_DIRECTORIES
        
        # 解析绝对路径
        absolute_directories = [
            self._resolve_path(directory) for directory in directories
        ]
        
        # 过滤存在的目录
        existing_directories = [
            directory for directory in absolute_directories 
            if os.path.exists(directory) and os.path.isdir(directory)
        ]
        
        if not existing_directories:
            logger.warning("没有找到有效的技能目录")
            return []
        
        logger.info(f"开始扫描技能目录: {existing_directories}")
        
        # 并行扫描目录
        skill_files = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_directory = {
                executor.submit(self._scan_single_directory, directory, recursive): directory
                for directory in existing_directories
            }
            
            for future in as_completed(future_to_directory):
                directory = future_to_directory[future]
                try:
                    files = future.result()
                    skill_files.extend(files)
                    logger.debug(f"目录 {directory} 扫描完成，找到 {len(files)} 个技能文件")
                except Exception as e:
                    logger.error(f"扫描目录 {directory} 时出错: {e}")
        
        logger.info(f"技能扫描完成，共找到 {len(skill_files)} 个技能文件")
        return skill_files
    
    def _scan_single_directory(self, directory: str, recursive: bool) -> List[str]:
        """
        扫描单个目录
        
        Args:
            directory: 目录路径
            recursive: 是否递归扫描
            
        Returns:
            技能文件路径列表
        """
        skill_files = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # 过滤排除目录
                dirs[:] = [d for d in dirs if not self._should_exclude_directory(d)]
                
                # 扫描当前目录的文件
                for file in files:
                    if self._is_valid_skill_file(file):
                        file_path = os.path.join(root, file)
                        skill_files.append(file_path)
                
                # 如果不递归，只扫描当前目录
                if not recursive:
                    break
                    
        except PermissionError as e:
            logger.warning(f"没有权限访问目录 {directory}: {e}")
        except Exception as e:
            logger.error(f"扫描目录 {directory} 时出错: {e}")
            
        return skill_files
    
    def _should_exclude_directory(self, directory_name: str) -> bool:
        """
        判断是否应该排除目录
        
        Args:
            directory_name: 目录名称
            
        Returns:
            是否排除该目录
        """
        return directory_name in self.EXCLUDE_DIRECTORIES or directory_name.startswith('.')
    
    def _is_valid_skill_file(self, filename: str) -> bool:
        """
        判断是否为有效的技能文件
        
        Args:
            filename: 文件名
            
        Returns:
            是否为有效技能文件
        """
        # 检查是否在有效文件列表中
        if filename in self.VALID_SKILL_FILES:
            return True
        
        # 检查是否应该排除
        for pattern in self._compiled_exclude_patterns:
            if pattern.search(filename):
                return False
        
        return False
    
    def _resolve_path(self, path: str) -> str:
        """
        解析路径为绝对路径
        
        Args:
            path: 路径字符串
            
        Returns:
            绝对路径
        """
        if os.path.isabs(path):
            return path
        
        return os.path.join(self.base_directory, path)
    
    def get_skill_directories(self) -> List[str]:
        """
        获取所有技能目录
        
        Returns:
            技能目录路径列表
        """
        directories = []
        
        for directory in self.DEFAULT_SCAN_DIRECTORIES:
            absolute_path = self._resolve_path(directory)
            if os.path.exists(absolute_path) and os.path.isdir(absolute_path):
                directories.append(absolute_path)
        
        return directories
    
    def watch_directory(
        self, 
        directory: str, 
        callback: Callable[[List[str]], None],
        poll_interval: int = 5
    ) -> None:
        """
        监听目录变化（简化实现，实际生产环境应使用watchdog等库）
        
        Args:
            directory: 要监听的目录
            callback: 变化回调函数
            poll_interval: 轮询间隔（秒）
        """
        logger.warning("目录监听功能需要集成watchdog库，当前为简化实现")
        
        # 记录初始状态
        initial_files = set(self._scan_single_directory(directory, True))
        
        # 简化实现：定期轮询
        import time
        while True:
            time.sleep(poll_interval)
            
            try:
                current_files = set(self._scan_single_directory(directory, True))
                
                # 检测变化
                added_files = current_files - initial_files
                removed_files = initial_files - current_files
                
                if added_files or removed_files:
                    logger.info(f"检测到目录变化: 新增 {len(added_files)} 个文件, 删除 {len(removed_files)} 个文件")
                    callback(list(current_files))
                    initial_files = current_files
                    
            except Exception as e:
                logger.error(f"监听目录 {directory} 时出错: {e}")
    
    def validate_directory(self, directory: str) -> Dict[str, Any]:
        """
        验证目录结构是否符合技能目录规范
        
        Args:
            directory: 目录路径
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'skill_count': 0,
            'directory_structure': {}
        }
        
        if not os.path.exists(directory):
            result['errors'].append(f"目录不存在: {directory}")
            return result
        
        if not os.path.isdir(directory):
            result['errors'].append(f"路径不是目录: {directory}")
            return result
        
        # 扫描目录结构
        skill_files = self._scan_single_directory(directory, True)
        result['skill_count'] = len(skill_files)
        
        # 分析目录结构
        structure = {}
        for file_path in skill_files:
            relative_path = os.path.relpath(file_path, directory)
            dir_name = os.path.dirname(relative_path)
            file_name = os.path.basename(file_path)
            
            if dir_name not in structure:
                structure[dir_name] = []
            structure[dir_name].append(file_name)
        
        result['directory_structure'] = structure
        
        # 验证技能文件
        for file_path in skill_files:
            if not self._validate_skill_file_structure(file_path):
                result['warnings'].append(f"技能文件结构可能有问题: {file_path}")
        
        # 如果没有找到技能文件，添加警告
        if not skill_files:
            result['warnings'].append("目录中没有找到技能文件")
        
        result['valid'] = len(result['errors']) == 0
        return result
    
    def _validate_skill_file_structure(self, file_path: str) -> bool:
        """
        验证技能文件结构（基础验证）
        
        Args:
            file_path: 技能文件路径
            
        Returns:
            文件结构是否有效
        """
        try:
            # 检查文件大小（不超过10MB）
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"技能文件过大: {file_path} ({file_size} bytes)")
                return False
            
            # 检查文件可读性
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # 只读取前1KB进行基础验证
                
            # 对于SKILL.md文件，检查是否包含frontmatter
            if file_path.endswith('SKILL.md'):
                if '---' not in content:
                    logger.warning(f"SKILL.md文件缺少frontmatter: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证技能文件 {file_path} 时出错: {e}")
            return False


def create_scanner(base_directory: Optional[str] = None) -> SkillDirectoryScanner:
    """
    创建技能目录扫描器实例
    
    Args:
        base_directory: 基础目录路径
        
    Returns:
        技能目录扫描器实例
    """
    return SkillDirectoryScanner(base_directory)


# 测试函数
def test_scanner():
    """测试扫描器功能"""
    scanner = SkillDirectoryScanner()
    
    # 测试扫描默认目录
    skill_files = scanner.scan_directories()
    print(f"找到 {len(skill_files)} 个技能文件:")
    for file in skill_files[:5]:  # 只显示前5个
        print(f"  - {file}")
    
    # 测试验证目录
    if skill_files:
        test_dir = os.path.dirname(skill_files[0])
        validation_result = scanner.validate_directory(test_dir)
        print(f"\n目录验证结果: {validation_result}")


if __name__ == "__main__":
    test_scanner()