"""
日志轮转和归档模块

实现日志文件的自动轮转、压缩归档和过期清理功能。
"""
import os
import gzip
import shutil
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor


class LogRotationManager:
    """日志轮转管理器"""
    
    def __init__(self, log_dir: str = "logs", max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5, archive_after_days: int = 7,
                 cleanup_after_days: int = 30):
        """初始化日志轮转管理器
        
        Args:
            log_dir: 日志目录
            max_file_size: 最大文件大小（字节）
            backup_count: 备份文件数量
            archive_after_days: 归档天数
            cleanup_after_days: 清理天数
        """
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.archive_after_days = archive_after_days
        self.cleanup_after_days = cleanup_after_days
        
        # 确保日志目录存在
        self.log_dir.mkdir(exist_ok=True)
        
        # 线程池用于异步处理
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.running = False
        
        # 日志记录器
        self.logger = logging.getLogger("log_rotation")
        
    def start_rotation_service(self):
        """启动日志轮转服务"""
        if self.running:
            self.logger.warning("日志轮转服务已在运行")
            return
            
        self.running = True
        self.logger.info("启动日志轮转服务")
        
        # 启动轮转检查线程
        rotation_thread = threading.Thread(target=self._rotation_check_loop, daemon=True)
        rotation_thread.start()
        
        # 启动归档检查线程
        archive_thread = threading.Thread(target=self._archive_check_loop, daemon=True)
        archive_thread.start()
        
        # 启动清理检查线程
        cleanup_thread = threading.Thread(target=self._cleanup_check_loop, daemon=True)
        cleanup_thread.start()
        
    def stop_rotation_service(self):
        """停止日志轮转服务"""
        self.running = False
        self.logger.info("停止日志轮转服务")
        self.executor.shutdown(wait=True)
        
    def _rotation_check_loop(self):
        """轮转检查循环"""
        while self.running:
            try:
                self.check_and_rotate_logs()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                self.logger.error(f"轮转检查失败: {e}")
                time.sleep(300)  # 出错后等待5分钟
                
    def _archive_check_loop(self):
        """归档检查循环"""
        while self.running:
            try:
                self.check_and_archive_logs()
                time.sleep(3600)  # 每小时检查一次
            except Exception as e:
                self.logger.error(f"归档检查失败: {e}")
                time.sleep(3600)  # 出错后等待1小时
                
    def _cleanup_check_loop(self):
        """清理检查循环"""
        while self.running:
            try:
                self.check_and_cleanup_logs()
                time.sleep(86400)  # 每天检查一次
            except Exception as e:
                self.logger.error(f"清理检查失败: {e}")
                time.sleep(86400)  # 出错后等待1天
                
    def check_and_rotate_logs(self):
        """检查并轮转日志文件"""
        try:
            log_files = list(self.log_dir.glob("*.log"))
            
            for log_file in log_files:
                if log_file.stat().st_size > self.max_file_size:
                    self.rotate_log_file(log_file)
                    
        except Exception as e:
            self.logger.error(f"检查日志轮转失败: {e}")
            
    def rotate_log_file(self, log_file: Path):
        """轮转日志文件
        
        Args:
            log_file: 日志文件路径
        """
        try:
            # 检查备份文件数量
            backup_files = list(log_file.parent.glob(f"{log_file.stem}.*{log_file.suffix}"))
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            # 删除超过备份数量的文件
            if len(backup_files) >= self.backup_count:
                for old_file in backup_files[:len(backup_files) - self.backup_count + 1]:
                    old_file.unlink()
                    self.logger.info(f"删除旧备份文件: {old_file}")
                    
            # 重命名当前日志文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = log_file.with_name(f"{log_file.stem}.{timestamp}{log_file.suffix}")
            
            log_file.rename(backup_file)
            self.logger.info(f"轮转日志文件: {log_file} -> {backup_file}")
            
            # 创建新的日志文件
            log_file.touch()
            
        except Exception as e:
            self.logger.error(f"轮转日志文件失败 {log_file}: {e}")
            
    def check_and_archive_logs(self):
        """检查并归档日志文件"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.archive_after_days)
            
            # 查找需要归档的文件
            files_to_archive = []
            for pattern in ["*.log.*", "*.log"]:
                for log_file in self.log_dir.glob(pattern):
                    if log_file.is_file() and log_file.stat().st_mtime < cutoff_time.timestamp():
                        files_to_archive.append(log_file)
                        
            # 异步归档文件
            if files_to_archive:
                self.executor.submit(self._archive_files, files_to_archive)
                
        except Exception as e:
            self.logger.error(f"检查日志归档失败: {e}")
            
    def _archive_files(self, files: List[Path]):
        """归档文件
        
        Args:
            files: 文件列表
        """
        try:
            archive_dir = self.log_dir / "archived"
            archive_dir.mkdir(exist_ok=True)
            
            for file_path in files:
                self._archive_single_file(file_path, archive_dir)
                
            self.logger.info(f"归档完成: {len(files)} 个文件")
            
        except Exception as e:
            self.logger.error(f"归档文件失败: {e}")
            
    def _archive_single_file(self, file_path: Path, archive_dir: Path):
        """归档单个文件
        
        Args:
            file_path: 文件路径
            archive_dir: 归档目录
        """
        try:
            # 创建归档文件名
            timestamp = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y%m")
            archive_file = archive_dir / f"{file_path.stem}_{timestamp}.gz"
            
            # 压缩文件
            with open(file_path, 'rb') as f_in:
                with gzip.open(archive_file, 'ab') as f_out:  # 追加模式
                    shutil.copyfileobj(f_in, f_out)
                    
            # 删除原文件
            file_path.unlink()
            
            self.logger.debug(f"归档文件: {file_path} -> {archive_file}")
            
        except Exception as e:
            self.logger.error(f"归档文件失败 {file_path}: {e}")
            
    def check_and_cleanup_logs(self):
        """检查并清理过期日志"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.cleanup_after_days)
            
            # 查找需要清理的文件
            files_to_cleanup = []
            archive_dir = self.log_dir / "archived"
            
            if archive_dir.exists():
                for archive_file in archive_dir.glob("*.gz"):
                    if archive_file.stat().st_mtime < cutoff_time.timestamp():
                        files_to_cleanup.append(archive_file)
                        
            # 异步清理文件
            if files_to_cleanup:
                self.executor.submit(self._cleanup_files, files_to_cleanup)
                
        except Exception as e:
            self.logger.error(f"检查日志清理失败: {e}")
            
    def _cleanup_files(self, files: List[Path]):
        """清理文件
        
        Args:
            files: 文件列表
        """
        try:
            for file_path in files:
                file_path.unlink()
                self.logger.info(f"清理过期文件: {file_path}")
                
            self.logger.info(f"清理完成: {len(files)} 个文件")
            
        except Exception as e:
            self.logger.error(f"清理文件失败: {e}")
            
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息
        
        Returns:
            日志统计信息
        """
        try:
            stats = {
                "log_dir": str(self.log_dir),
                "total_size": 0,
                "file_count": 0,
                "active_logs": [],
                "archived_logs": [],
                "rotation_settings": {
                    "max_file_size": self.max_file_size,
                    "backup_count": self.backup_count,
                    "archive_after_days": self.archive_after_days,
                    "cleanup_after_days": self.cleanup_after_days
                }
            }
            
            # 统计活动日志文件
            for pattern in ["*.log", "*.log.*"]:
                for log_file in self.log_dir.glob(pattern):
                    if log_file.is_file():
                        file_stat = log_file.stat()
                        stats["total_size"] += file_stat.st_size
                        stats["file_count"] += 1
                        
                        stats["active_logs"].append({
                            "name": log_file.name,
                            "size": file_stat.st_size,
                            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            "is_archive_candidate": file_stat.st_mtime < 
                                (datetime.now() - timedelta(days=self.archive_after_days)).timestamp()
                        })
                        
            # 统计归档日志文件
            archive_dir = self.log_dir / "archived"
            if archive_dir.exists():
                for archive_file in archive_dir.glob("*.gz"):
                    if archive_file.is_file():
                        file_stat = archive_file.stat()
                        stats["total_size"] += file_stat.st_size
                        stats["file_count"] += 1
                        
                        stats["archived_logs"].append({
                            "name": archive_file.name,
                            "size": file_stat.st_size,
                            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            "is_cleanup_candidate": file_stat.st_mtime < 
                                (datetime.now() - timedelta(days=self.cleanup_after_days)).timestamp()
                        })
                        
            # 格式化文件大小
            stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取日志统计失败: {e}")
            return {}
            
    def manual_rotate(self, log_name: str) -> bool:
        """手动轮转指定日志
        
        Args:
            log_name: 日志名称
            
        Returns:
            是否成功
        """
        try:
            log_file = self.log_dir / f"{log_name}.log"
            if log_file.exists():
                self.rotate_log_file(log_file)
                self.logger.info(f"手动轮转日志: {log_name}")
                return True
            else:
                self.logger.warning(f"日志文件不存在: {log_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"手动轮转日志失败 {log_name}: {e}")
            return False
            
    def manual_archive(self) -> Dict[str, Any]:
        """手动归档日志
        
        Returns:
            归档结果
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=self.archive_after_days)
            files_to_archive = []
            
            for pattern in ["*.log.*", "*.log"]:
                for log_file in self.log_dir.glob(pattern):
                    if log_file.is_file() and log_file.stat().st_mtime < cutoff_time.timestamp():
                        files_to_archive.append(log_file)
                        
            result = {
                "files_found": len(files_to_archive),
                "files_archived": 0,
                "errors": []
            }
            
            for file_path in files_to_archive:
                try:
                    self._archive_single_file(file_path, self.log_dir / "archived")
                    result["files_archived"] += 1
                except Exception as e:
                    result["errors"].append({
                        "file": str(file_path),
                        "error": str(e)
                    })
                    
            return result
            
        except Exception as e:
            self.logger.error(f"手动归档日志失败: {e}")
            return {"error": str(e)}
            
    def manual_cleanup(self) -> Dict[str, Any]:
        """手动清理过期日志
        
        Returns:
            清理结果
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=self.cleanup_after_days)
            files_to_cleanup = []
            
            archive_dir = self.log_dir / "archived"
            if archive_dir.exists():
                for archive_file in archive_dir.glob("*.gz"):
                    if archive_file.stat().st_mtime < cutoff_time.timestamp():
                        files_to_cleanup.append(archive_file)
                        
            result = {
                "files_found": len(files_to_cleanup),
                "files_cleaned": 0,
                "errors": []
            }
            
            for file_path in files_to_cleanup:
                try:
                    file_path.unlink()
                    result["files_cleaned"] += 1
                except Exception as e:
                    result["errors"].append({
                        "file": str(file_path),
                        "error": str(e)
                    })
                    
            return result
            
        except Exception as e:
            self.logger.error(f"手动清理日志失败: {e}")
            return {"error": str(e)}


# 全局日志轮转管理器实例
log_rotation_manager = LogRotationManager()


class LogRotationConfig:
    """日志轮转配置类"""
    
    def __init__(self):
        """初始化日志轮转配置"""
        self.config = {
            "enabled": True,
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5,
            "archive_after_days": 7,
            "cleanup_after_days": 30,
            "log_dir": "logs"
        }
        
    def update_config(self, **kwargs):
        """更新配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                
    def get_config(self) -> Dict[str, Any]:
        """获取配置
        
        Returns:
            配置字典
        """
        return self.config.copy()


# 全局日志轮转配置实例
log_rotation_config = LogRotationConfig()


def initialize_log_rotation():
    """初始化日志轮转服务"""
    try:
        # 更新全局管理器配置
        config = log_rotation_config.get_config()
        
        global log_rotation_manager
        log_rotation_manager = LogRotationManager(
            log_dir=config["log_dir"],
            max_file_size=config["max_file_size"],
            backup_count=config["backup_count"],
            archive_after_days=config["archive_after_days"],
            cleanup_after_days=config["cleanup_after_days"]
        )
        
        if config["enabled"]:
            log_rotation_manager.start_rotation_service()
            
        logging.getLogger("log_rotation").info("日志轮转服务初始化完成")
        
    except Exception as e:
        logging.getLogger("log_rotation").error(f"初始化日志轮转服务失败: {e}")


def cleanup_log_rotation():
    """清理日志轮转服务"""
    try:
        log_rotation_manager.stop_rotation_service()
        logging.getLogger("log_rotation").info("日志轮转服务已清理")
    except Exception as e:
        logging.getLogger("log_rotation").error(f"清理日志轮转服务失败: {e}")