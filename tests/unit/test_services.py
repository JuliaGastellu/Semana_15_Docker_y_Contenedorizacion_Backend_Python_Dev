import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.auth_service import AuthService
from app.schemas import RegisterRequest
from app.exceptions import DuplicateError, UnauthorizedError

pytestmark = pytest.mark.unit


def test_duplicate_registration():
    db = MagicMock()
    db.scalar = AsyncMock(return_value=1)
    with pytest.raises(DuplicateError):
        asyncio.run(
            AuthService(db).register(
                RegisterRequest(username="usuario", email="u@example.com", password="clave1234")
            )
        )


def test_bad_login():
    db = MagicMock()
    db.scalar = AsyncMock(return_value=None)
    with pytest.raises(UnauthorizedError):
        asyncio.run(AuthService(db).authenticate("usuario", "clave1234"))


def test_register_hashes_password():
    db = MagicMock()
    db.scalar = AsyncMock(return_value=None)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    user = asyncio.run(
        AuthService(db).register(
            RegisterRequest(username="usuario", email="u@example.com", password="clave1234")
        )
    )
    assert user.hashed_password != "clave1234"
    db.add.assert_called_once_with(user)
    db.commit.assert_awaited_once()


def test_refresh_rejects_access():
    from datetime import timedelta
    from app.security import create_token

    token, _, _ = create_token(1, "user", "access", timedelta(minutes=1))
    with pytest.raises(UnauthorizedError):
        asyncio.run(AuthService(MagicMock()).rotate(token))
