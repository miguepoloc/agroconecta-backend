"""SQLAlchemy ORM models for the order context."""

import sqlalchemy
import sqlalchemy.orm

from src.shared_kernel.infrastructure.database import base


class OrderOrm(base.Base):
    __tablename__ = "orders"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(10), primary_key=True
    )
    order_number: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, unique=True, index=True
    )
    buyer_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(10),
        sqlalchemy.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_type: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(15), nullable=False
    )
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(15), nullable=False, index=True
    )
    subtotal_cop: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(15, 2), nullable=False
    )
    delivery_fee_cop: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(15, 2), nullable=False
    )
    total_cop: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(15, 2), nullable=False
    )
    payment_method: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(15), nullable=False
    )
    delivery_date: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
    delivery_street: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    delivery_city: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100), nullable=False
    )
    delivery_department: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100), nullable=False
    )
    delivery_postal_code: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=True
    )
    delivery_notes: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=True
    )
    purchase_order_number: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(50), nullable=True
    )
    version: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=1
    )
    created_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
    updated_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )

    items: sqlalchemy.orm.Mapped[list["OrderItemOrm"]] = sqlalchemy.orm.relationship(
        "OrderItemOrm", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItemOrm(base.Base):
    __tablename__ = "order_items"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), primary_key=True
    )
    order_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(10),
        sqlalchemy.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36),
        sqlalchemy.ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), nullable=False
    )
    quantity: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(10, 3), nullable=False
    )
    unit_price_cop: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(15, 2), nullable=False
    )
    created_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )

    order: sqlalchemy.orm.Mapped[OrderOrm] = sqlalchemy.orm.relationship(
        "OrderOrm", back_populates="items"
    )
