# Scripts - VertiFlow Data Platform

Ce dossier contient tous les scripts d'automatisation de la plateforme VertiFlow.

## Vue d'ensemble

```
scripts/
├── data_sources/          # Recuperation donnees externes (APIs, scrapers)
├── etl/                   # Pipelines de transformation (Kafka -> ClickHouse)
├── health/                # Verification de sante des services
├── init/                  # Initialisation infrastructure (DB, topics)
├── mapping/               # Mapping des 156 colonnes
├── nifi_workflows/        # Deploiement pipelines NiFi
├── simulators/            # Generateurs de donnees IoT
└── utils/                 # Utilitaires (validation, catalogue)
```

## Modules

| Dossier | Description | Scripts principaux |
|---------|-------------|--------------------|
| [data_sources/](data_sources/) | APIs et scrapers de donnees externes | `fetch_all_external_data.py`, `download_all_sources.sh` |
| [etl/](etl/) | Transformation et chargement | `transform_telemetry.py`, `aggregate_metrics.py` |
| [health/](health/) | Monitoring infrastructure | `health_check.py` |
| [init/](init/) | Bootstrap des services | `init_clickhouse.py`, `init_kafka_topics.py` |
| [mapping/](mapping/) | Documentation colonnes | `mapping_156_parameters.py` |
| [nifi_workflows/](nifi_workflows/) | Deploiement NiFi | `deploy/deploy_pipeline_v2_full.py` |
| [simulators/](simulators/) | Generation donnees test | `run_all_simulators.py` |
| [utils/](utils/) | Outils divers | `validate_deployment.py` |

## Demarrage rapide

### 1. Initialisation de l'infrastructure
```bash
# Demarrer les services Docker
make compose-up

# Initialiser ClickHouse
python scripts/init/init_clickhouse.py

# Creer les topics Kafka
python scripts/init/init_kafka_topics.py

# Seeder MongoDB
python scripts/init/init_mongodb.py
```

### 2. Deploiement du pipeline NiFi
```bash
# Deployer le pipeline complet (v2)
python scripts/nifi_workflows/deploy/deploy_pipeline_v2_full.py

# Activer les processeurs
python scripts/nifi_workflows/utils/activate_pipeline.py
```

### 3. Recuperation des donnees externes
```bash
# Toutes les sources
python scripts/data_sources/fetch_all_external_data.py

# Par categorie
python scripts/data_sources/fetch_all_external_data.py --category weather
```

### 4. Lancer les simulateurs
```bash
# Tous les simulateurs
python scripts/simulators/run_all_simulators.py

# Un simulateur specifique
python scripts/simulators/iot_sensor_simulator.py
```

### 5. Verification
```bash
# Health check
python scripts/health/health_check.py

# Validation complete
python scripts/utils/validate_deployment.py
```

## Architecture des flux

```
[IoT Sensors]     [External APIs]
      |                  |
      v                  v
[Mosquitto MQTT]  [NiFi GetHTTP]
      |                  |
      +--------+---------+
               |
               v
    [NiFi - Zone 1: Validation]
               |
               v
    [NiFi - Zone 2: Enrichissement]
               |
               v
    [Kafka: telemetry.enriched]
               |
    +----------+----------+
    |                     |
    v                     v
[ClickHouse]         [MongoDB]
(Time-series)        (Recipes)
    |                     |
    +----------+----------+
               |
               v
    [Power BI / Grafana]
```

## Variables d'environnement

Voir le fichier `.env.example` pour la liste complete. Variables principales :

| Variable | Description |
|----------|-------------|
| `CLICKHOUSE_HOST` | Hote ClickHouse |
| `KAFKA_BOOTSTRAP` | Serveurs Kafka |
| `MONGODB_URI` | URI MongoDB |
| `NIFI_BASE_URL` | URL API NiFi |
| `MQTT_BROKER` | Broker Mosquitto |

## Makefile

```bash
make help              # Afficher toutes les commandes
make install           # Installer les dependances
make simulators        # Lancer les simulateurs
make etl-transform     # Transformer la telemetrie
make etl-external      # Charger les donnees externes
make validate          # Valider le deploiement
```

## Equipe

| Membre | Role | Modules |
|--------|------|---------|
| @Mounir | Architecte | Cloud Citadel, ML |
| @Imrane | DevOps | Init, NiFi, Health |
| @Mouhammed | Data Engineer | ETL, Data Sources |
| @Asama | Biologiste | Simulators, Mapping |
| @MrZakaria | Encadrant | Supervision |
