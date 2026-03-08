from pydantic import BaseModel, EmailStr

__all__ = ["IncomingTokenRequest", "ReturnedToken"]


class IncomingTokenRequest(BaseModel):
    e_mail: EmailStr
    password: str


class ReturnedToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
