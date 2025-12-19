"""增强日志配置模块"""
import logging
import os
import json
import time
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

from app.core.config import settings

# 确保日志目录存在
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record):
        """格式化日志记录"""
        # 基础日志信息
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "thread": record.threadName,
            "process": record.processName
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_fields') and record.extra_fields:
            log_data.update(record.extra_fields)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers = {}
    
    def start_timer(self, operation_name: str) -> str:
        """开始计时器"""
        timer_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.timers[timer_id] = {
            "operation": operation_name,
            "start_time": time.time(),
            "start_timestamp": datetime.now().isoformat()
        }
        return timer_id
    
    def stop_timer(self, timer_id: str, extra_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """停止计时器并记录性能数据"""
        if timer_id not in self.timers:
            self.logger.warning(f"计时器不存在: {timer_id}")
            return {}
        
        timer_data = self.timers[timer_id]
        end_time = time.time()
        duration = end_time - timer_data["start_time"]
        
        performance_data = {
            "operation": timer_data["operation"],
            "duration_ms": round(duration * 1000, 2),
            "start_time": timer_data["start_timestamp"],
            "end_time": datetime.now().isoformat()
        }
        
        if extra_fields:
            performance_data.update(extra_fields)
        
        # 记录性能日志
        self.logger.info(
            f"性能监控 - 操作: {timer_data['operation']}, 耗时: {performance_data['duration_ms']}ms",
            extra={"extra_fields": performance_data}
        )
        
        # 清理计时器
        del self.timers[timer_id]
        
        return performance_data

def log_execution_time(logger: logging.Logger):
    """记录函数执行时间的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            timer_id = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"函数执行完成 - {func.__name__}: {duration:.3f}s",
                    extra={
                        "extra_fields": {
                            "function": func.__name__,
                            "module": func.__module__,
                            "duration_s": round(duration, 3),
                            "status": "success"
                        }
                    }
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"函数执行失败 - {func.__name__}: {duration:.3f}s, 错误: {str(e)}",
                    extra={
                        "extra_fields": {
                            "function": func.__name__,
                            "module": func.__module__,
                            "duration_s": round(duration, 3),
                            "status": "failed",
                            "error": str(e)
                        }
                    }
                )
                raise
        
        return wrapper
    return decorator

def setup_logging():
    """
    设置增强的日志配置
    
    - 结构化日志输出
    - 性能监控支持
    - 多级别日志记录
    - 日志轮转和归档
    """
    # 获取root日志记录器
    root_logger = logging.getLogger()
    
    # 设置root日志级别
    root_logger.setLevel(logging.DEBUG)
    
    # 避免重复添加处理器
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # 结构化日志格式化器
    structured_formatter = StructuredFormatter()
    
    # 简单文本格式化器（用于控制台）
    text_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )
    
    # 文件日志处理器（结构化JSON格式）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(structured_formatter)
    root_logger.addHandler(file_handler)
    
    # 控制台日志处理器（文本格式）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(text_formatter)
    root_logger.addHandler(console_handler)
    
    # 设置特定模块的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return root_logger

# 创建全局日志记录器
logger = setup_logging()

# 创建性能日志记录器
performance_logger = PerformanceLogger(logger)

# 导出常用装饰器
log_execution = log_execution_time(logger)
