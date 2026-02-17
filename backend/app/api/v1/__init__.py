"""API v1 版本路由初始化"""
from fastapi import APIRouter
from typing import Dict, List
import importlib
import logging

from app.core.config import settings
from app.core.logging_config import logger

logger = logging.getLogger(__name__)

api_router = APIRouter()

# 路由分组配置（包含路由注册参数）
ROUTE_GROUPS: Dict[str, List[Dict]] = {
    'auth': [
        {'module': 'app.modules.auth.api.auth', 'prefix': '/auth', 'tags': ['auth']}
    ],
    'conversation': [
        {'module': 'app.modules.conversation.api.conversations', 'prefix': '/conversations', 'tags': ['conversations']}
    ],
    'llm': [
        {'module': 'app.modules.llm.api.llm', 'prefix': '/llm', 'tags': ['llm']}
    ],
    'memory': [
        {'module': 'app.modules.memory.api.memories', 'prefix': '/memory', 'tags': ['memory']}
    ],
    'models': [
        {'module': 'app.modules.supplier_model_management.api.model_management', 'prefix': '/model-management', 'tags': ['model-management']},
        {'module': 'app.modules.supplier_model_management.api.supplier_model', 'tags': ['supplier-model']},
        {'module': 'app.api.v1.model_capabilities', 'tags': ['model_capabilities']},
        {'module': 'app.api.v1.model_management', 'prefix': '/model-management', 'tags': ['model-parameters']},
        {'module': 'app.api.v1.default_model', 'tags': ['default-model']},
        {'module': 'app.api.v1.local_models', 'tags': ['local-models']}
    ],
    'capabilities': [
        {'module': 'app.api.v1.capability', 'prefix': '/capabilities', 'tags': ['model_capabilities']},
        {'module': 'app.api.v1.capability_types', 'tags': ['capability_types']},
        {'module': 'app.api.v1.capability_dimensions', 'tags': ['capability_dimensions']},
        {'module': 'app.modules.capability_category.api.model_categories', 'tags': ['model_categories']},
        {'module': 'app.modules.capability_category.api.category_templates', 'tags': ['category_templates']}
    ],
    'agents': [
        {'module': 'app.api.v1.agents', 'prefix': '/agents', 'tags': ['agents']},
        {'module': 'app.api.v1.agent_categories', 'prefix': '/agent-categories', 'tags': ['agent-categories']},
        {'module': 'app.api.v1.agent_parameters', 'prefix': '/agents', 'tags': ['agent-parameters']},
        {'module': 'app.api.v1.agent_system', 'prefix': '/agent-system', 'tags': ['agent-system']}
    ],
    'skills': [
        {'module': 'app.api.v1.skills', 'prefix': '/skills', 'tags': ['skills']},
        {'module': 'app.api.v1.external_skills', 'prefix': '/external-skills', 'tags': ['external-skills']},
        {'module': 'app.api.v1.skill_management_router', 'prefix': '/skill-management', 'tags': ['skill-management']}
    ],
    'knowledge': [
        {'module': 'app.modules.knowledge.api.knowledge', 'prefix': '/knowledge', 'tags': ['knowledge']},
        {'module': 'app.modules.knowledge.api.knowledge_graph_api', 'prefix': '/knowledge-graph', 'tags': ['knowledge-graph']},
        {'module': 'app.modules.knowledge.api.entity_config_api', 'tags': ['entity-config']}
    ],
    'workflow': [
        {'module': 'app.modules.workflow.api.workflow', 'tags': ['workflows']}
    ],
    'translation': [
        {'module': 'app.api.v1.translation_history', 'prefix': '/translation-history', 'tags': ['translation-history']},
        {'module': 'app.api.v1.document_translation', 'prefix': '/translate', 'tags': ['document-translation']},
        {'module': 'app.api.v1.batch_translation', 'prefix': '/batch-translate', 'tags': ['batch-translation']}
    ],
    'tasks': [
        {'module': 'app.api.v1.tasks', 'prefix': '/tasks', 'tags': ['tasks']}
    ],
    'parameters': [
        {'module': 'app.api.v1.parameter_template', 'tags': ['parameter-template']},
        {'module': 'app.api.v1.parameter_normalization_rules', 'tags': ['parameter-normalization-rules']},
        {'module': 'app.api.v1.parameter_mappings', 'tags': ['parameter-mappings']},
        {'module': 'app.api.v1.parameter_templates', 'tags': ['parameter-templates']},
        {'module': 'app.api.v1.system_parameters', 'tags': ['system-parameters']},
        {'module': 'app.api.v1.dimension_hierarchy', 'prefix': '/dimension-hierarchy', 'tags': ['dimension-hierarchy']}
    ],
    'search': [
        {'module': 'app.api.v1.search_management', 'tags': ['search']}
    ],
    'file': [
        {'module': 'app.api.v1.file_upload', 'prefix': '/file-upload', 'tags': ['file-upload']}
    ],
    'terminology': [
        {'module': 'app.api.v1.terminology', 'tags': ['terminology']}
    ],
    'topic': [
        {'module': 'app.api.v1.topic_title', 'tags': ['topic-title']}
    ],
    'orchestration': [
        {'module': 'app.modules.orchestration.api', 'prefix': '/orchestration', 'tags': ['orchestration']}
    ],
    'docs': [
        {'module': 'app.api.v1.api_docs', 'prefix': '/api-docs', 'tags': ['api-docs']}
    ]
}

_loaded_groups = set()

async def load_route_group(group_name: str) -> bool:
    """
    动态加载路由组
    
    Args:
        group_name: 路由组名称
        
    Returns:
        是否加载成功
    """
    if group_name in _loaded_groups:
        logger.info(f"路由组 {group_name} 已加载，跳过")
        return True
    
    routes = ROUTE_GROUPS.get(group_name, [])
    if not routes:
        logger.warning(f"路由组 {group_name} 不存在")
        return False
    
    # 特殊处理知识图谱路由组
    if group_name == 'knowledge' and not settings.enable_knowledge_graph:
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
        
        logger.info("知识图谱功能已禁用，跳过相关路由")
        _loaded_groups.add(group_name)
        return True
    
    for route_config in routes:
        module_path = route_config['module']
        prefix = route_config.get('prefix')
        tags = route_config.get('tags')
        
        # 如果知识图谱功能禁用，跳过相关路由
        if not settings.enable_knowledge_graph and ('knowledge_graph' in module_path or 'entity_config' in module_path):
            logger.info(f"知识图谱功能已禁用，跳过路由模块: {module_path}")
            continue
        
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, 'router'):
                if prefix:
                    api_router.include_router(module.router, prefix=prefix, tags=tags)
                else:
                    api_router.include_router(module.router, tags=tags)
                logger.info(f"成功加载路由模块: {module_path}")
        except ImportError as e:
            logger.error(f"加载路由模块失败 {module_path}: {e}")
            return False
    
    _loaded_groups.add(group_name)
    logger.info(f"路由组 {group_name} 加载完成")
    return True

# 预加载核心路由组（启动时加载）
CORE_ROUTE_GROUPS = ['auth', 'conversation', 'llm', 'memory']

async def preload_core_routes():
    """预加载核心路由组"""
    logger.info("开始预加载核心路由组...")
    for group_name in CORE_ROUTE_GROUPS:
        await load_route_group(group_name)
    logger.info(f"核心路由组预加载完成，已加载: {_loaded_groups}")

# 导出API路由对象和加载函数
__all__ = ["api_router", "load_route_group", "preload_core_routes"]
