# Decisions d'Architecture - VertiFlow

Ce document centralise les decisions architecturales du projet pour assurer la coherence.

## Date: 2026-01-11
## Version: 1.0

---

## 1. Sources de Verite (Single Source of Truth)

### 1.1 Configuration
| Domaine | Fichier Unique | Localisation |
|---------|----------------|--------------|
| Parametres agronomiques | `agronomic_parameters.yaml` | `config/` |
| Configuration MQTT | `mosquitto.conf` | `config/mosquitto/` |
| Mapping colonnes | `mapping.json` | `config/` |
| Variables environnement | `.env.example` | Racine (template) |

### 1.2 Schemas
| Schema | Fichier Unique | Usage |
|--------|----------------|-------|
| Telemetrie v3 | `telemetry_v3_complete.json` | `docs/schemas/` |
| Commandes v3 | `command_v3.json` | `docs/schemas/` |

### 1.3 Images/Assets
Toutes les images sont dans `images/` uniquement.

---

## 2. Stack Technologique

### 2.1 Bases de Donnees UTILISEES
| Technologie | Usage | Port |
|-------------|-------|------|
| **ClickHouse** | Time-series OLAP | 9000, 8123 |
| **MongoDB** | Documents (recettes, config) | 27017 |
| **Kafka** | Event streaming | 9092 |

### 2.2 NON UTILISE (Commente)
| Technologie | Raison |
|-------------|--------|
| ~~TimescaleDB~~ | ClickHouse couvre le besoin time-series |
| ~~PostgreSQL~~ | MongoDB couvre le besoin documents |

---

## 3. Topics Kafka (Standardises)

### 3.1 Topics ACTIFS (utilises dans le code)
```
basil_telemetry_full             # Donnees brutes capteurs (6 partitions)
vertiflow.commands               # Commandes actuateurs (3 partitions)
vertiflow.alerts                 # Alertes systeme (3 partitions)
dead_letter_queue                # Messages invalides DLQ (1 partition)
vertiflow.quality_predictions    # Predictions A10 (3 partitions)
vertiflow.recipe_updates         # Optimisations A11 (1 partition)
```

### 3.2 Source de verite
Voir `config/vertiflow_constants.py` - classe `KafkaTopics`

### 3.3 Topics futurs (migration planifiee)
```
vertiflow.telemetry.raw          # Remplacera basil_telemetry_full
vertiflow.telemetry.enriched     # Donnees transformees
vertiflow.telemetry.deadletter   # Remplacera dead_letter_queue
```

---

## 4. Scripts d'Initialisation

### 4.1 Point d'entree unique
```bash
python infrastructure/init_infrastructure.py
```

Ce script :
1. Verifie les services (ClickHouse, MongoDB, Kafka)
2. Cree la base ClickHouse
3. Cree les topics Kafka
4. Seed MongoDB

### 4.2 Scripts specialises (optionnels)
Les scripts dans `scripts/init/` peuvent etre utilises individuellement :
```bash
python scripts/init/init_clickhouse.py    # Schema detaille
python scripts/init/init_kafka_topics.py  # Topics supplementaires
python scripts/init/init_mongodb.py       # Seed complet
```

---

## 5. Colonnes ClickHouse

### Decision: 156 colonnes
Le schema officiel comporte **156 colonnes** (pas 153).

Reference: `docs/CLICKHOUSE_COLUMN_DICTIONARY.md`

---

## 6. Conventions de Nommage

### 6.1 Dossiers
- Format: `snake_case`
- Exemples: `cloud_citadel`, `nifi_exchange`, `data_sources`

### 6.2 Fichiers Python
- Format: `snake_case.py`
- Exemples: `init_clickhouse.py`, `transform_telemetry.py`

### 6.3 Fichiers de configuration
- Format: `snake_case.yaml` ou `snake_case.json`
- Exemples: `agronomic_parameters.yaml`, `mapping.json`

### 6.4 Documentation
- Format: `UPPER_CASE.md` ou `Title_Case.md`
- Numerotation: `01_`, `02_`, `03_`...

---

## 7. Securite

### 7.1 Fichiers sensibles (JAMAIS dans Git)
```
.env
.env.local
.env.development
.env.production
*.pem
*.key
config/mosquitto/passwords
```

### 7.2 Templates (dans Git)
```
.env.example
config/mosquitto/passwords.example
```

---

## 8. Structure des Dossiers

```
vertiflow/
├── bibliography/        # References scientifiques
├── cloud_citadel/       # ML/AI (utilise config/ pour params)
├── config/              # SOURCE DE VERITE configuration
├── dashboards/          # Visualisation
├── datasets/            # Donnees de recherche
├── docs/                # Documentation
├── drivers/             # JDBC drivers
├── images/              # SOURCE DE VERITE images
├── infrastructure/      # Scripts SQL/JS init
├── models/              # Entrainement ML
├── monitoring/          # Prometheus/Alertmanager
├── scripts/             # Automatisation
├── security/            # Config securite
└── tests/               # Tests automatises
```

---

## 9. Flux de Donnees Complet

### 9.1 Pipeline End-to-End
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     VERTIFLOW DATA PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [1] IoT Sensors                                                        │
│      scripts/simulators/iot_sensor_simulator.py                         │
│      ↓ MQTT (vertiflow/telemetry/#)                                     │
│                                                                          │
│  [2] Mosquitto Broker (port 1883)                                       │
│      ↓                                                                   │
│                                                                          │
│  [3] Apache NiFi (port 8443)                                            │
│      scripts/nifi_workflows/deploy/deploy_pipeline_v2_full.py           │
│      - Validation JSON Schema                                            │
│      - Enrichissement (zone, cultivar)                                   │
│      - Calculs derives (VPD, dew point)                                  │
│      ↓ Kafka                                                             │
│                                                                          │
│  [4] Kafka Topic: basil_telemetry_full                                  │
│      ↓                                                                   │
│                                                                          │
│  [5] ETL Transformer                                                     │
│      scripts/etl/transform_telemetry.py                                  │
│      - Normalisation unites                                              │
│      - Batch insert (500 rows / 5s)                                      │
│      ↓                                                                   │
│                                                                          │
│  [6] ClickHouse                                                          │
│      Table: vertiflow.basil_ultimate_realtime (153 colonnes)            │
│      ↓                                                                   │
│                                                                          │
│  [7] ML Algorithms                                                       │
│      cloud_citadel/nervous_system/oracle.py    (A9 - Prediction)        │
│      cloud_citadel/nervous_system/classifier.py (A10 - Qualite)         │
│      cloud_citadel/nervous_system/cortex.py    (A11 - Optimisation)     │
│      ↓                                                                   │
│                                                                          │
│  [8] MongoDB: vertiflow_ops                                              │
│      Collections: plant_recipes, quality_predictions, live_state        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Point d'Entree Unifie
```bash
# Demarrer tout le systeme
python scripts/start_vertiflow.py

# Ou etape par etape:
docker compose up -d                                          # Services
python infrastructure/init_infrastructure.py                  # Init DB/Kafka
python scripts/nifi_workflows/deploy/deploy_pipeline_v2_full.py  # NiFi
python scripts/simulators/iot_sensor_simulator.py            # Simulator
python scripts/etl/transform_telemetry.py                    # ETL
```

---

## 10. Historique des Decisions

| Date | Decision | Responsable |
|------|----------|-------------|
| 2026-01-11 | Suppression TimescaleDB | @Imrane |
| 2026-01-11 | Centralisation config dans `config/` | @Mouhammed |
| 2026-01-11 | Standardisation topics Kafka | @Mouhammed |
| 2026-01-11 | 153 colonnes + 3 ALTER = 156 officielles | @Mounir |
| 2026-01-11 | Creation point entree unifie start_vertiflow.py | @Claude |
| 2026-01-11 | Correction references tables dans ML scripts | @Claude |
