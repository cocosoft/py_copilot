#!/usr/bin/env python3
"""
Celery应用入口文件

用于启动Celery Worker和Beat

使用方法:
    # 启动Worker
    celery -A celery_app worker --loglevel=info
    
    # 启动Worker（指定队列）
    celery -A celery_app worker --loglevel=info -Q knowledge_processing
    
    # 启动Beat（定时任务）
    celery -A celery_app beat --loglevel=info
    
    # 同时启动Worker和Beat
    celery -A celery_app worker --loglevel=info --beat
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入环境变量配置
from app.core.env_config import *

# 创建Celery应用
from app.core.celery_config import create_celery_app

celery = create_celery_app("knowledge_base")

# 自动发现任务
celery.autodiscover_tasks([
    'app.tasks.knowledge_graph_tasks',
    'app.tasks.entity_extraction_tasks',
    'app.tasks.entity_alignment_tasks',
    'app.tasks.knowledge',
])

if __name__ == '__main__':
    celery.start()
