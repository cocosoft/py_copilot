#!/usr/bin/env python3
"""监测实体提取任务运行情况"""

import requests
import json
import time
import sys
from datetime import datetime

base_url = "http://127.0.0.1:8010/api/v1"

def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def create_task(document_id=102, max_workers=4):
    """创建实体提取任务"""
    url = f"{base_url}/knowledge/documents/{document_id}/extract-chunk-entities?max_workers={max_workers}"
    log(f"创建任务: {url}")
    
    try:
        response = requests.post(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            log(f"✓ 任务创建成功: {task_id}")
            return task_id
        else:
            log(f"✗ 创建任务失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        log(f"✗ 创建任务异常: {e}")
        return None

def check_task_status(document_id, task_id):
    """检查任务状态"""
    url = f"{base_url}/knowledge/documents/{document_id}/extract-chunk-entities/status/{task_id}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            log(f"✗ 获取状态失败: {response.status_code}")
            return None
    except Exception as e:
        log(f"✗ 获取状态异常: {e}")
        return None

def monitor_task(document_id=102, task_id=None, max_polls=300):
    """监测任务直到完成"""
    if task_id is None:
        task_id = create_task(document_id)
        if task_id is None:
            return False
    
    log(f"开始监测任务: {task_id}")
    log("-" * 60)
    
    poll_count = 0
    last_status = None
    last_progress = -1
    
    while poll_count < max_polls:
        status = check_task_status(document_id, task_id)
        
        if status is None:
            poll_count += 1
            time.sleep(2)
            continue
        
        current_status = status.get('status')
        current_progress = status.get('progress', 0)
        message = status.get('message', '')
        completed = status.get('completed_chunks', 0)
        total = status.get('total_chunks', 0)
        failed = status.get('failed_chunks', 0)
        
        # 只在状态或进度变化时打印
        if current_status != last_status or current_progress != last_progress:
            log(f"状态: {current_status:12} | 进度: {current_progress:3}% | "
                f"片段: {completed}/{total} | 失败: {failed} | {message}")
            last_status = current_status
            last_progress = current_progress
        
        # 检查是否完成
        if current_status in ['completed', 'failed']:
            log("-" * 60)
            if current_status == 'completed':
                log(f"✓ 任务完成! 总片段: {total}, 完成: {completed}, 失败: {failed}")
                if status.get('result'):
                    result = status['result']
                    log(f"  提取实体数: {result.get('total_entities', 0)}")
                    log(f"  处理耗时: {result.get('processing_time', 0):.2f}秒")
            else:
                log(f"✗ 任务失败: {status.get('error', '未知错误')}")
            return current_status == 'completed'
        
        poll_count += 1
        time.sleep(2)
    
    log(f"✗ 监测超时，已轮询 {max_polls} 次")
    return False

def check_system_status():
    """检查系统状态"""
    log("=" * 60)
    log("检查系统状态")
    log("=" * 60)
    
    # 检查健康状态
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            log(f"✓ 系统健康: {response.json()}")
        else:
            log(f"✗ 健康检查失败: {response.status_code}")
    except Exception as e:
        log(f"✗ 健康检查异常: {e}")
    
    # 检查文档状态
    try:
        response = requests.get(f"{base_url}/knowledge/documents/102", timeout=5)
        if response.status_code == 200:
            doc = response.json()
            log(f"✓ 文档信息: ID={doc.get('id')}, 标题={doc.get('title')}")
            log(f"  状态: {doc.get('status')}, 分块数: {doc.get('chunk_count')}")
        else:
            log(f"✗ 获取文档失败: {response.status_code}")
    except Exception as e:
        log(f"✗ 获取文档异常: {e}")
    
    log("")

if __name__ == "__main__":
    log("=" * 60)
    log("实体提取任务监测工具")
    log("=" * 60)
    log("")
    
    # 检查系统状态
    check_system_status()
    
    # 监测任务
    success = monitor_task(document_id=102)
    
    log("")
    log("=" * 60)
    if success:
        log("监测完成: 任务成功")
    else:
        log("监测完成: 任务失败或超时")
    log("=" * 60)
