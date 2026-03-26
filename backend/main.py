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
    log_level = "info"  # 生产环境使用info级别，减少日志开销
    
    uvicorn.run(
        app="app.api.main:app",
        host="0.0.0.0",
        port=8020,  # 使用新端口，避免端口冲突
        reload=False,  # 禁用reload模式以避免多进程问题
        log_level=log_level,
        workers=1,  # 使用单进程模式，确保代码修改生效
        backlog=2048,  # 增加连接队列大小
        limit_concurrency=1000,  # 限制并发连接数
        limit_max_requests=100000,  # 每个worker处理的最大请求数
        timeout_keep_alive=30,  # 保持连接的超时时间
        timeout_graceful_shutdown=120,  # 优雅关闭的超时时间
        # 性能优化
        access_log=True,  # 启用访问日志，便于调试
        use_colors=False,  # 禁用彩色日志
        forwarded_allow_ips="*"  # 允许所有代理IP
    )