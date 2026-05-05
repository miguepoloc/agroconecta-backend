# Eval 1 WITH SKILL — Crear contexto acotado commerce/order

## Estructura generada

```
src/commerce/order/
├── domain/
│   ├── types.py
│   ├── value_objects.py
│   ├── events.py
│   ├── exceptions.py
│   ├── aggregates.py
│   └── repositories.py
├── application/
│   ├── unit_of_work.py
│   ├── dtos/inputs.py
│   ├── dtos/outputs.py
│   └── handlers/commands.py
└── infrastructure/
    ├── models.py
    ├── mappers.py
    └── repositories.py
```

## domain/types.py
```python
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
```

## domain/value_objects.py
```python
import typing
from decimal import Decimal
import pydantic
from src.shared_kernel.domain import value_objects as shared_vo

class OrderId(shared_vo.UuidId):
    pass

class ProductId(shared_vo.UuidId):
    pass

class BuyerId(shared_vo.UuidId):
    pass

class QuantityKg(shared_vo.BaseValueObject):
    value: Decimal

    @pydantic.field_validator("value", mode="before")
    @classmethod
    def coerce_decimal(cls, v: typing.Any) -> Decimal:
        return Decimal(str(v))

    @pydantic.field_validator("value")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Quantity must be greater than 0")
        return v
```

## domain/events.py
```python
from src.shared_kernel.domain import events as domain_events

class OrderPlaced(domain_events.DomainEvent):
    order_id: str
    buyer_id: str
    item_count: int
    total_amount_cop: str
```

## domain/exceptions.py
```python
from src.shared_kernel.domain import exceptions as shared_exceptions

class OrderNotFoundError(shared_exceptions.NotFoundError):
    def __init__(self, order_id: str) -> None:
        super().__init__(f"Order {order_id} not found")

class OrderCannotBeCancelledError(shared_exceptions.BusinessRuleViolationError):
    def __init__(self, order_id: str, status: str) -> None:
        super().__init__(f"Order {order_id} cannot be cancelled because its status is {status}")

class EmptyOrderError(shared_exceptions.ValidationError):
    def __init__(self) -> None:
        super().__init__("An order must have at least one item")
```

## domain/aggregates.py
```python
import pydantic
from src.shared_kernel.domain import aggregates as shared_aggregates
from src.shared_kernel.domain import value_objects as shared_vo
from src.commerce.order.domain import events as order_events
from src.commerce.order.domain import exceptions as order_exceptions
from src.commerce.order.domain import types, value_objects

class OrderItem(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)
    product_id: value_objects.ProductId
    quantity_kg: value_objects.QuantityKg

class Order(shared_aggregates.BaseAggregateRoot):
    id: value_objects.OrderId
    buyer_id: value_objects.BuyerId
    items: list[OrderItem] = pydantic.Field(default_factory=list)
    total_amount: shared_vo.NonNegativeMoney
    status: types.OrderStatus = types.OrderStatus.PENDING

    @classmethod
    def place(
        cls,
        buyer_id: value_objects.BuyerId,
        items: list[OrderItem],
        total_amount: shared_vo.NonNegativeMoney,
    ) -> "Order":
        if not items:
            raise order_exceptions.EmptyOrderError()
        order = cls(
            id=value_objects.OrderId.generate(),
            buyer_id=buyer_id,
            items=items,
            total_amount=total_amount,
        )
        order.record_event(
            order_events.OrderPlaced(
                order_id=str(order.id),
                buyer_id=str(order.buyer_id),
                item_count=len(order.items),
                total_amount_cop=str(order.total_amount.amount),
            )
        )
        return order

    def cancel(self) -> None:
        if self.status == types.OrderStatus.CANCELLED:
            raise order_exceptions.OrderCannotBeCancelledError(str(self.id), self.status.value)
        self.status = types.OrderStatus.CANCELLED
        self.touch()
```

## domain/repositories.py
```python
import abc
import typing
from src.shared_kernel.application.ports import repositories as shared_repos
from src.commerce.order.domain import aggregates

class OrderRepository(shared_repos.Repository[aggregates.Order]):
    def model_type(self) -> type[aggregates.Order]:
        return aggregates.Order

    @abc.abstractmethod
    async def find_by_buyer_id(self, buyer_id: str) -> list[aggregates.Order]:
        raise NotImplementedError
```

## infrastructure/models.py
```python
import sqlalchemy
import sqlalchemy.orm
from src.shared_kernel.infrastructure.database import base

class OrderOrm(base.Base):
    __tablename__ = "orders"
    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(36), primary_key=True)
    buyer_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(36), sqlalchemy.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    total_amount: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.Numeric(14, 2), nullable=False)
    total_currency: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(10), nullable=False, default="COP")
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(20), nullable=False, default="PENDING", index=True)
    version: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(sqlalchemy.Integer, nullable=False, default=1)
    created_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(sqlalchemy.BigInteger, nullable=False)
    updated_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(sqlalchemy.BigInteger, nullable=False)
    items: sqlalchemy.orm.Mapped[list["OrderItemOrm"]] = sqlalchemy.orm.relationship("OrderItemOrm", back_populates="order", cascade="all, delete-orphan")

class OrderItemOrm(base.Base):
    __tablename__ = "order_items"
    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(36), primary_key=True)
    order_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(36), sqlalchemy.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(36), sqlalchemy.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_kg: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.Numeric(10, 3), nullable=False)
    order: sqlalchemy.orm.Mapped[OrderOrm] = sqlalchemy.orm.relationship("OrderOrm", back_populates="items")
```

## infrastructure/mappers.py
```python
import uuid
from decimal import Decimal
from src.shared_kernel.domain import value_objects as shared_vo
from src.commerce.order.domain import aggregates as order_aggregates
from src.commerce.order.domain import types, value_objects
from src.commerce.order.infrastructure import models

def orm_to_domain(orm: models.OrderOrm) -> order_aggregates.Order:
    return order_aggregates.Order(
        id=value_objects.OrderId(value=orm.id),
        buyer_id=value_objects.BuyerId(value=orm.buyer_id),
        items=[order_aggregates.OrderItem(
            product_id=value_objects.ProductId(value=item.product_id),
            quantity_kg=value_objects.QuantityKg(value=Decimal(str(item.quantity_kg))),
        ) for item in orm.items],
        total_amount=shared_vo.NonNegativeMoney(amount=Decimal(str(orm.total_amount)), currency=orm.total_currency),
        status=types.OrderStatus(orm.status),
        version=orm.version,
        created_at=shared_vo.PosixTime(microseconds=orm.created_at),
        updated_at=shared_vo.PosixTime(microseconds=orm.updated_at),
    )

def domain_to_orm(order: order_aggregates.Order) -> models.OrderOrm:
    order_id = str(order.id)
    return models.OrderOrm(
        id=order_id,
        buyer_id=str(order.buyer_id),
        total_amount=str(order.total_amount.amount),
        total_currency=order.total_amount.currency,
        status=order.status.value,
        version=order.version,
        created_at=order.created_at.microseconds,
        updated_at=order.updated_at.microseconds,
        items=[models.OrderItemOrm(
            id=str(uuid.uuid4()),
            order_id=order_id,
            product_id=str(item.product_id),
            quantity_kg=str(item.quantity_kg.value),
        ) for item in order.items],
    )
```

## infrastructure/repositories.py
```python
import typing
import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.orm
from src.shared_kernel.domain import value_objects as shared_vo
from src.commerce.order.domain import aggregates as order_aggregates
from src.commerce.order.domain import repositories as order_repos
from src.commerce.order.infrastructure import mappers, models

class SqlAlchemyOrderRepository(order_repos.OrderRepository):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._seen: set[order_aggregates.Order] = set()

    async def put(self, entity: order_aggregates.Order) -> None:
        orm = mappers.domain_to_orm(entity)
        await self._session.merge(orm)
        self._seen.add(entity)

    async def find_by_id(self, id: shared_vo.DomainId) -> typing.Optional[order_aggregates.Order]:
        stmt = (
            sqlalchemy.select(models.OrderOrm)
            .where(models.OrderOrm.id == str(id))
            .options(sqlalchemy.orm.selectinload(models.OrderOrm.items))
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        order = mappers.orm_to_domain(orm)
        self._seen.add(order)
        return order

    async def find_by_buyer_id(self, buyer_id: str) -> list[order_aggregates.Order]:
        stmt = (
            sqlalchemy.select(models.OrderOrm)
            .where(models.OrderOrm.buyer_id == buyer_id)
            .options(sqlalchemy.orm.selectinload(models.OrderOrm.items))
        )
        result = await self._session.execute(stmt)
        orders = [mappers.orm_to_domain(orm) for orm in result.scalars().all()]
        self._seen.update(orders)
        return orders
```

## application/unit_of_work.py
```python
import sqlalchemy.ext.asyncio
from src.shared_kernel.infrastructure import uow
from src.commerce.order.domain import repositories as order_repos
from src.commerce.order.infrastructure import repositories as order_infra_repos

class OrderUnitOfWork(uow.FastAPIUnitOfWork):
    orders: order_repos.OrderRepository

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        super().__init__(session)
        self.orders = order_infra_repos.SqlAlchemyOrderRepository(session)

    def _repositories(self) -> list[order_repos.OrderRepository]:
        return [self.orders]
```

## application/handlers/commands.py
```python
import sqlalchemy.ext.asyncio
from src.shared_kernel.application.ports import event_publisher as event_publisher_port
from src.shared_kernel.domain import value_objects as shared_vo
from src.commerce.order.application import unit_of_work as order_uow
from src.commerce.order.application.dtos import inputs, outputs
from src.commerce.order.domain import aggregates as order_aggregates
from src.commerce.order.domain import exceptions as order_exceptions
from src.commerce.order.domain import value_objects as order_vo

async def handle_place_order(
    command: inputs.PlaceOrderInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    publisher: event_publisher_port.AbstractEventPublisher,
) -> outputs.OrderOutput:
    async with order_uow.OrderUnitOfWork(session) as uow:
        items = [
            order_aggregates.OrderItem(
                product_id=order_vo.ProductId(value=item.product_id),
                quantity_kg=order_vo.QuantityKg(value=item.quantity_kg),
            )
            for item in command.items
        ]
        total_amount = shared_vo.NonNegativeMoney.cop(command.total_amount_cop)
        order = order_aggregates.Order.place(
            buyer_id=order_vo.BuyerId(value=command.buyer_id),
            items=items,
            total_amount=total_amount,
        )
        await uow.orders.put(order)
        await uow.commit()
        pending_events = list(uow.collect_new_events())   # INSIDE async with

    await publisher.publish_many(pending_events)           # OUTSIDE async with
    return _build_order_output(order)
```

## Convenciones verificadas
- ✅ Imports absolutos (from src....)
- ✅ import typing (no from typing import)
- ✅ Módulo importado, no clase (from src.x.domain import aggregates as x_aggregates)
- ✅ PosixTime para timestamps, BigInteger en ORM
- ✅ NonNegativeMoney para total_amount
- ✅ UuidId para OrderId/ProductId/BuyerId
- ✅ BaseAggregateRoot heredado
- ✅ DomainEvent heredado, record_event() usado
- ✅ mapper con orm_to_domain / domain_to_orm y conversiones .microseconds
- ✅ self._seen: set en repository
- ✅ collect_new_events() DENTRO del async with
- ✅ publish_many() FUERA del async with
