#!/usr/bin/env python3
"""
默认供应商和模型数据初始化脚本
此脚本用于初始化数据库中的默认供应商和模型数据
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.supplier_db import SupplierDB, ModelDB
from app.core.encryption import encrypt_string


def seed_default_suppliers_and_models(db: Session):
    """初始化默认供应商和模型数据"""
    
    print("开始初始化默认供应商和模型数据...")
    
    # 检查是否已有供应商数据
    existing_suppliers = db.query(SupplierDB).count()
    if existing_suppliers > 0:
        print(f"数据库中已有 {existing_suppliers} 个供应商，跳过初始化")
        return
    
    # 默认供应商数据
    default_suppliers = [
        {
            "name": "openai",
            "display_name": "OpenAI",
            "description": "OpenAI提供先进的AI模型，包括GPT系列模型",
            "api_endpoint": "https://api.openai.com/v1",
            "api_key_required": True,
            "category": "chat",
            "website": "https://openai.com",
            "api_docs": "https://platform.openai.com/docs",
            "api_key": None,  # 从环境变量获取
            "is_active": True
        },
        {
            "name": "deepseek",
            "display_name": "DeepSeek",
            "description": "深度求索提供的AI模型，支持多种语言和任务",
            "api_endpoint": "https://api.deepseek.com/v1",
            "api_key_required": True,
            "category": "chat",
            "website": "https://www.deepseek.com",
            "api_docs": "https://platform.deepseek.com/api-docs",
            "api_key": None,  # 从环境变量获取
            "is_active": True
        },
        {
            "name": "anthropic",
            "display_name": "Anthropic",
            "description": "Anthropic提供的Claude系列模型",
            "api_endpoint": "https://api.anthropic.com",
            "api_key_required": True,
            "category": "chat",
            "website": "https://www.anthropic.com",
            "api_docs": "https://docs.anthropic.com",
            "api_key": None,  # 从环境变量获取
            "is_active": True
        },
        {
            "name": "ollama",
            "display_name": "Ollama",
            "description": "本地部署的AI模型服务",
            "api_endpoint": "http://localhost:11434/v1",
            "api_key_required": False,
            "category": "local",
            "website": "https://ollama.ai",
            "api_docs": "https://github.com/ollama/ollama",
            "api_key": None,
            "is_active": True
        }
    ]
    
    # 插入供应商数据
    supplier_ids = {}
    for supplier_data in default_suppliers:
        try:
            # 创建供应商对象
            supplier = SupplierDB(
                name=supplier_data["name"],
                display_name=supplier_data["display_name"],
                description=supplier_data["description"],
                api_endpoint=supplier_data["api_endpoint"],
                api_key_required=supplier_data["api_key_required"],
                category=supplier_data["category"],
                website=supplier_data["website"],
                api_docs=supplier_data["api_docs"],
                is_active=supplier_data["is_active"]
            )
            
            # 如果有API密钥，加密存储
            if supplier_data["api_key"]:
                supplier._api_key = encrypt_string(supplier_data["api_key"])
            
            db.add(supplier)
            db.commit()
            db.refresh(supplier)
            
            supplier_ids[supplier_data["name"]] = supplier.id
            print(f"✓ 创建供应商: {supplier.display_name} (ID: {supplier.id})")
            
        except Exception as e:
            db.rollback()
            print(f"✗ 创建供应商 {supplier_data['name']} 失败: {e}")
    
    # 默认模型数据
    default_models = [
        # OpenAI 模型
        {
            "model_id": "gpt-3.5-turbo",
            "model_name": "GPT-3.5 Turbo",
            "description": "OpenAI的GPT-3.5 Turbo模型，适用于一般对话任务",
            "supplier_name": "openai",
            "context_window": 4096,
            "max_tokens": 2000,
            "is_default": True,
            "is_active": True
        },
        {
            "model_id": "gpt-4",
            "model_name": "GPT-4",
            "description": "OpenAI的GPT-4模型，更强大的推理能力",
            "supplier_name": "openai",
            "context_window": 8192,
            "max_tokens": 4000,
            "is_default": False,
            "is_active": True
        },
        
        # DeepSeek 模型
        {
            "model_id": "deepseek-chat",
            "model_name": "DeepSeek Chat",
            "description": "深度求索的对话模型",
            "supplier_name": "deepseek",
            "context_window": 32000,
            "max_tokens": 8000,
            "is_default": True,
            "is_active": True
        },
        {
            "model_id": "deepseek-coder",
            "model_name": "DeepSeek Coder",
            "description": "深度求索的代码生成模型",
            "supplier_name": "deepseek",
            "context_window": 16000,
            "max_tokens": 4000,
            "is_default": False,
            "is_active": True
        },
        
        # Anthropic 模型
        {
            "model_id": "claude-3-sonnet-20240229",
            "model_name": "Claude 3 Sonnet",
            "description": "Anthropic的Claude 3 Sonnet模型",
            "supplier_name": "anthropic",
            "context_window": 200000,
            "max_tokens": 8000,
            "is_default": True,
            "is_active": True
        },
        
        # Ollama 模型
        {
            "model_id": "llama2",
            "model_name": "Llama 2",
            "description": "Meta的Llama 2模型（通过Ollama）",
            "supplier_name": "ollama",
            "context_window": 4096,
            "max_tokens": 2000,
            "is_default": True,
            "is_active": True
        }
    ]
    
    # 插入模型数据
    for model_data in default_models:
        try:
            supplier_id = supplier_ids.get(model_data["supplier_name"])
            if not supplier_id:
                print(f"✗ 找不到供应商: {model_data['supplier_name']}")
                continue
            
            # 创建模型对象
            model = ModelDB(
                model_id=model_data["model_id"],
                model_name=model_data["model_name"],
                description=model_data["description"],
                supplier_id=supplier_id,
                context_window=model_data["context_window"],
                max_tokens=model_data["max_tokens"],
                is_default=model_data["is_default"],
                is_active=model_data["is_active"]
            )
            
            db.add(model)
            db.commit()
            db.refresh(model)
            
            print(f"✓ 创建模型: {model.model_name} (供应商: {model_data['supplier_name']})")
            
        except Exception as e:
            db.rollback()
            print(f"✗ 创建模型 {model_data['model_name']} 失败: {e}")
    
    print("默认供应商和模型数据初始化完成！")


def main():
    """主函数"""
    db = SessionLocal()
    try:
        seed_default_suppliers_and_models(db)
    except Exception as e:
        print(f"初始化失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()