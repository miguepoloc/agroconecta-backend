"""Domain exceptions — never carry infrastructure concerns."""


class DomainException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainException):...

class ConflictError(DomainException):...

class ValidationError(DomainException):...

class AuthorizationError(DomainException):...

class BusinessRuleViolationError(DomainException):...
