#!/usr/bin/env python3
"""
能力表数据迁移脚本
将 capabilities 表中的数据迁移到 model_capabilities 表
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# 导入模型
from app.models.capability_db import CapabilityDB
from app.models.model_capability import ModelCapability
from app.core.config import settings

# 创建数据库连接
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate_capabilities():
    """执行能力数据迁移"""
    db = SessionLocal()
    
    try:
        print("开始迁移能力数据...")
        
        # 获取所有capabilities表中的数据
        capabilities = db.query(CapabilityDB).all()
        print(f"找到 {len(capabilities)} 条能力数据需要迁移")
        
        migrated_count = 0
        skipped_count = 0
        
        for capability in capabilities:
            # 检查是否已存在相同名称的能力
            existing = db.query(ModelCapability).filter(ModelCapability.name == capability.name).first()
            
            if existing:
                print(f"跳过已存在的能力: {capability.name}")
                skipped_count += 1
                continue
            
            # 创建新的ModelCapability记录
            new_capability = ModelCapability(
                name=capability.name,
                display_name=capability.display_name,
                description=capability.description,
                capability_type=capability.capability_type or "standard",
                domain="nlp",  # 默认领域
                is_active=capability.is_active,
                # input_types和output_types默认为None，后续可以手动更新
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(new_capability)
            migrated_count += 1
            print(f"迁移能力: {capability.name}")
        
        # 提交事务
        db.commit()
        
        print(f"\n迁移完成！")
        print(f"成功迁移: {migrated_count} 条记录")
        print(f"跳过已存在: {skipped_count} 条记录")
        
    except IntegrityError as e:
        db.rollback()
        print(f"\n迁移失败: 数据完整性错误 - {e}")
        sys.exit(1)
    except Exception as e:
        db.rollback()
        print(f"\n迁移失败: 未知错误 - {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate_capabilities()