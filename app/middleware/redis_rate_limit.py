import time
from uuid import uuid4

from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.redis_client import redis
from app.security import decode_token

FIXED = """
local n = redis.call('INCR',KEYS[1])
if n == 1 then redis.call('EXPIRE',KEYS[1],60) end
return {n,redis.call('TTL',KEYS[1])}
"""
SLIDING = """
redis.call('ZREMRANGEBYSCORE',KEYS[1],'-inf',ARGV[1]-60)
local n = redis.call('ZCARD',KEYS[1])
if n < tonumber(ARGV[2]) then redis.call('ZADD',KEYS[1],ARGV[1],ARGV[3]) end
redis.call('EXPIRE',KEYS[1],60)
return n+1
"""


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in {"/", "/health", "/docs", "/openapi.json"}:
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        identity = f"ip:{ip}"
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            try:
                identity = f"user:{int(decode_token(authorization[7:], 'access')['sub'])}"
            except Exception:
                pass
        login = request.url.path == "/api/v1/auth/token"
        limit = settings.login_rate_limit_per_minute if login else settings.rate_limit_per_minute
        try:
            if login:
                count = int(
                    await redis.eval(
                        SLIDING,
                        1,
                        f"ratelimit:login:{ip}",
                        time.time(),
                        limit,
                        uuid4().hex,
                    )
                )
                remaining_time = 60
            else:
                count, remaining_time = await redis.eval(
                    FIXED, 1, f"ratelimit:{identity}:{int(time.time() // 60)}"
                )
            if count > limit:
                return JSONResponse(
                    {"detail": "Superé el límite de peticiones"},
                    status_code=429,
                    headers={
                        "Retry-After": str(max(1, remaining_time)),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )
        except RedisError:
            return await call_next(request)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
