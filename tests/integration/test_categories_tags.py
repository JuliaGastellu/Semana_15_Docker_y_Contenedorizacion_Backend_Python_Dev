import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "role,category,tag", [("user", 403, 403), ("editor", 403, 201), ("admin", 201, 201)]
)
def test_catalog_roles(client, make_user, role, category, tag):
    user = make_user(role)
    assert (
        client.post(
            "/api/v1/categories",
            json={"name": "Mi categoría", "slug": "mi-categoria"},
            headers=user["headers"],
        ).status_code
        == category
    )
    assert (
        client.post(
            "/api/v1/tags",
            json={"name": "Mi tag", "slug": "mi-tag"},
            headers=user["headers"],
        ).status_code
        == tag
    )


def test_catalog_reads(client):
    assert client.get("/api/v1/categories").status_code == 200
    assert client.get("/api/v1/tags").status_code == 200
