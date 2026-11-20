import io
import pytest
from starlette.websockets import WebSocketDisconnect

pytestmark = pytest.mark.integration


def test_upload_download_export(client, make_user, post_data):
    editor = make_user("editor")
    post = client.post("/api/v1/posts", json=post_data, headers=editor["headers"]).json()
    url = f"/api/v1/posts/{post['id']}/image"
    assert client.get(url).status_code == 404
    invalid = client.post(
        url,
        files={"file": ("fake.png", b"not png", "image/png")},
        headers=editor["headers"],
    )
    assert invalid.status_code == 415
    large = client.post(
        url,
        files={"file": ("large.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")},
        headers=editor["headers"],
    )
    assert large.status_code == 413
    data = b"\x89PNG\r\n\x1a\n" + b"sample"
    valid = client.post(
        url, files={"file": ("foto.png", data, "image/png")}, headers=editor["headers"]
    )
    assert valid.status_code == 200, valid.text
    assert client.get(url).content == data
    again = client.post(
        url, files={"file": ("foto.png", data, "image/png")}, headers=editor["headers"]
    )
    assert again.status_code == 200
    exported = client.get("/api/v1/posts/export")
    assert (
        exported.status_code == 200
        and "id,slug,title" in exported.text
        and post_data["slug"] in exported.text
    )
    assert client.get("/api/v1/posts/export", headers=editor["headers"]).status_code == 200


def test_autosave_and_profile(client, make_user, post_data):
    user = make_user("editor")
    assert client.get("/api/v1/autosave", headers=user["headers"]).status_code == 404
    assert (
        client.put(
            "/api/v1/autosave",
            json={"title": "Mi borrador", "content": "Mi contenido"},
            headers=user["headers"],
        ).status_code
        == 200
    )
    assert client.get("/api/v1/autosave", headers=user["headers"]).json()["title"] == "Mi borrador"
    assert client.delete("/api/v1/autosave", headers=user["headers"]).status_code == 204
    assert client.get("/api/v1/users/me", headers=user["headers"]).status_code == 200
    assert (
        client.put(
            "/api/v1/users/me",
            json={"email": "nuevo@example.com"},
            headers=user["headers"],
        ).status_code
        == 200
    )
    post_data["status"] = "draft"
    client.post("/api/v1/posts", json=post_data, headers=user["headers"])
    assert len(client.get("/api/v1/users/me/posts", headers=user["headers"]).json()) == 1


def test_websocket_ping(client, make_user):
    user = make_user()
    assert client.get("/api/v1/ws/client").status_code == 200
    with client.websocket_connect(
        "/api/v1/ws/notifications?token=" + user["access_token"]
    ) as socket:
        socket.send_text("ping")
        assert socket.receive_json() == {"type": "pong"}
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws/notifications?token=invalid"):
            pass


def test_websocket_comment_delivery(client, make_user, post_data):
    author = make_user("editor")
    reader = make_user()
    post = client.post("/api/v1/posts", json=post_data, headers=author["headers"]).json()
    with client.websocket_connect(
        "/api/v1/ws/notifications?token=" + author["access_token"]
    ) as socket:
        response = client.post(
            f"/api/v1/posts/{post['id']}/comments",
            json={"content": "Comentario con aviso"},
            headers=reader["headers"],
        )
        assert response.status_code == 201
        assert socket.receive_json()["post_id"] == post["id"]


def test_user_admin_crud(client, make_user):
    admin = make_user("admin")
    data = {
        "username": "nuevo_usuario",
        "email": "nuevo@example.com",
        "password": "clave1234",
    }
    created = client.post("/api/v1/users", json=data, headers=admin["headers"])
    assert created.status_code == 201, created.text
    uid = created.json()["id"]
    url = f"/api/v1/users/{uid}"
    assert client.get("/api/v1/users", headers=admin["headers"]).status_code == 200
    assert client.get(url, headers=admin["headers"]).headers["X-Cache"] == "MISS"
    assert client.get(url, headers=admin["headers"]).headers["X-Cache"] == "HIT"
    assert (
        client.put(url, json={"email": "editado@example.com"}, headers=admin["headers"]).status_code
        == 200
    )
    assert client.get(url, headers=admin["headers"]).json()["email"] == "editado@example.com"
    assert client.delete(url, headers=admin["headers"]).status_code == 204
    assert client.get(url, headers=admin["headers"]).status_code == 404


def test_category_detail_delete(client, make_user):
    admin = make_user("admin")
    item = client.post(
        "/api/v1/categories",
        json={"name": "Mi categoría", "slug": "mi-categoria"},
        headers=admin["headers"],
    ).json()
    url = f"/api/v1/categories/{item['id']}"
    assert client.get(url).status_code == 200
    assert client.delete(url, headers=admin["headers"]).status_code == 204
    assert client.get(url).status_code == 404
