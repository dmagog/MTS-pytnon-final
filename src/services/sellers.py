import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.sellers import Seller
from src.schemas.sellers import IncomingSeller, UpdateSeller

__all__ = ["SellerService", "hash_password", "verify_password"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


class SellerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_sellers(self) -> list[Seller]:
        result = await self.session.execute(select(Seller).order_by(Seller.id))
        return result.scalars().all()

    async def get_seller_by_id(self, seller_id: int) -> Seller | None:
        query = select(Seller).options(selectinload(Seller.books)).where(Seller.id == seller_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_seller_by_email(self, e_mail: str) -> Seller | None:
        result = await self.session.execute(select(Seller).where(Seller.e_mail == e_mail))
        return result.scalar_one_or_none()

    async def add_seller(self, seller: IncomingSeller) -> Seller:
        new_seller = Seller(
            first_name=seller.first_name,
            last_name=seller.last_name,
            e_mail=seller.e_mail,
            password=hash_password(seller.password),
        )
        self.session.add(new_seller)
        await self.session.flush()
        await self.session.refresh(new_seller)
        return new_seller

    async def update_seller(self, seller_id: int, seller_data: UpdateSeller) -> Seller | None:
        seller = await self.session.get(Seller, seller_id)
        if seller is None:
            return None

        seller.first_name = seller_data.first_name
        seller.last_name = seller_data.last_name
        seller.e_mail = seller_data.e_mail

        await self.session.flush()
        await self.session.refresh(seller)
        return seller

    async def delete_seller(self, seller_id: int) -> bool:
        seller = await self.session.get(Seller, seller_id)
        if seller is None:
            return False

        await self.session.delete(seller)
        await self.session.flush()
        return True
