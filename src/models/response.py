from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from src.models.database import UserRole


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class RegisterResponse(BaseModel):
    message: str
    username: str
    role: UserRole


class MessageResponse(BaseModel):
    message: str


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    id: int
    title: str
    content: str
    relevance_score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    page: int
    page_size: int


class SearchSuggestionResponse(BaseModel):
    suggestions: List[str]


class RecentSearchResponse(BaseModel):
    recent_searches: List[str]
