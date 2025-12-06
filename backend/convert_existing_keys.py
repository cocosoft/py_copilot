#!/usr/bin/env python3
"""
将现有的明文API密钥转换为加密存储格式
"""
import sqlite3
import os
from app.models.supplier_db import SupplierDB
from app.core.database import SessionLocal
from app.core.encryption import encrypt_string

def convert_existing_api_keys():
    """将现有明文API密钥转换为加密格式"""
    db_path = os.path.join(os.path.dirname(__file__), 'py_copilot.db')
    
    print(f"🔍 正在连接数据库: {db_path}")
    
    try:
        # 直接连接数据库检查明文API密钥
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询所有包含API密钥的供应商
        cursor.execute("SELECT id, name, api_key FROM suppliers WHERE api_key IS NOT NULL")
        results = cursor.fetchall()
        
        print(f"\n📊 发现 {len(results)} 条包含API密钥的记录")
        
        # 检查哪些是明文
        plaintext_keys = []
        for row in results:
            supplier_id, name, api_key = row
            
            # 简单判断是否为明文（加密后的密钥通常以gAAAA开头）
            if not api_key.startswith('gAAAA'):
                plaintext_keys.append((supplier_id, name, api_key))
        
        print(f"\n⚠️  发现 {len(plaintext_keys)} 条明文API密钥记录需要转换")
        
        if plaintext_keys:
            print("\n📋 需要转换的供应商:")
            for supplier_id, name, api_key in plaintext_keys:
                print(f"  - {name} (ID: {supplier_id})")
            
            # 使用ORM转换
            db = SessionLocal()
            try:
                for supplier_id, name, api_key in plaintext_keys:
                    # 获取供应商对象
                    supplier = db.query(SupplierDB).filter(SupplierDB.id == supplier_id).first()
                    if supplier:
                        # 重新设置API密钥以触发加密
                        supplier.api_key = api_key
                        print(f"✅ {name} 的API密钥已转换为加密格式")
                
                # 提交更改
                db.commit()
                print(f"\n🎉 成功转换所有 {len(plaintext_keys)} 条API密钥")
                
            except Exception as e:
                print(f"❌ 转换过程中出错: {e}")
                db.rollback()
            finally:
                db.close()
        
        conn.close()
        
        # 再次验证加密状态
        print("\n🔍 验证转换后的加密状态")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, api_key FROM suppliers WHERE api_key IS NOT NULL")
        results = cursor.fetchall()
        
        print(f"\n📊 验证 {len(results)} 条API密钥的加密状态:")
        
        for row in results:
            supplier_id, name, api_key = row
            
            if api_key.startswith('gAAAA'):
                print(f"✅ {name}: 已加密")
                print(f"   存储值: {api_key[:30]}...")
            else:
                print(f"❌ {name}: 仍为明文")
                print(f"   存储值: {api_key}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("🎉 API密钥转换和验证完成")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 转换过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def final_verification():
    """最终验证所有功能正常工作"""
    print(f"\n🔍 最终功能验证")
    
    from datetime import datetime
    from app.models.supplier_db import SupplierDB
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # 1. 测试新供应商创建
        test_supplier = SupplierDB(
            name="验证供应商",
            display_name="验证供应商",
            api_endpoint="https://test-api.com",
            api_key_required=True,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        test_key = "sk-verify1234567890"
        test_supplier.api_key = test_key
        
        db.add(test_supplier)
        db.commit()
        db.refresh(test_supplier)
        
        # 2. 测试更新
        new_key = "sk-updated1234567890"
        test_supplier.api_key = new_key
        db.commit()
        db.refresh(test_supplier)
        
        # 3. 验证加密
        from app.core.encryption import decrypt_string
        if decrypt_string(test_supplier._api_key) == new_key:
            print("✅ 新供应商创建和更新功能正常")
            print(f"   API密钥已正确加密存储")
        else:
            print("❌ 新供应商加密功能异常")
        
        # 清理测试数据
        db.delete(test_supplier)
        db.commit()
        
    except Exception as e:
        print(f"❌ 最终验证失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    convert_existing_api_keys()
    final_verification()
