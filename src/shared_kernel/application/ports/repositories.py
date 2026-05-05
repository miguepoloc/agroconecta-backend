"""Generic repository port — collection-like persistence abstraction."""

import abc
import typing

from src.shared_kernel.domain import entities, value_objects

T = typing.TypeVar("T", bound=entities.BaseEntity)
V = typing.TypeVar("V", bound=value_objects.DomainId)


class Page(typing.Generic[T]):
    def __init__(
        self, items: list[T], next_page_token: typing.Optional[str] = None
    ) -> None:
        self.items = items
        self.next_page_token = next_page_token


class Repository(abc.ABC, typing.Generic[T]):
    @abc.abstractmethod
    def model_type(self) -> type[T]:
        raise NotImplementedError

    @abc.abstractmethod
    async def put(self, entity: T) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_id(
        self, id: value_objects.DomainId
    ) -> typing.Optional[T]:
        raise NotImplementedError

    async def find_by_ids(
        self, ids: set[value_objects.DomainId]
    ) -> typing.Iterator[tuple[value_objects.DomainId, T]]:
        raise NotImplementedError

    async def find_all(
        self,
        page_size: int = 20,
        next_page_token: typing.Optional[str] = None,
    ) -> "Page[T]":
        raise NotImplementedError
