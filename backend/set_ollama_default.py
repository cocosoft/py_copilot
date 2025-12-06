#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.core.database import get_db
from app.models.supplier_db import ModelDB as Model

db = next(get_db())

# 首先取消所有模型的默认状态
all_models = db.query(Model).filter(Model.model_type == "chat").all()
for model in all_models:
    if model.is_default:
        model.is_default = False
        print(f"取消模型 {model.name} 的默认状态")

# 设置Ollama的llama3为默认模型
ollama_llama3 = db.query(Model).filter(Model.name == "llama3").first()

if ollama_llama3:
    ollama_llama3.is_default = True
    db.commit()
    print(f"已将Ollama的 {ollama_llama3.name} 设置为新的默认模型")
    
    # 验证供应商是否活跃
    supplier = ollama_llama3.supplier
    if not supplier.is_active:
        supplier.is_active = True
        db.commit()
        print(f"已激活供应商 {supplier.name}")
        
    print(f"\n模型详情:")
    print(f"名称: {ollama_llama3.name}")
    print(f"供应商: {supplier.name}")
    print(f"API端点: {supplier.api_endpoint}")
    print(f"是否需要API密钥: {supplier.api_key_required}")
    print(f"是否活跃: {supplier.is_active}")
else:
    print("没有找到llama3模型")
    
    # 列出所有Ollama模型
    ollama_models = db.query(Model).filter(Model.supplier.has(name="Ollama")).all()
    if ollama_models:
        print("可用的Ollama模型:")
        for model in ollama_models:
            print(f"- {model.name}")
    else:
        print("没有找到Ollama模型")
