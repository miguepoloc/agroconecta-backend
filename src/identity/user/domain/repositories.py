"""User repository port."""

import abc
import typing

from src.shared_kernel.application.ports import repositories
from src.identity.user.domain import aggregates as user_aggregates
from src.identity.user.domain import value_objects as user_value_objects


class UserRepository(repositories.Repository[user_aggregates.User]):
    def model_type(self) -> type[user_aggregates.User]:
        return user_aggregates.User

    @abc.abstractmethod
    async def find_by_email(
        self, email: user_value_objects.Email
    ) -> typing.Optional[user_aggregates.User]:
        raise NotImplementedError
