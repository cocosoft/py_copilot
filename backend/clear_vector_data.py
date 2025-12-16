#!/usr/bin/env python3
"""
清空向量数据库中的所有数据
用于测试目的
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.knowledge.chroma_service import ChromaService

def clear_vector_data():
    """清空向量数据库中的所有数据"""
    print("正在初始化ChromaService...")
    chroma_service = ChromaService()
    
    if not chroma_service.available or chroma_service.collection is None:
        print("错误: ChromaDB初始化失败，无法清空数据")
        return False
    
    try:
        print("正在获取当前向量数据数量...")
        current_count = chroma_service.get_document_count()
        print(f"当前向量数据库中有 {current_count} 条数据")
        
        if current_count == 0:
            print("向量数据库已经是空的，无需清空")
            return True
        
        print("正在获取所有文档ID...")
        # 获取所有文档ID
        all_documents = chroma_service.list_documents(limit=10000)  # 设置一个足够大的限制
        all_ids = [doc['id'] for doc in all_documents]
        
        print(f"获取到 {len(all_ids)} 个文档ID，正在删除...")
        
        # 批量删除所有文档
        if all_ids:
            chroma_service.collection.delete(ids=all_ids)
        
        # 验证清空结果
        new_count = chroma_service.get_document_count()
        if new_count == 0:
            print("成功: 向量数据库已清空")
            return True
        else:
            print(f"警告: 清空后仍有 {new_count} 条数据")
            return False
            
    except Exception as e:
        print(f"错误: 清空向量数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = clear_vector_data()
    sys.exit(0 if success else 1)
