#!/usr/bin/env python3
"""
数据库迁移脚本：为现有文档添加UUID
"""
import sqlite3
import uuid
import os

def migrate_add_uuid():
    """为现有文档添加UUID字段"""
    db_path = os.path.join(os.path.dirname(__file__), "backend", "py_copilot.db")
    print(f"数据库路径: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 检查uuid字段是否存在
        cursor.execute("PRAGMA table_info(knowledge_documents)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'uuid' not in columns:
            print("\n添加uuid字段...")
            cursor.execute("ALTER TABLE knowledge_documents ADD COLUMN uuid VARCHAR(40)")
            conn.commit()
            print("✓ uuid字段已添加")
        else:
            print("\nuuid字段已存在")

        # 2. 为现有文档生成UUID
        print("\n为现有文档生成UUID...")
        cursor.execute("SELECT id FROM knowledge_documents WHERE uuid IS NULL")
        docs_without_uuid = cursor.fetchall()

        if docs_without_uuid:
            print(f"  需要生成UUID的文档数: {len(docs_without_uuid)}")
            for (doc_id,) in docs_without_uuid:
                new_uuid = f"doc-{uuid.uuid4()}"
                cursor.execute(
                    "UPDATE knowledge_documents SET uuid = ? WHERE id = ?",
                    (new_uuid, doc_id)
                )
            conn.commit()
            print(f"✓ 已为 {len(docs_without_uuid)} 个文档生成UUID")
        else:
            print("  所有文档已有UUID")

        # 3. 创建uuid唯一索引
        print("\n创建uuid索引...")
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_knowledge_documents_uuid ON knowledge_documents(uuid)")
            conn.commit()
            print("✓ uuid索引已创建")
        except Exception as e:
            print(f"  索引创建失败（可能已存在）: {e}")

        # 4. 验证结果
        print("\n验证结果...")
        cursor.execute("SELECT COUNT(*) FROM knowledge_documents")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM knowledge_documents WHERE uuid IS NOT NULL")
        with_uuid = cursor.fetchone()[0]

        print(f"  总文档数: {total}")
        print(f"  有UUID的文档数: {with_uuid}")

        if total == with_uuid:
            print("\n✓ 迁移完成！")
        else:
            print(f"\n⚠ 警告: 有 {total - with_uuid} 个文档没有UUID")

        conn.close()
        return True

    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移：添加UUID字段")
    print("=" * 60)
    migrate_add_uuid()
