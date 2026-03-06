#!/usr/bin/env python3
"""
查找DeepSeek R1模型
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.supplier_db import SupplierDB, ModelDB


def find_deepseek_r1():
    """查找DeepSeek R1模型"""
    
    db = SessionLocal()
    
    try:
        print("查找DeepSeek R1模型...\n")
        
        # 查询所有模型，筛选包含R1的
        all_models = db.query(ModelDB).all()
        
        r1_models = []
        for model in all_models:
            model_id = model.model_id.lower()
            model_name = model.model_name.lower() if model.model_name else ""
            
            # 检查是否包含r1
            if 'r1' in model_id or 'r1' in model_name:
                r1_models.append(model)
        
        print(f"找到 {len(r1_models)} 个R1相关模型:\n")
        
        for model in r1_models:
            supplier = db.query(SupplierDB).filter(SupplierDB.id == model.supplier_id).first()
            supplier_name = supplier.name if supplier else "未知"
            
            print(f"🎯 模型: {model.model_id}")
            print(f"  - 数据库ID: {model.id}")
            print(f"  - 模型名称: {model.model_name}")
            print(f"  - 描述: {model.description}")
            print(f"  - 供应商: {supplier_name}")
            print(f"  - 上下文窗口: {model.context_window}")
            print(f"  - 最大Token: {model.max_tokens}")
            print(f"  - 状态: {'启用' if model.is_active else '禁用'}")
            print()
        
        # 返回第一个R1模型
        return r1_models[0] if r1_models else None
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    model = find_deepseek_r1()
    sys.exit(0 if model else 1)
