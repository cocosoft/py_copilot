#!/usr/bin/env python3
"""
创建model_parameters表的脚本
"""

from sqlalchemy import create_engine, text, Table, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# 创建数据库引擎
DATABASE_URL = "sqlite:///./py_copilot.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_model_parameters_table():
    """创建模型参数表"""
    db = SessionLocal()
    try:
        # 检查表是否存在
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='model_parameters';")).fetchone()
        
        if not result:
            # 创建表
            db.execute(text("""
                CREATE TABLE model_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER NOT NULL,
                    parameter_name VARCHAR(100) NOT NULL,
                    parameter_type VARCHAR(50) NOT NULL,
                    parameter_value TEXT,
                    is_default BOOLEAN DEFAULT FALSE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
                )
            """))
            print("✓ 创建model_parameters表成功")
        else:
            print("ℹ️ model_parameters表已存在")
        
        db.commit()
    except Exception as e:
        print(f"❌ 出错了: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("开始创建model_parameters表...")
    create_model_parameters_table()
