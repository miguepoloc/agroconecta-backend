"""User domain exceptions."""

from src.shared_kernel.domain import exceptions


class InvalidCredentialsError(exceptions.AuthorizationError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class EmailAlreadyExistsError(exceptions.ConflictError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Email already registered: {email}")


class UserNotFoundError(exceptions.NotFoundError):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"User not found: {identifier}")


class UserBlockedError(exceptions.AuthorizationError):
    def __init__(self) -> None:
        super().__init__("User account is blocked")
