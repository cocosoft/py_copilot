"""应用配置文件 - 统一管理数据库和其他配置"""

# 数据库配置
# 使用单一数据库文件存储所有数据
SQLALCHEMY_DATABASE_URL = "sqlite:///./py_copilot.db"

# 数据库连接参数
DATABASE_CONNECT_ARGS = {
    "check_same_thread": False  # SQLite需要这个参数
}

# API配置
API_VERSION = "0.1.0"
API_TITLE = "Py Copilot API"
API_DESCRIPTION = "统一管理供应商、模型、分类和能力的API系统"

# CORS配置
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# 日志配置
LOG_LEVEL = "debug"
