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
        {'module': 'app.api.v1.supplier_model', 'tags': ['supplier-model-v1']},
        {'module': 'app.api.v1.model_capabilities', 'prefix': '/model-capabilities', 'tags': ['model_capabilities']},
        {'module': 'app.api.v1.model_management', 'prefix': '/model-management', 'tags': ['model-parameters']},
        {'module': 'app.api.v1.default_model', 'tags': ['default-model']},
        {'module': 'app.api.v1.local_models', 'tags': ['local-models']}
    ],
    'capabilities': [
        {'module': 'app.api.v1.capability', 'prefix': '/capabilities', 'tags': ['model_capabilities']},
        {'module': 'app.api.v1.capability_types', 'prefix': '/capability-types', 'tags': ['capability_types']},
        {'module': 'app.api.v1.capability_dimensions', 'prefix': '/model-capability/dimensions', 'tags': ['capability_dimensions']},
        {'module': 'app.modules.capability_category.api.model_categories', 'prefix': '/categories', 'tags': ['model_categories']},
        {'module': 'app.modules.capability_category.api.category_templates', 'prefix': '/category-templates', 'tags': ['category_templates']}
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
    'tools': [
        {'module': 'app.api.v1.tools', 'prefix': '/tools', 'tags': ['tools']}
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

def _load_route_group_sync(group_name: str) -> bool:
    """
    同步加载路由组（模块加载时使用）
    
    Args:
        group_name: 路由组名称
        
    Returns:
        是否加载成功
    """
    logger.info(f"[同步] 开始加载路由组: {group_name}")
    
    if group_name in _loaded_groups:
        logger.info(f"[同步] 路由组 {group_name} 已加载，跳过")
        return True
    
    routes = ROUTE_GROUPS.get(group_name, [])
    if not routes:
        logger.warning(f"[同步] 路由组 {group_name} 不存在")
        return False
    
    logger.info(f"[同步] 路由组 {group_name} 包含 {len(routes)} 个模块")
    
    for route_config in routes:
        module_path = route_config['module']
        prefix = route_config.get('prefix')
        tags = route_config.get('tags')
        
        logger.info(f"[同步] 正在加载模块: {module_path}")
        
        try:
            module = importlib.import_module(module_path)
            logger.info(f"[同步] 模块导入成功: {module_path}")
            if hasattr(module, 'router'):
                if prefix:
                    api_router.include_router(module.router, prefix=prefix, tags=tags)
                else:
                    api_router.include_router(module.router, tags=tags)
                logger.info(f"[同步] 成功加载路由模块: {module_path}")
            else:
                logger.warning(f"[同步] 模块 {module_path} 没有router属性")
        except Exception as e:
            logger.error(f"[同步] 加载路由模块失败 {module_path}: {e}", exc_info=True)
            return False
    
    _loaded_groups.add(group_name)
    logger.info(f"[同步] 路由组 {group_name} 加载完成")
    return True

async def load_route_group(group_name: str) -> bool:
    """
    动态加载路由组
    
    Args:
        group_name: 路由组名称
        
    Returns:
        是否加载成功
    """
    logger.info(f"开始加载路由组: {group_name}")
    
    if group_name in _loaded_groups:
        logger.info(f"路由组 {group_name} 已加载，跳过")
        return True
    
    routes = ROUTE_GROUPS.get(group_name, [])
    if not routes:
        logger.warning(f"路由组 {group_name} 不存在")
        return False
    
    logger.info(f"路由组 {group_name} 包含 {len(routes)} 个模块")
    
    for route_config in routes:
        module_path = route_config['module']
        prefix = route_config.get('prefix')
        tags = route_config.get('tags')
        
        logger.info(f"正在加载模块: {module_path}")
        
        # 如果知识图谱功能禁用，跳过相关路由
        if not settings.enable_knowledge_graph and ('knowledge_graph' in module_path or 'entity_config' in module_path):
            logger.info(f"知识图谱功能已禁用，跳过路由模块: {module_path}")
            continue
        
        try:
            logger.info(f"开始导入模块: {module_path}")
            module = importlib.import_module(module_path)
            logger.info(f"模块导入成功: {module_path}")
            if hasattr(module, 'router'):
                if prefix:
                    api_router.include_router(module.router, prefix=prefix, tags=tags)
                else:
                    api_router.include_router(module.router, tags=tags)
                logger.info(f"成功加载路由模块: {module_path}")
            else:
                logger.warning(f"模块 {module_path} 没有router属性")
        except Exception as e:
            logger.error(f"加载路由模块失败 {module_path}: {e}", exc_info=True)
            return False
    
    _loaded_groups.add(group_name)
    logger.info(f"路由组 {group_name} 加载完成")
    return True

# 预加载核心路由组（启动时加载）
CORE_ROUTE_GROUPS = ['auth', 'conversation', 'llm', 'memory', 'models', 'tasks', 'agents', 'skills', 'capabilities', 'knowledge', 'tools']

async def preload_core_routes():
    """预加载核心路由组"""
    logger.info("开始预加载核心路由组...")
    logger.info(f"核心路由组列表: {CORE_ROUTE_GROUPS}")
    for group_name in CORE_ROUTE_GROUPS:
        logger.info(f"正在加载路由组: {group_name}")
        try:
            result = await load_route_group(group_name)
            if not result:
                logger.error(f"路由组 {group_name} 加载失败")
        except Exception as e:
            logger.error(f"加载路由组 {group_name} 时发生异常: {e}", exc_info=True)
    logger.info(f"核心路由组预加载完成，已加载: {_loaded_groups}")

def preload_core_routes_sync():
    """
    同步预加载核心路由组（模块加载时调用）
    确保路由在应用启动前就已经注册
    """
    logger.info("[同步] 开始预加载核心路由组...")
    logger.info(f"[同步] 核心路由组列表: {CORE_ROUTE_GROUPS}")
    for group_name in CORE_ROUTE_GROUPS:
        try:
            result = _load_route_group_sync(group_name)
            if not result:
                logger.error(f"[同步] 路由组 {group_name} 加载失败")
        except Exception as e:
            logger.error(f"[同步] 加载路由组 {group_name} 时发生异常: {e}", exc_info=True)
    logger.info(f"[同步] 核心路由组预加载完成，已加载: {_loaded_groups}")

preload_core_routes_sync()

# 导出API路由对象和加载函数
__all__ = ["api_router", "load_route_group", "preload_core_routes"]
