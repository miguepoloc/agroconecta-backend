import asyncio
import time
import uuid

import bcrypt

from src.catalog.farmer.infrastructure.models import CertificationOrm, FarmerOrm
from src.catalog.product.infrastructure.models import (
    ProductOrm,
    TraceabilityStepOrm,
    VolumePriceOrm,
)
from src.identity.user.infrastructure.models import UserOrm
from src.shared_kernel.infrastructure import config
from src.shared_kernel.infrastructure.database.session import build_engine, build_session_factory

now_us = int(time.time() * 1_000_000)
password_hash = bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode()

frm_1_id = str(uuid.uuid4())
prod_1_id = str(uuid.uuid4())
prod_2_id = str(uuid.uuid4())

USERS = [
    UserOrm(
        id="usr-1",
        email="comprador@demo.co",
        first_name="Laura",
        last_name="Gómez",
        phone="+573001234567",
        password_hash=password_hash,
        role="comprador",
        status="active",
        created_at=now_us,
        updated_at=now_us,
    ),
    UserOrm(
        id="usr-2",
        email="agricultor@demo.co",
        first_name="Carlos",
        last_name="Muñoz",
        phone="+573104567890",
        password_hash=password_hash,
        role="agricultor",
        status="active",
        created_at=now_us,
        updated_at=now_us,
    ),
    UserOrm(
        id="usr-3",
        email="institucion@demo.co",
        first_name="Roberto",
        last_name="Cárdenas",
        phone="+573209876543",
        password_hash=password_hash,
        role="institucion",
        status="active",
        created_at=now_us,
        updated_at=now_us,
    ),
    UserOrm(
        id="usr-4",
        email="admin@demo.co",
        first_name="Sofía",
        last_name="Vargas",
        phone="+573152468013",
        password_hash=password_hash,
        role="admin",
        status="active",
        created_at=now_us,
        updated_at=now_us,
    ),
]

FARMERS = [
    FarmerOrm(
        id=frm_1_id,
        user_id="usr-2",
        region="Valle de Tenza",
        department="Boyacá",
        bio="Agricultor de tercera generación en el Valle de Tenza.",
        total_sales="128500000",
        compliance_status="active",
        sustainability_rank="gold",
        created_at=now_us,
        updated_at=now_us,
    )
]

CERTIFICATIONS = [
    CertificationOrm(
        id=str(uuid.uuid4()),
        farmer_id=frm_1_id,
        certification_type="GlobalGAP",
        issue_date=now_us - 86400 * 1_000_000 * 30,
        expiry_date=now_us + 86400 * 1_000_000 * 300,
        status="active",
    )
]

PRODUCTS = [
    ProductOrm(
        id=prod_1_id,
        slug="papa-criolla-boyaca",
        name="Papa Criolla Boyacá",
        description=(
            "Papa criolla de primera calidad cultivada en las laderas del Valle de Tenza, Boyacá."
        ),
        category="tuberculos",
        price="3200",
        institutional_price="2600",
        minimum_lot="50",
        unit="kg",
        images=["/images/papa-criolla.png"],
        farmer_id=frm_1_id,
        lot_number="LOT-2026-0501-01",
        harvest_date=now_us - 86400 * 1_000_000 * 3,
        freshness_score=97,
        in_stock=True,
        featured=True,
        created_at=now_us,
        updated_at=now_us,
    ),
    ProductOrm(
        id=prod_2_id,
        slug="tomate-chonto-antioquia",
        name="Tomate Chonto Invernadero",
        description="Tomate chonto cultivado en invernadero con control fitosanitario certificado.",
        category="verduras",
        price="4800",
        institutional_price="3900",
        minimum_lot="100",
        unit="kg",
        images=["https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&q=80"],
        farmer_id=frm_1_id,
        lot_number="LOT-2026-0430-02",
        harvest_date=now_us - 86400 * 1_000_000 * 4,
        freshness_score=94,
        in_stock=True,
        featured=True,
        created_at=now_us,
        updated_at=now_us,
    ),
]

VOLUME_PRICES = [
    VolumePriceOrm(
        id=str(uuid.uuid4()), product_id=prod_1_id, min_kg="1", max_kg="9", price_per_kg="3200"
    ),
    VolumePriceOrm(
        id=str(uuid.uuid4()), product_id=prod_1_id, min_kg="10", max_kg="49", price_per_kg="2900"
    ),
]

TRACEABILITY_STEPS = [
    TraceabilityStepOrm(
        id=str(uuid.uuid4()),
        product_id=prod_1_id,
        stage="cosecha",
        date=now_us - 86400 * 1_000_000 * 3,
        location="Valle de Tenza, Boyacá",
        responsible="Carlos Muñoz",
        notes="Cosecha manual",
    )
]


async def seed():
    settings = config.get_settings()
    engine = build_engine(settings.database_url)
    SessionFactory = build_session_factory(engine)

    async with SessionFactory() as session:
        print("Seeding Users...")
        session.add_all(USERS)
        await session.commit()

        print("Seeding Farmers...")
        session.add_all(FARMERS)
        await session.commit()

        print("Seeding Certifications...")
        session.add_all(CERTIFICATIONS)
        await session.commit()

        print("Seeding Products...")
        session.add_all(PRODUCTS)
        await session.commit()

        print("Seeding Volume Prices...")
        session.add_all(VOLUME_PRICES)
        await session.commit()

        print("Seeding Traceability Steps...")
        session.add_all(TRACEABILITY_STEPS)
        await session.commit()

        print("Database seeded successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
