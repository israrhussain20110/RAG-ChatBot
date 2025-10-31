from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str


class TokenData(BaseModel):
    username: str | None = None

