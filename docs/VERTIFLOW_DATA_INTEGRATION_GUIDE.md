# VertiFlow - Guide d'Integration des Donnees

## Vue d'Ensemble du Systeme de Donnees

Ce document resume toutes les structures de donnees, schemas et sources disponibles pour le pipeline NiFi VertiFlow.

---

## 1. ClickHouse - Base de Donnees Analytique

### Base: `vertiflow`

#### Table Principale: `basil_ultimate_realtime` (153 colonnes - Golden Record)

**Moteur:** ReplacingMergeTree()
**Partitionnement:** Mensuel (toYYYYMM(timestamp))
**Tri:** (farm_id, parcel_id, rack_id, level_index, timestamp)
**TTL:** 5 ans

| Categorie | Colonnes | Description |
|-----------|----------|-------------|
| Identification | 13 | timestamp, farm_id, parcel_id, latitude, longitude, zone_id, rack_id, level_index, module_id, batch_id, species_variety, position_x_y, structural_weight_load |
| Nutrition Minerale | 15 | nutrient_n_total, nutrient_p_phosphorus, nutrient_k_potassium, nutrient_ca_calcium, nutrient_mg_magnesium, nutrient_s_sulfur, nutrient_fe_iron, nutrient_mn_manganese, nutrient_zn_zinc, nutrient_cu_copper, nutrient_b_boron, nutrient_mo_molybdenum, nutrient_cl_chlorine, nutrient_ni_nickel, nutrient_solution_ec |
| Photosynthese & Lumiere | 15 | light_intensity_ppfd, light_compensation_point, light_saturation_point, light_ratio_red_blue, light_far_red_intensity, light_dli_accumulated, light_photoperiod, quantum_yield_psii, photosynthetic_rate_max, co2_level_ambient, co2_consumption_rate, night_respiration_rate, light_use_efficiency, leaf_absorption_pct, spectral_recipe_id |
| Biomasse & Croissance | 15 | fresh_biomass_est, dry_biomass_est, leaf_area_index_lai, root_shoot_ratio, relative_growth_rate, net_assimilation_rate, canopy_height, harvest_index, days_since_planting, thermal_sum_accumulated, growth_stage, predicted_yield_kg_m2, expected_harvest_date, biomass_accumulation_daily, target_harvest_weight |
| Physiologie & Sante | 15 | health_score, chlorophyll_index_spad, stomatal_conductance, anthocyanin_index, tip_burn_risk, leaf_temp_delta, stem_diameter_micro, sap_flow_rate, leaf_wetness_duration, potential_hydrique_foliaire, ethylene_level, ascorbic_acid_content, phenolic_content, essential_oil_yield, aroma_compounds_ratio |
| Environnement & Climat | 16 | air_temp_internal, air_humidity, vapor_pressure_deficit, airflow_velocity, air_pressure, fan_speed_pct, ext_temp_nasa, ext_humidity_nasa, ext_solar_radiation, oxygen_level, dew_point, hvac_load_pct, co2_injection_status, energy_footprint_hourly, renewable_energy_pct, ambient_light_pollution |
| Rhizosphere & Eau | 15 | water_temp, water_ph, dissolved_oxygen, water_turbidity, wue_current, water_recycled_rate, coefficient_cultural_kc, microbial_density, beneficial_microbes_ratio, root_fungal_pressure, biofilm_thickness, algae_growth_index, redox_potential, irrigation_line_pressure, leaching_fraction |
| Economie & Bail | 10 | energy_price_kwh, market_price_kg, lease_index_value, daily_rent_cost, lease_profitability_index, is_compliant_lease, labor_cost_pro_rata, carbon_credit_value, operational_cost_total, carbon_footprint_per_kg |
| Hardware & Infra | 10 | pump_vibration_level, fan_current_draw, led_driver_temp, filter_differential_pressure, ups_battery_health, leak_detection_status, emergency_stop_status, network_latency_ms, sensor_calibration_offset, module_integrity_score |
| Intelligence & Decision | 10 | ai_decision_mode, anomaly_confidence_score, predicted_energy_need_24h, risk_pest_outbreak, irrigation_strategy_id, master_compliance_index, blockchain_hash, audit_trail_signature, quality_grade_prediction, system_reboot_count |
| Cibles Referentielles | 15 | ref_n_target, ref_p_target, ref_k_target, ref_ca_target, ref_mg_target, ref_temp_opt, ref_lai_target, ref_oil_target, ref_wue_target, ref_microbial_target, ref_photoperiod_opt, ref_sum_thermal_target, ref_brix_target, ref_nitrate_limit, ref_humidity_opt |
| Tracabilite | 8 | data_source_type, sensor_hardware_id, api_endpoint_version, source_reliability_score, data_integrity_flag, last_calibration_date, maintenance_urgency_score, lineage_uuid |

#### Tables Externes

| Table | Description | Source |
|-------|-------------|--------|
| `ext_weather_history` | Historique meteo | NASA POWER, Open-Meteo |
| `ext_energy_market` | Prix energie, mix carbone | API RTE |
| `ref_plant_recipes` | Recettes de reference | Labo/Base de connaissance |
| `ext_land_registry` | Donnees cadastrales | Etalab/ERP |
| `ext_market_prices` | Prix marche agricole | RNM |

---

## 2. MongoDB - Base Operationnelle

### Base: `vertiflow_ops`

#### Collection: `live_state` (Digital Twin)
```json
{
  "farm_id": "VERT-MAROC-01",
  "rack_id": "R01",
  "module_id": "MOD-001",
  "last_update": ISODate(),
  "telemetry": {
    "air_temp_internal": 24.5,
    "nutrient_n_total": 150
  },
  "status": {
    "is_active": true,
    "alert_level": "NORMAL"
  }
}
```
**Index:** Unique sur (farm_id, rack_id, module_id)
**TTL:** 7 jours sur last_update

#### Collection: `incident_logs` (Journal d'Alertes)
```json
{
  "timestamp": ISODate(),
  "severity": "CRITICAL",
  "status": "OPEN",
  "source": "Algo_A5",
  "message": "VPD threshold exceeded",
  "module_id": "MOD-001"
}
```

#### Collection: `plant_recipes` (Recettes Agronomiques)
```json
{
  "recipe_id": "BASIL-VEG-001",
  "crop_type": "basil",
  "variety": "Genovese",
  "growth_stage": "vegetative",
  "environment": {
    "temperature_c": { "min": 22, "max": 28, "optimal": 25 },
    "humidity_pct": { "min": 55, "max": 70, "optimal": 62 },
    "vpd_kpa": { "min": 0.7, "max": 1.1, "optimal": 0.9 }
  },
  "lighting": {
    "ppfd_umol": { "min": 300, "max": 450, "optimal": 380 },
    "dli_mol": { "min": 15, "max": 22, "optimal": 18 },
    "photoperiod_h": 16,
    "spectrum": {
      "blue_450nm_pct": 25,
      "red_660nm_pct": 55,
      "far_red_730nm_pct": 8
    }
  },
  "nutrition": {
    "ec_ms": { "min": 1.4, "max": 1.8, "optimal": 1.6 },
    "ph": { "min": 5.8, "max": 6.4, "optimal": 6.0 },
    "macronutrients": {
      "N": { "min": 140, "max": 180, "optimal": 160 },
      "P": { "min": 45, "max": 65, "optimal": 55 },
      "K": { "min": 180, "max": 240, "optimal": 210 }
    }
  }
}
```

### Base: `vertiflow_metadata`

#### Collection: `spectral_recipes`
Recettes spectrales LED pour optimisation photomorphogenese.

#### Collection: `fao_kc_coefficients`
Coefficients culturaux FAO pour calcul evapotranspiration.

---

## 3. Apache Kafka - Topics

### Topics Principaux

| Topic | Partitions | Description | Producteur | Consommateur |
|-------|------------|-------------|------------|--------------|
| `basil_telemetry_full` | 6 | Telemetrie 153 colonnes | Zone 2 | Zone 3, Zone 4 |
| `vertiflow.commands` | 3 | Commandes vers IoT | Zone 4 | Actionneurs |
| `vertiflow.alerts` | 3 | Alertes prioritaires | Zone 4 | Monitoring |
| `dead_letter_queue` | 1 | Erreurs NiFi | DLQ | Audit |

### Topics Donnees Externes (Zone 0)

| Topic | Description | Source API |
|-------|-------------|------------|
| `vertiflow.external.weather` | Meteo horaire | Open-Meteo |
| `vertiflow.external.nasa` | Climat agricole | NASA POWER |
| `vertiflow.external.airquality` | Qualite air | OpenAQ |

### Topics Donnees Statiques (Zone 5)

| Topic | Description |
|-------|-------------|
| `vertiflow.static.datasets` | Datasets CSV |
| `vertiflow.static.lab` | Donnees laboratoire |
| `vertiflow.scraped.prices` | Prix scraped (RNM, ONEE) |

---

## 4. Schemas JSON

### Schema Telemetrie v3 (docs/schemas/telemetry_v3.json)

Champs requis:
- `timestamp` (ISO8601 UTC)
- `farm_id` (pattern: VERT-[A-Z]+-[0-9]+)
- `sensor_hardware_id`
- `data_source_type` (enum: IoT, API, ML, Lab)

### Schema Commande v3 (docs/schemas/command_v3.json)

Champs requis:
- `command_id` (UUID)
- `timestamp` (ISO8601 UTC)
- `target_farm_id`
- `command_type` (enum: SET_POINT, EMERGENCY_STOP, RESET, CALIBRATE, MODE_SWITCH)
- `priority` (enum: LOW, NORMAL, HIGH, CRITICAL)

---

## 5. Datasets Disponibles

### Dossier: `datasets/`

| Fichier | Description | Volume |
|---------|-------------|--------|
| `Basil Data.zip` | Dataset principal MIT OpenAg | ~50 MB, 73,000+ datapoints |
| `MANUAL_data_BV_FS2.xlsx` | Donnees manuelles Food Server 2 | 1.4 MB |
| `META_BV_FS2.xlsx` | Metadonnees | 278 KB |
| `DataSheet_1_Chilling*.xlsx` | Etude temperatures basilic | 731 KB |

### Dossier: `datasets/basil_research/`

| Type | Description |
|------|-------------|
| `*.pdf` | Articles Frontiers in Plant Science |
| `*.xlsx` | Donnees experimentales (stress, spectre, metabolites) |
| `Table_*.XLSX` | Tableaux scientifiques |

---

## 6. Integration Pipeline NiFi

### Zone 0 - External Data APIs
```
Trigger → InvokeHTTP → PublishKafka
         (Open-Meteo)   (vertiflow.external.weather)
         (NASA POWER)   (vertiflow.external.nasa)
         (OpenAQ)       (vertiflow.external.airquality)
```

### Zone 1 - Ingestion & Validation
```
ListenHTTP/ConsumeMQTT/GetFile → ValidateRecord → Monitor → Zone 2
```

### Zone 2 - Contextualisation
```
From_Zone_1 → LookupRecord (MongoDB) → ExecuteScript (VPD) → JoltTransform → PublishKafka
                                                                            (basil_telemetry_full)
```

### Zone 3 - Persistance
```
ConsumeKafka (basil_telemetry_full) → PutClickHouse (basil_ultimate_realtime)
                                   → PutMongo (incident_logs)
                                   → PutFile (archive)
```

### Zone 4 - Retroaction
```
ConsumeKafka → QueryRecord (VPD alerts) → AttributesToJSON → PublishMQTT
```

### Zone 5 - Static Data Loaders
```
GetFile (CSV/JSON) → ConvertRecord → PublishKafka (vertiflow.static.*)
GetFile (Recipes) → PutMongo (plant_recipes)
ConsumeKafka (scraped) → PutMongo (market_prices)
```

---

## 7. Connexions et Ports

### NiFi (8443)
- URL: https://localhost:8443/nifi
- User: admin
- Password: (voir docker-compose)

### Kafka
- Interne Docker: `kafka:29092`
- Externe: `localhost:9092`

### ClickHouse
- HTTP: `clickhouse:8123`
- Native: `clickhouse:9000`
- User: default / default

### MongoDB
- URI: `mongodb://mongodb:27017`
- Database: `vertiflow_ops`

### Mosquitto MQTT
- URI: `tcp://mosquitto:1883`
- WebSocket: `ws://localhost:9001`

---

## 8. Recettes Disponibles (plant_recipes)

| recipe_id | Stage | Temp (C) | VPD (kPa) | PPFD | DLI | EC | pH |
|-----------|-------|----------|-----------|------|-----|----|----|
| BASIL-GERM-001 | germination | 20-25 | 0.4-0.8 | 100-200 | 6-10 | 0.8-1.2 | 5.5-6.0 |
| BASIL-SEED-001 | seedling | 20-26 | 0.5-0.9 | 200-300 | 10-14 | 1.0-1.4 | 5.6-6.2 |
| BASIL-VEG-001 | vegetative | 22-28 | 0.7-1.1 | 300-450 | 15-22 | 1.4-1.8 | 5.8-6.4 |
| BASIL-FIN-001 | finishing | 20-24 | 0.9-1.3 | 400-550 | 18-26 | 1.0-1.4 | 5.6-6.0 |

---

**Document genere: 2026-01-14**
**Projet: VertiFlow Governance Pipeline**
