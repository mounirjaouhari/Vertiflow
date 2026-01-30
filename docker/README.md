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

## Build multi-architecture

```bash
# Build pour AMD64 et ARM64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile.ml \
  -t vertiflow/ml:latest \
  --push .
```
