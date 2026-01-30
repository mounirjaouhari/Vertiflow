<!-- 
================================================================================
FILE: docs/01_ARCHITECTURE.md
TICKET: TICKET-112
TEAM MEMBERS: @Mounir (Architecture Lead), @Imrane (Infrastructure), @Mouhammed (Data Engineering)
DATE CREATED: 2026-01-02
LAST MODIFIED: 2026-01-02
VERSION: 1.0.0
DEPENDENCIES: None (core documentation)
================================================================================

PURPOSE:
Complete technical architecture documentation for VertiFlow Data Platform,
including system design, data flows, component interactions, and deployment
topology. This is the primary reference for understanding system structure.

DOCUMENT STRUCTURE:
1. Executive Summary
2. System Overview Diagram
3. Core Components
4. Data Flow Architecture
5. Technology Stack Details
6. Deployment Topology
7. Scalability & Performance
8. Security Architecture
9. Integration Points
10. Design Patterns & Principles

AUDIENCE: 
- Software architects
- DevOps engineers
- Data engineers
- New team members onboarding to the project

REVISION HISTORY:
v1.0.0 (2026-01-02): Initial comprehensive architecture documentation
================================================================================
-->

# VertiFlow Data Platform - Technical Architecture

## Executive Summary

VertiFlow is an **industrial-grade data platform for intelligent vertical farming**, designed to process real-time sensor data, perform predictive analytics, and generate actionable insights for autonomous farming operations. The platform integrates bio-physics simulation, machine learning prediction, and optimization algorithms to maximize crop yield while minimizing resource consumption.

**Key Characteristics:**
- **Real-time Processing**: Sub-second latency sensor data ingestion and stream processing
- **Scalable Analytics**: Distributed computing with Kafka + ClickHouse for handling millions of events/day
- **Intelligent Inference**: ML-powered prediction engine with self-learning feedback loops
- **Bio-Physics Integration**: Scientifically-validated crop models (Farquhar, Penman-Monteith, Tetens)
- **Autonomous Control**: Optimization algorithms for resource allocation and anomaly detection
- **Multi-Tenant Ready**: Farm/crop/zone isolation with role-based access control

---

## System Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VERTIFLOW DATA PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                      DATA INGESTION LAYER                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │   │
│  │  │  IoT Sensors │  │  External    │  │  NiFi Data Pipeline  │    │   │
│  │  │  (MQTT)      │  │  Data APIs   │  │  (Orchestration)     │    │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘    │   │
│  │         │                 │                     │                 │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│         │                     │                     │                      │
│         └─────────────────────┼─────────────────────┘                      │
│                               ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    MESSAGE BROKER LAYER                            │   │
│  │           ┌─────────────────────────────────────┐                 │   │
│  │           │  Apache Kafka (Streaming Messages)  │                 │   │
│  │           │  Topics: telemetry, commands, alerts│                 │   │
│  │           └─────────────────────────────────────┘                 │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                               │                                            │
│         ┌─────────────────────┼─────────────────────┐                     │
│         ▼                     ▼                     ▼                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐     │
│  │ Stream          │  │ Real-time Data   │  │ ML Inference       │     │
│  │ Processor       │  │ Store (CH)       │  │ Engine             │     │
│  │ (Process)       │  │ - Time-series    │  │ - Oracle (RandomFr)│     │
│  │ - Validation    │  │ - Raw telemetry  │  │ - Classifier (CNN) │     │
│  │ - Enrichment    │  │ - Aggregates     │  │ - Nervous System   │     │
│  │ - Aggregation   │  │                  │  │   (LSTM)           │     │
│  └────────┬────────┘  └──────────────────┘  └─────────┬──────────┘     │
│           │                                           │                  │
│           └───────────────────┬──────────────────────┘                   │
│                               ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │              ANALYTICS & OPTIMIZATION LAYER                        │ │
│  │  ┌────────────────┐  ┌────────────┐  ┌────────────────────────┐  │ │
│  │  │ Cortex Engine  │  │ Simulator  │  │ Feedback Loop Manager  │  │ │
│  │  │ - scipy.opt    │  │ - VPD calc │  │ - Performance tracking │  │ │
│  │  │ - Resource     │  │ - PSN calc │  │ - Model retraining     │  │ │
│  │  │   allocation   │  │ - DLI calc │  │ - Drift detection      │  │ │
│  │  │ - Anomaly det  │  │ - ET calc  │  │                        │  │ │
│  │  └────────────────┘  └────────────┘  └────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│           │                                                              │
│           └────────────────────────┬──────────────────────────┐         │
│                                    ▼                          ▼         │
│  ┌─────────────────────────────────────────────┐  ┌──────────────────┐ │
│  │  MongoDB Document Store                     │  │ PostgreSQL       │ │
│  │  - Recipes & control strategies             │  │ - User auth      │ │
│  │  - Operational logs                         │  │ - Audit logs     │ │
│  │  - Farm configuration                       │  │ - Subscriptions  │ │
│  │  - Model versioning                         │  │                  │ │
│  └─────────────────────────────────────────────┘  └──────────────────┘ │
│           │                                                              │
│           └─────────────────────┬──────────────────────────────┐        │
│                                 ▼                              ▼        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    PRESENTATION LAYER                          │   │
│  │  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────┐│   │
│  │  │ Grafana       │  │ Custom Web   │  │ Mobile / Alerts     ││   │
│  │  │ Dashboards    │  │ Dashboard    │  │ (Webhook / Email)   ││   │
│  │  │ (Metrics)     │  │ (React.js)   │  │                     ││   │
│  │  └───────────────┘  └──────────────┘  └─────────────────────┘│   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Data Ingestion & Orchestration

#### IoT Sensor Input (MQTT)
- **Protocol**: MQTT 3.1.1 over Mosquitto broker
- **Topics**: 
  - `vertiflow/farm/{farm_id}/sensor/{sensor_id}/telemetry` → Raw sensor readings
  - `vertiflow/farm/{farm_id}/zone/{zone_id}/environmental` → Aggregated zone data
- **Data Format**: JSON with timestamp, value, unit, quality_flag
- **Rate**: 100-1000 Hz per sensor, scalable to 10,000+ simultaneous sensors
- **QoS**: Level 1 (at-least-once delivery with acknowledgment)

#### NiFi Orchestration Layer
- **Role**: Data pipeline orchestration and transformation
- **Key Flows**:
  - NASA Power external data ingestion (daily forecasts)
  - Legacy database polling and ETL
  - Data quality validation and schema enforcement
  - Historical data migration and backfill
- **Configuration**: `config/nifi_pipeline_prod.yaml`
- **Scaling**: Clustered NiFi nodes for high-availability

### 2. Message Broker (Apache Kafka)

**Topics Architecture:**

| Topic | Partitions | Retention | Purpose |
|-------|-----------|-----------|---------|
| `vertiflow.sensor.telemetry` | 12 | 7 days | Raw sensor data (primary ingestion) |
| `vertiflow.computed.features` | 6 | 14 days | ML-computed features & aggregates |
| `vertiflow.farm.commands` | 3 | 24 hours | Commands to farm control systems |
| `vertiflow.alerts.critical` | 3 | 30 days | Critical alerts & anomalies |
| `vertiflow.models.predictions` | 6 | 7 days | ML model predictions (Oracle output) |
| `vertiflow.optimization.actions` | 3 | 24 hours | Cortex optimization recommendations |

**Consumer Groups:**
- `stream-processor` → Processes raw telemetry → ClickHouse
- `ml-inference` → Consumes features → Oracle/Classifier
- `feedback-loop` → Tracks prediction performance → model retraining
- `monitoring-exporter` → Prometheus metrics export

### 3. Stream Processing Engine

**Component**: `cloud_citadel/connectors/stream_processor.py`

```
Raw Telemetry (Kafka)
    ↓
[Schema Validation]
    ↓
[Data Quality Checks]
    - Min/Max range validation
    - Outlier detection (IQR method)
    - Missing data imputation
    ↓
[Feature Engineering]
    - Rolling averages (5min, 15min, 1hr)
    - Derivative features (rates of change)
    - Seasonal decomposition
    ↓
[Aggregation by Zone/Crop]
    - Time-series materialized views
    - Dimensional aggregates
    ↓
[ClickHouse Insert]
    - Batch inserts (1000 row blocks)
    - Async write with retry
```

**Performance Targets:**
- P50 latency: < 100ms (ingestion to ClickHouse)
- P99 latency: < 500ms
- Throughput: 100,000 events/second
- Data loss: 0 (exactly-once semantics with deduplication)

### 4. Real-Time Analytics Engine

#### ClickHouse Data Warehouse
- **Engine**: MergeTree (time-series optimized)
- **Primary Tables**:
  - `sensor_telemetry` (immutable raw data)
  - `computed_features` (ML features, 1min granularity)
  - `hourly_aggregates` (hourly statistics)
  - `daily_summaries` (daily KPIs)
- **Partitioning**: By (farm_id, toYYYYMM(timestamp))
- **Replication**: 2x replica for HA
- **Compression**: ZSTD with dictionary compression

#### Data Structure Example:
```sql
CREATE TABLE sensor_telemetry (
    farm_id UInt32,
    zone_id UInt32,
    sensor_id String,
    measurement_type String,  -- 'temperature', 'humidity', 'light', etc.
    value Float32,
    unit String,
    timestamp DateTime,
    quality_flag UInt8,  -- 0=valid, 1=interpolated, 2=suspicious
    reception_delay_ms UInt16
) ENGINE = MergeTree
ORDER BY (farm_id, zone_id, timestamp, sensor_id)
PARTITION BY (farm_id, toYYYYMM(timestamp));
```

### 5. ML Inference Engine

#### Oracle Module (cloud_citadel/nervous_system/oracle.py)
- **Algorithm**: Random Forest Regressor (scikit-learn)
- **Predictions**:
  - **Yield prediction**: Estimated crop weight at harvest
  - **Quality class**: PREMIUM / GRADE_A / GRADE_B / REJECT
  - **Optimal harvesting time**: Days to maturity
- **Input Features**: 45-dimensional vector (sensor aggregates + environmental)
- **Training Data**: Historical 12+ months per crop type
- **Retraining Frequency**: Weekly with sliding window validation
- **Performance Metrics**: R² > 0.92, RMSE < 150g/plant

#### Classifier Module (cloud_citadel/nervous_system/classifier.py)
- **Algorithm**: Custom CNN (TensorFlow/Keras)
- **Task**: Visual quality classification from images
- **Classes**: 4 (PREMIUM, GRADE_A, GRADE_B, REJECT)
- **Input**: 256×256×3 RGB images from overhead cameras
- **Accuracy**: > 96% on validation set (Haralick et al., 1973)
- **Inference Time**: < 50ms per image

#### Nervous System (LSTM-based)
- **Algorithm**: Multi-layer LSTM (TensorFlow)
- **Purpose**: Sequential anomaly detection and trend forecasting
- **Lookback Window**: 7 days of hourly data
- **Prediction Horizon**: 24-48 hours ahead
- **Applications**:
  - Early detection of disease/pest outbreaks
  - Water stress prediction
  - Nutrient deficiency warnings

### 6. Optimization Engine (Cortex)

**Component**: `cloud_citadel/nervous_system/cortex.py`

**Problems Solved:**
1. **Resource Allocation** - Water, nutrients, light distribution
   - Algorithm: Quadratic programming (scipy.optimize.minimize)
   - Objective: Maximize yield × quality while minimizing resource cost
   - Constraints: Water budget, electrical load, nutrient availability
   
2. **Anomaly Detection** - Identify equipment malfunction or unusual patterns
   - Method: Isolation Forest on 45-dim feature space
   - Threshold: Dynamically adjusted based on historical percentiles
   - Output: Severity score (0-100), recommended action

3. **Scheduling Optimization** - Irrigation/fertilizer/light control
   - Algorithm: Dynamic programming with rolling horizon
   - Objective: Maximize cumulative yield given resource constraints
   - Horizon: 7-day planning window with daily updates

**Optimization Loop:**
```
Current State (ClickHouse)
    ↓
[Feature Extraction & Normalization]
    ↓
[Oracle Prediction] → Yield/Quality estimates
    ↓
[Constraint Validation]
    ↓
[Optimization Problem Setup]
    - Objective: f(actions) = expected_yield × expected_quality
    - Constraints: resources ≤ budgets
    - Variables: irrigation_rate, nutrient_dose, light_intensity
    ↓
[scipy.optimize.minimize] → Optimal actions
    ↓
[Feedback Loop Learning]
    - Compare predicted vs. actual outcomes
    - Adjust weights for next optimization cycle
    ↓
[Commands Published] → Kafka (farm.commands)
```

### 7. Simulator Module (Bio-Physics)

**Component**: `cloud_citadel/nervous_system/simulator.py`

Implements validated scientific models for crop physiology:

#### Vapor Pressure Deficit (VPD) - Tetens Formula
```
E_s(T) = 6.112 × exp(17.67 × T / (T + 243.5))  [hPa]
VPD = (E_s - E_a) = E_s × (1 - RH/100)
Optimal range: 0.8-1.2 kPa for most crops
```
- **Inputs**: Temperature, Relative Humidity
- **Output**: VPD in kPa, stress indicator
- **Application**: Irrigation trigger, disease risk assessment

#### Photosynthetic Rate (PSN) - Farquhar Model
```
A = min(J/4 - Γ*, (V_cmax(C_i - Γ*)/(C_i + K_m)) - R_d)
where:
  J = PPFD × 0.25 × φ  [photon rate, Farquhar 1980]
  Γ* = CO₂ compensation point
  V_cmax = max carboxylation velocity
  K_m = Michaelis-Menten constant for CO₂
```
- **Inputs**: PPFD (µmol/m²/s), Leaf temperature, CO₂
- **Output**: Photosynthetic assimilation rate (µmol CO₂/m²/s)
- **Application**: Light optimization, growth rate prediction

#### Transpiration - Penman-Monteith Equation
```
ET = [Δ(R_n - G) + ρ c_p (e_s - e_a)/r_a] / [Δ + γ(1 + r_s/r_a)]
where:
  R_n = net radiation, G = ground heat flux
  r_a = aerodynamic resistance
  r_s = stomatal resistance
```
- **Inputs**: Radiation, temperature, VPD, wind speed
- **Output**: Evapotranspiration rate (mm/day)
- **Application**: Water requirement calculation

#### Daily Light Integral (DLI)
```
DLI = (PPFD × daylength × 3.6) / 10^6  [mol/m²/day]
Typical requirement: 12-17 mol/m²/day for vegetables
```

### 8. Feedback Loop & Model Retraining

**Component**: `cloud_citedel/connectors/feedback_loop.py`

```
Production Predictions (Oracle)
    ↓ [Store in MongoDB]
    ↓
[1 week later] Actual Outcomes Available
    ↓ [Pull from ClickHouse]
    ↓
[Performance Metrics Calculation]
    - MAE: Mean Absolute Error
    - RMSE: Root Mean Squared Error
    - MAPE: Mean Absolute Percentage Error
    - R²: Coefficient of determination
    ↓
[Drift Detection]
    - Compare current metric vs. baseline (Kolmogorov-Smirnov test)
    - Trigger retraining if drift detected
    ↓
[Model Retraining Pipeline]
    - Feature engineering on 12 months historical data
    - Train/val/test split (60/20/20)
    - Hyperparameter tuning with GridSearchCV
    - Cross-validation to prevent overfitting
    ↓
[Approval Workflow]
    - New model evaluated on holdout test set
    - Performance threshold check (R² > 0.92)
    - A/B testing period (20% of predictions)
    ↓
[Promotion to Production]
    - Model versioning in MongoDB
    - Gradual traffic shift (10% → 50% → 100%)
    - Automatic rollback if performance degrades
```

**Metrics Tracked:**
| Metric | Threshold | Action |
|--------|-----------|--------|
| RMSE > baseline × 1.2 | Drift Detected | Flag for review |
| R² < 0.88 | Performance degradation | Trigger retrain |
| MAE trend +10%/week | Concept drift | Retrain with new data |
| Prediction latency > 500ms | Performance issue | Optimize model |

---

## Data Flow Architecture

### End-to-End Telemetry Flow

```
PHASE 1: INGESTION (Real-time, MQTT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sensor (Temperature, Humidity, Light)
  ├─ Data: {"value": 24.5, "unit": "°C", "ts": 1704192000}
  ├─ Protocol: MQTT QoS1
  └─ Topic: vertiflow/farm/F001/sensor/TMP001/telemetry

Mosquitto Broker
  ├─ Message Persistence: Enabled
  ├─ Max Messages: 10,000 per topic
  └─ Clean Session: False (allows resumption)

NiFi Processor (Optional enrichment)
  ├─ Add metadata (farm_id, zone_id)
  ├─ Schema validation
  └─ Batch → Kafka producer

PHASE 2: MESSAGE ROUTING (Kafka)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Kafka Topic: vertiflow.sensor.telemetry
  ├─ Partition key: farm_id + zone_id (consistent routing)
  ├─ Replication: 2x
  ├─ Min In-Sync Replicas: 2
  ├─ Retention: 7 days / 100GB
  └─ Compression: Snappy

Message Format (Avro):
{
  "farm_id": "F001",
  "zone_id": "Z001",
  "sensor_id": "TMP001",
  "measurement_type": "temperature",
  "value": 24.5,
  "unit": "C",
  "timestamp": 1704192000000,
  "quality_flag": 0
}

PHASE 3: STREAM PROCESSING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Consumer Group: stream-processor
  ├─ Auto-commit offset: Every 5 seconds
  ├─ Processing guarantee: Exactly-once
  └─ Fetch size: 50MB

StreamProcessor (Python)
  Step 1: Deserialize Avro → Dict
  Step 2: Schema validation (jsonschema)
  Step 3: Range checks (is 24.5°C within expected range for crop?)
  Step 4: Outlier detection (IQR method)
  Step 5: Missing value handling (forward-fill)
  Step 6: Aggregation (store raw, compute 5-min average)
  Step 7: ClickHouse batch insert (1000 rows)

PHASE 4: ANALYTICS STORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ClickHouse Table: sensor_telemetry
  ├─ Row inserted with timestamp indexing
  ├─ Partitioned by: (farm_id, YYYY-MM)
  ├─ Compressed with: ZSTD
  └─ Replicated to standby node

Materialized Views (auto-aggregation):
  ├─ computed_features (1-minute aggregates)
  │   └─ Avg, Min, Max, StdDev per sensor per minute
  ├─ hourly_aggregates (1-hour stats)
  │   └─ Daily curves, thermal integral, light sum
  └─ daily_summaries (1-day KPIs)
      └─ Total irrigation, nutrient use, yield estimate

PHASE 5: ML INFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature Vector (45-dim):
  From computed_features (45-minute window):
    ├─ Temperature: mean, min, max, std, trend
    ├─ Humidity: mean, min, max, std, VPD
    ├─ Light: total PPFD, peak, DLI
    ├─ Environmental: CO₂, wind speed
    └─ Temporal: hour_of_day, day_of_week, days_since_planting

Oracle (Random Forest)
  ├─ Input: 45-dim feature vector
  ├─ Prediction 1: yield_estimate (kg/m²)
  ├─ Prediction 2: quality_class (PREMIUM/A/B/REJECT)
  └─ Confidence: prediction uncertainty (std dev across trees)

Classifier (CNN)
  ├─ Input: Latest plant image (256×256×3 RGB)
  ├─ Output: Quality class + confidence score
  └─ Latency: 45ms per image

PHASE 6: OPTIMIZATION & CONTROL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cortex Optimization Engine
  ├─ Current state: Retrieved from ClickHouse
  ├─ Predictions: From Oracle + Nervous System
  ├─ Constraints: Water budget, electrical load, nutrient stock
  ├─ Objective: max(yield × quality - cost)
  └─ Solution: Optimal irrigation/light/nutrient settings

Control Commands Kafka Topic: vertiflow.farm.commands
  └─ Published: Every 15 minutes
      {
        "farm_id": "F001",
        "zone_id": "Z001",
        "command_id": "CMD-20260102-001",
        "timestamp": 1704192900000,
        "action_type": "set_irrigation_rate",
        "parameters": {
          "flow_rate_ml_per_min": 2.5,
          "duration_minutes": 30,
          "priority": "normal"
        }
      }

PHASE 7: FEEDBACK & LEARNING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Weekly Batch Process:
  Step 1: Retrieve actual outcomes (weight, quality) → ClickHouse
  Step 2: Calculate prediction errors (RMSE, MAPE, R²)
  Step 3: Detect concept drift (KS test)
  Step 4: If drift detected → trigger model retraining
  Step 5: Retrain on sliding 12-month window
  Step 6: Validate on holdout test set
  Step 7: A/B test new model (10% traffic)
  Step 8: Promote if performance verified
  Step 9: Archive old model for audit trail

Performance Repository: MongoDB collection "model_versions"
  └─ Each entry: {version, train_date, metrics, status, promotion_date}
```

---

## Technology Stack Details

### Languages & Frameworks
- **Python 3.11+** - Core platform language
  - scikit-learn: ML algorithms (RandomForest, IsolationForest)
  - TensorFlow/Keras: Deep learning (CNN, LSTM)
  - pandas/numpy: Data manipulation
  - scipy: Scientific computing & optimization
  - pydantic: Data validation
  
- **SQL** - ClickHouse, PostgreSQL queries
- **JavaScript/React.js** - Custom web dashboard (optional)
- **Bash/Python** - DevOps and automation scripts

### Databases & Data Stores
| Component | Purpose | Scale | Replication |
|-----------|---------|-------|-------------|
| ClickHouse | Analytics OLAP | 500M+ rows/day | 2x |
| MongoDB | Documents (recipes, logs) | 100GB+ | 3x replica set |
| ~~PostgreSQL~~ | ~~Relational (users, audit)~~ | NON UTILISE | - |
| Redis (optional) | Caching, rate limiting | - | Sentinel HA |

> **Note**: PostgreSQL/TimescaleDB ne sont PAS utilises dans l'implementation actuelle.
> ClickHouse couvre les besoins time-series et MongoDB les besoins documents.
> Voir `docs/ARCHITECTURE_DECISIONS.md` pour plus de details.

### Message Brokers & Streaming
- **Apache Kafka**: Primary event backbone
  - Cluster size: 3+ brokers for HA
  - Zookeeper: 3-node ensemble for coordination
  - Schema Registry: Avro schema versioning
  
- **Mosquitto MQTT**: IoT sensor gateway
  - Multi-threaded architecture
  - TLS/SSL support
  - Persistence: SQLite backend

### Orchestration & Scheduling
- **Apache NiFi**: Data pipeline orchestration
  - Cluster mode: 3+ nodes
  - REST API for programmatic control
  - Visual dataflow design
  
- **Docker Compose**: Local/staging deployment
- **Kubernetes** (future): Production deployment

### Infrastructure
- **Linux** (Ubuntu 22.04 LTS): All services
- **Docker**: Container runtime
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **ELK Stack** (optional): Centralized logging

---

## Deployment Topology

### Single-Node Development (docker-compose.yml)

```
┌─ Development Machine ──────────────────────────────────────┐
│                                                             │
│  Container: mosquitto       Container: kafka              │
│  ├─ MQTT broker           ├─ Broker 1                     │
│  ├─ Port 1883             ├─ Zookeeper (embedded)         │
│  └─ No persistence        └─ Schema Registry              │
│                                                             │
│  Container: clickhouse    Container: mongodb              │
│  ├─ Analytics DB          ├─ Document store               │
│  ├─ Port 8123 (HTTP)      ├─ Port 27017                   │
│  └─ Dev defaults          └─ Auth disabled                │
│                                                             │
│  Container: vertiflow-app                                 │
│  ├─ Python application                                    │
│  ├─ Stream processor                                      │
│  ├─ ML inference                                          │
│  └─ Cortex optimization                                   │
│                                                             │
│  Container: grafana       Container: prometheus           │
│  ├─ Dashboard UI          ├─ Metrics DB                   │
│  ├─ Port 3000             ├─ Port 9090                    │
│  └─ Preset dashboards     └─ 30-day retention            │
└─────────────────────────────────────────────────────────────┘

Docker Network: vertiflow-net (bridge)
  └─ All containers communicate via internal DNS
```

### Cluster Production Deployment (Kubernetes)

```
┌─ Kubernetes Cluster ──────────────────────────────────────┐
│                                                             │
│  ┌─ Kafka StatefulSet                                     │
│  │  ├─ kafka-0, kafka-1, kafka-2                         │
│  │  ├─ PersistentVolume: 100GB per broker               │
│  │  ├─ ZooKeeper: 3-node ensemble                       │
│  │  └─ ClusterIP service: kafka-cluster:9092            │
│  │                                                        │
│  ├─ ClickHouse StatefulSet                              │
│  │  ├─ clickhouse-0 (primary), clickhouse-1 (replica)   │
│  │  ├─ PersistentVolume: 500GB per node                 │
│  │  └─ ClusterIP service: clickhouse:9000 (native)      │
│  │                                                        │
│  ├─ Streaming App Deployment                            │
│  │  ├─ 3 replicas (horizontal scaling)                 │
│  │  ├─ Resource requests: CPU 2, Memory 4Gi             │
│  │  ├─ Health check: liveness + readiness probes        │
│  │  └─ Rolling update strategy                          │
│  │                                                        │
│  ├─ ML Inference Deployment                             │
│  │  ├─ 2 replicas (GPU-enabled nodes)                   │
│  │  ├─ Resource requests: 1 GPU, 8GB memory             │
│  │  └─ Model cache: 50GB shared PVC                     │
│  │                                                        │
│  ├─ MongoDB Replica Set                                 │
│  │  ├─ 3 pods with StatefulSet                          │
│  │  ├─ PersistentVolume: 200GB per pod                  │
│  │  └─ Headless service: mongodb-headless:27017         │
│  │                                                        │
│  ├─ PostgreSQL                                          │
│  │  ├─ Primary + 2 streaming replicas                  │
│  │  ├─ PersistentVolume: 50GB                           │
│  │  └─ ClusterIP service: postgresql:5432               │
│  │                                                        │
│  ├─ Prometheus                                          │
│  │  ├─ StatefulSet with 1 replica                      │
│  │  ├─ PersistentVolume: 100GB                          │
│  │  └─ Service monitor: scrapes endpoints               │
│  │                                                        │
│  ├─ Grafana                                             │
│  │  ├─ Deployment with 2 replicas                      │
│  │  ├─ ConfigMap: Dashboard definitions                 │
│  │  └─ LoadBalancer: External port 3000                 │
│  │                                                        │
│  └─ NiFi Cluster                                        │
│     ├─ 3 StatefulSet pods                              │
│     ├─ ZooKeeper cluster for coordination              │
│     └─ Ingress: nifi.vertiflow.io                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Persistent Storage:
  ├─ AWS EBS / GCP Persistent Disk / Azure Disk for data
  ├─ S3 / GCS / Azure Blob for model archives
  └─ PostgreSQL RDS for managed relational DB

Networking:
  ├─ VPC isolation
  ├─ Security groups: Only ports 443 (HTTPS), 22 (SSH)
  ├─ LoadBalancer: Ingress controller with TLS termination
  └─ Internal DNS: kubernetes.default.svc.cluster.local
```

---

## Scalability & Performance

### Horizontal Scaling Strategy

**Kafka**: Partition distribution across 3-5 brokers
- Telemetry topic: 12 partitions (1 per 100K events/sec)
- Commands topic: 3 partitions
- Auto-scaling: Monitor broker CPU, add broker if > 70%

**Stream Processor**: Container/Pod replication
- Each replica processes 1-2 Kafka partitions
- Scaling: Horizontal (add more replicas)
- Auto-scaling trigger: ClickHouse insert queue > 10K rows

**ClickHouse**: Distributed queries
- Shard by farm_id (each farm → single shard)
- Replicate each shard 2x for HA
- Max nodes: 8 shards × 2 replicas = 16 nodes

**ML Inference**: GPU-accelerated serving
- TensorFlow Serving or TorchServe
- Batch prediction: 100-1000 samples/batch
- Scaling: Add GPU nodes as inference queue grows

### Performance Targets

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| MQTT→ClickHouse latency | < 100ms | < 150ms | P50 |
| P99 latency | < 500ms | < 600ms | Including retries |
| Throughput | 100K evt/sec | 50K evt/sec | Headroom for 2x |
| Query latency (1M rows) | < 1 sec | < 500ms | ClickHouse optimized |
| Model inference time | < 50ms | < 35ms | Per-sample |
| Batch prediction | < 5ms/sample | < 3ms/sample | 1K batch size |
| Data loss | 0 (zero) | 0 | Exactly-once semantics |

### Optimization Techniques

1. **Caching**
   - Redis: Feature cache (45-dim vectors), 1-hour TTL
   - ClickHouse: Dictionary for crop parameters (read-only)
   - Model inference: Batch predictions to amortize overhead

2. **Compression**
   - Kafka: Snappy codec (3:1 ratio)
   - ClickHouse: ZSTD (4:1 ratio)
   - Network: gzip for REST APIs

3. **Batching**
   - ClickHouse inserts: 1000-row blocks
   - Kafka consumer: Fetch 50MB batches
   - ML inference: Vectorized batch scoring

4. **Indexing & Partitioning**
   - ClickHouse: (farm_id, zone_id, timestamp) primary key
   - MongoDB: farm_id + created_at compound index
   - PostgreSQL: B-tree on farm_id, user_id

---

## Security Architecture

### Authentication & Authorization

**Users**
- System: OpenID Connect (OAuth2) with GitHub/Google/Azure AD
- API keys: JWT tokens with expiration (30-day rotation)
- Role-based access control (RBAC):
  - Admin: Full access to all farms
  - Farm Manager: Read/write for assigned farms
  - Operator: Read-only telemetry + execute approved commands
  - Viewer: Dashboard read-only

**Service-to-Service**
- Kafka: SASL/SCRAM for broker authentication
- PostgreSQL: Database roles with least privilege
- MongoDB: Database users with collection-level permissions
- ClickHouse: X.509 client certificates (optional)

### Data Encryption

**At Rest**
- PostgreSQL: Encrypted storage (dm-crypt or filesystem-level)
- MongoDB: Encrypted storage engine
- ClickHouse: Filesystem encryption (same as MongoDB)
- S3/GCS/Azure: Server-side encryption (SSE-S3, SSE-KMS)

**In Transit**
- MQTT: TLS 1.2+ with certificate pinning
- Kafka: SASL_SSL (broker↔broker, client↔broker)
- REST APIs: HTTPS with TLS 1.3
- Internal K8s: mTLS with Istio/Linkerd (optional)

### Network Security

- **Firewall**: Cloud security groups
  - Inbound: HTTPS (443), SSH (22) only
  - Outbound: NTP (123), DNS (53), HTTP (80 for external APIs)
  
- **VPC Isolation**: Private subnets for databases
  - NAT gateway for external outbound
  - No direct internet access to DB layer
  
- **API Rate Limiting**: 1000 req/min per user, 100K req/min per API key

### Compliance & Audit

- **Logging**: All API calls → PostgreSQL audit log
- **Data Retention**: Telemetry after 7 days soft-deleted, 30 days hard-deleted
- **Encryption Key Rotation**: Quarterly
- **Security Patches**: Applied within 7 days of release (critical: 24 hours)
- **GDPR Compliance**: User data export, right-to-be-forgotten (soft delete)

---

## Integration Points

### External Data Sources

**NASA Power API**
- **Data**: Daily solar radiation, temperature, precipitation forecasts
- **Integration**: NiFi scheduled fetch (daily at 00:00 UTC)
- **Endpoint**: `https://power.larc.nasa.gov/api/temporal/daily`
- **Caching**: 30-day local cache in ClickHouse
- **Fallback**: Use 10-year climate normal if API unavailable

**Weather APIs** (optional)
- OpenWeatherMap, Meteoblue, DarkSky
- 5-day forecast for local accuracy
- Trigger: Every 3 hours, before optimization cycle

**Fertilizer Supplier APIs** (optional)
- Inventory tracking
- Price fluctuation alerts
- Automated ordering threshold

### Control System Integration

**Farm Equipment Commands**
- Irrigation controllers: MQTT + REST API
- Light control: Modbus TCP / RS-485
- Climate control: BACnet / KNX
- Command validation: White-list known command types

**Legacy Databases**
- NiFi bridges to PostgreSQL, MySQL, Oracle
- Daily ETL for historical data enrichment
- Dual-write during migration period

### Visualization & Alerts

**Grafana Dashboards**
- Real-time metrics: 5-second refresh
- Custom panels: Crop health, resource use, yield forecast
- Alerting: Integrate with PagerDuty / OpsGenie

**Webhooks & Notifications**
- Email alerts for critical anomalies
- SMS for severe water stress events
- Slack integration for team notifications
- Mobile push notifications (future)

---

## Design Patterns & Principles

### Architectural Patterns

1. **Microservices**: Loosely-coupled, independently scalable components
   - Each module (stream processor, ML, cortex) can scale independently
   - API contracts via Kafka topics (event-driven communication)

2. **Event-Driven Architecture**: Kafka as event backbone
   - Decouples producers from consumers
   - Enables replay of historical events for debugging
   - Natural audit trail of all state changes

3. **CQRS (Command Query Responsibility Segregation)**
   - Commands: Write optimized (Kafka topics)
   - Queries: Read optimized (ClickHouse analytics)
   - Separate data flows for different access patterns

4. **Strangler Pattern**: Gradual migration from legacy systems
   - NiFi bridges old and new systems during transition
   - Feature flags for dual processing

5. **Circuit Breaker**: Fault tolerance for external API calls
   - NASA Power, weather APIs wrapped in retry logic
   - Fallback to cached/synthetic data if service unavailable

### Design Principles

**Robustness**
- Defensive coding: Null checks, type hints (mypy strict mode)
- Idempotency: All Kafka consumers handle duplicate messages
- Graceful degradation: Missing sensor data → interpolation, not failure

**Traceability**
- Correlation IDs: Trace single event through entire pipeline
- Structured logging: JSON format with farm_id, event_id, timestamp
- OpenTelemetry spans for distributed tracing (future)

**Testability**
- Unit tests for each module (pytest with fixtures)
- Integration tests for Kafka/ClickHouse flows
- Property-based testing for optimization algorithm (Hypothesis)

**Observability**
- Prometheus metrics: Throughput, latency, errors per component
- Structured logs: Farm-level aggregation for debugging
- Health checks: Liveness probes for container orchestration

---

## Related Documentation

- **Data Governance** → [02_DATA_GOVERNANCE.md](02_DATA_GOVERNANCE.md)
- **Data Catalog** → [03_DATA_CATALOG.md](03_DATA_CATALOG.md)
- **Deployment Guide** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Contributing Guidelines** → [CONTRIBUTING.md](CONTRIBUTING.md)

## References

- Farquhar, G. D., von Caemmerer, S., & Berry, J. A. (1980). A biochemical model of photosynthetic CO₂ assimilation in leaves of C₃ species. *Planta*, 149(1), 78-90.
- Murray, F. W. (1967). On the computation of saturation vapor pressure. *Journal of Applied Meteorology*, 6(2), 203-204.
- Haralick, R. M., Shanmugam, K., & Dinstein, I. (1973). Textural features for image classification. *IEEE Transactions on Systems, Man, and Cybernetics*, 3(6), 610-621.

---

<!-- 
================================================================================
DOCUMENT FOOTER
================================================================================
Version: 1.0.0
Last Updated: 2026-01-02 by @Mounir
Status: APPROVED ✓
Reviewed By: @Mounir, @Imrane, @Mouhammed
Next Review: 2026-04-02 (quarterly)
Related PRs: #112
Change Log: Initial creation with complete system architecture
================================================================================
-->