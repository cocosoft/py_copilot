"""Py Copilot 后端服务主入口文件"""
import uvicorn
import os

# 从app.api.main导入配置好的FastAPI应用实例，避免导入config等可能触发langsmith的模块
from app.api.main import app

if __name__ == "__main__":
    """启动FastAPI应用服务器"""
    # 硬编码配置，避免读取配置文件
    LOG_LEVEL = "INFO"
    uvicorn.run(
        "main:app",  # 使用当前文件中的app实例
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level=LOG_LEVEL.lower()
    )