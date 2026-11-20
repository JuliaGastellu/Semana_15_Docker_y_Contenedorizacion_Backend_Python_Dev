import asyncio
import json
import random
from uuid import uuid4

from redis.exceptions import RedisError

from app.redis_client import redis


async def cached(key, ttl, loader):
    token = uuid4().hex
    lock = f"lock:{key}"
    acquired = False
    try:
        value = await redis.get(key)
        if value is not None:
            return json.loads(value), "HIT"
        acquired = bool(await redis.set(lock, token, nx=True, ex=10))
        if not acquired:
            for _ in range(20):
                await asyncio.sleep(0.05)
                value = await redis.get(key)
                if value is not None:
                    return json.loads(value), "HIT"
        result = await loader()
        if acquired:
            await redis.set(key, json.dumps(result), ex=ttl + random.randint(0, max(1, ttl // 10)))
        return result, "MISS"
    except RedisError:
        return await loader(), "BYPASS"
    finally:
        if acquired:
            try:
                await redis.eval(
                    "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end",
                    1,
                    lock,
                    token,
                )
            except RedisError:
                pass


async def invalidate(pattern="cache:post*"):
    try:
        async for key in redis.scan_iter(match=pattern, count=100):
            await redis.delete(key)
    except RedisError:
        pass


async def write_user(user_id, payload):
    try:
        await redis.set(f"cache:user:{user_id}", json.dumps(payload), ex=600)
    except RedisError:
        pass
