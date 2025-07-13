# KnowFlow API Documentation

This document outlines the REST API endpoints available in KnowFlow.

## Authentication

The API uses OAuth2 with Bearer token authentication. Most endpoints require authentication through a Bearer token that can be obtained via the `/auth/token` or `/auth/login` endpoints.

### Base URL

All API endpoints are prefixed with `/api/v1`

## Endpoints

### Authentication Routes

#### Login for Access Token

- **POST** `/auth/token`
- **Description**: OAuth2 compatible token login
- **Request Body** (form-data):
  - `username`: string (email)
  - `password`: string
- **Response**:
  ```json
  {
    "access_token": "string",
    "token_type": "bearer",
    "user": {
      "id": "integer",
      "username": "string",
      "email": "string",
      "created_at": "datetime"
    }
  }
  ```

#### User Login

- **POST** `/auth/login`
- **Description**: Alternative JSON-based login endpoint
- **Request Body**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response**: Same as `/auth/token`

#### Register New User

- **POST** `/auth/register`
- **Description**: Register a new user
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "message": "User registered successfully",
    "username": "string"
  }
  ```

#### Logout

- **POST** `/auth/logout`
- **Auth**: Required
- **Response**:
  ```json
  {
    "message": "Successfully logged out"
  }
  ```

#### Get Current User

- **GET** `/auth/me`
- **Auth**: Required
- **Response**:
  ```json
  {
    "id": "integer",
    "username": "string",
    "email": "string",
    "created_at": "datetime"
  }
  ```

### Chat Routes

#### Send Chat Message

- **POST** `/chat`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "query": "string",
    "session_id": "string (optional)",
    "context": "object (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "message": "string",
    "context_used": "object (optional)",
    "session_id": "string (optional)"
  }
  ```

#### Follow-up Chat

- **POST** `/chat/followup/{session_id}`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "message": "string",
    "referenced_node_ids": "array[string] (optional)",
    "context_window": "integer (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "response": "string",
    "context_nodes": "array[object]",
    "memory_context": "object",
    "referenced_entities": "array[string]"
  }
  ```

### Document Routes

#### List Documents

- **GET** `/documents`
- **Auth**: Required
- **Query Parameters**:
  - `status`: string (optional) - Filter by document status
  - `page`: integer (default: 1)
  - `page_size`: integer (default: 10, max: 100)
- **Response**: Array of document objects

#### Upload Document

- **POST** `/documents/upload`
- **Auth**: Required
- **Request Body**: Multipart form data
  - `file`: File
- **Response**:
  ```json
  {
    "doc_id": "string",
    "status": "processing",
    "message": "string"
  }
  ```

#### Get Document

- **GET** `/documents/{doc_id}`
- **Auth**: Required
- **Response**: Document object

### Chat Session Routes

#### Create Session

- **POST** `/sessions`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "title": "string (optional)"
  }
  ```
- **Response**: Chat session object

#### List Sessions

- **GET** `/sessions`
- **Auth**: Required
- **Response**: Array of chat session objects with format:
  ```json
  {
    "id": "integer",
    "title": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "message_count": "integer",
    "last_message_at": "datetime (optional)"
  }
  ```

#### Get Session

- **GET** `/sessions/{session_id}`
- **Auth**: Required
- **Response**: Detailed chat session object including messages

#### Send Message in Session

- **POST** `/sessions/{session_id}/messages`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "content": "string",
    "context_used": "object (optional)"
  }
  ```
- **Response**: Updated chat session object

#### Delete Session

- **DELETE** `/sessions/{session_id}`
- **Auth**: Required
- **Response**: No content (204)

## Error Responses

All endpoints may return the following error responses:

- **401 Unauthorized**: Invalid or missing authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Requested resource not found
- **422 Unprocessable Entity**: Invalid request body or parameters
- **500 Internal Server Error**: Server-side error

Error responses follow this format:

```json
{
  "detail": "Error message"
}
```

```

This update reflects the current state of the API based on the route handlers and models provided in the codebase. The documentation has been updated to include:

1. More accurate authentication response models with user ID and timestamps
2. The new follow-up chat endpoint
3. Updated document routes with current request/response models
4. More detailed session route documentation
5. Removal of outdated admin-specific routes
6. More comprehensive request/response model documentation
7. Current validation rules from the models
```
