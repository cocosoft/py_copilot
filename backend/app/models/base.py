"""SQLAlchemy基础模型定义"""
from sqlalchemy.ext.declarative import declarative_base

# 创建基础模型类
Base = declarative_base()

# 注意：这里不导入具体模型类，避免循环导入
# 模型注册将在应用启动时通过其他方式完成