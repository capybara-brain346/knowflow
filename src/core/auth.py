from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.database import User
from src.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    return auth_service.get_current_user(token)
