"""Unit tests for the User aggregate."""

import pytest

from src.identity.user.domain import aggregates, events, exceptions, types, value_objects
from src.identity.user.infrastructure.adapters import password


def make_user(role: types.UserRole = types.UserRole.COMPRADOR) -> aggregates.User:
    return aggregates.User.register(
        email=value_objects.Email(value="test@agroconecta.co"),
        first_name="Juan",
        last_name="García",
        password_hash=password.hash_password("secret123"),
        phone=value_objects.Phone(value="+573001234567"),
        role=role,
    )


class TestUserRegistration:
    def test_register_emits_user_registered_event(self) -> None:
        user = make_user()
        pending = user.pull_events()

        assert len(pending) == 1
        assert isinstance(pending[0], events.UserRegistered)
        assert pending[0].email == "test@agroconecta.co"
        assert pending[0].role == "comprador"

    def test_register_sets_active_status(self) -> None:
        user = make_user()
        assert user.status == types.UserStatus.ACTIVE
        assert user.is_active()

    def test_register_normalizes_email_to_lowercase(self) -> None:
        user = aggregates.User.register(
            email=value_objects.Email(value="UPPER@AGROCONECTA.CO"),
            first_name="Ana",
            last_name="López",
            password_hash=password.hash_password("pass"),
            phone=value_objects.Phone(value="+573009999999"),
            role=types.UserRole.AGRICULTOR,
        )
        assert str(user.email) == "upper@agroconecta.co"

    def test_pull_events_clears_queue(self) -> None:
        user = make_user()
        user.pull_events()
        assert not user.has_pending_events()


class TestUserPasswordChange:
    def test_change_password_emits_event(self) -> None:
        user = make_user()
        user.pull_events()

        new_hash = password.hash_password("newpass456")
        user.change_password(new_hash)

        pending = user.pull_events()
        assert len(pending) == 1
        assert isinstance(pending[0], events.UserPasswordChanged)

    def test_change_password_updates_hash(self) -> None:
        user = make_user()
        new_hash = password.hash_password("newpass456")
        user.change_password(new_hash)

        assert password.verify_password("newpass456", user.password_hash)


class TestUserStatusTransitions:
    def test_block_user(self) -> None:
        user = make_user()
        user.block()
        assert user.status == types.UserStatus.BLOCKED
        assert not user.is_active()

    def test_reactivate_blocked_user(self) -> None:
        user = make_user()
        user.block()
        user.activate()
        assert user.is_active()


class TestEmailValueObject:
    def test_invalid_email_raises(self) -> None:
        with pytest.raises(Exception):
            value_objects.Email(value="not-an-email")

    def test_email_is_case_insensitive(self) -> None:
        e1 = value_objects.Email(value="User@Test.com")
        e2 = value_objects.Email(value="user@test.com")
        assert e1 == e2
