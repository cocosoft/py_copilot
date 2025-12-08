#!/usr/bin/env python3
"""
查看所有模型及其关联的供应商
"""

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.supplier_db import SupplierDB, ModelDB, ModelParameter


def list_all_models():
    """列出所有模型及其关联的供应商和参数"""
    print("获取所有模型数据...")
    
    # 创建会话
    with Session(engine) as session:
        # 查询所有模型，包含供应商信息
        models = session.query(ModelDB).join(SupplierDB).all()
        
        print(f"共找到 {len(models)} 个模型：")
        print("-" * 120)
        
        for model in models:
            print(f"模型ID: {model.id}")
            print(f"名称: {model.name}")
            print(f"显示名称: {model.display_name}")
            print(f"供应商: {model.supplier.display_name}")
            print(f"类型: {model.model_type}")
            print(f"上下文窗口: {model.context_window}")
            print(f"最大Token数: {model.max_tokens}")
            print(f"默认模型: {model.is_default}")
            print(f"状态: {'激活' if model.is_active else '禁用'}")
            
            # 获取模型参数
            params = session.query(ModelParameter).filter(ModelParameter.model_id == model.id).all()
            if params:
                print(f"参数: {', '.join([f'{p.parameter_name}={p.parameter_value}' for p in params])}")
            
            print("-" * 120)


if __name__ == "__main__":
    list_all_models()