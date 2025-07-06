from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.models.database import UserRole, DocumentStatus


# Auth Models
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime

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


# Chat and Session Models
class MessageResponse(BaseModel):
    id: int
    sender: str
    content: str
    context_used: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]
    user_id: int

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(default=0)
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    message: str
    context_used: Optional[Dict[str, Any]] = None
    session_id: Optional[int] = None


# Admin Models
class DocumentResponse(BaseModel):
    id: int
    doc_id: str
    title: str
    content_type: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    indexed_at: Optional[datetime]
    error_message: Optional[str]
    doc_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    doc_id: str
    status: DocumentStatus
    message: str


class DocumentIndexResponse(BaseModel):
    doc_id: str
    status: DocumentStatus
    chunks_processed: int
    message: str


# Graph Models
class GraphNodeResponse(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]


class GraphRelationResponse(BaseModel):
    source: str
    target: str
    type: str
    properties: Dict[str, Any]


class GraphQueryResponse(BaseModel):
    nodes: List[GraphNodeResponse]
    relations: List[GraphRelationResponse]
    metadata: Optional[Dict[str, Any]] = None


# Search Models
class SearchResult(BaseModel):
    id: int
    title: str
    content: str
    relevance_score: float
    doc_type: str
    snippet: str
    highlights: List[str]
    metadata: Optional[Dict[str, Any]]


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    page: int
    page_size: int
    query_time_ms: float
    facets: Optional[Dict[str, Any]] = None


class SearchSuggestionResponse(BaseModel):
    suggestions: List[str]
    query: str


class RecentSearchResponse(BaseModel):
    recent_searches: List[Dict[str, Any]]
    total_count: int


class FollowUpChatResponse(BaseModel):
    response: str
    context_nodes: List[Dict[str, Any]]
    memory_context: Dict[str, Any]
    referenced_entities: List[str]
