from pydantic import BaseModel, EmailStr, Field, constr
from typing import Optional, Dict, Any
from datetime import datetime


# Auth Models
class UserLogin(BaseModel):
    username: str
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


# Chat Models
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


# Session Models
class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)
    context_used: Optional[Dict[str, Any]] = None


# Graph Models
class GraphQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    params: Optional[Dict[str, Any]] = None


# Admin Models
class DocumentMetadataRequest(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class DocumentIndexRequest(BaseModel):
    doc_id: str = Field(
        ...,
        pattern="^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    force_reindex: bool = False


# Search Models
class SearchParams(BaseModel):
    query: str = Field(..., min_length=1)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    filter_type: Optional[str] = None
    doc_type: Optional[str] = None
    date_range: Optional[tuple[datetime, datetime]] = None


class SearchSuggestionParams(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=20)


class RecentSearchParams(BaseModel):
    limit: int = Field(10, ge=1, le=50)
    user_id: Optional[int] = None
