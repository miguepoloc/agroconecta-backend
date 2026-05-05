"""FastAPI middleware — DB session injection, error handling, CORS."""

import logging
import typing

import fastapi
import fastapi.middleware.cors
import sqlalchemy.ext.asyncio

from src.shared_kernel.domain import exceptions as domain_exceptions
from src.identity.user.domain import exceptions as user_exceptions
from src.catalog.farmer.domain import exceptions as farmer_exceptions
from src.catalog.product.domain import exceptions as product_exceptions
from src.commerce.order.domain import exceptions as order_exceptions

logger = logging.getLogger(__name__)


def add_cors_middleware(
    app: fastapi.FastAPI,
    allowed_origins: list[str],
) -> None:
    wildcard = allowed_origins == ["*"]
    app.add_middleware(
        fastapi.middleware.cors.CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=not wildcard,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def build_db_session_middleware(
    session_factory: sqlalchemy.ext.asyncio.async_sessionmaker[
        sqlalchemy.ext.asyncio.AsyncSession
    ],
) -> typing.Callable[..., typing.Any]:
    async def middleware(
        request: fastapi.Request,
        call_next: typing.Callable[..., typing.Any],
    ) -> fastapi.Response:
        async with session_factory() as session:
            request.state.db_session = session
            response = await call_next(request)
        return response

    return middleware


def add_exception_handlers(app: fastapi.FastAPI) -> None:
    @app.exception_handler(user_exceptions.InvalidCredentialsError)
    @app.exception_handler(user_exceptions.UserBlockedError)
    async def handle_auth_error(
        request: fastapi.Request, exc: domain_exceptions.AuthorizationError
    ) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(
            status_code=401, content={"detail": exc.message}
        )

    @app.exception_handler(user_exceptions.EmailAlreadyExistsError)
    async def handle_conflict(
        request: fastapi.Request, exc: domain_exceptions.ConflictError
    ) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(
            status_code=409, content={"detail": exc.message}
        )

    @app.exception_handler(order_exceptions.InvalidStatusTransitionError)
    @app.exception_handler(order_exceptions.ProductOutOfStockError)
    @app.exception_handler(order_exceptions.MinimumLotNotMetError)
    async def handle_order_rule(
        request: fastapi.Request, exc: domain_exceptions.DomainException
    ) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(
            status_code=422, content={"detail": exc.message}
        )

    @app.exception_handler(order_exceptions.OrderNotFoundError)
    @app.exception_handler(farmer_exceptions.FarmerNotFoundError)
    @app.exception_handler(product_exceptions.ProductNotFoundError)
    @app.exception_handler(user_exceptions.UserNotFoundError)
    async def handle_not_found(
        request: fastapi.Request, exc: domain_exceptions.NotFoundError
    ) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(
            status_code=404, content={"detail": exc.message}
        )

    @app.exception_handler(domain_exceptions.BusinessRuleViolationError)
    async def handle_business_rule(
        request: fastapi.Request, exc: domain_exceptions.BusinessRuleViolationError
    ) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(
            status_code=422, content={"detail": exc.message}
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(
        request: fastapi.Request, exc: Exception
    ) -> fastapi.responses.JSONResponse:
        logger.exception("Unexpected error: %s", exc)
        return fastapi.responses.JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
