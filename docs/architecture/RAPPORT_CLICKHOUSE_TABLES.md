# Rapport explicatif : Schéma des tables ClickHouse du projet VertiFlow

Ce document présente le format des tables principales créées dans ClickHouse pour le projet VertiFlow, avec une explication de leur rôle et de leurs colonnes.

## 1. Table `telemetry_raw`
- **Description** : Données brutes de télémétrie issues des capteurs (niveau Bronze, rétention 30 jours).
- **Colonnes** :
  - `timestamp` (DateTime64(3)) : Horodatage précis de la mesure
  - `device_id` (String) : Identifiant du capteur
  - `zone` (String) : Zone ou emplacement
  - `metric_type` (String) : Type de métrique (température, humidité, etc.)
  - `value` (Float64) : Valeur mesurée
  - `unit` (String) : Unité de la mesure
  - `governance_ingest_ts` (UInt64) : Timestamp d’ingestion pour la gouvernance
  - `governance_schema_version` (String) : Version du schéma
  - `governance_environment` (String) : Environnement (dev, prod, etc.)
  - `data_tier` (String) : Niveau de la donnée (Bronze, Silver, Gold)
  - `lineage_source` (String) : Source d’origine de la donnée

## 2. Vue matérialisée `telemetry_1min_mv`
- **Description** : Agrégations par minute des données brutes (niveau Silver, rétention 90 jours).
- **Colonnes** :
  - `timestamp_1min` (DateTime) : Début de la minute
  - `zone` (String)
  - `metric_type` (String)
  - `value_avg` (Float64) : Moyenne
  - `value_min` (Float64) : Minimum
  - `value_max` (Float64) : Maximum
  - `value_stddev` (Float64) : Écart-type
  - `sample_count` (UInt64) : Nombre d’échantillons

## 3. Vue matérialisée `telemetry_1h_mv`
- **Description** : Agrégations par heure des données brutes (niveau Silver, rétention 90 jours).
- **Colonnes** :
  - `timestamp_1h` (DateTime) : Début de l’heure
  - `zone` (String)
  - `metric_type` (String)
  - `value_avg` (Float64)
  - `value_min` (Float64)
  - `value_max` (Float64)
  - `value_stddev` (Float64)
  - `sample_count` (UInt64)

## 4. Table `predictions`
- **Description** : Prédictions issues des modèles de Machine Learning (niveau Gold).
- **Colonnes** :
  - `timestamp` (DateTime)
  - `batch_id` (String) : Identifiant du lot de prédiction
  - `zone` (String)
  - `predicted_yield_g` (Float64) : Rendement prédit (g)
  - `confidence_score` (Float64) : Score de confiance
  - `model_version` (String) : Version du modèle
  - `features_json` (String) : Caractéristiques utilisées (JSON)

## 5. Table `system_errors`
- **Description** : Journalisation des erreurs système et Dead Letter Queue (DLQ).
- **Colonnes** :
  - `timestamp` (DateTime)
  - `error_type` (String)
  - `error_message` (String)
  - `source_system` (String)
  - `raw_payload` (String)

## 6. Table `nasa_power_climate`
- **Description** : Données climatiques et solaires issues de la NASA POWER.
- **Colonnes** :
  - `date` (Date)
  - `latitude` (Float64)
  - `longitude` (Float64)
  - `solar_irradiance` (Float64) : Irradiance solaire
  - `temperature_2m` (Float64) : Température à 2m
  - `humidity_2m` (Float64) : Humidité à 2m
  - `precipitation` (Float64) : Précipitations
  - `location` (String)

## 7. Table `openag_benchmarks`
- **Description** : Jeux de données de benchmarks OpenAg (Cooper Hewitt PFC, Basil FS2).
- **Colonnes** :
  - `timestamp` (DateTime)
  - `experiment` (String)
  - `zone` (String)
  - `metric_type` (String)
  - `value` (Float64)
  - `unit` (String)
  - `growth_stage` (String)
  - `notes` (String)

## 8. Table `spectral_research`
- **Description** : Données de recherche sur l’éclairage LED (Wageningen).
- **Colonnes** :
  - `study_id` (String)
  - `crop_type` (String)
  - `led_spectrum_r` (Int32) : Pourcentage LED rouge
  - `led_spectrum_g` (Int32) : Pourcentage LED vert
  - `led_spectrum_b` (Int32) : Pourcentage LED bleu
  - `led_spectrum_fr` (Int32) : Pourcentage LED far-red
  - `ppfd` (Float64) : Densité de flux photonique
  - `photoperiod` (Int32) : Heures d’éclairage
  - `yield_g` (Float64) : Rendement
  - `quality_score` (Float64) : Score de qualité
  - `publication_year` (Int32)
  - `institution` (String)

---

---

# Schéma des collections MongoDB du projet VertiFlow

Cette section décrit le format des collections MongoDB utilisées pour la configuration, la traçabilité et la base de connaissances scientifique.

## 1. Collection `spectral_recipes`
- **Description** : Recettes d’éclairage LED par stade de croissance.
- **Champs** :
  - `stage` (String) : Stade de croissance (SEEDLING, VEGETATIVE, FLOWERING)
  - `led_red` (Number) : % LED rouge
  - `led_blue` (Number) : % LED bleu
  - `led_far_red` (Number) : % LED far-red
  - `led_white` (Number) : % LED blanc
  - `photoperiod_hours` (Number) : Durée d’éclairage (heures)
  - `ppfd_target` (Number) : Densité de flux photonique cible
  - `description` (String) : Explication de la recette
  - `created_at` (Date) : Date de création

## 2. Collection `control_config`
- **Description** : Configuration des consignes de contrôle par zone et culture.
- **Champs** :
  - `zone` (String)
  - `crop_type` (String)
  - `target_temperature` (Number)
  - `target_humidity` (Number)
  - `target_co2` (Number)
  - `target_ph` (Number)
  - `target_ec` (Number)
  - `enabled` (Boolean)
  - `updated_at` (Date)

## 3. Collection `batches`
- **Description** : Suivi des lots de culture.
- **Champs** :
  - `batch_id` (String)
  - `zone` (String)
  - `crop_type` (String)
  - `germination_date` (Date)
  - `current_stage` (String)
  - `plant_count` (Number)
  - `expected_harvest_date` (Date)
  - `status` (String)
  - `created_at` (Date)

## 4. Collection `scientific_knowledge`
- **Description** : Base de connaissances scientifique (publications, recherches).
- **Champs** :
  - `title` (String)
  - `authors` (Array[String])
  - `year` (Number)
  - `institution` (String)
  - `key_findings` (String)
  - `relevance` (String)
  - `url` (String)
  - `added_at` (Date)

---

Ce rapport synthétise la structure des tables ClickHouse et des collections MongoDB du projet VertiFlow, facilitant la compréhension du stockage et de l’analyse des données pour l’agriculture verticale intelligente.