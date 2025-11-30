"""数据库初始化脚本"""
from app.core.database import SessionLocal, engine
from app.models.supplier_db import Base, SupplierDB, ModelDB

# 创建数据库表
print("开始创建数据库表...")
Base.metadata.create_all(bind=engine)
print("数据库表创建完成！")

# 初始化一些示例数据
db = SessionLocal()
try:
    # 检查是否已有供应商数据
    if db.query(SupplierDB).count() == 0:
        print("添加示例供应商数据...")
        # 添加一些示例供应商
        suppliers_data = [
            {
                "name": "OpenAI",
                "description": "提供GPT系列模型的AI公司",
                "category": "国外",
                "website": "https://openai.com",
                "api_endpoint": "https://api.openai.com/v1",
                "api_key_required": True,
                "is_active": True,
                "isDomestic": False
            },
            {
                "name": "百度文心一言",
                "description": "百度AI开发的大语言模型",
                "category": "国内",
                "website": "https://wenxin.baidu.com",
                "api_endpoint": "https://aip.baidubce.com",
                "api_key_required": True,
                "is_active": True,
                "isDomestic": True
            }
        ]
        
        for supplier_data in suppliers_data:
            supplier = SupplierDB(
                **{k: v for k, v in supplier_data.items() if k != 'isDomestic'},
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            db.add(supplier)
        
        db.commit()
        print("示例数据添加完成！")
    else:
        print("数据库中已有供应商数据，跳过初始化")
except Exception as e:
    print(f"初始化数据时出错: {e}")
    db.rollback()
finally:
    db.close()