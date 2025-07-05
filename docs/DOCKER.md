# Docker Setup Guide

## Prerequisites

- Docker Engine 24.0+
- Docker Compose v2.0+
- At least 16GB RAM for development setup
- 50GB free disk space

## Project Structure

```
docker/
├── development/
│   ├── Dockerfile
│   └── docker-compose.yml
├── production/
│   ├── Dockerfile
│   └── docker-compose.yml
└── scripts/
    ├── init-db.sh
    └── healthcheck.sh
```

## Quick Start

### Development Environment

```bash
# Start all services
docker compose -f docker/development/docker-compose.yml up -d

# View logs
docker compose -f docker/development/docker-compose.yml logs -f

# Stop all services
docker compose -f docker/development/docker-compose.yml down
```

### Production Environment

```bash
# Start production stack
docker compose -f docker/production/docker-compose.yml up -d

# Scale API servers
docker compose -f docker/production/docker-compose.yml up -d --scale api=3
```

## Services Configuration

### API Service

```yaml
api:
  build:
    context: .
    dockerfile: docker/production/Dockerfile
  environment:
    - POSTGRES_HOST=postgres
    - QDRANT_HOST=qdrant
    - NEO4J_URI=neo4j://neo4j:7687
    - GROQ_API_KEY=${GROQ_API_KEY}
  ports:
    - "8000:8000"
```

### Vector Database (Qdrant)

```yaml
qdrant:
  image: qdrant/qdrant:latest
  volumes:
    - qdrant_data:/qdrant/storage
  ports:
    - "6333:6333"
```

### Knowledge Graph (Neo4j)

```yaml
neo4j:
  image: neo4j:5.11
  environment:
    - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
  volumes:
    - neo4j_data:/data
  ports:
    - "7474:7474"
    - "7687:7687"
```

### PostgreSQL

```yaml
postgres:
  image: postgres:16
  environment:
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
  ports:
    - "5432:5432"
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Database
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=knowflow
POSTGRES_USER=knowflow

# Neo4j
NEO4J_PASSWORD=secure_password

# API Keys
GROQ_API_KEY=your_groq_api_key

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

## Volume Management

### List of Volumes

- `postgres_data`: PostgreSQL data
- `qdrant_data`: Vector database storage
- `neo4j_data`: Graph database files

### Backup Volumes

```bash
# Backup PostgreSQL
docker exec postgres pg_dump -U knowflow > backup.sql

# Backup Qdrant
docker run --rm --volumes-from qdrant -v $(pwd):/backup ubuntu tar cvf /backup/qdrant.tar /qdrant/storage

# Backup Neo4j
docker exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j.dump
```

## Health Checks

The `healthcheck.sh` script monitors:

- API service health
- Database connections
- Vector store status
- Graph database status

```bash
# Run health checks
./docker/scripts/healthcheck.sh
```

## Resource Requirements

### Development

- API: 2 vCPU, 4GB RAM
- Qdrant: 2 vCPU, 4GB RAM
- Neo4j: 2 vCPU, 4GB RAM
- PostgreSQL: 1 vCPU, 2GB RAM

### Production

- API: 4 vCPU, 8GB RAM per instance
- Qdrant: 4 vCPU, 16GB RAM
- Neo4j: 4 vCPU, 16GB RAM
- PostgreSQL: 2 vCPU, 4GB RAM

## Troubleshooting

### Common Issues

1. **Services Won't Start**

   ```bash
   # Check logs
   docker compose logs <service_name>

   # Verify resources
   docker stats
   ```

2. **Database Connection Issues**

   ```bash
   # Check network
   docker network ls
   docker network inspect knowflow_network
   ```

3. **Volume Mounting Problems**

   ```bash
   # List volumes
   docker volume ls

   # Inspect volume
   docker volume inspect <volume_name>
   ```

## Security Best Practices

1. Use non-root users in Dockerfiles
2. Implement resource limits
3. Regular security updates
4. Proper secret management
5. Network isolation

## Monitoring

### Prometheus & Grafana Setup

```yaml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
build:
  docker:
    - build -t knowflow:$TAG .
    - docker push knowflow:$TAG
```
