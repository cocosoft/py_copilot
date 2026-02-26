"""
存储路径管理器

统一管理文件存储路径，实现用户隔离和功能细分
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class FileCategory(Enum):
    """文件分类枚举"""
    CONVERSATION_ATTACHMENT = "conversation_attachment"
    VOICE_MESSAGE = "voice_message"
    KNOWLEDGE_DOCUMENT = "knowledge_document"
    KNOWLEDGE_EXTRACT = "knowledge_extract"
    TRANSLATION_INPUT = "translation_input"
    TRANSLATION_OUTPUT = "translation_output"
    USER_AVATAR = "user_avatar"
    USER_EXPORT = "user_export"
    TEMP_FILE = "temp_file"


class FilePrefix:
    """文件前缀定义"""
    
    # 聊天相关
    CONVERSATION_ATTACHMENT = "conv"
    VOICE_MESSAGE = "voice"
    
    # 知识库相关
    KNOWLEDGE_DOCUMENT = "kb"
    KNOWLEDGE_EXTRACT = "kb_ext"
    
    # 翻译相关
    TRANSLATION_INPUT = "trans_in"
    TRANSLATION_OUTPUT = "trans_out"
    
    # 用户相关
    USER_AVATAR = "avatar"
    USER_EXPORT = "export"
    
    # 临时文件
    TEMP_FILE = "temp"
    
    # 系统文件
    SYSTEM_BACKUP = "backup"
    SYSTEM_LOG = "log"
    
    @classmethod
    def get_prefix(cls, category: FileCategory) -> str:
        """根据分类获取前缀"""
        prefix_map = {
            FileCategory.CONVERSATION_ATTACHMENT: cls.CONVERSATION_ATTACHMENT,
            FileCategory.VOICE_MESSAGE: cls.VOICE_MESSAGE,
            FileCategory.KNOWLEDGE_DOCUMENT: cls.KNOWLEDGE_DOCUMENT,
            FileCategory.KNOWLEDGE_EXTRACT: cls.KNOWLEDGE_EXTRACT,
            FileCategory.TRANSLATION_INPUT: cls.TRANSLATION_INPUT,
            FileCategory.TRANSLATION_OUTPUT: cls.TRANSLATION_OUTPUT,
            FileCategory.USER_AVATAR: cls.USER_AVATAR,
            FileCategory.USER_EXPORT: cls.USER_EXPORT,
            FileCategory.TEMP_FILE: cls.TEMP_FILE,
        }
        return prefix_map.get(category, "file")


class StoragePathManager:
    """
    存储路径管理器
    
    统一管理文件存储路径，实现：
    1. 用户隔离 - 每个用户独立文件夹
    2. 功能细分 - 按业务功能组织
    3. 时间分层 - 按年月组织避免单目录文件过多
    """
    
    def __init__(self, base_path: str = "uploads"):
        """
        初始化存储路径管理器
        
        Args:
            base_path: 基础存储路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_storage_path(
        self,
        user_id: int,
        category: FileCategory,
        related_id: Optional[int] = None,
        create_dirs: bool = True
    ) -> Path:
        """
        获取存储路径
        
        Args:
            user_id: 用户ID
            category: 文件分类
            related_id: 关联ID（如对话ID、知识库ID）
            create_dirs: 是否自动创建目录
        
        Returns:
            Path: 存储路径对象
        """
        # 构建路径组件
        path_parts = [self.base_path, "users", str(user_id)]
        
        # 根据分类添加子目录
        category_paths = {
            FileCategory.CONVERSATION_ATTACHMENT: ["conversations", str(related_id), "attachments"],
            FileCategory.VOICE_MESSAGE: ["conversations", str(related_id), "voice"],
            FileCategory.KNOWLEDGE_DOCUMENT: ["knowledge", str(related_id), "documents"],
            FileCategory.KNOWLEDGE_EXTRACT: ["knowledge", str(related_id), "extracted"],
            FileCategory.TRANSLATION_INPUT: ["translations", "input"],
            FileCategory.TRANSLATION_OUTPUT: ["translations", "output"],
            FileCategory.USER_AVATAR: ["profile"],
            FileCategory.USER_EXPORT: ["exports"],
            FileCategory.TEMP_FILE: ["temp"],
        }
        
        if category in category_paths:
            path_parts.extend(category_paths[category])
        
        # 添加日期层级（除了特定目录）
        if category not in [FileCategory.USER_AVATAR]:
            now = datetime.now()
            path_parts.extend([now.strftime("%Y"), now.strftime("%m")])
        
        # 构建完整路径
        full_path = Path(*path_parts)
        
        # 创建目录
        if create_dirs:
            full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
    
    def get_user_base_path(self, user_id: int) -> Path:
        """
        获取用户基础路径
        
        Args:
            user_id: 用户ID
        
        Returns:
            Path: 用户基础路径
        """
        return self.base_path / "users" / str(user_id)
    
    def get_user_all_paths(self, user_id: int) -> Dict[str, Path]:
        """
        获取用户的所有存储路径
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict[str, Path]: 各分类路径字典
        """
        user_base = self.get_user_base_path(user_id)
        
        return {
            'base': user_base,
            'conversations': user_base / "conversations",
            'knowledge': user_base / "knowledge",
            'translations': user_base / "translations",
            'exports': user_base / "exports",
            'temp': user_base / "temp",
            'profile': user_base / "profile",
        }
    
    def calculate_user_storage(self, user_id: int) -> Dict[str, Any]:
        """
        计算用户存储使用情况
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict[str, Any]: 存储使用统计信息
        """
        user_paths = self.get_user_all_paths(user_id)
        
        result = {}
        total_size = 0
        total_files = 0
        
        for category, path in user_paths.items():
            if path.exists():
                size, files = self._calculate_dir_size(path)
                result[category] = {
                    'size': size,
                    'size_human': self._format_size(size),
                    'files': files
                }
                total_size += size
                total_files += files
        
        result['total'] = {
            'size': total_size,
            'size_human': self._format_size(total_size),
            'files': total_files
        }
        
        return result
    
    def _calculate_dir_size(self, path: Path) -> tuple:
        """
        计算目录大小和文件数
        
        Args:
            path: 目录路径
        
        Returns:
            tuple: (总大小, 文件数)
        """
        total_size = 0
        file_count = 0
        
        for entry in path.rglob('*'):
            if entry.is_file():
                total_size += entry.stat().st_size
                file_count += 1
        
        return total_size, file_count
    
    def _format_size(self, size_bytes: int) -> str:
        """
        格式化文件大小显示
        
        Args:
            size_bytes: 字节数
        
        Returns:
            str: 格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
    
    def cleanup_user_temp(self, user_id: int, max_age_hours: int = 24) -> int:
        """
        清理用户临时文件
        
        Args:
            user_id: 用户ID
            max_age_hours: 最大保留时间（小时）
        
        Returns:
            int: 清理的文件数量
        """
        temp_path = self.get_storage_path(
            user_id, 
            FileCategory.TEMP_FILE, 
            create_dirs=False
        )
        
        if not temp_path.exists():
            return 0
        
        import time
        
        cutoff_time = time.time() - (max_age_hours * 3600)
        deleted_count = 0
        
        for entry in temp_path.rglob('*'):
            if entry.is_file() and entry.stat().st_mtime < cutoff_time:
                try:
                    entry.unlink()
                    deleted_count += 1
                except Exception:
                    pass
        
        # 清理空目录
        self._cleanup_empty_dirs(temp_path)
        
        return deleted_count
    
    def _cleanup_empty_dirs(self, path: Path):
        """
        清理空目录
        
        Args:
            path: 起始路径
        """
        try:
            for entry in sorted(path.rglob('*'), key=lambda x: len(x.parts), reverse=True):
                if entry.is_dir() and not any(entry.iterdir()):
                    try:
                        entry.rmdir()
                    except Exception:
                        pass
        except Exception:
            pass
    
    def delete_user_all_files(self, user_id: int) -> bool:
        """
        删除用户所有文件（用户注销时使用）
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 是否成功删除
        """
        user_base = self.get_user_base_path(user_id)
        
        if user_base.exists():
            try:
                shutil.rmtree(user_base)
                return True
            except Exception:
                return False
        
        return True
    
    def generate_filename(
        self, 
        original_name: str, 
        category: FileCategory
    ) -> str:
        """
        生成标准文件名
        
        格式: [prefix]_[uuid]_[timestamp]_[safe_original_name]
        示例: conv_a1b2c3_20250225_143052_report.pdf
        
        Args:
            original_name: 原始文件名
            category: 文件分类
        
        Returns:
            str: 生成的文件名
        """
        import uuid
        import re
        
        # 获取前缀
        prefix = FilePrefix.get_prefix(category)
        
        # 生成唯一ID（前8位）
        unique_id = str(uuid.uuid4())[:8]
        
        # 时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 清理原始文件名
        safe_name = self._sanitize_filename(original_name)
        
        # 组合文件名
        return f"{prefix}_{unique_id}_{timestamp}_{safe_name}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除危险字符
        
        Args:
            filename: 原始文件名
        
        Returns:
            str: 清理后的文件名
        """
        import re
        
        # 分离文件名和扩展名
        name, ext = os.path.splitext(filename)
        
        # 移除危险字符
        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        
        # 限制长度（保留扩展名）
        max_name_length = 50
        if len(name) > max_name_length:
            name = name[:max_name_length]
        
        # 去除首尾空白
        name = name.strip()
        
        return f"{name}{ext}"
    
    def parse_filename(self, filename: str) -> Dict[str, str]:
        """
        解析文件名获取元数据
        
        示例: conv_a1b2c3_20250225_143052_report.pdf
        返回: {
            'prefix': 'conv',
            'uuid': 'a1b2c3',
            'timestamp': '20250225_143052',
            'original_name': 'report.pdf'
        }
        
        Args:
            filename: 文件名
        
        Returns:
            Dict[str, str]: 解析结果
        """
        parts = filename.split('_')
        
        result = {
            'prefix': parts[0] if len(parts) > 0 else '',
            'uuid': parts[1] if len(parts) > 1 else '',
            'timestamp': f"{parts[2]}_{parts[3]}" if len(parts) > 3 else '',
            'original_name': '_'.join(parts[4:]) if len(parts) > 4 else filename
        }
        
        return result


# 全局实例
storage_path_manager = StoragePathManager()
