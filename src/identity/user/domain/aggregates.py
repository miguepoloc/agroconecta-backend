"""User aggregate root."""

from src.shared_kernel.domain import aggregates
from src.identity.user.domain import events as user_events
from src.identity.user.domain import types, value_objects


class User(aggregates.BaseAggregateRoot):
    id: value_objects.UserId
    email: value_objects.Email
    personal_name: value_objects.PersonalName
    phone: value_objects.Phone
    password_hash: value_objects.PasswordHash
    role: types.UserRole
    status: types.UserStatus = types.UserStatus.ACTIVE

    @classmethod
    def register(
        cls,
        email: value_objects.Email,
        first_name: str,
        last_name: str,
        password_hash: value_objects.PasswordHash,
        phone: value_objects.Phone,
        role: types.UserRole,
    ) -> "User":
        user = cls(
            id=value_objects.UserId.generate(),
            email=email,
            personal_name=value_objects.PersonalName(
                first_name=first_name, last_name=last_name
            ),
            phone=phone,
            password_hash=password_hash,
            role=role,
        )
        user.record_event(
            user_events.UserRegistered(
                aggregate_id=str(user.id),
                user_id=str(user.id),
                email=str(user.email),
                first_name=first_name,
                last_name=last_name,
                phone=str(user.phone),
                role=role.value,
            )
        )
        return user

    def change_password(self, new_password_hash: value_objects.PasswordHash) -> None:
        self.password_hash = new_password_hash
        self.touch()
        self.record_event(user_events.UserPasswordChanged(aggregate_id=str(self.id), user_id=str(self.id)))

    def block(self) -> None:
        self.status = types.UserStatus.BLOCKED
        self.touch()

    def activate(self) -> None:
        self.status = types.UserStatus.ACTIVE
        self.touch()

    def is_active(self) -> bool:
        return self.status == types.UserStatus.ACTIVE
