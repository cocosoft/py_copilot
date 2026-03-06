#!/usr/bin/env python3
"""
配置知识库场景默认模型
使用Ollama的deepseek-r1:1.5b模型
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.default_model import DefaultModel


def setup_knowledge_base_scene():
    """配置知识库场景使用deepseek-r1:1.5b模型"""
    
    db = SessionLocal()
    
    try:
        print("配置知识库场景默认模型...\n")
        
        # Ollama的deepseek-r1:1.5b模型ID
        model_id = 46  # deepseek-r1:1.5b
        
        # 检查是否已有知识库场景配置
        existing = db.query(DefaultModel).filter(
            DefaultModel.scope == "scene",
            DefaultModel.scene == "knowledge"
        ).first()
        
        if existing:
            print(f"更新现有配置 (ID: {existing.id})")
            existing.model_id = model_id
            existing.is_active = True
            existing.priority = 1
        else:
            print("创建新的知识库场景配置...")
            config = DefaultModel(
                scope="scene",
                scene="knowledge",
                model_id=model_id,
                priority=1,
                is_active=True
            )
            db.add(config)
        
        db.commit()
        
        print("✅ 知识库场景默认模型配置成功！")
        print(f"   场景: knowledge (知识库)")
        print(f"   模型ID: {model_id}")
        print(f"   模型: deepseek-r1:1.5b (Ollama)")
        print()
        
        # 验证配置
        config = db.query(DefaultModel).filter(
            DefaultModel.scope == "scene",
            DefaultModel.scene == "knowledge"
        ).first()
        
        if config:
            print("✅ 配置验证成功")
            print(f"   配置ID: {config.id}")
            print(f"   模型ID: {config.model_id}")
            print(f"   状态: {'启用' if config.is_active else '禁用'}")
            return True
        else:
            print("❌ 配置验证失败")
            return False
        
    except Exception as e:
        db.rollback()
        print(f"❌ 配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = setup_knowledge_base_scene()
    sys.exit(0 if success else 1)
