#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版服务器启动脚本，直接使用uvicorn运行，从配置文件读取服务器参数
"""

import uvicorn
import sys
import logging
from app.core.config import settings as config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == "__main__":
    print(f"启动简化版服务器，运行在 {config.server_host}:{config.server_port}...")
    # 直接运行main.py中的应用，使用配置文件中的参数
    uvicorn.run(
        "main:app",
        host=config.server_host,
        port=config.server_port,
        reload=config.server_reload,
        workers=config.server_workers
    )
