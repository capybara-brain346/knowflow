# KnowFlow API Documentation

## Overview

KnowFlow provides a RESTful API built with FastAPI for hybrid search combining vector similarity and knowledge graph traversal.

## API Documentation

Interactive API documentation is available at:

- Swagger UI: `http://api.knowflow.com/docs`
- ReDoc: `http://api.knowflow.com/redoc`

## Base URL

```
Production: https://api.knowflow.com/v1
Staging: https://api-staging.knowflow.com/v1
```

## FastAPI Implementation Details

### Dependencies

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
```

### Models

```python
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
```

## Authentication

All API requests require a Bearer token in the Authorization header:

```
Authorization: Bearer <your_api_key>
```

FastAPI OAuth2 implementation with JWT tokens.

## User Authentication & Management

### Register User

`POST /auth/register`

FastAPI Route:

```python
@app.post("/auth/register", response_model=User)
async def register_user(user: UserCreate):
    # Implementation details
```

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

### Login

`POST /auth/login`

FastAPI Route:

```python
@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Implementation details
```

**Request Body:**

```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "string",
  "user": {
    "id": "string",
    "email": "string",
    "name": "string",
    "role": "user|admin"
  }
}
```

### Refresh Token

`POST /auth/refresh`

FastAPI Route:

```python
@app.post("/auth/refresh")
async def refresh_token(refresh_token: str = Body(...)):
    # Implementation details
```

**Request Body:**

```json
{
  "refresh_token": "string"
}
```

**Response:**

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Admin Routes

#### Create Admin User

`POST /auth/admin/create`

FastAPI Route:

```python
@app.post("/auth/admin/create", dependencies=[Depends(admin_required)])
async def create_admin(user: UserCreate):
    # Implementation details
```

Requires existing admin authentication.

**Request Body:**

```json
{
  "email": "string",
  "password": "string",
  "name": "string"
}
```

#### List Users

`GET /auth/admin/users`

FastAPI Route:

```python
@app.get("/auth/admin/users", dependencies=[Depends(admin_required)])
async def list_users(skip: int = 0, limit: int = 100):
    # Implementation details
```

Requires admin authentication.

**Response:**

```json
{
  "users": [
    {
      "id": "string",
      "email": "string",
      "name": "string",
      "role": "user|admin",
      "created_at": "2024-03-20T12:00:00Z",
      "last_login": "2024-03-20T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1
}
```

## Search Endpoints

### Hybrid Search

`POST /search/hybrid`

FastAPI Route:

```python
@app.post("/search/hybrid", dependencies=[Depends(get_current_user)])
async def hybrid_search(query: SearchQuery):
    # Implementation details
```

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

## Document Management

### Upload Document

`POST /documents/upload`

FastAPI Route:

```python
@app.post("/documents/upload", dependencies=[Depends(admin_required)])
async def upload_document(
    file: UploadFile,
    metadata: DocumentMetadata = Depends()
):
    # Implementation details
```

**Request Body:**
Multipart form data with:

- File
- Metadata JSON

**Response:**

```json
{
  "document_id": "string",
  "status": "processing|completed|failed",
  "vector_id": "string",
  "graph_nodes": ["string"]
}
```

## Error Handling

FastAPI automatic error responses:

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail
            }
        }
    )
```

All errors follow this format:

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

Using FastAPI middleware:

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Implementation details
```

- Free tier: 100 requests/hour
- Pro tier: 1000 requests/hour
- Enterprise: Custom limits

## Best Practices

1. Use FastAPI dependency injection for:

   - Authentication
   - Database sessions
   - Rate limiting
   - Logging

2. Implement proper response models using Pydantic

3. Use FastAPI background tasks for:

   - Document processing
   - Vector embedding
   - Graph updates

4. Enable CORS middleware for frontend integration:

   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

5. Use proper status codes and response models
