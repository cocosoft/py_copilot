"""
清理重复的实体识别任务

问题：由于代码逻辑问题，同一文档创建了多个任务记录
解决方案：保留每个文档最新的任务，删除旧的任务
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.modules.knowledge.models.knowledge_document import EntityExtractionTask, ChunkExtractionStatus

def cleanup_duplicate_tasks():
    """清理重复的任务记录"""

    # 从环境变量或配置文件读取数据库URL
    from app.core.config import settings
    database_url = settings.database_url

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("开始清理重复任务...")

        # 查询每个文档的最新任务
        from sqlalchemy import distinct

        # 获取所有文档ID
        document_ids = db.query(distinct(EntityExtractionTask.document_id)).all()
        document_ids = [d[0] for d in document_ids]

        total_deleted = 0
        total_docs = len(document_ids)

        for doc_id in document_ids:
            # 获取该文档的所有任务，按创建时间倒序
            tasks = db.query(EntityExtractionTask).filter(
                EntityExtractionTask.document_id == doc_id
            ).order_by(EntityExtractionTask.created_at.desc()).all()

            if len(tasks) > 1:
                # 保留最新的一个，删除其他的
                latest_task = tasks[0]
                old_tasks = tasks[1:]

                print(f"文档 {doc_id}: 发现 {len(tasks)} 个任务，保留最新任务(ID={latest_task.id})，删除 {len(old_tasks)} 个旧任务")

                for old_task in old_tasks:
                    # 先删除关联的 ChunkExtractionStatus 记录
                    db.query(ChunkExtractionStatus).filter(
                        ChunkExtractionStatus.task_id == old_task.id
                    ).delete(synchronize_session=False)

                    # 删除任务
                    db.delete(old_task)
                    total_deleted += 1

        db.commit()
        print(f"\n清理完成！")
        print(f"共处理 {total_docs} 个文档")
        print(f"共删除 {total_deleted} 个重复任务")

    except Exception as e:
        db.rollback()
        print(f"清理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicate_tasks()
