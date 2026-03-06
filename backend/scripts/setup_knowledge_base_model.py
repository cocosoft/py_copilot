#!/usr/bin/env python3
"""
配置知识库场景默认模型脚本
将Ollama的deepseek-r1模型配置为知识库场景的默认模型
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.supplier_db import SupplierDB, ModelDB
from app.models.default_model import DefaultModel


def setup_knowledge_base_model():
    """配置知识库场景使用Ollama deepseek-r1模型"""
    
    db = SessionLocal()
    
    try:
        print("开始配置知识库场景默认模型...")
        
        # 1. 查找Ollama供应商
        ollama_supplier = db.query(SupplierDB).filter(SupplierDB.name == "ollama").first()
        
        if not ollama_supplier:
            print("错误：未找到Ollama供应商，请先运行种子脚本初始化供应商数据")
            return False
        
        print(f"找到Ollama供应商 (ID: {ollama_supplier.id})")
        
        # 2. 查找或创建deepseek-r1模型
        deepseek_model = db.query(ModelDB).filter(
            ModelDB.model_id == "deepseek-r1",
            ModelDB.supplier_id == ollama_supplier.id
        ).first()
        
        if not deepseek_model:
            print("创建deepseek-r1模型...")
            deepseek_model = ModelDB(
                model_id="deepseek-r1",
                model_name="DeepSeek R1",
                description="DeepSeek R1推理模型（通过Ollama本地部署）",
                supplier_id=ollama_supplier.id,
                context_window=32000,
                max_tokens=8000,
                is_default=False,
                is_active=True
            )
            db.add(deepseek_model)
            db.commit()
            db.refresh(deepseek_model)
            print(f"✓ 创建模型成功 (ID: {deepseek_model.id})")
        else:
            print(f"找到deepseek-r1模型 (ID: {deepseek_model.id})")
        
        # 3. 检查是否已有知识库场景配置
        existing_config = db.query(DefaultModel).filter(
            DefaultModel.scope == "scene",
            DefaultModel.scene == "knowledge"
        ).first()
        
        if existing_config:
            print(f"更新现有知识库场景配置 (ID: {existing_config.id})")
            existing_config.model_id = deepseek_model.id
            existing_config.is_active = True
        else:
            print("创建知识库场景默认模型配置...")
            config = DefaultModel(
                scope="scene",
                scene="knowledge",
                model_id=deepseek_model.id,
                priority=1,
                is_active=True
            )
            db.add(config)
        
        db.commit()
        print("✓ 知识库场景默认模型配置成功！")
        print(f"  - 场景: knowledge (知识库)")
        print(f"  - 模型: deepseek-r1 (ID: {deepseek_model.id})")
        print(f"  - 供应商: Ollama")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"✗ 配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = setup_knowledge_base_model()
    sys.exit(0 if success else 1)
