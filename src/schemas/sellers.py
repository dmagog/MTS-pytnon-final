from pydantic import BaseModel, ConfigDict, EmailStr

from .books import ReturnedBook

__all__ = [
    "IncomingSeller",
    "ReturnedAllSellers",
    "ReturnedSeller",
    "ReturnedSellerDetail",
    "UpdateSeller",
]


class SellerBase(BaseModel):
    first_name: str
    last_name: str
    e_mail: EmailStr


class IncomingSeller(SellerBase):
    password: str


class UpdateSeller(SellerBase):
    pass


class ReturnedSeller(SellerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ReturnedSellerDetail(ReturnedSeller):
    books: list[ReturnedBook]

    model_config = ConfigDict(from_attributes=True)


class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSeller]
