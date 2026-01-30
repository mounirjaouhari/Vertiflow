# Architecture du Flux NiFi - Plateforme VertiFlow

Ce document détaille la configuration des 4 Groupes de Processus (Process Groups) à implémenter dans l'interface NiFi (https://localhost:8443).

## 1. Groupe : COLLECTION & NORMALISATION (Zone 1)

**Objectif :** Transformer des sources hétérogènes en un JSON standardisé de 153 colonnes.

- **Processeur : `ConsumeMQTT`**
  - *Broker URI :* `tcp://mosquitto:1883`
  - *Topic :* `vertiflow/telemetry/#`
  - *Rôle :* Capte les données brutes des capteurs (Colonnes 11-100).
- **Processeur : `InvokeHTTP` (NASA Power API)**
  - *Remote URL :* `https://power.larc.nasa.gov/api/temporal/daily/point?...`
  - *Scheduling :* 1 heure.
  - *Rôle :* Récupère les données météo (Colonnes 77-80).
- **Processeur : `GetFile` (Labo CSV)**
  - *Input Directory :* `/opt/nifi/data/lab_input`
  - *Rôle :* Ingeste les résultats microbiomes (Colonnes 86-100).
- **Processeur : `ConvertRecord`**
  - *Record Reader :* `CSVReader` / `BinaryReader`
  - *Record Writer :* `JsonRecordSetWriter`
  - *Rôle :* Unifie toutes les entrées vers le format JSON.

## 2. Groupe : FUSION & ENRICHISSEMENT (Zone 2)

**Objectif :** Créer le "Golden Record" en ajoutant le contexte métier.

- **Processeur : `LookupRecord` (Jointure Contextuelle)**
  - *Lookup Service :* `SimpleKeyValueLookupService` (ou MongoDB Lookup).
  - *Rôle :* Ajoute `rack_id`, `parcel_id`, et `lease_id` en fonction de l'ID du capteur.
- **Processeur : `UpdateAttribute`**
  - *Attributs :* * `ingestion.timestamp` : `${now()}`
    - `environment.mode` : `PROD`
- **Processeur : `JoltTransformJSON`**
  - *Jolt Specification :* Définit la structure finale pour aligner les 153 colonnes, même si certaines sont nulles à ce stade.

## 3. Groupe : TRAÇABILITÉ & VALIDATION (Qualité Scientifique)

**Objectif :** Exécuter les algorithmes de vérification avant stockage.

- **Processeur : `ValidateRecord` (Validation du Contrat)**
  - *Schema Registry :* `AvroSchemaRegistry`
  - *Schema Access Strategy :* Utilise `/opt/nifi/schemas/telemetry_v3.json` (monté via Docker).
  - *Rôle :* Rejette toute donnée dont le type est incorrect (ex: String au lieu de Float).
- **Algorithme 1 & 2 : `ExecuteScript` (Python/Groovy)**
  - *Script :* Calcule le Z-Score en temps réel sur les colonnes critiques (Temp/pH).
  - *Logique :* Si `abs(value - mean) > 3 * std_dev`, ajout d'un flag `is_anomaly = true`.
- **Processeur : `CryptographicHashContent`**
  - *Hash Algorithm :* SHA-256.
  - *Rôle :* Génère le hash (Col 127) pour garantir l'intégrité face au bailleur.

## 4. Groupe : ROUTAGE & PUBLICATION (Zone 3 & 4)

**Objectif :** Distribuer la donnée aux consommateurs finaux.

- **Processeur : `RouteOnAttribute`**
  - *Condition "Critical" :* `${is_anomaly:equals('true')}` ou `${alert_level:gt(2)}`.
- **Processeur : `PublishKafka_2_6`**
  - *Kafka Brokers :* `kafka:29092` (Utilise le listener interne configuré dans votre docker-compose).
  - *Topic Name :* `basil_telemetry_full`
  - *Delivery Guarantee :* `Guarantee Replicated Delivery` (acks=all).
- **Processeur : `PutDatabaseRecord` (ClickHouse)**
  - *Record Reader :* `JsonTreeReader`
  - *Database Connection Pooling Service :* `DBCPConnectionPool`
  - *JDBC Connection URL :* `jdbc:clickhouse://clickhouse:8123/vertiflow`
  - *JDBC Driver Class :* `com.clickhouse.jdbc.ClickHouseDriver` (Placé dans `/opt/nifi/nifi-current/drivers`).

## Résumé des Flux de Rétroaction (Feedback)

1. **Succès :** Les données validées partent vers Kafka $\rightarrow$ ClickHouse $\rightarrow$ Power BI.
2. **Échec :** Les erreurs de schéma ou d'algorithme sont routées vers un dossier local `/opt/nifi/logs/quarantine` pour analyse par l'équipe Data.
3. **Alerte :** Les anomalies critiques déclenchent un `InvokeHTTP` vers un webhook Slack/Teams.