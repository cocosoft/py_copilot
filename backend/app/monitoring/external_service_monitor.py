"""
外部服务状态监控模块

监控依赖的外部服务（如API服务、数据库服务等）的健康状态和可用性。
"""
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 降级
    UNHEALTHY = "unhealthy"  # 不健康
    UNKNOWN = "unknown"  # 未知
    OFFLINE = "offline"  # 离线


class ServiceType(Enum):
    """服务类型枚举"""
    DATABASE = "database"  # 数据库服务
    API = "api"  # API服务
    CACHE = "cache"  # 缓存服务
    MESSAGE_QUEUE = "message_queue"  # 消息队列
    STORAGE = "storage"  # 存储服务
    EXTERNAL_API = "external_api"  # 外部API


class ServiceMetricType(Enum):
    """服务指标类型枚举"""
    RESPONSE_TIME = "response_time"  # 响应时间
    AVAILABILITY = "availability"  # 可用性
    ERROR_RATE = "error_rate"  # 错误率
    THROUGHPUT = "throughput"  # 吞吐量


class ExternalService:
    """外部服务类"""
    
    def __init__(self, name: str, service_type: ServiceType, endpoint: str, 
                 check_interval: int = 60, timeout: int = 10):
        """初始化外部服务
        
        Args:
            name: 服务名称
            service_type: 服务类型
            endpoint: 服务端点
            check_interval: 检查间隔（秒）
            timeout: 超时时间（秒）
        """
        self.name = name
        self.service_type = service_type
        self.endpoint = endpoint
        self.check_interval = check_interval
        self.timeout = timeout
        self.status = ServiceStatus.UNKNOWN
        self.last_check_time = None
        self.last_success_time = None
        self.response_times: deque = deque(maxlen=100)  # 保留最近100次响应时间
        self.check_count = 0
        self.success_count = 0
        self.error_count = 0
        self.last_error = None
        
    def check_health(self) -> Tuple[ServiceStatus, float, Optional[str]]:
        """检查服务健康状态
        
        Returns:
            (状态, 响应时间, 错误消息)
        """
        self.last_check_time = datetime.now()
        
        try:
            start_time = time.time()
            
            # 根据服务类型执行不同的健康检查
            if self.service_type in [ServiceType.API, ServiceType.EXTERNAL_API]:
                response = requests.get(self.endpoint, timeout=self.timeout)
                response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                
                if response.status_code == 200:
                    self.success_count += 1
                    self.last_success_time = datetime.now()
                    self.response_times.append(response_time)
                    self.status = ServiceStatus.HEALTHY
                    return ServiceStatus.HEALTHY, response_time, None
                else:
                    self.error_count += 1
                    self.last_error = f"HTTP {response.status_code}"
                    self.status = ServiceStatus.UNHEALTHY
                    return ServiceStatus.UNHEALTHY, response_time, self.last_error
                    
            elif self.service_type == ServiceType.DATABASE:
                # 数据库健康检查（这里以SQLite为例）
                import sqlite3
                start_time = time.time()
                connection = sqlite3.connect(self.endpoint)
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                connection.close()
                response_time = (time.time() - start_time) * 1000
                
                self.success_count += 1
                self.last_success_time = datetime.now()
                self.response_times.append(response_time)
                self.status = ServiceStatus.HEALTHY
                return ServiceStatus.HEALTHY, response_time, None
                
            else:
                # 其他服务类型的健康检查
                response_time = (time.time() - start_time) * 1000
                self.status = ServiceStatus.UNKNOWN
                return ServiceStatus.UNKNOWN, response_time, "不支持的服务类型检查"
                
        except requests.exceptions.RequestException as e:
            response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
            self.error_count += 1
            self.last_error = str(e)
            self.status = ServiceStatus.OFFLINE
            return ServiceStatus.OFFLINE, response_time, self.last_error
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
            self.error_count += 1
            self.last_error = str(e)
            self.status = ServiceStatus.UNHEALTHY
            return ServiceStatus.UNHEALTHY, response_time, self.last_error
            
        finally:
            self.check_count += 1
            
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计
        
        Returns:
            服务统计信息
        """
        availability = (self.success_count / self.check_count * 100) if self.check_count > 0 else 0
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "name": self.name,
            "type": self.service_type.value,
            "endpoint": self.endpoint,
            "status": self.status.value,
            "availability": availability,
            "avg_response_time": avg_response_time,
            "check_count": self.check_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_error": self.last_error
        }
        
    def should_check(self) -> bool:
        """判断是否应该进行检查
        
        Returns:
            是否应该检查
        """
        if self.last_check_time is None:
            return True
            
        time_since_last_check = (datetime.now() - self.last_check_time).total_seconds()
        return time_since_last_check >= self.check_interval


class ServiceMetric:
    """服务指标类"""
    
    def __init__(self, metric_type: ServiceMetricType, value: float, timestamp: datetime, 
                 service_name: str, metadata: Optional[Dict[str, Any]] = None):
        """初始化服务指标
        
        Args:
            metric_type: 指标类型
            value: 指标值
            timestamp: 时间戳
            service_name: 服务名称
            metadata: 元数据
        """
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp
        self.service_name = service_name
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "service_name": self.service_name,
            "metadata": self.metadata
        }


class ServiceStats:
    """服务统计类"""
    
    def __init__(self, window_size: int = 100):
        """初始化服务统计
        
        Args:
            window_size: 统计窗口大小
        """
        self.window_size = window_size
        self.metrics: Dict[ServiceMetricType, deque] = {}
        for metric_type in ServiceMetricType:
            self.metrics[metric_type] = deque(maxlen=window_size)
        self.start_time = datetime.now()
        
    def add_metric(self, metric: ServiceMetric):
        """添加服务指标
        
        Args:
            metric: 服务指标
        """
        self.metrics[metric.metric_type].append(metric)
        
    def get_service_stats(self, metric_type: ServiceMetricType) -> Dict[str, Any]:
        """获取指定指标类型的统计
        
        Args:
            metric_type: 指标类型
            
        Returns:
            指标统计信息
        """
        metrics = list(self.metrics[metric_type])
        
        if not metrics:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "current": 0
            }
            
        values = [m.value for m in metrics]
        current_value = metrics[-1].value if metrics else 0
        
        return {
            "count": len(values),
            "avg": sum(values) / len(values) if values else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "current": current_value
        }


class ExternalServiceMonitor:
    """外部服务监控器"""
    
    def __init__(self, window_size: int = 100):
        """初始化外部服务监控器
        
        Args:
            window_size: 统计窗口大小
        """
        self.services: Dict[str, ExternalService] = {}
        self.stats = ServiceStats(window_size)
        self.is_monitoring = False
        self._monitoring_task = None
        
    def register_service(self, name: str, service_type: ServiceType, endpoint: str, 
                        check_interval: int = 60, timeout: int = 10):
        """注册外部服务
        
        Args:
            name: 服务名称
            service_type: 服务类型
            endpoint: 服务端点
            check_interval: 检查间隔（秒）
            timeout: 超时时间（秒）
        """
        service = ExternalService(name, service_type, endpoint, check_interval, timeout)
        self.services[name] = service
        logger.info(f"已注册外部服务: {name} ({service_type.value}) - {endpoint}")
        
    def unregister_service(self, name: str):
        """取消注册外部服务
        
        Args:
            name: 服务名称
        """
        if name in self.services:
            del self.services[name]
            logger.info(f"已取消注册外部服务: {name}")
        
    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("外部服务监控已在运行")
            return
            
        self.is_monitoring = True
        logger.info("开始外部服务监控")
        
        # 这里可以启动异步监控任务
        # 由于当前环境限制，我们使用同步方式
        
    async def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        logger.info("停止外部服务监控")
        
    def check_all_services(self):
        """检查所有服务"""
        results = {}
        
        for service_name, service in self.services.items():
            if service.should_check():
                status, response_time, error = service.check_health()
                results[service_name] = {
                    "status": status.value,
                    "response_time": response_time,
                    "error": error
                }
                
                # 记录指标
                timestamp = datetime.now()
                
                # 响应时间指标
                response_metric = ServiceMetric(
                    metric_type=ServiceMetricType.RESPONSE_TIME,
                    value=response_time,
                    timestamp=timestamp,
                    service_name=service_name
                )
                self.stats.add_metric(response_metric)
                
                # 可用性指标（成功为100，失败为0）
                availability = 100 if status == ServiceStatus.HEALTHY else 0
                availability_metric = ServiceMetric(
                    metric_type=ServiceMetricType.AVAILABILITY,
                    value=availability,
                    timestamp=timestamp,
                    service_name=service_name
                )
                self.stats.add_metric(availability_metric)
                
                # 记录日志
                if status == ServiceStatus.HEALTHY:
                    logger.debug(f"服务 {service_name} 健康检查通过，响应时间: {response_time:.2f}ms")
                else:
                    logger.warning(f"服务 {service_name} 健康检查失败: {error}")
                    
        return results
        
    def get_service_summary(self) -> Dict[str, Any]:
        """获取服务摘要
        
        Returns:
            服务摘要信息
        """
        # 检查所有服务
        self.check_all_services()
        
        service_stats = {}
        healthy_count = 0
        total_count = len(self.services)
        
        for service_name, service in self.services.items():
            stats = service.get_stats()
            service_stats[service_name] = stats
            
            if service.status == ServiceStatus.HEALTHY:
                healthy_count += 1
                
        overall_availability = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "services": service_stats,
            "total_services": total_count,
            "healthy_services": healthy_count,
            "overall_availability": overall_availability,
            "is_monitoring": self.is_monitoring
        }
        
    def check_services_health(self, availability_threshold: float = 95.0) -> Dict[str, Any]:
        """检查服务健康状态
        
        Args:
            availability_threshold: 可用性阈值（百分比）
            
        Returns:
            服务健康状态信息
        """
        summary = self.get_service_summary()
        
        # 健康状态判断
        is_healthy = True
        warnings = []
        problematic_services = []
        
        for service_name, service_stats in summary["services"].items():
            availability = service_stats["availability"]
            status = service_stats["status"]
            
            if availability < availability_threshold or status != "healthy":
                problematic_services.append({
                    "service": service_name,
                    "availability": availability,
                    "status": status,
                    "last_error": service_stats["last_error"]
                })
                
        if problematic_services:
            warnings.append(f"发现 {len(problematic_services)} 个有问题的服务")
            is_healthy = False
            
        # 总体可用性检查
        if summary["overall_availability"] < availability_threshold:
            warnings.append(f"总体可用性过低: {summary['overall_availability']:.2f}%")
            is_healthy = False
            
        return {
            "status": "healthy" if is_healthy else "warning",
            "timestamp": datetime.now().isoformat(),
            "overall_availability": summary["overall_availability"],
            "healthy_services": summary["healthy_services"],
            "total_services": summary["total_services"],
            "warnings": warnings,
            "problematic_services": problematic_services,
            "is_healthy": is_healthy
        }
        
    def get_service_trend(self, metric_type: ServiceMetricType, service_name: str, 
                         hours: int = 24) -> List[Dict[str, Any]]:
        """获取服务趋势数据
        
        Args:
            metric_type: 指标类型
            service_name: 服务名称
            hours: 时间范围（小时）
            
        Returns:
            服务趋势数据
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指定时间范围内的指标
        recent_metrics = [
            m for m in self.stats.metrics[metric_type]
            if m.timestamp >= cutoff_time and m.service_name == service_name
        ]
        
        return [metric.to_dict() for metric in recent_metrics]
        
    def get_critical_services_report(self) -> Dict[str, Any]:
        """获取关键服务报告
        
        Returns:
            关键服务报告
        """
        summary = self.get_service_summary()
        
        # 找出有问题的服务
        problematic_services = []
        for service_name, service_stats in summary["services"].items():
            if service_stats["status"] != "healthy":
                problematic_services.append(service_stats)
                
        # 找出响应时间最慢的服务
        slow_services = []
        for service_name, service_stats in summary["services"].items():
            if service_stats["avg_response_time"] > 1000:  # 超过1秒
                slow_services.append(service_stats)
                
        return {
            "problematic_services": problematic_services,
            "slow_services": slow_services,
            "overall_health": summary["overall_availability"],
            "timestamp": datetime.now().isoformat()
        }


# 全局外部服务监控器实例
external_service_monitor = ExternalServiceMonitor()

# 注册默认服务
default_services = [
    {
        "name": "main_database",
        "type": ServiceType.DATABASE,
        "endpoint": "backend/py_copilot.db",
        "check_interval": 30
    },
    {
        "name": "local_api",
        "type": ServiceType.API,
        "endpoint": "http://localhost:8000/api/health",
        "check_interval": 60
    }
]

# 注册默认服务
for service_config in default_services:
    external_service_monitor.register_service(
        name=service_config["name"],
        service_type=service_config["type"],
        endpoint=service_config["endpoint"],
        check_interval=service_config["check_interval"]
    )