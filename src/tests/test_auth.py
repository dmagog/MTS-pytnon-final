import pytest
from fastapi import status

from src.models.books import Book
from src.models.sellers import Seller
from src.services.sellers import hash_password


async def create_authorized_seller(db_session, email="ivan@example.com", password="secret123"):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        email=email,
        password=hash_password(password),
    )
    db_session.add(seller)
    await db_session.flush()
    return seller, password


async def get_access_token(async_client, email, password):
    response = await async_client.post(
        "/api/v1/token",
        json={"email": email, "password": password},
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]


@pytest.mark.asyncio()
async def test_create_token(db_session, async_client):
    seller, password = await create_authorized_seller(db_session)

    response = await async_client.post(
        "/api/v1/token",
        json={"email": seller.email, "password": password},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


@pytest.mark.asyncio()
async def test_get_single_seller_requires_token(db_session, async_client):
    seller, _ = await create_authorized_seller(db_session)

    response = await async_client.get(f"/api/v1/seller/{seller.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
async def test_get_single_seller_with_token(db_session, async_client):
    seller, password = await create_authorized_seller(db_session)
    book = Book(title="Book 1", author="Author 1", year=2024, pages=111, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()
    token = await get_access_token(async_client, seller.email, password)

    response = await async_client.get(
        f"/api/v1/seller/{seller.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == seller.id
    assert response.json()["books"][0]["seller_id"] == seller.id


@pytest.mark.asyncio()
async def test_create_book_requires_token(db_session, async_client):
    seller, _ = await create_authorized_seller(db_session)

    response = await async_client.post(
        "/api/v1/books/",
        json={
            "title": "Book 1",
            "author": "Author 1",
            "count_pages": 123,
            "year": 2024,
            "seller_id": seller.id,
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
async def test_create_book_with_token(db_session, async_client):
    seller, password = await create_authorized_seller(db_session)
    token = await get_access_token(async_client, seller.email, password)

    response = await async_client.post(
        "/api/v1/books/",
        json={
            "title": "Book 1",
            "author": "Author 1",
            "count_pages": 123,
            "year": 2024,
            "seller_id": seller.id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["seller_id"] == seller.id


@pytest.mark.asyncio()
async def test_update_book_with_token(db_session, async_client):
    seller, password = await create_authorized_seller(db_session)
    book = Book(title="Book 1", author="Author 1", year=2024, pages=111, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()
    token = await get_access_token(async_client, seller.email, password)

    response = await async_client.put(
        f"/api/v1/books/{book.id}",
        json={
            "title": "Book 2",
            "author": "Author 2",
            "pages": 222,
            "year": 2025,
            "seller_id": seller.id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Book 2"
