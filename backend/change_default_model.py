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

# 设置新的默认模型 (例如使用qwen-pro)
new_default_model = db.query(Model).filter(Model.name == "qwen-pro").first()

if new_default_model:
    new_default_model.is_default = True
    db.commit()
    print(f"已将模型 {new_default_model.name} 设置为新的默认模型")
else:
    # 如果qwen-pro不存在，尝试使用其他模型
    print("qwen-pro模型不存在，尝试查找其他可用模型...")
    available_models = db.query(Model).filter(Model.model_type == "chat", Model.is_active == True).all()
    if available_models:
        # 使用第一个可用模型
        available_models[0].is_default = True
        db.commit()
        print(f"已将模型 {available_models[0].name} 设置为新的默认模型")
    else:
        print("没有找到可用的聊天模型")

# 验证新的默认模型
current_default = db.query(Model).filter(Model.model_type == "chat", Model.is_default == True).first()
if current_default:
    print(f"\n当前默认模型:")
    print(f"名称: {current_default.name}")
    print(f"显示名称: {current_default.display_name}")
    print(f"供应商: {current_default.supplier.name}")
    print(f"供应商显示名称: {current_default.supplier.display_name}")
    print(f"API端点: {current_default.supplier.api_endpoint}")
    print(f"是否活跃: {current_default.is_active}")
else:
    print("\n没有找到默认模型")
