"""API v1 版本路由初始化"""
from fastapi import APIRouter

# 导入配置
from app.core.config import settings

# 从模块化的API中导入路由
from app.modules.auth.api.auth import router as auth_router
from app.modules.conversation.api.conversations import router as conversation_router
from app.modules.llm.api.llm import router as llm_router
from app.modules.memory.api.memories import router as memory_router
from app.modules.supplier_model_management.api.model_management import router as model_management_router
from app.modules.supplier_model_management.api.supplier_model import router as supplier_model_router
from app.api.v1.model_capabilities import router as model_capabilities_router
from app.api.v1.capability import router as capability_router
from app.api.v1.capability_types import router as capability_types_router
from app.api.v1.capability_dimensions import router as capability_dimensions_router
from app.api.v1.model_management import router as model_management_v1_router
from app.api.v1.default_model import router as default_model_router
from app.api.v1.parameter_template import router as parameter_template_router
from app.api.v1.parameter_normalization_rules import router as parameter_normalization_rules_router
from app.api.v1.parameter_mappings import router as parameter_mappings_router
from app.api.v1.system_parameters import router as system_parameters_router

from app.modules.capability_category.api.model_categories import router as model_categories_router
from app.modules.capability_category.api.category_templates import router as category_templates_router
from app.api.v1.agents import router as agents_router
from app.api.v1.agent_categories import router as agent_categories_router
from app.modules.knowledge.api.knowledge import router as knowledge_router
from app.modules.knowledge.api.knowledge_graph_api import router as knowledge_graph_router
from app.modules.knowledge.api.entity_config_api import router as entity_config_router
from app.modules.workflow.api.workflow import router as workflow_router
from app.api.v1.agent_parameters import router as agent_parameters_router
from app.api.v1.search_management import router as search_management_router
from app.api.v1.supplier_model import router as supplier_model_v1_router
from app.api.v1.skills import router as skills_router
from app.api.v1.external_skills import router as external_skills_router
from app.api.v1.skill_management_router import router as skill_management_router
from app.api.v1.file_upload import router as file_upload_router

api_router = APIRouter()

# 注册所有模块的API路由
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(conversation_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(llm_router, prefix="/llm", tags=["llm"])
# 先注册包含suppliers-list的模型管理路由
# api_router.include_router(model_management_router, prefix="/model-management", tags=["model-management"])
# 启用supplier_model_router以提供/suppliers端点，放在前面确保优先匹配
api_router.include_router(supplier_model_v1_router, tags=["supplier-model"])
api_router.include_router(default_model_router, tags=["default-model"])
api_router.include_router(model_management_v1_router, prefix="/model-management", tags=["model-parameters"])
# 注册参数模板路由
api_router.include_router(parameter_template_router, tags=["parameter-template"])
# 注册参数归一化规则路由
api_router.include_router(parameter_normalization_rules_router, tags=["parameter-normalization-rules"])
# 注册参数映射路由
api_router.include_router(parameter_mappings_router, tags=["parameter-mappings"])
# 注册系统参数管理路由
api_router.include_router(system_parameters_router, tags=["system-parameters"])
# 注册维度层次结构路由
from app.api.v1.dimension_hierarchy import router as dimension_hierarchy_router
api_router.include_router(dimension_hierarchy_router, prefix="/dimension-hierarchy", tags=["dimension-hierarchy"])
api_router.include_router(model_capabilities_router, tags=["model_capabilities"])
api_router.include_router(capability_router, tags=["model_capabilities"])
api_router.include_router(capability_types_router, tags=["capability_types"])
api_router.include_router(capability_dimensions_router, tags=["capability_dimensions"])
# 先注册支持文件上传的model_categories_router
api_router.include_router(model_categories_router, tags=["model_categories"])

# 注册分类模板路由
api_router.include_router(category_templates_router, tags=["category_templates"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(agent_parameters_router, prefix="/agents", tags=["agent-parameters"])
api_router.include_router(agent_categories_router, prefix="/agent-categories", tags=["agent-categories"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])

# 根据配置决定是否启用知识图谱功能
if settings.enable_knowledge_graph:
    api_router.include_router(knowledge_graph_router, prefix="/knowledge-graph", tags=["knowledge-graph"])
    api_router.include_router(entity_config_router, tags=["entity-config"])
else:
    # 知识图谱功能禁用时，返回友好的错误信息
    from fastapi import HTTPException
    
    @api_router.get("/knowledge-graph/{path:path}")
    @api_router.post("/knowledge-graph/{path:path}")
    @api_router.put("/knowledge-graph/{path:path}")
    @api_router.delete("/knowledge-graph/{path:path}")
    async def knowledge_graph_disabled():
        raise HTTPException(status_code=503, detail="知识图谱功能暂时禁用，正在优化中")
    
    @api_router.get("/entity-config/{path:path}")
    @api_router.post("/entity-config/{path:path}")
    @api_router.put("/entity-config/{path:path}")
    @api_router.delete("/entity-config/{path:path}")
    async def entity_config_disabled():
        raise HTTPException(status_code=503, detail="实体配置功能暂时禁用，正在优化中")
api_router.include_router(workflow_router, tags=["workflows"])
api_router.include_router(search_management_router)
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
api_router.include_router(external_skills_router, prefix="/external-skills", tags=["external-skills"])
api_router.include_router(skill_management_router, prefix="/skill-management", tags=["skill-management"])
api_router.include_router(memory_router, prefix="/memory", tags=["memory"])

# 注册翻译历史路由
from app.api.v1.translation_history import router as translation_history_router
api_router.include_router(translation_history_router, prefix="/translation-history", tags=["translation-history"])

# 注册文档翻译路由
from app.api.v1.document_translation import router as document_translation_router
api_router.include_router(document_translation_router, prefix="/translate", tags=["document-translation"])

# 注册批量翻译路由
from app.api.v1.batch_translation import router as batch_translation_router
api_router.include_router(batch_translation_router, prefix="/batch-translate", tags=["batch-translation"])

# 注册任务处理路由
from app.api.v1.tasks import router as tasks_router
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])

# 注册术语库路由
from app.api.v1.terminology import router as terminology_router
api_router.include_router(terminology_router, tags=["terminology"])

# 注册智能体编排系统路由
from app.modules.orchestration.api import router as orchestration_router
api_router.include_router(orchestration_router, prefix="/orchestration", tags=["orchestration"])

# 注册文件上传路由
api_router.include_router(file_upload_router, prefix="/file-upload", tags=["file-upload"])

# 导出API路由对象
__all__ = ["api_router"]