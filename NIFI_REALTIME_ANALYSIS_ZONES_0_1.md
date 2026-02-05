# 🔍 ANALYSE TEMPS RÉEL NiFi - Zones 0 & 1  
**Date:** 2026-02-01  
**Analyseur:** Pipeline Debug Script  
**Source:** `/opt/nifi/nifi-current/conf/flow.xml.gz` (config NiFi réelle)

---

## 🚨 DIAGNOSTIC CRITIQUE

### État Actuel des Zones 0 & 1
| Zone | Processeurs | Ports | Connexions | État |
|------|-----------|-------|-----------|------|
| **Zone 0** (External APIs) | 9 | ❌ 0 | 12 | 🟢 RUNNING |
| **Zone 1** (Ingestion) | 6 | ❌ 0 | 9 | 🟢 RUNNING |

⚠️ **PROBLÈME CRITIQUE**: Les deux zones **n'ont PAS de PORTS**  
→ Cela signifie que les données **ne passent pas entre Zone 0 et Zone 1** en temps réel.

---

## 📊 Zone 0 - External Data APIs (Données Entrantes)

### Processeurs Actuels (9 total):

**API Triggers** (GenerateFlowFile):
- ✅ Trigger - Air Quality [RUNNING]
- ✅ Trigger - Daily NASA POWER [RUNNING]
- ✅ Trigger - Hourly Weather [RUNNING]

**APIs HTTP Calls** (InvokeHTTP):
- ✅ API - Open-Meteo Weather [RUNNING]
- ✅ API - OpenAQ Air Quality [RUNNING]
- ✅ API - NASA POWER [RUNNING]

**Kafka Publishers** (PublishKafka_2_6):
- ✅ Publish - Weather to Kafka [RUNNING]
- ✅ Publish - AirQuality to Kafka [RUNNING]
- ✅ Publish - NASA to Kafka [RUNNING]

### ✅ Ce que Zone 0 Envoie:

| Processeur | Topic Kafka | Colonnes Fournies | Fréquence |
|-----------|----------|----------------|-----------|
| **API - NASA POWER** | `vertiflow.external.nasa` | `ext_temp_nasa`, `ext_humidity_nasa`, `ext_solar_radiation`, `ext_pressure` | 1h (GenerateFlowFile trigger) |
| **API - Open-Meteo** | `vertiflow.external.weather` | `ext_temp_openmeteo`, `ext_humidity_openmeteo`, `ext_uv_index`, `ext_wind_speed`, `ext_soil_temp`, `ext_evapotranspiration` | Horaire |
| **API - OpenAQ** | `vertiflow.external.airquality` | `ext_air_quality_pm25`, `ext_air_quality_pm10` | Horaire |

### ❌ PROBLÈME: Zone 0 → Zone 1 

**Connexion Inter-Zone**: ❌ **N'EXISTE PAS**

Zone 0 publie dans Kafka, mais **Zone 1 ne consomme que**:
- ✅ `vertiflow.ingestion.raw` (IoT Simulator)
- ❌ `vertiflow.external.*` (NOT CONSUMED)

**Impact**: Les colonnes externes NASA/Open-Meteo **ne sont jamais injectées** dans le golden record.

---

## 📊 Zone 1 - Ingestion & Validation (Données de Base)

### Processeurs Actuels (6 total):

**Ingestion Sources**:
- ✅ A2 - ConsumeMQTT [RUNNING] → Capteurs IoT
- ✅ A1 - ListenHTTP [RUNNING] → HTTP POST
- ✅ A3 - GetFile [RUNNING] → Fichiers locaux
- ✅ ConsumeKafkaRecord_2_6 [RUNNING] → Topic Kafka

**Validation & Monitoring**:
- ✅ ValidateRecord [RUNNING] → Vérification schéma
- ✅ Monitor_Ingestion_Health [RUNNING] → Métriques

### ✅ Ce que Zone 1 Reçoit:

| Source | Format | Colonnes Attendues | État |
|--------|--------|------------------|------|
| **MQTT** (A2) | JSON | `timestamp`, `sensor_id`, `metrics.*` (air_temp, humidity, co2, etc.) | 🟢 Connecté |
| **HTTP** (A1) | JSON | Même que MQTT | 🟢 Écoute |
| **GetFile** (A3) | CSV/JSON | Recettes, données labo | 🟢 Running |
| **Kafka** | JSON/Binary | Données IoT simulées | 🟢 Running |

### ❌ PROBLÈME: Colonnes Manquantes en Zone 1

Zone 1 reçoit des données brutes mais **les colonnes manquantes ne sont PAS produites ici**:

#### Colonnes Manquantes = Colonnes non dans la Source:

| Colonne | Devrait venir de | Problème | Impact |
|---------|------------------|---------|--------|
| `rack_id` | Dérivation de `zone_id` + lookup | ❌ Pas de LookupRecord actif en Zone 1 | Dashboard 05, 06, 09 vide |
| `health_score` | Calcul à partir des métriques | ❌ Aucun calcul en Zone 1 | Dashboard 05, 07, 08 vide |
| `growth_stage` | Import/lookup/défaut | ❌ Pas fourni | Dashboard 06, 07 vide |
| `days_since_planting` | Calcul depuis `timestamp` + plantation date | ❌ Pas calculé | Dashboard 06, 07 vide |
| **Colonnes NASA Externes** | Zone 0 (Kafka) | ❌ Zone 1 ne consomme pas `vertiflow.external.*` | Dashboard 12 complètement vide |
| **Colonnes ML** | Zone 4/ML | ❌ Produites après Zone 3 | Dashboard 08 vide |

---

## 🔗 Flux de Données Réel vs Attendu

### RÉEL (Maintenant):
```
Zone 0 (APIs)
  ├─ GenerateFlowFile (Hourly trigger)
  ├─ InvokeHTTP (appelle NASA/Open-Meteo/OpenAQ)
  └─ PublishKafka → vertiflow.external.{nasa|weather|airquality}
                         ↓ (NON CONSOMMÉ - LAG MONTE)
                    Kafka Dead Letter Queue

Zone 1 (Ingestion)
  ├─ ConsumeMQTT ← capteurs (4-5 colonnes attendues)
  ├─ ListenHTTP ← POST manuels
  ├─ GetFile ← fichiers locaux
  └─ ConsumeKafka ← UNIQUEMENT vertiflow.ingestion.raw
       ↓
  ❌ Zone 1 produit JSON avec SEULEMENT:
     {timestamp, sensor_id, metrics.air_temp, metrics.humidity, ...}
     (24+ colonnes manquantes)
       ↓
  Zone 2 (Enrichissement)
     └─ ⚠️ Essaie d'ajouter colonnes mais certaines ne peuvent pas être calculées
           (example: ext_temp_nasa n'existe nulle part)
```

### ATTENDU (Selon Architecture):
```
Zone 0 (APIs) 
  → Tous les 3 topics Kafka: external.nasa, external.weather, external.airquality
       ↓
Zone 1 (Ingestion)
  ├─ ConsumeKafka → vertiflow.external.* (NASA, météo, air quality)
  ├─ ConsumeMQTT → IoT sensors
  ├─ ListenHTTP → HTTP posts
  └─ GetFile → Fichiers
       ↓
  Merge / Flatten tous les flux
       ↓
  Output: JSON avec 40+ colonnes (incluant colonnes externes)
       ↓
Zone 2 (Enrichissement)
  Ajouter les colonnes calculées (health_score, vpd, etc.)
```

---

## 📝 CHECK-LIST: Ce qui faut Entrer en Zone 0 & Zone 1

### Zone 0 Requirements:
```json
// 1. Triggers Kafka Topics (CONFIGURÉS):
✅ Topic: vertiflow.external.nasa
✅ Topic: vertiflow.external.weather  
✅ Topic: vertiflow.external.airquality

// 2. APIs Credentials & Endpoints (À VÉRIFIER):
NASA POWER API: ✅ Configuré (https://power.larc.nasa.gov/api)
Open-Meteo: ✅ Gratuit (https://api.open-meteo.com/v1/forecast)
OpenAQ: ✅ Gratuit (https://api.openaq.org/v2/measurements)

// 3. Données Attendues par Zone 0:
Chaque API call retourne:
- Temperature, Humidity, Pressure, Wind Speed (Open-Meteo)
- Solar Radiation, UV Index, Evapotranspiration (Open-Meteo)
- PM2.5, PM10 (OpenAQ)
- Temperature, Humidity, Solar Radiation (NASA POWER)
```

### Zone 1 Requirements - CE QUI MANQUE:
```json
// 1. SOURCE MQTT (Déjà active):
✅ Broker: mosquitto:1883
✅ Topic: vertiflow/telemetry/#
💡 Payload doit contenir:
   {
     "timestamp": "ISO8601",
     "sensor_hardware_id": "SEN-001",
     "zone_id": "ZONE_1",  // ou ZONE_GERMINATION, etc.
     "metrics": {
       "air_temp_internal": 24.5,
       "air_humidity": 64.0,
       "co2_level_ambient": 420,
       "light_intensity_ppfd": 326,
       "water_ph": 6.5,
       "nutrient_solution_ec": 1.8,
       "nutrient_n_total": 169,
       "nutrient_p_phosphorus": 31,
       "nutrient_k_potassium": 195
     }
   }

// 2. KAFKA SOURCE (À AJOUTER):
❌ ConsumeKafka_2_6 pour vertiflow.external.nasa
❌ ConsumeKafka_2_6 pour vertiflow.external.weather
❌ ConsumeKafka_2_6 pour vertiflow.external.airquality
   → Ces données doivent être fusionnées dans Zone 1

// 3. COLONNES À INJECTER DIRECTEMENT:
Zone 1 devrait merger:
  - MQTT data (IoT sensors)
  - Kafka external data (NASA/Open-Meteo/OpenAQ)
  - LocalFile data (recipes, lab results)
  → Output un JSON unifié avant Zone 2

// 4. COLONNES QUE ZONE 1 NE PEUT PAS CRÉER:
Ces colonnes doivent venir de SOURCES EXTERNES:
❌ rack_id → lookup table needed (mapping zone → rack)
❌ parcel_id → configuration/constants
❌ health_score → CALCUL nécessaire (pas de formule en Zone 1)
❌ predicted_* → ML Zone (Zone 4)
```

---

## 🎯 Tableau Complet: Colonnes → Source → Processeur NiFi

### COLONNES FOURNIES PAR ZONE 0 (Actuellement perdues en Kafka):

| Colonne | API Source | Topic Kafka | Processeur | Consommateur Zone 1 | Status |
|---------|-----------|------------|----------|------------------|--------|
| `ext_temp_nasa` | NASA POWER | `vertiflow.external.nasa` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_humidity_nasa` | NASA POWER | `vertiflow.external.nasa` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_solar_radiation` | NASA POWER | `vertiflow.external.nasa` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_pressure` | NASA POWER | `vertiflow.external.nasa` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_temp_openmeteo` | Open-Meteo | `vertiflow.external.weather` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_humidity_openmeteo` | Open-Meteo | `vertiflow.external.weather` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_uv_index` | Open-Meteo | `vertiflow.external.weather` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_wind_speed` | Open-Meteo | `vertiflow.external.weather` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_evapotranspiration` | Open-Meteo | `vertiflow.external.weather` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_air_quality_pm25` | OpenAQ | `vertiflow.external.airquality` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |
| `ext_air_quality_pm10` | OpenAQ | `vertiflow.external.airquality` | InvokeHTTP → PublishKafka | ❌ ABSENT | 🔴 PERDUE |

### COLONNES FOURNIES PAR ZONE 1 (IoT Sensors):

| Colonne | Source | Processeur | Actuellement | Status |
|---------|--------|-----------|-------------|--------|
| `timestamp` | MQTT/HTTP/Kafka | ConsumeMQTT / ListenHTTP | ✅ Oui | 🟢 OK |
| `sensor_hardware_id` | MQTT/HTTP | ConsumeMQTT / ListenHTTP | ✅ Oui | 🟢 OK |
| `zone_id` | MQTT/HTTP | ConsumeMQTT / ListenHTTP | ✅ Oui (si payload) | 🟢 OK (conditionnel) |
| `air_temp_internal` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |
| `air_humidity` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |
| `co2_level_ambient` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |
| `light_intensity_ppfd` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |
| `water_ph` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |
| `nutrient_solution_ec` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |
| `nutrient_n_total` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |
| `nutrient_p_phosphorus` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |
| `nutrient_k_potassium` | MQTT | ConsumeMQTT | ✅ Oui | 🟢 OK |

### COLONNES MANQUANTES (Doivent être produites en Zone 2):

| Colonne | Calcul/Source | Processeur Attendu | Processeur Réel | Status |
|---------|--------------|-------------------|-----------------|--------|
| `rack_id` | Lookup(zone_id) → recettes table | LookupRecord | B1 - LookupRecord [DISABLED] | 🔴 DISABLED |
| `parcel_id` | Const / Lookup | LookupRecord | B1 - LookupRecord [DISABLED] | 🔴 DISABLED |
| `health_score` | `(temp_ok + humidity_ok + co2_ok + ph_ok) / 4 * 100` | ExecuteScript | B2 - ExecuteScript (VPD) | ❌ Calcule VPD, pas health |
| `days_since_planting` | `now() - planting_date` | ExecuteScript | B2 - ExecuteScript | ❌ Pas implémenté |
| `growth_stage` | Lookup ou const | LookupRecord | B1 - LookupRecord [DISABLED] | 🔴 DISABLED |
| `vapor_pressure_deficit` | `(temp, humidity) → VPD formula` | ExecuteScript | B2 - ExecuteScript (VPD) | 🟢 OK |
| `ref_temp_opt`, `ref_humidity_opt`, etc. | Join recettes | LookupRecord | B1 - LookupRecord [DISABLED] | 🔴 DISABLED |
| `predicted_*` | ML Models | Zone 4 | Zone 4 | ❌ Pas exécuté |
| `anomaly_*` | ML Models | Zone 4 | Zone 4 | ❌ Pas exécuté |
| `maintenance_*` | ML Models | Zone 4 | Zone 4 | ❌ Pas exécuté |

---

## 🚨 Résumé des Bottlenecks

### Bottleneck #1: Zone 0 → Zone 1 Pas de Consommation Kafka
**Problème**: Zone 0 publie dans `vertiflow.external.*` mais Zone 1 n'a pas de ConsumeKafka pour ces topics  
**Impact**: 11 colonnes NASA/Open-Meteo perdues  
**Fix**: Ajouter 3 × ConsumeKafka_2_6 en Zone 1

### Bottleneck #2: LookupRecord DISABLED en Zone 2
**Problème**: B1 - LookupRecord est DISABLED → pas de jointure recettes  
**Impact**: `rack_id`, `parcel_id`, `growth_stage`, `ref_*_target` = NULL  
**Fix**: ENABLE B1 + configurer lookup table

### Bottleneck #3: ExecuteScript Zone 2 Calcule VPD Mais Pas Health Score
**Problème**: B2 calcule `vapor_pressure_deficit` mais pas `health_score` ni `days_since_planting`  
**Impact**: Dashboard 05, 07, 08 vides (besoin health_score)  
**Fix**: Ajouter logique calcul health_score dans ExecuteScript

### Bottleneck #4: Données ML Pas Générées
**Problème**: Zone 4 ne consomme pas de données (ConsumeKafka DISABLED)  
**Impact**: Pas de `predicted_*`, `anomaly_*`, `maintenance_*`  
**Fix**: Générer données ML ou ENABLE Zone 4 + joindre aux enregistrements

---

## 📋 Action Plan (Sans Casser la Structure)

### ✅ ACTION 1: Ajouter ConsumKafka en Zone 1 (5 min)
```
Zone 1 + 3 nouveaux processeurs:
  • ConsumeKafka (NASA) → vertiflow.external.nasa
  • ConsumeKafka (Weather) → vertiflow.external.weather
  • ConsumeKafka (AirQuality) → vertiflow.external.airquality
  ↓ Fusionner avec MergeContent existant
```

### ✅ ACTION 2: ENABLE LookupRecord Zone 2 (2 min)
```
Zone 2:
  B1 - LookupRecord: DISABLED → RUNNING
  Lookup Service: Simple Key Value ou MongoDB
  Mapping: zone_id → (rack_id, growth_stage, parcel_id)
```

### ✅ ACTION 3: Enrichir ExecuteScript Zone 2 (10 min)
```
B2 - ExecuteScript ajouter calcul:
  health_score = avg(temp_ok%, humidity_ok%, co2_ok%, ph_ok%)
  days_since_planting = days_between(timestamp, planting_date)
  growth_stage = lookup ou défaut
```

### ✅ ACTION 4: ENABLE ConsumeKafka Zone 4 + JOIN (10 min)
```
Zone 4:
  D0 - ConsumeKafka (Feedback): DISABLED → RUNNING
  Joindre ml_predictions (si disponible) avec telemetry
```

---

## 🎯 Conclusion

**Zone 0**: Fonctionne ✅ (mais données perdues en Kafka)  
**Zone 1**: Reçoit données brutes ✅ (mais incomplet - manque colonnes externes)  
**Zone 2**: Partiellement actif ⚠️ (LookupRecord DISABLED, calculs incomplets)  
**Zone 4**: DISABLED ❌ (pas de données ML générées)

**Résultat**: Toutes les colonnes attendues existent dans NiFi, mais **elles ne sont pas connectées entre elles** → data silos.

**Fix Time**: ~30 minutes pour tout reconnecter + ~1 heure pour valider les données.
