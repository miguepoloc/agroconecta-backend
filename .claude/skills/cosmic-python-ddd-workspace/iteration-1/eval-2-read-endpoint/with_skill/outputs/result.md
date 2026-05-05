# Eval 2 WITH SKILL — Endpoint GET /products/{product_id}

## Lo que ya existe (no requiere cambios)

| Archivo | Estado |
|---------|--------|
| `domain/exceptions.py` | `ProductNotFoundError` ya existe y registrada en middleware → HTTP 404 |
| `application/dtos/outputs.py` | `ProductDetailOutput` ya tiene precio, stock, imágenes |
| `infrastructure/repositories.py` | `find_by_id()` ya existe con selectinload |

## Query Handler — agregar a queries.py

```python
from src.shared_kernel.domain import value_objects as shared_value_objects

async def handle_get_product_by_id(
    product_id: str,
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> outputs.ProductDetailOutput:
    repo = product_repos.SqlAlchemyProductRepository(session)
    product = await repo.find_by_id(
        shared_value_objects.DomainId(value=product_id)
    )
    if product is None:
        raise product_exceptions.ProductNotFoundError(product_id)
    return _to_detail(product)
```

Sin UoW porque es solo lectura. Patrón idéntico a `handle_get_product_by_slug` ya existente.

## Router — agregar endpoint

```python
@router.get("/products/{product_id}", response_model=outputs.ProductDetailOutput)
async def get_product_by_id(
    product_id: str,
    request: fastapi.Request,
) -> outputs.ProductDetailOutput:
    return await queries.handle_get_product_by_id(product_id, request.state.db_session)
```

Sesión desde `request.state.db_session`, nunca `fastapi.Depends`.

## Convenciones verificadas
- ✅ session vía request.state.db_session (no Depends)
- ✅ Sin UoW para queries de solo lectura
- ✅ ProductNotFoundError (excepción de dominio, no HTTPException)
- ✅ Imports absolutos, import typing
- ✅ DTO correcto

## Flujo completo
```
GET /api/v1/products/a1b2c3d4-...
    → middleware abre AsyncSession → request.state.db_session
    → get_product_by_id()
    → handle_get_product_by_id() → repo.find_by_id()
    → None → ProductNotFoundError → middleware → 404
    → existe → mappers.orm_to_domain() → _to_detail() → ProductDetailOutput → 200
```
