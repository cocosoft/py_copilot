import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
# 导入所有模型以确保创建所有表
from app.models import *
from app.modules.knowledge.models.knowledge_document import KnowledgeBase, KnowledgeDocument, KnowledgeTag
from app.modules.workflow.models.workflow import Workflow, WorkflowExecution, WorkflowNode, NodeExecution
from app.models.search_settings import SearchSetting

# 创建所有表
Base.metadata.create_all(bind=engine)
print("数据库表创建成功！")
