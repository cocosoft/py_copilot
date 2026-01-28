"""
结构化日志记录模块

实现基于JSON的结构化日志记录，支持日志级别、上下文信息、请求追踪等功能。
"""
import json
import logging
import logging.handlers
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogContext:
    """日志上下文信息"""
    
    def __init__(self):
        """初始化日志上下文"""
        self._context = {}
        
    def set(self, key: str, value: Any):
        """设置上下文值
        
        Args:
            key: 键名
            value: 值
        """
        self._context[key] = value
        
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文值
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            上下文值
        """
        return self._context.get(key, default)
        
    def remove(self, key: str):
        """移除上下文值
        
        Args:
            key: 键名
        """
        if key in self._context:
            del self._context[key]
            
    def clear(self):
        """清空上下文"""
        self._context.clear()
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            上下文字典
        """
        return self._context.copy()


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def __init__(self, include_context: bool = True):
        """初始化JSON格式化器
        
        Args:
            include_context: 是否包含上下文信息
        """
        super().__init__()
        self.include_context = include_context
        
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON
        
        Args:
            record: 日志记录
            
        Returns:
            JSON格式的日志字符串
        """
        # 基础日志信息
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
            "thread_name": record.threadName
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # 添加上下文信息
        if hasattr(record, 'context') and self.include_context:
            log_data["context"] = record.context
            
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
            
        return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        """初始化结构化日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level.value)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level.value)
            console_formatter = JSONFormatter()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
        self.context = LogContext()
        
    def _log_with_context(self, level: LogLevel, message: str, 
                         extra_fields: Optional[Dict[str, Any]] = None,
                         exc_info: Optional[Exception] = None):
        """带上下文的日志记录
        
        Args:
            level: 日志级别
            message: 日志消息
            extra_fields: 额外字段
            exc_info: 异常信息
        """
        # 创建日志记录
        log_record = self.logger.makeRecord(
            self.logger.name,
            level.value,
            "", 0,  # 跳过路径名和行号
            message,
            (),
            exc_info
        )
        
        # 添加上下文信息
        if self.context._context:
            log_record.context = self.context.to_dict()
            
        # 添加额外字段
        if extra_fields:
            log_record.extra_fields = extra_fields
            
        # 处理日志记录
        self.logger.handle(log_record)
        
    def debug(self, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """记录调试级别日志
        
        Args:
            message: 日志消息
            extra_fields: 额外字段
        """
        self._log_with_context(LogLevel.DEBUG, message, extra_fields)
        
    def info(self, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """记录信息级别日志
        
        Args:
            message: 日志消息
            extra_fields: 额外字段
        """
        self._log_with_context(LogLevel.INFO, message, extra_fields)
        
    def warning(self, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """记录警告级别日志
        
        Args:
            message: 日志消息
            extra_fields: 额外字段
        """
        self._log_with_context(LogLevel.WARNING, message, extra_fields)
        
    def error(self, message: str, extra_fields: Optional[Dict[str, Any]] = None,
              exc_info: Optional[Exception] = None):
        """记录错误级别日志
        
        Args:
            message: 日志消息
            extra_fields: 额外字段
            exc_info: 异常信息
        """
        self._log_with_context(LogLevel.ERROR, message, extra_fields, exc_info)
        
    def critical(self, message: str, extra_fields: Optional[Dict[str, Any]] = None,
                 exc_info: Optional[Exception] = None):
        """记录严重级别日志
        
        Args:
            message: 日志消息
            extra_fields: 额外字段
            exc_info: 异常信息
        """
        self._log_with_context(LogLevel.CRITICAL, message, extra_fields, exc_info)
        
    def set_level(self, level: LogLevel):
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        self.logger.setLevel(level.value)
        for handler in self.logger.handlers:
            handler.setLevel(level.value)


class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        """初始化日志管理器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self._loggers = {}
        self._configure_root_logger()
        
    def _configure_root_logger(self):
        """配置根日志记录器"""
        # 移除默认处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # 设置级别
        root_logger.setLevel(logging.INFO)
        
    def get_logger(self, name: str, level: LogLevel = LogLevel.INFO) -> StructuredLogger:
        """获取或创建结构化日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
            
        Returns:
            结构化日志记录器
        """
        if name not in self._loggers:
            self._loggers[name] = StructuredLogger(name, level)
            
        return self._loggers[name]
    
    def add_file_handler(self, logger_name: str, filename: str, 
                        level: LogLevel = LogLevel.INFO, 
                        max_bytes: int = 10 * 1024 * 1024,  # 10MB
                        backup_count: int = 5):
        """为日志记录器添加文件处理器
        
        Args:
            logger_name: 日志记录器名称
            filename: 文件名
            level: 日志级别
            max_bytes: 最大文件大小
            backup_count: 备份文件数量
        """
        if logger_name not in self._loggers:
            raise ValueError(f"日志记录器 {logger_name} 不存在")
            
        logger = self._loggers[logger_name]
        
        # 创建文件处理器
        file_path = self.log_dir / filename
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level.value)
        
        # 设置JSON格式化器
        formatter = JSONFormatter()
        file_handler.setFormatter(formatter)
        
        # 添加到日志记录器
        logger.logger.addHandler(file_handler)
        
    def add_console_handler(self, logger_name: str, level: LogLevel = LogLevel.INFO):
        """为日志记录器添加控制台处理器
        
        Args:
            logger_name: 日志记录器名称
            level: 日志级别
        """
        if logger_name not in self._loggers:
            raise ValueError(f"日志记录器 {logger_name} 不存在")
            
        logger = self._loggers[logger_name]
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level.value)
        
        # 设置JSON格式化器
        formatter = JSONFormatter()
        console_handler.setFormatter(formatter)
        
        # 添加到日志记录器
        logger.logger.addHandler(console_handler)


# 全局日志管理器实例
log_manager = LogManager()


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self, logger: StructuredLogger):
        """初始化请求日志记录器
        
        Args:
            logger: 结构化日志记录器
        """
        self.logger = logger
        self.request_id = None
        
    def set_request_id(self, request_id: str):
        """设置请求ID
        
        Args:
            request_id: 请求ID
        """
        self.request_id = request_id
        self.logger.context.set("request_id", request_id)
        
    def log_request_start(self, method: str, path: str, client_ip: str, 
                         user_agent: str = None):
        """记录请求开始
        
        Args:
            method: HTTP方法
            path: 请求路径
            client_ip: 客户端IP
            user_agent: 用户代理
        """
        extra_fields = {
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "event": "request_start"
        }
        
        self.logger.info(f"请求开始: {method} {path}", extra_fields)
        
    def log_request_end(self, method: str, path: str, status_code: int, 
                       response_time: float, response_size: int = None):
        """记录请求结束
        
        Args:
            method: HTTP方法
            path: 请求路径
            status_code: 状态码
            response_time: 响应时间（秒）
            response_size: 响应大小（字节）
        """
        extra_fields = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
            "response_size": response_size,
            "event": "request_end"
        }
        
        self.logger.info(
            f"请求完成: {method} {path} - {status_code} ({response_time:.3f}s)",
            extra_fields
        )
        
    def log_error(self, method: str, path: str, status_code: int, 
                  error_message: str, exc_info: Exception = None):
        """记录请求错误
        
        Args:
            method: HTTP方法
            path: 请求路径
            status_code: 状态码
            error_message: 错误消息
            exc_info: 异常信息
        """
        extra_fields = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "error_message": error_message,
            "event": "request_error"
        }
        
        self.logger.error(
            f"请求错误: {method} {path} - {status_code}: {error_message}",
            extra_fields,
            exc_info
        )


# 创建常用日志记录器
app_logger = log_manager.get_logger("app", LogLevel.INFO)
api_logger = log_manager.get_logger("api", LogLevel.INFO)
db_logger = log_manager.get_logger("database", LogLevel.INFO)
websocket_logger = log_manager.get_logger("websocket", LogLevel.INFO)
monitoring_logger = log_manager.get_logger("monitoring", LogLevel.INFO)


# 添加文件处理器
log_manager.add_file_handler("app", "app.log", LogLevel.INFO)
log_manager.add_file_handler("api", "api.log", LogLevel.INFO)
log_manager.add_file_handler("database", "database.log", LogLevel.INFO)
log_manager.add_file_handler("websocket", "websocket.log", LogLevel.INFO)
log_manager.add_file_handler("monitoring", "monitoring.log", LogLevel.INFO)