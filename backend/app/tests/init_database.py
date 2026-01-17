#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建智能桌面助手应用的所有数据库表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.dependencies import engine
from app.core.database import Base

# 导入所有模型，确保它们被注册到Base.metadata
from app.models import user, agent, conversation, memory, knowledge_base
from app.modules.conversation.models import conversation as module_conversation
from app.modules.memory.models import memory as module_memory

def init_database():
    """初始化数据库表"""
    print("=== 数据库初始化 ===")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功！")
        
        print("\n已创建的表：")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
    except Exception as e:
        print(f"数据库初始化失败：{e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()