"""日志配置模块"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

from app.core.config import settings

# 确保日志目录存在
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")


def setup_logging():
    """
    设置日志配置
    
    - 控制台日志：显示 INFO 及以上级别，彩色输出
    - 文件日志：显示 DEBUG 及以上级别，按大小分割，保留历史日志
    """
    # 获取root日志记录器
    root_logger = logging.getLogger()
    
    # 设置root日志级别
    root_logger.setLevel(logging.DEBUG)
    
    # 避免重复添加处理器
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )
    
    # 文件日志处理器
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # 添加编码设置，确保中文正确显示
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger


# 创建全局日志记录器
logger = setup_logging()
