"""User domain enumerations."""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    COMPRADOR = "comprador"
    AGRICULTOR = "agricultor"
    INSTITUCION = "institucion"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    DELETED = "deleted"
