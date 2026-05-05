"""User domain events."""

from src.shared_kernel.domain import events


class UserRegistered(events.DomainEvent):
    user_id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    role: str


class UserPasswordChanged(events.DomainEvent):
    user_id: str
