import pytest

pytestmark = pytest.mark.integration


def test_register(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"username": "usuario", "email": "u@example.com", "password": "clave1234"},
    )
    assert r.status_code == 201 and "hashed_password" not in r.json()


@pytest.mark.parametrize("field", ["email", "username"])
def test_duplicate(client, make_user, field):
    user = make_user()
    data = {"username": "otro", "email": "otro@example.com", "password": "clave1234"}
    data[field] = user[field]
    assert client.post("/api/v1/auth/register", json=data).status_code == 409


def test_login_and_me(client, make_user):
    user = make_user()
    assert client.get("/api/v1/auth/me", headers=user["headers"]).json()["id"] == user["id"]


def test_wrong_password(client, make_user):
    user = make_user()
    assert (
        client.post(
            "/api/v1/auth/token",
            data={"username": user["username"], "password": "incorrecta"},
        ).status_code
        == 401
    )


@pytest.mark.parametrize("token", ["invalid", "", "Bearer xyz"])
def test_bad_token(client, token):
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + token}).status_code
        == 401
    )


def test_rotation_and_reuse(client, make_user):
    user = make_user()
    old = user["refresh_token"]
    new = client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert new.status_code == 200 and new.json()["refresh_token"] != old
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": old}).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": new.json()["refresh_token"]}
        ).status_code
        == 401
    )


def test_logout(client, make_user):
    user = make_user()
    assert (
        client.post(
            "/api/v1/auth/logout", json={"refresh_token": user["refresh_token"]}
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": user["refresh_token"]}
        ).status_code
        == 401
    )
