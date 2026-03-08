#!/usr/bin/env python3
"""
异步任务模块

包含知识图谱构建相关的异步任务
"""

from app.tasks.knowledge_graph_tasks import (
    build_knowledge_graph_task,
    build_document_layer_task,
    build_knowledge_base_layer_task,
    build_global_layer_task,
    incremental_update_task,
)

from app.tasks.entity_extraction_tasks import (
    extract_entities_task,
    batch_extract_entities_task,
)

from app.tasks.entity_alignment_tasks import (
    align_entities_task,
    cross_kb_link_task,
)

__all__ = [
    # 知识图谱构建任务
    'build_knowledge_graph_task',
    'build_document_layer_task',
    'build_knowledge_base_layer_task',
    'build_global_layer_task',
    'incremental_update_task',
    # 实体提取任务
    'extract_entities_task',
    'batch_extract_entities_task',
    # 实体对齐任务
    'align_entities_task',
    'cross_kb_link_task',
]
