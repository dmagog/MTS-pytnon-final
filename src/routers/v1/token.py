from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.schemas import IncomingTokenRequest, ReturnedToken
from src.services import SellerService, create_access_token, verify_password

token_router = APIRouter(prefix="/token", tags=["token"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


@token_router.post("", response_model=ReturnedToken)
async def create_token(credentials: IncomingTokenRequest, session: DBSession):
    seller = await SellerService(session).get_seller_by_email(credentials.email)
    if seller is None or not verify_password(credentials.password, seller.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return {"access_token": create_access_token(seller), "token_type": "bearer"}
