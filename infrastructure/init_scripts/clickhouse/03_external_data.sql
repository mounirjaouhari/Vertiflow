-- =============================================================================
-- PROJET VERTIFLOW - TABLES DE RÉFÉRENCE POUR SOURCES EXTERNES
-- =============================================================================
-- Date de création    : 25/12/2025
-- Responsable         : VertiFlow Core Team
-- Ticket Associé      : TICKET-017
-- Description         : Stockage des données contextuelles (Météo, Énergie, Référentiels).
--                       Ces tables permettent d'enrichir l'analyse sans polluer
--                       la table principale temps réel.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS vertiflow;

-- =============================================================================
-- 1. TABLE : HISTORIQUE MÉTÉO & PRÉVISIONS (NASA POWER / OPENWEATHER)
-- Source : API NASA (via NiFi)
-- Fréquence : Mise à jour horaire
-- Usage : Comparaison Intérieur/Extérieur, Calcul de l'isolation
-- =============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.ext_weather_history (
    timestamp DateTime64(3, 'UTC'),
    location_id LowCardinality(String), -- Ex: "FARM_MAROC_01"
    latitude Float64,
    longitude Float64,
    
    -- Données Atmosphériques
    temp_c Float32,
    humidity_pct Float32,
    pressure_hpa Float32,
    wind_speed_ms Float32,
    wind_direction_deg Float32,
    
    -- Données Solaires (Critique pour l'optimisation LED)
    solar_radiation_w_m2 Float32,
    cloud_cover_pct Float32,
    uv_index Float32,
    
    -- Métadonnées Source
    api_source LowCardinality(String), -- Ex: "NASA_POWER_V2"
    ingestion_time DateTime DEFAULT now()

) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (location_id, timestamp);

-- =============================================================================
-- 2. TABLE : MARCHÉ DE L'ÉNERGIE & MIX CARBONE (RTE / ENTSO-E)
-- Source : API RTE Eco2mix
-- Fréquence : 15 minutes
-- Usage : Optimisation des coûts (Smart Grid) et Calcul RSE
-- =============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.ext_energy_market (
    timestamp DateTime64(3, 'UTC'),
    region_code LowCardinality(String), -- Ex: "FR", "MA"
    
    -- Prix
    spot_price_eur_kwh Float32,
    
    -- Mix Énergétique (Pour le score RSE)
    carbon_intensity_g_co2_kwh Float32,
    renewable_pct Float32,
    nuclear_pct Float32,
    fossil_pct Float32,
    
    -- Statut Réseau
    grid_load_mw Float32,
    alert_status LowCardinality(String) -- Ex: "RED", "ORANGE", "GREEN"

) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (region_code, timestamp);

-- =============================================================================
-- 3. TABLE : RÉFÉRENTIEL SCIENTIFIQUE (PLANT RECIPES)
-- Source : Saisie Labo / Base de connaissance
-- Fréquence : Mise à jour manuelle (Rare)
-- Usage : Fournir les cibles (Targets) pour les comparaisons
-- =============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.ref_plant_recipes (
    recipe_id String,                -- Ex: "BASIL_GENOVESE_GROWTH_V1"
    species_variety String,          -- Ex: "Genovese"
    growth_stage Enum8('Semis'=1, 'Végétatif'=2, 'Bouton'=3, 'Récolte'=4),
    
    -- Cibles Climatiques
    target_temp_day Float32,
    target_temp_night Float32,
    target_humidity_min Float32,
    target_humidity_max Float32,
    target_vpd Float32,
    
    -- Cibles Lumière
    target_dli Float32,
    target_photoperiod_hours Float32,
    target_spectrum_ratio_rb Float32, -- Rouge/Bleu
    
    -- Cibles Nutrition (NPK)
    target_n_ppm Float32,
    target_p_ppm Float32,
    target_k_ppm Float32,
    target_ec Float32,
    target_ph Float32,
    
    -- Métadonnées
    author String,
    validation_date Date,
    version UInt16,
    is_active UInt8 DEFAULT 1

) ENGINE = ReplacingMergeTree(version)
ORDER BY (recipe_id, species_variety, growth_stage);

-- =============================================================================
-- 4. TABLE : DONNÉES LÉGALES & FONCIÈRES (CADASTRE / BAIL)
-- Source : API Etalab / ERP Interne
-- Fréquence : Mensuelle
-- Usage : Calcul de rentabilité au m² cadastral
-- =============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.ext_land_registry (
    parcel_id String,                -- Clé de jointure principale
    lease_contract_id String,
    
    -- Données Géographiques
    surface_m2 Float32,
    orientation_deg Float32,
    altitude_m Float32,
    
    -- Données Financières (Indexées)
    base_rent_eur_m2 Float32,
    lease_index_reference Float32,   -- Indice de base à la signature
    last_index_value Float32,        -- Dernier indice publié
    
    -- Statut Juridique
    zone_type LowCardinality(String), -- Ex: "Agricole", "Industriel"
    lease_start_date Date,
    lease_end_date Date,
    landlord_hash String             -- Anonymisé

) ENGINE = ReplacingMergeTree()
ORDER BY (parcel_id, lease_contract_id);

-- =============================================================================
-- 5. TABLE : COTATION DU MARCHÉ AGRICOLE (PRIX DE VENTE)
-- Source : RNM (Réseau des Nouvelles des Marchés)
-- Fréquence : Hebdomadaire
-- Usage : Calcul du Chiffre d'Affaires prévisionnel
-- =============================================================================
CREATE TABLE IF NOT EXISTS vertiflow.ext_market_prices (
    date Date,
    product_code LowCardinality(String), -- Ex: "HERB_BASIL_FRESH"
    market_place LowCardinality(String), -- Ex: "RUNGIS", "CASABLANCA"
    
    -- Prix (Min, Max, Moyen)
    price_min_eur_kg Float32,
    price_max_eur_kg Float32,
    price_avg_eur_kg Float32,
    
    volume_tons Float32,
    quality_grade LowCardinality(String) -- Ex: "EXTRA", "CAT1"

) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (product_code, market_place, date);