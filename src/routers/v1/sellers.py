from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.models.sellers import Seller
from src.schemas import (
    IncomingSeller,
    ReturnedAllSellers,
    ReturnedSeller,
    ReturnedSellerDetail,
    UpdateSeller,
)
from src.services import SellerService, get_current_seller

sellers_router = APIRouter(prefix="/seller", tags=["seller"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentSeller = Annotated[Seller, Depends(get_current_seller)]


@sellers_router.post("", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED)
async def create_seller(seller: IncomingSeller, session: DBSession):
    service = SellerService(session)
    existing_seller = await service.get_seller_by_email(seller.email)
    if existing_seller is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seller with this email already exists")

    return await service.add_seller(seller)


@sellers_router.get("", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    sellers = await SellerService(session).get_all_sellers()
    return {"sellers": sellers}


@sellers_router.get("/{seller_id}", response_model=ReturnedSellerDetail)
async def get_single_seller(seller_id: int, session: DBSession, current_seller: CurrentSeller):
    if current_seller.id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can view only your own profile")

    seller = await SellerService(session).get_seller_by_id(seller_id)
    if seller is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return seller


@sellers_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(seller_id: int, seller_data: UpdateSeller, session: DBSession, current_seller: CurrentSeller):
    if current_seller.id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can edit only your own profile")

    service = SellerService(session)
    existing_seller = await service.get_seller_by_email(seller_data.email)
    if existing_seller is not None and existing_seller.id != seller_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seller with this email already exists")

    seller = await service.update_seller(seller_id, seller_data)
    if seller is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return seller


@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession, current_seller: CurrentSeller):
    if current_seller.id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can delete only your own profile")

    deleted = await SellerService(session).delete_seller(seller_id)
    if not deleted:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
