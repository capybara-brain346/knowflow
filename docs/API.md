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
  - `username`: string
  - `password`: string
- **Response**:
  ```json
  {
    "access_token": "string",
    "token_type": "bearer",
    "user": {
      "username": "string",
      "email": "string",
      "role": "string"
    }
  }
  ```

#### User Login

- **POST** `/auth/login`
- **Description**: Alternative JSON-based login endpoint
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response**: Same as `/auth/token`

#### Register New User

- **POST** `/auth/register`
- **Description**: Register a new regular user
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
    "username": "string",
    "role": "string"
  }
  ```

#### Register Admin User

- **POST** `/auth/register/admin`
- **Description**: Register a new admin user (requires admin privileges)
- **Auth**: Required (Admin only)
- **Request Body**: Same as regular registration
- **Response**: Same as regular registration

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
    "username": "string",
    "email": "string",
    "role": "string"
  }
  ```

### Admin Routes

#### Upload Document

- **POST** `/admin/documents/upload`
- **Auth**: Required (Admin only)
- **Request Body**: Multipart form data
  - `file`: File
  - `metadata`: JSON object
- **Response**:
  ```json
  {
    "doc_id": "string",
    "status": "processing",
    "message": "string"
  }
  ```

#### Index Document

- **POST** `/admin/documents/{doc_id}/index`
- **Auth**: Required (Admin only)
- **Request Body**:
  ```json
  {
    "force_reindex": boolean
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "message": "string"
  }
  ```

#### List Documents

- **GET** `/admin/documents`
- **Auth**: Required (Admin only)
- **Query Parameters**:
  - `status`: string (optional)
  - `page`: integer (default: 1)
  - `page_size`: integer (default: 10, max: 100)
- **Response**: Array of document objects

#### Get Document

- **GET** `/admin/documents/{doc_id}`
- **Auth**: Required (Admin only)
- **Response**: Document object

### Chat Routes

#### Send Chat Message

- **POST** `/chat`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "query": "string",
    "session_id": "string",
    "context": {}
  }
  ```
- **Response**:
  ```json
  {
    "message": "string",
    "context_used": {},
    "session_id": "string"
  }
  ```

### Graph Routes

#### Query Graph

- **POST** `/graph/query`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "query": "string",
    "params": {}
  }
  ```
- **Response**:
  ```json
  {
    "nodes": [],
    "relations": [],
    "metadata": {}
  }
  ```

### Chat Session Routes

#### Create Session

- **POST** `/sessions`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "title": "string"
  }
  ```
- **Response**: Chat session object

#### List Sessions

- **GET** `/sessions`
- **Auth**: Required
- **Response**: Array of chat session objects

#### Get Session

- **GET** `/sessions/{session_id}`
- **Auth**: Required
- **Response**: Chat session object

#### Send Message in Session

- **POST** `/sessions/{session_id}/messages`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "content": "string",
    "context_used": {}
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

This API documentation provides a comprehensive overview of all available endpoints, their authentication requirements, request/response formats, and possible error responses. The documentation is structured to be easily readable and follows common REST API documentation practices.
```
