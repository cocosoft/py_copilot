import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.modules.knowledge.models.knowledge_document import KnowledgeBase, KnowledgeDocument

# 创建所有表
Base.metadata.create_all(bind=engine)
print("数据库表创建成功！")
