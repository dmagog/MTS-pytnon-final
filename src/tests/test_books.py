import pytest
from fastapi import status
from sqlalchemy import select

from src.models.books import Book
from src.models.sellers import Seller
from src.services.sellers import hash_password

API_V1_URL_PREFIX = "/api/v1/books"


async def create_seller(
    db_session,
    first_name="Ivan",
    last_name="Petrov",
    email="ivan@example.com",
    password="secret123",
):
    seller = Seller(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hash_password(password),
    )
    db_session.add(seller)
    await db_session.flush()
    return seller


async def get_auth_headers(async_client, seller, password="secret123"):
    response = await async_client.post(
        "/api/v1/token",
        json={"email": seller.email, "password": password},
    )
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio()
async def test_create_book(db_session, async_client):
    seller = await create_seller(db_session)
    headers = await get_auth_headers(async_client, seller)
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": seller.id,
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()
    resp_book_id = result_data.pop("id", None)

    assert resp_book_id is not None
    assert result_data == {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "pages": 300,
        "year": 2025,
        "seller_id": seller.id,
    }


@pytest.mark.asyncio()
async def test_create_book_with_old_year(db_session, async_client):
    seller = await create_seller(db_session)
    headers = await get_auth_headers(async_client, seller)
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 1986,
        "seller_id": seller.id,
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio()
async def test_get_books(db_session, async_client):
    seller = await create_seller(db_session)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=2021, pages=108, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2021,
                "id": book.id,
                "pages": 104,
                "seller_id": seller.id,
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 2021,
                "id": book_2.id,
                "pages": 108,
                "seller_id": seller.id,
            },
        ]
    }


@pytest.mark.asyncio()
async def test_get_single_book(db_session, async_client):
    seller = await create_seller(db_session)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=2024, pages=104, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2001,
        "pages": 104,
        "id": book.id,
        "seller_id": seller.id,
    }


@pytest.mark.asyncio()
async def test_get_single_book_with_wrong_id(db_session, async_client):
    seller = await create_seller(db_session)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/426548")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_update_book(db_session, async_client):
    seller = await create_seller(db_session)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=104, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()
    headers = await get_auth_headers(async_client, seller)

    data = {
        "title": "Mziri",
        "author": "Lermontov",
        "pages": 250,
        "year": 2024,
        "seller_id": seller.id,
    }

    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/{book.id}",
        json=data,
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.refresh(book)

    assert book.title == "Mziri"
    assert book.author == "Lermontov"
    assert book.pages == 250
    assert book.year == 2024
    assert book.seller_id == seller.id


@pytest.mark.asyncio()
async def test_delete_book(db_session, async_client):
    seller = await create_seller(db_session)
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


@pytest.mark.asyncio()
async def test_delete_book_with_invalid_book_id(db_session, async_client):
    seller = await create_seller(db_session)
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
