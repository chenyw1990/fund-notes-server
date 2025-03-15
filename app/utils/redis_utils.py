import json
from app.extensions import redis_client

def cache_get(key):
    """从Redis缓存获取数据"""
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def cache_set(key, data, expire=3600):
    """将数据存入Redis缓存"""
    redis_client.setex(key, expire, json.dumps(data))

def cache_delete(key):
    """删除Redis缓存"""
    redis_client.delete(key)

def cache_clear_pattern(pattern):
    """清除匹配模式的所有缓存"""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)

def increment_counter(key, amount=1, expire=None):
    """增加计数器"""
    value = redis_client.incrby(key, amount)
    if expire and redis_client.ttl(key) < 0:
        redis_client.expire(key, expire)
    return value

def get_counter(key):
    """获取计数器值"""
    value = redis_client.get(key)
    return int(value) if value else 0 