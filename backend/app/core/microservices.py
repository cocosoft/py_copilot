"""微服务基础配置和工具"""
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import redis
from app.core.config import settings
from app.core.redis import get_redis


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
    
    async def register_service(self, config: MicroserviceConfig) -> bool:
        """注册微服务"""
        try:
            service_data = config.dict()
            service_data["last_heartbeat"] = asyncio.get_event_loop().time()
            
            # 优先使用Redis存储
            if self.redis:
                await self.redis.hset(
                    self.registry_key,
                    config.name,
                    json.dumps(service_data)
                )
                # 设置过期时间（30秒）
                await self.redis.expire(self.registry_key, 30)
            else:
                # Redis不可用时使用内存存储
                self.memory_registry[config.name] = service_data
            
            return True
        except Exception as e:
            print(f"注册服务失败: {e}")
            return False
    
    async def discover_service(self, service_name: str) -> Optional[MicroserviceConfig]:
        """发现微服务"""
        try:
            # 优先从Redis获取
            if self.redis:
                service_data = await self.redis.hget(self.registry_key, service_name)
                if service_data:
                    data = json.loads(service_data)
                    return MicroserviceConfig(**data)
            
            # Redis不可用或未找到时从内存获取
            if service_name in self.memory_registry:
                data = self.memory_registry[service_name]
                return MicroserviceConfig(**data)
                
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


class MessageQueue:
    """消息队列管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def publish_message(self, channel: str, message: Dict[str, Any]) -> bool:
        """发布消息到指定频道"""
        try:
            message_data = json.dumps({
                "timestamp": asyncio.get_event_loop().time(),
                "data": message
            })
            
            # 使用Redis Stream发布消息
            await self.redis.xadd(channel, {"message": message_data})
            return True
        except Exception as e:
            print(f"发布消息失败: {e}")
            return False
    
    async def subscribe_to_channel(self, channel: str, callback) -> None:
        """订阅消息频道"""
        try:
            # 创建消费者组
            consumer_group = f"{channel}:consumers"
            
            # 确保消费者组存在
            try:
                await self.redis.xgroup_create(channel, consumer_group, "0", mkstream=True)
            except Exception:
                # 消费者组可能已存在
                pass
            
            # 持续监听消息
            while True:
                try:
                    # 读取消息
                    messages = await self.redis.xreadgroup(
                        consumer_group, "worker", {channel: ">"}, count=1
                    )
                    
                    if messages:
                        for message_id, message_data in messages[0][1]:
                            message_content = json.loads(message_data["message"])
                            await callback(message_content["data"])
                            
                            # 确认消息处理
                            await self.redis.xack(channel, consumer_group, message_id)
                    
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"消息处理错误: {e}")
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"订阅频道失败: {e}")


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


# 全局微服务管理器实例
_service_registry: Optional[ServiceRegistry] = None
_message_queue: Optional[MessageQueue] = None


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