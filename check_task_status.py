#!/usr/bin/env python3
"""
检查实体识别任务状态
"""

import sys
sys.path.insert(0, 'backend')

from app.modules.knowledge.models.knowledge_document import EntityExtractionTask
from app.core.database import SessionLocal
from datetime import datetime

def check_tasks():
    db = SessionLocal()
    try:
        # 获取所有任务
        tasks = db.query(EntityExtractionTask).order_by(EntityExtractionTask.created_at.desc()).all()
        
        print("=" * 80)
        print(f"{'ID':<5} {'文档ID':<8} {'状态':<12} {'类型':<12} {'进度':<10} {'实体数':<10} {'创建时间'}")
        print("=" * 80)
        
        for task in tasks:
            progress = f"{task.processed_chunks}/{task.total_chunks}"
            entities = f"片段:{task.chunk_entity_count} 文档:{task.document_entity_count}"
            created = task.created_at.strftime("%m-%d %H:%M") if task.created_at else "N/A"
            
            print(f"{task.id:<5} {task.document_id:<8} {task.status:<12} {task.task_type or 'N/A':<12} {progress:<10} {entities:<10} {created}")
        
        print("=" * 80)
        print(f"\n总任务数: {len(tasks)}")
        
        # 统计各状态任务数
        processing = db.query(EntityExtractionTask).filter(EntityExtractionTask.status == 'processing').count()
        pending = db.query(EntityExtractionTask).filter(EntityExtractionTask.status == 'pending').count()
        completed = db.query(EntityExtractionTask).filter(EntityExtractionTask.status == 'completed').count()
        failed = db.query(EntityExtractionTask).filter(EntityExtractionTask.status == 'failed').count()
        
        print(f"处理中: {processing} | 待处理: {pending} | 已完成: {completed} | 失败: {failed}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_tasks()
