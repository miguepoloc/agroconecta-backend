# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
uv sync                          # install dependencies

# Local services
make db-up                       # start PostgreSQL on :5432
make infra-up                    # start PostgreSQL + LocalStack

# Development
make dev                         # fastapi dev server on :8000 (hot reload)
make migrate                     # alembic upgrade head
make migrate-create name="desc"  # generate autogenerate migration

# Quality
make test                        # all tests
make test-unit                   # unit tests only (no DB needed)
make test-integration            # integration tests (requires db-test-up)
make lint                        # ruff check + format check
make format                      # ruff autofix + format
make typecheck                   # mypy

# Single test
pytest tests/unit/identity/domain/test_user_aggregate.py::TestUserRegistration::test_register_emits_user_registered_event -v

# Deploy
make deploy                      # cdk deploy --all (from infra/)
```

## Architecture

**Hexagonal + DDD (Cosmic Python)**. The domain layer has zero knowledge of the database, HTTP, or AWS. Three bounded contexts under `src/`:

```
src/
├── shared_kernel/               # DDD building blocks shared across all contexts
│   ├── domain/                  # DomainModel, BaseAggregateRoot, DomainEvent, value objects
│   ├── application/ports/       # AbstractUnitOfWork, Repository[T], AbstractMessageBus
│   └── infrastructure/          # FastAPIUnitOfWork, SqlAlchemyUnitOfWork, Settings, session factory
├── identity/user/               # Auth bounded context
├── catalog/farmer/              # Farmer + Certification bounded context
├── catalog/product/             # Product, VolumePrice, TraceabilityStep bounded context
├── commerce/                    # Orders (Sprint 2 — placeholder)
└── entrypoints/                 # app.py (factory), middleware.py, dependencies.py, lambda_handler.py
```

Each bounded context follows the same internal structure:
```
<context>/
├── domain/          aggregates.py, value_objects.py, events.py, exceptions.py, repositories.py, types.py
├── application/     handlers/ (commands.py or queries.py), dtos/ (inputs.py, outputs.py), unit_of_work.py
└── infrastructure/  models.py (SQLAlchemy ORM), mappers.py (ORM↔domain), repositories.py, entrypoints/router.py
```

### Key patterns

**DB session flow**: `build_db_session_middleware` in `middleware.py` opens an `AsyncSession` per request and stores it at `request.state.db_session`. Routers access it via `request.state.db_session` — there is no FastAPI `Depends` injection for the session.

**Unit of Work**: `FastAPIUnitOfWork` wraps the request-scoped session (used in API handlers). `SqlAlchemyUnitOfWork` owns its own session (use for Lambda jobs/CLI). Both are `async with` context managers; `commit()` must be called explicitly — `__aexit__` only rolls back on exception.

**Data Mapper**: ORM models (`*Orm` classes) never enter the domain layer. `mappers.py` in each context converts `OrmModel → DomainAggregate` and back. The domain is pure Pydantic v2 with `validate_assignment=True`.

**Domain events (pull-and-clear)**: Aggregates queue events via `record_event()`. After `commit()`, call `uow.collect_new_events()` to pull events from all tracked aggregates — events are cleared from the aggregate on pull.

**Authentication**: JWT HS256 via `python-jose`. `create_access_token` / `decode_access_token` live in `src/identity/user/infrastructure/adapters/jwt.py`. The `get_current_user` dependency in `dependencies.py` decodes the `Authorization: Bearer` header and sets `request.state.current_user`.

**Timestamps**: All times are stored as `PosixTime` (microseconds UTC since epoch, `BigInteger` in DB). Use `PosixTime.now()` / `PosixTime.from_datetime()` / `.to_isoformat()`.

**Money**: `Money(amount: Decimal, currency: str = "COP")`. Use `Money.cop(amount)` factory. `NonNegativeMoney` and `PositiveMoney` enforce their constraints via validators.

**IDs**: Aggregates use `HumanFriendlyId` (10-char uppercase alphanumeric) or `UuidId`. ORM columns match: `String(10)` for HumanFriendlyId, `String(36)` for UUID.

### Adding a new bounded context

1. Create `src/<context>/<entity>/domain/` — aggregate, value objects, events, exceptions, repositories port, types.
2. Create `src/<context>/<entity>/infrastructure/` — SQLAlchemy ORM model, mapper, concrete repository, router.
3. Create `src/<context>/<entity>/application/` — handlers (commands/queries), DTOs, unit_of_work.
4. Import the ORM model in `alembic/env.py` so Alembic detects the table.
5. Register the router in `src/entrypoints/app.py`.
6. Add exception types to `src/entrypoints/middleware.py` exception handlers.

## Import conventions

- **No** `from __future__ import annotations`
- **No** relative imports (`from . import`) — always use absolute: `from src.shared_kernel.domain import base_model`
- **No** `from typing import X` — use `import typing` then `typing.Optional`, `typing.Generator`, etc.
- Import the **module**, not the class: `from src.identity.user.domain import aggregates` then `aggregates.User`

## Environment

Copy `.env.example` → `.env`. Minimum required vars:

```
DATABASE_URL=postgresql+asyncpg://agroconecta:agroconecta@localhost:5432/agroconecta
JWT_SECRET_KEY=<32-byte hex>
```

Docs available at `http://localhost:8000/docs` in `development` / `staging` environments only.

## Infrastructure (AWS CDK)

Stacks in `infra/stacks/`:
- `DatabaseStack` — RDS PostgreSQL 16, t4g.micro, private VPC subnet
- `StorageStack` — S3 bucket for product images (public read)
- `ApiStack` — Lambda (ARM64, Python 3.12) + API Gateway HTTP, references DB secret from Secrets Manager

Lambda entry point: `src/entrypoints/lambda_handler.py` → `Mangum(app, lifespan="off")`.
