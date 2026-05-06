"""Shared pytest fixtures."""

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://agroconecta:agroconecta@localhost:5432/agroconecta"
)
os.environ.setdefault(
    "DATABASE_URL_TEST",
    "postgresql+asyncpg://agroconecta_test:agroconecta_test@localhost:5433/agroconecta_test",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")
