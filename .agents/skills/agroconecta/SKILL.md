---
name: agroconecta
description: Experto en el backend de AgroConecta. Usa cuando el usuario pida crear un nuevo contexto acotado, agregar un endpoint, implementar un caso de uso, entender la arquitectura, agregar eventos de dominio, o cualquier tarea relacionada con el proyecto agroconecta-backend.
---

# AgroConecta Backend Expert

Eres un experto en el backend de AgroConecta — un marketplace agrícola colombiano B2B/B2C. Conoces en detalle su arquitectura hexagonal + DDD, sus patrones de implementación, y su infraestructura AWS.

## Qué es AgroConecta

Marketplace agrícola colombiano que conecta agricultores certificados con compradores e instituciones. Soporta trazabilidad de lotes, precios por volumen, cumplimiento de certificaciones y roles diferenciados.

**Roles:** `comprador` | `agricultor` | `institucion` | `admin`

---

## Stack técnico

- **Runtime:** Python 3.12, uv (package manager)
- **Framework:** FastAPI 0.115+ con Mangum para AWS Lambda
- **DB:** PostgreSQL 16, SQLAlchemy 2.0 async, asyncpg, Alembic
- **Validación:** Pydantic V2 con `validate_assignment=True`
- **Auth:** JWT HS256 (python-jose), refresh tokens SHA-256 en PostgreSQL
- **Eventos:** EventBridge → Lambda → SES (emails)
- **Infra:** AWS CDK (Python), Lambda ARM64, API Gateway HTTP, RDS, S3
- **Local:** Docker Compose (PostgreSQL + LocalStack), `make dev`

---

## Arquitectura: Hexagonal + DDD

**Regla fundamental:** el dominio no sabe nada de la base de datos, HTTP ni AWS.

```
src/
├── shared_kernel/               # Bloques DDD compartidos
│   ├── domain/                  # DomainModel, BaseAggregateRoot, DomainEvent, value objects
│   ├── application/ports/       # AbstractUnitOfWork, Repository[T], AbstractEventPublisher, AbstractEmailService
│   └── infrastructure/
│       ├── database/            # DeclarativeBase, async session factory
│       ├── adapters/            # EventBridgePublisher, SesEmailAdapter, Stub* (para local/test)
│       ├── uow.py               # SqlAlchemyUnitOfWork, FastAPIUnitOfWork
│       └── config.py            # Settings (pydantic-settings, lee .env)
├── identity/user/               # Auth: registro, login, JWT, refresh tokens
├── catalog/farmer/              # Agricultores y certificaciones
├── catalog/product/             # Productos, precios por volumen, trazabilidad
├── notifications/               # Handlers de eventos de dominio (user_events.py)
├── commerce/                    # Órdenes — Sprint 2
└── entrypoints/
    ├── app.py                   # create_app() — factory principal
    ├── middleware.py            # CORS, DB session por request, exception handlers
    ├── dependencies.py          # get_current_user (JWT)
    ├── lambda_handler.py        # Mangum(app) — API Lambda
    └── event_lambda_handler.py  # EventBridge Lambda — procesa eventos de dominio
```

### Estructura interna de cada contexto acotado

```
<contexto>/<entidad>/
├── domain/
│   ├── aggregates.py       # Aggregate root — toda la lógica de negocio aquí
│   ├── value_objects.py    # Value objects inmutables
│   ├── events.py           # DomainEvent (frozen Pydantic)
│   ├── exceptions.py       # Excepciones de dominio
│   ├── repositories.py     # Puerto abstracto (ABC)
│   └── types.py            # Enums del dominio
├── application/
│   ├── handlers/
│   │   ├── commands.py     # Handlers de escritura (async def handle_*)
│   │   └── queries.py      # Handlers de lectura
│   ├── dtos/
│   │   ├── inputs.py       # Pydantic models de entrada
│   │   └── outputs.py      # Pydantic models de salida
│   └── unit_of_work.py     # UoW específico del contexto
└── infrastructure/
    ├── models.py           # SQLAlchemy ORM (*Orm classes)
    ├── mappers.py          # ORM ↔ Domain (nunca mezclar capas)
    ├── repositories.py     # SqlAlchemy*Repository implementa el puerto
    └── entrypoints/
        └── router.py       # FastAPI router — HTTP adapter
```

---

## Patrones clave

### Data Mapper (NUNCA mezclar ORM con dominio)

```python
# infrastructure/mappers.py
def orm_to_domain(orm: ProductOrm) -> product_aggregates.Product:
    return product_aggregates.Product(
        id=product_value_objects.ProductId(value=orm.id),
        name=orm.name,
        ...
    )

def domain_to_orm(product: product_aggregates.Product) -> ProductOrm:
    return ProductOrm(id=str(product.id), name=product.name, ...)
```

### Unit of Work — commit explícito + collect events

```python
async with user_uow.UserUnitOfWork(session) as uow:
    user = user_aggregates.User.register(...)
    await uow.users.put(user)
    await uow.commit()
    pending_events = list(uow.collect_new_events())  # dentro del bloque

await publisher.publish_many(pending_events)  # fuera del bloque, post-commit
```

### Domain Events — pull-and-clear

```python
# En el aggregate:
def register(cls, ...) -> "User":
    user = cls(...)
    user.record_event(events.UserRegistered(user_id=..., email=...))
    return user

# collect_new_events() llama pull_events() que vacía la lista interna
```

### Event publishing — hexagonal

```python
# Puerto (nunca cambia):
# shared_kernel/application/ports/event_publisher.py → AbstractEventPublisher

# Adaptadores (intercambiables):
# staging/prod → EventBridgePublisher (publica a AWS EventBridge)
# development  → StubEventPublisher  (solo loggea, sin AWS)

# Selección en app.py según settings.environment:
app.state.event_publisher = _build_event_publisher(settings)

# Router pasa el publisher al handler:
publisher = request.app.state.event_publisher
await commands.handle_register(body, session, settings, publisher)
```

### Email service — hexagonal

```python
# Puerto: AbstractEmailService → send(EmailMessage)
# SES adapter:    SesEmailAdapter   (AWS SES real o LocalStack)
# Stub adapter:   StubEmailAdapter  (guarda en .sent[], solo loggea)

# El event_lambda_handler instancia el adapter según AWS_ENDPOINT_URL:
email_svc = SesEmailAdapter(
    sender_email=settings.ses_sender_email,
    endpoint_url=settings.aws_endpoint_url or None,
)
```

### DB Session — middleware, no Depends

```python
# El middleware abre AsyncSession por request y la guarda en request.state:
session = request.state.db_session  # en el router

# NO usar FastAPI Depends para la session — viene del middleware
```

### Timestamps y tipos especiales

```python
# PosixTime = microsegundos UTC desde epoch (BigInteger en DB)
PosixTime.now()                    # timestamp actual
PosixTime.from_datetime(dt)        # desde datetime
pos_time.to_isoformat()            # a ISO string

# Money — COP por defecto
Money.cop(Decimal("15000"))        # factory COP
money.add(other_money)
money.multiply(Decimal("1.19"))    # IVA

# IDs
HumanFriendlyId.generate()         # "X6UNFCKQMP" — 10 chars alfanumérico mayúscula
UuidId.generate()                  # UUID v4
```

---

## Convenciones de imports (OBLIGATORIO)

```python
# ✅ CORRECTO
import typing
from src.shared_kernel.domain import aggregates          # módulo, no clase
from src.catalog.product.domain import value_objects as product_vos

product_vos.ProductId(value="X6UNFCKQMP")
typing.Optional[str]

# ❌ INCORRECTO
from __future__ import annotations   # NUNCA
from typing import Optional           # NUNCA
from . import aggregates              # NUNCA imports relativos
from src.catalog.product.domain.aggregates import Product  # NUNCA importar clase directamente
```

---

## Flujo de eventos de dominio (end-to-end)

```
POST /api/v1/auth/register
  → handle_register(command, session, settings, publisher)
    → uow.commit()                        # persiste en PostgreSQL
    → uow.collect_new_events()            # extrae UserRegistered del aggregate
    → publisher.publish_many(events)
          ├── development  → StubEventPublisher (log en consola)
          └── staging/prod → EventBridgePublisher
                               → AWS EventBridge bus "agroconecta-events"
                               → regla "user-registered-rule"
                               → Lambda "agroconecta-event-handler"
                               → event_lambda_handler.handler()
                               → handle_user_registered(detail, email_svc)
                               → SesEmailAdapter.send(EmailMessage)
                               → AWS SES (o LocalStack /_aws/ses)
```

**Para agregar un nuevo evento al flujo:**
1. Definir el evento en `domain/events.py` del contexto
2. Llamar `record_event()` en el aggregate
3. Crear handler en `notifications/<contexto>_events.py`
4. Registrar en `_HANDLERS` de `event_lambda_handler.py`

---

## Cómo crear un nuevo contexto acotado

### 1. Dominio

```python
# src/<contexto>/<entidad>/domain/types.py
import enum
class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"

# src/<contexto>/<entidad>/domain/value_objects.py
import typing
from src.shared_kernel.domain import value_objects as shared_vos

class OrderId(shared_vos.HumanFriendlyId):
    pass

# src/<contexto>/<entidad>/domain/events.py
from src.shared_kernel.domain import events

class OrderPlaced(events.DomainEvent):
    order_id: str
    buyer_id: str
    total_cop: str

# src/<contexto>/<entidad>/domain/exceptions.py
from src.shared_kernel.domain import exceptions

class OrderNotFoundError(exceptions.NotFoundError):
    pass

# src/<contexto>/<entidad>/domain/aggregates.py
import typing
from src.shared_kernel.domain import aggregates, value_objects as shared_vos
from src.<contexto>.<entidad>.domain import value_objects, events, types

class Order(aggregates.BaseAggregateRoot):
    buyer_id: str
    status: types.OrderStatus = types.OrderStatus.PENDING

    @classmethod
    def place(cls, buyer_id: str, ...) -> "Order":
        order = cls(id=value_objects.OrderId.generate(), buyer_id=buyer_id, ...)
        order.record_event(events.OrderPlaced(
            aggregate_id=str(order.id),
            order_id=str(order.id),
            buyer_id=buyer_id,
            total_cop="0",
        ))
        return order
```

### 2. Infraestructura ORM

```python
# src/<contexto>/<entidad>/infrastructure/models.py
import sqlalchemy
import sqlalchemy.orm
from src.shared_kernel.infrastructure.database import base

class OrderOrm(base.Base):
    __tablename__ = "orders"
    id = sqlalchemy.Column(sqlalchemy.String(10), primary_key=True)
    buyer_id = sqlalchemy.Column(sqlalchemy.String(10), nullable=False)
    status = sqlalchemy.Column(sqlalchemy.String(20), nullable=False)
    created_at = sqlalchemy.Column(sqlalchemy.BigInteger, nullable=False)
    updated_at = sqlalchemy.Column(sqlalchemy.BigInteger, nullable=False)
```

### 3. Mapper

```python
# src/<contexto>/<entidad>/infrastructure/mappers.py
from src.<contexto>.<entidad>.infrastructure import models
from src.<contexto>.<entidad>.domain import aggregates, value_objects

def orm_to_domain(orm: models.OrderOrm) -> aggregates.Order:
    return aggregates.Order(
        id=value_objects.OrderId(value=orm.id),
        buyer_id=orm.buyer_id,
        ...
    )

def domain_to_orm(order: aggregates.Order) -> models.OrderOrm:
    return models.OrderOrm(id=str(order.id), buyer_id=order.buyer_id, ...)
```

### 4. Repository

```python
# src/<contexto>/<entidad>/domain/repositories.py
import abc
from src.shared_kernel.application.ports import repositories
from src.<contexto>.<entidad>.domain import aggregates, value_objects

class OrderRepository(repositories.Repository[aggregates.Order]):
    @abc.abstractmethod
    async def find_by_id(self, order_id: value_objects.OrderId) -> aggregates.Order | None:
        raise NotImplementedError

# src/<contexto>/<entidad>/infrastructure/repositories.py
import sqlalchemy.ext.asyncio
from src.<contexto>.<entidad>.domain import repositories as order_repos, aggregates, value_objects
from src.<contexto>.<entidad>.infrastructure import mappers, models

class SqlAlchemyOrderRepository(order_repos.OrderRepository):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        super().__init__()
        self._session = session

    async def put(self, order: aggregates.Order) -> None:
        orm = mappers.domain_to_orm(order)
        await self._session.merge(orm)
        self._seen.add(order)

    async def find_by_id(self, order_id: value_objects.OrderId) -> aggregates.Order | None:
        result = await self._session.get(models.OrderOrm, str(order_id))
        return mappers.orm_to_domain(result) if result else None
```

### 5. Unit of Work

```python
# src/<contexto>/<entidad>/application/unit_of_work.py
import sqlalchemy.ext.asyncio
from src.shared_kernel.infrastructure import uow
from src.<contexto>.<entidad>.domain import repositories as order_repos
from src.<contexto>.<entidad>.infrastructure import repositories as order_infra_repos

class OrderUnitOfWork(uow.FastAPIUnitOfWork):
    orders: order_repos.OrderRepository

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        super().__init__(session)
        self.orders = order_infra_repos.SqlAlchemyOrderRepository(session)

    def _repositories(self) -> list[order_repos.OrderRepository]:
        return [self.orders]
```

### 6. Handler

```python
# src/<contexto>/<entidad>/application/handlers/commands.py
import sqlalchemy.ext.asyncio
from src.shared_kernel.infrastructure import config as app_config
from src.shared_kernel.application.ports import event_publisher as event_publisher_port
from src.<contexto>.<entidad>.application import unit_of_work as order_uow
from src.<contexto>.<entidad>.application.dtos import inputs, outputs
from src.<contexto>.<entidad>.domain import aggregates

async def handle_place_order(
    command: inputs.PlaceOrderInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    settings: app_config.Settings,
    publisher: event_publisher_port.AbstractEventPublisher,
) -> outputs.OrderOutput:
    async with order_uow.OrderUnitOfWork(session) as uow:
        order = aggregates.Order.place(buyer_id=command.buyer_id, ...)
        await uow.orders.put(order)
        await uow.commit()
        pending_events = list(uow.collect_new_events())

    await publisher.publish_many(pending_events)
    return outputs.OrderOutput(id=str(order.id), ...)
```

### 7. Router

```python
# src/<contexto>/<entidad>/infrastructure/entrypoints/router.py
import typing
import fastapi
from src.shared_kernel.infrastructure import config as app_config
from src.<contexto>.<entidad>.application.dtos import inputs, outputs
from src.<contexto>.<entidad>.application.handlers import commands

router = fastapi.APIRouter(prefix="/orders", tags=["orders"])

async def _get_settings() -> typing.AsyncGenerator[app_config.Settings, None]:
    yield app_config.get_settings()

SettingsDep = typing.Annotated[app_config.Settings, fastapi.Depends(_get_settings)]

@router.post("", response_model=outputs.OrderOutput, status_code=201)
async def place_order(
    body: inputs.PlaceOrderInput,
    settings: SettingsDep,
    request: fastapi.Request,
) -> outputs.OrderOutput:
    session = request.state.db_session
    publisher = request.app.state.event_publisher
    return await commands.handle_place_order(body, session, settings, publisher)
```

### 8. Registrar en Alembic y app.py

```python
# alembic/env.py — importar el modelo para que Alembic lo detecte
from src.<contexto>.<entidad>.infrastructure import models as order_models  # noqa: F401

# src/entrypoints/app.py — registrar el router
from src.<contexto>.<entidad>.infrastructure.entrypoints import router as order_router
api_v1.include_router(order_router.router)
```

### 9. Generar y aplicar la migración

```bash
make migrate-create name="add_orders"
make migrate
```

---

## Comandos frecuentes

```bash
make dev              # API en localhost:8000 (hot reload)
make migrate          # aplicar migraciones pendientes
make migrate-create name="descripcion"   # nueva migración
make test-unit        # tests sin DB
make format           # ruff autofix

# LocalStack — workflow completo
make lambda-build     # crea lambda.zip para Linux x86_64
make localstack-setup # crea bus + Lambda + regla EventBridge en LocalStack
make localstack-reset # borra todo y recrea

# Verificar email enviado por SES en LocalStack
curl -s http://localhost:4566/_aws/ses | jq '.messages[-1]'
```

---

## Variables de entorno clave

| Variable | Descripción | Default local |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async | `postgresql+asyncpg://agroconecta:agroconecta@localhost:5432/agroconecta` |
| `JWT_SECRET_KEY` | 32-byte hex | — |
| `ENVIRONMENT` | `development`/`staging`/`production` | `development` |
| `AWS_ENDPOINT_URL` | LocalStack endpoint | `http://localhost:4566` |
| `EVENTBRIDGE_BUS_NAME` | Nombre del bus | `agroconecta-events` |
| `SES_SENDER_EMAIL` | Remitente de emails | `noreply@agroconecta.co` |

Con `ENVIRONMENT=development` no se usa EventBridge ni SES — el `StubEventPublisher` y `StubEmailAdapter` loggean todo localmente.

---

## Checklist al crear un nuevo contexto

- [ ] `domain/`: aggregate, value_objects, events, exceptions, repositories (ABC), types
- [ ] `infrastructure/models.py`: clase `*Orm` con `__tablename__`
- [ ] `infrastructure/mappers.py`: `orm_to_domain()` y `domain_to_orm()`
- [ ] `infrastructure/repositories.py`: implementa el puerto, agrega a `_seen` en `put()`
- [ ] `application/unit_of_work.py`: expone repos, implementa `_repositories()`
- [ ] `application/handlers/`: recibe session + settings + publisher, commit + collect_events
- [ ] `infrastructure/entrypoints/router.py`: obtiene session de `request.state.db_session` y publisher de `request.app.state.event_publisher`
- [ ] `alembic/env.py`: importar el modelo ORM
- [ ] `src/entrypoints/app.py`: registrar el router
- [ ] `src/entrypoints/middleware.py`: mapear nuevas excepciones a HTTP status codes
- [ ] `make migrate-create name="..."` + `make migrate`
- [ ] Si hay nuevos eventos: agregar handler en `notifications/` y registrar en `event_lambda_handler._HANDLERS`
