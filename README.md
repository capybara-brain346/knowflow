# KnowFlow
---
![Gemini_Generated_Image_j5414ij5414ij541](https://github.com/user-attachments/assets/032a9bc6-b0fb-437d-93cd-a9f063220e03)

# Deployment
---
<img width="2942" height="2022" alt="diagram-export-7-20-2025-6_03_33-PM" src="https://github.com/user-attachments/assets/8f8fc44a-766d-48c0-97aa-59ef0883bdfd" />

# AI Infra
---
<img width="4030" height="3416" alt="diagram-export-7-20-2025-6_57_03-PM" src="https://github.com/user-attachments/assets/22e8bfb1-ebc2-4824-80b0-5cf01e4094cc" />

KnowFlow is a powerful hybrid Retrieval-Augmented Generation (RAG) system that combines semantic search with knowledge graph capabilities for intelligent document processing and querying.

## 🌟 Features

- **Advanced Document Processing**

  - Multi-format support (PDF, DOCX, CSV, TXT)
  - Intelligent chunking with configurable size and overlap
  - Parallel batch processing with S3 storage
  - Document status tracking (PENDING, PROCESSING, INDEXED, FAILED)
  - Secure per-user document isolation

- **Hybrid RAG + Knowledge Graph Architecture**

  - Dense semantic embeddings via Google Gemini + pgvector
  - Structured knowledge extraction to Neo4j
  - Multi-hop reasoning through graph relationships
  - Automatic entity and relationship mapping
  - Query decomposition for complex questions

- **Smart Query Processing**

  - Automatic query decomposition for complex questions
  - Hybrid vector + graph-based retrieval
  - Retrieval quality evaluation and improvement
  - Context-aware response synthesis
  - Conversation memory with graph context

- **Chat & Session Management**

  - Persistent chat sessions with history
  - Context-aware follow-up questions
  - Session renaming and management
  - Message tracking with context preservation
  - Multi-user support with isolation

- **Security & Authentication**

  - JWT-based authentication
  - Secure password hashing with bcrypt
  - Role-based access control
  - Per-user data isolation
  - Document access verification

- **Storage & Infrastructure**
  - S3-compatible object storage
  - PostgreSQL for structured data
  - Neo4j for graph relationships
  - Concurrent file operations
  - Efficient batch processing

## 🏗️ Architecture

```mermaid
graph TD
    A[Frontend React/Vite] -->|REST API| B[FastAPI Backend]
    B --> C[PostgreSQL + pgvector]
    B --> D[Neo4j Graph DB]
    B --> E[Google Gemini API]
    B --> F[S3 Storage]

    subgraph Document Processing
        G[Document Upload] --> H[Chunking]
        H --> I[Vector Embedding]
        H --> J[Knowledge Extraction]
    end

    subgraph Query Processing
        K[User Query] --> L[Query Decomposition]
        L --> M[Vector Search]
        L --> N[Graph Traversal]
        M --> O[Response Synthesis]
        N --> O
    end

    C -->|Semantic Search| B
    D -->|Knowledge Graph| B
    F -->|Document Storage| B
    E -->|Embeddings & Generation| B
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 14+ with pgvector extension
- Neo4j 5.0+
- S3-compatible storage
- Google Cloud API key for Gemini

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/knowflow
VECTOR_COLLECTION_NAME=document_embeddings

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Google API
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL_NAME=gemini-pro
GEMINI_EMBEDDING_MODEL=embedding-001

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=knowflow-documents

# App Settings
SECRET_KEY=your_jwt_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=60
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
TOP_K_RESULTS=3
```

### Development Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/knowflow.git
cd knowflow
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run migrations:

```bash
alembic upgrade head
```

4. Start the development server:

```bash
uvicorn src.main:app --reload
```

## 📚 API Documentation

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Documents

- `POST /documents/upload` - Upload multiple documents
- `POST /documents/{doc_id}/index` - Index document content
- `GET /documents` - List user documents
- `GET /documents/{doc_id}` - Get document details

### Chat

- `POST /chat/query` - Process a new query
- `POST /chat/sessions/{session_id}/messages` - Send follow-up message
- `GET /chat/sessions` - List chat sessions
- `PUT /chat/sessions/{session_id}/rename` - Rename session
- `DELETE /chat/sessions/{session_id}` - Delete session

## 🔒 Security Features

- JWT-based authentication with expiration
- Bcrypt password hashing
- Per-user document isolation
- Access control verification
- Secure file storage paths
- Input validation and sanitization

## 📊 Monitoring & Logging

- Structured logging with levels
- Request/response tracking
- Error handling and reporting
- Performance metrics
- Document processing status
- Chat session analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the terms of the LICENSE file included in the repository.
