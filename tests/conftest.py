import os
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

database_url = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:local-test-only@127.0.0.1:55432/pulse_test",
)
redis_url = os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:56379/15")
if "test" not in make_url(database_url).database.lower():
    raise RuntimeError("Necesito una base de prueba identificada con test")
if not redis_url.endswith("/15"):
    raise RuntimeError("Reservo Redis DB 15 para pruebas")
os.environ["DATABASE_URL"] = database_url
os.environ["REDIS_URL"] = redis_url
os.environ["JWT_SECRET"] = "clave-exclusiva-de-pruebas-locales-de-bootcamp"
os.environ["RATE_LIMIT_PER_MINUTE"] = "10000"
os.environ["LOGIN_RATE_LIMIT_PER_MINUTE"] = "10000"

from app.main import app
from app.database import engine, async_session_factory
from app.models import User
from app.redis_client import redis


@pytest.fixture
def client():
    with TestClient(app) as client:

        async def reset():
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        "TRUNCATE notifications, refresh_tokens, comments, post_tags, posts, tags, categories, users RESTART IDENTITY CASCADE"
                    )
                )
            await redis.flushdb()

        client.portal.call(reset)
        yield client
        client.portal.call(reset)


@pytest.fixture
def make_user(client):
    def create(role="user"):
        username = role + uuid4().hex[:8]
        password = "Mi-clave-de-prueba-2026"
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": username,
                "email": username + "@example.com",
                "password": password,
            },
        )
        assert response.status_code == 201, response.text
        user = response.json()

        async def promote():
            async with async_session_factory() as db:
                item = await db.get(User, user["id"])
                item.role = role
                await db.commit()

        client.portal.call(promote)
        login = client.post("/api/v1/auth/token", data={"username": username, "password": password})
        assert login.status_code == 200, login.text
        return {
            **user,
            "password": password,
            "role": role,
            **login.json(),
            "headers": {"Authorization": "Bearer " + login.json()["access_token"]},
        }

    return create


@pytest.fixture
def post_data():
    return {
        "title": "Mi publicación",
        "slug": "mi-publicacion",
        "content": "Contenido suficiente para mi post",
        "status": "published",
    }
