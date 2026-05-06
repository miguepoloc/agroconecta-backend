"""Domain event base — immutable facts about state changes."""

import pydantic

from src.shared_kernel.domain import base_model, value_objects


class DomainEvent(base_model.DomainModel):
    model_config = pydantic.ConfigDict(frozen=True)

    event_id: value_objects.UuidId = pydantic.Field(default_factory=value_objects.UuidId.generate)
    occurred_on: value_objects.PosixTime = pydantic.Field(
        default_factory=value_objects.PosixTime.now
    )
    aggregate_id: str
    correlation_id: value_objects.UuidId = pydantic.Field(
        default_factory=value_objects.UuidId.generate
    )
    version: int = 1

    @property
    def event_name(self) -> str:
        return self.__class__.__name__

    def idempotence_key(self) -> str:
        return f"{self.event_name}-{self.event_id}"
