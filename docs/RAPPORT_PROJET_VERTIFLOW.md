# RAPPORT TECHNIQUE - PROJET VERTIFLOW
## Plateforme de Donnees pour l'Agriculture Verticale Intelligente

---

**Document a destination de**: Mr. Zakaria (Encadrant & Architecte Data)
**Redige par**: VertiFlow Core Team
**Date**: Janvier 2026
**Version**: 1.0

---

## Table des Matieres

1. [Vision et Objectifs du Projet](#1-vision-et-objectifs-du-projet)
2. [Architecture Globale](#2-architecture-globale)
3. [Pipeline de Donnees NiFi](#3-pipeline-de-donnees-nifi)
4. [Integration du Machine Learning](#4-integration-du-machine-learning)
5. [Stack Technologique](#5-stack-technologique)
6. [Diagrammes d'Orchestration](#6-diagrammes-dorchestration)
7. [Etat Actuel et Prochaines Etapes](#7-etat-actuel-et-prochaines-etapes)

---

## 1. Vision et Objectifs du Projet

### 1.1 Vision

VertiFlow est une **plateforme de donnees industrielle** concue pour revolutionner l'agriculture verticale au Maroc. Le projet vise a creer un systeme autonome capable de:

- **Collecter** des donnees en temps reel depuis des capteurs IoT (temperature, humidite, lumiere, CO2, pH, etc.)
- **Analyser** ces donnees via des algorithmes scientifiques valides
- **Predire** les rendements et la qualite des recoltes grace au Machine Learning
- **Optimiser** automatiquement les conditions de culture pour maximiser la productivite

### 1.2 Objectifs Strategiques

| Objectif | Description | KPI Cible |
|----------|-------------|-----------|
| **Temps Reel** | Ingestion et traitement des donnees < 100ms | Latence P50 < 100ms |
| **Precision ML** | Predictions de rendement fiables | R² > 0.92 |
| **Scalabilite** | Support de milliers de capteurs | 100K events/sec |
| **Autonomie** | Optimisation automatique des cultures | 24/7 sans intervention |
| **Tracabilite** | Gouvernance complete des donnees | 100% auditable |

### 1.3 Contexte Marocain

Ce projet s'inscrit dans le cadre de l'**Initiative Nationale Marocaine JobInTech** a l'Ecole YNOV Maroc Campus. Il repond aux defis de:

- Securite alimentaire nationale
- Optimisation des ressources en eau (stress hydrique)
- Modernisation de l'agriculture marocaine
- Formation aux technologies de pointe (Big Data, ML, IoT)

---

## 2. Architecture Globale

### 2.1 Architecture en 7 Couches

Le systeme VertiFlow suit une architecture en couches, depuis les capteurs physiques jusqu'a la visualisation:

```mermaid
---
config:
  layout: elk
---
graph TB
    subgraph "COUCHE 1: PHYSIQUE (IoT)"
        S1[Capteurs Temperature]
        S2[Capteurs Humidite]
        S3[Capteurs Lumiere PPFD]
        S4[Capteurs CO2]
        S5[Capteurs pH/EC]
    end

    subgraph "COUCHE 2: INGESTION"
        MQTT[Mosquitto MQTT Broker]
        NIFI[Apache NiFi Pipeline]
        HTTP[API REST HTTP]
    end

    subgraph "COUCHE 3: STREAMING"
        KAFKA[Apache Kafka]
        T1[basil_telemetry_full]
        T2[vertiflow.commands]
        T3[vertiflow.alerts]
        T4[dead_letter_queue]
    end

    subgraph "COUCHE 4: STOCKAGE"
        CH[(ClickHouse - Time Series)]
        MONGO[(MongoDB - Documents)]
    end

    subgraph "COUCHE 5: INTELLIGENCE ML"
        A9[Oracle A9 - Prediction Rendement]
        A10[Classifier A10 - Qualite]
        A11[Cortex A11 - Optimisation]
    end

    subgraph "COUCHE 6: RETROACTION"
        FB[Feedback Loop Manager]
        CMD[Command Publisher]
    end

    subgraph "COUCHE 7: VISUALISATION"
        PBI[Power BI Dashboards]
        GRAF[Grafana Metrics]
    end

    S1 & S2 & S3 & S4 & S5 --> MQTT
    MQTT --> NIFI
    HTTP --> NIFI
    NIFI --> KAFKA
    KAFKA --> T1 & T2 & T3 & T4
    T1 --> CH
    T1 --> A9 & A10
    A9 & A10 --> A11
    A11 --> MONGO
    A11 --> CMD
    CMD --> T2
    CH --> FB
    FB --> A9
    CH --> PBI
    CH --> GRAF
```

### 2.2 Golden Record - Schema 153 Colonnes

Toutes les donnees convergent vers une **table principale** dans ClickHouse: `basil_ultimate_realtime`

Cette table contient **153 colonnes** couvrant:
- Donnees environnementales (temperature, humidite, CO2, VPD)
- Donnees nutritives (pH, EC, concentrations NPK)
- Donnees lumineuses (PPFD, DLI, spectre)
- Donnees calculees (photosynthese, transpiration)
- Metadonnees (zone, rack, batch, timestamps)

---

## 3. Pipeline de Donnees NiFi

### 3.1 Architecture du Pipeline

Le pipeline NiFi est organise en **6 zones fonctionnelles** + une Dead Letter Queue:

```mermaid
flowchart LR
    subgraph "ZONE 0: External APIs"
        API1[Open-Meteo]
        API2[NASA POWER]
        API3[OpenAQ]
    end

    subgraph "ZONE 1: Ingestion"
        HTTP[ListenHTTP:8080]
        MQTT[ConsumeMQTT]
        FILE[GetFile]
        VAL[ValidateRecord]
    end

    subgraph "ZONE 2: Contextualisation"
        LOOKUP[LookupRecord MongoDB]
        VPD[ExecuteScript VPD]
        JOLT[JoltTransformJSON]
    end

    subgraph "ZONE 3: Persistance"
        CH_PUT[PutDatabaseRecord ClickHouse]
        MONGO_PUT[PutMongo]
        ARCHIVE[PutFile Archive]
    end

    subgraph "ZONE 4: Retroaction"
        QUERY[QueryRecord Anomalies]
        PUB[PublishMQTT Commandes]
    end

    subgraph "ZONE 5: Static Data"
        CSV[CSV Datasets]
        LAB[Lab Data]
        REC[Plant Recipes]
    end

    subgraph "DLQ: Dead Letter Queue"
        DLQ[Error Handler]
        RETRY[Retry Logic]
    end

    API1 & API2 & API3 --> VAL
    HTTP & MQTT & FILE --> VAL
    VAL -->|Valid| LOOKUP
    VAL -->|Invalid| DLQ
    LOOKUP --> VPD
    VPD --> JOLT
    JOLT --> CH_PUT & MONGO_PUT & ARCHIVE
    CH_PUT --> QUERY
    QUERY -->|Anomalie| PUB
    CSV & LAB & REC --> JOLT
    DLQ --> RETRY
    RETRY -->|3x| VAL
```

### 3.2 Protocole Vance (Gouvernance)

Chaque FlowFile traverse un processus de **validation zero-trust**:

1. **Validation Schema** - Conformite JSON Schema
2. **Validation Range** - Valeurs dans les bornes biologiques
3. **Enrichissement** - Ajout des metadonnees de gouvernance
4. **Estampillage** - Timestamp de traitement + checksum
5. **Routage** - Vers persistance ou DLQ

### 3.3 Scripts de Deploiement

| Script | Fonction |
|--------|----------|
| `deploy_pipeline_v2_full.py` | Deploiement complet (6 zones + DLQ) |
| `fix_invalid_processors.py` | Correction automatique des erreurs |
| `fix_queryrecord_vpd.py` | Correction des noms de colonnes SQL |
| `nifi_health_check.py` | Diagnostic de sante du pipeline |

---

## 4. Integration du Machine Learning

### 4.1 Les 11 Algorithmes Scientifiques

Le projet implemente **11 algorithmes** (A1-A11) repartis en 3 categories:

```mermaid
graph TB
    subgraph "ALGORITHMES DE TRAITEMENT (A1-A8)"
        A1[A1: Normalisation JSON]
        A2[A2: Detection Outliers Z-Score]
        A3[A3: Enrichissement Contextuel]
        A4[A4: Seuillage Dynamique]
        A5[A5: Moteur de Regles]
        A6[A6: Agregation Temporelle]
        A7[A7: Correlation Pearson]
        A8[A8: Segmentation ANOVA]
    end

    subgraph "ALGORITHMES ML (A9-A11)"
        A9[A9: Oracle - Random Forest<br/>Prediction Rendement]
        A10[A10: Classifier - Random Forest<br/>Classification Qualite]
        A11[A11: Cortex - Scipy Optimize<br/>Optimisation Recettes]
    end

    A1 --> A2 --> A3 --> A4
    A4 --> A5 --> A6 --> A7 --> A8
    A8 --> A9
    A8 --> A10
    A9 & A10 --> A11
```

### 4.2 Oracle (A9) - Prediction de Rendement

**Fichier**: `cloud_citadel/nervous_system/oracle.py`

| Caracteristique | Valeur |
|-----------------|--------|
| **Algorithme** | Random Forest Regressor |
| **Librairie** | scikit-learn |
| **Features** | 5 dimensions (temp, PAR, humidite, CO2, stddev) |
| **Sortie** | Rendement predit (g/m²) + Score de confiance |
| **Frequence** | Toutes les 5 minutes par zone |

```mermaid
sequenceDiagram
    participant CH as ClickHouse
    participant O as Oracle A9
    participant P as Predictions Table

    loop Toutes les 5 minutes
        O->>CH: SELECT features 24h (zone)
        CH-->>O: temp_mean, par_mean, humidity...
        O->>O: model.predict(features)
        O->>P: INSERT prediction, confidence
        Note over O,P: Rendement predit + confiance
    end
```

### 4.3 Classifier (A10) - Classification Qualite

**Fichier**: `cloud_citadel/nervous_system/classifier.py`

| Caracteristique | Valeur |
|-----------------|--------|
| **Algorithme** | Random Forest Classifier |
| **Classes** | PREMIUM, STANDARD, REJECT |
| **Source** | Topic Kafka `basil_telemetry_full` |
| **Sortie** | Topic Kafka `vertiflow.quality_predictions` |
| **Mode** | Streaming temps reel |

```mermaid
sequenceDiagram
    participant K1 as Kafka (telemetry)
    participant C as Classifier A10
    participant K2 as Kafka (predictions)

    loop Streaming continu
        K1->>C: Message telemetrie
        C->>C: Extraction features (temp, VPD, DLI, EC)
        C->>C: model.predict() ou mock_predict()
        C->>K2: {grade: PREMIUM/STANDARD/REJECT}
    end
```

### 4.4 Cortex (A11) - Optimisation des Recettes

**Fichier**: `cloud_citadel/nervous_system/cortex.py`

| Caracteristique | Valeur |
|-----------------|--------|
| **Algorithme** | Minimisation L-BFGS-B (scipy.optimize) |
| **Objectif** | Maximiser (Yield × Quality - Cost) |
| **Variables** | Temperature, EC, DLI |
| **Contraintes** | Bornes biologiques |
| **Frequence** | Cycle 24h |

```mermaid
sequenceDiagram
    participant CH as ClickHouse
    participant CX as Cortex A11
    participant MG as MongoDB (recipes)
    participant K as Kafka (commands)

    CX->>CH: Fetch performance 30 jours
    CH-->>CX: avg_biomass, avg_oil, efficiency
    CX->>CX: scipy.optimize.minimize()
    CX->>MG: Update recipe targets
    CX->>K: Publish new commands
    Note over CX: Cycle toutes les 24h
```

### 4.5 Feedback Loop - Apprentissage Continu

**Fichier**: `cloud_citadel/connectors/feedback_loop.py`

Le systeme apprend de ses erreurs via une boucle de retroaction:

```mermaid
flowchart LR
    PRED[Predictions Oracle]
    ACTUAL[Resultats Reels]
    COMPARE[Comparaison RMSE/MAE]
    DRIFT{Drift Detecte?}
    RETRAIN[Retraining Model]
    DEPLOY[Deploiement A/B]

    PRED --> COMPARE
    ACTUAL --> COMPARE
    COMPARE --> DRIFT
    DRIFT -->|Oui| RETRAIN
    DRIFT -->|Non| PRED
    RETRAIN --> DEPLOY
    DEPLOY --> PRED
```

---

## 5. Stack Technologique

### 5.1 Vue d'Ensemble

```mermaid
graph TB
    subgraph "INGESTION"
        MQTT[Mosquitto MQTT<br/>IoT Gateway]
        NIFI[Apache NiFi<br/>Orchestration ETL]
    end

    subgraph "STREAMING"
        KAFKA[Apache Kafka<br/>Event Backbone]
        ZK[Zookeeper<br/>Coordination]
    end

    subgraph "STOCKAGE"
        CH[(ClickHouse<br/>OLAP Time-Series)]
        MG[(MongoDB<br/>Documents JSON)]
    end

    subgraph "COMPUTE ML"
        PY[Python 3.11+]
        SK[scikit-learn<br/>Random Forest]
        SP[scipy<br/>Optimization]
        PD[pandas/numpy<br/>Data Processing]
    end

    subgraph "VISUALISATION"
        PBI[Power BI<br/>11 Dashboards]
        GRAF[Grafana<br/>Metriques Temps Reel]
    end

    subgraph "INFRASTRUCTURE"
        DOCKER[Docker<br/>Containerisation]
        PROM[Prometheus<br/>Monitoring]
    end

    MQTT --> NIFI
    NIFI --> KAFKA
    KAFKA --> CH & MG
    CH --> PY
    PY --> SK & SP & PD
    CH --> PBI & GRAF
    DOCKER --> MQTT & NIFI & KAFKA & CH & MG
    PROM --> GRAF
```

### 5.2 Configuration Centralisee

Toute la configuration est centralisee dans **`config/vertiflow_constants.py`**:

| Classe | Contenu |
|--------|---------|
| `KafkaTopics` | Noms des topics Kafka |
| `ClickHouseTables` | Tables et vues ClickHouse |
| `MongoDBCollections` | Collections MongoDB |
| `Infrastructure` | Hosts, ports, URIs |
| `Algorithms` | Identifiants A1-A11 |
| `FarmConfig` | Zones, racks, farm_id |

Cette approche garantit la **coherence** entre tous les modules du projet.

---

## 6. Diagrammes d'Orchestration

### 6.1 Flux de Donnees Complet

```mermaid
flowchart TB
    subgraph "SOURCES"
        IOT[Capteurs IoT<br/>MQTT]
        EXT[APIs Externes<br/>NASA/Meteo]
        CSV[Datasets CSV<br/>Historiques]
    end

    subgraph "INGESTION NiFi"
        direction TB
        CONS[ConsumeMQTT]
        FETCH[InvokeHTTP]
        READ[GetFile]
        VALID[ValidateRecord<br/>Schema JSON]
        ENRICH[Enrichissement<br/>VPD/DLI Calculs]
    end

    subgraph "MESSAGE BUS"
        K1[basil_telemetry_full<br/>Telemetrie complete]
        K2[vertiflow.commands<br/>Commandes actionneurs]
        K3[vertiflow.alerts<br/>Alertes prioritaires]
        K4[dead_letter_queue<br/>Erreurs]
    end

    subgraph "PERSISTANCE"
        CH_RT[(basil_ultimate_realtime<br/>153 colonnes)]
        CH_PRED[(predictions<br/>ML outputs)]
        MG_REC[(plant_recipes<br/>Recettes culture)]
        MG_LOG[(incident_logs<br/>Audit trail)]
    end

    subgraph "INTELLIGENCE"
        A9[Oracle A9<br/>Random Forest]
        A10[Classifier A10<br/>Quality Grading]
        A11[Cortex A11<br/>Scipy Optimize]
    end

    subgraph "VISUALISATION"
        V1[Operational Cockpit]
        V2[Science Lab]
        V3[Executive Finance]
        V4[Anomalies Log]
    end

    IOT --> CONS
    EXT --> FETCH
    CSV --> READ
    CONS & FETCH & READ --> VALID
    VALID -->|OK| ENRICH
    VALID -->|KO| K4
    ENRICH --> K1

    K1 --> CH_RT
    K1 --> A9 & A10

    A9 --> CH_PRED
    A10 --> A11
    A11 --> MG_REC
    A11 --> K2

    K2 --> IOT
    K3 --> MG_LOG

    CH_RT --> V1 & V2 & V3 & V4
```

### 6.2 Cycle de Vie d'une Mesure

```mermaid
sequenceDiagram
    participant S as Capteur IoT
    participant M as Mosquitto MQTT
    participant N as Apache NiFi
    participant K as Apache Kafka
    participant C as ClickHouse
    participant O as Oracle ML
    participant P as Power BI

    S->>M: Publish temperature=24.5C
    M->>N: Message MQTT
    N->>N: Validation Schema
    N->>N: Calcul VPD, DLI
    N->>K: Produce to basil_telemetry_full
    K->>C: INSERT INTO basil_ultimate_realtime
    K->>O: Consume for prediction
    O->>O: Extract features (24h)
    O->>O: model.predict()
    O->>C: INSERT INTO predictions
    C->>P: Refresh Dashboard
    Note over S,P: Latence totale < 100ms
```

### 6.3 Architecture de Deploiement

```mermaid
graph TB
    subgraph "DOCKER COMPOSE"
        direction TB
        C1[mosquitto:1883<br/>MQTT Broker]
        C2[kafka:9092<br/>+ Zookeeper:2181]
        C3[clickhouse:8123/9000<br/>Analytics DB]
        C4[mongodb:27017<br/>Document Store]
        C5[nifi:8443<br/>Pipeline UI]
        C6[grafana:3000<br/>Monitoring]
        C7[prometheus:9090<br/>Metrics]
    end

    subgraph "PYTHON SERVICES"
        S1[stream_processor.py<br/>Kafka Consumer]
        S2[oracle.py<br/>ML Predictions]
        S3[classifier.py<br/>Quality Grading]
        S4[cortex.py<br/>Optimization]
        S5[feedback_loop.py<br/>Model Learning]
    end

    subgraph "VOLUMES"
        V1[nifi_exchange/<br/>Input/Output]
        V2[models/<br/>ML Artifacts]
        V3[data/<br/>Datasets]
    end

    C1 --> C5
    C5 --> C2
    C2 --> C3 & C4
    C3 --> S1 & S2 & S3 & S4
    S2 & S3 --> S4
    S4 --> C4
    C3 --> C6
    C7 --> C6

    V1 --> C5
    V2 --> S2 & S3
    V3 --> C5
```

---

## 7. Etat Actuel et Prochaines Etapes

### 7.1 Travaux Realises

| Module | Statut | Description |
|--------|--------|-------------|
| **Infrastructure Docker** | Complet | Tous les services containerises |
| **Pipeline NiFi v2** | Complet | 6 zones + DLQ deployes |
| **Schema ClickHouse** | Complet | 153 colonnes + 11 vues Power BI |
| **Oracle A9** | Complet | Random Forest fonctionnel |
| **Classifier A10** | Complet | Classification qualite |
| **Cortex A11** | Complet | Optimisation scipy |
| **Configuration Centralisee** | Complet | vertiflow_constants.py |
| **Scripts NiFi** | Nettoyes | Suppression doublons, credentials centralises |

### 7.2 Nettoyage Effectue (Session Actuelle)

1. **Suppression dossier duplique** `vertiflow_ML/` (1.2 GB)
2. **Consolidation SQL** - Fusion des scripts predictions
3. **Centralisation NiFi** - Creation `nifi_config.py`
4. **Credentials securises** - Variables d'environnement
5. **Documentation** - README.md mis a jour

### 7.3 Prochaines Etapes Recommandees

| Priorite | Tache | Effort Estime |
|----------|-------|---------------|
| **P0** | Tests d'integration end-to-end | Court |
| **P1** | Entrainement modeles sur donnees reelles | Moyen |
| **P2** | Monitoring Prometheus complet | Moyen |
| **P3** | Documentation API (Swagger) | Court |
| **P4** | CI/CD Pipeline (GitHub Actions) | Moyen |

---

## Annexes

### A. Equipe Projet

| Membre | Role | Responsabilite |
|--------|------|----------------|
| @Mounir | Architecte & Scientifique | Architecture, ML, Bio-physique |
| @Imrane | DevOps & Infrastructure | Docker, NiFi, Deploiement |
| @Mouhammed | Data Engineer | ETL, ClickHouse, Kafka |
| @Asama | Biologiste | Validation scientifique |
| **@MrZakaria** | Encadrant | Architecture Data, Review |

### B. Repertoire du Code

```
test-projet-agri/
├── cloud_citadel/
│   ├── nervous_system/
│   │   ├── oracle.py          # A9 - Prediction rendement
│   │   ├── classifier.py      # A10 - Classification qualite
│   │   ├── cortex.py          # A11 - Optimisation recettes
│   │   └── simulator.py       # Calculs bio-physiques
│   └── connectors/
│       ├── stream_processor.py # Kafka → ClickHouse
│       └── feedback_loop.py    # Apprentissage continu
├── config/
│   └── vertiflow_constants.py  # SOURCE DE VERITE
├── infrastructure/
│   ├── docker-compose.yml
│   └── init_scripts/
├── scripts/
│   └── nifi_workflows/
│       ├── nifi_config.py      # Config centralisee
│       └── deploy/             # Scripts deploiement
└── docs/
    └── 01_ARCHITECTURE.md      # Documentation technique
```

### C. References

- Farquhar, G.D. et al. (1980) - Modele de photosynthese
- Murray, F.W. (1967) - Calcul pression de vapeur saturante
- Initiative JobInTech - YNOV Maroc Campus

---

**Document genere le**: Janvier 2026
**Version**: 1.0
**Statut**: Approuve pour revue par Mr. Zakaria
