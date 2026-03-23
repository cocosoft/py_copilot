"""
重置文档状态并重新处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 先导入所有模型
from app.modules.knowledge.models.knowledge_document import *
from app.core.database import SessionLocal

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_document_status(doc_id: int):
    """重置文档处理状态"""
    db = SessionLocal()
    try:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            logger.error(f"文档 {doc_id} 不存在")
            return False

        # 重置处理状态
        if doc.document_metadata is None:
            doc.document_metadata = {}

        doc.document_metadata["processing_status"] = "pending"
        doc.document_metadata["vectorization_rate"] = 0
        doc.document_metadata["success_count"] = 0
        doc.document_metadata["total_chunks"] = 0
        doc.document_metadata["chunks_count"] = 0

        # 标记为已修改
        from sqlalchemy.orm import attributes
        attributes.flag_modified(doc, "document_metadata")

        db.commit()
        db.refresh(doc)

        logger.info(f"✓ 文档 {doc_id} 状态已重置为 pending")
        return True
    except Exception as e:
        logger.error(f"重置文档状态失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def delete_document_chunks(doc_id: int):
    """删除文档的分块"""
    db = SessionLocal()
    try:
        count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc_id
        ).delete(synchronize_session=False)
        db.commit()
        logger.info(f"✓ 已删除 {count} 个旧分块")
        return True
    except Exception as e:
        logger.error(f"删除分块失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def trigger_reprocess(doc_id: int):
    """触发重新处理"""
    import requests

    url = f"http://localhost:8009/api/v1/knowledge/documents/{doc_id}/process"
    try:
        resp = requests.post(url, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            logger.info(f"✓ 重新处理已启动: {result}")
            return True
        else:
            logger.error(f"启动重新处理失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logger.error(f"请求失败: {e}")
        return False


def check_status(doc_id: int):
    """检查文档状态"""
    import requests
    import time

    url = f"http://localhost:8009/api/v1/knowledge/documents/{doc_id}"
    chunks_url = f"http://localhost:8009/api/v1/knowledge/documents/{doc_id}/chunks"

    for i in range(30):  # 最多等待150秒
        try:
            # 检查文档状态
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                doc = resp.json()
                status = doc.get("document_metadata", {}).get("processing_status", "unknown")
                logger.info(f"  文档状态: {status}")

                if status == "completed":
                    # 检查分块
                    chunks_resp = requests.get(chunks_url, timeout=5)
                    if chunks_resp.status_code == 200:
                        chunks = chunks_resp.json()
                        logger.info(f"  ✓ 分块数量: {len(chunks)}")
                        return len(chunks)
                    return 0

                if status == "failed":
                    logger.error("  ✗ 处理失败")
                    return -1

            time.sleep(5)
        except Exception as e:
            logger.error(f"  检查状态失败: {e}")
            time.sleep(5)

    logger.warning("  等待超时")
    return -2


def main():
    doc_id = 102  # 《三体》文档ID

    print("=" * 70)
    print("重置并重新处理文档")
    print("=" * 70)

    # 1. 删除旧分块
    print(f"\n[1] 删除文档 {doc_id} 的旧分块...")
    delete_document_chunks(doc_id)

    # 2. 重置文档状态
    print(f"\n[2] 重置文档 {doc_id} 状态...")
    if not reset_document_status(doc_id):
        print("✗ 重置状态失败")
        return

    # 3. 触发重新处理
    print(f"\n[3] 触发重新处理...")
    if not trigger_reprocess(doc_id):
        print("✗ 触发重新处理失败")
        return

    # 4. 等待处理完成
    print(f"\n[4] 等待处理完成...")
    chunk_count = check_status(doc_id)

    print("\n" + "=" * 70)
    if chunk_count > 0:
        print(f"✅ 成功！文档已重新处理，共有 {chunk_count} 个分块")
    elif chunk_count == 0:
        print("⚠️ 处理完成，但没有分块")
    else:
        print("✗ 处理失败或超时")
    print("=" * 70)


if __name__ == "__main__":
    main()
