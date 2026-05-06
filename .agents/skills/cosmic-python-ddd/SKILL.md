---
name: cosmic-python-ddd
description: |
  Expert guide for the AgroConecta backend architecture: Hexagonal + DDD following Cosmic Python (cosmicpython.com).
  Use this skill whenever the user asks to: create a new bounded context, add a new endpoint, implement a use case or command handler, add domain events, create aggregates or value objects, write repositories or mappers, understand how the layers connect, or debug any architectural question about this codebase.
  Also trigger for: "cómo agrego un endpoint", "crear contexto acotado", "implementar caso de uso", "agregar evento de dominio", "entender la arquitectura", "cómo funciona el UoW", "cómo hago el mapper", "cómo registro el router".
---

# AgroConecta Backend — Cosmic Python DDD Architecture

## Mental model

The architecture has **zero coupling** between layers in one direction: the domain knows nothing about the DB, HTTP, or AWS. Dependencies flow inward only.

```
HTTP request
    → FastAPI Router (infrastructure/entrypoints/)
        → Command Handler (application/handlers/)
            → UnitOfWork + Repository (application/ + infrastructure/)
                → Domain Aggregate (domain/)
                    → Domain Events (domain/events.py)
                        → Event Publisher (shared_kernel)
```

Three bounded contexts live under `src/`:
- `identity/user/` — authentication, users
- `catalog/farmer/` — farmers + certifications
- `catalog/product/` — products, prices, traceability

Each context has the same internal structure:
```
<context>/
├── domain/          aggregates.py, value_objects.py, events.py, exceptions.py, repositories.py, types.py
├── application/     handlers/commands.py, handlers/queries.py, dtos/inputs.py, dtos/outputs.py, unit_of_work.py
└── infrastructure/  models.py, mappers.py, repositories.py, entrypoints/router.py
```

---

## Import conventions (strict — never deviate)

```python
# ✅ Correct
import typing
from src.identity.user.domain import aggregates as user_aggregates
from src.shared_kernel.domain import value_objects as shared_value_objects

# ❌ Wrong — all three of these
from __future__ import annotations
from .aggregates import User
from typing import Optional
```

Rules:
- **No** `from __future__ import annotations`
- **No** relative imports (`from .module import X`) — always absolute (`from src....`)
- **No** `from typing import X` — use `import typing` then `typing.Generator`, etc.
- **Use `X | None`** instead of `typing.Optional[X]` for optional fields and return types
- Import the **module**, not the class: `from src.identity.user.domain import aggregates` then `aggregates.User`

```python
# ✅ Optional fields
bio: str | None = None
async def find_by_email(self, email: str) -> aggregates.User | None: ...

# ❌ Never
bio: typing.Optional[str] = None
async def find_by_email(self, email: str) -> typing.Optional[aggregates.User]: ...
```

---

## Code style rules

### Empty exception classes use `...` not `pass`
```python
# ✅ Correct
class MyEntityConflictError(shared_exceptions.ConflictError): ...

# ❌ Wrong
class MyEntityConflictError(shared_exceptions.ConflictError):
    pass
```

### `__init__.py` files are always empty
Every package needs an `__init__.py` — leave it completely empty. Never put imports or code in them.

### Abstract methods never use `raise NotImplementedError`
`@abc.abstractmethod` already prevents calling unimplemented methods. The body should be `...`.
```python
# ✅ Correct
@abc.abstractmethod
async def find_by_name(self, name: str) -> aggregates.MyEntity | None: ...

# ❌ Wrong
@abc.abstractmethod
async def find_by_name(self, name: str) -> aggregates.MyEntity | None:
    raise NotImplementedError
```

### No `# type: ignore` comments
Never suppress type errors with `# type: ignore[override]` or similar. Fix the actual type mismatch instead. Consistent typing is non-negotiable.

### Functions should be small and focused
Split large handlers into private helper functions. A function that builds an output DTO, validates a condition, or constructs domain objects should be its own function, not inline code inside the handler.

```python
# ✅ Small, named helpers
def _to_output(entity: aggregates.MyEntity) -> outputs.EntityOutput:
    return outputs.EntityOutput(id=str(entity.id), name=entity.name)

def _build_items(raw_items: list[inputs.ItemInput]) -> list[aggregates.OrderItem]:
    return [aggregates.OrderItem(...) for i in raw_items]

async def handle_create_order(command, session, publisher):
    async with uow:
        items = _build_items(command.items)
        order = aggregates.Order.place(items=items, ...)
        await uow.orders.put(order)
        await uow.commit()
        events = list(uow.collect_new_events())
    await publisher.publish_many(events)
    return _to_output(order)
```

---

## Enums — use `enum.auto()` with StrEnum

**Never hardcode string values.** Use `enum.auto()` with the appropriate base class:

- **`enum.StrEnum`** — Python 3.11 built-in, `auto()` generates **lowercase** member name
- **`UpperStrEnum`** — custom base class (add to `shared_kernel/domain/types.py` if needed), `auto()` generates **uppercase** member name

```python
# ✅ Correct — lowercase values (status, ranks, categories)
import enum

class OrderStatus(enum.StrEnum):
    PENDING = enum.auto()    # → "pending"
    CONFIRMED = enum.auto()  # → "confirmed"
    CANCELLED = enum.auto()  # → "cancelled"

class SustainabilityRank(enum.StrEnum):
    BRONZE = enum.auto()  # → "bronze"
    SILVER = enum.auto()  # → "silver"
    GOLD = enum.auto()    # → "gold"

# ✅ Correct — uppercase values (ISO codes, external identifiers)
# First add UpperStrEnum to src/shared_kernel/domain/types.py:
class UpperStrEnum(enum.StrEnum):
    @staticmethod
    def _generate_next_value_(name, _start, _count, _last_values) -> str:
        return name  # returns the member name verbatim (already uppercase)

class CertificationType(UpperStrEnum):
    GLOBAL_GAP = enum.auto()  # → "GLOBAL_GAP"
    FAIR_TRADE = enum.auto()  # → "FAIR_TRADE"

# ❌ Wrong — hardcoded strings
class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
```

The ORM column maps the string value: `entity.status.value` → `"pending"`, and `OrderStatus("pending")` reconstructs the enum from DB.

---

## Domain layer — what lives here

**Rule**: Zero infrastructure imports. No SQLAlchemy, no FastAPI, no boto3.

### Aggregates (domain/aggregates.py)
The aggregate is the transactional boundary. All state changes go through it.

Nested objects that **belong to the aggregate** but have their own identity use `BaseEntity`. Nested objects identified only by their data use `BaseValueObject` (frozen). Never use raw `pydantic.BaseModel` directly.

```python
import pydantic
from src.shared_kernel.domain import aggregates as shared_aggregates
from src.shared_kernel.domain import entities as shared_entities
from src.shared_kernel.domain import value_objects as shared_vo
from src.my_context.my_entity.domain import value_objects, events, types

# Nested value (no identity — immutable, equality by data)
class OrderItem(shared_vo.BaseValueObject):
    product_id: value_objects.ProductId
    quantity_kg: value_objects.QuantityKg

# Nested entity (has identity — mutable, equality by id)
class Certification(shared_entities.BaseEntity):
    id: value_objects.CertificationId
    certification_type: types.CertificationType
    expires_at: shared_vo.PosixTime

# Aggregate root
class MyEntity(shared_aggregates.BaseAggregateRoot):
    id: value_objects.MyEntityId
    name: str
    status: types.MyStatus = types.MyStatus.PENDING
    # auto fields from BaseEntity: created_at, updated_at, version

    @classmethod
    def create(cls, name: str) -> "MyEntity":
        entity = cls(id=value_objects.MyEntityId.generate(), name=name)
        entity.record_event(events.MyEntityCreated(name=name))
        return entity

    def deactivate(self) -> None:
        if self.status == types.MyStatus.INACTIVE:
            raise exceptions.AlreadyInactiveError()
        self.status = types.MyStatus.INACTIVE
        self.touch()
        self.record_event(events.MyEntityDeactivated())
```

`record_event()` automatically sets `aggregate_id`. `pull_events()` returns and clears the list (pull-and-clear — called by `uow.collect_new_events()` after commit).

### Value Objects (domain/value_objects.py)
```python
import pydantic
from src.shared_kernel.domain import value_objects as shared_vo

class MyEntityId(shared_vo.HumanFriendlyId): ...  # inherits generate()

class MyName(shared_vo.BaseValueObject):
    value: str

    @pydantic.field_validator("value")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
```

### DomainEvent (domain/events.py)
```python
from src.shared_kernel.domain import events as domain_events

class SomethingHappened(domain_events.DomainEvent):
    # auto fields: event_id (UUID), occurred_on (PosixTime), aggregate_id, correlation_id
    field_a: str
    field_b: int
```
Events are frozen Pydantic models. Name them as past-tense facts.

### Repository port (domain/repositories.py)
This is the interface — implementation lives in infrastructure. No `raise NotImplementedError` in abstract methods.
```python
import abc
from src.shared_kernel.application.ports import repositories as shared_repos
from src.my_context.my_entity.domain import aggregates

class MyEntityRepository(shared_repos.Repository[aggregates.MyEntity]):
    def model_type(self) -> type[aggregates.MyEntity]:
        return aggregates.MyEntity

    @abc.abstractmethod
    async def find_by_name(self, name: str) -> aggregates.MyEntity | None: ...
```

### Exceptions (domain/exceptions.py)
```python
from src.shared_kernel.domain import exceptions as shared_exceptions

class MyEntityNotFoundError(shared_exceptions.NotFoundError):
    def __init__(self, entity_id: str) -> None:
        super().__init__(f"MyEntity {entity_id} not found")

# Empty subclasses use `...`
class MyEntityConflictError(shared_exceptions.ConflictError): ...
class MyEntityBlockedError(shared_exceptions.AuthorizationError): ...
```

Base exception classes: `NotFoundError`, `ConflictError`, `ValidationError`, `AuthorizationError`, `BusinessRuleViolationError`.

---

## Application layer — orchestration only

No domain logic here. No business rules. Just: fetch → validate → invoke domain → persist → publish events. Keep handlers small — extract private helpers.

### Unit of Work (application/unit_of_work.py)
```python
import sqlalchemy.ext.asyncio
from src.shared_kernel.infrastructure import uow as shared_uow
from src.my_context.my_entity.infrastructure import repositories

class MyEntityUnitOfWork(shared_uow.FastAPIUnitOfWork):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        super().__init__(session)
        self.my_entities = repositories.SqlAlchemyMyEntityRepository(session)

    def _repositories(self) -> list[repositories.SqlAlchemyMyEntityRepository]:
        return [self.my_entities]
```

`FastAPIUnitOfWork` wraps the request-scoped session from `request.state.db_session`. Use `SqlAlchemyUnitOfWork` for Lambda jobs or CLI scripts that manage their own session.

### Command Handler (application/handlers/commands.py)
```python
import sqlalchemy.ext.asyncio
from src.shared_kernel.application.ports import event_publisher as event_publisher_port
from src.my_context.my_entity.application import unit_of_work as my_uow
from src.my_context.my_entity.application.dtos import inputs, outputs
from src.my_context.my_entity.domain import aggregates, exceptions, value_objects


def _to_output(entity: aggregates.MyEntity) -> outputs.EntityOutput:
    return outputs.EntityOutput(
        id=str(entity.id),
        name=entity.name,
        created_at=entity.created_at.to_isoformat(),
    )


async def _ensure_name_available(uow: my_uow.MyEntityUnitOfWork, name: str) -> None:
    existing = await uow.my_entities.find_by_name(name)
    if existing is not None:
        raise exceptions.MyEntityConflictError()


async def handle_create_entity(
    command: inputs.CreateEntityInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    publisher: event_publisher_port.AbstractEventPublisher,
) -> outputs.EntityOutput:
    async with my_uow.MyEntityUnitOfWork(session) as uow:
        await _ensure_name_available(uow, command.name)
        entity = aggregates.MyEntity.create(name=command.name)
        await uow.my_entities.put(entity)
        await uow.commit()
        pending_events = list(uow.collect_new_events())   # INSIDE async with

    await publisher.publish_many(pending_events)           # OUTSIDE async with
    return _to_output(entity)
```

**Critical**: `collect_new_events()` must be called **inside** the `async with` block (needs `repo._seen`). `publisher.publish_many()` goes **outside** (if it fails, the DB commit already happened — no rollback).

### DTOs (application/dtos/)
```python
# inputs.py
from src.shared_kernel.domain import base_model

class CreateEntityInput(base_model.DomainModel):
    name: str
    description: str | None = None

# outputs.py
class EntityOutput(base_model.DomainModel):
    id: str
    name: str
    created_at: str  # ISO format string
```

DTOs are plain Pydantic models — carry data in/out, contain no logic.

---

## Infrastructure layer — DB and HTTP

### ORM Model (infrastructure/models.py)
```python
import sqlalchemy
import sqlalchemy.orm
from src.shared_kernel.infrastructure.database import base

class MyEntityOrm(base.Base):
    __tablename__ = "my_entities"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(10), primary_key=True          # HumanFriendlyId → String(10)
    )
    name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), nullable=False, unique=True, index=True
    )
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, default="pending"
    )
    version: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=1
    )
    created_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False            # PosixTime → BigInteger (microseconds)
    )
    updated_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
```

ORM models **never enter the domain layer**. They are infrastructure objects only.

### Data Mapper (infrastructure/mappers.py)
```python
from src.my_context.my_entity.domain import aggregates, value_objects, types
from src.my_context.my_entity.infrastructure import models
from src.shared_kernel.domain import value_objects as shared_vo


def orm_to_domain(orm: models.MyEntityOrm) -> aggregates.MyEntity:
    return aggregates.MyEntity(
        id=value_objects.MyEntityId(value=orm.id),
        name=orm.name,
        status=types.MyStatus(orm.status),
        version=orm.version,
        created_at=shared_vo.PosixTime(microseconds=orm.created_at),
        updated_at=shared_vo.PosixTime(microseconds=orm.updated_at),
    )


def domain_to_orm(entity: aggregates.MyEntity) -> models.MyEntityOrm:
    return models.MyEntityOrm(
        id=str(entity.id),
        name=entity.name,
        status=entity.status.value,
        version=entity.version,
        created_at=entity.created_at.microseconds,
        updated_at=entity.updated_at.microseconds,
    )
```

The mapper is the only place that knows about both ORM and domain types.

### Repository (infrastructure/repositories.py)
```python
import typing
import sqlalchemy
import sqlalchemy.ext.asyncio
from src.shared_kernel.domain import value_objects as shared_vo
from src.my_context.my_entity.domain import aggregates
from src.my_context.my_entity.domain import repositories as repo_port
from src.my_context.my_entity.infrastructure import mappers, models


class SqlAlchemyMyEntityRepository(repo_port.MyEntityRepository):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._seen: set[aggregates.MyEntity] = set()

    async def put(self, entity: aggregates.MyEntity) -> None:
        orm = mappers.domain_to_orm(entity)
        await self._session.merge(orm)
        self._seen.add(entity)

    async def find_by_id(self, id: shared_vo.DomainId) -> aggregates.MyEntity | None:
        result = await self._session.get(models.MyEntityOrm, str(id))
        if result is None:
            return None
        entity = mappers.orm_to_domain(result)
        self._seen.add(entity)
        return entity

    async def find_by_name(self, name: str) -> aggregates.MyEntity | None:
        stmt = sqlalchemy.select(models.MyEntityOrm).where(models.MyEntityOrm.name == name)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        entity = mappers.orm_to_domain(orm)
        self._seen.add(entity)
        return entity
```

Always add to `self._seen` after loading — enables `uow.collect_new_events()` to find all modified aggregates.

### Router (infrastructure/entrypoints/router.py)
```python
import typing
import fastapi
from src.shared_kernel.infrastructure import config as app_config
from src.my_context.my_entity.application.dtos import inputs, outputs
from src.my_context.my_entity.application.handlers import commands, queries

router = fastapi.APIRouter(prefix="/my-entities", tags=["my-entities"])


async def _get_settings() -> typing.AsyncGenerator[app_config.Settings, None]:
    yield app_config.get_settings()


SettingsDep = typing.Annotated[app_config.Settings, fastapi.Depends(_get_settings)]


@router.post("", response_model=outputs.EntityOutput, status_code=201)
async def create_entity(
    body: inputs.CreateEntityInput,
    request: fastapi.Request,
) -> outputs.EntityOutput:
    session = request.state.db_session           # never use Depends for session
    publisher = request.app.state.event_publisher
    return await commands.handle_create_entity(body, session, publisher)


@router.get("/{entity_id}", response_model=outputs.EntityOutput)
async def get_entity(
    entity_id: str,
    request: fastapi.Request,
) -> outputs.EntityOutput:
    return await queries.handle_get_entity(entity_id, request.state.db_session)
```

**Key**: session comes from `request.state.db_session`, NOT from `fastapi.Depends`. The middleware puts it there.

For protected routes:
```python
@router.post("/protected")
async def protected_route(
    body: inputs.SomeInput,
    current_user: typing.Annotated[
        user_aggregates.User, fastapi.Depends(lambda r: r.state.current_user)
    ],
    request: fastapi.Request,
) -> outputs.SomeOutput: ...
```

---

## Adding a new bounded context — checklist

Follow this order exactly. All `__init__.py` files are empty.

### 1. Domain layer
```
src/<context>/<entity>/domain/
    __init__.py           # empty
    types.py              # StrEnum/UpperStrEnum with enum.auto()
    value_objects.py      # IDs + business value types
    events.py             # Past-tense domain events
    exceptions.py         # Context-specific exceptions (use ... not pass)
    aggregates.py         # The aggregate root + nested entities/value objects
    repositories.py       # Abstract port (no raise NotImplementedError)
```

### 2. Infrastructure layer
```
src/<context>/<entity>/infrastructure/
    __init__.py           # empty
    models.py             # SQLAlchemy ORM (imports base.Base)
    mappers.py            # orm_to_domain() and domain_to_orm()
    repositories.py       # SqlAlchemy concrete repository (with self._seen)
    entrypoints/
        __init__.py       # empty
        router.py         # FastAPI APIRouter
```

### 3. Application layer
```
src/<context>/<entity>/application/
    __init__.py           # empty
    unit_of_work.py       # Extends FastAPIUnitOfWork
    dtos/
        __init__.py       # empty
        inputs.py         # Input DTOs (Pydantic, use | None)
        outputs.py        # Output DTOs (Pydantic)
    handlers/
        __init__.py       # empty
        commands.py       # Write use cases (small functions)
        queries.py        # Read use cases (optional)
```

### 4. Wire up
```python
# alembic/env.py — add ORM import so Alembic detects the table
from src.my_context.my_entity.infrastructure import models  # noqa: F401

# src/entrypoints/app.py — register the router
from src.my_context.my_entity.infrastructure.entrypoints import router as my_router
api_router.include_router(my_router.router)

# src/entrypoints/middleware.py — add exception handlers
from src.my_context.my_entity.domain import exceptions as my_exceptions
```

### 5. Migration
```bash
make migrate-create name="add_my_entity_table"
make migrate
```

---

## Common patterns and pitfalls

### Value objects in shared kernel
| Type | Use for | Example |
|------|---------|---------|
| `HumanFriendlyId` | Human-readable IDs (users, farmers) | `"A3BX92KQPZ"` |
| `UuidId` | Opaque IDs (products, orders) | `"a1b2c3d4-..."` |
| `PosixTime` | All timestamps | `PosixTime.now()`, `PosixTime.from_datetime(dt)` |
| `Money` | Monetary values | `Money.cop(15000)` |
| `NonNegativeMoney` | Prices, balances | validates `amount >= 0` |
| `PositiveMoney` | Required payments | validates `amount > 0` |

### ORM columns for common domain types
| Domain type | ORM column |
|-------------|-----------|
| `HumanFriendlyId` | `String(10)` |
| `UuidId` | `String(36)` |
| `PosixTime` | `BigInteger` (microseconds) |
| `Money.amount` | `Numeric(14, 2)` |
| `Enum.value` | `String(20)` |
| `bool` | `Boolean` |

### Timestamp handling
```python
# Domain: always PosixTime
created_at: shared_vo.PosixTime = shared_vo.PosixTime.now()

# ORM → domain
created_at = shared_vo.PosixTime(microseconds=orm.created_at)

# domain → ORM
orm.created_at = entity.created_at.microseconds

# DTO output: ISO string
created_at_str = entity.created_at.to_isoformat()
```

### Reading without UoW (queries)
For read-only queries that don't modify state, query the ORM directly — no UoW needed:
```python
async def handle_get_entity(entity_id: str, session: sqlalchemy.ext.asyncio.AsyncSession) -> outputs.EntityOutput:
    orm = await session.get(models.MyEntityOrm, entity_id)
    if orm is None:
        raise exceptions.MyEntityNotFoundError(entity_id)
    entity = mappers.orm_to_domain(orm)
    return _to_output(entity)
```

### Event publishing pattern
```python
async with uow:
    entity = await uow.my_entities.find_by_id(value_objects.MyEntityId(value=entity_id))
    entity.do_something()
    await uow.my_entities.put(entity)
    await uow.commit()
    pending_events = list(uow.collect_new_events())   # INSIDE — needs repo._seen

await publisher.publish_many(pending_events)          # OUTSIDE — DB already committed
```

---

## File reference: actual implementations

When in doubt, look at the existing bounded contexts as canonical examples:

- **Simplest full context**: `src/identity/user/` — auth, JWT, refresh tokens
- **Complex aggregate**: `src/catalog/product/` — nested value objects (VolumePrice, TraceabilityStep), custom queries
- **Shared building blocks**: `src/shared_kernel/domain/` — all base classes with full implementations
- **UoW implementations**: `src/shared_kernel/infrastructure/uow.py` — FastAPIUnitOfWork vs SqlAlchemyUnitOfWork
- **App factory + middleware**: `src/entrypoints/app.py` and `src/entrypoints/middleware.py`
- **StrEnum/UpperStrEnum pattern**: `old_backend/backend/src/shared_kernel/domain/types.py`
