#!/usr/bin/env python3
"""
检查文档状态与向量数据库的一致性
"""
import requests
import json

def check_consistency():
    # 1. 获取所有知识库
    kb_resp = requests.get('http://127.0.0.1:8000/api/v1/knowledge/knowledge-bases?skip=0&limit=100')
    kbs_data = kb_resp.json()
    # 处理不同的响应格式
    if isinstance(kbs_data, list):
        kbs = kbs_data
    elif isinstance(kbs_data, dict) and 'knowledge_bases' in kbs_data:
        kbs = kbs_data['knowledge_bases']
    else:
        kbs = []
    
    print('=== 知识库列表 ===')
    for kb in kbs:
        print(f"ID: {kb['id']}, Name: {kb['name']}")

    # 2. 获取第一个知识库的所有文档
    docs_resp = requests.get('http://127.0.0.1:8000/api/v1/knowledge/documents?knowledge_base_id=1&skip=0&limit=1000')
    docs_data = docs_resp.json()
    # 处理不同的响应格式
    if isinstance(docs_data, dict) and 'documents' in docs_data:
        docs = docs_data
    elif isinstance(docs_data, list):
        docs = {'documents': docs_data, 'total': len(docs_data)}
    else:
        docs = {'documents': [], 'total': 0}
    
    print(f"\n=== Knowledge Base 1 Documents ({docs.get('total', 0)}) ===")

    completed = 0
    not_completed = 0
    has_vector_id = 0
    no_vector_id = 0
    
    # 检查状态与vector_id的一致性
    inconsistent = []
    
    for doc in docs.get('documents', []):
        metadata = doc.get('document_metadata', {}) or {}
        status = metadata.get('processing_status', 'unknown')
        vector_id = doc.get('vector_id')
        
        if status == 'completed':
            completed += 1
        else:
            not_completed += 1
            
        if vector_id:
            has_vector_id += 1
        else:
            no_vector_id += 1
        
        # 检查不一致：状态为completed但没有vector_id，或状态不是completed但有vector_id
        if status == 'completed' and not vector_id:
            inconsistent.append({
                'id': doc['id'],
                'title': doc['title'],
                'issue': 'Status is completed but no vector_id',
                'status': status,
                'vector_id': vector_id
            })
        elif status != 'completed' and vector_id:
            inconsistent.append({
                'id': doc['id'],
                'title': doc['title'],
                'issue': 'Status is NOT completed but has vector_id',
                'status': status,
                'vector_id': vector_id
            })
        
        print(f"  ID:{doc['id']} Status:{status} vector_id:{vector_id}")

    print(f"\n=== Statistics ===")
    print(f"Completed: {completed}")
    print(f"Not Completed: {not_completed}")
    print(f"Has vector_id: {has_vector_id}")
    print(f"No vector_id: {no_vector_id}")
    
    # 分类统计不一致
    completed_no_vector = [i for i in inconsistent if i['issue'] == 'Status is completed but no vector_id']
    not_completed_has_vector = [i for i in inconsistent if i['issue'] == 'Status is NOT completed but has vector_id']
    
    print(f"\n=== Inconsistencies ({len(inconsistent)}) ===")
    print(f"  1. Status completed but no vector_id: {len(completed_no_vector)}")
    print(f"  2. Status NOT completed but has vector_id: {len(not_completed_has_vector)}")
    
    if not_completed_has_vector:
        print(f"\n=== Details: Status NOT completed but has vector_id ===")
        for item in not_completed_has_vector[:10]:  # 只显示前10个
            print(f"  Doc {item['id']} ({item['title'][:50]}...)")
            print(f"    Status: {item['status']}, Vector ID: {item['vector_id']}")
        if len(not_completed_has_vector) > 10:
            print(f"    ... and {len(not_completed_has_vector) - 10} more")

if __name__ == '__main__':
    check_consistency()
