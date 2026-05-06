"""User domain enumerations."""

import enum


class UserRole(enum.StrEnum):
    COMPRADOR = "comprador"
    AGRICULTOR = "agricultor"
    INSTITUCION = "institucion"
    ADMIN = "admin"


class UserStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    DELETED = "deleted"
