import pytest
from fastapi import status
from sqlalchemy import select

from src.models.books import Book
from src.models.sellers import Seller
from src.services.sellers import hash_password, verify_password

API_V1_URL_PREFIX = "/api/v1/seller"


async def get_auth_headers(async_client, e_mail, password):
    response = await async_client.post(
        "/api/v1/token",
        json={"e_mail": e_mail, "password": password},
    )
    assert response.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio()
async def test_create_seller(async_client):
    data = {
        "first_name": "Ivan",
        "last_name": "Petrov",
        "e_mail": "ivan@example.com",
        "password": "secret123",
    }

    response = await async_client.post(API_V1_URL_PREFIX, json=data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "id": 1,
        "first_name": "Ivan",
        "last_name": "Petrov",
        "e_mail": "ivan@example.com",
    }


@pytest.mark.asyncio()
async def test_get_sellers_list_without_password(db_session, async_client):
    seller = Seller(first_name="Ivan", last_name="Petrov", e_mail="ivan@example.com", password="secret")
    db_session.add(seller)
    await db_session.flush()

    response = await async_client.get(API_V1_URL_PREFIX)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "sellers": [
            {
                "id": seller.id,
                "first_name": "Ivan",
                "last_name": "Petrov",
                "e_mail": "ivan@example.com",
            }
        ]
    }
    assert "password" not in response.json()["sellers"][0]


@pytest.mark.asyncio()
async def test_get_single_seller_with_books_without_password(db_session, async_client):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        e_mail="ivan@example.com",
        password=hash_password("secret123"),
    )
    db_session.add(seller)
    await db_session.flush()

    book = Book(title="Book 1", author="Author 1", year=2024, pages=123, seller_id=seller.id)
    book_2 = Book(title="Book 2", author="Author 2", year=2025, pages=456, seller_id=seller.id)
    db_session.add_all([book, book_2])
    await db_session.flush()
    token_response = await async_client.post(
        "/api/v1/token",
        json={"e_mail": seller.e_mail, "password": "secret123"},
    )
    token = token_response.json()["access_token"]

    response = await async_client.get(
        f"{API_V1_URL_PREFIX}/{seller.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": seller.id,
        "first_name": "Ivan",
        "last_name": "Petrov",
        "e_mail": "ivan@example.com",
        "books": [
            {
                "id": book.id,
                "title": "Book 1",
                "author": "Author 1",
                "year": 2024,
                "pages": 123,
                "seller_id": seller.id,
            },
            {
                "id": book_2.id,
                "title": "Book 2",
                "author": "Author 2",
                "year": 2025,
                "pages": 456,
                "seller_id": seller.id,
            },
        ],
    }
    assert "password" not in response.json()


@pytest.mark.asyncio()
async def test_update_seller(db_session, async_client):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        e_mail="ivan@example.com",
        password=hash_password("secret123"),
    )
    db_session.add(seller)
    await db_session.flush()
    headers = await get_auth_headers(async_client, seller.e_mail, "secret123")

    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/{seller.id}",
        json={
            "first_name": "Petr",
            "last_name": "Sidorov",
            "e_mail": "petr@example.com",
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.refresh(seller)
    assert seller.first_name == "Petr"
    assert seller.last_name == "Sidorov"
    assert seller.e_mail == "petr@example.com"
    assert verify_password("secret123", seller.password)


@pytest.mark.asyncio()
async def test_delete_seller_deletes_books(db_session, async_client):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        e_mail="ivan@example.com",
        password=hash_password("secret123"),
    )
    db_session.add(seller)
    await db_session.flush()
    headers = await get_auth_headers(async_client, seller.e_mail, "secret123")

    book = Book(title="Book 1", author="Author 1", year=2024, pages=123, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{seller.id}", headers=headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    sellers = await db_session.execute(select(Seller))
    books = await db_session.execute(select(Book))

    assert sellers.scalars().all() == []
    assert books.scalars().all() == []


@pytest.mark.asyncio()
async def test_get_single_seller_with_other_seller_token(db_session, async_client):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        e_mail="ivan@example.com",
        password=hash_password("secret123"),
    )
    seller_2 = Seller(
        first_name="Petr",
        last_name="Sidorov",
        e_mail="petr@example.com",
        password=hash_password("secret456"),
    )
    db_session.add_all([seller, seller_2])
    await db_session.flush()

    token_response = await async_client.post(
        "/api/v1/token",
        json={"e_mail": seller.e_mail, "password": "secret123"},
    )
    token = token_response.json()["access_token"]

    response = await async_client.get(
        f"{API_V1_URL_PREFIX}/{seller_2.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio()
async def test_update_seller_with_other_seller_token(db_session, async_client):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        e_mail="ivan@example.com",
        password=hash_password("secret123"),
    )
    seller_2 = Seller(
        first_name="Petr",
        last_name="Sidorov",
        e_mail="petr@example.com",
        password=hash_password("secret456"),
    )
    db_session.add_all([seller, seller_2])
    await db_session.flush()

    headers = await get_auth_headers(async_client, seller.e_mail, "secret123")
    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/{seller_2.id}",
        json={
            "first_name": "Stepan",
            "last_name": "Stepanov",
            "e_mail": "stepan@example.com",
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio()
async def test_delete_seller_with_other_seller_token(db_session, async_client):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        e_mail="ivan@example.com",
        password=hash_password("secret123"),
    )
    seller_2 = Seller(
        first_name="Petr",
        last_name="Sidorov",
        e_mail="petr@example.com",
        password=hash_password("secret456"),
    )
    db_session.add_all([seller, seller_2])
    await db_session.flush()

    headers = await get_auth_headers(async_client, seller.e_mail, "secret123")
    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{seller_2.id}", headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
