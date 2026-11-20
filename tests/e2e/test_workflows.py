import pytest

pytestmark = pytest.mark.e2e


def test_full_blog_workflow(client, make_user, post_data):
    admin = make_user("admin")
    editor = make_user("editor")
    reader = make_user()
    category = client.post(
        "/api/v1/categories",
        json={"name": "Mi categoría", "slug": "mi-categoria"},
        headers=admin["headers"],
    ).json()
    tag = client.post(
        "/api/v1/tags",
        json={"name": "Python", "slug": "python"},
        headers=editor["headers"],
    ).json()
    post_data.update(category_id=category["id"], tags=[tag["slug"]], status="draft")
    post = client.post("/api/v1/posts", json=post_data, headers=editor["headers"]).json()
    url = f"/api/v1/posts/{post['id']}"
    assert client.get(url).status_code == 404
    assert (
        client.put(url, json={"status": "published"}, headers=editor["headers"]).status_code == 200
    )
    assert (
        client.post(
            url + "/comments",
            json={"content": "Mi comentario"},
            headers=reader["headers"],
        ).status_code
        == 201
    )
    assert len(client.get(url + "/comments").json()) == 1


def test_rbac_workflow(client, make_user, post_data):
    admin = make_user("admin")
    editor = make_user("editor")
    reader = make_user()
    assert (
        client.post("/api/v1/posts", json=post_data, headers=reader["headers"]).status_code == 403
    )
    assert (
        client.post(
            "/api/v1/categories",
            json={"name": "Mi categoría", "slug": "mi-categoria"},
            headers=editor["headers"],
        ).status_code
        == 403
    )
    post = client.post("/api/v1/posts", json=post_data, headers=editor["headers"]).json()
    assert client.delete(f"/api/v1/posts/{post['id']}", headers=admin["headers"]).status_code == 204
