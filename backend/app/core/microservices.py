"""微服务基础配置和工具"""
import os
import json
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import redis
from app.core.config import settings
from app.core.redis import get_redis
from app.core.logging_config import logger


class MicroserviceConfig(BaseModel):
    """微服务配置模型"""
    name: str = Field(..., description="微服务名称")
    version: str = Field("1.0.0", description="服务版本")
    host: str = Field("localhost", description="服务主机")
    port: int = Field(..., description="服务端口")
    health_check_path: str = Field("/health", description="健康检查路径")
    api_prefix: str = Field("/api/v1", description="API前缀")
    description: Optional[str] = Field(None, description="服务描述")
    dependencies: List[str] = Field(default_factory=list, description="依赖服务列表")
    health_status: str = Field("healthy", description="服务健康状态")
    last_heartbeat: Optional[float] = Field(None, description="最后心跳时间")
    weight: int = Field(1, description="服务权重，用于负载均衡")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="服务元数据")
    tags: List[str] = Field(default_factory=list, description="服务标签")
    capacity: int = Field(100, description="服务容量，用于限流")
    current_load: int = Field(0, description="当前服务负载")
    
    class Config:
        json_encoders = {
            # 自定义JSON编码器
        }


class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.registry_key = "microservices:registry"
        self.memory_registry: Dict[str, Dict[str, Any]] = {}  # 内存注册表作为备用
        self.health_check_interval = 60  # 健康检查间隔（秒）
        self.max_retry_attempts = 5  # 最大重试次数
        self.initial_retry_delay = 1.0  # 初始重试延迟（秒）
        self.max_retry_delay = 60.0  # 最大重试延迟（秒）
        self.service_connections: Dict[str, int] = {}  # 记录每个服务实例的连接数
        self.service_stats: Dict[str, Dict[str, Any]] = {}  # 服务统计信息
        self.last_load_update: float = 0  # 上次负载更新时间
        self.load_update_interval = 5  # 负载更新间隔（秒）
    
    async def _retry_with_backoff(self, operation: callable, operation_name: str, 
                                   max_attempts: Optional[int] = None) -> bool:
        """
        使用指数退避重试机制执行操作
        
        Args:
            operation: 要执行的操作函数
            operation_name: 操作名称（用于日志）
            max_attempts: 最大重试次数，默认使用类配置值
            
        Returns:
            操作是否成功
        """
        if max_attempts is None:
            max_attempts = self.max_retry_attempts
        
        attempt = 0
        last_error = None
        
        while attempt < max_attempts:
            attempt += 1
            try:
                result = await operation()
                if result:
                    logger.info(f"{operation_name} 成功 (尝试 {attempt}/{max_attempts})")
                    return True
            except Exception as e:
                last_error = e
                logger.warning(f"{operation_name} 失败 (尝试 {attempt}/{max_attempts}): {str(e)}")
            
            if attempt < max_attempts:
                delay = min(
                    self.initial_retry_delay * (2 ** (attempt - 1)),
                    self.max_retry_delay
                )
                logger.info(f"{operation_name} 将在 {delay:.2f} 秒后重试...")
                await asyncio.sleep(delay)
        
        logger.error(f"{operation_name} 在 {max_attempts} 次尝试后仍然失败: {str(last_error)}")
        return False
    
    async def register_service(self, config: MicroserviceConfig) -> bool:
        """
        注册微服务（带指数退避重试机制）
        
        Args:
            config: 微服务配置
            
        Returns:
            注册是否成功
        """
        async def _register_operation():
            """执行注册操作"""
            service_data = config.dict()
            service_data["last_heartbeat"] = asyncio.get_event_loop().time()
            service_data["health_status"] = "healthy"
            
            # 优先使用Redis存储
            if self.redis:
                await self.redis.hset(
                    self.registry_key,
                    config.name,
                    json.dumps(service_data)
                )
                # 设置过期时间（30秒）
                await self.redis.expire(self.registry_key, 30)
                
                # 启动健康检查任务
                asyncio.create_task(self._health_check_service(config))
                return True
            else:
                # Redis不可用时使用内存存储
                self.memory_registry[config.name] = service_data
                return True
        
        return await self._retry_with_backoff(_register_operation, f"注册服务 {config.name}")
    
    async def discover_service(self, service_name: str, strategy: str = "round_robin") -> Optional[MicroserviceConfig]:
        """发现微服务（支持多种负载均衡策略）"""
        try:
            # 获取所有同名服务
            all_services = await self.get_all_services()
            service_instances = []
            
            for name, config in all_services.items():
                if name == service_name and config.health_status == "healthy":
                    service_instances.append(config)
            
            if not service_instances:
                return None
            
            # 根据策略选择服务实例
            if strategy == "round_robin":
                # 简单轮询负载均衡策略
                current_time = asyncio.get_event_loop().time()
                index = int(current_time) % len(service_instances)
                selected_service = service_instances[index]
                self._update_service_connection(selected_service.name, 1)
                return selected_service
            elif strategy == "weighted_round_robin":
                # 加权轮询负载均衡策略（基于服务配置的权重）
                # 为每个服务实例分配权重（默认为1）
                total_weight = sum(getattr(config, "weight", 1) for config in service_instances)
                current_time = asyncio.get_event_loop().time()
                weight_index = int(current_time) % total_weight
                
                current_weight = 0
                for config in service_instances:
                    current_weight += getattr(config, "weight", 1)
                    if weight_index < current_weight:
                        self._update_service_connection(config.name, 1)
                        return config
                selected_service = service_instances[0]  # 默认返回第一个
                self._update_service_connection(selected_service.name, 1)
                return selected_service
            elif strategy == "least_connections":
                # 最少连接数策略
                min_connections = float('inf')
                selected_service = None
                
                for config in service_instances:
                    connections = self.service_connections.get(config.name, 0)
                    if connections < min_connections:
                        min_connections = connections
                        selected_service = config
                
                if selected_service:
                    self._update_service_connection(selected_service.name, 1)
                    return selected_service
                else:
                    selected_service = service_instances[0]
                    self._update_service_connection(selected_service.name, 1)
                    return selected_service
            elif strategy == "least_load":
                # 最小负载策略（基于服务的当前负载和容量）
                min_load_ratio = float('inf')
                selected_service = None
                
                for config in service_instances:
                    load_ratio = getattr(config, "current_load", 0) / getattr(config, "capacity", 100)
                    if load_ratio < min_load_ratio:
                        min_load_ratio = load_ratio
                        selected_service = config
                
                if selected_service:
                    self._update_service_connection(selected_service.name, 1)
                    return selected_service
                else:
                    selected_service = service_instances[0]
                    self._update_service_connection(selected_service.name, 1)
                    return selected_service
            elif strategy == "random":
                # 随机策略
                import random
                selected_service = random.choice(service_instances)
                self._update_service_connection(selected_service.name, 1)
                return selected_service
            else:
                # 默认使用轮询策略
                current_time = asyncio.get_event_loop().time()
                index = int(current_time) % len(service_instances)
                selected_service = service_instances[index]
                self._update_service_connection(selected_service.name, 1)
                return selected_service
                
        except Exception as e:
            print(f"发现服务失败: {e}")
        return None
    
    async def get_all_services(self) -> Dict[str, MicroserviceConfig]:
        """获取所有注册的服务"""
        try:
            services = {}
            
            # 优先从Redis获取
            if self.redis:
                services_data = await self.redis.hgetall(self.registry_key)
                for name, data in services_data.items():
                    service_info = json.loads(data)
                    services[name] = MicroserviceConfig(**service_info)
            
            # 从内存存储获取（覆盖或补充Redis中的服务）
            for name, data in self.memory_registry.items():
                services[name] = MicroserviceConfig(**data)
                
            return services
        except Exception as e:
            print(f"获取服务列表失败: {e}")
            # 返回内存存储中的服务作为备用
            services = {}
            for name, data in self.memory_registry.items():
                services[name] = MicroserviceConfig(**data)
            return services
    
    def _update_service_connection(self, service_name: str, delta: int):
        """更新服务实例的连接数"""
        current_connections = self.service_connections.get(service_name, 0)
        new_connections = max(0, current_connections + delta)
        self.service_connections[service_name] = new_connections
        
        # 更新服务统计信息
        if service_name not in self.service_stats:
            self.service_stats[service_name] = {
                "total_connections": 0,
                "current_connections": 0,
                "peak_connections": 0,
                "total_requests": 0,
                "failed_requests": 0,
                "last_request_time": None
            }
        
        self.service_stats[service_name]["current_connections"] = new_connections
        self.service_stats[service_name]["total_connections"] += abs(delta)
        self.service_stats[service_name]["peak_connections"] = max(
            self.service_stats[service_name]["peak_connections"],
            new_connections
        )
        if delta > 0:
            self.service_stats[service_name]["total_requests"] += 1
            self.service_stats[service_name]["last_request_time"] = asyncio.get_event_loop().time()
    
    async def update_service_load(self, service_name: str, load: int):
        """更新服务实例的负载"""
        try:
            # 更新Redis中的服务负载
            if self.redis:
                service_data = await self.redis.hget(self.registry_key, service_name)
                if service_data:
                    data = json.loads(service_data)
                    data["current_load"] = load
                    await self.redis.hset(self.registry_key, service_name, json.dumps(data))
            
            # 更新内存中的服务负载
            if service_name in self.memory_registry:
                self.memory_registry[service_name]["current_load"] = load
        except Exception as e:
            print(f"更新服务负载失败: {e}")
    
    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """获取服务实例的统计信息"""
        return self.service_stats.get(service_name, {
            "total_connections": 0,
            "current_connections": 0,
            "peak_connections": 0,
            "total_requests": 0,
            "failed_requests": 0,
            "last_request_time": None
        })
    
    def record_service_failure(self, service_name: str):
        """记录服务实例的失败请求"""
        if service_name in self.service_stats:
            self.service_stats[service_name]["failed_requests"] += 1
    
    async def deregister_service(self, service_name: str) -> bool:
        """注销服务"""
        try:
            if self.redis:
                await self.redis.hdel(self.registry_key, service_name)
            
            if service_name in self.memory_registry:
                del self.memory_registry[service_name]
            
            # 清理服务连接数和统计信息
            if service_name in self.service_connections:
                del self.service_connections[service_name]
            if service_name in self.service_stats:
                del self.service_stats[service_name]
            
            print(f"服务注销成功: {service_name}")
            return True
        except Exception as e:
            print(f"服务注销失败: {e}")
            return False
    
    async def update_heartbeat(self, service_name: str) -> bool:
        """更新服务心跳"""
        try:
            if self.redis:
                service_data = await self.redis.hget(self.registry_key, service_name)
                if service_data:
                    data = json.loads(service_data)
                    data["last_heartbeat"] = asyncio.get_event_loop().time()
                    await self.redis.hset(self.registry_key, service_name, json.dumps(data))
                    return True
            
            if service_name in self.memory_registry:
                self.memory_registry[service_name]["last_heartbeat"] = asyncio.get_event_loop().time()
                return True
            
            return False
        except Exception as e:
            print(f"更新心跳失败: {e}")
            return False
    
    async def _health_check_service(self, config: MicroserviceConfig):
        """健康检查服务"""
        while True:
            try:
                health_status = "healthy"
                
                try:
                    # 发送健康检查请求
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"http://{config.host}:{config.port}{config.health_check_path}",
                            timeout=5.0
                        )
                        if response.status_code != 200:
                            health_status = "unhealthy"
                except Exception:
                    health_status = "unhealthy"
                
                # 更新服务健康状态
                if self.redis:
                    service_data = await self.redis.hget(self.registry_key, config.name)
                    if service_data:
                        data = json.loads(service_data)
                        data["health_status"] = health_status
                        data["last_heartbeat"] = asyncio.get_event_loop().time()
                        await self.redis.hset(self.registry_key, config.name, json.dumps(data))
                
                if config.name in self.memory_registry:
                    self.memory_registry[config.name]["health_status"] = health_status
                    self.memory_registry[config.name]["last_heartbeat"] = asyncio.get_event_loop().time()
                    
            except Exception as e:
                print(f"健康检查失败: {e}")
            
            await asyncio.sleep(self.health_check_interval)


class MessageQueue:
    """消息队列管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.consumer_groups: Dict[str, List[str]] = {}  # 记录已创建的消费者组
    
    async def publish_message(self, channel: str, message: Dict[str, Any], message_id: Optional[str] = None) -> bool:
        """发布消息到指定频道"""
        try:
            message_data = json.dumps({
                "timestamp": asyncio.get_event_loop().time(),
                "data": message
            })
            
            # 使用Redis Stream发布消息
            if message_id:
                await self.redis.xadd(channel, {"message": message_data}, id=message_id)
            else:
                await self.redis.xadd(channel, {"message": message_data})
            return True
        except Exception as e:
            print(f"发布消息失败: {e}")
            return False
    
    async def subscribe_to_channel(self, channel: str, callback, consumer_id: str = "worker", batch_size: int = 10) -> None:
        """订阅消息频道"""
        try:
            # 创建消费者组
            consumer_group = f"{channel}:consumers"
            
            # 确保消费者组存在
            if channel not in self.consumer_groups or consumer_group not in self.consumer_groups[channel]:
                try:
                    await self.redis.xgroup_create(channel, consumer_group, "0", mkstream=True)
                    if channel not in self.consumer_groups:
                        self.consumer_groups[channel] = []
                    self.consumer_groups[channel].append(consumer_group)
                except Exception:
                    # 消费者组可能已存在
                    pass
            
            # 持续监听消息
            while True:
                try:
                    # 读取消息
                    messages = await self.redis.xreadgroup(
                        consumer_group, consumer_id, {channel: ">"}, count=batch_size, block=1000
                    )
                    
                    if messages:
                        for stream, stream_messages in messages:
                            for message_id, message_data in stream_messages:
                                try:
                                    message_content = json.loads(message_data["message"])
                                    await callback(message_content["data"])
                                    
                                    # 确认消息处理
                                    await self.redis.xack(channel, consumer_group, message_id)
                                except Exception as msg_e:
                                    print(f"处理消息 {message_id} 失败: {msg_e}")
                    
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"消息处理错误: {e}")
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"订阅频道失败: {e}")
    
    async def get_pending_messages(self, channel: str, consumer_group: str, count: int = 100) -> List[Dict[str, Any]]:
        """获取未确认的消息"""
        try:
            pending_messages = await self.redis.xpending(channel, consumer_group, "-", "+", count)
            return pending_messages
        except Exception as e:
            print(f"获取未确认消息失败: {e}")
            return []
    
    async def acknowledge_message(self, channel: str, consumer_group: str, message_id: str) -> bool:
        """确认消息处理"""
        try:
            await self.redis.xack(channel, consumer_group, message_id)
            return True
        except Exception as e:
            print(f"确认消息失败: {e}")
            return False
    
    async def set_stream_length(self, channel: str, max_length: int, approximate: bool = True) -> bool:
        """设置流的最大长度"""
        try:
            if approximate:
                await self.redis.xtrim(channel, maxlen=max_length, approximate=True)
            else:
                await self.redis.xtrim(channel, maxlen=max_length, approximate=False)
            return True
        except Exception as e:
            print(f"设置流长度失败: {e}")
            return False
    
    async def create_consumer_group(self, channel: str, consumer_group: str) -> bool:
        """创建消费者组"""
        try:
            await self.redis.xgroup_create(channel, consumer_group, "0", mkstream=True)
            if channel not in self.consumer_groups:
                self.consumer_groups[channel] = []
            self.consumer_groups[channel].append(consumer_group)
            return True
        except Exception as e:
            print(f"创建消费者组失败: {e}")
            return False
    
    async def delete_consumer_group(self, channel: str, consumer_group: str) -> bool:
        """删除消费者组"""
        try:
            await self.redis.xgroup_destroy(channel, consumer_group)
            if channel in self.consumer_groups and consumer_group in self.consumer_groups[channel]:
                self.consumer_groups[channel].remove(consumer_group)
            return True
        except Exception as e:
            print(f"删除消费者组失败: {e}")
            return False


class CircuitBreaker:
    """断路器模式实现"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def execute(self, operation) -> Any:
        """执行操作，应用断路器逻辑"""
        if self.state == "OPEN":
            # 检查是否应该尝试恢复
            if self._should_try_recovery():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await operation()
            
            # 操作成功，重置计数器
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failure_count = 0
            
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e
    
    def _should_try_recovery(self) -> bool:
        """检查是否应该尝试恢复"""
        if self.last_failure_time is None:
            return True
        
        current_time = asyncio.get_event_loop().time()
        return (current_time - self.last_failure_time) > self.timeout


class MicroserviceClient:
    """微服务客户端，用于简化服务间通信"""
    
    def __init__(self):
        self.service_registry = get_service_registry()
        self.http_client = httpx.AsyncClient()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    async def call_service(self, service_name: str, path: str, method: str = "GET", 
                          headers: Optional[Dict[str, str]] = None, 
                          body: Optional[Any] = None, 
                          timeout: float = 30.0) -> Dict[str, Any]:
        """调用其他微服务"""
        # 发现目标服务
        service_config = await self.service_registry.discover_service(service_name)
        if not service_config:
            raise Exception(f"服务 {service_name} 不可用")
        
        # 获取或创建断路器
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        
        circuit_breaker = self.circuit_breakers[service_name]
        
        # 构建目标URL
        target_url = f"http://{service_config.host}:{service_config.port}{service_config.api_prefix}{path}"
        
        async def make_request():
            """执行HTTP请求"""
            try:
                response = await self.http_client.request(
                    method=method,
                    url=target_url,
                    headers=headers or {},
                    json=body if body else None,
                    timeout=timeout
                )
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text,
                    "data": response.json() if response.text else None
                }
            except httpx.TimeoutException:
                raise Exception("服务请求超时")
            except httpx.HTTPStatusError as e:
                raise Exception(f"服务调用失败: {e.response.status_code} {e.response.text}")
            except Exception as e:
                raise Exception(f"服务调用失败: {str(e)}")
        
        # 使用断路器执行请求
        try:
            result = await circuit_breaker.execute(make_request)
            # 请求成功，减少连接数
            self.service_registry._update_service_connection(service_name, -1)
            return result
        except Exception as e:
            # 请求失败，减少连接数并记录失败
            self.service_registry._update_service_connection(service_name, -1)
            self.service_registry.record_service_failure(service_name)
            raise e
    
    async def get(self, service_name: str, path: str, 
                 headers: Optional[Dict[str, str]] = None, 
                 params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送GET请求"""
        if params:
            # 构建查询参数
            query_params = "&" if "?" in path else "?"
            query_params += "&" .join([f"{k}={v}" for k, v in params.items()])
            path += query_params
        
        return await self.call_service(service_name, path, "GET", headers)
    
    async def post(self, service_name: str, path: str, 
                  headers: Optional[Dict[str, str]] = None, 
                  body: Optional[Any] = None) -> Dict[str, Any]:
        """发送POST请求"""
        return await self.call_service(service_name, path, "POST", headers, body)
    
    async def put(self, service_name: str, path: str, 
                 headers: Optional[Dict[str, str]] = None, 
                 body: Optional[Any] = None) -> Dict[str, Any]:
        """发送PUT请求"""
        return await self.call_service(service_name, path, "PUT", headers, body)
    
    async def delete(self, service_name: str, path: str, 
                    headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """发送DELETE请求"""
        return await self.call_service(service_name, path, "DELETE", headers)


# 全局微服务管理器实例
_service_registry: Optional[ServiceRegistry] = None
_message_queue: Optional[MessageQueue] = None
_microservice_client: Optional[MicroserviceClient] = None


def get_service_registry() -> ServiceRegistry:
    """获取服务注册中心实例"""
    global _service_registry
    if _service_registry is None:
        redis_client = get_redis()
        _service_registry = ServiceRegistry(redis_client)
    return _service_registry


def get_message_queue() -> MessageQueue:
    """获取消息队列实例"""
    global _message_queue
    if _message_queue is None:
        redis_client = get_redis()
        _message_queue = MessageQueue(redis_client)
    return _message_queue


def get_microservice_client() -> MicroserviceClient:
    """获取微服务客户端实例"""
    global _microservice_client
    if _microservice_client is None:
        _microservice_client = MicroserviceClient()
    return _microservice_client