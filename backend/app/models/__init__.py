"""Database models module"""
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.llm import LLMRequestHistory, ModelConfiguration
# 使用supplier_db中的模型而不是model_management中的模型
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.agent import Agent

__all__ = [
    "User",
    "Conversation",
    "Message",
    "LLMRequestHistory",
    "ModelConfiguration",
    # "ModelSupplier" 和 "Model" 从supplier_db导入
    "ModelCapability",
    "ModelCapabilityAssociation",
    "Agent"
]