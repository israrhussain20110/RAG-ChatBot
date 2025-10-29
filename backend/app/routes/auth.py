from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..schemas.user import Token
from ..services.auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password

# This is a fake user database. In a real app, you'd use a proper database.
FAKE_USERS_DB = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": get_password_hash("testpassword"),
        "disabled": False,
    }
}

router = APIRouter()

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return user_dict

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = get_user(FAKE_USERS_DB, form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
