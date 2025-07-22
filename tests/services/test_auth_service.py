import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt
from src.services.auth_service import AuthService
from src.core.config import settings
from src.models.database import User


def test_verify_password(db_session):
    auth_service = AuthService(db_session)
    hashed_password = auth_service.get_password_hash("testpassword")
    assert auth_service.verify_password("testpassword", hashed_password)
    assert not auth_service.verify_password("wrongpassword", hashed_password)


def test_get_user_by_username(db_session, test_user):
    auth_service = AuthService(db_session)
    user = auth_service.get_user_by_username("testuser")
    assert user is not None
    assert user.username == "testuser"
    assert auth_service.get_user_by_username("nonexistent") is None


def test_get_user_by_email(db_session, test_user):
    auth_service = AuthService(db_session)
    user = auth_service.get_user_by_email("test@example.com")
    assert user is not None
    assert user.email == "test@example.com"
    assert auth_service.get_user_by_email("nonexistent@example.com") is None


def test_create_user_success(db_session):
    auth_service = AuthService(db_session)
    user = auth_service.create_user(
        username="newuser", email="new@example.com", password="password123"
    )
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert auth_service.verify_password("password123", user.hashed_password)


def test_create_user_duplicate_username(db_session, test_user):
    auth_service = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        auth_service.create_user(
            username="testuser", email="another@example.com", password="password123"
        )
    assert exc_info.value.status_code == 400
    assert "Username already registered" in str(exc_info.value.detail)


def test_create_user_duplicate_email(db_session, test_user):
    auth_service = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        auth_service.create_user(
            username="anotheruser", email="test@example.com", password="password123"
        )
    assert exc_info.value.status_code == 400
    assert "Email already registered" in str(exc_info.value.detail)


def test_authenticate_user_success(db_session):
    auth_service = AuthService(db_session)
    user = auth_service.create_user(
        username="authuser", email="auth@example.com", password="password123"
    )
    authenticated_user = auth_service.authenticate_user(
        "auth@example.com", "password123"
    )
    assert authenticated_user is not None
    assert authenticated_user.id == user.id


def test_authenticate_user_failure(db_session, test_user):
    auth_service = AuthService(db_session)
    assert auth_service.authenticate_user("test@example.com", "wrongpassword") is None
    assert (
        auth_service.authenticate_user("nonexistent@example.com", "password123") is None
    )


def test_create_access_token(db_session):
    auth_service = AuthService(db_session)
    data = {"sub": "1"}
    expires_delta = timedelta(minutes=15)
    token = auth_service.create_access_token(data, expires_delta)

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert decoded["sub"] == "1"
    assert "exp" in decoded


def test_get_current_user_success(db_session, test_user):
    auth_service = AuthService(db_session)
    token = auth_service.create_access_token({"sub": str(test_user.id)})
    user = auth_service.get_current_user(token)
    assert user.id == test_user.id


def test_get_current_user_invalid_token(db_session):
    auth_service = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        auth_service.get_current_user("invalid_token")
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in str(exc_info.value.detail)


def test_get_user_s3_prefix(db_session, test_user):
    auth_service = AuthService(db_session)
    prefix = auth_service.get_user_s3_prefix(test_user.id)
    assert prefix == f"user_{test_user.id}/"
