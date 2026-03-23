# -*- coding: utf-8 -*-
"""检测文件编码"""
import os

# 检查两个txt文件的编码
files = [
    r'e:\PY\CODES\py copilot IV\frontend\public\knowledges\knowledge_base_2\f05e853b-d06b-4fdf-89cf-9d97d7619b2f_金麟QI SHI池中物.txt',
    r'e:\PY\CODES\py copilot IV\frontend\public\knowledges\knowledge_base_2\255bf992-d96a-48b6-99d7-3174f74620be_小女人的幸福.txt'
]

# 常见编码列表
encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1', 'utf-16']

for file_path in files:
    try:
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        print(f"文件: {file_name}")
        print(f"  大小: {file_size / 1024 / 1024:.2f} MB")
        
        # 尝试不同的编码
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(200)
                    print(f"  成功解码: {encoding}")
                    print(f"  前100字符: {content[:100]}")
                    break
            except UnicodeDecodeError:
                continue
        else:
            print(f"  所有编码都失败")
        print()
    except Exception as e:
        print(f"文件: {os.path.basename(file_path)}")
        print(f"  错误: {e}")
        print()
