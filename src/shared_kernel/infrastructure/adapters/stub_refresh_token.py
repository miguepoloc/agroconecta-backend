"""In-memory stub for refresh token storage — used in development."""

import time
import typing


class StubRefreshTokenAdapter:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, typing.Any]] = {}

    async def put(self, token_hash: str, user_id: str, expires_at_unix: int) -> None:
        self._store[token_hash] = {
            "token_hash": token_hash,
            "user_id": user_id,
            "expires_at": expires_at_unix,
            "created_at": int(time.time()),
        }

    async def find_by_hash(self, token_hash: str) -> dict[str, typing.Any] | None:
        item = self._store.get(token_hash)
        if item is None:
            return None
        if int(item["expires_at"]) <= int(time.time()):
            del self._store[token_hash]
            return None
        return item

    async def delete_by_hash(self, token_hash: str) -> None:
        self._store.pop(token_hash, None)

    async def delete_by_user(self, user_id: str) -> None:
        to_delete = [k for k, v in self._store.items() if v["user_id"] == user_id]
        for key in to_delete:
            del self._store[key]
