import pytest
from pydantic import ValidationError
from app.schemas import PostCreate, PostUpdate, UserCreate, RegisterRequest

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("length,valid", [(2, False), (3, True), (200, True), (201, False)])
def test_title(length, valid):
    payload = dict(title="x" * length, slug="post-prueba", content="contenido suficiente")
    if valid:
        assert PostCreate(**payload).title == "x" * length
    else:
        with pytest.raises(ValidationError):
            PostCreate(**payload)


@pytest.mark.parametrize("length,valid", [(7, False), (8, True), (128, True), (129, False)])
def test_password(length, valid):
    payload = dict(username="usuario", email="user@example.com", password="x" * length)
    if valid:
        assert UserCreate(**payload).password == "x" * length
    else:
        with pytest.raises(ValidationError):
            UserCreate(**payload)


@pytest.mark.parametrize("field", ["title", "slug", "content", "status", "tags"])
def test_update_rejects_null(field):
    with pytest.raises(ValidationError):
        PostUpdate(**{field: None})


def test_registration_rejects_role():
    with pytest.raises(ValidationError):
        RegisterRequest(
            username="usuario",
            email="u@example.com",
            password="clave1234",
            role="admin",
        )


def test_post_defaults():
    assert (
        PostCreate(title="Mi post", slug="mi-post", content="Mi contenido completo").status
        == "draft"
    )
