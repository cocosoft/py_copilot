from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class WorkflowBase(BaseModel):
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    definition: Optional[Dict[str, Any]] = Field(None, description="工作流定义")

class WorkflowCreate(WorkflowBase):
    status: Optional[str] = Field("draft", description="工作流状态")
    version: Optional[str] = Field("1.0", description="工作流版本")

class WorkflowUpdate(WorkflowBase):
    status: Optional[str] = Field(None, description="工作流状态")

class Workflow(WorkflowBase):
    id: int
    status: str
    version: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class WorkflowExecutionBase(BaseModel):
    workflow_id: int = Field(..., description="工作流ID")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")

class WorkflowExecutionCreate(WorkflowExecutionBase):
    pass

class WorkflowExecution(WorkflowExecutionBase):
    id: int
    status: str
    output_data: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    created_by: Optional[int]
    
    class Config:
        from_attributes = True

class WorkflowNodeBase(BaseModel):
    workflow_id: int = Field(..., description="工作流ID")
    node_id: str = Field(..., description="节点唯一标识")
    node_type: str = Field(..., description="节点类型")
    name: str = Field(..., description="节点名称")
    config: Optional[Dict[str, Any]] = Field(None, description="节点配置")
    position: Optional[Dict[str, Any]] = Field(None, description="节点位置")

class WorkflowNodeCreate(WorkflowNodeBase):
    pass

class WorkflowNode(WorkflowNodeBase):
    id: int
    
    class Config:
        from_attributes = True

class NodeExecution(BaseModel):
    id: int
    workflow_execution_id: int
    node_id: str
    node_type: str
    status: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

# 知识图谱相关的工作流节点配置
class KnowledgeSearchNodeConfig(BaseModel):
    knowledge_base_id: Optional[int] = Field(None, description="知识库ID")
    search_query: str = Field(..., description="搜索查询")
    entity_types: Optional[List[str]] = Field(None, description="实体类型过滤")
    confidence_threshold: float = Field(0.5, description="置信度阈值")
    max_results: int = Field(10, description="最大结果数")
    include_relationships: bool = Field(True, description="是否包含关系")

class EntityExtractionNodeConfig(BaseModel):
    text_input: str = Field(..., description="输入文本")
    entity_types: Optional[List[str]] = Field(None, description="实体类型")
    confidence_threshold: float = Field(0.5, description="置信度阈值")

class RelationshipAnalysisNodeConfig(BaseModel):
    entity_ids: List[str] = Field(..., description="实体ID列表")
    relationship_types: Optional[List[str]] = Field(None, description="关系类型")
    max_depth: int = Field(2, description="最大深度")

class WorkflowExecutionRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")

class WorkflowExecutionResponse(BaseModel):
    execution_id: int
    status: str
    message: str

class WorkflowNodeExecutionResult(BaseModel):
    node_id: str
    node_type: str
    status: str
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]