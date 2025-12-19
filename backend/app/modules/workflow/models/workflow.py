from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from app.core.database import Base
from datetime import datetime

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    definition = Column(JSON)  # 工作流定义（节点、边等）
    status = Column(String(50), default="draft")  # draft, active, inactive
    version = Column(String(50), default="1.0")
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name})>"

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, nullable=False)
    status = Column(String(50), default="running")  # running, completed, failed, paused
    input_data = Column(JSON)
    output_data = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_by = Column(Integer)
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"

class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, nullable=False)
    node_id = Column(String(100), nullable=False)  # 节点唯一标识
    node_type = Column(String(100), nullable=False)  # knowledge_search, entity_extraction, etc.
    name = Column(String(255), nullable=False)
    config = Column(JSON)  # 节点配置参数
    position = Column(JSON)  # 节点位置信息
    
    def __repr__(self):
        return f"<WorkflowNode(id={self.id}, node_id={self.node_id}, type={self.node_type})>"

class NodeExecution(Base):
    __tablename__ = "node_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_execution_id = Column(Integer, nullable=False)
    node_id = Column(String(100), nullable=False)
    node_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    input_data = Column(JSON)
    output_data = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<NodeExecution(id={self.id}, node_id={self.node_id}, status={self.status})>"