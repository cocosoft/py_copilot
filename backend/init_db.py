"""数据库初始化脚本"""
from app.core.database import SessionLocal, engine
from app.core.database import Base
from app.models.supplier_db import SupplierDB, ModelDB, ModelParameter
from app.models.model_category import ModelCategory
from app.models.model_capability import ModelCapability

# 创建数据库表
print("开始创建数据库表...")
# 先删除所有表，再重新创建
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("数据库表创建完成！")

# 初始化一些示例数据
db = SessionLocal()
try:
    print("添加示例供应商数据...")
    # 添加一些示例供应商
    suppliers_data = [
        {
            "name": "openai",
            "display_name": "OpenAI",
            "description": "提供GPT系列模型的AI公司",
            "website": "https://openai.com",
            "api_endpoint": "https://api.openai.com/v1",
            "is_active": True
        },
        {
            "name": "baidu",
            "display_name": "百度文心一言",
            "description": "百度AI开发的大语言模型",
            "website": "https://wenxin.baidu.com",
            "api_endpoint": "https://aip.baidubce.com",
            "is_active": True
        }
    ]
    
    for supplier_data in suppliers_data:
        supplier = SupplierDB(
            **supplier_data
        )
        db.add(supplier)
    
    db.commit()
    print("示例数据添加完成！")
except Exception as e:
    print(f"初始化数据时出错: {e}")
    db.rollback()
finally:
    db.close()