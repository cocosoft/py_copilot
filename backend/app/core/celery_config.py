#!/usr/bin/env python3
"""
Celery配置模块

提供异步任务队列的配置和管理
"""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from datetime import timedelta
import logging
import os

logger = logging.getLogger(__name__)

# Celery应用实例
celery_app = None


def create_celery_app(app_name: str = "knowledge_graph") -> Celery:
    """
    创建Celery应用实例

    Args:
        app_name: 应用名称

    Returns:
        Celery应用实例
    """
    global celery_app

    # 检查是否使用内存模式（开发/测试环境）
    use_memory = os.getenv("CELERY_USE_MEMORY", "false").lower() == "true"
    
    if use_memory:
        # 使用内存中的Redis替代方案（fakeredis）
        logger.info("使用内存模式（fakeredis）启动Celery")
        broker_url = "memory://"
        backend_url = "cache+memory://"
    else:
        # 从环境变量获取Redis配置
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_db = os.getenv("REDIS_DB", "0")
        redis_password = os.getenv("REDIS_PASSWORD", "")

        # 构建Redis URL
        if redis_password:
            broker_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
            backend_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{int(redis_db) + 1}"
        else:
            broker_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
            backend_url = f"redis://{redis_host}:{redis_port}/{int(redis_db) + 1}"

    celery_app = Celery(
        app_name,
        broker=broker_url,
        backend=backend_url,
        include=[
            'app.tasks.knowledge_graph_tasks',
            'app.tasks.entity_extraction_tasks',
            'app.tasks.entity_alignment_tasks',
            'app.tasks.knowledge.document_processing',
        ]
    )

    # 配置Celery
    celery_app.conf.update(
        # 任务序列化
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',

        # 时区设置
        timezone='Asia/Shanghai',
        enable_utc=True,

        # 任务执行设置
        task_track_started=True,
        task_time_limit=3600,  # 任务超时时间1小时
        task_soft_time_limit=3300,  # 软超时55分钟

        # 结果后端设置
        result_expires=timedelta(days=7),  # 结果保存7天
        result_extended=True,

        # 工作进程设置
        worker_prefetch_multiplier=1,  # 每次预取1个任务
        worker_max_tasks_per_child=1000,  # 每个worker处理1000个任务后重启

        # 任务路由
        task_routes={
            'app.tasks.knowledge_graph_tasks.*': {'queue': 'knowledge_graph'},
            'app.tasks.entity_extraction_tasks.*': {'queue': 'extraction'},
            'app.tasks.entity_alignment_tasks.*': {'queue': 'alignment'},
            'app.tasks.knowledge.document_processing.*': {'queue': 'knowledge_processing'},
        },

        # 任务默认队列
        task_default_queue='default',

        # 任务重试设置
        task_default_retry_delay=60,  # 默认60秒后重试
        task_max_retries=3,  # 最大重试3次

        # 监控设置
        worker_send_task_events=True,
        task_send_sent_event=True,
    )

    logger.info(f"Celery应用创建成功: {app_name}")
    if use_memory:
        logger.info(f"Broker: {broker_url}")
    else:
        logger.info(f"Broker: {broker_url.replace(redis_password, '***') if redis_password else broker_url}")

    # 注册定时任务
    register_periodic_tasks(celery_app)

    return celery_app


def get_celery_app() -> Celery:
    """获取Celery应用实例"""
    global celery_app
    if celery_app is None:
        celery_app = create_celery_app()
    return celery_app


# ============== 任务信号处理 ==============

@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extras):
    """任务开始前的处理"""
    logger.info(f"任务开始执行: {task.name}[{task_id}]")


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, state, **extras):
    """任务完成后的处理"""
    logger.info(f"任务执行完成: {task.name}[{task_id}], 状态: {state}")


@task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **extras):
    """任务失败时的处理"""
    logger.error(f"任务执行失败: {task_id}, 异常: {exception}")


# ============== 定时任务配置 ==============

def setup_periodic_tasks(sender, **kwargs):
    """设置定时任务"""
    # 每小时清理过期任务结果
    sender.add_periodic_task(
        timedelta(hours=1),
        cleanup_expired_results.s(),
        name='cleanup-expired-results'
    )

    # 每天凌晨进行系统维护
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        system_maintenance.s(),
        name='system-maintenance'
    )


from celery.schedules import crontab


# ============== 系统任务（占位符，在create_celery_app后注册） ==============

def register_periodic_tasks(app: Celery):
    """注册定时任务"""
    
    @app.on_after_configure.connect
    def setup_periodic_tasks_connect(sender, **kwargs):
        """连接定时任务配置"""
        # 每小时清理过期任务结果
        sender.add_periodic_task(
            timedelta(hours=1),
            cleanup_expired_results.s(),
            name='cleanup-expired-results'
        )
        
        # 每天凌晨进行系统维护
        sender.add_periodic_task(
            crontab(hour=2, minute=0),
            system_maintenance.s(),
            name='system-maintenance'
        )
    
    @app.task(bind=True)
    def cleanup_expired_results(self):
        """清理过期的任务结果"""
        try:
            logger.info("开始清理过期任务结果")
            return {"status": "success", "message": "过期结果已清理"}
        except Exception as e:
            logger.error(f"清理过期结果失败: {e}")
            return {"status": "error", "message": str(e)}
    
    @app.task(bind=True)
    def system_maintenance(self):
        """系统维护任务"""
        try:
            logger.info("开始系统维护")
            return {"status": "success", "message": "系统维护完成"}
        except Exception as e:
            logger.error(f"系统维护失败: {e}")
            return {"status": "error", "message": str(e)}
    
    return cleanup_expired_results, system_maintenance
