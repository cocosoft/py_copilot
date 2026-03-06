#!/usr/bin/env python3
"""
查询Ollama供应商下的模型信息
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.supplier_db import SupplierDB, ModelDB


def query_ollama_models():
    """查询Ollama供应商下的所有模型"""
    
    db = SessionLocal()
    
    try:
        print("查询Ollama供应商模型信息...\n")
        
        # 1. 查找Ollama供应商
        ollama_supplier = db.query(SupplierDB).filter(SupplierDB.name == "ollama").first()
        
        if not ollama_supplier:
            print("❌ 未找到Ollama供应商")
            return None
        
        print(f"✓ 找到Ollama供应商:")
        print(f"  - ID: {ollama_supplier.id}")
        print(f"  - 名称: {ollama_supplier.name}")
        print(f"  - 显示名称: {ollama_supplier.display_name}")
        print(f"  - API端点: {ollama_supplier.api_endpoint}")
        print(f"  - 状态: {'启用' if ollama_supplier.is_active else '禁用'}")
        print()
        
        # 2. 查询该供应商下的所有模型
        models = db.query(ModelDB).filter(ModelDB.supplier_id == ollama_supplier.id).all()
        
        if not models:
            print("❌ Ollama供应商下没有配置任何模型")
            return None
        
        print(f"✓ 找到 {len(models)} 个模型:\n")
        
        # 3. 查找包含r1的模型
        r1_models = []
        
        for model in models:
            print(f"模型: {model.model_id}")
            print(f"  - ID: {model.id}")
            print(f"  - 名称: {model.model_name}")
            print(f"  - 描述: {model.description}")
            print(f"  - 上下文窗口: {model.context_window}")
            print(f"  - 最大Token: {model.max_tokens}")
            print(f"  - 默认模型: {'是' if model.is_default else '否'}")
            print(f"  - 状态: {'启用' if model.is_active else '禁用'}")
            print()
            
            # 检查是否包含r1
            if 'r1' in model.model_id.lower() or 'r1' in model.model_name.lower():
                r1_models.append(model)
        
        # 4. 显示R1模型信息
        if r1_models:
            print(f"✓ 找到 {len(r1_models)} 个R1相关模型:\n")
            for model in r1_models:
                print(f"🎯 R1模型: {model.model_id}")
                print(f"  - 数据库ID: {model.id}")
                print(f"  - 模型名称: {model.model_name}")
                print(f"  - 描述: {model.description}")
                print()
            return r1_models[0]
        else:
            print("❌ 未找到R1相关模型")
            return None
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    model = query_ollama_models()
    sys.exit(0 if model else 1)
