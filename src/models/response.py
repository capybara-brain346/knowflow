from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.models.database import DocumentStatus


# Auth Models
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
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
    id: str
    title: str
    user_id: int
    memory_context: Dict[str, Any] = Field(default_factory=dict)
    recent_node_ids: List[str] = Field(default_factory=list)
    last_activity: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    id: str
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = 0
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    message: str
    context_used: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


# Doument Models
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


class MultiDocumentUploadResponse(BaseModel):
    documents: List[Dict[str, Any]]
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


class RenameChatResponse(BaseModel):
    session_id: str
    title: str

    class Config:
        from_attributes = True


class DeleteChatResponse(BaseModel):
    session_id: str
    status: str = Field(..., description="Status of the deletion operation")
