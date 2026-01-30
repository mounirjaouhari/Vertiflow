-- =============================================================================
-- PROJET VERTIFLOW - STRUCTURE CLICKHOUSE COMPLÈTE (GOLDEN RECORD 157 COLONNES)
-- =============================================================================
CREATE DATABASE IF NOT EXISTS vertiflow;

CREATE TABLE IF NOT EXISTS vertiflow.basil_ultimate_realtime (
    -- I. IDENTIFICATION & GÉOGRAPHIE (13 Colonnes)
                                                                 timestamp DateTime64(3, 'UTC'),
    farm_id LowCardinality(String),
    parcel_id LowCardinality(String),
    latitude Float64,
    longitude Float64,
    zone_id LowCardinality(String),
    rack_id LowCardinality(String),
    level_index UInt8,
    module_id String,
    batch_id LowCardinality(String),
    species_variety LowCardinality(String),
    position_x_y String,
    structural_weight_load Float32,

    -- II. NUTRITION MINÉRALE RÉELLE (15 Colonnes)
    nutrient_n_total Float32,
    nutrient_p_phosphorus Float32,
    nutrient_k_potassium Float32,
    nutrient_ca_calcium Float32,
    nutrient_mg_magnesium Float32,
    nutrient_s_sulfur Float32,
    nutrient_fe_iron Float32,
    nutrient_mn_manganese Float32,
    nutrient_zn_zinc Float32,
    nutrient_cu_copper Float32,
    nutrient_b_boron Float32,
    nutrient_mo_molybdenum Float32,
    nutrient_cl_chlorine Float32,
    nutrient_ni_nickel Float32,
    nutrient_solution_ec Float32,

    -- III. PHOTOSYNTHÈSE & LUMIÈRE (15 Colonnes)
    light_intensity_ppfd Float32,
    light_compensation_point Float32,
    light_saturation_point Float32,
    light_ratio_red_blue Float32,
    light_far_red_intensity Float32,
    light_dli_accumulated Float32,
    light_photoperiod Float32,
    quantum_yield_psii Float32,
    photosynthetic_rate_max Float32,
    co2_level_ambient UInt16,
    co2_consumption_rate Float32,
    night_respiration_rate Float32,
    light_use_efficiency Float32,
    leaf_absorption_pct Float32,
    spectral_recipe_id LowCardinality(String),

    -- IV. BIOMASSE & CROISSANCE (15 Colonnes)
    fresh_biomass_est Float32,
    dry_biomass_est Float32,
    leaf_area_index_lai Float32,
    root_shoot_ratio Float32,
    relative_growth_rate Float32,
    net_assimilation_rate Float32,
    canopy_height Float32,
    harvest_index Float32,
    days_since_planting UInt16,
    thermal_sum_accumulated Float32,
    growth_stage Enum8('Semis'=1, 'Végétatif'=2, 'Bouton'=3, 'Récolte'=4),
    predicted_yield_kg_m2 Float32,
    expected_harvest_date Date,
    biomass_accumulation_daily Float32,
    target_harvest_weight Float32,

    -- V. PHYSIOLOGIE & SANTÉ (15 Colonnes)
    health_score Float32,
    chlorophyll_index_spad Float32,
    stomatal_conductance Float32,
    anthocyanin_index Float32,
    tip_burn_risk Float32,
    leaf_temp_delta Float32,
    stem_diameter_micro Float32,
    sap_flow_rate Float32,
    leaf_wetness_duration Float32,
    potential_hydrique_foliaire Float32,
    ethylene_level Float32,
    ascorbic_acid_content Float32,
    phenolic_content Float32,
    essential_oil_yield Float32,
    aroma_compounds_ratio Float32,

    -- VI. ENVIRONNEMENT & CLIMAT (16 Colonnes)
    air_temp_internal Float32,
    air_humidity Float32,
    vapor_pressure_deficit Float32,
    airflow_velocity Float32,
    air_pressure Float32,
    fan_speed_pct Float32,
    ext_temp_nasa Float32,
    ext_humidity_nasa Float32,
    ext_solar_radiation Float32,
    oxygen_level Float32,
    dew_point Float32,
    hvac_load_pct Float32,
    co2_injection_status UInt8,
    energy_footprint_hourly Float32,
    renewable_energy_pct Float32,
    ambient_light_pollution Float32,

    -- VII. RHIZOSPHÈRE & EAU (15 Colonnes)
    water_temp Float32,
    water_ph Float32,
    dissolved_oxygen Float32,
    water_turbidity Float32,
    wue_current Float32,
    water_recycled_rate Float32,
    coefficient_cultural_kc Float32,
    microbial_density Float32,
    beneficial_microbes_ratio Float32,
    root_fungal_pressure Float32,
    biofilm_thickness Float32,
    algae_growth_index Float32,
    redox_potential Float32,
    irrigation_line_pressure Float32,
    leaching_fraction Float32,

    -- VIII. ÉCONOMIE & BAIL (10 Colonnes)
    energy_price_kwh Float32,
    market_price_kg Float32,
    lease_index_value Float32,
    daily_rent_cost Float32,
    lease_profitability_index Float32,
    is_compliant_lease UInt8,
    labor_cost_pro_rata Float32,
    carbon_credit_value Float32,
    operational_cost_total Float32,
    carbon_footprint_per_kg Float32,

    -- IX. HARDWARE & INFRA (10 Colonnes)
    pump_vibration_level Float32,
    fan_current_draw Float32,
    led_driver_temp Float32,
    filter_differential_pressure Float32,
    ups_battery_health Float32,
    leak_detection_status UInt8,
    emergency_stop_status UInt8,
    network_latency_ms UInt16,
    sensor_calibration_offset Float32,
    module_integrity_score Float32,

    -- X. INTELLIGENCE & DÉCISION (10 Colonnes)
    ai_decision_mode LowCardinality(String),
    anomaly_confidence_score Float32,
    predicted_energy_need_24h Float32,
    risk_pest_outbreak Float32,
    irrigation_strategy_id LowCardinality(String),
    master_compliance_index Float32,
    blockchain_hash String,
    audit_trail_signature String,
    quality_grade_prediction Enum8('Premium'=1, 'Standard'=2, 'Rejet'=3),
    system_reboot_count UInt8,

    -- XI. CIBLES RÉFÉRENTIELLES (15 Colonnes)
    ref_n_target Float32,
    ref_p_target Float32,
    ref_k_target Float32,
    ref_ca_target Float32,
    ref_mg_target Float32,
    ref_temp_opt Float32,
    ref_lai_target Float32,
    ref_oil_target Float32,
    ref_wue_target Float32,
    ref_microbial_target Float32,
    ref_photoperiod_opt Float32,
    ref_sum_thermal_target Float32,
    ref_brix_target Float32,
    ref_nitrate_limit Float32,
    ref_humidity_opt Float32,

    -- XII. TRAÇABILITÉ (8 Colonnes)
    data_source_type Enum8('IoT'=1, 'API'=2, 'ML'=3, 'Lab'=4),
    sensor_hardware_id LowCardinality(String),
    api_endpoint_version String,
    source_reliability_score Float32,
    data_integrity_flag UInt8,
    last_calibration_date Date,
    maintenance_urgency_score Float32,
    lineage_uuid UUID

    ) ENGINE = ReplacingMergeTree()
    PARTITION BY toYYYYMM(timestamp)
    ORDER BY (farm_id, parcel_id, rack_id, level_index, timestamp)
-- CORRECTION Master : Conversion obligatoire pour DateTime64
    TTL toDateTime(timestamp) + INTERVAL 5 YEAR
    SETTINGS index_granularity = 8192;

-- TABLE DE PRÉDICTIONS UNIFIÉE (A9, A10, A11)
CREATE TABLE IF NOT EXISTS vertiflow.ml_predictions (
                                                        timestamp DateTime64(3, 'UTC') DEFAULT now64(3),
    model_name LowCardinality(String),
    model_version String,
    batch_id String,
    prediction_type String,
    prediction_value Float64,
    confidence Float64,
    features_json String,
    execution_time_ms UInt32
    ) ENGINE = MergeTree()
    ORDER BY (timestamp, model_name)
    TTL toDateTime(timestamp) + INTERVAL 1 YEAR;