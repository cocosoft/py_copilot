"""
文件存储服务

集成存储路径管理器，提供统一的文件存储、读取、删除功能
"""

import uuid
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import BinaryIO, Dict, Any, List, Optional, Union
import aiofiles

from app.services.storage_path_manager import (
    storage_path_manager,
    FileCategory,
    FilePrefix
)


class FileStorageService:
    """
    文件存储服务
    
    提供统一的文件操作接口：
    1. 保存文件 - 自动处理路径和命名
    2. 读取文件 - 支持同步和异步读取
    3. 删除文件 - 自动清理空目录
    4. 复制/移动文件 - 支持文件迁移
    5. 存储统计 - 获取用户存储使用情况
    """
    
    def __init__(self):
        """初始化文件存储服务"""
        self.path_manager = storage_path_manager
    
    async def save_file(
        self,
        file_data: Union[BinaryIO, bytes],
        filename: str,
        user_id: int,
        category: FileCategory,
        related_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        generate_unique_name: bool = True
    ) -> Dict[str, Any]:
        """
        保存文件

        Args:
            file_data: 文件数据（文件对象或字节）
            filename: 原始文件名
            user_id: 用户ID
            category: 文件分类
            related_id: 关联ID（如对话ID、知识库ID）
            workspace_id: 工作空间ID（用于工作空间隔离）
            metadata: 额外元数据
            generate_unique_name: 是否生成唯一文件名

        Returns:
            Dict[str, Any]: 文件信息字典

        Raises:
            ValueError: 参数无效
            IOError: 文件保存失败
        """
        # 验证参数
        if not filename:
            raise ValueError("文件名不能为空")
        if user_id <= 0:
            raise ValueError("用户ID无效")

        # 读取文件内容
        if hasattr(file_data, 'read'):
            content = file_data.read()
            if hasattr(file_data, 'seek'):
                file_data.seek(0)
        else:
            content = file_data

        if isinstance(content, str):
            content = content.encode('utf-8')

        file_size = len(content)

        # 生成文件名
        if generate_unique_name:
            stored_name = self.path_manager.generate_filename(filename, category)
        else:
            stored_name = self.path_manager._sanitize_filename(filename)

        # 获取存储路径（支持工作空间隔离）
        storage_dir = self.path_manager.get_storage_path(
            user_id, category, related_id, workspace_id
        )
        file_path = storage_dir / stored_name
        
        # 检查文件是否已存在，如果存在则添加序号
        counter = 1
        original_stored_name = stored_name
        while file_path.exists():
            name_part, ext_part = original_stored_name.rsplit('.', 1) if '.' in original_stored_name else (original_stored_name, '')
            stored_name = f"{name_part}_{counter}.{ext_part}" if ext_part else f"{name_part}_{counter}"
            file_path = storage_dir / stored_name
            counter += 1
        
        # 保存文件
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
        except Exception as e:
            raise IOError(f"文件保存失败: {str(e)}")
        
        # 计算校验和
        checksum = hashlib.md5(content).hexdigest()
        
        # 获取文件扩展名
        extension = Path(filename).suffix.lower()
        
        # 构建文件信息
        file_info = {
            'file_id': str(uuid.uuid4()),
            'original_name': filename,
            'stored_name': stored_name,
            'file_path': str(file_path),
            'relative_path': str(file_path.relative_to(self.path_manager.base_path)),
            'file_size': file_size,
            'size_human': self._format_size(file_size),
            'checksum': checksum,
            'extension': extension,
            'user_id': user_id,
            'workspace_id': workspace_id,
            'category': category.value,
            'related_id': related_id,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat()
        }

        return file_info
    
    async def read_file(self, file_path: Union[str, Path]) -> bytes:
        """
        异步读取文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            bytes: 文件内容
        
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取失败
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
        except Exception as e:
            raise IOError(f"文件读取失败: {str(e)}")
    
    def read_file_sync(self, file_path: Union[str, Path]) -> bytes:
        """
        同步读取文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            bytes: 文件内容
        
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取失败
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            return path.read_bytes()
        except Exception as e:
            raise IOError(f"文件读取失败: {str(e)}")
    
    async def delete_file(self, file_path: Union[str, Path]) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            bool: 是否成功删除
        """
        path = Path(file_path)
        if not path.exists():
            return False
        
        try:
            path.unlink()
            # 尝试清理空目录
            self._cleanup_empty_dirs(path.parent)
            return True
        except Exception:
            return False
    
    async def copy_file(
        self,
        source_path: Union[str, Path],
        target_user_id: int,
        target_category: FileCategory,
        target_related_id: Optional[int] = None,
        target_workspace_id: Optional[int] = None,
        new_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        复制文件到新位置

        Args:
            source_path: 源文件路径
            target_user_id: 目标用户ID
            target_category: 目标分类
            target_related_id: 目标关联ID
            target_workspace_id: 目标工作空间ID
            new_filename: 新文件名（可选）

        Returns:
            Dict[str, Any]: 新文件信息
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在: {source_path}")

        # 读取源文件
        content = source.read_bytes()

        # 确定文件名
        filename = new_filename or source.name

        # 保存到新位置
        return await self.save_file(
            file_data=content,
            filename=filename,
            user_id=target_user_id,
            category=target_category,
            related_id=target_related_id,
            workspace_id=target_workspace_id
        )
    
    async def move_file(
        self,
        source_path: Union[str, Path],
        target_user_id: int,
        target_category: FileCategory,
        target_related_id: Optional[int] = None,
        target_workspace_id: Optional[int] = None,
        new_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        移动文件到新位置

        Args:
            source_path: 源文件路径
            target_user_id: 目标用户ID
            target_category: 目标分类
            target_related_id: 目标关联ID
            target_workspace_id: 目标工作空间ID
            new_filename: 新文件名（可选）

        Returns:
            Dict[str, Any]: 新文件信息
        """
        # 先复制
        file_info = await self.copy_file(
            source_path=source_path,
            target_user_id=target_user_id,
            target_category=target_category,
            target_related_id=target_related_id,
            target_workspace_id=target_workspace_id,
            new_filename=new_filename
        )

        # 再删除源文件
        await self.delete_file(source_path)

        return file_info
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
        
        Returns:
            bool: 是否存在
        """
        return Path(file_path).exists()
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            Dict[str, Any]: 文件信息
        
        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        stat = path.stat()
        
        return {
            'name': path.name,
            'path': str(path),
            'size': stat.st_size,
            'size_human': self._format_size(stat.st_size),
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': path.suffix.lower()
        }
    
    def get_user_storage_info(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户存储信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict[str, Any]: 存储使用统计
        """
        return self.path_manager.calculate_user_storage(user_id)
    
    def cleanup_user_temp_files(self, user_id: int, max_age_hours: int = 24) -> int:
        """
        清理用户临时文件
        
        Args:
            user_id: 用户ID
            max_age_hours: 最大保留时间（小时）
        
        Returns:
            int: 清理的文件数量
        """
        return self.path_manager.cleanup_user_temp(user_id, max_age_hours)
    
    def validate_file(
        self,
        file_data: Union[BinaryIO, bytes],
        max_size: Optional[int] = None,
        allowed_extensions: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        验证文件
        
        Args:
            file_data: 文件数据
            max_size: 最大文件大小（字节）
            allowed_extensions: 允许的扩展名列表
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            'valid': True,
            'errors': []
        }
        
        # 读取内容
        if hasattr(file_data, 'read'):
            content = file_data.read()
            if hasattr(file_data, 'seek'):
                file_data.seek(0)
        else:
            content = file_data
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        file_size = len(content)
        
        # 验证大小
        if max_size and file_size > max_size:
            result['valid'] = False
            result['errors'].append(f"文件大小超过限制: {self._format_size(file_size)} > {self._format_size(max_size)}")
        
        # 验证扩展名（如果提供了文件名）
        if hasattr(file_data, 'filename') and allowed_extensions:
            filename = file_data.filename
            extension = Path(filename).suffix.lower()
            if extension not in allowed_extensions:
                result['valid'] = False
                result['errors'].append(f"不支持的文件类型: {extension}")
        
        result['size'] = file_size
        result['size_human'] = self._format_size(file_size)
        
        return result
    
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
    
    def _cleanup_empty_dirs(self, path: Path):
        """
        清理空目录
        
        Args:
            path: 起始路径
        """
        try:
            for parent in path.parents:
                if parent == self.path_manager.base_path:
                    break
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
        except Exception:
            pass
    
    async def save_temp_file(
        self,
        file_data: Union[BinaryIO, bytes],
        filename: str,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        保存临时文件
        
        Args:
            file_data: 文件数据
            filename: 文件名
            user_id: 用户ID
            metadata: 元数据
        
        Returns:
            Dict[str, Any]: 文件信息
        """
        return await self.save_file(
            file_data=file_data,
            filename=filename,
            user_id=user_id,
            category=FileCategory.TEMP_FILE,
            metadata=metadata
        )
    
    async def move_temp_to_permanent(
        self,
        temp_file_path: Union[str, Path],
        target_category: FileCategory,
        target_related_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        将临时文件移动到永久存储
        
        Args:
            temp_file_path: 临时文件路径
            target_category: 目标分类
            target_related_id: 目标关联ID
        
        Returns:
            Dict[str, Any]: 新文件信息
        """
        path = Path(temp_file_path)
        if not path.exists():
            raise FileNotFoundError(f"临时文件不存在: {temp_file_path}")
        
        # 从路径解析用户信息
        parts = path.parts
        try:
            user_id_index = parts.index('users') + 1
            user_id = int(parts[user_id_index])
        except (ValueError, IndexError):
            raise ValueError("无法从路径解析用户ID")
        
        # 移动文件
        return await self.move_file(
            source_path=temp_file_path,
            target_user_id=user_id,
            target_category=target_category,
            target_related_id=target_related_id
        )
    
    # ==================== 工具兼容接口 ====================
    
    async def read_text_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        读取文本文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            str: 文件内容
        """
        content = await self.read_file(file_path)
        return content.decode(encoding)
    
    async def write_text_file(
        self,
        content: str,
        filename: str,
        user_id: int,
        category: FileCategory = FileCategory.CONVERSATION_ATTACHMENT,
        encoding: str = 'utf-8'
    ) -> Dict[str, Any]:
        """
        写入文本文件
        
        Args:
            content: 文本内容
            filename: 文件名
            user_id: 用户ID
            category: 文件分类
            encoding: 文件编码
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        return await self.save_file(
            file_data=content.encode(encoding),
            filename=filename,
            user_id=user_id,
            category=category
        )
    
    def list_files(
        self,
        user_id: int,
        category: Optional[FileCategory] = None,
        pattern: str = "*"
    ) -> List[Dict[str, Any]]:
        """
        列出用户文件
        
        Args:
            user_id: 用户ID
            category: 文件分类过滤
            pattern: 文件名匹配模式
            
        Returns:
            List[Dict[str, Any]]: 文件信息列表
        """
        if category:
            storage_dir = self.path_manager.get_storage_path(user_id, category)
        else:
            storage_dir = self.path_manager.base_path / "users" / str(user_id)
        
        files = []
        if storage_dir.exists():
            for file_path in storage_dir.rglob(pattern):
                if file_path.is_file():
                    try:
                        files.append(self.get_file_info(file_path))
                    except Exception:
                        pass
        
        return files
    
    def get_file_size(self, file_path: Union[str, Path]) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 文件大小（字节）
        """
        path = Path(file_path)
        if not path.exists():
            return 0
        return path.stat().st_size


# 全局实例
file_storage_service = FileStorageService()
