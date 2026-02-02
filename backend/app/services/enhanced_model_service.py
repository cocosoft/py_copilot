"""增强的模型管理服务

提供模型性能监控和智能切换功能
"""
import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import random

from app.core.task_queue import (
    submit_task,
    TaskPriority,
    TaskStatus
)
from app.services.model_query_service import model_query_service
from app.api.dependencies import get_db

logger = logging.getLogger(__name__)


class ModelHealthStatus(Enum):
    """模型健康状态"""
    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 性能下降
    UNHEALTHY = "unhealthy"  # 不健康
    DOWN = "down"  # 不可用


@dataclass
class ModelPerformanceMetrics:
    """模型性能指标"""
    model_id: str
    model_name: str
    supplier_id: int
    supplier_name: str
    
    # 响应时间指标
    response_times: List[float] = field(default_factory=list)
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p95_response_time: float = 0.0
    
    # 成功率指标
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 0.0
    
    # 性能指标
    tokens_per_second: List[float] = field(default_factory=list)
    avg_tokens_per_second: float = 0.0
    
    # 健康状态
    health_status: ModelHealthStatus = ModelHealthStatus.HEALTHY
    last_checked: Optional[datetime] = None
    
    # 时间窗口
    metrics_window: timedelta = timedelta(minutes=5)
    
    def add_metrics(
        self,
        response_time: float,
        success: bool,
        tokens_generated: Optional[int] = None
    ):
        """
        添加性能指标
        
        Args:
            response_time: 响应时间（秒）
            success: 是否成功
            tokens_generated: 生成的token数
        """
        # 添加响应时间
        self.response_times.append(response_time)
        
        # 更新请求统计
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # 计算tokens/s
        if success and tokens_generated and response_time > 0:
            self.tokens_per_second.append(tokens_generated / response_time)
        
        # 更新统计指标
        self._update_statistics()
        
        # 更新健康状态
        self._update_health_status()
        
        # 更新最后检查时间
        self.last_checked = datetime.now()
    
    def _update_statistics(self):
        """更新统计指标"""
        # 更新响应时间统计
        if self.response_times:
            self.avg_response_time = statistics.mean(self.response_times)
            self.min_response_time = min(self.response_times)
            self.max_response_time = max(self.response_times)
            # 计算p95响应时间
            if len(self.response_times) >= 20:
                sorted_times = sorted(self.response_times)
                p95_index = int(len(sorted_times) * 0.95)
                self.p95_response_time = sorted_times[p95_index]
        
        # 更新成功率
        if self.total_requests > 0:
            self.success_rate = (self.successful_requests / self.total_requests) * 100
        
        # 更新tokens/s统计
        if self.tokens_per_second:
            self.avg_tokens_per_second = statistics.mean(self.tokens_per_second)
    
    def _update_health_status(self):
        """更新健康状态"""
        # 基于成功率和响应时间判断健康状态
        if self.total_requests == 0:
            self.health_status = ModelHealthStatus.HEALTHY
            return
        
        # 检查成功率
        if self.success_rate < 50:
            self.health_status = ModelHealthStatus.DOWN
        elif self.success_rate < 80:
            self.health_status = ModelHealthStatus.UNHEALTHY
        elif self.avg_response_time > 5.0:
            self.health_status = ModelHealthStatus.DEGRADED
        else:
            self.health_status = ModelHealthStatus.HEALTHY
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            性能摘要字典
        """
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "avg_response_time": round(self.avg_response_time, 2),
            "max_response_time": round(self.max_response_time, 2),
            "p95_response_time": round(self.p95_response_time, 2),
            "success_rate": round(self.success_rate, 2),
            "total_requests": self.total_requests,
            "health_status": self.health_status.value,
            "avg_tokens_per_second": round(self.avg_tokens_per_second, 2),
            "last_checked": self.last_checked.isoformat() if self.last_checked else None
        }
    
    def clear_old_metrics(self):
        """清除过期的指标"""
        now = datetime.now()
        cutoff_time = now - self.metrics_window
        
        # 清除过期的响应时间
        self.response_times = [
            rt for rt, t in zip(
                self.response_times,
                [now - timedelta(seconds=rt) for rt in self.response_times]
            )
            if t >= cutoff_time
        ]
        
        # 清除过期的tokens/s
        self.tokens_per_second = [
            tps for tps, t in zip(
                self.tokens_per_second,
                [now - timedelta(seconds=1/tps) for tps in self.tokens_per_second]
            )
            if t >= cutoff_time
        ]
        
        # 重新计算统计指标
        self._update_statistics()


class ModelSelector:
    """模型选择器"""
    
    def __init__(self, metrics_store: Dict[str, ModelPerformanceMetrics]):
        """
        初始化模型选择器
        
        Args:
            metrics_store: 性能指标存储
        """
        self.metrics_store = metrics_store
    
    def select_best_model(
        self,
        model_type: str = "chat",
        min_success_rate: float = 70.0
    ) -> Optional[str]:
        """
        选择最佳模型
        
        Args:
            model_type: 模型类型
            min_success_rate: 最小成功率
            
        Returns:
            最佳模型ID
        """
        # 过滤健康且成功率符合要求的模型
        eligible_models = []
        for model_id, metrics in self.metrics_store.items():
            if (
                metrics.health_status in (ModelHealthStatus.HEALTHY, ModelHealthStatus.DEGRADED) and
                metrics.success_rate >= min_success_rate
            ):
                eligible_models.append((model_id, metrics))
        
        if not eligible_models:
            logger.warning("没有符合条件的模型")
            return None
        
        # 基于响应时间和成功率评分
        scored_models = []
        for model_id, metrics in eligible_models:
            # 计算评分（响应时间权重0.6，成功率权重0.4）
            # 响应时间越短越好，成功率越高越好
            response_time_score = max(0, 1 - (metrics.avg_response_time / 10))  # 10秒作为基准
            success_rate_score = metrics.success_rate / 100
            total_score = (response_time_score * 0.6) + (success_rate_score * 0.4)
            
            scored_models.append((model_id, total_score))
        
        # 选择评分最高的模型
        scored_models.sort(key=lambda x: x[1], reverse=True)
        best_model_id = scored_models[0][0]
        
        logger.debug(f"选择的最佳模型: {best_model_id}, 评分: {scored_models[0][1]:.2f}")
        return best_model_id
    
    def select_fallback_model(
        self,
        primary_model_id: str,
        model_type: str = "chat"
    ) -> Optional[str]:
        """
        选择备用模型
        
        Args:
            primary_model_id: 主模型ID
            model_type: 模型类型
            
        Returns:
            备用模型ID
        """
        # 过滤健康的模型，排除主模型
        eligible_models = []
        for model_id, metrics in self.metrics_store.items():
            if (
                model_id != primary_model_id and
                metrics.health_status in (ModelHealthStatus.HEALTHY, ModelHealthStatus.DEGRADED)
            ):
                eligible_models.append((model_id, metrics))
        
        if not eligible_models:
            logger.warning("没有符合条件的备用模型")
            return None
        
        # 基于健康状态和成功率选择
        eligible_models.sort(
            key=lambda x: (
                x[1].health_status == ModelHealthStatus.HEALTHY,
                x[1].success_rate
            ),
            reverse=True
        )
        
        fallback_model_id = eligible_models[0][0]
        logger.debug(f"选择的备用模型: {fallback_model_id}")
        return fallback_model_id


class ModelMonitoringService:
    """模型监控服务"""
    
    def __init__(self):
        """初始化模型监控服务"""
        self.metrics_store: Dict[str, ModelPerformanceMetrics] = {}
        self.model_selector = ModelSelector(self.metrics_store)
        self.health_check_interval = timedelta(seconds=30)
        self.last_health_check = datetime.now()
        self.running = False
    
    async def initialize(self):
        """初始化服务"""
        # 加载所有可用模型
        db = next(get_db())
        try:
            available_models = model_query_service.get_available_models_dict(db)
            for model_info in available_models:
                model_id = str(model_info["id"])
                if model_id not in self.metrics_store:
                    self.metrics_store[model_id] = ModelPerformanceMetrics(
                        model_id=model_id,
                        model_name=model_info["model_name"],
                        supplier_id=model_info["supplier_id"],
                        supplier_name=model_info["supplier_name"]
                    )
            logger.info(f"已初始化 {len(self.metrics_store)} 个模型的监控")
        finally:
            db.close()
    
    async def start_monitoring(self):
        """启动监控"""
        self.running = True
        logger.info("模型监控服务已启动")
        
        # 启动健康检查任务
        asyncio.create_task(self._health_check_loop())
    
    async def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info("模型监控服务已停止")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                # 执行健康检查
                await self.perform_health_checks()
                
                # 清除过期指标
                self._cleanup_old_metrics()
                
                # 等待下一次检查
                await asyncio.sleep(self.health_check_interval.total_seconds())
            except Exception as e:
                logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(5)  # 出错后短暂等待
    
    async def perform_health_checks(self):
        """执行健康检查"""
        # 对每个模型执行健康检查
        for model_id, metrics in self.metrics_store.items():
            try:
                # 提交健康检查任务
                await submit_task(
                    self._check_model_health,
                    model_id,
                    priority=TaskPriority.LOW
                )
            except Exception as e:
                logger.error(f"提交健康检查任务失败: {e}")
    
    async def _check_model_health(self, model_id: str):
        """
        检查模型健康状态
        
        Args:
            model_id: 模型ID
        """
        # 这里实现简单的健康检查
        # 实际应用中应该调用模型API进行测试
        logger.debug(f"检查模型健康状态: {model_id}")
        
        # 模拟健康检查
        # 在实际应用中，这里应该发送一个简单的请求到模型API
        await asyncio.sleep(0.5)  # 模拟API调用
        
        # 随机生成健康状态（实际应用中应该基于真实响应）
        success = random.random() > 0.1  # 90%成功率
        response_time = random.uniform(0.5, 3.0)
        
        # 更新指标
        if model_id in self.metrics_store:
            self.metrics_store[model_id].add_metrics(
                response_time=response_time,
                success=success
            )
    
    def _cleanup_old_metrics(self):
        """清除过期指标"""
        for model_id, metrics in self.metrics_store.items():
            metrics.clear_old_metrics()
    
    def record_model_usage(
        self,
        model_id: str,
        response_time: float,
        success: bool,
        tokens_generated: Optional[int] = None
    ):
        """
        记录模型使用情况
        
        Args:
            model_id: 模型ID
            response_time: 响应时间（秒）
            success: 是否成功
            tokens_generated: 生成的token数
        """
        if model_id not in self.metrics_store:
            # 如果模型不存在，创建新的指标记录
            db = next(get_db())
            try:
                model_info = model_query_service.get_model_by_id(db, int(model_id))
                if model_info:
                    self.metrics_store[model_id] = ModelPerformanceMetrics(
                        model_id=model_id,
                        model_name=model_info.model_name or model_info.model_id,
                        supplier_id=model_info.supplier_id,
                        supplier_name=model_info.supplier.name
                    )
            finally:
                db.close()
        
        if model_id in self.metrics_store:
            self.metrics_store[model_id].add_metrics(
                response_time=response_time,
                success=success,
                tokens_generated=tokens_generated
            )
    
    def get_model_metrics(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模型性能指标
        
        Args:
            model_id: 模型ID
            
        Returns:
            性能指标字典
        """
        if model_id in self.metrics_store:
            return self.metrics_store[model_id].get_summary()
        return None
    
    def get_all_model_metrics(self) -> List[Dict[str, Any]]:
        """
        获取所有模型的性能指标
        
        Returns:
            性能指标列表
        """
        return [
            metrics.get_summary()
            for metrics in self.metrics_store.values()
        ]
    
    def select_model(
        self,
        model_type: str = "chat",
        preferred_model_id: Optional[str] = None
    ) -> Optional[str]:
        """
        选择模型
        
        Args:
            model_type: 模型类型
            preferred_model_id: 首选模型ID
            
        Returns:
            选中的模型ID
        """
        # 如果指定了首选模型且该模型健康，则使用首选模型
        if preferred_model_id and preferred_model_id in self.metrics_store:
            metrics = self.metrics_store[preferred_model_id]
            if metrics.health_status in (ModelHealthStatus.HEALTHY, ModelHealthStatus.DEGRADED):
                logger.debug(f"使用首选模型: {preferred_model_id}")
                return preferred_model_id
            else:
                logger.warning(f"首选模型 {preferred_model_id} 不健康，正在选择备用模型")
        
        # 选择最佳模型
        return self.model_selector.select_best_model(model_type)
    
    def get_model_health_status(self, model_id: str) -> Optional[ModelHealthStatus]:
        """
        获取模型健康状态
        
        Args:
            model_id: 模型ID
            
        Returns:
            健康状态
        """
        if model_id in self.metrics_store:
            return self.metrics_store[model_id].health_status
        return None
    
    def get_service_health_summary(self) -> Dict[str, Any]:
        """
        获取服务健康摘要
        
        Returns:
            健康摘要字典
        """
        # 计算整体健康状态
        healthy_models = 0
        degraded_models = 0
        unhealthy_models = 0
        down_models = 0
        
        for metrics in self.metrics_store.values():
            if metrics.health_status == ModelHealthStatus.HEALTHY:
                healthy_models += 1
            elif metrics.health_status == ModelHealthStatus.DEGRADED:
                degraded_models += 1
            elif metrics.health_status == ModelHealthStatus.UNHEALTHY:
                unhealthy_models += 1
            elif metrics.health_status == ModelHealthStatus.DOWN:
                down_models += 1
        
        total_models = len(self.metrics_store)
        
        return {
            "total_models": total_models,
            "healthy_models": healthy_models,
            "degraded_models": degraded_models,
            "unhealthy_models": unhealthy_models,
            "down_models": down_models,
            "overall_health": self._calculate_overall_health(
                total_models,
                healthy_models,
                degraded_models,
                unhealthy_models,
                down_models
            ),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_overall_health(
        self,
        total: int,
        healthy: int,
        degraded: int,
        unhealthy: int,
        down: int
    ) -> str:
        """
        计算整体健康状态
        
        Args:
            total: 总模型数
            healthy: 健康模型数
            degraded: 性能下降模型数
            unhealthy: 不健康模型数
            down: 不可用模型数
            
        Returns:
            整体健康状态
        """
        if total == 0:
            return "unknown"
        
        # 计算健康比例
        healthy_ratio = (healthy + degraded * 0.5) / total
        
        if healthy_ratio >= 0.8:
            return "healthy"
        elif healthy_ratio >= 0.5:
            return "degraded"
        elif healthy_ratio >= 0.2:
            return "unhealthy"
        else:
            return "critical"


# 创建全局模型管理服务实例
model_monitoring_service: Optional[ModelMonitoringService] = None


def get_model_monitoring_service() -> ModelMonitoringService:
    """
    获取全局模型监控服务实例
    
    Returns:
        模型监控服务实例
    """
    global model_monitoring_service
    if model_monitoring_service is None:
        model_monitoring_service = ModelMonitoringService()
    return model_monitoring_service


# 便捷函数
async def initialize_model_monitoring():
    """
    初始化模型监控服务
    """
    service = get_model_monitoring_service()
    await service.initialize()
    await service.start_monitoring()


async def shutdown_model_monitoring():
    """
    关闭模型监控服务
    """
    service = get_model_monitoring_service()
    await service.stop_monitoring()


def record_model_usage(
    model_id: str,
    response_time: float,
    success: bool,
    tokens_generated: Optional[int] = None
):
    """
    记录模型使用情况
    
    Args:
        model_id: 模型ID
        response_time: 响应时间（秒）
        success: 是否成功
        tokens_generated: 生成的token数
    """
    service = get_model_monitoring_service()
    service.record_model_usage(
        model_id=model_id,
        response_time=response_time,
        success=success,
        tokens_generated=tokens_generated
    )


def select_model(
    model_type: str = "chat",
    preferred_model_id: Optional[str] = None
) -> Optional[str]:
    """
    选择模型
    
    Args:
        model_type: 模型类型
        preferred_model_id: 首选模型ID
        
    Returns:
        选中的模型ID
    """
    service = get_model_monitoring_service()
    return service.select_model(model_type, preferred_model_id)
