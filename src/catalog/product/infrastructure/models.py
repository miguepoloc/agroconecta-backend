"""SQLAlchemy ORM models for the product context."""

import sqlalchemy
import sqlalchemy.orm

from src.shared_kernel.infrastructure.database import base


class ProductOrm(base.Base):
    __tablename__ = "products"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), primary_key=True
    )
    slug: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), unique=True, nullable=False, index=True
    )
    name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), nullable=False
    )
    description: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=True
    )
    category: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(50), nullable=False, index=True
    )
    price: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(15, 2), nullable=False
    )
    institutional_price: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(15, 2), nullable=False
    )
    minimum_lot: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(10, 3), nullable=False
    )
    unit: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False
    )
    images: sqlalchemy.orm.Mapped[list[str]] = sqlalchemy.orm.mapped_column(
        sqlalchemy.JSON, nullable=False, default=list
    )
    farmer_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36),
        sqlalchemy.ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lot_number: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, unique=True, index=True
    )
    harvest_date: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
    freshness_score: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=100
    )
    in_stock: sqlalchemy.orm.Mapped[bool] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    featured: sqlalchemy.orm.Mapped[bool] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False, index=True
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

    volume_prices: sqlalchemy.orm.Mapped[list["VolumePriceOrm"]] = (
        sqlalchemy.orm.relationship(
            "VolumePriceOrm", back_populates="product", cascade="all, delete-orphan"
        )
    )
    traceability_steps: sqlalchemy.orm.Mapped[list["TraceabilityStepOrm"]] = (
        sqlalchemy.orm.relationship(
            "TraceabilityStepOrm",
            back_populates="product",
            cascade="all, delete-orphan",
            order_by="TraceabilityStepOrm.date",
        )
    )


class VolumePriceOrm(base.Base):
    __tablename__ = "volume_prices"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), primary_key=True
    )
    product_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36),
        sqlalchemy.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    min_kg: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(10, 3), nullable=False
    )
    max_kg: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(10, 3), nullable=False
    )
    price_per_kg: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(15, 2), nullable=False
    )

    product: sqlalchemy.orm.Mapped[ProductOrm] = sqlalchemy.orm.relationship(
        "ProductOrm", back_populates="volume_prices"
    )


class TraceabilityStepOrm(base.Base):
    __tablename__ = "traceability_steps"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), primary_key=True
    )
    product_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36),
        sqlalchemy.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(50), nullable=False
    )
    date: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
    location: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), nullable=False
    )
    responsible: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), nullable=False
    )
    notes: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=True
    )

    product: sqlalchemy.orm.Mapped[ProductOrm] = sqlalchemy.orm.relationship(
        "ProductOrm", back_populates="traceability_steps"
    )
