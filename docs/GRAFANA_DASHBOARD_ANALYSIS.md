# 📊 Analyse des Dashboards Grafana - VertiFlow Cloud

**Date**: 2026-02-01  
**Version**: v4.2.0  
**Auteur**: Analyse Automatique  
**Statut**: ✅ COMPLET

---

## 🎯 Résumé Exécutif

### Vue d'Ensemble
- **Total Dashboards**: 12
- **Datasource Principale**: ClickHouse (uid: aeb1b4ee-1f88-42c3-a35a-f594cac90e00)
- **Datasource Secondaire**: Prometheus (uid: eac5c342-46aa-46b8-934f-8e09892a5192)
- **Database ClickHouse**: `vertiflow`
- **Statut Connexion**: ✅ CONFIGURÉ

---

## 📁 Inventaire des Dashboards

### 1. **01_operational_cockpit.json**
- **Titre**: Cockpit Opérationnel
- **Cible**: Vue d'ensemble des opérations quotidiennes
- **Datasource**: ClickHouse (défaut)

### 2. **02_science_lab.json** 🔬
- **Titre**: VertiFlow Science Lab
- **Cible**: Analyse scientifique et recherche
- **Datasource**: ClickHouse
- **Tables Utilisées**:
  - `vertiflow.basil_ultimate_realtime`
- **Métriques Scientifiques**:
  - Taux de photosynthèse (`photosynthetic_rate_max`)
  - Indice de chlorophylle SPAD (`chlorophyll_index_spad`)
  - Nutriments NPK (`nutrient_n_total`, `nutrient_p_phosphorus`, `nutrient_k_potassium`)
  - Nutriments secondaires (`nutrient_ca_calcium`, `nutrient_mg_magnesium`, `nutrient_fe_iron`)
  - Intensité lumineuse PPFD (`light_intensity_ppfd`)
  - DLI accumulé (`light_dli_accumulated`)
  - Ratio lumière rouge/bleue (`light_ratio_red_blue`, `light_far_red_intensity`)
  - Différentiels de température (`leaf_temp_delta`)
  - Consommation CO2 (`co2_consumption_rate`)
  - Efficacité d'utilisation de la lumière (`light_use_efficiency`)

### 3. **03_executive_finance.json**
- **Titre**: Dashboard Exécutif & Finance
- **Cible**: Métriques business et ROI
- **Datasource**: ClickHouse

### 4. **04_system_health.json**
- **Titre**: Santé Système
- **Cible**: Monitoring infrastructure
- **Datasource**: ClickHouse + Prometheus

### 5. **05_data_governance.json**
- **Titre**: Data Governance
- **Cible**: Qualité et traçabilité des données
- **Datasource**: ClickHouse

### 6. **06_recipe_optimization.json**
- **Titre**: Optimisation des Recettes
- **Cible**: Amélioration continue Cortex A11
- **Datasource**: ClickHouse

### 7. **07_realtime_basil.json** 🌿
- **Titre**: Basil Temps Réel
- **Cible**: Monitoring production basilic en direct
- **Datasource**: ClickHouse
- **Tables Utilisées**:
  - `vertiflow.basil_ultimate_realtime`
- **Métriques Temps Réel**:
  - Nombre total d'enregistrements (`count()`)
  - Température moyenne (`air_temp_internal`)
  - Température eau (`water_temp`)
  - Humidité moyenne (`air_humidity`)
  - Zones actives (`zone_id`)
  - Niveau CO2 (`co2_level_ambient`)
  - Intensité lumineuse PPFD (`light_intensity_ppfd`)
  - pH moyen (`water_ph`)
  - EC moyenne (`nutrient_solution_ec`)
- **Rafraîchissement**: 30s (données live)

### 8. **08_ml_predictions.json**
- **Titre**: Prédictions Machine Learning
- **Cible**: Modèles prédictifs et forecasting
- **Datasource**: ClickHouse

### 9. **09_iot_health_map.json** 🗺️
- **Titre**: Carte Santé IoT
- **Cible**: Géolocalisation et statut capteurs
- **Datasource**: ClickHouse
- **Tables Utilisées**:
  - `vertiflow.iot_sensors`
- **Métriques IoT**:
  - Total capteurs (`sensor_id`)
  - Statuts: online, offline, warning, error, maintenance
  - Score de santé (`health_score`)
  - Niveau batterie (`battery_level`)
  - Types de capteurs (`sensor_type`)
  - Géolocalisation (`latitude`, `longitude`)
  - Répartition zones (`zone_id`, `rack_id`)
- **Carte Géographique**:
  - Centrage: Casablanca (33.574°N, -7.590°W)
  - Zoom: 17 (niveau bâtiment)
  - Basemap: OpenStreetMap

### 10. **10_incident_logs.json**
- **Titre**: Logs d'Incidents
- **Cible**: Traçabilité incidents et alertes
- **Datasource**: ClickHouse

### 11. **11_plant_recipes.json** 🌱
- **Titre**: Dashboard des Recettes de Culture
- **Cible**: Recettes initiales et optimales Cortex A11
- **Datasource**: ClickHouse
- **Tables Utilisées**:
  - `vertiflow.plant_recipes`
- **Métriques Recettes**:
  - Nombre recettes initiales (`type = 'initial'`)
  - Nombre recettes optimales (`type = 'optimal'`)
  - Score optimisation moyen (`optimization_score`)
  - Types de plantes (`plant_type`)
  - Paramètres environnementaux:
    - Température optimale (`temp_optimal`)
    - Humidité optimale (`humidity_optimal`)
    - CO2 optimal (`co2_optimal`)
    - pH optimal (`ph_optimal`)
    - EC optimale (`ec_optimal`)
    - DLI optimal (`dli_optimal`)
  - Nutriments NPK:
    - Azote (`nitrogen_optimal`)
    - Phosphore (`phosphorus_optimal`)
    - Potassium (`potassium_optimal`)
  - Améliorations Cortex A11:
    - Augmentation rendement (`yield_increase`)
    - Augmentation qualité (`quality_increase`)
    - Réduction énergie (`energy_reduction`)
  - Métadonnées:
    - Stade de croissance (`growth_stage`)
    - Statut (`status`)
    - Version (`version`)
    - Système optimisation (`optimized_by`)
    - Date mise à jour (`updated_at`)

### 12. **12_meteo_externe.json**
- **Titre**: Météo Externe
- **Cible**: Données météorologiques externes (NASA POWER)
- **Datasource**: ClickHouse

---

## 🔌 Configuration des Datasources

### Datasource ClickHouse (Principal)
```yaml
Name: ClickHouse
Type: grafana-clickhouse-datasource
UID: aeb1b4ee-1f88-42c3-a35a-f594cac90e00
URL: http://clickhouse:8123
Database: vertiflow
Access: proxy
Default: true
Editable: true
```

### Datasource Prometheus (Monitoring Infrastructure)
```yaml
Name: Prometheus
Type: prometheus
UID: eac5c342-46aa-46b8-934f-8e09892a5192
URL: http://prometheus:9090
Access: proxy
Default: false
```

---

## 📊 Mapping Tables ClickHouse → Dashboards

### Tables Identifiées dans les Dashboards

#### 1. `vertiflow.basil_ultimate_realtime`
**Utilisée par**:
- ✅ **07_realtime_basil.json** (monitoring temps réel)
- ✅ **02_science_lab.json** (analyses scientifiques)

**Colonnes Requises**:
- `timestamp` (DateTime)
- `zone_id` (String)
- `air_temp_internal` (Float64)
- `water_temp` (Float64)
- `air_humidity` (Float64)
- `co2_level_ambient` (Float64)
- `light_intensity_ppfd` (Float64)
- `water_ph` (Float64)
- `nutrient_solution_ec` (Float64)
- `photosynthetic_rate_max` (Float64)
- `chlorophyll_index_spad` (Float64)
- `nutrient_n_total` (Float64)
- `nutrient_p_phosphorus` (Float64)
- `nutrient_k_potassium` (Float64)
- `nutrient_ca_calcium` (Float64)
- `nutrient_mg_magnesium` (Float64)
- `nutrient_fe_iron` (Float64)
- `light_dli_accumulated` (Float64)
- `light_ratio_red_blue` (Float64)
- `light_far_red_intensity` (Float64)
- `leaf_temp_delta` (Float64)
- `ext_temp_nasa` (Float64)
- `co2_consumption_rate` (Float64)
- `light_use_efficiency` (Float64)

**Statut**: ⚠️ **TABLE NÉCESSAIRE** (fichier CSV existe mais pas encore importé)

---

#### 2. `vertiflow.plant_recipes`
**Utilisée par**:
- ✅ **11_plant_recipes.json** (recettes culture)

**Colonnes Requises**:
- `recipe_id` (String)
- `name` (String)
- `plant_type` (String)
- `type` (Enum: 'initial', 'optimal')
- `growth_stage` (String)
- `temp_optimal` (Float64)
- `humidity_optimal` (Float64)
- `co2_optimal` (Float64)
- `ph_optimal` (Float64)
- `ec_optimal` (Float64)
- `dli_optimal` (Float64)
- `nitrogen_optimal` (Float64)
- `phosphorus_optimal` (Float64)
- `potassium_optimal` (Float64)
- `optimization_score` (Float64)
- `yield_increase` (Float64)
- `quality_increase` (Float64)
- `energy_reduction` (Float64)
- `optimized_by` (String)
- `status` (String)
- `version` (String)
- `updated_at` (DateTime)

**Statut**: ⚠️ **TABLE EXISTE** mais Dashboard référence `plant_recipes` au lieu de `basil_recipes`  
**Action Requise**: Vérifier nom de table ou créer alias

---

#### 3. `vertiflow.iot_sensors`
**Utilisée par**:
- ✅ **09_iot_health_map.json** (géolocalisation capteurs)

**Colonnes Requises**:
- `sensor_id` (String)
- `sensor_type` (String)
- `status` (Enum: 'online', 'offline', 'warning', 'error', 'maintenance')
- `health_score` (Float64)
- `battery_level` (Float64)
- `latitude` (Float64)
- `longitude` (Float64)
- `zone_id` (String)
- `rack_id` (String)

**Statut**: ❌ **TABLE MANQUANTE** (pas créée, pas de données)

---

## ⚠️ Problèmes Identifiés

### 🔴 Critique

#### 1. **Table `basil_ultimate_realtime` Non Importée**
- **Dashboards Impactés**: 07_realtime_basil.json, 02_science_lab.json
- **Fichier Source**: `basil_ultimate_realtime1.csv` (racine du projet)
- **Impact**: 2 dashboards majeurs non fonctionnels
- **Solution**: Importer CSV vers ClickHouse

#### 2. **Discordance Nom Table `plant_recipes` vs `basil_recipes`**
- **Dashboard Impacté**: 11_plant_recipes.json
- **Situation**: Dashboard référence `plant_recipes`, mais la table importée est `basil_recipes`
- **Impact**: Dashboard recettes non fonctionnel
- **Solutions**:
  - Option A: Renommer table `basil_recipes` → `plant_recipes` dans ClickHouse
  - Option B: Créer alias/vue `plant_recipes` pointant vers `basil_recipes`
  - Option C: Modifier dashboard JSON pour utiliser `basil_recipes`

#### 3. **Table `iot_sensors` Complètement Manquante**
- **Dashboard Impacté**: 09_iot_health_map.json
- **Situation**: Table jamais créée, aucune donnée
- **Impact**: Dashboard géolocalisation IoT non fonctionnel
- **Solution**: Créer table et générer données fictives ou mapper depuis tables existantes

### 🟡 Avertissements

#### 4. **Absence de Données `ref_plant_recipes`**
- **Statut Actuel**: Table existe avec 6 recettes (✅ RÉSOLU dans conversation précédente)
- **Note**: Cette table pourrait être utilisée par d'autres dashboards non analysés

#### 5. **Tables Référence Non Utilisées dans Dashboards**
- Tables créées mais non référencées:
  - `ref_light_spectra` (3 enregistrements)
  - `ref_nutrient_measurements` (18 enregistrements)
  - `ref_quality_thresholds` (11 enregistrements)
  - `ref_aroma_profiles` (134 enregistrements)
  - `ref_photosynthesis_curves` (200 enregistrements)
  - `ref_sensory_evaluation` (150 enregistrements)
  - `ref_mit_openag_experiments` (1 enregistrement)
- **Impact**: Aucun (tables peuvent servir pour analyses futures ou ML)

---

## ✅ Données Déjà Disponibles

### Tables ClickHouse Peuplées (4,350+ records)

| Table | Records | Statut Dashboard | Utilisée Par |
|-------|---------|------------------|--------------|
| `basil_recipes` | 6 | ⚠️ Nom discordant | 11_plant_recipes (attends `plant_recipes`) |
| `led_spectrum_data` | 3,320 | ✅ OK (non utilisée dashboards) | - |
| `iot_nutrient_measurements` | 501 | ✅ OK (non utilisée dashboards) | - |
| `ref_light_spectra` | 3 | ✅ OK (non utilisée dashboards) | - |
| `ref_nutrient_measurements` | 18 | ✅ OK (non utilisée dashboards) | - |
| `ref_quality_thresholds` | 11 | ✅ OK (non utilisée dashboards) | - |
| `ref_aroma_profiles` | 134 | ✅ OK (non utilisée dashboards) | - |
| `ref_photosynthesis_curves` | 200 | ✅ OK (non utilisée dashboards) | - |
| `ref_sensory_evaluation` | 150 | ✅ OK (non utilisée dashboards) | - |
| `ref_mit_openag_experiments` | 1 | ✅ OK (non utilisée dashboards) | - |
| `ref_plant_recipes` | 6 | ✅ OK (non utilisée dashboards) | - |

---

## 🔧 Plan d'Action Recommandé

### Phase 1: Résolution Critique (Priorité HAUTE)

#### Action 1.1: Importer `basil_ultimate_realtime.csv`
```sql
-- Créer table si nécessaire
CREATE TABLE IF NOT EXISTS vertiflow.basil_ultimate_realtime (
    timestamp DateTime,
    zone_id String,
    air_temp_internal Float64,
    water_temp Float64,
    air_humidity Float64,
    co2_level_ambient Float64,
    light_intensity_ppfd Float64,
    water_ph Float64,
    nutrient_solution_ec Float64,
    photosynthetic_rate_max Float64,
    chlorophyll_index_spad Float64,
    nutrient_n_total Float64,
    nutrient_p_phosphorus Float64,
    nutrient_k_potassium Float64,
    nutrient_ca_calcium Float64,
    nutrient_mg_magnesium Float64,
    nutrient_fe_iron Float64,
    light_dli_accumulated Float64,
    light_ratio_red_blue Float64,
    light_far_red_intensity Float64,
    leaf_temp_delta Float64,
    ext_temp_nasa Float64,
    co2_consumption_rate Float64,
    light_use_efficiency Float64
) ENGINE = MergeTree()
ORDER BY (zone_id, timestamp);

-- Importer CSV
-- Script Python requis pour parser et insérer données
```

**Dashboards Débloqués**: 07_realtime_basil.json, 02_science_lab.json

---

#### Action 1.2: Résoudre Discordance `plant_recipes`
**Option Recommandée: Créer Alias dans ClickHouse**

```sql
-- Option A: Créer vue matérialisée (alias)
CREATE VIEW vertiflow.plant_recipes AS 
SELECT * FROM vertiflow.basil_recipes;
```

OU

**Option Alternative: Renommer Table**
```sql
-- Option B: Renommer table existante
RENAME TABLE vertiflow.basil_recipes TO vertiflow.plant_recipes;
```

**Dashboard Débloqué**: 11_plant_recipes.json

---

#### Action 1.3: Créer Table `iot_sensors`
**Option 1: Mapper depuis données existantes**

```sql
-- Créer table
CREATE TABLE IF NOT EXISTS vertiflow.iot_sensors (
    sensor_id String,
    sensor_type String,
    status Enum8('online'=1, 'offline'=2, 'warning'=3, 'error'=4, 'maintenance'=5),
    health_score Float64,
    battery_level Float64,
    latitude Float64,
    longitude Float64,
    zone_id String,
    rack_id String,
    last_seen DateTime
) ENGINE = MergeTree()
ORDER BY (zone_id, sensor_id);

-- Insérer données fictives basées sur led_spectrum_data et iot_nutrient_measurements
INSERT INTO vertiflow.iot_sensors
SELECT 
    sensor_id,
    'LED' as sensor_type,
    'online' as status,
    95.0 as health_score,
    100.0 as battery_level,
    33.574 + (rand() % 100 - 50) * 0.0001 as latitude,
    -7.590 + (rand() % 100 - 50) * 0.0001 as longitude,
    zone_name as zone_id,
    rack_id,
    now() as last_seen
FROM vertiflow.led_spectrum_data
GROUP BY sensor_id, zone_name, rack_id
LIMIT 50;
```

**Dashboard Débloqué**: 09_iot_health_map.json

---

### Phase 2: Validation (Priorité MOYENNE)

#### Action 2.1: Tester Connexion Datasources
```bash
# Tester ClickHouse depuis Grafana
curl -X POST http://localhost:3000/api/datasources/uid/aeb1b4ee-1f88-42c3-a35a-f594cac90e00/health \
  -H "Content-Type: application/json" \
  -u admin:admin

# Tester Prometheus
curl -X POST http://localhost:3000/api/datasources/uid/eac5c342-46aa-46b8-934f-8e09892a5192/health \
  -H "Content-Type: application/json" \
  -u admin:admin
```

#### Action 2.2: Vérifier Import Dashboards
```bash
# Lister dashboards provisionnés
curl http://localhost:3000/api/search?type=dash-db -u admin:admin | jq .

# Vérifier nombre de dashboards (doit être 12)
curl http://localhost:3000/api/search?type=dash-db -u admin:admin | jq '. | length'
```

#### Action 2.3: Valider Requêtes SQL
- Ouvrir chaque dashboard dans Grafana UI
- Vérifier panels chargent les données
- Identifier erreurs SQL dans les logs

---

### Phase 3: Optimisation (Priorité BASSE)

#### Action 3.1: Créer Index Optimisés
```sql
-- Index pour table basil_ultimate_realtime
ALTER TABLE vertiflow.basil_ultimate_realtime 
ADD INDEX idx_zone (zone_id) TYPE bloom_filter GRANULARITY 3;

-- Index pour plant_recipes
ALTER TABLE vertiflow.plant_recipes 
ADD INDEX idx_type (type) TYPE set(100) GRANULARITY 1;
```

#### Action 3.2: Ajouter Rétention Données Temps Réel
```sql
-- TTL 90 jours pour basil_ultimate_realtime
ALTER TABLE vertiflow.basil_ultimate_realtime 
MODIFY TTL timestamp + INTERVAL 90 DAY;
```

---

## 📈 Statistiques d'Utilisation

### Dashboards par Catégorie

| Catégorie | Nombre | Dashboards |
|-----------|--------|------------|
| **Production** | 3 | 07_realtime_basil, 11_plant_recipes, 06_recipe_optimization |
| **Science/R&D** | 2 | 02_science_lab, 08_ml_predictions |
| **Infrastructure** | 3 | 04_system_health, 09_iot_health_map, 10_incident_logs |
| **Business** | 2 | 01_operational_cockpit, 03_executive_finance |
| **Gouvernance** | 2 | 05_data_governance, 12_meteo_externe |

### Tables ClickHouse par Fréquence d'Usage

| Table | Dashboards Utilisateurs | Priorité |
|-------|-------------------------|----------|
| `basil_ultimate_realtime` | 2 | 🔴 CRITIQUE |
| `plant_recipes` | 1 | 🔴 CRITIQUE |
| `iot_sensors` | 1 | 🔴 CRITIQUE |
| `ref_*` (tables référence) | 0 | 🟢 OPTIONNEL |

---

## 🔍 Vérifications Finales

### Checklist Datasources
- [x] ✅ Fichier `datasources.yml` existe
- [x] ✅ ClickHouse configuré avec database `vertiflow`
- [x] ✅ Prometheus configuré
- [x] ✅ UID datasources correspondent dans dashboards

### Checklist Tables ClickHouse
- [ ] ⏳ Table `basil_ultimate_realtime` créée et peuplée
- [ ] ⏳ Table `plant_recipes` accessible (alias ou renommage)
- [ ] ⏳ Table `iot_sensors` créée et peuplée
- [x] ✅ Tables `basil_recipes` + 10 tables référence peuplées (4,350 records)

### Checklist Dashboards
- [x] ✅ 12 fichiers JSON présents dans `/dashboards/grafana/`
- [ ] ⏳ Dashboards provisionnés dans Grafana
- [ ] ⏳ Panels fonctionnels sans erreurs SQL
- [ ] ⏳ Données visibles dans l'interface utilisateur

---

## 📝 Conclusion

### État Actuel
- **Datasources**: ✅ Correctement configurées
- **Dashboards**: ✅ 12 fichiers JSON valides
- **Tables ClickHouse**: ⚠️ 3 tables critiques manquantes/non mappées
- **Données**: ⚠️ 4,350 records importés mais dans tables non utilisées par dashboards

### Impact Business
- **Dashboards Fonctionnels**: 7/12 (58%) - estimation sans tests
- **Dashboards Critiques Bloqués**: 3 (realtime, recipes, iot_map)
- **Risque**: MOYEN - Données existent mais mappings incomplets

### Prochaines Étapes Recommandées
1. **URGENT**: Importer `basil_ultimate_realtime.csv` (débloque 2 dashboards majeurs)
2. **URGENT**: Créer alias `plant_recipes` (débloque dashboard recettes)
3. **IMPORTANT**: Créer table `iot_sensors` (débloque carte IoT)
4. **VALIDATION**: Tester connexion Grafana → ClickHouse
5. **OPTIMISATION**: Ajouter index et TTL

---

**Rapport Généré**: 2026-02-01T15:30:00Z  
**Prochaine Révision**: Après implémentation Phase 1  
**Contact Support**: vertiflow-support@domain.com
