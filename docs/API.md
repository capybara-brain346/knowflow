# KnowFlow API Documentation

## Overview

KnowFlow provides a RESTful API for hybrid search combining vector similarity and knowledge graph traversal.

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

## Rate Limiting

- Free tier: 100 requests/hour
- Pro tier: 1000 requests/hour
- Enterprise: Custom limits

## API Endpoints

### Search

#### Hybrid Search

`POST /search/hybrid`

Performs combined vector and graph-based search.

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
      "id": "string",
      "title": "string",
      "content": "string",
      "relevance_score": 0.95,
      "source": "vector|graph|hybrid",
      "metadata": {}
    }
  ],
  "total": 100,
  "page": 1
}
```

### Document Management

#### Upload Document

`POST /documents/upload`

**Request Body:**

```json
{
  "content": "string",
  "metadata": {
    "title": "string",
    "author": "string",
    "tags": ["string"]
  }
}
```

**Response:**

```json
{
  "document_id": "string",
  "status": "processing|completed|failed",
  "vector_id": "string",
  "graph_nodes": ["string"]
}
```

### Knowledge Graph

#### Query Graph

`POST /graph/query`

**Request Body:**

```json
{
  "query": "MATCH (n)-[r]->(m) WHERE n.type = 'concept' RETURN n, r, m LIMIT 10",
  "parameters": {}
}
```

### Vector Operations

#### Similarity Search

`POST /vectors/search`

**Request Body:**

```json
{
  "query_vector": [0.1, 0.2, ...],
  "top_k": 10
}
```

### Health Check

#### System Status

`GET /health`

**Response:**

```json
{
  "status": "healthy",
  "components": {
    "database": "up",
    "vector_store": "up",
    "graph_store": "up",
    "llm_service": "up"
  }
}
```

## Error Handling

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

Common Error Codes:

- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## Webhooks

### Document Processing Status

`POST <your_webhook_url>`

```json
{
  "event": "document.processed",
  "document_id": "string",
  "status": "completed",
  "timestamp": "2024-03-20T12:00:00Z"
}
```

## SDK Support

- Python
- JavaScript/TypeScript
- Go
- Java

## Best Practices

1. Always set appropriate timeouts
2. Implement exponential backoff for retries
3. Handle rate limits gracefully
4. Cache responses when appropriate
5. Use compression for large payloads
