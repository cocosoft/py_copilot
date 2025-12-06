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

# 设置DeepSeek模型为默认模型
deepseek_model = db.query(Model).filter(Model.name == "deepseek-chat").first()

if deepseek_model:
    deepseek_model.is_default = True
    db.commit()
    print(f"已将DeepSeek的 {deepseek_model.name} 设置为新的默认模型")
    
    # 验证供应商是否活跃
    supplier = deepseek_model.supplier
    if not supplier.is_active:
        supplier.is_active = True
        db.commit()
        print(f"已激活供应商 {supplier.name}")
        
    print(f"\n模型详情:")
    print(f"名称: {deepseek_model.name}")
    print(f"供应商: {supplier.name}")
    print(f"API端点: {supplier.api_endpoint}")
    print(f"是否需要API密钥: {supplier.api_key_required}")
    print(f"是否活跃: {supplier.is_active}")
    print(f"是否有API密钥配置: {'是' if deepseek_model.api_key else '否'}")
else:
    print("没有找到deepseek-chat模型")
