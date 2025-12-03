"""创建模型能力相关的数据库表"""
from app.api.dependencies import engine
from app.models.model_capability import Base

# 创建所有模型能力相关的表
Base.metadata.create_all(bind=engine)
print("模型能力相关表创建完成！")