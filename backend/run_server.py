#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版服务器启动脚本，直接使用uvicorn运行，不启用热重载
"""

import uvicorn
import sys

if __name__ == "__main__":
    print("启动简化版服务器，不启用热重载...")
    # 直接运行main.py中的应用，不启用热重载
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 关闭热重载
        workers=1
    )
