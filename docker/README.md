# Docker - Images personnalisees

Ce dossier contient les Dockerfiles personnalises pour VertiFlow.

## Structure

```
docker/
├── Dockerfile.ingestion             # Image d'ingestion de donnees
├── Dockerfile.ml                    # Image ML/Intelligence
└── Dockerfile.processor             # Image de traitement
```

## Images

### Dockerfile.ingestion
Image pour l'ingestion de donnees :
- Base: Python 3.11
- Packages: kafka-python, paho-mqtt, requests
- Usage: Connecteurs, simulateurs

```bash
docker build -f docker/Dockerfile.ingestion -t vertiflow/ingestion .
```

### Dockerfile.ml
Image pour le machine learning :
- Base: Python 3.11 + CUDA (optionnel)
- Packages: scikit-learn, tensorflow, pandas
- Usage: Entrainement et inference ML

```bash
docker build -f docker/Dockerfile.ml -t vertiflow/ml .
```

### Dockerfile.processor
Image pour le traitement de donnees :
- Base: Python 3.11
- Packages: kafka-python, clickhouse-driver
- Usage: ETL, transformations

```bash
docker build -f docker/Dockerfile.processor -t vertiflow/processor .
```

## Utilisation avec docker-compose

Les images sont referencees dans `docker-compose.yml` :

```yaml
services:
  ingestion:
    build:
      context: .
      dockerfile: docker/Dockerfile.ingestion
    # ...
```

## Services ML (docker-compose.yml)

Les services ML sont definis directement dans `docker-compose.yml` :

| Service | Container | Script | Description |
|---------|-----------|--------|-------------|
| `ml-engine` | ml_engine | oracle.py | Prediction de rendement (A9), cycle 5min |
| `ml-classifier` | ml_classifier | classifier.py | Classification qualite (A10), ecoute Kafka |
| `ml-cortex` | ml_cortex | cortex.py | Optimisation recettes (A11), cycle 24h |

### Demarrage des services ML

```bash
# Demarrer tous les services ML
docker compose up -d ml-engine ml-classifier ml-cortex

# Verifier les logs
docker logs ml_engine --tail 20
docker logs ml_classifier --tail 20
docker logs ml_cortex --tail 20

# Redemarrer un service specifique
docker compose restart ml-engine
```

### Variables d'environnement ML

```yaml
environment:
  - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
  - CLICKHOUSE_HOST=clickhouse
  - CLICKHOUSE_PORT=9000
  - MONGODB_HOST=mongodb
  - MONGODB_URI=mongodb://mongodb:27017/
```

## Build multi-architecture

```bash
# Build pour AMD64 et ARM64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile.ml \
  -t vertiflow/ml:latest \
  --push .
```
