import pytest

pytestmark = pytest.mark.integration


def test_comment_crud_notification(client, make_user, post_data):
    author = make_user("editor")
    reader = make_user()
    post = client.post("/api/v1/posts", json=post_data, headers=author["headers"]).json()
    url = f"/api/v1/posts/{post['id']}/comments"
    comment = client.post(url, json={"content": "Mi comentario"}, headers=reader["headers"])
    assert comment.status_code == 201, comment.text
    cid = comment.json()["id"]
    assert len(client.get(url).json()) == 1
    assert (
        client.put(
            f"/api/v1/comments/{cid}",
            json={"content": "Mi edición"},
            headers=reader["headers"],
        ).status_code
        == 200
    )
    notices = client.get("/api/v1/notifications", headers=author["headers"]).json()
    assert notices["unread"] == 1
    nid = notices["items"][0]["id"]
    assert (
        client.put(f"/api/v1/notifications/{nid}/read", headers=reader["headers"]).status_code
        == 404
    )
    assert (
        client.put(f"/api/v1/notifications/{nid}/read", headers=author["headers"]).status_code
        == 200
    )
    assert client.delete(f"/api/v1/comments/{cid}", headers=reader["headers"]).status_code == 204
