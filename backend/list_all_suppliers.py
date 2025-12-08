#!/usr/bin/env python3
"""
查看所有供应商的name和display_name
"""

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.supplier_db import SupplierDB


def list_all_suppliers():
    """列出所有供应商的name和display_name"""
    print("获取所有供应商数据...")
    
    # 创建会话
    with Session(engine) as session:
        # 查询所有供应商
        suppliers = session.query(SupplierDB).all()
        
        print(f"共找到 {len(suppliers)} 个供应商：")
        print("name | display_name")
        print("-" * 50)
        
        for supplier in suppliers:
            print(f"{supplier.name} | {supplier.display_name}")


if __name__ == "__main__":
    list_all_suppliers()