"""Order query output DTOs."""

import datetime
import decimal

import pydantic

from src.commerce.order.domain import types


class DeliveryAddressOutput(pydantic.BaseModel):
    street: str
    city: str
    department: str
    postal_code: str | None
    notes: str | None


class OrderItemOutput(pydantic.BaseModel):
    product_id: str
    product_name: str
    quantity: decimal.Decimal
    unit_price: decimal.Decimal
    subtotal: decimal.Decimal


class OrderOutput(pydantic.BaseModel):
    id: str
    order_number: str
    type: str
    status: str
    buyer_id: str
    items: list[OrderItemOutput]
    subtotal: decimal.Decimal
    delivery_fee: decimal.Decimal
    total: decimal.Decimal
    payment_method: str
    delivery_date: datetime.date
    delivery_address: DeliveryAddressOutput
    purchase_order_number: str | None
    created_at: str
    updated_at: str


class OrderSummaryOutput(pydantic.BaseModel):
    id: str
    order_number: str
    type: str
    status: str
    total: decimal.Decimal
    item_count: int
    created_at: str
