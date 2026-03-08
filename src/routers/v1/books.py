from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.models.sellers import Seller
from src.schemas import IncomingBook, PatchBook, ReturnedAllBooks, ReturnedBook, UpdateBook
from src.services import BookService, get_current_seller

books_router = APIRouter(prefix="/books", tags=["books"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentSeller = Annotated[Seller, Depends(get_current_seller)]


@books_router.get("/", response_model=ReturnedAllBooks)
async def get_all_books(session: DBSession):
    books = await BookService(session).get_all_books()
    return {"books": books}


@books_router.post("/", response_model=ReturnedBook, status_code=status.HTTP_201_CREATED)
async def create_book(book: IncomingBook, session: DBSession, current_seller: CurrentSeller):
    if book.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can create books only for yourself")

    new_book = await BookService(session).add_book(book)
    if new_book is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return new_book


@books_router.get("/{book_id}", response_model=ReturnedBook)
async def get_single_book(book_id: int, session: DBSession):
    book = await BookService(session).get_single_book(book_id)

    if book is not None:
        return book

    return Response(status_code=status.HTTP_404_NOT_FOUND)


@books_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, session: DBSession):

    deleted_book = await BookService(session).delete_book(book_id)

    if not deleted_book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@books_router.put("/{book_id}", response_model=ReturnedBook)
async def update_book(book_id: int, new_book_data: UpdateBook, session: DBSession, current_seller: CurrentSeller):
    existing_book = await BookService(session).get_single_book(book_id)
    if existing_book is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    if existing_book.seller_id != current_seller.id or new_book_data.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can edit only your own books")

    updated_book = await BookService(session).update_book(book_id, new_book_data)

    if not updated_book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return updated_book


@books_router.patch("/{book_id}", response_model=ReturnedBook)
async def patch_book(book_id: int, patched_book: PatchBook, session: DBSession, current_seller: CurrentSeller):
    existing_book = await BookService(session).get_single_book(book_id)
    if existing_book is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    if existing_book.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can edit only your own books")
    if patched_book.seller_id is not None and patched_book.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can edit only your own books")

    book = await BookService(session).partial_update_book(book_id, patched_book)

    if not book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return book
