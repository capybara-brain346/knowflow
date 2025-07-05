# Deployment Guide

## Infrastructure Overview

### Cloud Provider Requirements

- Kubernetes cluster (GKE/EKS/AKS)
- Load balancer
- Managed databases (optional)
- Object storage
- Monitoring and logging

## Deployment Environments

### Development

- Local Docker setup
- Mocked services where appropriate
- Hot reload enabled
- Debug logging

### Staging

- Minimal cloud resources
- Automated deployments
- Integration testing
- Performance monitoring

### Production

- High availability setup
- Auto-scaling
- Regular backups
- Full monitoring

## Infrastructure as Code

### Terraform Configuration

```hcl
# Main VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "knowflow-${var.environment}"
  }
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = "knowflow-${var.environment}"
  version  = "1.27"

  vpc_config {
    subnet_ids = aws_subnet.private[*].id
  }
}

# RDS Instance
resource "aws_db_instance" "postgres" {
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class      = "db.t3.medium"
  allocated_storage   = 50

  backup_retention_period = 7
  multi_az             = true
}
```

## Kubernetes Deployment

### Base Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowflow-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: knowflow-api
  template:
    spec:
      containers:
        - name: api
          image: knowflow/api:latest
          resources:
            requests:
              memory: "4Gi"
              cpu: "2"
            limits:
              memory: "8Gi"
              cpu: "4"
```

### Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: knowflow-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: knowflow-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Database Management

### Backup Strategy

1. **PostgreSQL**

   - Daily full backups
   - Point-in-time recovery
   - Cross-region replication

2. **Neo4j**

   - Regular snapshots
   - Transaction logs
   - Standby replicas

3. **Qdrant**
   - Volume snapshots
   - Regular backups
   - Replication setup

## Monitoring & Observability

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "knowflow-api"
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: knowflow-api
        action: keep
```

### Grafana Dashboards

1. API Performance

   - Request latency
   - Error rates
   - Throughput

2. Database Metrics

   - Connection pool
   - Query performance
   - Storage usage

3. Vector Search
   - Search latency
   - Index size
   - Cache hits/misses

## Security

### Network Security

1. VPC setup
2. Security groups
3. Network policies
4. WAF configuration

### Access Management

1. IAM roles
2. Service accounts
3. RBAC policies
4. Secret management

## SSL/TLS Configuration

### Certificate Management

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: knowflow-tls
spec:
  secretName: knowflow-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - api.knowflow.com
    - "*.knowflow.com"
```

## Deployment Process

### CI/CD Pipeline

1. Build and test
2. Security scan
3. Deploy to staging
4. Run integration tests
5. Deploy to production
6. Post-deployment checks

### Rollback Procedure

1. Identify issue
2. Revert deployment
3. Verify services
4. Root cause analysis

## Scaling Strategy

### Vertical Scaling

- API: Up to 8 vCPU, 16GB RAM
- Databases: Based on load

### Horizontal Scaling

- API: 3-10 replicas
- Read replicas for databases
- Load balancer configuration

## Disaster Recovery

### Backup Locations

- Primary region: us-east-1
- Backup region: us-west-2

### Recovery Time Objectives

- RTO: 4 hours
- RPO: 15 minutes

### Recovery Steps

1. Activate backup region
2. Restore from backups
3. Update DNS
4. Verify services

## Cost Optimization

### Resource Management

1. Right-sizing instances
2. Spot instances where applicable
3. Auto-scaling policies
4. Storage optimization

### Monitoring and Alerts

1. Cost anomaly detection
2. Budget alerts
3. Resource utilization
4. Waste identification

## Maintenance

### Update Strategy

1. Regular security updates
2. Database maintenance
3. Dependency updates
4. Infrastructure patches

### Maintenance Windows

- Non-critical: Weekly
- Security: As needed
- Database: Monthly

## Troubleshooting Guide

### Common Issues

1. Pod startup failures
2. Database connectivity
3. Memory pressure
4. Network issues

### Debug Process

1. Check logs
2. Monitor metrics
3. Review events
4. Analyze traces

## Contact Information

### On-Call Rotation

- Primary: DevOps Team
- Secondary: Database Team
- Escalation: Platform Team

### Emergency Procedures

1. Incident response
2. Communication plan
3. Escalation matrix
4. Post-mortem process
