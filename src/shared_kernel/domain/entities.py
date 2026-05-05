"""Base entity — identity-based equality, mutable."""

from src.shared_kernel.domain import base_model, value_objects


class BaseEntity(base_model.DomainModel):
    id: value_objects.DomainId
    created_at: value_objects.PosixTime = value_objects.PosixTime.now()
    updated_at: value_objects.PosixTime = value_objects.PosixTime.now()

    def touch(self) -> None:
        self.updated_at = value_objects.PosixTime.now()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
