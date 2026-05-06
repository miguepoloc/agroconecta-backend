"""Unit of Work port — transaction coordination (Cosmic Python Ch. 6)."""

import abc
import typing

from src.shared_kernel.application.ports import repositories
from src.shared_kernel.domain import events


class AbstractUnitOfWork(abc.ABC):
    async def __aenter__(self) -> typing.Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    @abc.abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError

    def collect_new_events(
        self,
    ) -> typing.Generator[events.DomainEvent, None, None]:
        for repo in self._repositories():
            if hasattr(repo, "_seen"):
                for aggregate in repo._seen:
                    yield from aggregate.pull_events()

    def _repositories(self) -> list[repositories.Repository]:  # type: ignore[type-arg]
        return []
