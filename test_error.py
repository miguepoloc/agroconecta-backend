import asyncio
from src.shared_kernel.infrastructure.database.session import build_engine, build_session_factory
from src.shared_kernel.infrastructure import config
from src.catalog.product.infrastructure.repositories import SqlAlchemyProductRepository
from src.catalog.product.application.handlers.queries import handle_list_featured

async def main():
    settings = config.get_settings()
    engine = build_engine(settings.database_url)
    SessionFactory = build_session_factory(engine)
    try:
        async with SessionFactory() as session:
            res = await handle_list_featured(session)
            print(res)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
