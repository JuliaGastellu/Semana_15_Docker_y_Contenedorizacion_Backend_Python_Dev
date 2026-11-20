from typing import Awaitable, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.dependencies import EditorDep
from app.redis_client import get_redis

router = APIRouter(prefix="/autosave", tags=["autosave"])


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="", max_length=200)
    content: str = Field(default="", max_length=100000)


@router.put("")
async def save(data: Draft, user: EditorDep, cache: Redis = Depends(get_redis)):
    try:
        async with cache.pipeline(transaction=True) as pipe:
            pipe.hset(f"autosave:user:{user.id}", mapping=data.model_dump())
            pipe.expire(f"autosave:user:{user.id}", 86400)
            await pipe.execute()
        return data
    except RedisError as exc:
        raise HTTPException(503, "No pude guardar el borrador") from exc


@router.get("")
async def get(user: EditorDep, cache: Redis = Depends(get_redis)):
    try:
        data = await cast(Awaitable[dict[str, str]], cache.hgetall(f"autosave:user:{user.id}"))
    except RedisError as exc:
        raise HTTPException(503, "El autoguardado no está disponible") from exc
    if not data:
        raise HTTPException(404, "No tengo un borrador guardado")
    return data


@router.delete("", status_code=204)
async def delete(user: EditorDep, cache: Redis = Depends(get_redis)):
    try:
        await cache.delete(f"autosave:user:{user.id}")
    except RedisError as exc:
        raise HTTPException(503, "No pude descartar el borrador") from exc
