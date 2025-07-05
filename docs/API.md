# KnowFlow API Documentation

## Overview

KnowFlow provides a RESTful API built with FastAPI for hybrid search combining vector similarity and knowledge graph traversal, using PostgreSQL with pgvector for vector storage and SQLAlchemy for ORM.

## Database Integration

The API uses SQLAlchemy with PostgreSQL and pgvector for:

- User management and authentication
- Document storage and metadata
- Vector embeddings and similarity search
- Full-text search capabilities

## Base URL

```
Production: https://api.knowflow.com/v1
Staging: https://api-staging.knowflow.com/v1
```

## Authentication

All API requests require a Bearer token in the Authorization header:

```
Authorization: Bearer <your_api_key>
```

## API Endpoints

### User Management

#### Register User

`POST /auth/register`

**Request Body:**

```json
{
  "email": "string",
  "password": "string",
  "name": "string"
}
```

**Response:**

```json
{
  "user_id": "string",
  "email": "string",
  "name": "string",
  "role": "user",
  "created_at": "2024-03-20T12:00:00Z"
}
```

### Document Management

#### Upload Document

`POST /documents/upload`

**Request Body (multipart/form-data):**

```
file: binary
title: string
description: string (optional)
```

**Response:**

```json
{
  "document_id": "string",
  "title": "string",
  "description": "string",
  "file_path": "string",
  "embeddings_status": "processing|completed|failed",
  "created_at": "2024-03-20T12:00:00Z"
}
```

### Vector Search

#### Semantic Search

`POST /search/semantic`

**Request Body:**

```json
{
  "query": "string",
  "filters": {
    "document_type": ["article", "paper"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-03-20"
    }
  },
  "limit": 10
}
```

**Response:**

```json
{
  "results": [
    {
      "document_id": "string",
      "title": "string",
      "content": "string",
      "metadata": {
        "file_type": "string",
        "uploaded_by": "string",
        "created_at": "2024-03-20T12:00:00Z"
      },
      "similarity_score": 0.95
    }
  ],
  "total": 1,
  "processing_time_ms": 150
}
```

## Implementation Details

### Database Models

The API uses SQLAlchemy models for database interactions:

```python
from sqlalchemy.orm import Session
from .models import User, Document
from .vector_store import vector_store

async def create_user(db: Session, user_data: dict):
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

async def search_documents(db: Session, query: str, filters: dict):
    # Vector search using LangChain PGVector
    vector_results = await vector_store.asimilarity_search(
        query=query,
        k=10,
        filter=filters
    )

    # Combine with metadata from documents table
    document_ids = [doc.metadata['document_id'] for doc in vector_results]
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()

    return documents
```

### Vector Store Integration

The API uses LangChain's PGVector for vector operations:

```python
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import OpenAIEmbeddings

# Initialize vector store
vector_store = PGVector(
    connection_string=POSTGRES_CONNECTION_STRING,
    embedding_function=OpenAIEmbeddings(),
    collection_name="document_embeddings"
)

# Add documents to vector store
async def index_document(document: Document, content: str):
    try:
        await vector_store.aadd_texts(
            texts=[content],
            metadatas=[{
                "document_id": document.id,
                "title": document.title,
                "file_type": document.file_type
            }]
        )
        return True
    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        return False
```

## Error Handling

Standard HTTP status codes are used:

- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

Error responses include:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

## Rate Limiting

- Free tier: 100 requests/hour
- Pro tier: 1000 requests/hour
- Enterprise: Custom limits

## Best Practices

1. Use connection pooling for database connections
2. Implement retry logic for vector operations
3. Cache frequently accessed embeddings
4. Use batch operations for multiple documents
5. Implement proper error handling and logging
6. Use appropriate indexes for better performance
7. Monitor query performance and optimize as needed
