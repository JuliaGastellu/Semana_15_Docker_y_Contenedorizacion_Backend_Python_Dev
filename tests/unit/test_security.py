from datetime import timedelta
import pytest
from app.security import (
    hash_password,
    verify_password,
    create_token,
    decode_token,
    hash_jti,
)
from app.exceptions import UnauthorizedError

pytestmark = pytest.mark.unit


def test_hash_has_salt():
    assert hash_password("clave1234") != hash_password("clave1234")


@pytest.mark.parametrize(
    "password,expected", [("clave1234", True), ("incorrecta", False), ("", False)]
)
def test_verify(password, expected):
    assert verify_password(password, hash_password("clave1234")) is expected


def test_invalid_hash():
    assert verify_password("clave1234", "invalido") is False


def test_jti_is_hash():
    assert len(hash_jti("identificador")) == 64


@pytest.mark.parametrize("role", ["admin", "editor", "user"])
def test_claims(role):
    token, jti, expiry = create_token(4, role, "access", timedelta(minutes=5))
    payload = decode_token(token, "access")
    assert payload["sub"] == "4" and payload["role"] == role and payload["jti"] == jti
    assert payload["exp"] == int(expiry.timestamp())


@pytest.mark.parametrize("kind", ["expired", "wrong_type", "invalid"])
def test_reject_tokens(kind):
    token, _, _ = create_token(
        1,
        "user",
        "refresh" if kind == "wrong_type" else "access",
        timedelta(seconds=-10 if kind == "expired" else 60),
    )
    with pytest.raises(UnauthorizedError):
        decode_token("invalid" if kind == "invalid" else token, "access")
