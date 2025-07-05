from pydantic import BaseModel
from typing import List

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class RegisterResponse(BaseModel):
    message: str
    username: str

class MessageResponse(BaseModel):
    message: str

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
