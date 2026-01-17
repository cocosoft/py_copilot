#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建智能桌面助手应用的所有数据库表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'py_copilot.db')}"

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 导入所有模型，确保它们被注册到Base.metadata
# 注意：这里需要直接导入模型类，避免循环导入

# 用户模型
from app.models.user import User

# 智能体模型
from app.models.agent import Agent

# 对话模型
from app.models.conversation import Conversation, Message

# 记忆模型
from app.models.memory import (
    GlobalMemory,
    UserMemoryConfig,
    MemoryAccessLog,
    ConversationMemoryMapping,
    KnowledgeMemoryMapping,
    MemoryAssociation
)

# 知识库模型
from app.modules.knowledge.models.knowledge_document import KnowledgeBase, KnowledgeDocument, KnowledgeTag, DocumentEntity, DocumentChunk, EntityRelationship

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