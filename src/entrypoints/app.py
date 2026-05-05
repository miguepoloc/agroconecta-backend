"""FastAPI application factory."""

import fastapi
import sqlalchemy.ext.asyncio

from src.shared_kernel.infrastructure import config as app_config
from src.shared_kernel.infrastructure.database import session as db_session
from src.shared_kernel.infrastructure.adapters import (
    postgres_refresh_token,
    postgres_event_publisher,
    resend_email,
    stub_event_publisher,
    stub_refresh_token,
)
from src.entrypoints import middleware
from src.identity.user.infrastructure.entrypoints import router as auth_router
from src.catalog.farmer.infrastructure.entrypoints import router as farmer_router
from src.catalog.product.infrastructure.entrypoints import router as product_router
from src.commerce.order.infrastructure.entrypoints import router as order_router

_SessionFactory = sqlalchemy.ext.asyncio.async_sessionmaker[sqlalchemy.ext.asyncio.AsyncSession]


def _build_event_publisher(
    settings: app_config.Settings,
    session_factory: _SessionFactory,
) -> postgres_event_publisher.PostgresEventPublisher | stub_event_publisher.StubEventPublisher:
    if settings.environment in ("staging", "production"):
        email_svc = resend_email.ResendEmailAdapter(
            api_key=settings.resend_api_key,
            sender_email=settings.sender_email,
        )
        return postgres_event_publisher.PostgresEventPublisher(
            session_factory=session_factory,
            email_svc=email_svc,
        )
    return stub_event_publisher.StubEventPublisher()


def _build_token_adapter(
    settings: app_config.Settings,
    session_factory: _SessionFactory,
) -> postgres_refresh_token.PostgresRefreshTokenAdapter | stub_refresh_token.StubRefreshTokenAdapter:
    if settings.environment in ("staging", "production"):
        return postgres_refresh_token.PostgresRefreshTokenAdapter(
            session_factory=session_factory,
        )
    return stub_refresh_token.StubRefreshTokenAdapter()


def create_app() -> fastapi.FastAPI:
    settings = app_config.get_settings()

    app = fastapi.FastAPI(
        title="AgroConecta API",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
    )

    engine = db_session.build_engine(settings.database_url)
    session_factory = db_session.build_session_factory(engine)

    app.state.event_publisher = _build_event_publisher(settings, session_factory)
    app.state.token_adapter = _build_token_adapter(settings, session_factory)

    middleware.add_cors_middleware(app, settings.cors_origins_list)
    app.middleware("http")(middleware.build_db_session_middleware(session_factory))
    middleware.add_exception_handlers(app)

    api_v1 = fastapi.APIRouter(prefix="/api/v1")
    api_v1.include_router(auth_router.router)
    api_v1.include_router(farmer_router.router)
    api_v1.include_router(product_router.router)
    api_v1.include_router(product_router.traceability_router)
    api_v1.include_router(order_router.router)
    api_v1.include_router(order_router.admin_router)

    app.include_router(api_v1)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
