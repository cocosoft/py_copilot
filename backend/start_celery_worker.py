#!/usr/bin/env python3
"""
启动 Celery Worker（内存模式）

使用方法:
    python start_celery_worker.py

环境变量:
    CELERY_USE_MEMORY: 设置为 true 使用内存模式
    CELERY_LOG_LEVEL: 日志级别 (默认: info)
    CELERY_QUEUES: 队列列表，逗号分隔 (默认: knowledge_processing,default)
"""

import os
import sys

# 设置内存模式
os.environ['CELERY_USE_MEMORY'] = 'true'

# 获取配置
log_level = os.getenv('CELERY_LOG_LEVEL', 'info')
queues = os.getenv('CELERY_QUEUES', 'knowledge_processing,default')

print('='*60)
print('启动 Celery Worker（内存模式）')
print('='*60)
print(f'日志级别: {log_level}')
print(f'队列: {queues}')
print('='*60)
print()

# 使用 subprocess 启动 celery
import subprocess

cmd = [
    sys.executable, '-m', 'celery',
    '-A', 'celery_app',
    'worker',
    '--loglevel=' + log_level,
    '-Q', queues
]

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print('\n\nWorker 已停止')
    sys.exit(0)
