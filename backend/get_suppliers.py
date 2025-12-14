from app.core.database import SessionLocal
from app.models.supplier_db import SupplierDB

# 创建数据库会话
db = SessionLocal()

# 查询所有供应商
suppliers = db.query(SupplierDB).all()
for s in suppliers:
    print(f'ID: {s.id}, Name: {s.name}')

# 关闭数据库会话
db.close()
