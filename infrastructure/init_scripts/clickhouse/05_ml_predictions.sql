-- ============================================================================
-- PROJET VERTIFLOW - Tables et Vues ML Predictions (CORRIGÉ)
-- ============================================================================
-- Date de correction : 30/01/2026
-- Correction appliquée : Conversion toDateTime() pour compatibilité TTL
-- ============================================================================

-- ============================================================================
-- TABLE 1 : PREDICTIONS DE RENDEMENT (Oracle A9)
-- ============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.predictions (
                                                     timestamp DateTime64(3, 'UTC') DEFAULT now64(3),
    batch_id String,
    zone LowCardinality(String),
    predicted_yield_g Float32,
    confidence_score Float32,
    model_version LowCardinality(String) DEFAULT 'rf_v1.0',
    features_json String DEFAULT '{}',

    INDEX idx_zone zone TYPE bloom_filter GRANULARITY 1,
    INDEX idx_batch batch_id TYPE bloom_filter GRANULARITY 1
    )
    ENGINE = MergeTree()
    PARTITION BY toYYYYMM(timestamp)
    ORDER BY (timestamp, zone, batch_id)
-- CORRECTION : Conversion obligatoire pour DateTime64
    TTL toDateTime(timestamp) + INTERVAL 90 DAY
    SETTINGS index_granularity = 8192;

-- ============================================================================
-- TABLE 2 : CLASSIFICATIONS DE QUALITE (Classifier A10)
-- ============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.quality_classifications (
                                                                 timestamp DateTime64(3, 'UTC') DEFAULT now64(3),
    batch_id LowCardinality(String),
    algo_id LowCardinality(String) DEFAULT 'A10',
    predicted_quality_grade Enum8('PREMIUM'=1, 'STANDARD'=2, 'REJECT'=3),
    health_score_input Float32,
    confidence Float32 DEFAULT 0.0,
    air_temp Float32,
    vpd Float32,
    dli Float32,
    ec Float32,
    days_since_planting UInt16,

    INDEX idx_quality_batch batch_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_quality_grade predicted_quality_grade TYPE set(3) GRANULARITY 1
    )
    ENGINE = MergeTree()
    PARTITION BY toYYYYMM(timestamp)
    ORDER BY (batch_id, timestamp)
-- CORRECTION : Conversion obligatoire pour DateTime64
    TTL toDateTime(timestamp) + INTERVAL 1 YEAR
    SETTINGS index_granularity = 8192;

-- ============================================================================
-- TABLE 3 : OPTIMISATIONS DE RECETTES (Cortex A11)
-- ============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.recipe_optimizations (
                                                              timestamp DateTime64(3, 'UTC') DEFAULT now64(3),
    recipe_id LowCardinality(String),
    zone LowCardinality(String),
    temp_opt Float32,
    humidity_opt Float32,
    ec_target Float32,
    dli_target Float32,
    co2_target Float32,
    optimization_score Float32,
    applied UInt8 DEFAULT 0,
    applied_at DateTime64(3, 'UTC') DEFAULT toDateTime64(0, 3),

    INDEX idx_recipe recipe_id TYPE bloom_filter GRANULARITY 1
    )
    ENGINE = MergeTree()
    PARTITION BY toYYYYMM(timestamp)
    ORDER BY (recipe_id, timestamp)
-- CORRECTION : Conversion obligatoire pour DateTime64
    TTL toDateTime(timestamp) + INTERVAL 2 YEAR
    SETTINGS index_granularity = 8192;

-- ============================================================================
-- TABLE 4 : HISTORIQUE DES MODELES ML
-- ============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.ml_model_history (
                                                          timestamp DateTime64(3, 'UTC') DEFAULT now64(3),
    model_name LowCardinality(String),
    model_version LowCardinality(String),
    accuracy Float32,
    precision_score Float32,
    recall_score Float32,
    f1_score Float32,
    rmse Float32,
    r2_score Float32,
    training_samples UInt32,
    training_duration_sec Float32,
    hyperparameters_json String DEFAULT '{}',
    is_active UInt8 DEFAULT 0,
    deployed_at DateTime64(3, 'UTC') DEFAULT toDateTime64(0, 3)
    )
    ENGINE = MergeTree()
    PARTITION BY toYYYYMM(timestamp)
    ORDER BY (model_name, timestamp)
    SETTINGS index_granularity = 8192;

-- ============================================================================
-- VUES ANALYTIQUES (Restées identiques car non impactées par le TTL)
-- ============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_latest_predictions AS
SELECT
    zone, batch_id, max(timestamp) as last_prediction_time,
    argMax(predicted_yield_g, timestamp) as latest_yield_prediction,
    argMax(confidence_score, timestamp) as latest_confidence,
    count() as total_predictions
FROM vertiflow.predictions
WHERE timestamp > now() - INTERVAL 7 DAY
GROUP BY zone, batch_id
ORDER BY last_prediction_time DESC;

CREATE OR REPLACE VIEW vertiflow.view_pbi_quality_stats AS
SELECT
    toStartOfHour(timestamp) as time_bucket,
    countIf(predicted_quality_grade = 'PREMIUM') as premium_count,
    countIf(predicted_quality_grade = 'STANDARD') as standard_count,
    countIf(predicted_quality_grade = 'REJECT') as reject_count,
    count() as total_classifications,
    round(countIf(predicted_quality_grade = 'PREMIUM') * 100.0 / count(), 2) as premium_rate_pct,
    avg(confidence) as avg_confidence
FROM vertiflow.quality_classifications
WHERE timestamp > now() - INTERVAL 24 HOUR
GROUP BY time_bucket
ORDER BY time_bucket DESC;

CREATE OR REPLACE VIEW vertiflow.view_pbi_model_performance AS
SELECT
    model_name,
    argMax(model_version, timestamp) as current_version,
    argMax(accuracy, timestamp) as current_accuracy,
    argMax(r2_score, timestamp) as current_r2,
    argMax(rmse, timestamp) as current_rmse,
    max(timestamp) as last_training,
    sum(training_samples) as total_samples_trained
FROM vertiflow.ml_model_history
GROUP BY model_name
ORDER BY model_name;