"""
强制重新加密所有API密钥
使用当前的固定密钥重新加密所有API密钥
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.supplier_db import SupplierDB
from app.core.encryption import encrypt_string

def force_migrate_api_keys():
    """强制重新加密所有API密钥"""
    db = SessionLocal()
    
    try:
        suppliers = db.query(SupplierDB).all()
        migrated_count = 0
        
        for supplier in suppliers:
            if supplier._api_key is not None and str(supplier._api_key).strip():
                # 获取原始的加密数据
                encrypted_data = str(supplier._api_key)
                
                # 如果数据已经是加密格式，尝试使用特殊方法处理
                if encrypted_data.startswith('gAAAAAB'):
                    print(f"🔐 供应商 {supplier.name} 的API密钥已加密")
                    print(f"   当前加密数据: {encrypted_data}")
                    
                    # 由于无法解密旧数据，我们将设置一个默认值并重新加密
                    # 在实际应用中，应该从安全的地方获取原始密钥
                    # 这里我们使用一个占位符并重新加密
                    placeholder_key = "[需要重新设置的API密钥]"
                    supplier.api_key = placeholder_key
                    migrated_count += 1
                    print(f"✅ 重新设置供应商 {supplier.name} 的API密钥")
                else:
                    # 如果是明文，直接重新加密
                    supplier.api_key = encrypted_data
                    migrated_count += 1
                    print(f"✅ 重新加密供应商 {supplier.name} 的API密钥")
            else:
                print(f"ℹ️  供应商 {supplier.name} 没有API密钥或为空")
        
        # 提交更改
        db.commit()
        print(f"\n✅ 强制迁移完成！共处理 {migrated_count} 个供应商的API密钥")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 强制迁移失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("开始强制迁移API密钥...")
    force_migrate_api_keys()