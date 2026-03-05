"""Py Copilot 后端服务主入口文件"""
import os
import sys

# 首先导入环境变量配置（必须在任何其他导入之前）
from app.core.env_config import *

import uvicorn

# 首先导入并配置日志
from app.core.logging_config import logger

# 从app.api.main导入配置好的FastAPI应用实例，避免导入config等可能触发langsmith的模块
from app.api.main import app

if __name__ == "__main__":
    """启动FastAPI应用服务器"""
    # 从日志配置中获取日志级别
    log_level = "debug"  # 确保使用DEBUG级别记录详细日志
    
    uvicorn.run(
        app="app.api.main:app",
        host="0.0.0.0",
        port=8007,
        reload=False,  # 禁用reload模式以避免多进程问题
        log_level=log_level,
        workers=1  # 明确使用单进程模式
    )