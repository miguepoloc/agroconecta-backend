"""SQLAlchemy implementation of UserRepository."""

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.identity.user.domain import aggregates as user_aggregates
from src.identity.user.domain import repositories as user_repos
from src.identity.user.domain import value_objects as user_value_objects
from src.identity.user.infrastructure import mappers, models
from src.shared_kernel.domain import value_objects as shared_value_objects


class SqlAlchemyUserRepository(user_repos.UserRepository):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._seen: set[user_aggregates.User] = set()

    async def put(self, entity: user_aggregates.User) -> None:
        orm = mappers.domain_to_orm(entity)
        await self._session.merge(orm)
        self._seen.add(entity)

    async def find_by_id(self, id: shared_value_objects.DomainId) -> user_aggregates.User | None:
        result = await self._session.get(models.UserOrm, str(id))
        if result is None:
            return None
        user = mappers.orm_to_domain(result)
        self._seen.add(user)
        return user

    async def find_by_email(self, email: user_value_objects.Email) -> user_aggregates.User | None:
        stmt = sqlalchemy.select(models.UserOrm).where(models.UserOrm.email == str(email))
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        user = mappers.orm_to_domain(orm)
        self._seen.add(user)
        return user
