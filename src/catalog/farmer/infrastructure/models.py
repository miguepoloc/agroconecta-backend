"""SQLAlchemy ORM models for the farmer context."""

import sqlalchemy
import sqlalchemy.orm

from src.shared_kernel.infrastructure.database import base


class FarmerOrm(base.Base):
    __tablename__ = "farmers"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), primary_key=True
    )
    user_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(10),
        sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    region: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100), nullable=False
    )
    department: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100), nullable=False
    )
    bio: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.Text, nullable=True)
    total_sales: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(15, 2), nullable=False, default="0"
    )
    compliance_status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, default="active"
    )
    sustainability_rank: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, default="bronze"
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

    certifications: sqlalchemy.orm.Mapped[list["CertificationOrm"]] = sqlalchemy.orm.relationship(
        "CertificationOrm", back_populates="farmer", cascade="all, delete-orphan"
    )


class CertificationOrm(base.Base):
    __tablename__ = "certifications"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), primary_key=True
    )
    farmer_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36),
        sqlalchemy.ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    certification_type: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(50), nullable=False
    )
    issue_date: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
    expiry_date: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, default="active"
    )

    farmer: sqlalchemy.orm.Mapped[FarmerOrm] = sqlalchemy.orm.relationship(
        "FarmerOrm", back_populates="certifications"
    )
