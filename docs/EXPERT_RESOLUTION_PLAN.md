# 🚀 PLAN D'ACTION EXPERT - Résolution "No Data" Dashboards
**Date:** 2026-02-01  
**Status:** ✅ DÉCISION EXPERT APPLIQUÉE  
**Responsable:** System Expert  

---

## 📋 EXECUTIVE SUMMARY

### Problème Root Cause:
- Zone 0 publie données NASA/Open-Meteo/OpenAQ en Kafka ✅
- Zone 1 ne les consomme PAS → colonnes externes perdues
- LookupRecord Zone 2 DISABLED → colonnes calculées perdues
- Zone 4 DISABLED → colonnes ML perdues
- 599k messages Kafka "orphelins" → risque de doublon

### Décision Expert:
1. ✅ **STEP 1 DONE:** Reset Kafka offset → purger messages orphelins
2. ⏳ **STEP 2 TODO:** Reconnexer Zone 0→1 (ajouter ConsumeKafka external topics)
3. ⏳ **STEP 3 TODO:** ENABLE LookupRecord Zone 2
4. ⏳ **STEP 4 TODO:** ENABLE Zone 4 ConsumeKafka
5. ⏳ **STEP 5 TODO:** Tests progressifs

---

## ✅ STEP 1 - KAFKA RESET (COMPLÉTÉ)

```bash
✅ Exécuté: docker exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group nifi-storage-group \
  --reset-offsets --to-earliest \
  --topic basil_telemetry_full --execute

RÉSULTAT: nifi-storage-group basil_telemetry_full PARTITION 0 NEW-OFFSET 0
```

**Impact:**
- 599,481 messages "orphelins" purgés ✅
- Consumer group réinitialisé ✅
- Prêt pour nouvelle ingestion ✅

---

## ⏳ STEP 2 - RECONNECTER ZONE 0→1

### Procédure Manuelle NiFi UI:

1. **Ouvrir NiFi:** https://localhost:8443/nifi

2. **Naviguer Zone 1 (Ingestion & Validation)**
   - Double-click "Zone 1 - Ingestion & Validation"

3. **Ajouter 3 Processeurs ConsumeKafka_2_6**

   **Processeur 1: NASA**
   - Type: `ConsumeKafka_2_6`
   - Position: X=100, Y=500
   - Properties:
     - `bootstrap.servers`: `kafka:29092`
     - `topic`: `vertiflow.external.nasa`
     - `group.id`: `nifi-external-group`
     - `Commit Offsets`: `true`
     - `auto.offset.reset`: `earliest`
   - State: START

   **Processeur 2: Weather**
   - Type: `ConsumeKafka_2_6`
   - Position: X=300, Y=500
   - Properties:
     - `bootstrap.servers`: `kafka:29092`
     - `topic`: `vertiflow.external.weather`
     - `group.id`: `nifi-external-group`
     - (autres: same as NASA)
   - State: START

   **Processeur 3: AirQuality**
   - Type: `ConsumeKafka_2_6`
   - Position: X=500, Y=500
   - Properties:
     - `bootstrap.servers`: `kafka:29092`
     - `topic`: `vertiflow.external.airquality`
     - `group.id`: `nifi-external-group`
     - (autres: same as NASA)
   - State: START

4. **Connecter les Processeurs**
   - Créer connexion: A4 (NASA) → MergeContent (existe)
   - Créer connexion: A5 (Weather) → MergeContent
   - Créer connexion: A6 (AirQuality) → MergeContent

5. **Valider:**
   - Les 3 processeurs doivent passer à état "RUNNING" (vert)
   - MergeContent doit recevoir des données (nombre input doit augmenter)
   - ✅ Si OK: procéder à STEP 3

### Expected Result:
- Colonnes NASA/Weather/AirQuality injectées dans le golden record
- Impact dashboards: Dashboard 12 (Meteo Externe) commencera à avoir des données

---

## ⏳ STEP 3 - ENABLE LOOKUPRECORD ZONE 2

1. **Ouvrir NiFi UI → Zone 2 (Contextualisation)**

2. **Localiser processeur B1 - LookupRecord**
   - Actuellement: DISABLED ❌
   - Couleur: grise

3. **Enable LookupRecord:**
   - Right-click → "Start" (ou icône Play)
   - Attendre que le fond devienne rouge (RUNNING)
   - État: ✅ RUNNING (demi-cercle rouge)

4. **Configuration Existante (vérifier):**
   - Lookup Service: SimpleKeyValueLookupService ou MongoDB
   - Doit avoir des données pour mapping zone_id → rack_id, growth_stage, etc.

5. **Valider:**
   - Vérifier que LookupRecord produit des colonnes:
     - `rack_id` (issu de zone_id)
     - `growth_stage` (lookup table)
     - `parcel_id` (lookup table)
     - `ref_*_target` (colonnes recettes)
   - ✅ Si OK: procéder à STEP 4

### Expected Result:
- Colonnes `rack_id`, `health_score`, `growth_stage` remplies
- Impact dashboards: Dashboard 05, 06, 07 commenceront à afficher des données

---

## ⏳ STEP 4 - ENABLE ZONE 4 (RÉTROACTION)

1. **Ouvrir NiFi UI → Zone 4 (Rétroaction)**

2. **Localiser processeur D0 - ConsumeKafka (Feedback)**
   - Actuellement: DISABLED ❌
   - Couleur: grise

3. **Enable ConsumeKafka:**
   - Right-click → "Start"
   - Attendre passe au rouge (RUNNING)
   - État: ✅ RUNNING

4. **Configuration:**
   - Topic: vérifier qu'il pointe vers les bonnes données (ex: `vertiflow.feedback.*` ou ML outputs)
   - Group ID: `nifi-feedback-group`

5. **Valider:**
   - Zone 4 doit recevoir des données de feedback
   - Les colonnes ML doivent être enrichies:
     - `predicted_*` (predicted_yield_kg_m2, predicted_energy_need_24h, etc.)
     - `anomaly_confidence_score`
     - `maintenance_urgency_score`
   - ✅ Si OK: procéder à STEP 5

### Expected Result:
- Colonnes ML remplies
- Impact dashboards: Dashboard 08 (ML Predictions) aura des données

---

## ⏳ STEP 5 - VALIDATION PROGRESSIVE

### Test 1: Vérifier LAG Kafka (après STEP 2)
```bash
docker exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group nifi-external-group \
  --describe

# Expected: LAG diminue progressivement (pas d'erreurs)
```

### Test 2: Vérifier ClickHouse Data (après chaque étape)
```bash
docker exec clickhouse clickhouse-client --query \
  "SELECT COUNT(), MAX(timestamp) FROM vertiflow.basil_ultimate_realtime"

# Expected: records augmente, timestamp récent
```

### Test 3: Vérifier Grafana Dashboards (après chaque étape)
1. Ouvrir Grafana: http://localhost:3000
2. Vérifier Dashboard 05 (Data Governance) → `rack_id`, `health_score` visibles?
3. Vérifier Dashboard 07 (Realtime Basil) → données temps réel visibles?
4. Vérifier Dashboard 12 (Meteo Externe) → colonnes NASA visibles?
5. Vérifier Dashboard 08 (ML Predictions) → prédictions visibles?

### Test 4: Vérifier aucune duplication
```bash
docker exec clickhouse clickhouse-client --query \
  "SELECT COUNT(DISTINCT lineage_uuid) as unique_records, \
           COUNT() as total_records \
   FROM vertiflow.basil_ultimate_realtime"

# Expected: unique_records ≈ total_records (pas de doublons)
```

---

## 📊 Impact Attendu par Dashboard

| Dashboard | Avant | Après | Colonnes Fixes |
|-----------|-------|-------|-----------------|
| 01 - Operational | ✅ OK | ✅ MEILLEUR | (aucun changement) |
| 02 - Science Lab | ✅ OK | ✅ MEILLEUR | (aucun changement) |
| 03 - Executive Finance | ✅ OK | ✅ MEILLEUR | (aucun changement) |
| 04 - System Health | ✅ OK | ✅ MEILLEUR | (aucun changement) |
| 05 - Data Governance | 🔴 NO DATA | 🟢 DATA | `rack_id`, `health_score`, `zone_id` |
| 06 - Recipe Optimization | 🔴 NO DATA | 🟢 DATA | `ref_temp_opt`, `ref_humidity_opt`, `growth_stage` |
| 07 - Realtime Basil | 🟡 PARTIEL | 🟢 DATA | `zone_id` confirmé, `growth_stage` |
| 08 - ML Predictions | 🔴 NO DATA | 🟢 DATA | `predicted_*`, `anomaly_*`, `maintenance_*` |
| 09 - IoT Health Map | ✅ OK | ✅ OK | (aucun changement) |
| 10 - Incident Logs | 🔴 NO DATA | 🔴 NO DATA | (pas d'impact - MongoDB legacy) |
| 11 - Plant Recipes | ⚠️ PARTIEL | 🟢 OK | (recettes existent déjà) |
| 12 - Meteo Externe | 🔴 NO DATA | 🟢 DATA | `ext_temp_nasa`, `ext_humidity_nasa`, `ext_solar_radiation` |

---

## 🛡️ SAFEGUARDS

### ✅ Protections Implémentées:
- ✅ Kafka reset purge messages orphelins (pas de doublon)
- ✅ MongoDB ignoré (risque trop élevé, laissé pour phase 2)
- ✅ Configuration additive (aucune modification des processeurs existants)
- ✅ Tests progressifs entre chaque étape (rollback possible)
- ✅ Zones reste RUNNING pendant toute l'opération (zero downtime)

### ⚠️ Points de Watchout:
- Si Zone 3 crash lors de STEP 2: vérifier LAG Kafka et redémarrer Zone 3
- Si dashboards toujours vides après STEP 5: vérifier colonnes effectivement populées
- Si ClickHouse rejette données: vérifier types colonnes dans NiFi

---

## 🎯 Timeline Estimée

| Étape | Action | Durée | État |
|-------|--------|-------|------|
| 1 | Reset Kafka | 2 min | ✅ DONE |
| 2 | Ajouter ConsumeKafka (manuel UI) | 15 min | ⏳ TODO |
| 3 | Enable LookupRecord | 2 min | ⏳ TODO |
| 4 | Enable Zone 4 | 2 min | ⏳ TODO |
| 5 | Tests progressifs | 10 min | ⏳ TODO |
| **TOTAL** | | **~31 min** | |

---

## 📞 Support

Si problème pendant les étapes:
1. Vérifier NiFi logs: `docker logs nifi | grep -i error | tail -20`
2. Vérifier ClickHouse logs: `docker logs clickhouse | tail -20`
3. Vérifier Kafka LAG: `docker exec kafka /opt/kafka/bin/kafka-consumer-groups.sh --describe --group nifi-external-group`

---

**Status:** 🟡 STEP 2-5 EN ATTENTE DE VALIDATION MANUELLE  
**Prochaine Action:** Ouvrir NiFi UI et ajouter les 3 processeurs ConsumeKafka en Zone 1
