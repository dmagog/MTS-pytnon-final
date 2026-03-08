import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncConnection, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.configurations.settings import settings
from src.models import books, sellers  # noqa
from src.models.base import BaseModel
from src.models.books import Book  # noqa F401
from src.models.sellers import Seller  # noqa F401

async_test_engine = create_async_engine(
    settings.database_test_url,
    echo=True,
    poolclass=NullPool,
)

async_test_session = async_sessionmaker(async_test_engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def create_tables() -> None:
    async with async_test_engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.drop_all)
        await connection.run_sync(BaseModel.metadata.create_all)


@pytest_asyncio.fixture(scope="function")
async def db_connection() -> AsyncConnection:
    async with async_test_engine.connect() as connection:
        transaction = await connection.begin()
        yield connection
        await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_connection: AsyncConnection):
    async with async_test_session(bind=db_connection, join_transaction_mode="create_savepoint") as session:
        yield session
        await session.close()


@pytest.fixture(scope="function")
def override_get_async_session(db_session):
    async def _override_get_async_session():
        yield db_session

    return _override_get_async_session


@pytest.fixture(scope="function")
def test_app(override_get_async_session):
    from src.configurations.database import get_async_session
    from src.main import app

    app.dependency_overrides[get_async_session] = override_get_async_session

    yield app

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app):
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as test_client:
        yield test_client
