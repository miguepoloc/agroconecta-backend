"""Layer supertype — decouples domain from Pydantic specifics."""

import json
import typing

import pydantic


class DomainModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        validate_assignment=True,
        populate_by_name=True,
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    def to_dict(self) -> dict[str, typing.Any]:
        return self.model_dump(mode="json")

    def to_primitive_dict(self) -> dict[str, typing.Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> "DomainModel":
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, json_str: str) -> "DomainModel":
        return cls.model_validate(json.loads(json_str))
