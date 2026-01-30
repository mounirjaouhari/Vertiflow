# Config - Configuration du systeme

Ce dossier contient tous les fichiers de configuration de VertiFlow.

## Structure

```
config/
├── agronomic_parameters.yaml        # Parametres biologiques (35 cultures)
├── external_data_sources.yaml       # Sources de donnees externes
├── mapping.json                     # Mapping des 156 colonnes
├── mosquitto.conf                   # Configuration MQTT
├── nifi_pipeline_dev.yaml           # Pipeline NiFi (dev)
├── nifi_pipeline_prod.yaml          # Pipeline NiFi (prod)
├── prometheus.yml                   # Configuration Prometheus
├── vertiflow_constants.py           # Constantes Python
├── environments/                    # Variables par environnement
│   ├── .env.development
│   └── .env.production
└── mosquitto/                       # Config Mosquitto detaillee
    ├── acls
    ├── mosquitto.conf
    └── passwords
```

## Fichiers principaux

### agronomic_parameters.yaml
Parametres agronomiques pour 35 cultures :
- Plages optimales (temperature, EC, pH, DLI)
- Coefficients de culture (Kc)
- Durees de cycle

### external_data_sources.yaml
Configuration des sources de donnees externes :
- NASA POWER
- Open-Meteo
- OpenAg Foundation
- Wageningen Research

### mapping.json
Mapping des colonnes ClickHouse :
- 156 colonnes documentees
- Types de donnees
- Unites et plages valides

### nifi_pipeline_*.yaml
Configuration des pipelines NiFi :
- `dev`: Schema simplifie, DLQ basique
- `prod`: Governance complete, 3-tier DLQ

## Variables d'environnement

### .env.development
```bash
CLICKHOUSE_HOST=localhost
KAFKA_BOOTSTRAP=localhost:9092
NIFI_BASE_URL=https://localhost:8443/nifi-api
LOG_LEVEL=DEBUG
```

### .env.production
```bash
CLICKHOUSE_HOST=clickhouse.vertiflow.local
KAFKA_BOOTSTRAP=kafka1:9092,kafka2:9092,kafka3:9092
NIFI_BASE_URL=https://nifi.vertiflow.local/nifi-api
LOG_LEVEL=INFO
```

## Utilisation

```python
import yaml

# Charger les parametres agronomiques
with open("config/agronomic_parameters.yaml") as f:
    params = yaml.safe_load(f)

basil_config = params["crops"]["basil"]
optimal_temp = basil_config["temperature"]["optimal"]
```
