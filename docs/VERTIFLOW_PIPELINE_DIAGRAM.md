# VertiFlow NiFi Pipeline - Architecture Diagram

## Vue d'Ensemble Complète

```mermaid
flowchart TB
    subgraph ZONE0["Zone 0 - External Data APIs"]
        direction TB
        T_WEATHER[/"Trigger - Hourly Weather<br/>(GenerateFlowFile)"/]
        T_NASA[/"Trigger - Daily NASA POWER<br/>(GenerateFlowFile)"/]
        T_AIR[/"Trigger - Air Quality<br/>(GenerateFlowFile)"/]

        API_WEATHER["API - Open-Meteo Weather<br/>(InvokeHTTP)"]
        API_NASA["API - NASA POWER<br/>(InvokeHTTP)"]
        API_AIR["API - OpenAQ Air Quality<br/>(InvokeHTTP)"]

        PUB_WEATHER["Publish - Weather to Kafka<br/>(PublishKafka_2_6)"]
        PUB_NASA["Publish - NASA to Kafka<br/>(PublishKafka_2_6)"]
        PUB_AIR["Publish - AirQuality to Kafka<br/>(PublishKafka_2_6)"]

        T_WEATHER --> API_WEATHER --> PUB_WEATHER
        T_NASA --> API_NASA --> PUB_NASA
        T_AIR --> API_AIR --> PUB_AIR
    end

    subgraph ZONE5["Zone 5 - Static Data Loaders"]
        direction TB
        GF_RECIPES["GetFile - Recipes<br/>(GetFile)"]
        GF_LAB["GetFile - Lab Data<br/>(GetFile)"]
        GF_DATASETS["GetFile - Datasets CSV<br/>(GetFile)"]

        VALIDATE_LAB["ValidateRecord - Lab Data<br/>(ValidateRecord)"]
        CONVERT_CSV["ConvertRecord - CSV to JSON<br/>(ConvertRecord)"]

        PUB_DATASETS["Publish - Datasets to Kafka<br/>(PublishKafka_2_6)"]
        PUB_LAB["Publish - Lab to Kafka<br/>(PublishKafka_2_6)"]

        CONSUME_SCRAPED["ConsumeKafka - Scraped Data<br/>(ConsumeKafka_2_6)"]
        PUT_MARKET["PutMongo - Market Prices<br/>(PutMongo)"]
        PUT_RECIPES["PutMongo - Plant Recipes<br/>(PutMongo)"]

        GF_RECIPES --> PUT_RECIPES
        GF_LAB --> VALIDATE_LAB --> PUB_LAB
        GF_DATASETS --> CONVERT_CSV --> PUB_DATASETS
        CONSUME_SCRAPED --> PUT_MARKET
    end

    subgraph ZONE1["Zone 1 - Ingestion & Validation"]
        direction TB
        A1_HTTP["A1 - ListenHTTP<br/>(ListenHTTP)"]
        A2_MQTT["A2 - ConsumeMQTT<br/>(ConsumeMQTT)"]
        A3_FILE["A3 - GetFile<br/>(GetFile)"]

        VALIDATE["ValidateRecord<br/>(ValidateRecord)"]
        MONITOR["Monitor_Ingestion_Health<br/>(MonitorActivity)"]

        TO_ZONE2(["To_Zone_2<br/>(Output Port)"])

        A1_HTTP --> VALIDATE
        A2_MQTT --> VALIDATE
        A3_FILE --> VALIDATE
        VALIDATE --> MONITOR --> TO_ZONE2
    end

    subgraph ZONE2["Zone 2 - Contextualisation"]
        direction TB
        FROM_ZONE1(["From_Zone_1<br/>(Input Port)"])

        B1_LOOKUP["B1 - LookupRecord<br/>(LookupRecord)"]
        B2_VPD["B2 - ExecuteScript (VPD)<br/>(ExecuteScript - Groovy)"]
        B3_JOLT["B3 - JoltTransformJSON<br/>(JoltTransformJSON)"]
        B4_KAFKA["B4 - PublishKafka (Telemetry)<br/>(PublishKafka_2_6)"]

        FROM_ZONE1 --> B1_LOOKUP
        B1_LOOKUP -->|matched/unmatched| B2_VPD
        B2_VPD -->|success| B3_JOLT
        B3_JOLT -->|success| B4_KAFKA
    end

    subgraph ZONE3["Zone 3 - Persistance"]
        direction TB
        C0_CONSUME["C0 - ConsumeKafka (Storage)<br/>(ConsumeKafka_2_6)"]

        C1_CLICK["C1 - PutClickHouse (via JDBC)<br/>(PutDatabaseRecord)"]
        C2_MONGO["C2 - PutMongo (Audit)<br/>(PutMongo)"]
        C3_FILE["C3 - PutFile (Archive)<br/>(PutFile)"]

        RATE1["Rate Limit<br/>(ControlRate)"]
        LOG1["Log Error<br/>(LogAttribute)"]

        C0_CONSUME --> C1_CLICK
        C0_CONSUME --> C2_MONGO
        C0_CONSUME --> C3_FILE

        C1_CLICK -->|failure| LOG1 --> RATE1
        C2_MONGO -->|failure| LOG1
        C3_FILE -->|failure| LOG1
    end

    subgraph ZONE4["Zone 4 - Retroaction"]
        direction TB
        D0_CONSUME["D0 - ConsumeKafka (Feedback)<br/>(ConsumeKafka_2_6)"]
        D1_QUERY["D1 - QueryRecord<br/>(QueryRecord)"]
        D2_JSON["D2 - AttributesToJSON<br/>(AttributesToJSON)"]
        D3_MQTT["D3 - PublishMQTT<br/>(PublishMQTT)"]

        ALERTS_EXT(["Alerts_External<br/>(Output Port)"])

        D0_CONSUME --> D1_QUERY
        D1_QUERY --> D2_JSON
        D2_JSON --> D3_MQTT
        D3_MQTT --> ALERTS_EXT
    end

    subgraph DLQ["DLQ - Dead Letter Queue"]
        direction TB
        DLQ_LOG["DLQ_Logger<br/>(LogAttribute)"]
    end

    subgraph EXTERNAL["Systemes Externes"]
        direction TB
        KAFKA[(Apache Kafka<br/>kafka:29092)]
        CLICKHOUSE[(ClickHouse<br/>vertiflow DB)]
        MONGODB[(MongoDB<br/>vertiflow_ops)]
        MOSQUITTO[Eclipse Mosquitto<br/>MQTT Broker]
        FILES[/File System<br/>exchange/output/]
    end

    %% Connexions inter-zones
    TO_ZONE2 --> FROM_ZONE1

    %% Connexions Kafka
    PUB_WEATHER --> KAFKA
    PUB_NASA --> KAFKA
    PUB_AIR --> KAFKA
    B4_KAFKA --> KAFKA
    PUB_DATASETS --> KAFKA
    PUB_LAB --> KAFKA

    KAFKA --> C0_CONSUME
    KAFKA --> D0_CONSUME
    KAFKA --> CONSUME_SCRAPED

    %% Connexions bases de donnees
    C1_CLICK --> CLICKHOUSE
    C2_MONGO --> MONGODB
    PUT_MARKET --> MONGODB
    PUT_RECIPES --> MONGODB

    %% Connexions fichiers
    C3_FILE --> FILES

    %% Connexions MQTT
    MOSQUITTO --> A2_MQTT
    D3_MQTT --> MOSQUITTO

    %% Connexions DLQ (erreurs)
    VALIDATE -->|failure| DLQ_LOG
    B1_LOOKUP -->|failure| DLQ_LOG
    B2_VPD -->|failure| DLQ_LOG
    B3_JOLT -->|failure| DLQ_LOG

    %% Styles
    classDef zone0 fill:#e1f5fe,stroke:#01579b
    classDef zone1 fill:#fff3e0,stroke:#e65100
    classDef zone2 fill:#f3e5f5,stroke:#4a148c
    classDef zone3 fill:#e8f5e9,stroke:#1b5e20
    classDef zone4 fill:#fce4ec,stroke:#880e4f
    classDef zone5 fill:#fff8e1,stroke:#ff6f00
    classDef dlq fill:#ffebee,stroke:#b71c1c
    classDef external fill:#eceff1,stroke:#37474f

    class ZONE0 zone0
    class ZONE1 zone1
    class ZONE2 zone2
    class ZONE3 zone3
    class ZONE4 zone4
    class ZONE5 zone5
    class DLQ dlq
    class EXTERNAL external
```

## Flux de Donnees Simplifie

```mermaid
flowchart LR
    subgraph Sources["Sources de Donnees"]
        API[APIs Externes]
        MQTT_IN[Capteurs MQTT]
        HTTP_IN[HTTP REST]
        FILES_IN[Fichiers CSV/JSON]
    end

    subgraph Pipeline["Pipeline NiFi"]
        Z0[Zone 0<br/>APIs Externes]
        Z1[Zone 1<br/>Ingestion]
        Z2[Zone 2<br/>Contextualisation]
        Z3[Zone 3<br/>Persistance]
        Z4[Zone 4<br/>Retroaction]
        Z5[Zone 5<br/>Static Loaders]
        DLQ[DLQ]
    end

    subgraph Storage["Stockage"]
        KAFKA[(Kafka)]
        CLICK[(ClickHouse)]
        MONGO[(MongoDB)]
        ARCHIVE[Archive Files]
    end

    subgraph Output["Sorties"]
        MQTT_OUT[Alertes MQTT]
        DASHBOARD[Power BI]
    end

    API --> Z0 --> KAFKA
    MQTT_IN --> Z1
    HTTP_IN --> Z1
    FILES_IN --> Z1
    FILES_IN --> Z5

    Z1 --> Z2 --> KAFKA
    KAFKA --> Z3
    KAFKA --> Z4
    KAFKA --> Z5

    Z3 --> CLICK
    Z3 --> MONGO
    Z3 --> ARCHIVE

    Z4 --> MQTT_OUT
    CLICK --> DASHBOARD

    Z1 -.->|errors| DLQ
    Z2 -.->|errors| DLQ
```

## Architecture des Topics Kafka

```mermaid
flowchart TB
    subgraph Producers["Producteurs"]
        Z0_PROD["Zone 0<br/>External APIs"]
        Z2_PROD["Zone 2<br/>Telemetry"]
        Z5_PROD["Zone 5<br/>Datasets"]
    end

    subgraph Topics["Topics Kafka"]
        T_WEATHER["vertiflow.external.weather"]
        T_NASA["vertiflow.external.nasa"]
        T_AIR["vertiflow.external.airquality"]
        T_TELEMETRY["basil_telemetry_full"]
        T_DATASETS["datasets_topic"]
        T_LAB["lab_data_topic"]
    end

    subgraph Consumers["Consommateurs"]
        Z3_CONS["Zone 3<br/>Persistance"]
        Z4_CONS["Zone 4<br/>Feedback"]
        Z5_CONS["Zone 5<br/>Market Data"]
    end

    Z0_PROD --> T_WEATHER
    Z0_PROD --> T_NASA
    Z0_PROD --> T_AIR
    Z2_PROD --> T_TELEMETRY
    Z5_PROD --> T_DATASETS
    Z5_PROD --> T_LAB

    T_TELEMETRY --> Z3_CONS
    T_TELEMETRY --> Z4_CONS
    T_DATASETS --> Z5_CONS
```

## Details par Zone

### Zone 0 - External Data APIs
| Processeur | Type | Description |
|-----------|------|-------------|
| Trigger - Hourly Weather | GenerateFlowFile | Declencheur horaire pour meteo |
| Trigger - Daily NASA POWER | GenerateFlowFile | Declencheur quotidien NASA |
| Trigger - Air Quality | GenerateFlowFile | Declencheur qualite de l'air |
| API - Open-Meteo Weather | InvokeHTTP | Appel API meteo Open-Meteo |
| API - NASA POWER | InvokeHTTP | Appel API NASA POWER |
| API - OpenAQ Air Quality | InvokeHTTP | Appel API qualite air |
| Publish - Weather to Kafka | PublishKafka_2_6 | Publication vers Kafka |
| Publish - NASA to Kafka | PublishKafka_2_6 | Publication vers Kafka |
| Publish - AirQuality to Kafka | PublishKafka_2_6 | Publication vers Kafka |

### Zone 1 - Ingestion & Validation
| Processeur | Type | Description |
|-----------|------|-------------|
| A1 - ListenHTTP | ListenHTTP | Reception donnees HTTP REST |
| A2 - ConsumeMQTT | ConsumeMQTT | Reception capteurs MQTT |
| A3 - GetFile | GetFile | Lecture fichiers locaux |
| ValidateRecord | ValidateRecord | Validation schema JSON |
| Monitor_Ingestion_Health | MonitorActivity | Surveillance ingestion |

### Zone 2 - Contextualisation
| Processeur | Type | Description |
|-----------|------|-------------|
| B1 - LookupRecord | LookupRecord | Enrichissement via MongoDB lookup |
| B2 - ExecuteScript (VPD) | ExecuteScript | Calcul VPD (Vapor Pressure Deficit) |
| B3 - JoltTransformJSON | JoltTransformJSON | Transformation structure JSON |
| B4 - PublishKafka (Telemetry) | PublishKafka_2_6 | Publication telemetrie vers Kafka |

### Zone 3 - Persistance
| Processeur | Type | Description |
|-----------|------|-------------|
| C0 - ConsumeKafka (Storage) | ConsumeKafka_2_6 | Consommation depuis Kafka |
| C1 - PutClickHouse (via JDBC) | PutDatabaseRecord | Insertion ClickHouse (OLAP) |
| C2 - PutMongo (Audit) | PutMongo | Insertion MongoDB (audit) |
| C3 - PutFile (Archive) | PutFile | Archivage fichiers |

### Zone 4 - Retroaction
| Processeur | Type | Description |
|-----------|------|-------------|
| D0 - ConsumeKafka (Feedback) | ConsumeKafka_2_6 | Consommation feedback |
| D1 - QueryRecord | QueryRecord | Filtrage alertes SQL |
| D2 - AttributesToJSON | AttributesToJSON | Conversion attributs en JSON |
| D3 - PublishMQTT | PublishMQTT | Publication alertes MQTT |

### Zone 5 - Static Data Loaders
| Processeur | Type | Description |
|-----------|------|-------------|
| GetFile - Recipes | GetFile | Chargement recettes agronomiques |
| GetFile - Lab Data | GetFile | Chargement donnees laboratoire |
| GetFile - Datasets CSV | GetFile | Chargement datasets CSV |
| ValidateRecord - Lab Data | ValidateRecord | Validation donnees labo |
| ConvertRecord - CSV to JSON | ConvertRecord | Conversion CSV vers JSON |
| PutMongo - Plant Recipes | PutMongo | Stockage recettes |
| PutMongo - Market Prices | PutMongo | Stockage prix marche |

### DLQ - Dead Letter Queue
| Processeur | Type | Description |
|-----------|------|-------------|
| DLQ_Logger | LogAttribute | Journalisation des erreurs |

## Infrastructure Docker

```mermaid
flowchart TB
    subgraph Docker["Docker Compose - vertiflow-network"]
        NIFI["Apache NiFi<br/>:8443"]
        KAFKA["Apache Kafka<br/>:29092 (internal)<br/>:9092 (external)"]
        ZOOKEEPER["Zookeeper<br/>:2181"]
        CLICKHOUSE["ClickHouse<br/>:8123 / :9000"]
        MONGODB["MongoDB<br/>:27017"]
        MOSQUITTO["Mosquitto<br/>:1883 / :9001"]
    end

    subgraph Volumes["Volumes Persistants"]
        V_NIFI["nifi-conf<br/>nifi-database<br/>nifi-flowfile<br/>nifi-content<br/>nifi-provenance"]
        V_CLICK["clickhouse-data"]
        V_MONGO["mongodb-data"]
        V_MOSQ["mosquitto-data<br/>mosquitto-logs"]
    end

    subgraph Host["Machine Hote"]
        EXCHANGE["./nifi_exchange<br/>/opt/nifi/nifi-current/exchange"]
        SCHEMAS["./docs/schemas<br/>/opt/nifi/schemas"]
        DRIVERS["./drivers<br/>/opt/nifi/nifi-current/drivers"]
    end

    KAFKA --> ZOOKEEPER
    NIFI --> KAFKA
    NIFI --> CLICKHOUSE
    NIFI --> MONGODB
    NIFI --> MOSQUITTO

    NIFI --- V_NIFI
    CLICKHOUSE --- V_CLICK
    MONGODB --- V_MONGO
    MOSQUITTO --- V_MOSQ

    NIFI --- EXCHANGE
    NIFI --- SCHEMAS
    NIFI --- DRIVERS
```

---
**Genere automatiquement pour le projet VertiFlow**
**Date: 2026-01-14**
