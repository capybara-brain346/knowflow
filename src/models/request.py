from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class SearchParams(BaseModel):
    query: str = Field(..., min_length=1)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    filter_type: Optional[str] = None


class SearchSuggestionParams(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=20)


class RecentSearchParams(BaseModel):
    limit: int = Field(10, ge=1, le=50)


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str
    context_used: Optional[dict] = None
