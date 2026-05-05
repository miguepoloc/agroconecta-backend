"""Order API router — /api/v1/orders and /api/v1/admin/orders."""

import typing

import fastapi

from src.entrypoints import dependencies
from src.commerce.order.application.dtos import inputs, outputs
from src.commerce.order.application.handlers import commands, queries
from src.identity.user.domain import types as user_types

router = fastapi.APIRouter(prefix="/orders", tags=["orders"])
admin_router = fastapi.APIRouter(prefix="/admin/orders", tags=["admin-orders"])


@router.post("", response_model=outputs.OrderOutput, status_code=201)
async def place_order(
    body: inputs.PlaceOrderInput,
    request: fastapi.Request,
    current_user: dependencies.CurrentUser,
) -> outputs.OrderOutput:
    from src.shared_kernel.infrastructure import config as app_config
    settings = app_config.get_settings()
    return await commands.handle_place_order(
        command=body,
        session=request.state.db_session,
        settings=settings,
        publisher=request.app.state.event_publisher,
        buyer_id=str(current_user.id),
        buyer_role=current_user.role.value,
    )


@router.get("/me", response_model=list[outputs.OrderSummaryOutput])
async def list_my_orders(
    request: fastapi.Request,
    current_user: dependencies.CurrentUser,
    limit: int = fastapi.Query(20, ge=1, le=100),
    offset: int = fastapi.Query(0, ge=0),
) -> list[outputs.OrderSummaryOutput]:
    return await queries.handle_list_my_orders(
        buyer_id=str(current_user.id),
        session=request.state.db_session,
        limit=limit,
        offset=offset,
    )


@router.get("/{order_id}", response_model=outputs.OrderOutput)
async def get_order(
    order_id: str,
    request: fastapi.Request,
    current_user: dependencies.CurrentUser,
) -> outputs.OrderOutput:
    return await queries.handle_get_order(
        order_id=order_id,
        buyer_id=str(current_user.id),
        is_admin=current_user.role == user_types.UserRole.ADMIN,
        session=request.state.db_session,
    )


@admin_router.get("", response_model=list[outputs.OrderSummaryOutput])
async def admin_list_orders(
    request: fastapi.Request,
    current_user: dependencies.CurrentUser,
    status: typing.Optional[str] = fastapi.Query(None),
    order_type: typing.Optional[str] = fastapi.Query(None),
    limit: int = fastapi.Query(20, ge=1, le=100),
    offset: int = fastapi.Query(0, ge=0),
) -> list[outputs.OrderSummaryOutput]:
    if current_user.role != user_types.UserRole.ADMIN:
        raise fastapi.HTTPException(status_code=403, detail="Admin only")
    return await queries.handle_list_all_orders(
        session=request.state.db_session,
        status=status,
        order_type=order_type,
        limit=limit,
        offset=offset,
    )


@admin_router.get("/{order_id}", response_model=outputs.OrderOutput)
async def admin_get_order(
    order_id: str,
    request: fastapi.Request,
    current_user: dependencies.CurrentUser,
) -> outputs.OrderOutput:
    if current_user.role != user_types.UserRole.ADMIN:
        raise fastapi.HTTPException(status_code=403, detail="Admin only")
    return await queries.handle_get_order(
        order_id=order_id,
        buyer_id=str(current_user.id),
        is_admin=True,
        session=request.state.db_session,
    )


@admin_router.patch("/{order_id}/status", response_model=outputs.OrderOutput)
async def admin_change_status(
    order_id: str,
    body: inputs.ChangeOrderStatusInput,
    request: fastapi.Request,
    current_user: dependencies.CurrentUser,
) -> outputs.OrderOutput:
    if current_user.role != user_types.UserRole.ADMIN:
        raise fastapi.HTTPException(status_code=403, detail="Admin only")
    return await commands.handle_change_status(
        order_id=order_id,
        command=body,
        session=request.state.db_session,
        publisher=request.app.state.event_publisher,
    )
