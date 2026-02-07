-- Création des 7 tables de référence ClickHouse pour Zone 5
-- Exécuter sur localhost:9000 database vertiflow

-- 1. Recettes lumineuses (Light spectra recipes)
CREATE TABLE IF NOT EXISTS vertiflow.ref_light_spectra (
    spectrum_id String,
    name String,
    red_ratio Float32,
    blue_ratio Float32,
    green_ratio Float32,
    ir_ratio Float32,
    ppfd_target Float32,
    daily_photoperiod_hours UInt8,
    spectrum_notes String,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (spectrum_id, created_date)
COMMENT 'Light spectral recipes for LED racks';

-- 2. Mesures nutriments (Nutrient measurements reference)
CREATE TABLE IF NOT EXISTS vertiflow.ref_nutrient_measurements (
    measurement_id String,
    nutrient_name String,
    element_symbol String,
    target_ppm Float32,
    min_ppm Float32,
    max_ppm Float32,
    safety_range_percent Float32,
    optimal_ratio Float32,
    nutrient_source String,
    deficiency_symptoms String,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (nutrient_name, created_date)
COMMENT 'Reference nutrient measurements and targets';

-- 3. Profils aromatiques (Aroma profiles from GC-MS)
CREATE TABLE IF NOT EXISTS vertiflow.ref_aroma_profiles (
    aroma_id String,
    compound_name String,
    cas_number String,
    retention_time_min Float32,
    mass_spec_pattern String,
    relative_abundance_percent Float32,
    sensory_descriptor String,
    basil_variety String,
    detection_method String,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (basil_variety, compound_name, created_date)
COMMENT 'Aroma compounds from GC-MS analysis';

-- 4. Courbes photosynthèse (Photosynthesis curves from Licor)
CREATE TABLE IF NOT EXISTS vertiflow.ref_photosynthesis_curves (
    curve_id String,
    light_condition String,
    ppfd_level Float32,
    net_photosynthesis_umol_m2s Float32,
    stomatal_conductance Float32,
    transpiration_mmol_m2s Float32,
    intercellular_co2 Float32,
    temperature_celcius Float32,
    basil_variety String,
    measurement_date Date,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (basil_variety, light_condition, ppfd_level, measurement_date)
COMMENT 'Photosynthesis response curves';

-- 5. Évaluations sensorielles (Sensory evaluation)
CREATE TABLE IF NOT EXISTS vertiflow.ref_sensory_evaluation (
    eval_id String,
    basil_variety String,
    evaluator_id String,
    leaf_color_score UInt8,
    leaf_texture_score UInt8,
    aroma_intensity_score UInt8,
    flavor_profile String,
    overall_quality_score UInt8,
    notes String,
    evaluation_date Date,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (basil_variety, evaluation_date)
COMMENT 'Sensory evaluation results';

-- 6. Expériences MIT OpenAG (MIT OpenAG baseline)
CREATE TABLE IF NOT EXISTS vertiflow.ref_mit_openag_experiments (
    experiment_id String,
    experiment_name String,
    basil_variety String,
    crop_cycle_days UInt16,
    plant_count UInt16,
    yield_g_per_plant Float32,
    final_fresh_weight_g Float32,
    final_dry_weight_g Float32,
    water_use_efficiency Float32,
    co2_uptake_rate Float32,
    notes String,
    experiment_date Date,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (experiment_id, basil_variety, experiment_date)
COMMENT 'MIT OpenAG reference experiments';

-- 7. Seuils qualité (Quality thresholds)
CREATE TABLE IF NOT EXISTS vertiflow.ref_quality_thresholds (
    threshold_id String,
    parameter_name String,
    optimal_min Float32,
    optimal_max Float32,
    warning_min Float32,
    warning_max Float32,
    critical_min Float32,
    critical_max Float32,
    unit String,
    description String,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (parameter_name, created_date)
COMMENT 'Quality control thresholds';

-- Vérification: lister toutes les tables créées
SELECT name FROM system.tables WHERE database = 'vertiflow' AND name LIKE 'ref_%' ORDER BY name;
