#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步ChromaDB和数据库状态
将ChromaDB中已向量化的文档标记为completed
"""

import sqlite3
import json
import os


def sync_vectorized_status():
    """同步向量化状态"""
    
    # 读取已向量化的文档ID
    with open('vectorized_docs.json', 'r') as f:
        data = json.load(f)
        vectorized_ids = data['document_ids']
    
    print(f'ChromaDB中已向量化的文档ID数量: {len(vectorized_ids)}')
    
    # 连接数据库
    conn = sqlite3.connect('py_copilot.db')
    cursor = conn.cursor()
    
    # 更新这些文档的状态为completed
    updated_count = 0
    for doc_id in vectorized_ids:
        # 先查询当前metadata
        cursor.execute('SELECT document_metadata FROM knowledge_documents WHERE id = ?', (doc_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            try:
                metadata = json.loads(result[0])
            except:
                metadata = {}
        else:
            metadata = {}
        
        # 更新状态
        metadata['processing_status'] = 'completed'
        metadata['vectorization_rate'] = 1.0
        metadata['success_count'] = 1
        
        # 更新数据库
        cursor.execute(
            'UPDATE knowledge_documents SET document_metadata = ?, is_vectorized = 1 WHERE id = ?',
            (json.dumps(metadata), doc_id)
        )
        updated_count += 1
    
    # 提交事务
    conn.commit()
    
    print(f'已更新文档数量: {updated_count}')
    
    # 验证更新结果
    cursor.execute('''SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN json_extract(document_metadata, '$.processing_status') = 'completed' THEN 1 ELSE 0 END) as completed
    FROM knowledge_documents WHERE knowledge_base_id = 1''')
    result = cursor.fetchone()
    print(f'\n验证结果:')
    print(f'  总文档数: {result[0]}')
    print(f'  已完成: {result[1]}')
    
    conn.close()
    print('\n数据库更新完成！')


if __name__ == '__main__':
    sync_vectorized_status()
