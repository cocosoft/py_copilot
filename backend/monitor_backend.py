#!/usr/bin/env python3
"""监测后端运行状态"""

import requests
import psutil
import time
import json
from datetime import datetime

def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_backend():
    """检查后端状态"""
    try:
        # 检查系统状态
        r = requests.get('http://127.0.0.1:8010/api/v1/system/status', timeout=5)
        if r.status_code == 200:
            data = r.json()
            log(f"✓ 后端运行正常")
            log(f"  内存使用: {data.get('memory_usage', 'N/A')}")
            log(f"  数据库连接: {data.get('database_connections', 'N/A')}")
            return True
        else:
            log(f"✗ 后端状态异常: {r.status_code}")
            return False
    except Exception as e:
        log(f"✗ 后端连接失败: {e}")
        return False

def check_document_api():
    """检查文档API"""
    try:
        r = requests.get('http://127.0.0.1:8010/api/v1/knowledge/documents/102', timeout=10)
        if r.status_code == 200:
            data = r.json()
            log(f"✓ 文档API正常")
            log(f"  文档: {data.get('title')}")
            log(f"  分块数: {data.get('chunk_count')}")
            return True
        else:
            log(f"✗ 文档API异常: {r.status_code}")
            return False
    except Exception as e:
        log(f"✗ 文档API错误: {e}")
        return False

def check_entity_extraction_api():
    """检查实体提取API"""
    try:
        # 测试获取任务状态（不存在的任务）
        r = requests.get('http://127.0.0.1:8010/api/v1/knowledge/documents/102/extract-chunk-entities/status/test-task-id', timeout=5)
        # 404 表示API可用但任务不存在，这是正常的
        if r.status_code in [200, 404]:
            log(f"✓ 实体提取API正常 (状态码: {r.status_code})")
            return True
        else:
            log(f"✗ 实体提取API异常: {r.status_code}")
            return False
    except Exception as e:
        log(f"✗ 实体提取API错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("后端运行状态监测")
    print("=" * 60)
    print()
    
    # 等待后端启动
    log("等待后端启动...")
    for i in range(60):  # 最多等待2分钟
        if check_backend():
            break
        time.sleep(2)
    else:
        log("✗ 后端启动超时")
        return
    
    print()
    print("-" * 60)
    
    # 检查文档API
    check_document_api()
    
    print()
    print("-" * 60)
    
    # 检查实体提取API
    check_entity_extraction_api()
    
    print()
    print("=" * 60)
    log("监测完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
