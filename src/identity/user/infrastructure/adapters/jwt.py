"""JWT token creation and verification adapter."""

import hashlib
import secrets
import typing
import uuid
from datetime import UTC, datetime

import jose.jwt

from src.shared_kernel.domain import value_objects as shared_value_objects


def create_access_token(
    user_id: str,
    role: str,
    secret_key: str,
    algorithm: str,
    expire_hours: int,
) -> str:
    now = datetime.now(tz=UTC)
    expire = now.timestamp() + expire_hours * 3600
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire),
        "jti": str(uuid.uuid4()),
    }
    return str(jose.jwt.encode(payload, secret_key, algorithm=algorithm))


def decode_access_token(
    token: str,
    secret_key: str,
    algorithm: str,
) -> dict[str, typing.Any] | None:
    try:
        return typing.cast(
            dict[str, typing.Any],
            jose.jwt.decode(token, secret_key, algorithms=[algorithm]),
        )
    except jose.jwt.ExpiredSignatureError:
        return None
    except jose.jwt.JWTError:
        return None


def generate_refresh_token() -> str:
    return secrets.token_hex(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expires_at(expire_days: int) -> shared_value_objects.PosixTime:
    return shared_value_objects.PosixTime.now().add_days(expire_days)
