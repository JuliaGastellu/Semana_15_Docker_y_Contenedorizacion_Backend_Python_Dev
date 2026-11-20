import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("role,expected", [("user", 403), ("editor", 201), ("admin", 201)])
def test_create_role(client, make_user, post_data, role, expected):
    user = make_user(role)
    assert (
        client.post("/api/v1/posts", json=post_data, headers=user["headers"]).status_code
        == expected
    )


def test_crud_cache(client, make_user, post_data):
    editor = make_user("editor")
    r = client.post("/api/v1/posts", json=post_data, headers=editor["headers"])
    assert r.status_code == 201
    url = "/api/v1/posts/" + str(r.json()["id"])
    assert client.get(url).headers["X-Cache"] == "MISS"
    assert client.get(url).headers["X-Cache"] == "HIT"
    assert (
        client.put(url, json={"title": "Mi título nuevo"}, headers=editor["headers"]).status_code
        == 200
    )
    assert client.get(url).json()["title"] == "Mi título nuevo"
    assert client.delete(url, headers=editor["headers"]).status_code == 204
    assert client.get(url).status_code == 404


def test_private_draft(client, make_user, post_data):
    editor = make_user("editor")
    other = make_user("editor")
    admin = make_user("admin")
    post_data["status"] = "draft"
    item = client.post("/api/v1/posts", json=post_data, headers=editor["headers"]).json()
    url = "/api/v1/posts/" + str(item["id"])
    assert client.get(url).status_code == 404
    assert client.get(url, headers=other["headers"]).status_code == 404
    assert client.get(url, headers=editor["headers"]).status_code == 200
    assert client.get(url, headers=admin["headers"]).status_code == 200
    assert client.get("/api/v1/posts").json()["total"] == 0


def test_ownership(client, make_user, post_data):
    owner = make_user("editor")
    other = make_user("editor")
    item = client.post("/api/v1/posts", json=post_data, headers=owner["headers"]).json()
    url = "/api/v1/posts/" + str(item["id"])
    assert (
        client.put(url, json={"title": "Intento ajeno"}, headers=other["headers"]).status_code
        == 403
    )
    assert client.delete(url, headers=other["headers"]).status_code == 403


def test_filters(client, make_user, post_data):
    editor = make_user("editor")
    client.post("/api/v1/posts", json=post_data, headers=editor["headers"])
    page = client.get("/api/v1/posts?author_id=" + str(editor["id"]) + "&limit=1").json()
    assert page["total"] == 1 and len(page["items"]) == 1


def test_nonexistent(client):
    assert client.get("/api/v1/posts/99999").status_code == 404
