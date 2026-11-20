"""Ejecuto un recorrido aislado contra PostgreSQL y Redis de prueba."""

from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
import asyncio
from app.main import app
from app.database import async_session_factory
from app.models import User
from sqlalchemy import select


def run():
    suffix = uuid4().hex[:8]
    password = "Mi-clave-de-prueba-2026"
    with TestClient(app) as client:
        names = {}
        for role in ("admin", "editor", "user"):
            username = role + suffix
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "username": username,
                    "email": username + "@example.com",
                    "password": password,
                },
            )
            assert response.status_code == 201, response.text
            names[role] = response.json()

        async def promote():
            async with async_session_factory() as db:
                for role in ("admin", "editor"):
                    item = await db.get(User, names[role]["id"])
                    item.role = role
                await db.commit()

        client.portal.call(promote)
        tokens = {}
        for role in names:
            response = client.post(
                "/api/v1/auth/token",
                data={"username": names[role]["username"], "password": password},
            )
            assert response.status_code == 200, response.text
            tokens[role] = response.json()

        def headers(role):
            return {"Authorization": "Bearer " + tokens[role]["access_token"]}

        category = client.post(
            "/api/v1/categories",
            json={"name": "Categoría " + suffix, "slug": "categoria-" + suffix},
            headers=headers("admin"),
        )
        assert category.status_code == 201, category.text
        post = client.post(
            "/api/v1/posts",
            json={
                "title": "Mi post de prueba",
                "slug": "post-" + suffix,
                "content": "Contenido de prueba suficiente",
                "status": "published",
                "category_id": category.json()["id"],
            },
            headers=headers("editor"),
        )
        assert post.status_code == 201, post.text
        post_id = post.json()["id"]
        first = client.get(f"/api/v1/posts/{post_id}")
        second = client.get(f"/api/v1/posts/{post_id}")
        assert first.status_code == second.status_code == 200
        assert second.headers["X-Cache"] == "HIT"
        edit = client.put(
            f"/api/v1/posts/{post_id}",
            json={"title": "Mi título actualizado"},
            headers=headers("editor"),
        )
        assert edit.status_code == 200, edit.text
        refreshed = client.get(f"/api/v1/posts/{post_id}")
        assert refreshed.headers["X-Cache"] == "MISS"
        assert refreshed.json()["title"] == "Mi título actualizado"
        denied = client.put(
            f"/api/v1/posts/{post_id}",
            json={"title": "No permitido"},
            headers=headers("user"),
        )
        assert denied.status_code == 403
        draft = client.put(
            "/api/v1/autosave",
            json={"title": "Mi borrador", "content": "Contenido"},
            headers=headers("editor"),
        )
        assert draft.status_code == 200, draft.text
        assert (
            client.get("/api/v1/autosave", headers=headers("editor")).json()["title"]
            == "Mi borrador"
        )
        comment = client.post(
            f"/api/v1/posts/{post_id}/comments",
            json={"content": "Mi comentario"},
            headers=headers("user"),
        )
        assert comment.status_code == 201, comment.text
        notifications = client.get("/api/v1/notifications", headers=headers("editor"))
        assert notifications.status_code == 200 and notifications.json()["total"] >= 1, (
            notifications.text
        )
        assert client.get("/health").json()["redis"] == "ok"
        assert (
            client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": tokens["user"]["refresh_token"]},
            ).status_code
            == 200
        )
        print(
            "Registro, login, RBAC, CRUD, caché HIT/MISS, invalidación, autosave, notificaciones, refresh y health: OK"
        )


if __name__ == "__main__":
    run()
