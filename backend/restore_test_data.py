import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.supplier_db import SupplierDB
from app.core.encryption import encrypt_string

def restore_test_data():
    """恢复测试数据到原始状态"""
    db = SessionLocal()
    try:
        # 恢复硅基流动的API密钥
        supplier = db.query(SupplierDB).filter(SupplierDB.id == 2).first()
        if supplier:
            supplier.api_key = encrypt_string("test_db_api_key_456")
            supplier.updated_at = datetime.utcnow()
            db.commit()
            print("✓ 已恢复硅基流动的API密钥")
        else:
            print("✗ 未找到硅基流动供应商")
        
        print("\n🎉 测试数据已恢复完成！")
        
    except Exception as e:
        print(f"✗ 恢复数据时发生错误: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore_test_data()