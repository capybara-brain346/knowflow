from fastapi import APIRouter, HTTPException, status

from models.request import UserLogin, UserRegister
from models.response import (
    TokenResponse,
    UserResponse,
    RegisterResponse,
    MessageResponse,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    return {"access_token": "dummy_token", "token_type": "bearer"}


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserRegister):
    return {"message": "User registered successfully", "username": user_data.username}


@router.post("/logout", response_model=MessageResponse)
async def logout():
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user():
    return {"id": 1, "username": "current_user", "email": "user@example.com"}
