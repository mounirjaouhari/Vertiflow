# VertiFlow Comprehensive Data Catalog
## Document Reference: TICKET-114
**Date**: January 3, 2026  
**Version**: 1.0.0  
**Author/Team**: @Mouhammed (Data Engineer), @Mounir (Architect)  
**Status**: Production  
**Classification**: Technical - Internal  
**Last Modified**: 2026-01-03  

---

## Executive Summary

The VertiFlow Data Catalog provides a centralized, searchable inventory of all data assets within the platform. This document describes the structure, definitions, relationships, quality metrics, and ownership of datasets, data streams, and derived analytics across the vertical farming platform. The catalog serves as the single source of truth for data governance, enabling efficient data discovery, lineage tracking, and compliance management.

**Key Features:**
- Complete inventory of 150+ data assets
- Standardized metadata for each asset
- Quality scores and SLA tracking
- Data lineage and transformation tracking
- Access control and sensitivity classification
- Refresh frequency and availability SLAs

---

## Table of Contents

1. [Catalog Structure](#catalog-structure)
2. [Core Domains](#core-domains)
3. [Data Assets by Domain](#data-assets-by-domain)
4. [Asset Definitions & Specifications](#asset-definitions--specifications)
5. [Data Relationships & Lineage](#data-relationships--lineage)
6. [Quality Metrics & SLAs](#quality-metrics--slas)
7. [Asset Discovery & Search](#asset-discovery--search)
8. [Metadata Standards](#metadata-standards)

---

## 1. Catalog Structure

### 1.1 Catalog Hierarchy

```
VertiFlow Data Catalog
├─ TELEMETRY DOMAIN
│  ├─ Real-Time Streams
│  ├─ Aggregated Metrics
│  └─ Historical Archive
├─ PLANT GROWTH DOMAIN
│  ├─ Biometric Measurements
│  ├─ Growth Stage Classifications
│  └─ Growth Predictions
├─ QUALITY DOMAIN
│  ├─ Product Quality Assessments
│  ├─ Quality Metrics & KPIs
│  └─ Quality Trend Analysis
├─ OPERATIONS DOMAIN
│  ├─ System Commands & Events
│  ├─ Alerts & Notifications
│  └─ Maintenance Logs
├─ ENVIRONMENTAL DOMAIN
│  ├─ Climate Control Data
│  ├─ Resource Consumption
│  └─ Environmental Compliance
├─ FINANCIAL DOMAIN
│  ├─ Cost Tracking
│  ├─ Revenue Analysis
│  └─ ROI Calculations
└─ ML/AI DOMAIN
   ├─ Model Predictions
   ├─ Training Datasets
   └─ Feature Engineering
```

### 1.2 Asset Metadata Template

Every data asset in the catalog includes:

```
IDENTITY:
  - Asset ID (unique identifier)
  - Asset name & aliases
  - Asset type (table, stream, file, API, etc.)
  - Description (1-100 words)

OWNERSHIP:
  - Data owner (primary steward)
  - Data custodian (technical owner)
  - Contact email & phone
  - Escalation path

CLASSIFICATION:
  - Sensitivity level (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED)
  - Regulatory requirements
  - Approved use cases
  - Restricted/prohibited uses

TECHNICAL:
  - Storage location (database, table, path)
  - Format (SQL, JSON, CSV, Parquet, etc.)
  - Schema version
  - Record count & size (GB)
  - Update frequency & latency

QUALITY:
  - Quality score (0-100)
  - Last quality assessment
  - Quality issues (if any)
  - Data validation rules
  - SLA compliance (%)

AVAILABILITY:
  - SLA availability (99%, 99.5%, etc.)
  - Refresh schedule
  - Backup/recovery procedures
  - Last backup timestamp
  - Uptime metrics

LINEAGE:
  - Source systems
  - Transformation rules
  - Downstream consumers
  - Dependencies

GOVERNANCE:
  - Retention policy
  - Disposal schedule
  - Compliance mappings
  - Last review date
  - Certification status
```

---

## 2. Core Domains

### 2.1 Domain Overview

| Domain | Purpose | Owner | Steward | Assets | Quality SLA |
|---|---|---|---|---|---|
| **TELEMETRY** | Real-time sensor data collection | @Imrane | @Mouhammed | 25 | 99.5% |
| **PLANT GROWTH** | Biometric measurements & forecasts | @Asama | @Mouhammed | 18 | 99% |
| **QUALITY** | Product quality assessment & grading | @Asama | @Mouhammed | 22 | 99% |
| **OPERATIONS** | System commands, events, maintenance | @Imrane | @Imrane | 16 | 99.5% |
| **ENVIRONMENTAL** | Climate control & resource data | @Asama | @Imrane | 19 | 99% |
| **FINANCIAL** | Cost, revenue, profitability data | @MrZakaria | @Imrane | 14 | 98% |
| **ML/AI** | Model predictions & training data | @Mounir | @Mouhammed | 20 | 98% |

---

## 3. Data Assets by Domain

### 3.1 TELEMETRY DOMAIN

#### A. Real-Time Sensor Streams

**T001: mqtt-sensor-readings** (MQTT Stream)
```
Asset ID: T001
Type: Event Stream (MQTT)
Owner: @Imrane | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: JSON
Frequency: 1-second intervals (47 sensors per reading)
Volume: ~4.1M messages/day
Quality Score: 98.5%
SLA: 99.5% availability, <30sec latency

Fields:
  ├─ timestamp (DateTime, UTC)
  ├─ device_id (String, e.g., "TEMP-001")
  ├─ facility_id (String, e.g., "FAC-001")
  ├─ sensor_type (Enum: TEMPERATURE|HUMIDITY|CO2|LIGHT|etc)
  ├─ sensor_value (Float)
  ├─ sensor_unit (String, e.g., "°C", "%", "ppm")
  ├─ quality_flag (Enum: GOOD|WARNING|ERROR)
  └─ error_description (String, nullable)

Source: Mosquitto MQTT Broker (12.34.56.78:1883)
Encryption: TLS 1.3
Update Frequency: Real-time (1-second)
Retention: Hot (30 days), Warm (1 year), Archive (5 years)
Downtime Triggers: Sensor offline >5 min
Last Validation: 2026-01-03 14:00 UTC
Quality Assessment: PASSED (98.5%)
Dependencies: Mosquitto MQTT Broker
Consumers: Kafka Stream Processor, ClickHouse Ingest, Real-time Dashboard
```

**T002: kafka-telemetry-normalized** (Kafka Topic)
```
Asset ID: T002
Type: Event Stream (Kafka)
Owner: @Imrane | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: Avro (with schema evolution)
Frequency: Real-time (1-10 second aggregation)
Volume: ~350K messages/hour
Quality Score: 99.2%
SLA: 99.9% availability, <100msec latency

Fields:
  ├─ timestamp (DateTime, UTC)
  ├─ facility_id (String, partitioned on this)
  ├─ sensor_readings (Array<SensorReading>)
  │  ├─ device_id
  │  ├─ sensor_type
  │  ├─ value (normalized)
  │  ├─ unit
  │  └─ quality_flag
  ├─ processing_timestamp (DateTime)
  ├─ processor_version (String)
  └─ quality_score (Float, 0-1)

Partitions: 12 (by facility_id)
Replication: 3
Retention: 7 days
Compression: Snappy
Producers: Stream Processor (normalizer)
Consumers: ClickHouse Connector, ML Feature Engine, Analytics
```

**T003: clickhouse-telemetry-raw** (ClickHouse Table)
```
Asset ID: T003
Type: OLAP Table
Owner: @Imrane | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: ClickHouse MergeTree
Volume: 82.3 GB (30-day retention)
Record Count: 3.9B rows
Quality Score: 99.5%
SLA: 99.5% availability, <5 second query

Table: telemetry.sensor_readings_raw
Rows: 3,864,521,847
Size: 82.3 GB
Compression: ZSTD (compression ratio: 8.4:1)

Columns:
  ├─ timestamp DateTime (index)
  ├─ facility_id String (index)
  ├─ device_id String (index)
  ├─ sensor_type String
  ├─ sensor_value Float32
  ├─ sensor_unit String
  ├─ quality_flag String
  ├─ processing_timestamp DateTime
  └─ ingestion_id UInt64

Partition Key: (toYYYYMMDD(timestamp), facility_id)
Order Key: (facility_id, timestamp, device_id)
Primary Index: (facility_id, timestamp)
TTL: 30 days (auto-delete)

Sampling Strategy: 1 in 10 (for 1-second data, becomes 10-second)
Replication: 3x
Backup: Hourly snapshots
Last Backup: 2026-01-03 14:00 UTC
Backup Location: S3://vertiflow-backups/telemetry/

Consumers:
  ├─ Real-time Dashboard (aggregations)
  ├─ Daily Quality Reports
  ├─ Weekly Analytics
  └─ ML Training Pipelines (sampled)
```

#### B. Aggregated Telemetry

**T004: hourly-facility-averages** (ClickHouse Materialized View)
```
Asset ID: T004
Type: Time Series (Aggregated)
Owner: @Imrane | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: ClickHouse Table (MergeTree)
Frequency: Hourly aggregation
Volume: 547 MB (2-year retention)
Quality Score: 99.8%
SLA: 99.9% availability, <100ms query

Aggregations:
  - Temperature: avg, min, max, stdev
  - Humidity: avg, min, max, stdev
  - CO2: avg, min, max
  - Light Intensity: avg, min, max
  - Vapor Pressure Deficit (VPD): avg, percentile
  - Record count per hour

Retention: 2 years (warm storage)
Update: Hourly (via materialized view)
Backup: Daily snapshots

Fields:
  ├─ facility_id String
  ├─ hour DateTime
  ├─ avg_temperature Float32
  ├─ min_temperature Float32
  ├─ max_temperature Float32
  ├─ stdev_temperature Float32
  ├─ avg_humidity Float32
  ├─ avg_co2 Float32
  ├─ avg_light_intensity Float32
  ├─ avg_vpd Float32
  ├─ record_count UInt32
  └─ quality_score Float32

Consumers:
  ├─ Grafana Dashboards
  ├─ Daily Report Generation
  ├─ Trend Analysis
  └─ ML Feature Engineering
```

**T005: daily-facility-summary** (ClickHouse Table)
```
Asset ID: T005
Type: Daily Summary
Owner: @Imrane | Custodian: @Mouhammed
Classification: INTERNAL
Format: ClickHouse Table
Frequency: Daily (generated 06:00 UTC)
Volume: 15 MB (5-year retention)
Quality Score: 99.9%
SLA: 99% availability, <1 second query

Metrics (daily aggregates):
  - Temperature: min, avg, max, median
  - Humidity: min, avg, max
  - CO2: min, avg, max
  - Light: total DLI (Daily Light Integral)
  - VPD: average, max
  - Energy consumption (kWh)
  - Water usage (liters)
  - Alerts count (by severity)
  - Commands executed count
  - Uptime percentage

Retention: 5 years
Archival: S3 Glacier (after 1 year)

Consumers:
  ├─ Executive Dashboard
  ├─ Weekly Reports
  ├─ Long-term Trend Analysis
  └─ External Reporting (GDPR data export)
```

---

### 3.2 PLANT GROWTH DOMAIN

#### A. Biometric Measurements

**P001: daily-plant-measurements** (Database Table)
```
Asset ID: P001
Type: Transactional Table
Owner: @Asama | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: ClickHouse MergeTree
Frequency: Daily (manual measurement + auto-estimation)
Volume: 42 GB (5-year retention)
Record Count: 12.4M records
Quality Score: 97.8%
SLA: 99% availability

Fields (31 measurements per plant per day):
  ├─ plant_id String (PK, e.g., "PLT-FAC001-R01C01")
  ├─ measurement_date Date
  ├─ measurement_timestamp DateTime (time of measurement)
  ├─ measured_by String (operator ID or "AUTOMATED")
  ├─ height_cm Float32 (±2% accuracy)
  ├─ leaf_area_cm2 Float32 (from image analysis)
  ├─ stem_diameter_mm Float32
  ├─ leaf_count_total Int32
  ├─ leaf_count_green Int32
  ├─ leaf_count_damaged Int32
  ├─ biomass_g Float32 (estimated from allometry)
  ├─ fresh_weight_g Float32 (optional, destructive)
  ├─ dry_weight_g Float32 (optional, destructive)
  ├─ color_spad Int32 (chlorophyll content)
  ├─ stomatal_conductance Float32 (µmol m⁻² s⁻¹)
  ├─ photosynthesis_rate Float32 (µmol m⁻² s⁻¹)
  ├─ transpiration_rate Float32 (mmol m⁻² s⁻¹)
  ├─ growth_stage String (GERMINATION|SEEDLING|VEGETATIVE|etc)
  ├─ growth_stage_notes String
  ├─ disease_present Bool
  ├─ disease_type String (if present)
  ├─ pest_present Bool
  ├─ pest_type String (if present)
  ├─ nutrient_deficiency Bool
  ├─ deficiency_type String (if present)
  ├─ harvest_ready Bool
  ├─ days_to_harvest_estimated Int32
  ├─ quality_assessment String (PREMIUM|A|B|REJECT)
  ├─ quality_score Float32 (0-100)
  ├─ environmental_conditions JSON
  ├─ measurement_method String (MANUAL|AUTOMATED|HYBRID)
  ├─ measurement_error_flag String (GOOD|WARNING|ERROR)
  └─ notes String

Data Sources:
  ├─ Manual measurements: Daily by @Asama team
  ├─ Image analysis: Automated computer vision (3x/day)
  ├─ Spectral sensors: Automated SPAD readings (hourly)
  └─ Environmental integration: From telemetry domain

Quality Validation Rules:
  1. Height monotonically increasing (or stable if mature)
  2. Leaf area proportional to plant age
  3. No retroactive timestamps (forward-only)
  4. Growth stage sequence validation
  5. Outlier detection (±3σ from cohort)
  6. Cross-validation with biomass estimates

Partitions: (toYYYYMM(measurement_date), plant_id)
TTL: 5 years with S3 archival after 1 year
Backup: Daily snapshots

Consumers:
  ├─ Growth Prediction Model (P003)
  ├─ Quality Assessment (Q001)
  ├─ Optimization Engine (ML)
  ├─ Executive Dashboard
  └─ Research Publications
```

**P002: growth-tracking-history** (Time Series)
```
Asset ID: P002
Type: Time Series (Derived)
Owner: @Asama | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: ClickHouse Table
Frequency: Daily aggregation
Volume: 2.1 GB (historical)
Quality Score: 99.2%
SLA: 99% availability

Provides historical trend lines:
  - Height progression (cm/day growth rate)
  - Biomass accumulation (g/day)
  - Leaf area expansion (cm²/day)
  - Growth stage timeline
  - Quality score trajectory

Retention: 5 years
Used For: Trend analysis, anomaly detection, forecasting

Consumers:
  ├─ Growth Prediction Model
  ├─ Analytics Reports
  └─ Research Analysis
```

#### B. Growth Predictions

**P003: growth-forecast-predictions** (ML Model Output)
```
Asset ID: P003
Type: Prediction Dataset
Owner: @Mounir | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: ClickHouse Table
Frequency: Daily (updated 05:00 UTC)
Volume: 850 MB (2-year retention)
Record Count: 5.2M predictions
Quality Score: 96.5%
SLA: 98% availability

Fields:
  ├─ plant_id String (PK)
  ├─ forecast_date Date
  ├─ prediction_timestamp DateTime
  ├─ days_ahead Int32 (1, 2, 3, 5, 7, 14)
  ├─ predicted_height_cm Float32
  ├─ predicted_height_std Float32 (uncertainty)
  ├─ predicted_biomass_g Float32
  ├─ predicted_biomass_std Float32
  ├─ predicted_quality_score Float32
  ├─ predicted_harvest_readiness_date Date
  ├─ harvest_confidence Float32 (0-1)
  ├─ model_version String (e.g., "LSTM-v2.3.1")
  ├─ model_mape Float32 (mean absolute % error)
  ├─ training_accuracy Float32
  ├─ model_confidence Float32 (0-1)
  ├─ prediction_status String (VALID|NEEDS_RETRAINING|FAILED)
  ├─ model_last_retrain_date Date
  └─ notes String

ML Model Details:
  - Type: LSTM (Long Short-Term Memory) Neural Network
  - Training data: 2+ years historical measurements
  - Features: Temperature, humidity, light, nutrients, biomass, growth stage
  - Retraining: Weekly on new data
  - Validation MAPE: 8.3% (height), 12.1% (biomass)
  - Validation R²: 0.92 (height), 0.87 (biomass)
  - Framework: TensorFlow 2.11 / PyTorch 2.0

Quality Thresholds:
  - Use prediction only if confidence > 0.75
  - Flag for review if MAPE > 15%
  - Retrain if accuracy drops below 85%

Consumers:
  ├─ Optimization Engine (resource allocation)
  ├─ Harvest Planning (P005)
  ├─ Yield Forecasting Dashboard
  └─ Executive Planning
```

**P004: cohort-growth-analysis** (Aggregated Analytics)
```
Asset ID: P004
Type: Analytical Summary
Owner: @Asama | Custodian: @Mouhammed
Classification: INTERNAL
Format: ClickHouse Table
Frequency: Daily aggregation
Volume: 120 MB (2-year retention)
Quality Score: 99.5%
SLA: 99% availability

Provides cohort-level statistics:
  - Cohort ID & planting date
  - Number of plants in cohort
  - Average height, biomass, leaf area
  - Height/biomass percentiles (25%, 50%, 75%, 95%)
  - Growth rates (cm/day, g/day)
  - Uniformity metrics (coefficient of variation)
  - Quality grade distribution
  - Days to harvest (estimated)
  - Expected yield

Retention: 2 years
Update: Daily (06:00 UTC)

Consumers:
  ├─ Decision Support System
  ├─ Executive Dashboard
  ├─ Operations Planning
  └─ Financial Forecasting
```

---

### 3.3 QUALITY DOMAIN

#### A. Quality Assessments

**Q001: product-quality-assessment** (Transaction Table)
```
Asset ID: Q001
Type: Transactional Table
Owner: @Asama | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: ClickHouse MergeTree
Frequency: Per-harvest/product (multiple per day)
Volume: 15 GB (5-year retention)
Record Count: 8.7M records
Quality Score: 98.9%
SLA: 99% availability

Fields (Quality Grading):
  ├─ assessment_id UUID (PK)
  ├─ product_id String (unique product identifier)
  ├─ assessment_timestamp DateTime
  ├─ assessed_by String (operator name/ID)
  ├─ assessment_method String (MANUAL|AUTOMATED|HYBRID)
  ├─ plant_source_id String (FK to P001)
  ├─ cohort_id String (FK)
  ├─ harvest_date Date
  ├─ weight_g Float32
  ├─ color_score Float32 (0-100, visual assessment)
  ├─ texture_score Float32 (0-100, tactile assessment)
  ├─ defect_count Int32
  ├─ defect_types Array(String) (e.g., ["bruise", "yellowing"])
  ├─ disease_present Bool
  ├─ pest_damage Bool
  ├─ overall_quality_score Float32 (0-100)
  ├─ grade String (PREMIUM|GRADE_A|GRADE_B|REJECT)
  ├─ marketability String (MARKET|SECONDS|COMPOST|REJECT)
  ├─ estimated_shelf_life_days Int32
  ├─ recommendation String (FOR_SALE|PROCESSING|DISPOSAL)
  ├─ classifier_model_version String
  ├─ classifier_confidence Float32 (0-1)
  ├─ reviewed_by String (quality auditor, if reviewed)
  ├─ review_status String (PENDING|APPROVED|FLAGGED)
  ├─ review_timestamp DateTime
  ├─ review_notes String
  └─ environmental_context JSON

Quality Grading Scale:
  ```
  PREMIUM (95-100): Perfect, premium market
  GRADE_A (85-94): Minor cosmetic imperfections only
  GRADE_B (70-84): Observable defects, acceptable quality
  REJECT (<70): Not suitable for market
  ```

Defect Categories:
  - Color: pale, yellowing, browning, mottled
  - Shape: irregular, stunted, oversized
  - Texture: wilted, limp, rubbery, mushy
  - Damage: bruising, cuts, holes, pest damage
  - Disease: powdery mildew, botrytis, bacterial spots
  - Contamination: debris, insects, residue

Data Quality:
  - Grade consistency checks (multiple assessors)
  - Confidence thresholds enforced
  - Appeal/override process documented
  - Regular auditor calibration

Consumers:
  ├─ Q002 (Quality Metrics)
  ├─ Financial Dashboard (revenue by grade)
  ├─ Customer Quality Reports
  └─ ML Model Training (classifier)
```

**Q002: daily-quality-metrics** (Aggregated KPIs)
```
Asset ID: Q002
Type: Daily Summary KPI
Owner: @Asama | Custodian: @Mouhammed
Classification: INTERNAL
Format: ClickHouse Table
Frequency: Daily (generated 21:00 UTC)
Volume: 18 MB (5-year retention)
Quality Score: 99.8%
SLA: 99% availability

Daily Quality KPIs:
  - Total products assessed
  - Grade distribution (%, count)
  - Average quality score
  - Rejection rate (%)
  - Defect frequency (top 5 defects)
  - Consistency metrics
  - Shelf-life estimates
  - Marketability percentage
  - Trend vs. 7-day average
  - Trend vs. 30-day average

Retention: 5 years
Archival: S3 after 1 year

Consumers:
  ├─ Executive Dashboard
  ├─ Weekly Quality Reports
  ├─ Financial/Revenue Analysis
  └─ Trend Analysis
```

#### B. Quality ML Models

**Q003: quality-classifier-predictions** (ML Output)
```
Asset ID: Q003
Type: ML Prediction Output
Owner: @Mounir | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: JSON (streaming) + ClickHouse (batched)
Frequency: Real-time (per product scanned)
Volume: 2.3 GB/year
Quality Score: 96.2%
SLA: 98% availability, <5sec latency

ML Model Specifications:
  - Type: Convolutional Neural Network (ResNet-50 backbone)
  - Training data: 150K+ hand-labeled images
  - Framework: PyTorch 2.0 + TensorFlow
  - Input: RGB images (1280x720 minimum)
  - Output: Grade (PREMIUM|A|B|REJECT) + confidence
  - Validation accuracy: 97.3%
  - Validation F1-score: 0.964

Fields:
  ├─ prediction_id UUID
  ├─ product_id String (FK)
  ├─ image_path String (S3 location)
  ├─ prediction_timestamp DateTime
  ├─ predicted_grade String
  ├─ grade_confidence Float32 (0-1)
  ├─ defect_detections Array<Defect>
  │  ├─ defect_type String
  │  ├─ confidence Float32
  │  ├─ bounding_box (x, y, width, height)
  │  └─ severity (LOW|MED|HIGH)
  ├─ color_score Float32 (0-100)
  ├─ texture_analysis JSON
  ├─ model_version String
  ├─ processing_time_ms Int32
  ├─ gpu_utilization Float32
  └─ notes String

Consumers:
  ├─ Real-time Quality Monitoring
  ├─ Automated Sorting System (commands)
  ├─ Q001 (Quality Assessment input)
  └─ Quality Optimization
```

---

### 3.4 OPERATIONS DOMAIN

#### A. System Events

**O001: system-commands-log** (Event Stream)
```
Asset ID: O001
Type: Event Log
Owner: @Imrane | Custodian: @Imrane
Classification: CONFIDENTIAL
Format: Kafka Topic → ClickHouse Table
Frequency: Real-time (per command)
Volume: 1.8 GB/month
Record Count: 125K commands/day
Quality Score: 99.7%
SLA: 99.5% availability

Fields:
  ├─ command_id UUID (PK)
  ├─ command_timestamp DateTime
  ├─ command_type String (TEMPERATURE|HUMIDITY|LIGHT|NUTRIENT|etc)
  ├─ facility_id String
  ├─ device_id String
  ├─ action String (SET|INCREASE|DECREASE|TOGGLE|etc)
  ├─ parameter_name String
  ├─ target_value Float32
  ├─ target_unit String
  ├─ issued_by String (user/system)
  ├─ approval_required Bool
  ├─ approved_by String (if required)
  ├─ approval_timestamp DateTime
  ├─ execution_timestamp DateTime
  ├─ execution_status String (PENDING|EXECUTING|SUCCESS|FAILED)
  ├─ error_message String (if failed)
  └─ notes String

Retention: 5 years
Archive: S3 after 1 year

Consumers:
  ├─ Operations Audit Trail
  ├─ Compliance Reporting
  ├─ Environmental Reconstruction
  └─ Issue Diagnostics
```

**O002: system-alerts-log** (Event Stream)
```
Asset ID: O002
Type: Alert Event Log
Owner: @Imrane | Custodian: @Imrane
Classification: INTERNAL
Format: Kafka Topic → ClickHouse Table
Frequency: Real-time
Volume: 3.2 GB/month
Record Count: 18K alerts/day
Quality Score: 99.5%
SLA: 99.5% availability

Fields:
  ├─ alert_id UUID (PK)
  ├─ alert_timestamp DateTime
  ├─ facility_id String
  ├─ alert_type String (SENSOR_OFFLINE|TEMPERATURE_OOB|etc)
  ├─ severity String (INFO|WARNING|CRITICAL)
  ├─ message String
  ├─ affected_resource String
  ├─ threshold_value Float32 (what triggered alert)
  ├─ current_value Float32 (actual reading)
  ├─ auto_remediation_attempted Bool
  ├─ auto_remediation_success Bool
  ├─ manual_action_required Bool
  ├─ assigned_to String (operator)
  ├─ resolution_timestamp DateTime
  ├─ resolution_notes String
  └─ escalation_level Int32

Retention: 2 years
Archive: S3 after 1 year

Consumers:
  ├─ Real-time Alerting Dashboard
  ├─ Operations Management
  ├─ Maintenance Scheduling
  └─ SLA Tracking
```

#### C. Maintenance Logs

**O003: maintenance-log** (Transactional)
```
Asset ID: O003
Type: Maintenance Records
Owner: @Imrane | Custodian: @Imrane
Classification: INTERNAL
Format: ClickHouse Table
Frequency: As-needed (per maintenance event)
Volume: 45 MB (5-year retention)
Record Count: 45K records
Quality Score: 99.8%
SLA: 99% availability

Fields:
  ├─ maintenance_id UUID (PK)
  ├─ facility_id String
  ├─ device_id String
  ├─ maintenance_date DateTime
  ├─ maintenance_type String (PREVENTIVE|CORRECTIVE|EMERGENCY)
  ├─ performed_by String (technician)
  ├─ work_description String
  ├─ parts_replaced Array(String)
  ├─ downtime_minutes Int32
  ├─ cost_usd Float32
  ├─ device_status_before String (GOOD|DEGRADED|FAILED)
  ├─ device_status_after String
  ├─ estimated_next_service Date
  ├─ approval_status String (PENDING|APPROVED|COMPLETED)
  └─ notes String

Retention: 5 years
Used For: Preventive maintenance scheduling, cost tracking

Consumers:
  ├─ Maintenance Planning
  ├─ Financial Tracking
  └─ Equipment Reliability Analysis
```

---

### 3.5 ENVIRONMENTAL DOMAIN

#### A. Climate Control Data

**E001: climate-control-setpoints** (Configuration)
```
Asset ID: E001
Type: Configuration/Setpoint Data
Owner: @Asama | Custodian: @Imrane
Classification: CONFIDENTIAL
Format: ClickHouse Table
Frequency: Daily (when changed, or daily snapshot)
Volume: 85 MB (2-year retention)
Quality Score: 99.9%
SLA: 99% availability

Fields:
  ├─ facility_id String (PK)
  ├─ effective_date Date
  ├─ crop_stage String (GERMINATION|SEEDLING|etc)
  ├─ temperature_target_c Float32
  ├─ temperature_min_c Float32
  ├─ temperature_max_c Float32
  ├─ humidity_target_pct Float32
  ├─ humidity_min_pct Float32
  ├─ humidity_max_pct Float32
  ├─ co2_target_ppm Float32
  ├─ co2_min_ppm Float32
  ├─ co2_max_ppm Float32
  ├─ light_target_dli_moles Float32 (Daily Light Integral)
  ├─ light_photoperiod_hours Int32
  ├─ light_start_time String (HH:MM UTC)
  ├─ nutrient_ec_target Float32 (electrical conductivity)
  ├─ nutrient_ph_target Float32
  ├─ vpd_target_kpa Float32 (Vapor Pressure Deficit)
  ├─ vpd_min_kpa Float32
  ├─ vpd_max_kpa Float32
  ├─ set_by String (agronomist)
  ├─ approval_status String
  ├─ approved_by String
  ├─ change_reason String
  └─ notes String

Retention: 2 years
Source: @Asama (biologist) specifications

Consumers:
  ├─ Climate Control System
  ├─ Optimization Engine
  ├─ Quality Assessment
  └─ Environmental Compliance Reports
```

#### B. Resource Consumption

**E002: facility-energy-consumption** (Meter Data)
```
Asset ID: E002
Type: Resource Consumption
Owner: @Imrane | Custodian: @Imrane
Classification: INTERNAL
Format: ClickHouse Table
Frequency: Hourly metering
Volume: 1.2 GB (5-year retention)
Record Count: 438K readings
Quality Score: 99.6%
SLA: 99% availability

Fields:
  ├─ facility_id String (PK)
  ├─ measurement_hour DateTime
  ├─ electricity_kwh Float32 (total facility)
  ├─ heating_kwh Float32 (HVAC heating)
  ├─ cooling_kwh Float32 (HVAC cooling)
  ├─ lighting_kwh Float32 (grow lights)
  ├─ irrigation_kwh Float32 (pumps)
  ├─ other_kwh Float32 (misc)
  ├─ total_kwh Float32
  ├─ cost_usd Float32 (based on utility rate)
  ├─ carbon_kg_co2 Float32 (estimated emissions)
  ├─ meter_reading_timestamp DateTime
  ├─ meter_status String (GOOD|ERROR)
  └─ notes String

Retention: 5 years
Cost Per Record: ~$0.015 (at $0.12/kWh average)

Consumers:
  ├─ Financial Dashboard (cost tracking)
  ├─ Sustainability Reports
  ├─ Optimization Analysis (energy efficiency)
  └─ Executive Reporting
```

**E003: water-consumption-log** (Meter Data)
```
Asset ID: E003
Type: Resource Consumption
Owner: @Asama | Custodian: @Imrane
Classification: INTERNAL
Format: ClickHouse Table
Frequency: Hourly metering
Volume: 320 MB (5-year retention)
Quality Score: 99.7%
SLA: 99% availability

Fields:
  ├─ facility_id String
  ├─ measurement_hour DateTime
  ├─ irrigation_liters Float32
  ├─ nutrient_solution_liters Float32
  ├─ cleaning_liters Float32
  ├─ other_liters Float32
  ├─ total_liters Float32
  ├─ recycled_liters Float32 (irrigation recycling rate)
  ├─ waste_liters Float32
  ├─ cost_usd Float32
  ├─ meter_status String
  └─ notes String

Retention: 5 years
Used For: Sustainability, cost tracking, efficiency analysis

Consumers:
  ├─ Financial Dashboard
  ├─ Sustainability Reporting
  └─ Resource Optimization
```

---

### 3.6 FINANCIAL DOMAIN

#### A. Cost Tracking

**F001: operational-costs** (Transaction Table)
```
Asset ID: F001
Type: Financial Transaction
Owner: @MrZakaria | Custodian: @Imrane
Classification: CONFIDENTIAL
Format: ClickHouse Table
Frequency: Daily (per cost entry)
Volume: 890 MB (10-year retention)
Quality Score: 99.8%
SLA: 99% availability

Fields:
  ├─ cost_id UUID (PK)
  ├─ facility_id String
  ├─ cost_date Date
  ├─ cost_category String (UTILITIES|LABOR|MATERIALS|MAINTENANCE|etc)
  ├─ cost_subcategory String
  ├─ description String
  ├─ amount_usd Float32
  ├─ currency String (USD default)
  ├─ vendor String
  ├─ invoice_number String
  ├─ invoice_date Date
  ├─ payment_date Date
  ├─ allocated_cohort_id String (FK, if applicable)
  ├─ cost_driver String (LABOR_HOURS|ENERGY_KWH|etc)
  ├─ driver_value Float32
  ├─ unit_cost Float32 (cost per driver)
  ├─ approved_by String
  ├─ notes String
  └─ gl_account_code String

Retention: 10 years (for financial audit)
Archival: S3 after 3 years

Consumers:
  ├─ Financial Dashboard
  ├─ Cost Analysis
  ├─ Profitability Reports
  ├─ Tax/Audit Compliance
  └─ Forecasting Models
```

#### B. Revenue Tracking

**F002: sales-and-revenue** (Transaction Table)
```
Asset ID: F002
Type: Financial Transaction
Owner: @MrZakaria | Custodian: @Imrane
Classification: CONFIDENTIAL
Format: ClickHouse Table
Frequency: Per sale (multiple daily)
Volume: 1.1 GB (10-year retention)
Record Count: 847K sales records
Quality Score: 99.9%
SLA: 99% availability

Fields:
  ├─ sale_id UUID (PK)
  ├─ facility_id String
  ├─ sale_date DateTime
  ├─ product_id String (FK to Q001)
  ├─ product_grade String (PREMIUM|A|B)
  ├─ quantity_kg Float32
  ├─ unit_price_usd Float32
  ├─ total_revenue_usd Float32
  ├─ customer_id String (anonymized)
  ├─ customer_type String (RETAIL|WHOLESALE|DIRECT)
  ├─ sales_channel String (FARMER_MARKET|WHOLESALE|etc)
  ├─ harvest_cohort_id String (FK)
  ├─ profit_margin_usd Float32
  ├─ profit_margin_pct Float32
  ├─ shipped_date Date
  ├─ payment_status String (PAID|PENDING|OVERDUE)
  ├─ payment_received_date Date
  └─ notes String

Retention: 10 years
Archival: S3 after 3 years

Consumers:
  ├─ Financial Dashboard
  ├─ Revenue Analysis
  ├─ Profitability Reports
  ├─ Forecasting Models
  └─ Customer Analytics
```

---

### 3.7 ML/AI DOMAIN

#### A. ML Model Predictions

**M001: harvest-optimization-predictions** (ML Output)
```
Asset ID: M001
Type: ML Prediction
Owner: @Mounir | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: ClickHouse Table
Frequency: Daily (updated 04:00 UTC)
Volume: 560 MB (2-year retention)
Quality Score: 97.1%
SLA: 98% availability

ML Model: Random Forest Regressor
  - Features: 127 (temperature, humidity, light, nutrients, etc.)
  - Training data: 3+ years historical data
  - Validation RMSE: 2.3 days
  - Validation R²: 0.89

Predictions:
  ├─ plant_id String (PK)
  ├─ prediction_date Date
  ├─ optimal_harvest_date Date
  ├─ harvest_date_lower_bound Date (95% confidence)
  ├─ harvest_date_upper_bound Date
  ├─ expected_weight_g Float32
  ├─ expected_quality_grade String
  ├─ confidence_score Float32 (0-1)
  ├─ model_version String
  ├─ model_retraining_needed Bool
  └─ recommendation String

Used For:
  - Production scheduling
  - Resource allocation
  - Quality optimization
  - Revenue forecasting

Consumers:
  ├─ Operations Planning
  ├─ Sales/Revenue Forecasting
  ├─ Quality Assurance
  └─ Optimization Engine
```

#### B. Training Datasets

**M002: ml-training-data-snapshot** (Training Set)
```
Asset ID: M002
Type: ML Training Dataset
Owner: @Mounir | Custodian: @Mouhammed
Classification: CONFIDENTIAL
Format: Parquet (columnar compression)
Frequency: Weekly snapshots
Volume: 8.4 GB (versioned)
Record Count: 12.4M samples
Quality Score: 99.3%
SLA: 98% availability

Dataset Composition:
  - Historical telemetry: 80%
  - Plant measurements: 15%
  - Environmental: 5%
  - Time range: 36 months historical
  - Features: 127 standardized features
  - Target variables: 8 (growth, quality, harvest, etc.)

Quality Controls:
  - Missing value imputation: Forward-fill + interpolation
  - Outlier removal: IQR method
  - Feature scaling: StandardScaler (fit on training split)
  - Data leakage checks: Temporal validation
  - Class imbalance: SMOTE resampling
  - Cross-validation: 5-fold temporal
  
Train/Val/Test Split: 60% / 20% / 20%
Time-based split: Prevents future data leakage

Retention: All versions (100 snapshots)
Version Control: Git-based (DVC)

Used For:
  - Model training (weekly retraining)
  - Model validation and testing
  - Feature engineering experimentation
  - Research and analysis

Consumers:
  ├─ ML Pipeline (automated retraining)
  ├─ Model Development
  ├─ Research Projects
  └─ Data Science Team
```

---

## 4. Asset Definitions & Specifications

### 4.1 Data Type Specifications

**Numeric Specifications:**

```
Temperature (°C):
  Range: -5 to 40°C
  Precision: ±0.5°C
  Format: Float32
  Display: 1 decimal place
  Validation: Must be within growth range for species

Humidity (%):
  Range: 0 to 100%
  Precision: ±2%
  Format: Float32
  Display: Integer (0-100)
  Validation: No negative, max 100

CO2 (ppm):
  Range: 250 to 2000 ppm
  Precision: ±50 ppm
  Format: Float32
  Display: Integer
  Validation: Must be > 250 (min atmospheric)

Light Intensity (µmol m⁻² s⁻¹):
  Range: 0 to 3000 µmol/m²/s
  Precision: ±30 µmol/m²/s
  Format: Float32
  Display: Integer
  Validation: Proportional to light source

VPD (kPa):
  Range: 0.2 to 6.0 kPa
  Precision: ±0.1 kPa
  Format: Float32
  Display: 1 decimal place
  Validation: Calculated from temp + humidity

Biomass (g):
  Range: 0.1 to 500g
  Precision: ±2%
  Format: Float32
  Display: 1 decimal place
  Validation: Monotonically increasing (or stable)

Quality Score (0-100):
  Range: 0 to 100
  Precision: Integer
  Format: Int32
  Display: 0-100 with grade mapping
  Validation: Must fall within valid distribution
```

### 4.2 Quality Metrics by Asset

**Quality Score Calculation Framework:**

```
For Telemetry Assets (T001-T005):
  Quality = (Accuracy × 0.30) + 
            (Completeness × 0.25) + 
            (Timeliness × 0.20) + 
            (Consistency × 0.20) + 
            (Validity × 0.05)

For Plant Growth Assets (P001-P004):
  Quality = (Measurement Accuracy × 0.35) + 
            (Completeness × 0.25) + 
            (Prediction Accuracy × 0.20) + 
            (Timeliness × 0.15) + 
            (Validation × 0.05)

For Quality Assets (Q001-Q003):
  Quality = (Grading Consistency × 0.40) + 
            (Completeness × 0.25) + 
            (Model Accuracy × 0.20) + 
            (Timeliness × 0.10) + 
            (Appeal Resolution × 0.05)

For Financial Assets (F001-F002):
  Quality = (Reconciliation Match × 0.40) + 
            (Completeness × 0.30) + 
            (Timeliness × 0.20) + 
            (Audit Compliance × 0.10)
```

---

## 5. Data Relationships & Lineage

### 5.1 Data Lineage Diagram

```
MQTT Sensor Data (T001)
  ↓ (Real-time streaming)
Kafka Stream (T002: kafka-telemetry-normalized)
  ├─ Stream: Climate Control Optimization (E001)
  ├─ Stream: Quality Assessment Input (Q001)
  ├─ Stream: ML Feature Engineering (M002)
  └─ Stream: Real-time Dashboard
  │
  ↓ (Hourly ingestion)
ClickHouse Telemetry (T003: clickhouse-telemetry-raw)
  ├─→ Hourly Aggregates (T004)
  │    └─→ Daily Summary (T005)
  │        └─→ Executive Dashboard
  │
  ├─→ Plant Growth Analysis
  │    Plant Measurements (P001)
  │    └─→ Growth Tracking (P002)
  │        └─→ Predictions (P003)
  │            └─→ Harvest Optimization (M001)
  │                └─→ Production Planning
  │
  ├─→ Quality Assessment
  │    Quality Assessments (Q001)
  │    ├─→ Classifier Predictions (Q003)
  │    └─→ Daily Quality Metrics (Q002)
  │        └─→ Revenue Impact Analysis
  │
  └─→ Financial Impact
       Energy/Water Consumption (E002, E003)
       └─→ Operational Costs (F001)
           └─→ Profitability Analysis (F002)

Data Flow Example (Daily Harvest):
  Plant Growth Measurements (manual + auto) → P001
         ↓
  Growth Analysis/Predictions → P003
         ↓
  Quality Classification → Q001 + Q003
         ↓
  Quality Grading (PREMIUM|A|B|REJECT) → Q002
         ↓
  Sales Transaction → F002
         ↓
  Revenue Recognition / Cost Absorption → Financial Reports
```

### 5.2 Dependency Matrix

```
Asset    | Depends On              | Consumed By
─────────┼─────────────────────────┼──────────────────
T001     | MQTT Broker             | T002, T003
T002     | T001                    | T003, Q001, M002
T003     | T002                    | T004, T005, P001
T004     | T003                    | Dashboard, Analytics
T005     | T004                    | Executive Reports
────────────────────────────────────────────────────
P001     | T003, Manual Input      | P002, P003, Q001
P002     | P001                    | Analytics, Trends
P003     | P001, T003              | M001, Forecasting
P004     | P001                    | Decision Support
────────────────────────────────────────────────────
Q001     | P001, T002, Manual      | Q002, Q003, F002
Q002     | Q001                    | Dashboard, Reports
Q003     | Image Input, Q001       | Quality Sorting
────────────────────────────────────────────────────
O001     | User Actions            | Audit Trail
O002     | System Monitoring       | Alerts, Dashboard
O003     | Manual Entry            | Maintenance Planning
────────────────────────────────────────────────────
E001     | @Asama Specifications   | Climate System
E002     | Energy Meter            | Cost Analysis
E003     | Water Meter             | Sustainability
────────────────────────────────────────────────────
F001     | Vendor Invoices         | Profitability
F002     | Q001, E002, E003        | Financial Reports
────────────────────────────────────────────────────
M001     | P003, T003              | Production Plan
M002     | T003, P001, E002        | ML Model Training
M003     | Various historical      | Model Development
```

---

## 6. Quality Metrics & SLAs

### 6.1 SLA Matrix

| Asset | Availability | Latency | Accuracy | Data Age | Recovery |
|---|---|---|---|---|---|
| T001 (MQTT) | 99.5% | <30s | 98.5% | Real-time | 5 min |
| T002 (Kafka) | 99.9% | <100ms | 99.2% | Real-time | 1 min |
| T003 (ClickHouse) | 99.5% | <5s | 99.5% | <10min | 1 hour |
| P001 (Growth) | 99% | <24h | 97.8% | Daily | 4 hours |
| Q001 (Quality) | 99% | <5min | 98.9% | Real-time | 1 hour |
| F001 (Costs) | 99% | <24h | 99.8% | Daily | 4 hours |
| M001 (Predictions) | 98% | <1h | 97.1% | Daily | 2 hours |

### 6.2 Monitoring & Alerting

**Alerting Thresholds:**

```
Asset: T001 (MQTT Telemetry)
  ├─ Alert if: Availability < 95% (SLA: 99.5%)
  ├─ Alert if: Latency > 60s (SLA: <30s)
  ├─ Alert if: Data quality < 90% (SLA: 98.5%)
  └─ Alert if: Messages/minute < 100 (baseline)

Asset: P001 (Plant Growth)
  ├─ Alert if: Daily update not received by 15:00 UTC
  ├─ Alert if: Quality score < 90% (SLA: 97.8%)
  ├─ Alert if: Completeness < 95%
  └─ Alert if: Outliers > 5% of records

Asset: Q001 (Quality Assessments)
  ├─ Alert if: Assessment latency > 10 minutes
  ├─ Alert if: Classifier confidence < 75%
  ├─ Alert if: Manual override rate > 10%
  └─ Alert if: Grade distribution anomaly detected

Monitoring Frequency:
  ├─ Real-time metrics: Continuous (Kafka/Telegraf)
  ├─ Asset quality: Hourly assessment
  ├─ SLA tracking: Daily reports
  └─ Trend analysis: Weekly review
```

---

## 7. Asset Discovery & Search

### 7.1 Search Capabilities

The catalog supports search by:

- **Asset Name/ID**: Exact or wildcard matching
- **Classification**: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
- **Domain**: TELEMETRY, GROWTH, QUALITY, etc.
- **Owner**: @Mounir, @Imrane, @Mouhammed, @Asama, @MrZakaria
- **Data Type**: Time series, Transaction, Aggregated, ML output
- **Quality Score**: Range filters (e.g., ≥95%)
- **Update Frequency**: Real-time, hourly, daily, weekly
- **Consumers**: Downstream applications/dashboards
- **Free Text**: Full-text search in descriptions

**Example Queries:**
```
"CONFIDENTIAL" AND "QUALITY" AND owner:"@Asama"
  → Find all confidential quality assessment assets owned by @Asama

"@Mounir" AND quality_score:">95"
  → Find high-quality assets owned by @Mounir

"TELEMETRY" AND frequency:"Real-time"
  → Find all real-time telemetry streams
```

---

## 8. Metadata Standards

### 8.1 Metadata Governance

**Metadata Stewardship:**

```
Metadata Element | Owner | Update Frequency | Governance
─────────────────┼───────┼──────────────────┼────────────
Asset Name/ID   | Arch  | Ad-hoc (rarely)  | Change control
Description     | Owner | Annually         | Data owner review
Classification  | Owner | Quarterly        | Governance council
Technical Spec  | Cust  | As-needed        | Change management
Quality Metrics | Cust  | Continuous       | Automated monitoring
SLAs            | Owner | Annually         | Executive approval
Lineage         | Arch  | As-needed        | Design review
Retention       | Owner | Annually         | Governance council
```

**Metadata Quality Standards:**

```
Every asset must have:
  ✓ Unique ID (UUID or name-based)
  ✓ Clear 1-2 line description (mandatory)
  ✓ Classification level (required)
  ✓ Data owner assignment (required)
  ✓ Data custodian assignment (required)
  ✓ Schema definition (for structured data)
  ✓ Quality metrics (current score & trend)
  ✓ SLA targets (availability, latency, accuracy)
  ✓ Update frequency documented
  ✓ Lineage (upstream sources & downstream consumers)
  ✓ Retention schedule
  ✓ Last review/certification date
  ✓ Contact information for support
```

---

## References

1. **ISO/IEC 11179** - Metadata Registry
2. **DAMA-DMBOK** - Data Management Body of Knowledge
3. **Gartner Data Management Framework**
4. **NIST Data Catalog Standards**
5. **Apache Atlas Documentation** - Metadata Governance
6. **Collibra Enterprise Cloud** - Data Catalog Platform

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-03 | @Mouhammed | Initial creation |
| | | | |

---

**Document Footer**

```
TICKET: TICKET-114
ASSIGNED TO: @Mouhammed (Data Engineer), @Mounir (Architect)
TEAM: @Mouhammed, @Mounir, @Imrane, @Asama, @MrZakaria
PROJECT: VertiFlow Data Platform - Intelligent Vertical Farming
STATUS: Production Release
CLASSIFICATION: Technical - Internal
NEXT REVIEW: 2026-04-03 (Quarterly)
SUPPORT: Contact @Mouhammed for data catalog questions
REPOSITORY: J-Mounir/test-projet-agri (GitHub)
```

---

*This document is controlled and subject to change management procedures.*
*Last updated: 2026-01-03 | Next scheduled review: 2026-04-03*
