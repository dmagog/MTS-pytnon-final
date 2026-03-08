from pydantic import AliasChoices, BaseModel, EmailStr, Field

__all__ = ["IncomingTokenRequest", "ReturnedToken"]


class IncomingTokenRequest(BaseModel):
    email: EmailStr = Field(validation_alias=AliasChoices("email", "e_mail"))
    password: str


class ReturnedToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
