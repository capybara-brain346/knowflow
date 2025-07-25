from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.auth import get_current_user, get_auth_service
from src.core.config import settings
from src.models.request import UserLogin, UserRegister
from src.models.response import (
    TokenResponse,
    UserResponse,
    RegisterResponse,
    MessageResponse,
)
from src.models.database import User
from src.services.auth_service import AuthService

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = auth_service.create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserRegister, auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.create_user(
        username=user_data.username, email=user_data.email, password=user_data.password
    )
    return RegisterResponse(
        message="User registered successfully", username=user.username
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
