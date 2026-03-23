#!/usr/bin/env python3
"""
通用文档重新切片工具

用于重新切分知识库中的文档，支持自定义切片参数。
适用于大文件切片优化、切片策略调整等场景。

使用方法:
    python rechunk_tool.py --doc-id 102
    python rechunk_tool.py --doc-id 102 --max-size 2000 --min-size 400
    python rechunk_tool.py --all
"""

import re
import json
import sys
import argparse
sys.path.insert(0, 'e:\\PY\\CODES\\py copilot IV\\backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 连接数据库
engine = create_engine('sqlite:///py_copilot.db')
Session = sessionmaker(bind=engine)


def simple_chunking(text: str, max_chunk_size: int = 1500,
                    min_chunk_size: int = 300, overlap: int = 100) -> list:
    """
    基于规则的简单分块方法

    使用滑动窗口和句子边界检测，确保切片大小均匀且语义完整。

    Args:
        text: 输入文本
        max_chunk_size: 最大块大小（字符数）
        min_chunk_size: 最小块大小（字符数）
        overlap: 块之间的重叠大小（字符数）

    Returns:
        分块后的文本列表，每个元素包含text、start、end
    """
    if not text:
        return []

    if len(text) <= max_chunk_size:
        return [{'text': text, 'start': 0, 'end': len(text)}]

    chunks = []
    position = 0

    while position < len(text):
        # 计算当前块的结束位置
        end_pos = min(position + max_chunk_size, len(text))

        # 如果不是最后一块，尝试在句子边界处分割
        if end_pos < len(text):
            # 向前查找句子结束标记
            search_start = end_pos - 100  # 往回搜索100个字符
            if search_start < position:
                search_start = position

            search_text = text[search_start:end_pos + 100]

            # 查找最后一个句子结束标记
            sentence_ends = []
            for i, char in enumerate(search_text):
                if char in '.!?。！？':
                    actual_pos = search_start + i + 1
                    if actual_pos > position + min_chunk_size:
                        sentence_ends.append(actual_pos)

            if sentence_ends:
                end_pos = sentence_ends[-1]

        # 提取块文本
        chunk_text = text[position:end_pos].strip()

        if chunk_text:
            chunks.append({
                'text': chunk_text,
                'start': position,
                'end': end_pos
            })

        # 移动位置，考虑重叠
        position = end_pos
        if overlap > 0 and position < len(text):
            position = max(position - overlap, position)

    return chunks


def rechunk_document(document_id: int, max_chunk_size: int = 1500,
                     min_chunk_size: int = 300, overlap: int = 100,
                     dry_run: bool = False) -> bool:
    """
    重新切片单个文档

    Args:
        document_id: 文档ID
        max_chunk_size: 最大切片大小
        min_chunk_size: 最小切片大小
        overlap: 重叠大小
        dry_run: 是否只预览不执行

    Returns:
        是否成功
    """
    db = Session()

    try:
        # 1. 获取文档内容
        result = db.execute(text("""
            SELECT id, content, title, knowledge_base_id
            FROM knowledge_documents
            WHERE id = :doc_id
        """), {"doc_id": document_id})
        doc = result.fetchone()

        if not doc:
            print(f"❌ 未找到文档 ID {document_id}")
            return False

        content = doc.content
        print(f"\n{'='*60}")
        print(f"📄 文档: {doc.title}")
        print(f"🆔 ID: {document_id}")
        print(f"📊 内容长度: {len(content):,} 字符")
        print(f"{'='*60}")

        # 2. 获取旧切片信息
        result = db.execute(text("""
            SELECT COUNT(*) as count,
                   AVG(LENGTH(chunk_text)) as avg_length,
                   MAX(LENGTH(chunk_text)) as max_length,
                   MIN(LENGTH(chunk_text)) as min_length
            FROM document_chunks
            WHERE document_id = :doc_id
        """), {"doc_id": document_id})
        old_stats = result.fetchone()

        if old_stats and old_stats.count > 0:
            print(f"\n📦 旧切片统计:")
            print(f"   数量: {old_stats.count}")
            print(f"   平均: {old_stats.avg_length:.0f} 字符")
            print(f"   最大: {old_stats.max_length} 字符")
            print(f"   最小: {old_stats.min_length} 字符")

        # 3. 预览新切片
        print(f"\n🔧 切片参数:")
        print(f"   最大切片: {max_chunk_size} 字符")
        print(f"   最小切片: {min_chunk_size} 字符")
        print(f"   重叠大小: {overlap} 字符")

        chunks = simple_chunking(content, max_chunk_size, min_chunk_size, overlap)

        print(f"\n📦 新切片预览:")
        print(f"   数量: {len(chunks)}")
        if chunks:
            sizes = [len(c['text']) for c in chunks]
            print(f"   平均: {sum(sizes) // len(sizes)} 字符")
            print(f"   最大: {max(sizes)} 字符")
            print(f"   最小: {min(sizes)} 字符")

        if dry_run:
            print(f"\n⚠️  预览模式，未实际执行")
            return True

        # 4. 删除旧切片
        print(f"\n🗑️  删除旧切片...")
        result = db.execute(text("""
            DELETE FROM document_chunks
            WHERE document_id = :doc_id
        """), {"doc_id": document_id})
        deleted_count = result.rowcount
        print(f"   删除了 {deleted_count} 个旧切片")

        # 5. 删除旧实体
        print(f"\n🗑️  删除旧实体...")
        result = db.execute(text("""
            DELETE FROM chunk_entities
            WHERE document_id = :doc_id
        """), {"doc_id": document_id})
        deleted_entities = result.rowcount
        print(f"   删除了 {deleted_entities} 个旧实体")

        # 6. 保存新切片
        print(f"\n💾 保存新切片...")
        now = datetime.now().isoformat()

        for i, chunk_data in enumerate(chunks):
            chunk_text = chunk_data['text']
            start_pos = chunk_data['start']
            end_pos = chunk_data['end']

            # 准备元数据
            metadata = json.dumps({
                'char_count': len(chunk_text),
                'word_count': len(chunk_text.split()),
                'paragraph_count': chunk_text.count('\n\n') + 1
            })

            db.execute(text("""
                INSERT INTO document_chunks
                (document_id, chunk_index, chunk_text, start_pos, end_pos,
                 total_chunks, is_vectorized, created_at, chunk_metadata)
                VALUES (:doc_id, :index, :text, :start_pos, :end_pos,
                        :total_chunks, 0, :created_at, :metadata)
            """), {
                "doc_id": document_id,
                "index": i,
                "text": chunk_text,
                "start_pos": start_pos,
                "end_pos": end_pos,
                "total_chunks": len(chunks),
                "created_at": now,
                "metadata": metadata
            })

        # 7. 更新文档信息
        db.execute(text("""
            UPDATE knowledge_documents
            SET updated_at = :updated_at
            WHERE id = :doc_id
        """), {
            "updated_at": now,
            "doc_id": document_id
        })

        db.commit()

        print(f"\n✅ 重新切片成功！")
        return True

    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def rechunk_all_documents(max_chunk_size: int = 1500,
                          min_chunk_size: int = 300,
                          overlap: int = 100,
                          dry_run: bool = False) -> bool:
    """
    重新切片所有文档

    Args:
        max_chunk_size: 最大切片大小
        min_chunk_size: 最小切片大小
        overlap: 重叠大小
        dry_run: 是否只预览不执行

    Returns:
        是否全部成功
    """
    db = Session()

    try:
        # 获取所有文档
        result = db.execute(text("""
            SELECT id, title, LENGTH(content) as content_length
            FROM knowledge_documents
            ORDER BY id
        """))
        documents = result.fetchall()

        if not documents:
            print("❌ 未找到任何文档")
            return False

        print(f"\n📚 找到 {len(documents)} 个文档")
        print(f"{'='*60}")

        success_count = 0
        fail_count = 0

        for doc in documents:
            print(f"\n处理文档 {doc.id}: {doc.title}")
            if rechunk_document(doc.id, max_chunk_size, min_chunk_size, overlap, dry_run):
                success_count += 1
            else:
                fail_count += 1

        print(f"\n{'='*60}")
        print(f"📊 处理结果:")
        print(f"   成功: {success_count}")
        print(f"   失败: {fail_count}")
        print(f"   总计: {len(documents)}")

        return fail_count == 0

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='文档重新切片工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 重新切片指定文档
  python rechunk_tool.py --doc-id 102

  # 使用自定义参数重新切片
  python rechunk_tool.py --doc-id 102 --max-size 2000 --min-size 400 --overlap 150

  # 预览模式（不实际执行）
  python rechunk_tool.py --doc-id 102 --dry-run

  # 重新切片所有文档
  python rechunk_tool.py --all

  # 重新切片所有大文件（超过10万字符）
  python rechunk_tool.py --all --min-content 100000
        """
    )

    parser.add_argument('--doc-id', type=int, help='指定文档ID')
    parser.add_argument('--all', action='store_true', help='处理所有文档')
    parser.add_argument('--max-size', type=int, default=1500, help='最大切片大小（默认1500）')
    parser.add_argument('--min-size', type=int, default=300, help='最小切片大小（默认300）')
    parser.add_argument('--overlap', type=int, default=100, help='重叠大小（默认100）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际执行')
    parser.add_argument('--min-content', type=int, help='只处理内容长度超过此值的文档')

    args = parser.parse_args()

    if not args.doc_id and not args.all:
        parser.print_help()
        return

    if args.doc_id:
        # 处理单个文档
        success = rechunk_document(
            args.doc_id,
            args.max_size,
            args.min_size,
            args.overlap,
            args.dry_run
        )
        sys.exit(0 if success else 1)

    elif args.all:
        # 处理所有文档
        if args.min_content:
            # 只处理大文件
            db = Session()
            try:
                result = db.execute(text("""
                    SELECT id, title, LENGTH(content) as content_length
                    FROM knowledge_documents
                    WHERE LENGTH(content) > :min_content
                    ORDER BY id
                """), {"min_content": args.min_content})
                documents = result.fetchall()

                if not documents:
                    print(f"❌ 未找到内容长度超过 {args.min_content} 的文档")
                    return

                print(f"\n📚 找到 {len(documents)} 个大文件（>{args.min_content}字符）")
                print(f"{'='*60}")

                success_count = 0
                fail_count = 0

                for doc in documents:
                    print(f"\n处理文档 {doc.id}: {doc.title} ({doc.content_length}字符)")
                    if rechunk_document(doc.id, args.max_size, args.min_size, args.overlap, args.dry_run):
                        success_count += 1
                    else:
                        fail_count += 1

                print(f"\n{'='*60}")
                print(f"📊 处理结果:")
                print(f"   成功: {success_count}")
                print(f"   失败: {fail_count}")
                print(f"   总计: {len(documents)}")

            finally:
                db.close()
        else:
            # 处理所有文档
            success = rechunk_all_documents(
                args.max_size,
                args.min_size,
                args.overlap,
                args.dry_run
            )
            sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
