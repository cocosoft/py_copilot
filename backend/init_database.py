"""初始化数据库表脚本"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.base import Base

# 导入所有模型以注册到 Base.metadata
# 用户和基础模型
from app.models.user import User
from app.models.workspace import Workspace
from app.models.setting import UserSetting

# 对话和消息
from app.models.conversation import Conversation, Message

# LLM 相关
from app.models.llm import LLMRequestHistory, ModelConfiguration
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.model_category import ModelCategory, ModelCategoryAssociation
from app.models.category_capability_association import CategoryCapabilityAssociation
from app.models.default_model import DefaultModel

# 供应商和模型
from app.models.supplier_db import SupplierDB, ModelDB

# Agent 相关
from app.models.agent import Agent
from app.models.agent_category import AgentCategory
from app.models.agent_parameter import AgentParameter
from app.models.agent_tool_association import AgentToolAssociation
from app.models.agent_skill_association import AgentSkillAssociation

# 技能相关
from app.models.skill import Skill, SkillSession, SkillModelBinding, SkillExecutionLog, SkillRepository, RemoteSkill

# 工具相关
from app.models.tool import Tool as CapabilityTool, ToolExecutionLog as CapabilityToolExecutionLog
from app.models.function_calling import Tool, ToolExecution, ToolUsageStats

# 记忆相关
from app.models.memory import GlobalMemory, ConversationMemoryMapping, KnowledgeMemoryMapping, MemoryAssociation, MemoryAccessLog, UserMemoryConfig

# 搜索设置
from app.models.search_settings import SearchSetting

# 参数模板
from app.models.parameter_template import ParameterTemplate, ParameterTemplateVersion
from app.models.parameter_normalization import ParameterNormalizationRule

# 翻译历史
from app.models.translation_history import TranslationHistory

# 平台配置
from app.models.platform_config import PlatformConfig
from app.models.api_favorite import ApiFavorite

# 文件记录
from app.models.file_record import FileRecord, FileBlob, FileCategory, FileStatus, StorageType

# 能力中心相关
from app.models.capability_db import CapabilityDB

# 监控相关
from app.models.monitoring import MonitoringMetric, AlertRule, AlertHistory

# 审计日志
from app.models.audit_log import AuditLog

# 任务相关
from app.models.task import Task, TaskExecution, TaskSchedule

# 术语相关
from app.models.terminology import Terminology

# 分类模板
from app.models.category_template import CategoryTemplate

# 聊天增强
from app.models.chat_enhancements import ChatEnhancement

# 模型评分
from app.models.model_rating import ModelRating

# 模型管理
from app.models.model_management import ModelManagementConfig

def init_database():
    """初始化数据库，创建所有表"""
    print("开始初始化数据库...")
    
    # 查看当前注册的表
    print(f"\n当前 Base.metadata 中注册的表 ({len(Base.metadata.tables)} 个):")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")
    
    # 创建所有表
    print("\n正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    # 验证创建的表
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n✅ 数据库初始化完成！共创建 {len(tables)} 个表:")
    for table_name in sorted(tables):
        print(f"  - {table_name}")
    
    return len(tables)

if __name__ == "__main__":
    init_database()
