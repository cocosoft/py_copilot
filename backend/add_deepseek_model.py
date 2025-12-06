#!/usr/bin/env python3
"""
添加DeepSeek供应商和deepseek-chat模型到数据库
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.supplier_db import SupplierDB, ModelDB
from app.core.encryption import encryption_tool


def add_deepseek_to_db():
    """添加DeepSeek供应商和deepseek-chat模型到数据库"""
    # 创建数据库会话
    session = Session(bind=engine)
    
    try:
        # 检查DeepSeek供应商是否已存在
        deepseek_supplier = session.query(SupplierDB).filter(SupplierDB.name == "DeepSeek").first()
        
        if not deepseek_supplier:
            # 创建DeepSeek供应商
            deepseek_supplier = SupplierDB(
                name="DeepSeek",
                display_name="深度求索",
                description="深度求索（DeepSeek）提供的AI模型服务",
                category="chat",
                api_endpoint="https://api.deepseek.com/v1",
                api_key_required=True,
                is_active=True,
                logo="",
                website="https://www.deepseek.com/"
            )
            session.add(deepseek_supplier)
            session.commit()
            print("✅ DeepSeek供应商已添加到数据库")
        else:
            print("ℹ️ DeepSeek供应商已存在于数据库中")
        
        # 检查deepseek-chat模型是否已存在
        deepseek_chat_model = session.query(ModelDB).filter(ModelDB.name == "deepseek-chat").first()
        
        if not deepseek_chat_model:
            # 创建deepseek-chat模型
            deepseek_chat_model = ModelDB(
                name="deepseek-chat",
                display_name="DeepSeek Chat",
                description="DeepSeek的通用对话模型",
                model_type="chat",
                supplier_id=deepseek_supplier.id,
                max_tokens=32768,
                context_window=32768,
                is_active=True,
                is_default=False
            )
            session.add(deepseek_chat_model)
            session.commit()
            print("✅ deepseek-chat模型已添加到数据库")
        else:
            print("ℹ️ deepseek-chat模型已存在于数据库中")
        
        # 检查是否需要添加deepseek-coder模型
        deepseek_coder_model = session.query(ModelDB).filter(ModelDB.name == "deepseek-coder").first()
        
        if not deepseek_coder_model:
            # 创建deepseek-coder模型
            deepseek_coder_model = ModelDB(
                name="deepseek-coder",
                display_name="DeepSeek Coder",
                description="DeepSeek的代码生成模型",
                model_type="code",
                supplier_id=deepseek_supplier.id,
                max_tokens=32768,
                context_window=32768,
                is_active=True,
                is_default=False
            )
            session.add(deepseek_coder_model)
            session.commit()
            print("✅ deepseek-coder模型已添加到数据库")
        else:
            print("ℹ️ deepseek-coder模型已存在于数据库中")
            
    except Exception as e:
        print(f"❌ 添加DeepSeek模型到数据库时出错: {e}")
        session.rollback()
    finally:
        session.close()


def list_all_models():
    """列出数据库中所有模型"""
    # 创建数据库会话
    session = Session(bind=engine)
    
    try:
        # 获取所有模型及其供应商
        models = session.query(ModelDB).all()
        
        print(f"\n数据库中共有 {len(models)} 个模型:")
        for model in models:
            supplier = session.query(SupplierDB).filter(SupplierDB.id == model.supplier_id).first()
            supplier_name = supplier.name if supplier else "未知供应商"
            print(f"- {model.name} ({supplier_name}) - {model.model_type} - {'活跃' if model.is_active else '禁用'}")
            
    except Exception as e:
        print(f"❌ 列出模型时出错: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("正在添加DeepSeek模型到数据库...")
    add_deepseek_to_db()
    list_all_models()
    print("\n操作完成!")
