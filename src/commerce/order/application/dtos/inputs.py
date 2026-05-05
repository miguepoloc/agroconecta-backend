"""Order command input DTOs."""

import datetime
import decimal

import pydantic

from src.commerce.order.domain import types


class DeliveryAddressInput(pydantic.BaseModel):
    street: str
    city: str
    department: str
    postal_code: str | None = None
    notes: str | None = None


class OrderItemInput(pydantic.BaseModel):
    product_id: str
    quantity: decimal.Decimal = pydantic.Field(gt=0)


class PlaceOrderInput(pydantic.BaseModel):
    items: list[OrderItemInput] = pydantic.Field(min_length=1)
    payment_method: types.PaymentMethod
    delivery_date: datetime.date
    delivery_address: DeliveryAddressInput
    purchase_order_number: str | None = None


class ChangeOrderStatusInput(pydantic.BaseModel):
    status: types.OrderStatus
