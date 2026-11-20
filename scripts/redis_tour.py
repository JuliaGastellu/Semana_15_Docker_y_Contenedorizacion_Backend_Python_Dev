"""Practico los cinco tipos de Redis con keys temporales propias."""
import asyncio
from uuid import uuid4
from app.redis_client import redis

async def main():
    prefix = "demo:" + uuid4().hex
    keys = [prefix + ":" + kind for kind in ("string","hash","list","set","zset")]
    try:
        await redis.set(keys[0], "mi valor", ex=60)
        await redis.hset(keys[1], mapping={"title":"Mi borrador"})
        await redis.rpush(keys[2], "evento1", "evento2")
        await redis.sadd(keys[3], "python", "backend")
        await redis.zadd(keys[4], {"post1":10, "post2":20})
        for key in keys:
            await redis.expire(key,60)
            print(key,await redis.type(key),await redis.ttl(key))
    finally:
        await redis.delete(*keys)
        await redis.aclose()

if __name__ == "__main__":
    asyncio.run(main())
