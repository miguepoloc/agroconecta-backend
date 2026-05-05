"""Unit of Work for the identity context."""

import sqlalchemy.ext.asyncio

from src.shared_kernel.infrastructure import uow
from src.identity.user.domain import repositories as user_repos
from src.identity.user.infrastructure import repositories as user_infra_repos


class UserUnitOfWork(uow.FastAPIUnitOfWork):
    users: user_repos.UserRepository

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        super().__init__(session)
        self.users = user_infra_repos.SqlAlchemyUserRepository(session)

    def _repositories(self) -> list[user_repos.UserRepository]:  # type: ignore[override]
        return [self.users]
