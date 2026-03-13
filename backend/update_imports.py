#!/usr/bin/env python3
"""
批量更新导入路径脚本
用于更新项目整理后的导入路径
"""

import os
import re
from pathlib import Path

# 定义导入路径替换规则
REPLACEMENTS = {
    # core 模块
    'from app.services.knowledge.document_processor': 'from app.services.knowledge.core.document_processor',
    'from app.services.knowledge.document_parser': 'from app.services.knowledge.core.document_parser',
    'from app.services.knowledge.advanced_text_processor': 'from app.services.knowledge.core.advanced_text_processor',
    'from app.services.knowledge.text_processor': 'from app.services.knowledge.core.text_processor',
    
    # extraction 模块
    'from app.services.knowledge.llm_extractor': 'from app.services.knowledge.extraction.llm_extractor',
    'from app.services.knowledge.enhanced_extraction_rules': 'from app.services.knowledge.extraction.enhanced_extraction_rules',
    'from app.services.knowledge.entity_extraction_cache': 'from app.services.knowledge.extraction.entity_extraction_cache',
    
    # alignment 模块
    'from app.services.knowledge.entity_alignment_service': 'from app.services.knowledge.alignment.entity_alignment_service',
    'from app.services.knowledge.bert_entity_aligner': 'from app.services.knowledge.alignment.bert_entity_aligner',
    'from app.services.knowledge.cross_kb_linking_service': 'from app.services.knowledge.alignment.cross_kb_linking_service',
    'from app.services.knowledge.distributed_entity_alignment': 'from app.services.knowledge.alignment.distributed_entity_alignment',
    
    # vectorization 模块
    'from app.services.knowledge.chroma_service': 'from app.services.knowledge.vectorization.chroma_service',
    'from app.services.knowledge.faiss_index_service': 'from app.services.knowledge.vectorization.faiss_index_service',
    'from app.services.knowledge.vector_store_adapter': 'from app.services.knowledge.vectorization.vector_store_adapter',
    
    # graph 模块
    'from app.services.knowledge.knowledge_graph_service': 'from app.services.knowledge.graph.knowledge_graph_service',
    'from app.services.knowledge.graph_builder': 'from app.services.knowledge.graph.graph_builder',
    'from app.services.knowledge.hierarchical_build_service': 'from app.services.knowledge.graph.hierarchical_build_service',
    'from app.services.knowledge.batch_graph_builder': 'from app.services.knowledge.graph.batch_graph_builder',
    'from app.services.knowledge.gnn_service': 'from app.services.knowledge.graph.gnn_service',
    
    # retrieval 模块
    'from app.services.knowledge.retrieval_service': 'from app.services.knowledge.retrieval.retrieval_service',
    'from app.services.knowledge.semantic_search_service': 'from app.services.knowledge.retrieval.semantic_search_service',
    'from app.services.knowledge.rerank_service': 'from app.services.knowledge.retrieval.rerank_service',
    'from app.services.knowledge.cached_retrieval_service': 'from app.services.knowledge.retrieval.cached_retrieval_service',
    'from app.services.knowledge.optimized_retrieval_service': 'from app.services.knowledge.retrieval.optimized_retrieval_service',
    'from app.services.knowledge.unified_retrieval_service': 'from app.services.knowledge.retrieval.unified_retrieval_service',
    
    # utils 模块
    'from app.services.knowledge.entity_filter': 'from app.services.knowledge.utils.entity_filter',
    'from app.services.knowledge.processing_progress_service': 'from app.services.knowledge.utils.processing_progress_service',
    
    # 相对导入（在同一目录内的）
    'from .llm_extractor': 'from app.services.knowledge.extraction.llm_extractor',
    'from .advanced_text_processor': 'from app.services.knowledge.core.advanced_text_processor',
    'from .document_processor': 'from app.services.knowledge.core.document_processor',
    'from .document_parser': 'from app.services.knowledge.core.document_parser',
}

def update_file_imports(filepath):
    """更新单个文件的导入路径"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        for old_import, new_import in REPLACEMENTS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes.append(f"{old_import} -> {new_import}")
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        return False, []
    except Exception as e:
        return False, [f"错误: {str(e)}"]

def main():
    backend_dir = Path(__file__).parent
    app_dir = backend_dir / "app"
    
    updated_files = []
    error_files = []
    
    # 遍历所有Python文件
    for py_file in app_dir.rglob("*.py"):
        # 跳过备份目录和__pycache__
        if "knowledge_backup" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        # 跳过示例文件
        if "examples" in str(py_file):
            continue
        
        updated, changes = update_file_imports(py_file)
        if updated:
            updated_files.append({
                'file': str(py_file.relative_to(backend_dir)),
                'changes': changes
            })
            print(f"✅ 已更新: {py_file.relative_to(backend_dir)}")
    
    # 生成报告
    print(f"\n{'='*60}")
    print(f"导入路径更新完成!")
    print(f"{'='*60}")
    print(f"共更新 {len(updated_files)} 个文件")
    
    if updated_files:
        print(f"\n更新详情:")
        for item in updated_files[:10]:  # 只显示前10个
            print(f"\n  📄 {item['file']}")
            for change in item['changes'][:3]:  # 只显示前3个变更
                print(f"     - {change}")
    
    # 保存详细报告
    report_path = backend_dir / "import_update_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("导入路径更新报告\n")
        f.write("="*60 + "\n\n")
        f.write(f"共更新 {len(updated_files)} 个文件\n\n")
        for item in updated_files:
            f.write(f"文件: {item['file']}\n")
            for change in item['changes']:
                f.write(f"  - {change}\n")
            f.write("\n")
    
    print(f"\n详细报告已保存到: {report_path}")

if __name__ == "__main__":
    main()
