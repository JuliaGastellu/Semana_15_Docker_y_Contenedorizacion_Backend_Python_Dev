import asyncio
import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings
from app.realtime import manager, post_manager

logger = logging.getLogger("pulse.redis")
redis = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=2,
)


async def get_redis():
    return redis


async def available():
    try:
        return bool(await redis.ping())
    except RedisError:
        return False


async def listen():
    while True:
        try:
            async with redis.pubsub() as channel:
                await channel.psubscribe("notifications:user:*", "notifications:post:*")
                async for message in channel.listen():
                    if message["type"] == "pmessage":
                        user_id = int(message["channel"].rsplit(":", 1)[1])
                        target = post_manager if ":post:" in message["channel"] else manager
                        await target.send(user_id, json.loads(message["data"]))
        except asyncio.CancelledError:
            raise
        except (RedisError, ValueError):
            logger.warning("Redis pub/sub no disponible; reintento en dos segundos")
            await asyncio.sleep(2)


async def publish(user_id, payload):
    try:
        await redis.publish(f"notifications:user:{user_id}", json.dumps(payload))
    except RedisError:
        await manager.send(user_id, payload)
