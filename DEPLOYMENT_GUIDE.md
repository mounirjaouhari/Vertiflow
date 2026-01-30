# VertiFlow Deployment Guide
## Document Reference: TICKET-118
**Date**: January 3, 2026  
**Version**: 1.0.0  
**Author/Team**: @Imrane (DevOps & Infrastructure Lead), @MrZakaria (Project Lead)  
**Status**: Production  
**Classification**: Technical - Internal  
**Last Modified**: 2026-01-03  

---

## Executive Summary

This guide provides comprehensive instructions for deploying VertiFlow across development, staging, and production environments. It covers infrastructure setup, containerization, configuration management, database initialization, monitoring, and disaster recovery procedures.

**Target Audience:** DevOps engineers, system administrators, cloud infrastructure teams

**Deployment Timeline:**
- Development: 30 minutes (local Docker Compose)
- Staging: 2-4 hours (cloud infrastructure)
- Production: 4-8 hours (high availability setup)

---

## Table of Contents

1. [Pre-Deployment Requirements](#pre-deployment-requirements)
2. [Local Development Deployment](#local-development-deployment)
3. [Docker Container Deployment](#docker-container-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Platform Deployment](#cloud-platform-deployment)
6. [Database Initialization](#database-initialization)
7. [Configuration Management](#configuration-management)
8. [Service Connectivity Verification](#service-connectivity-verification)
9. [Health Checks & Monitoring](#health-checks--monitoring)
10. [Backup & Disaster Recovery](#backup--disaster-recovery)
11. [Troubleshooting](#troubleshooting)

---

## 1. Pre-Deployment Requirements

### 1.1 System Requirements

**Minimum Specifications (Development):**
```
CPU: 4 cores (Intel/AMD x86_64 or Apple Silicon)
RAM: 8 GB
Storage: 50 GB SSD
OS: Ubuntu 20.04+, macOS 11+, or Windows 10+ with WSL2
```

**Recommended Specifications (Production):**
```
CPU: 16+ cores
RAM: 64 GB
Storage: 500 GB SSD (ClickHouse) + 200 GB storage (Kafka)
OS: Ubuntu 20.04 LTS or RHEL 8.0+
Network: 1 Gbps+ connectivity
```

### 1.2 Software Prerequisites

```bash
# Required
- Docker: 20.10+ (docker --version)
- Docker Compose: 2.0+ (docker-compose --version)
- Git: 2.30+ (git --version)
- Python: 3.11+ (python --version)
- kubectl: 1.24+ (for Kubernetes deployment)

# Cloud-specific
- AWS CLI: 2.0+ (for AWS deployment)
- Azure CLI: 2.30+ (for Azure deployment)
- gcloud: 350.0+ (for GCP deployment)

# Development
- Make: 4.0+ (make --version)
- jq: 1.6+ (for JSON processing)
- curl: 7.68+ (for API testing)
```

### 1.3 Network Requirements

**Ports to be available (development):**
```
1883  : MQTT (Mosquitto)
2181  : Zookeeper
6379  : Redis
8123  : ClickHouse HTTP
8443  : NiFi
8501  : Streamlit (optional)
8761  : Eureka (optional)
9000  : ClickHouse TCP
9092  : Kafka broker
27017 : MongoDB
```

**Firewall rules (production):**
```
Inbound:
  - 443/tcp   : HTTPS (API)
  - 80/tcp    : HTTP (redirect)
  - 22/tcp    : SSH (administrative)
  - 3306/tcp  : MySQL (if using)

Outbound:
  - All to external API providers (NASA, NOAA, Market data)
  - 443/tcp to registry (Docker Hub, ECR, etc.)
```

---

## 2. Local Development Deployment

### 2.1 Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/J-Mounir/test-projet-agri.git
cd test-projet-agri/vertiflow-data-platform

# 2. Create .env from template
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be healthy
docker-compose ps

# 5. Initialize databases
python scripts/init_clickhouse.py
python scripts/init_mongodb.py
python scripts/init_kafka_topics.py

# 6. Validate deployment
python scripts/validate_deployment.py

# Expected output:
# ✅ ClickHouse: Connected (version 23.10)
# ✅ MongoDB: Connected (version 6.0)
# ✅ Kafka: Connected (3 brokers, 12 topics)
# ✅ Redis: Connected
# ✅ MQTT: Connected
# ✅ All systems operational
```

### 2.2 Docker Compose Stack Overview

```yaml
# docker-compose.yml structure

version: '3.8'

services:
  # Message Queue
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    ports: ["2181:2181"]
    
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports: ["9092:9092", "29092:29092"]
    depends_on: [zookeeper]
    
  # Database
  clickhouse:
    image: clickhouse/clickhouse-server:23.10
    ports: ["8123:8123", "9000:9000"]
    
  mongodb:
    image: mongo:6.0
    ports: ["27017:27017"]
    
  # Cache
  redis:
    image: redis:7.2-alpine
    ports: ["6379:6379"]
    
  # IoT
  mosquitto:
    image: eclipse-mosquitto:2.0
    ports: ["1883:1883"]
    
  # Data Integration
  nifi:
    image: apache/nifi:1.20.0
    ports: ["8443:8443"]
    
  # VertiFlow Services (custom)
  vertiflow-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports: ["8000:8000"]
    depends_on: [kafka, clickhouse, mongodb, redis]
```

### 2.3 Service Health Verification

```bash
# Check all services
docker-compose ps

# View logs for specific service
docker-compose logs -f kafka
docker-compose logs -f clickhouse

# Check specific service connectivity
# Kafka
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# ClickHouse
docker-compose exec clickhouse clickhouse-client --query "SELECT version()"

# MongoDB
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Redis
docker-compose exec redis redis-cli ping
# Output: PONG

# MQTT
docker-compose exec mosquitto mosquitto_sub -t '$SYS/broker/clients/active' -W 1
```

### 2.4 Development Utilities

```bash
# Start/stop services
docker-compose start kafka
docker-compose stop clickhouse
docker-compose restart redis

# Remove all data and start fresh
docker-compose down -v
docker-compose up -d

# View resource usage
docker stats

# Execute commands in containers
docker-compose exec kafka bash
docker-compose exec mongodb mongosh
docker-compose exec clickhouse clickhouse-client
```

---

## 3. Docker Container Deployment

### 3.1 Building Custom VertiFlow Image

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY cloud_citadel/ /app/cloud_citadel/
COPY scripts/ /app/scripts/
COPY config/ /app/config/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "cloud_citadel.nervous_system.nervous_system"]
```

**Build and run:**

```bash
# Build image
docker build -t vertiflow:latest .

# Tag for registry
docker tag vertiflow:latest your-registry/vertiflow:1.0.0

# Push to registry
docker push your-registry/vertiflow:1.0.0

# Run container
docker run -d \
  --name vertiflow-main \
  -p 8000:8000 \
  -e KAFKA_BROKERS=kafka:9092 \
  -e CLICKHOUSE_HOST=clickhouse \
  -e MONGODB_URI=mongodb://mongodb:27017 \
  your-registry/vertiflow:1.0.0
```

### 3.2 Multi-Stage Build (Production Optimized)

```dockerfile
# Dockerfile.prod - Optimized for production

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy only necessary packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY cloud_citadel/ ./cloud_citadel/
COPY config/ ./config/

# Non-root user
RUN useradd -m -u 1000 vertiflow
USER vertiflow

HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "cloud_citadel.nervous_system.nervous_system"]
```

---

## 4. Kubernetes Deployment

### 4.1 Kubernetes Architecture

```
┌─────────────────────────────────────────┐
│       Kubernetes Cluster (AWS/GCP)      │
├─────────────────────────────────────────┤
│  Namespace: vertiflow-prod              │
│                                         │
│  ┌─ Ingress (HTTPS)                    │
│  │                                      │
│  ├─ Deployment: vertiflow-api          │
│  │  └─ Replicas: 3 (HA)                │
│  │                                      │
│  ├─ StatefulSet: kafka                 │
│  │  └─ Replicas: 3                     │
│  │                                      │
│  ├─ StatefulSet: clickhouse            │
│  │  └─ Replicas: 1 (Keeper for HA)     │
│  │                                      │
│  ├─ Deployment: mongodb                │
│  │  └─ Replicas: 3 (ReplicaSet)        │
│  │                                      │
│  └─ ConfigMap & Secrets for config     │
│                                         │
│  PersistentVolumes:                     │
│  ├─ Kafka: 200GB                        │
│  ├─ ClickHouse: 500GB                   │
│  └─ MongoDB: 100GB                      │
└─────────────────────────────────────────┘
```

### 4.2 Kubernetes Manifests

**Namespace and RBAC:**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vertiflow-prod

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vertiflow-sa
  namespace: vertiflow-prod
```

**ConfigMap:**

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vertiflow-config
  namespace: vertiflow-prod
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  KAFKA_BROKERS: "kafka-0.kafka-headless.vertiflow-prod.svc.cluster.local:9092,kafka-1.kafka-headless.vertiflow-prod.svc.cluster.local:9092"
  CLICKHOUSE_HOST: "clickhouse.vertiflow-prod.svc.cluster.local"
  MONGODB_URI: "mongodb://mongodb-0.mongodb-headless.vertiflow-prod.svc.cluster.local:27017,mongodb-1.mongodb-headless.vertiflow-prod.svc.cluster.local:27017"
  REDIS_HOST: "redis.vertiflow-prod.svc.cluster.local"
```

**Secrets (for sensitive data):**

```bash
# Create secret from .env
kubectl create secret generic vertiflow-secrets \
  --from-env-file=.env \
  -n vertiflow-prod

# Or manually
kubectl create secret generic vertiflow-secrets \
  --from-literal=db-password='secure-password' \
  --from-literal=api-key='api-key-here' \
  -n vertiflow-prod
```

**Deployment:**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vertiflow-api
  namespace: vertiflow-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vertiflow-api
  template:
    metadata:
      labels:
        app: vertiflow-api
    spec:
      serviceAccountName: vertiflow-sa
      containers:
      - name: vertiflow
        image: your-registry/vertiflow:1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        
        # Environment from ConfigMap & Secrets
        envFrom:
        - configMapRef:
            name: vertiflow-config
        - secretRef:
            name: vertiflow-secrets
        
        # Resource limits
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 40
          periodSeconds: 10
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 5
        
        # Security
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
      
      # Pod disruption budget
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - vertiflow-api
              topologyKey: kubernetes.io/hostname
```

**Service:**

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: vertiflow-api
  namespace: vertiflow-prod
spec:
  selector:
    app: vertiflow-api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  type: LoadBalancer  # or ClusterIP with Ingress
```

**Deployment commands:**

```bash
# Create namespace
kubectl create namespace vertiflow-prod

# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check deployment status
kubectl get deployments -n vertiflow-prod
kubectl get pods -n vertiflow-prod
kubectl describe pod vertiflow-api-xxxxx -n vertiflow-prod

# View logs
kubectl logs -f deployment/vertiflow-api -n vertiflow-prod

# Scale deployment
kubectl scale deployment vertiflow-api --replicas=5 -n vertiflow-prod

# Rolling update
kubectl set image deployment/vertiflow-api \
  vertiflow=your-registry/vertiflow:1.1.0 \
  -n vertiflow-prod

# Rollback if needed
kubectl rollout undo deployment/vertiflow-api -n vertiflow-prod
```

---

## 5. Cloud Platform Deployment

### 5.1 AWS ECS Deployment

**Create ECS Cluster:**

```bash
# Create cluster
aws ecs create-cluster --cluster-name vertiflow-prod

# Create task definition
aws ecs register-task-definition \
  --family vertiflow-task \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 1024 \
  --memory 2048 \
  --container-definitions file://task-definition.json
```

**Task Definition (JSON):**

```json
{
  "family": "vertiflow-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "vertiflow",
      "image": "your-account.dkr.ecr.us-east-1.amazonaws.com/vertiflow:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:vertiflow-db-pass"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/vertiflow",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Create Service:**

```bash
aws ecs create-service \
  --cluster vertiflow-prod \
  --service-name vertiflow-api \
  --task-definition vertiflow-task:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/vertiflow/abc123,containerName=vertiflow,containerPort=8000"
```

### 5.2 AWS RDS for ClickHouse Alternative

```bash
# AWS supports ClickHouse managed service (in preview)
# Alternative: Use EC2 instance with RDS backup

# Or use ClickHouse Cloud (managed service)
# https://clickhouse.cloud

# Connection example:
CLICKHOUSE_HOST=xxx.clickhouse.cloud
CLICKHOUSE_PORT=9440
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=<from_cloud_console>
```

---

## 6. Database Initialization

### 6.1 ClickHouse Schema Creation

```bash
# Run initialization script
python scripts/init_clickhouse.py

# Or manually:
docker-compose exec clickhouse clickhouse-client << EOF

-- Create databases
CREATE DATABASE IF NOT EXISTS vertiflow;
CREATE DATABASE IF NOT EXISTS external;

-- Create tables (see docs/01_ARCHITECTURE.md)
CREATE TABLE vertiflow.telemetry (
  facility_id String,
  device_id String,
  measurement_date DateTime,
  temperature Float32,
  humidity Float32,
  ...
) ENGINE = MergeTree()
ORDER BY (facility_id, measurement_date)
PARTITION BY toYYYYMM(measurement_date);

EOF
```

**Complete schema migration:**

```bash
# From SQL file
cat config/schema/clickhouse/*.sql | \
  docker-compose exec -T clickhouse clickhouse-client

# Verify tables
docker-compose exec clickhouse clickhouse-client \
  --query "SHOW TABLES IN vertiflow"

# Check table structure
docker-compose exec clickhouse clickhouse-client \
  --query "DESCRIBE TABLE vertiflow.telemetry"
```

### 6.2 MongoDB Initialization

```bash
# Run seed script
python scripts/init_mongodb.py

# Or manually:
docker-compose exec mongodb mongosh << EOF

use vertiflow;

// Create collections with schema validation
db.createCollection("facilities", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["facility_id", "name"],
      properties: {
        facility_id: { bsonType: "string" },
        name: { bsonType: "string" },
        location: { bsonType: "object" }
      }
    }
  }
});

// Create indexes
db.facilities.createIndex({ facility_id: 1 }, { unique: true });
db.telemetry.createIndex({ facility_id: 1, timestamp: -1 });

EOF
```

### 6.3 Kafka Topic Creation

```bash
# Create topics
python scripts/init_kafka_topics.py

# Or manually:
docker-compose exec kafka kafka-topics \
  --create \
  --topic sensor-readings \
  --partitions 3 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092 \
  --config retention.ms=604800000

# List topics
docker-compose exec kafka kafka-topics \
  --list \
  --bootstrap-server localhost:9092

# Describe topic
docker-compose exec kafka kafka-topics \
  --describe \
  --topic sensor-readings \
  --bootstrap-server localhost:9092
```

---

## 7. Configuration Management

### 7.1 Environment Variables

**Development (.env):**

```bash
# Infrastructure
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Kafka
KAFKA_BROKERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# MongoDB
MONGODB_URI=mongodb://localhost:27017/vertiflow
MONGODB_TIMEOUT_MS=10000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# External APIs
NASA_POWER_API_KEY=demo  # For testing only
```

**Production (.env.prod):**

```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING

KAFKA_BROKERS=kafka-0:9092,kafka-1:9092,kafka-2:9092
KAFKA_SECURITY_PROTOCOL=SSL
KAFKA_SSL_CAFILE=/etc/kafka/secrets/ca-cert.pem

CLICKHOUSE_HOST=clickhouse-primary.internal
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=vertiflow_user
CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}

MONGODB_URI=mongodb+srv://${MONGO_USER}:${MONGO_PASSWORD}@mongodb-cluster.internal

REDIS_HOST=redis-primary.internal
REDIS_PASSWORD=${REDIS_PASSWORD}

API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=16

# Enable authentication
AUTH_ENABLED=true
JWT_SECRET=${JWT_SECRET}

# Enable monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

### 7.2 Secrets Management

**Using AWS Secrets Manager:**

```bash
# Store secret
aws secretsmanager create-secret \
  --name vertiflow/db-password \
  --secret-string 'supersecure-password'

# Retrieve secret
aws secretsmanager get-secret-value \
  --secret-id vertiflow/db-password \
  --query SecretString --output text

# Rotate secret
aws secretsmanager rotate-secret \
  --secret-id vertiflow/db-password \
  --rotation-rules AutomaticallyAfterDays=30
```

**Using HashiCorp Vault:**

```bash
# Authenticate
vault login -method=kubernetes

# Store secret
vault kv put secret/vertiflow/db \
  password="secure-password" \
  username="vertiflow_user"

# Retrieve secret
vault kv get secret/vertiflow/db

# Dynamic secrets for databases
vault write -f database/rotate-root/clickhouse
```

---

## 8. Service Connectivity Verification

### 8.1 Connectivity Test Script

```bash
# Run comprehensive validation
python scripts/validate_deployment.py

# Expected output:
# ✅ ClickHouse: OK (version 23.10.1.1)
# ✅ MongoDB: OK (replica set: rs0)
# ✅ Kafka: OK (3 brokers, 12 topics)
# ✅ Redis: OK (v7.2, memory: 1.5M)
# ✅ MQTT: OK (clients: 0, messages: 0)
# ✅ NiFi: OK (version 1.20.0)
# ✅ All external APIs: OK
# ✅ DNS resolution: OK
# ✅ Certificate validation: OK
# ========================
# DEPLOYMENT STATUS: READY
```

### 8.2 Individual Service Tests

```bash
# Kafka connectivity
docker-compose exec kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092

# ClickHouse connectivity
docker-compose exec clickhouse clickhouse-client \
  --query "SELECT version()"

# MongoDB connectivity
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Redis connectivity
docker-compose exec redis redis-cli ping

# MQTT connectivity
mosquitto_pub -h localhost -t "test/topic" -m "Hello"
mosquitto_sub -h localhost -t "test/topic" -W 1

# API health check
curl -X GET http://localhost:8000/health
```

---

## 9. Health Checks & Monitoring

### 9.1 Application Health Endpoints

**Health check endpoint:**

```python
# cloud_citadel/nervous_system/nervous_system.py

@app.get("/health")
async def health_check():
    """
    Basic liveness probe for Kubernetes
    Returns 200 if service is running
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@app.get("/ready")
async def readiness_check():
    """
    Readiness probe - checks all dependencies
    Returns 200 only if all services are accessible
    """
    checks = {
        "kafka": await check_kafka(),
        "clickhouse": await check_clickhouse(),
        "mongodb": await check_mongodb(),
        "redis": await check_redis(),
    }
    
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail="Service unavailable")
```

**Kubernetes probes:**

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 40
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 20
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### 9.2 Prometheus Metrics

```python
# cloud_citadel/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Counters
kafka_messages_processed = Counter(
    'kafka_messages_processed_total',
    'Total messages processed from Kafka',
    ['topic', 'status']
)

clickhouse_queries = Counter(
    'clickhouse_queries_total',
    'Total ClickHouse queries',
    ['query_type']
)

# Gauges
active_connections = Gauge(
    'active_connections',
    'Current active connections'
)

queue_depth = Gauge(
    'kafka_queue_depth',
    'Current Kafka queue depth',
    ['topic']
)

# Histograms
query_duration = Histogram(
    'query_duration_seconds',
    'Query duration in seconds',
    ['database']
)

photosynthesis_calculation_time = Histogram(
    'photosynthesis_calc_seconds',
    'Time to calculate photosynthesis rate',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)
```

### 9.3 Grafana Dashboards

**Dashboard JSON structure:**

```json
{
  "dashboard": {
    "title": "VertiFlow Operational Cockpit",
    "panels": [
      {
        "title": "Message Throughput (msg/sec)",
        "targets": [
          {
            "expr": "rate(kafka_messages_processed_total[1m])"
          }
        ]
      },
      {
        "title": "ClickHouse Query Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, query_duration_seconds)"
          }
        ]
      }
    ]
  }
}
```

---

## 10. Backup & Disaster Recovery

### 10.1 Backup Strategy

**ClickHouse Backup:**

```bash
# Using clickhouse-backup tool
docker-compose exec clickhouse clickhouse-backup create \
  --name backup_2026_01_03

# List backups
docker-compose exec clickhouse clickhouse-backup list

# Restore backup
docker-compose exec clickhouse clickhouse-backup restore \
  --name backup_2026_01_03
```

**MongoDB Backup:**

```bash
# Using mongodump
docker-compose exec mongodb mongodump \
  --out=/backup/mongo_$(date +%Y%m%d_%H%M%S)

# Restore
docker-compose exec mongodb mongorestore \
  /backup/mongo_20260103_100000
```

**Kafka Backup (logs are persisted):**

```bash
# Kafka logs are stored in Docker volumes
# Backup volumes
docker run --rm \
  -v vertiflow-kafka-data:/data \
  -v /backup:/backup \
  alpine tar czf /backup/kafka_backup.tar.gz /data
```

### 10.2 Automated Backup Schedule

**Cron job for daily backups:**

```bash
# /etc/cron.d/vertiflow-backup

0 2 * * * root /opt/vertiflow/scripts/backup.sh >> /var/log/vertiflow-backup.log 2>&1
0 3 * * 0 root /opt/vertiflow/scripts/backup.sh --full >> /var/log/vertiflow-backup.log 2>&1
```

**Backup script:**

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backup/vertiflow"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# ClickHouse backup
clickhouse-backup create --name "clickhouse_$DATE"

# MongoDB backup
mongodump --out="$BACKUP_DIR/mongodb_$DATE"

# Upload to S3
aws s3 sync $BACKUP_DIR s3://vertiflow-backups/ --delete

echo "Backup completed: $DATE"
```

### 10.3 Disaster Recovery Plan

**RTO/RPO Targets:**
```
- Recovery Time Objective (RTO): 4 hours
- Recovery Point Objective (RPO): 1 hour
- Backup retention: 30 days (production), 7 days (dev)
```

**Recovery procedure:**

```bash
# 1. Assess damage
docker-compose ps
kubectl get pods -n vertiflow-prod

# 2. Stop affected services
docker-compose stop <service>

# 3. Restore from backup
clickhouse-backup restore --name backup_YYYYMMDD_HHMMSS
mongorestore /backup/mongodb_YYYYMMDD_HHMMSS

# 4. Verify data integrity
python scripts/validate_deployment.py

# 5. Restart services
docker-compose up -d
kubectl rollout restart deployment/vertiflow-api

# 6. Monitor logs
docker-compose logs -f
kubectl logs -f deployment/vertiflow-api

# 7. Smoke tests
curl http://localhost:8000/health
pytest tests/smoke/
```

---

## 11. Troubleshooting

### 11.1 Common Issues

**Issue: "Kafka broker not available"**

```bash
# Check Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka

# Verify Zookeeper
docker-compose logs zookeeper

# Restart Kafka
docker-compose restart zookeeper kafka

# Wait for broker to be ready
docker-compose exec kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092
```

**Issue: "ClickHouse connection refused"**

```bash
# Check ClickHouse is running
docker-compose ps clickhouse

# Check port is listening
netstat -tlnp | grep 9000

# Test connection
clickhouse-client --host localhost --port 9000

# Check logs
docker-compose logs clickhouse
```

**Issue: "MongoDB replica set initialization"**

```bash
# Connect to MongoDB
docker-compose exec mongodb mongosh

# Initialize replica set
rs.initiate({
  _id: "rs0",
  members: [{_id: 0, host: "localhost:27017"}]
})

# Check status
rs.status()
```

### 11.2 Performance Tuning

**Kafka optimization:**

```properties
# config/kafka/server.properties
num.io.threads=16          # CPU cores
num.network.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
```

**ClickHouse optimization:**

```xml
<!-- config.xml -->
<clickhouse>
  <max_memory_usage>34359738368</max_memory_usage>  <!-- 32GB -->
  <max_concurrent_queries>100</max_concurrent_queries>
  <background_pool_size>32</background_pool_size>
</clickhouse>
```

**MongoDB optimization:**

```javascript
db.adminCommand({
  setParameter: 1,
  wiredTigerEngineRuntimeConfig: "cache_size=8G"
})
```

---

## Monitoring Checklist

```
☐ Kubernetes pod status (all running/ready)
☐ Service health endpoints (200 OK)
☐ Database connections (no errors)
☐ Message queue lag (< 1 hour)
☐ Storage utilization (< 80%)
☐ Memory usage (< 75%)
☐ CPU utilization (< 70%)
☐ Network bandwidth (< 80%)
☐ API latency (p95 < 200ms)
☐ Error rate (< 0.1%)
☐ Log files (no errors last 1h)
☐ Backup completeness (daily)
☐ SSL certificates (not expiring soon)
☐ Security patches (applied)
```

---

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/ecs/)
- [ClickHouse Deployment](https://clickhouse.com/docs/en/getting-started/install)
- [MongoDB Deployment](https://docs.mongodb.com/manual/deployment/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/)

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-03 | @Imrane, @MrZakaria | Initial creation |

---

**Document Footer**

```
TICKET: TICKET-118
ASSIGNED TO: @Imrane (DevOps Lead), @MrZakaria (Project Lead)
TEAM: @Imrane, @MrZakaria, @Mounir, @Mouhammed
PROJECT: VertiFlow Data Platform - Intelligent Vertical Farming
STATUS: Production Release
CLASSIFICATION: Technical - Internal
NEXT REVIEW: 2026-04-03 (Quarterly)
REPOSITORY: J-Mounir/test-projet-agri (GitHub)
```

---

*This document is controlled and subject to change management procedures.*
*Last updated: 2026-01-03 | Next scheduled review: 2026-04-03*
