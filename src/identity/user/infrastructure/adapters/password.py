"""bcrypt password hashing adapter."""

import bcrypt

from src.identity.user.domain import value_objects


def hash_password(plain_password: str) -> value_objects.PasswordHash:
    hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt())
    return value_objects.PasswordHash(value=hashed.decode())


def verify_password(plain_password: str, password_hash: value_objects.PasswordHash) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.value.encode())
