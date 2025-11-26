"""Redis连接配置"""
import redis
from typing import Optional

from app.core.config import settings

# 创建Redis连接池
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=50,
    decode_responses=True
)


def get_redis() -> Optional[redis.Redis]:
    """获取Redis连接的函数"""
    try:
        r = redis.Redis(connection_pool=redis_pool)
        # 测试连接
        r.ping()
        return r
    except redis.ConnectionError:
        # Redis连接失败时返回None
        return None


# 创建默认Redis客户端实例
redis_client: Optional[redis.Redis] = get_redis()