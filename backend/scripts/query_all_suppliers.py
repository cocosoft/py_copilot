#!/usr/bin/env python3
"""
查询所有供应商信息
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.supplier_db import SupplierDB, ModelDB


def query_all_suppliers():
    """查询所有供应商"""
    
    db = SessionLocal()
    
    try:
        print("查询所有供应商信息...\n")
        
        # 查询所有供应商
        suppliers = db.query(SupplierDB).all()
        
        print(f"找到 {len(suppliers)} 个供应商:\n")
        
        for supplier in suppliers:
            print(f"供应商: {supplier.name}")
            print(f"  - ID: {supplier.id}")
            print(f"  - 显示名称: {supplier.display_name}")
            print(f"  - API端点: {supplier.api_endpoint}")
            print(f"  - 类别: {supplier.category}")
            print(f"  - 状态: {'启用' if supplier.is_active else '禁用'}")
            
            # 查询该供应商下的模型
            models = db.query(ModelDB).filter(ModelDB.supplier_id == supplier.id).all()
            print(f"  - 模型数量: {len(models)}")
            
            for model in models:
                print(f"    - {model.model_id} ({model.model_name})")
            print()
        
        # 查找本地或ollama相关的供应商
        local_suppliers = [s for s in suppliers if 'local' in s.category.lower() or 'ollama' in s.name.lower()]
        
        if local_suppliers:
            print(f"\n找到 {len(local_suppliers)} 个本地/OLLAMA相关供应商:")
            for s in local_suppliers:
                print(f"  - {s.name} (ID: {s.id})")
        
        return suppliers
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        db.close()


if __name__ == "__main__":
    suppliers = query_all_suppliers()
    sys.exit(0 if suppliers else 1)
