# Documentations sur les algorithmes 

# 📘 ALGORITHME A1 : NORMALISATION JSON & STANDARDISATION

Ticket JIRA : TICKET-019

Responsable : @Mouhammed (Data Engineer)

Sprint : Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme se situe au tout début de la chaîne de traitement, dans la **Zone 1 (Collection & Normalisation)** de **Apache NiFi**.

- **Entrée :** Données hétérogènes (Binaires MQTT, CSV Labo, JSON imbriqué API).
- **Sortie :** JSON standardisé "à plat" respectant le schéma des 153 colonnes.
- **Composant NiFi :** `JoltTransformJSON` ou `ExecuteScript` (Python).

## 2. Description Scientifique & Technique

L'objectif est de transformer des données "sales" et disparates en un format unique compréhensible par le reste du système (Kafka, ClickHouse, Mongo).

### Problème : L'Hétérogénéité des Sources

- **Capteur A (MQTT) envoie :** `{"v": 24.5, "id": "S1"}` (Noms courts pour économiser la batterie).
- **Capteur B (API) envoie :** `{"temperature": {"value": 24.5, "unit": "C"}, "device": "S1"}` (Structure imbriquée).
- **Labo (CSV) envoie :** `24.5;S1;2025-12-31` (Pas de clés).

### Solution : Le Mapping Pivot

L'algorithme applique une transformation pour aligner toutes ces variantes sur le schéma canonique `telemetry_v3.json` :

- `v` -> `air_temp_internal`
- `id` -> `sensor_hardware_id`
- Conversion de types (String "24.5" -> Float 24.5).

## 3. Implémentation (Spécification JOLT pour NiFi)

Si vous utilisez le processeur standard `JoltTransformJSON`, voici la spécification "Shift" pour normaliser un message MQTT typique.

```
[
  {
    "operation": "shift",
    "spec": {
      "t": "timestamp",
      "id": "sensor_hardware_id",
      "val": {
        "temp": "air_temp_internal",
        "hum": "air_humidity",
        "co2": "co2_level_ambient",
        "ppfd": "light_intensity_ppfd",
        "ec": "nutrient_solution_ec",
        "ph": "water_ph"
      },
      "meta": {
        "bat": "ups_battery_health",
        "err": "sensor_calibration_offset"
      }
    }
  },
  {
    "operation": "default",
    "spec": {
      "data_source_type": "IoT",
      "data_integrity_flag": 0
    }
  }
]
```

## 4. Implémentation Alternative (Script Python)

Pour des transformations plus complexes (nettoyage de chaînes, calculs simples), on utilise `ExecuteScript` avec Python.

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ALGORITHME A1 : NORMALISATION UNIVERSELLE
================================================================================
Description :
Convertit les payloads entrants en dictionnaire Python standardisé
correspondant aux 153 colonnes du Golden Record.
Gère les conversions de types et les valeurs par défaut.
================================================================================
"""

import json
import java.io
from org.apache.commons.io import IOUtils
from java.nio.charset import StandardCharsets
from org.apache.nifi.processor.io import StreamCallback

class Standardizer(StreamCallback):
    def __init__(self):
        pass

    def process(self, inputStream, outputStream):
        # 1. Lecture de l'entrée brute
        text = IOUtils.toString(inputStream, StandardCharsets.UTF_8)
        try:
            raw_data = json.loads(text)
        except ValueError:
            # Si ce n'est pas du JSON, on rejette (sera géré par le Failure)
            raise

        # 2. Création du Golden Record vide (Structure cible)
        golden_record = {
            "timestamp": None,
            "sensor_hardware_id": None,
            "air_temp_internal": None,
            "air_humidity": None,
            # ... (autres colonnes initialisées à None)
            "data_source_type": "IoT_Sensor"
        }

        # 3. Logique de Mapping (Exemple pour un capteur MQTT compact)
        # Mapping explicite : Source -> Cible
        if 't' in raw_data:
            golden_record['timestamp'] = raw_data['t'] # Format ISO8601 attendu
        
        if 'id' in raw_data:
            golden_record['sensor_hardware_id'] = str(raw_data['id']).upper()

        # Extraction des mesures (Aplatissement)
        if 'm' in raw_data: # 'm' pour mesures
            measures = raw_data['m']
            golden_record['air_temp_internal'] = self.safe_float(measures.get('t'))
            golden_record['air_humidity'] = self.safe_float(measures.get('h'))
            golden_record['co2_level_ambient'] = self.safe_int(measures.get('c'))

        # 4. Écriture de la sortie standardisée
        outputStream.write(json.dumps(golden_record).encode('utf-8'))

    def safe_float(self, value):
        """Conversion sécurisée en Float32"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def safe_int(self, value):
        """Conversion sécurisée en UInt16"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

# Exécution NiFi
flowFile = session.get()
if flowFile is not None:
    try:
        flowFile = session.write(flowFile, Standardizer())
        session.transfer(flowFile, REL_SUCCESS)
    except Exception as e:
        # En cas d'erreur de parsing JSON critique
        session.transfer(flowFile, REL_FAILURE)
```

## 5. Critères de Validation (Definition of Done)

- [ ] Toutes les clés du JSON de sortie existent dans le schéma `telemetry_v3.json`.
- [ ] Les types de données sont corrects (Pas de "24.5" string dans un champ float).
- [ ] Les champs manquants sont mis à `null` (pas d'erreur de clé manquante plus loin).
- [ ] Le timestamp est au format ISO 8601 UTC (`2025-12-31T12:00:00.000Z`).

# 🛡️ ALGORITHME A2 : DÉTECTION D'ABERRATION (Z-SCORE)

**Ticket JIRA :** `TICKET-020` **Responsable :** @Mouhammed (Data Engineer) **Sprint :** Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme est exécuté dans la **Zone 2 (Fusion & Enrichissement)** de **Apache NiFi**, juste après la normalisation et l'enrichissement, mais avant l'envoi vers Kafka.

- **Entrée :** JSON standardisé avec valeurs brutes (ex: `air_temp_internal`).
- **Sortie :** JSON enrichi avec les flags de qualité (`data_integrity_flag`, `anomaly_confidence_score`).
- **Composant NiFi :** `ExecuteScript` (Jython - Python sur JVM).

## 2. Description Scientifique & Technique

L'objectif est de filtrer les "bruits" et les erreurs de capteurs (valeurs aberrantes) sans perdre de données. Une donnée n'est jamais supprimée, elle est "marquée".

### Problème : La fiabilité des Capteurs IoT

Un capteur de température peut, à cause d'une baisse de tension ou d'une interférence, envoyer soudainement une valeur de **85°C** ou **-50°C** dans une serre chauffée. Si cette donnée entre dans la moyenne scientifique (ClickHouse), elle faussera toutes les corrélations (Algo A7).

### Solution : Le Test Statistique Z-Score

Le Z-Score mesure à combien d'écarts-types ($\sigma$) une donnée se trouve de la moyenne ($\mu$).

$$Z = \frac{X - \mu}{\sigma}$$

- Si $-3 < Z < 3$ : La donnée est considérée comme **STATISTIQUEMENT NORMALE** (99.7% des cas).
- Si $|Z| \ge 3$ : La donnée est une **ANOMALIE** (Outlier).

## 3. Implémentation (Script Python pour NiFi)

Ce script maintient un état léger (moyenne glissante simplifiée ou constantes de référence) pour calculer le score. Pour la production, les constantes $\mu$ et $\sigma$ sont souvent chargées depuis le *DistributedMapCache* de NiFi.

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ALGORITHME A2 : Z-SCORE FILTER
================================================================================
Description :
Analyse chaque mesure entrante et calcule son Z-Score par rapport aux
références historiques de la ferme.
Marque les données comme 'VALID' (0) ou 'INVALID' (1).
================================================================================
"""

import json
import math
from org.apache.commons.io import IOUtils
from java.nio.charset import StandardCharsets
from org.apache.nifi.processor.io import StreamCallback

class QualityControl(StreamCallback):
    def __init__(self):
        # --- CONFIGURATION (Cibles Expert - À dynamiser via Cache) ---
        # Format: 'colonne': (Moyenne_Attendue, Ecart_Type_Toléré)
        self.stats_profile = {
            'air_temp_internal': (24.0, 3.5),      # Moy 24°C, Varie entre 13.5 et 34.5
            'air_humidity': (60.0, 15.0),          # Moy 60%, Varie bcp
            'nutrient_solution_ec': (1.8, 0.4),    # EC très stable
            'water_ph': (6.0, 0.5)                 # pH critique
        }
        self.SIGMA_THRESHOLD = 3.0

    def process(self, inputStream, outputStream):
        # 1. Lecture
        text = IOUtils.toString(inputStream, StandardCharsets.UTF_8)
        try:
            record = json.loads(text)
        except ValueError:
            # Pas de JSON ? Laissez passer, l'algo A1 aurait dû filtrer.
            outputStream.write(text.encode('utf-8'))
            return

        # 2. Analyse
        anomalies_found = 0
        details = []

        # On itère sur les champs qu'on sait surveiller
        for field, (mean, std_dev) in self.stats_profile.items():
            val = record.get(field)
            
            if val is not None and isinstance(val, (int, float)):
                # Calcul Z-Score
                z_score = (val - mean) / std_dev
                
                # Enrichissement (Optionnel : stocker le score pour analyse fine)
                # record[f'meta_zscore_{field}'] = round(z_score, 2)

                if abs(z_score) > self.SIGMA_THRESHOLD:
                    anomalies_found += 1
                    details.append(f"{field}:val={val}:z={z_score:.1f}")

        # 3. Marquage (Flagging)
        # 0 = OK, 1 = Warning/Rejet Statistique
        if anomalies_found > 0:
            record['data_integrity_flag'] = 1
            record['anomaly_confidence_score'] = min(1.0, anomalies_found * 0.5) # Score simple
            record['processing_notes'] = f"OUTLIERS_DETECTED: {','.join(details)}"
        else:
            if 'data_integrity_flag' not in record:
                record['data_integrity_flag'] = 0
            record['anomaly_confidence_score'] = 0.0

        # 4. Écriture
        outputStream.write(json.dumps(record).encode('utf-8'))

# Exécution NiFi Boilerplate
flowFile = session.get()
if flowFile is not None:
    try:
        # Exécute le callback
        flowFile = session.write(flowFile, QualityControl())
        
        # Routage intelligent basé sur le résultat
        # On lit l'attribut qu'on vient potentiellement d'écrire (ou on le déduit)
        # Ici on transfère tout en SUCCESS, le filtrage se fera par RouteOnAttribute plus tard
        session.transfer(flowFile, REL_SUCCESS)
    except Exception as e:
        session.getLogger().error(f"Erreur Algo A2: {str(e)}")
        session.transfer(flowFile, REL_FAILURE)
```

## 4. Critères de Validation (Definition of Done)

- [ ] Le script ne plante pas si un champ est manquant (`None`).
- [ ] Une température de **24°C** donne un Z-Score de 0 et un flag `0`.
- [ ] Une température de **80°C** (Z > 10) donne un flag `1` et une note dans `processing_notes`.
- [ ] Le format de sortie reste strictement conforme au schéma JSON global (pas de suppression de champs).

# 🔗 ALGORITHME A3 : ENRICHISSEMENT CONTEXTUEL & FUSION

**Ticket JIRA :** `TICKET-024` **Responsable :** @Mouhammed (Data Engineer) **Sprint :** Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme est exécuté dans la **Zone 2 (Fusion & Enrichissement)** de **Apache NiFi**. Il intervient après la normalisation (A1) et la validation statistique (A2).

- **Entrée :** Donnée normalisée avec un identifiant technique (ex: `sensor_hardware_id`).
- **Sortie :** Donnée enrichie avec le contexte spatial, juridique et environnemental (ex: `parcel_id`, `ext_temp_nasa`).
- **Composant NiFi :** `LookupRecord` + `InvokeHTTP` (Mise en cache).

## 2. Description Scientifique & Technique

Une mesure brute (ex: "24°C sur le capteur S1") n'a aucune valeur pour l'étude scientifique si on ne sait pas **où** elle a été prise et **quelles étaient les conditions externes** à ce moment précis.

### Problème : L'Isolation de la Donnée

- Le capteur ne connaît pas le bail agricole (`parcel_id`).
- Le capteur ne sait pas qu'il pleut dehors (donnée NASA).
- Le capteur ne connaît pas sa position 3D dans le rack (`level_index`).

### Solution : La Jointure Temporelle & Spatiale

L'algorithme A3 réalise une **jointure à la volée** (Lookup) entre le flux temps réel et des référentiels statiques ou dynamiques.

1. **Référentiel Topologique (Statique) :**
   - Clé : `sensor_hardware_id`
   - Valeurs : `farm_id`, `parcel_id`, `rack_id`, `level_index`, `zone_id`.
   - *Pourquoi ?* Pour lier la biologie (plante) au droit (bail).
2. **Référentiel Environnemental (Dynamique/Cache) :**
   - Clé : `timestamp` (arrondi à l'heure) + `geo_location`.
   - Valeurs : `ext_temp_nasa`, `ext_solar_radiation`.
   - *Pourquoi ?* Pour calculer l'efficacité énergétique (Isolation du bâtiment).

## 3. Implémentation (Script Python pour NiFi `ExecuteScript`)

Bien que `LookupRecord` soit le processeur standard, une implémentation Python offre plus de flexibilité pour gérer le cache météo et les règles métier complexes de fusion.

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ALGORITHME A3 : CONTEXT ENRICHMENT
================================================================================
Description :
Enrichit le flux de données avec :
1. La topologie (Où est le capteur ?) via un dictionnaire en mémoire.
2. La météo externe (Quel temps fait-il ?) via un cache local (NASA API).
================================================================================
"""

import json
from org.apache.commons.io import IOUtils
from java.nio.charset import StandardCharsets
from org.apache.nifi.processor.io import StreamCallback

class ContextEnricher(StreamCallback):
    def __init__(self):
        # 1. CHARGEMENT TOPOLOGIE (Simulé - En prod, vient d'un DistributedMapCache ou MongoDB)
        # Mapping: Sensor_ID -> { Context Data }
        self.topology_map = {
            "SN-001": {
                "farm_id": "VERT-MAROC-01",
                "parcel_id": "830-AB-123",
                "rack_id": "R01",
                "level_index": 1,
                "zone_id": "ZONE_GERMINATION"
            },
            "SN-002": {
                "farm_id": "VERT-MAROC-01",
                "parcel_id": "830-AB-123",
                "rack_id": "R04",
                "level_index": 5,
                "zone_id": "ZONE_CROISSANCE"
            }
        }
        
        # 2. CACHE MÉTÉO (Simulé - Mis à jour par un autre processeur InvokeHTTP)
        self.weather_cache = {
            "current": {
                "ext_temp_nasa": 18.5,
                "ext_humidity_nasa": 45.0,
                "ext_solar_radiation": 850.0
            }
        }

    def process(self, inputStream, outputStream):
        text = IOUtils.toString(inputStream, StandardCharsets.UTF_8)
        try:
            record = json.loads(text)
        except ValueError:
            return # Erreur JSON gérée en amont

        sensor_id = record.get('sensor_hardware_id')

        # --- A. ENRICHISSEMENT TOPOLOGIQUE ---
        if sensor_id in self.topology_map:
            context = self.topology_map[sensor_id]
            # Fusion des dictionnaires
            record.update(context)
            record['enrichment_status'] = "FULL"
        else:
            # Capteur inconnu (Nouveau ?)
            record['enrichment_status'] = "PARTIAL_UNKNOWN_DEVICE"
            record['farm_id'] = "UNKNOWN" # Valeur par défaut pour ne pas casser ClickHouse

        # --- B. ENRICHISSEMENT ENVIRONNEMENTAL ---
        # On ajoute les données NASA actuelles à chaque message
        # Cela permet à l'Algo A7 (Corrélation) de comparer Intérieur vs Extérieur
        record.update(self.weather_cache['current'])

        # --- C. CALCULS DÉRIVÉS IMMÉDIATS ---
        # Exemple : Delta Température (Isolation)
        if record.get('air_temp_internal') is not None:
            internal = float(record['air_temp_internal'])
            external = self.weather_cache['current']['ext_temp_nasa']
            record['temp_delta_isolation'] = round(internal - external, 2)

        outputStream.write(json.dumps(record).encode('utf-8'))

# Exécution NiFi
flowFile = session.get()
if flowFile is not None:
    try:
        flowFile = session.write(flowFile, ContextEnricher())
        session.transfer(flowFile, REL_SUCCESS)
    except Exception as e:
        session.getLogger().error(f"Erreur A3: {str(e)}")
        session.transfer(flowFile, REL_FAILURE)
```

## 4. Critères de Validation (Definition of Done)

- [ ] Chaque ligne sortante possède obligatoirement un `parcel_id` (vital pour la requête SQL de rentabilité du bail).
- [ ] Les données NASA (`ext_temp_nasa`) sont présentes même si le capteur est en intérieur.
- [ ] Si un capteur est inconnu, le flux ne plante pas (valeur par défaut "UNKNOWN").
- [ ] Le calcul du delta de température est correct (Intérieur - Extérieur).

# 🛡️ ALGORITHME A4 : SEUILLAGE & ALERTE (THRESHOLDING)

**Ticket JIRA :** `TICKET-021` **Responsable :** @Asama (Biologiste) & @Imrane (DevOps) **Sprint :** Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme est un composant **hybride**.

- **Logique Primaire (Filtrage rapide) :** Exécutée dans **Apache NiFi** (Zone 2/3) via `ExecuteScript`.
- **Logique Secondaire (Réaction complexe) :** Exécutée dans **MongoDB** (Change Streams) pour la persistance de l'état d'alerte.
- **Entrée :** Donnée enrichie (A3) contenant les valeurs réelles (ex: `nutrient_n_total`).
- **Sortie :** Donnée marquée avec un statut d'alerte (`alert_status`, `alert_details`, `maintenance_urgency_score`).

## 2. Description Scientifique & Technique

L'objectif est de protéger l'actif biologique (les plantes) en détectant **immédiatement** toute déviation par rapport aux conditions optimales de croissance.

### Problème : La Loi de Liebig (Facteur Limitant)

La croissance d'une plante n'est pas limitée par le total des ressources disponibles, mais par la ressource la plus rare (le facteur limitant).

- Si Azote (N) est bas, même avec une lumière parfaite, la plante ne grandira pas.
- Une température excessive (>30°C) peut tuer la culture en quelques heures.

### Solution : Comparaison Dynamique

L'algorithme compare chaque métrique entrante ($Valeur_{Reelle}$) aux cibles définies par l'agronome ($Cible_{Min}, Cible_{Max}$).

$$Etat =  \begin{cases}  NORMAL & \text{si } Cible_{Min} \le Valeur_{Reelle} \le Cible_{Max} \\ ALERTE & \text{sinon} \end{cases}$$

De plus, il calcule un **Score d'Urgence** (`maintenance_urgency_score` - Col 152) proportionnel à la gravité de l'écart et à la durée de l'anomalie.

## 3. Implémentation (Logique Python pour NiFi)

Le script ci-dessous est celui injecté par l'automatisme de déploiement (`scripts/setup_nifi_algo_a4.py`). Il illustre la logique de décision.

```
# Extrait de la logique métier (ExecuteScript NiFi)

# Cibles (En production, ces valeurs proviennent du Cache/Lookup A3)
TARGETS = {
    'nutrient_n_total': {'min': 100, 'max': 200}, # ppm
    'air_temp_internal': {'min': 18, 'max': 28},  # °C
    'vapor_pressure_deficit': {'min': 0.4, 'max': 1.5} # kPa
}

def check_thresholds(record):
    alerts = []
    urgency = 0
    
    # 1. Azote (Nutrition)
    n_val = record.get('nutrient_n_total')
    if n_val:
        if n_val < TARGETS['nutrient_n_total']['min']:
            alerts.append(f"CRITIQUE: Carence Azote ({n_val} ppm)")
            urgency += 50 # Haute priorité
        elif n_val > TARGETS['nutrient_n_total']['max']:
            alerts.append(f"WARN: Excès Azote ({n_val} ppm)")
            urgency += 20 # Priorité moyenne

    # 2. Température (Climat)
    t_val = record.get('air_temp_internal')
    if t_val:
         if t_val > TARGETS['air_temp_internal']['max']:
            alerts.append(f"CRITIQUE: Surchauffe ({t_val} °C)")
            urgency += 80 # Très haute priorité (Risque mortel)

    # Résultat
    if alerts:
        record['alert_status'] = "ACTIVE"
        record['alert_details'] = "; ".join(alerts)
        record['maintenance_urgency_score'] = min(100, urgency)
    else:
        record['alert_status'] = "NORMAL"
        record['maintenance_urgency_score'] = 0
        
    return record
```

## 4. Critères de Validation (Definition of Done)

- [ ] Si `nutrient_n_total` = 90 (Cible min 100), le champ `alert_status` passe à "ACTIVE".
- [ ] Le `maintenance_urgency_score` reflète correctement la gravité (Surchauffe > Carence légère).
- [ ] Les alertes générées contiennent un message clair pour l'opérateur (`alert_details`).
- [ ] Le flux de données continue même en cas d'alerte (pas de blocage du pipeline, juste un marquage).

# ⚙️ ALGORITHME A5 : MOTEUR DE RÈGLES MÉTIER (RULE ENGINE)

**Ticket JIRA :** `TICKET-025` **Responsable :** @Imrane (DevOps) & @Asama (Biologiste) **Sprint :** Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme réside dans le **Cerveau Réflexe (Zone 4)**, au niveau de la base de données **MongoDB**.

- **Entrée :** Flux de données temps réel (via Kafka Connector ou Change Stream).
- **Sortie :** Ordres d'action immédiats (ex: `STOP_PUMP`, `OPEN_VALVE`) et notifications d'urgence.
- **Composant Technique :** MongoDB Triggers (Atlas) ou Change Streams (Self-Hosted).

## 2. Description Scientifique & Technique

Contrairement à l'Algorithme A4 (Seuillage) qui surveille des tendances continues (ex: température qui monte), l'Algorithme A5 gère des **états binaires critiques**.

### Problème : La Sécurité Physique

Certains événements ne tolèrent aucune latence ni interprétation.

- Si le capteur d'inondation (`leak_detection_status`) passe à 1, il faut couper l'eau **tout de suite**.
- Si le bouton d'arrêt d'urgence (`emergency_stop_status`) est activé, tout doit s'arrêter.

### Solution : Logique Booléenne Déterministe

L'algorithme applique une série de règles `IF / THEN` strictes sur chaque document inséré.

| Règle                  | Condition (Si...)                  | Action (Alors...)           | Priorité      |
| ---------------------- | ---------------------------------- | --------------------------- | ------------- |
| **R1 (Inondation)**    | `leak_detection_status == 1`       | Couper Pompe Principale     | CRITIQUE (P0) |
| **R2 (Arrêt Urgence)** | `emergency_stop_status == 1`       | Couper Alimentation 24V     | CRITIQUE (P0) |
| **R3 (Pression)**      | `irrigation_line_pressure > 5 Bar` | Ouvrir Vanne de Décharge    | HAUTE (P1)    |
| **R4 (Communication)** | `ingestion_lag_ms > 5000`          | Passer en Mode "Safe Local" | MOYENNE (P2)  |

## 3. Implémentation (Script MongoDB Change Stream)

Ce script Node.js (ou Mongo Shell) écoute la collection `LiveState` et réagit instantanément aux changements.

```
/**
 * ================================================================================
 * ALGORITHME A5 : RULE ENGINE (MONGODB WATCHER)
 * ================================================================================
 * Description :
 * Écoute les modifications sur la collection 'telemetry_live' et déclenche
 * des actions physiques via MQTT si une règle métier est violée.
 * ================================================================================
 */

// Connexion au Cluster VertiFlow
const pipeline = [
    {
        $match: {
            $or: [
                { "fullDocument.leak_detection_status": 1 },
                { "fullDocument.emergency_stop_status": 1 },
                { "fullDocument.irrigation_line_pressure": { $gt: 5.0 } }
            ]
        }
    }
];

const changeStream = db.collection('telemetry_live').watch(pipeline);

changeStream.on('change', (next) => {
    const doc = next.fullDocument;
    const rackID = doc.rack_id;
    const actions = [];

    console.log(`[ALERTE A5] Détection événement critique sur Rack ${rackID}`);

    // --- RÈGLE R1 : INONDATION ---
    if (doc.leak_detection_status === 1) {
        actions.push({
            topic: `vertiflow/control/${rackID}/pump_main`,
            payload: "OFF",
            reason: "FLOOD_DETECTED"
        });
    }

    // --- RÈGLE R2 : ARRÊT D'URGENCE ---
    if (doc.emergency_stop_status === 1) {
        actions.push({
            topic: `vertiflow/control/${rackID}/power_24v`,
            payload: "CUT",
            reason: "MANUAL_EMERGENCY"
        });
    }

    // --- RÈGLE R3 : SURPRESSION ---
    if (doc.irrigation_line_pressure > 5.0) {
        actions.push({
            topic: `vertiflow/control/${rackID}/valve_relief`,
            payload: "OPEN",
            reason: "OVER_PRESSURE"
        });
    }

    // Exécution des actions (Simulation envoi MQTT)
    actions.forEach(action => {
        print(`--> EXECUTION: Envoi ordre ${action.payload} sur ${action.topic} (${action.reason})`);
        // Ici, on appellerait une fonction publishMQTT(action.topic, action.payload)
    });
    
    // Log de l'incident pour audit
    db.collection('incident_logs').insertOne({
        timestamp: new Date(),
        rack_id: rackID,
        triggers: actions.map(a => a.reason),
        severity: "CRITICAL"
    });
});
```

## 4. Critères de Validation (Definition of Done)

- [ ] Simuler une fuite (`leak_detection_status = 1`) déclenche un log "EXECUTION: OFF".
- [ ] Le temps de réaction entre l'insertion en base et l'action est < 100ms.
- [ ] Une trace de l'incident est créée dans la collection `incident_logs`.
- [ ] Le système gère plusieurs alertes simultanées (ex: Fuite + Arrêt Urgence).

# 📉 ALGORITHME A6 : AGRÉGATION TEMPORELLE (DOWNSAMPLING)

**Ticket JIRA :** `TICKET-026` **Responsable :** @Mounir (Architecte) & @Mouhammed (Data Engineer) **Sprint :** Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme est exécuté nativement par le moteur de base de données **ClickHouse** (Zone 5).

- **Entrée :** Table brute `basil_ultimate_realtime` (Flux Kafka, ~1 mesure/sec).
- **Sortie :** Vues Matérialisées `hourly_stats` et `daily_stats`.
- **Composant Technique :** ClickHouse `Materialized View` + Moteur `AggregatingMergeTree`.

## 2. Description Scientifique & Technique

Les capteurs envoient des données chaque seconde. Pour une étude agronomique sur 3 mois, cela représente des millions de points, ce qui est trop lourd et "bruyant" pour l'analyse statistique (A7/A8).

### Problème : Le Bruit vs La Tendance

- Une plante ne pousse pas en une seconde.
- Les micro-variations (ex: température qui oscille de 0.1°C) n'ont pas d'intérêt biologique direct.
- Le stockage brut coûte cher et ralentit les requêtes Power BI.

### Solution : L'Agrégation Intelligente

L'algorithme A6 réduit la résolution temporelle tout en conservant les métriques statistiques clés pour la science :

- **Moyenne (**$\mu$**) :** Tendance centrale.
- **Min/Max :** Pour détecter les stress extrêmes (ex: pic de chaleur bref).
- **Quantiles (P95) :** Pour éliminer les outliers restants.

**Ratio de compression visé :** 3600 lignes brutes $\rightarrow$ 1 ligne horaire.

## 3. Implémentation (Script SQL ClickHouse)

Nous utilisons les "Materialized Views" de ClickHouse. Elles calculent l'agrégation *au moment de l'insertion*, ce qui rend la lecture instantanée.

```
/*
================================================================================
ALGORITHME A6 : VUES D'AGRÉGATION (CLICKHOUSE)
================================================================================
Description :
Crée une vue matérialisée qui calcule automatiquement les statistiques horaires
pour chaque Rack et chaque Variété.
================================================================================
*/

-- 1. Table de destination (Optimisée pour l'agrogation)
CREATE TABLE IF NOT EXISTS smart_farming.basil_hourly_stats (
    timestamp DateTime,
    farm_id LowCardinality(String),
    rack_id LowCardinality(String),
    species_variety LowCardinality(String),
    
    -- Métriques agrégées (State)
    avg_temp SimpleAggregateFunction(avg, Float32),
    max_temp SimpleAggregateFunction(max, Float32),
    min_temp SimpleAggregateFunction(min, Float32),
    
    avg_humidity SimpleAggregateFunction(avg, Float32),
    
    total_par_light SimpleAggregateFunction(sum, Float32), -- Somme de la lumière (DLI partiel)
    
    avg_biomass_est SimpleAggregateFunction(avg, Float32)

) ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (farm_id, rack_id, species_variety, timestamp);


-- 2. La Vue Matérialisée (Le Trigger de calcul)
CREATE MATERIALIZED VIEW IF NOT EXISTS smart_farming.mv_basil_hourly
TO smart_farming.basil_hourly_stats
AS SELECT
    toStartOfHour(timestamp) as timestamp,
    farm_id,
    rack_id,
    species_variety,
    
    avg(air_temp_internal) as avg_temp,
    max(air_temp_internal) as max_temp,
    min(air_temp_internal) as min_temp,
    
    avg(air_humidity) as avg_humidity,
    
    sum(light_intensity_ppfd) as total_par_light,
    
    avg(fresh_biomass_est) as avg_biomass_est

FROM smart_farming.basil_ultimate_realtime
WHERE data_integrity_flag = 0 -- On n'agrège que les données valides (Algo A2)
GROUP BY
    toStartOfHour(timestamp),
    farm_id,
    rack_id,
    species_variety;
```

## 4. Critères de Validation (Definition of Done)

- [ ] La table `basil_hourly_stats` se remplit automatiquement dès que des données arrivent dans `basil_ultimate_realtime`.
- [ ] Une requête sur `basil_hourly_stats` est au moins 100x plus rapide que sur la table brute pour une période d'un mois.
- [ ] Les pics (Max) et les creux (Min) sont conservés (pas de lissage destructeur).
- [ ] Le calcul du DLI (Somme de lumière) est cohérent (somme des PPFD instantanés).

# 📊 ALGORITHME A7 : MATRICE DE CORRÉLATION (PEARSON)

**Ticket JIRA :** `TICKET-022` **Responsable :** @Mounir (Architecte / Scientifique) **Sprint :** Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme est exécuté nativement par le moteur de base de données **ClickHouse** (Zone 5).

- **Entrée :** Table `basil_ultimate_realtime` ou Vues Agrégées (A6).
- **Sortie :** Vue Analytique `view_algo_7_correlation`.
- **Composant Technique :** Fonctions d'agrégation `corr()` et `covarPop()`.

## 2. Description Scientifique & Technique

Pour valider une hypothèse agronomique, il ne suffit pas de regarder deux courbes. Il faut quantifier leur lien statistique.

### Problème : La Preuve Scientifique

L'agronome pense que *"Plus de CO2 = Plus de croissance"*. Mais si la croissance augmente alors que le CO2 baisse (à cause d'un autre facteur comme la température), l'observation visuelle est trompeuse.

### Solution : Le Coefficient de Corrélation de Pearson ($r$)

L'algorithme A7 calcule $r$ pour chaque paire de variables $(X, Y)$ sur une fenêtre de temps donnée.

$$r = \frac{\sum(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum(x_i - \bar{x})^2 \sum(y_i - \bar{y})^2}}$$

- $r \approx 1$ **:** Corrélation positive forte (Preuve validée).
- $r \approx -1$ **:** Corrélation négative forte (Inversement proportionnel).
- $r \approx 0$ **:** Aucune corrélation (Le facteur X n'a aucun effet sur Y).

**Seuil de validation scientifique :** $|r| > 0.8$.

## 3. Implémentation (Script SQL ClickHouse)

Cette vue calcule en temps réel la force des liens entre les paramètres environnementaux et les résultats biologiques.

```
/*
================================================================================
ALGORITHME A7 : MATRICE DE CORRÉLATION (PEARSON)
================================================================================
Description :
Calcule le coefficient de corrélation (r) entre les facteurs climatiques/nutritionnels
et les indicateurs de performance (Biomasse, Qualité).
Analyse segmentée par Variété pour éviter les biais génétiques.
================================================================================
*/

CREATE OR REPLACE VIEW smart_farming.view_algo_7_correlation AS
SELECT
    species_variety,
    
    -- HYPOTHÈSE 1 : LUMIÈRE vs CROISSANCE
    -- Est-ce que le DLI (Daily Light Integral) prédit la Biomasse ?
    corr(light_dli_accumulated, fresh_biomass_est) AS r_light_growth,
    
    -- HYPOTHÈSE 2 : TEMPÉRATURE vs QUALITÉ
    -- Est-ce que la chaleur détruit les huiles essentielles ?
    corr(air_temp_internal, essential_oil_yield) AS r_temp_quality,
    
    -- HYPOTHÈSE 3 : CO2 vs VITESSE
    -- Est-ce que le CO2 accélère le taux de croissance relatif (RGR) ?
    corr(co2_level_ambient, relative_growth_rate) AS r_co2_speed,
    
    -- HYPOTHÈSE 4 : NUTRITION K vs SANTÉ
    -- Est-ce que le Potassium améliore la régulation stomatique ?
    corr(nutrient_k_potassium, stomatal_conductance) AS r_k_stomata,

    -- Métriques de fiabilité
    count() AS sample_size,
    
    -- Interprétation automatique (String)
    multiIf(
        abs(r_light_growth) > 0.8, 'STRONG_LINK',
        abs(r_light_growth) > 0.5, 'MODERATE_LINK',
        'NO_LINK'
    ) as conclusion_light_growth

FROM smart_farming.basil_ultimate_realtime
WHERE 
    timestamp > now() - INTERVAL 30 DAY -- Fenêtre glissante de 30 jours
    AND data_integrity_flag = 0         -- Données valides uniquement (Algo A2)
GROUP BY 
    species_variety
ORDER BY 
    species_variety;
```

## 4. Critères de Validation (Definition of Done)

- [ ] La vue `view_algo_7_correlation` retourne un résultat en moins de 1 seconde (même sur 1M lignes).
- [ ] Le coefficient $r$ est toujours compris entre -1 et 1.
- [ ] Si `sample_size` < 100, l'analyse est marquée comme "Non significative" (à gérer dans Power BI).
- [ ] L'exclusion des données `data_integrity_flag != 0` fonctionne (les outliers ne faussent pas le calcul).

# 🧪 ALGORITHME A8 : SEGMENTATION & A/B TESTING (ANOVA)

**Ticket JIRA :** `TICKET-027` **Responsable :** @Mounir (Architecte / Scientifique) **Sprint :** Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme est exécuté nativement par le moteur de base de données **ClickHouse** (Zone 5).

- **Entrée :** Table `basil_ultimate_realtime` ou Vues Agrégées (A6).
- **Sortie :** Vue Analytique `view_algo_8_ab_testing`.
- **Composant Technique :** Fonctions d'agrégation `avg()`, `varPop()` (Variance de population) et calculs statistiques dérivés.

## 2. Description Scientifique & Technique

Pour optimiser la production, l'agronome doit pouvoir tester différentes "recettes" (combinaisons de lumière, nutriments, etc.) et déterminer laquelle est la meilleure.

### Problème : Comparer l'Incomparable

Comparer le rendement du Rack 1 (Recette A) et du Rack 2 (Recette B) ne suffit pas si le Rack 1 a reçu plus de lumière naturelle ou si ses plants étaient plus vieux.

### Solution : L'Analyse de Variance (ANOVA Simplifiée)

L'algorithme A8 segmente les données par `rack_id` (le groupe de test) et calcule pour chaque groupe :

- **Moyenne (**$\mu$**) :** Performance moyenne.
- **Variance (**$\sigma^2$**) :** Dispersions des résultats (Stabilité).
- **Intervalle de Confiance (IC) :** Plage dans laquelle se trouve la vraie moyenne à 95%.

Si les intervalles de confiance de deux racks ne se chevauchent pas, la différence de performance est **significative**.

## 3. Implémentation (Script SQL ClickHouse)

Cette vue permet de comparer instantanément les performances de différents racks (groupes de test).

```
/*
================================================================================
ALGORITHME A8 : SEGMENTATION & A/B TESTING
================================================================================
Description :
Compare les performances (Biomasse, Qualité) entre différents groupes (Racks).
Calcule les métriques statistiques pour valider si une différence est significative.
================================================================================
*/

CREATE OR REPLACE VIEW smart_farming.view_algo_8_ab_testing AS
SELECT
    rack_id,
    species_variety,
    
    -- Métriques de Performance (Moyenne)
    avg(fresh_biomass_est) AS avg_biomass,
    avg(essential_oil_yield) AS avg_oil_yield,
    
    -- Métriques de Stabilité (Variance & Ecart-Type)
    varPop(fresh_biomass_est) AS var_biomass,
    stddevPop(fresh_biomass_est) AS std_biomass,
    
    -- Taille de l'échantillon
    count() AS sample_size,
    
    -- Intervalle de Confiance à 95% (Approximation: 1.96 * Erreur Standard)
    -- CI_Lower = Moyenne - (1.96 * (Ecart-Type / Racine(N)))
    avg_biomass - (1.96 * (std_biomass / sqrt(sample_size))) AS ci_lower_biomass,
    avg_biomass + (1.96 * (std_biomass / sqrt(sample_size))) AS ci_upper_biomass,

    -- Score de Performance Global (Biomasse * Huile)
    avg_biomass * avg_oil_yield AS performance_score

FROM smart_farming.basil_ultimate_realtime
WHERE 
    timestamp > now() - INTERVAL 30 DAY -- Analyse sur le cycle en cours
    AND data_integrity_flag = 0         -- Données valides uniquement
GROUP BY 
    rack_id,
    species_variety
ORDER BY 
    performance_score DESC;
```

## 4. Critères de Validation (Definition of Done)

- [ ] La vue retourne une ligne par Rack actif.
- [ ] Les intervalles de confiance (`ci_lower`, `ci_upper`) sont calculés.
- [ ] Le tri par `performance_score` permet d'identifier immédiatement le meilleur Rack.
- [ ] L'exclusion des données invalides fonctionne correctement.

# 🔮 ALGORITHME A9 : PRÉDICTION DE RÉCOLTE (LSTM)

**Ticket JIRA :** `TICKET-023` **Responsable :** @Mounir (Scientifique) & @Mouhammed (Data Engineer) **Sprint :** Semaine 2 - Phase ETL

## 1. Emplacement dans l'Architecture

Cet algorithme réside dans la couche **Intelligence Prédictive (Zone 5)**, exécutée par un moteur Python externe (`oracle.py` dans le dossier `cloud_citadel/nervous_system/`).

- **Entrée :** Séries temporelles historiques provenant de **ClickHouse** (Table `basil_hourly_stats`).
- **Sortie :** Prédictions de date de récolte et de rendement injectées dans **Kafka** (Topic `basil_predictions`).
- **Composant Technique :** TensorFlow/Keras (Modèle LSTM) + Kafka Producer.

## 2. Description Scientifique & Technique

L'agriculture de précision ne se limite pas à observer le présent ; elle doit anticiper le futur. Prédire la date exacte de récolte permet d'optimiser la chaîne logistique et de maximiser la fraîcheur du produit.

### Problème : La Dynamique Non-Linéaire de la Croissance

La croissance d'une plante n'est pas linéaire. Elle dépend de l'historique cumulé des conditions environnementales (effet mémoire). Une baisse de température à J+10 peut retarder la récolte de plusieurs jours, même si les conditions redeviennent optimales ensuite.

### Solution : Long Short-Term Memory (LSTM)

Les réseaux de neurones récurrents LSTM sont spécifiquement conçus pour apprendre des dépendances à long terme dans des séquences temporelles. Le modèle prend en entrée une fenêtre glissante des conditions passées (ex: 7 jours) et prédit la biomasse future.

**Variables d'entrée (Features) :**

1. `air_temp_internal` (Température)
2. `light_dli_accumulated` (Lumière reçue)
3. `vapor_pressure_deficit` (Stress hydrique)
4. `co2_level_ambient` (Carbone disponible)
5. `fresh_biomass_est` (Biomasse actuelle estimée par vision)

**Variable Cible (Target) :**

- `fresh_biomass_est` à J+N.

## 3. Implémentation (Code Python - Oracle)

Ce script constitue le cœur du moteur prédictif `oracle.py`.

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ALGORITHME A9 : ORACLE DE PRÉDICTION DE RÉCOLTE (LSTM)
================================================================================
Description :
Modèle de Deep Learning pour prédire la biomasse future du basilic.
Utilise l'historique des capteurs pour estimer la date d'atteinte du poids cible.
================================================================================
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import logging

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Oracle-A9")

class HarvestPredictor:
    def __init__(self, sequence_length=7, n_features=5):
        """
        Initialise le modèle LSTM.
        :param sequence_length: Nombre de jours d'historique (fenêtre glissante)
        :param n_features: Nombre de variables d'entrée (Temp, DLI, VPD, CO2, Biomasse)
        """
        self.seq_len = sequence_length
        self.n_features = n_features
        self.model = self._build_model()
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def _build_model(self):
        """Construction de l'architecture du réseau de neurones."""
        model = Sequential()
        
        # Couche LSTM 1 : Extraction des features temporelles complexes
        model.add(LSTM(units=50, return_sequences=True, input_shape=(self.seq_len, self.n_features)))
        model.add(Dropout(0.2)) # Régularisation pour éviter le sur-apprentissage

        # Couche LSTM 2 : Consolidation de la mémoire
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))

        # Couche Dense de sortie : Régression (Prédiction de la biomasse future)
        model.add(Dense(units=1))

        model.compile(optimizer='adam', loss='mean_squared_error')
        logger.info("🧠 Modèle LSTM compilé avec succès.")
        return model

    def train(self, historical_data):
        """
        Entraîne le modèle sur les données historiques ClickHouse.
        :param historical_data: DataFrame Pandas avec les colonnes requises.
        """
        # Prétraitement des données
        data_scaled = self.scaler.fit_transform(historical_data)
        
        X, y = [], []
        for i in range(self.seq_len, len(data_scaled)):
            X.append(data_scaled[i-self.seq_len:i, :]) # Séquence de 7 jours
            y.append(data_scaled[i, 4]) # Cible : Biomasse (colonne index 4) au jour J
            
        X, y = np.array(X), np.array(y)
        
        logger.info(f"🏋️ Début de l'entraînement sur {len(X)} séquences...")
        self.model.fit(X, y, epochs=20, batch_size=32, verbose=1)
        logger.info("✅ Entraînement terminé.")

    def predict_harvest_date(self, current_sequence, target_weight):
        """
        Simule la croissance future jour par jour jusqu'à atteindre la cible.
        
        :param current_sequence: Array (1, 7, 5) - Les 7 derniers jours réels.
        :param target_weight: Float - Poids cible (ex: 50g).
        :return: Dict avec jours restants et date estimée.
        """
        # Normalisation de l'entrée
        # Note : En prod, il faut gérer le scaler pour ne transformer que les inputs
        # Ici on simplifie pour la logique algorithmique
        
        days_remaining = 0
        predicted_weight = current_sequence[0, -1, 4] # Poids actuel (Dernier jour)
        simulated_seq = current_sequence.copy()
        
        MAX_DAYS = 45 # Sécurité pour éviter boucle infinie
        
        logger.info(f"🔮 Simulation de croissance. Poids actuel: {predicted_weight:.2f}g -> Cible: {target_weight}g")

        while predicted_weight < target_weight and days_remaining < MAX_DAYS:
            # Prédiction pour J+1
            next_step_scaled = self.model.predict(simulated_seq, verbose=0)
            
            # Mise à jour du poids prédit (Dénormalisation approximative pour l'exemple)
            # Dans la réalité, on utiliserait self.scaler.inverse_transform()
            growth_factor = next_step_scaled[0][0] 
            predicted_weight += growth_factor # Hypothèse simplifiée : modèle prédit le gain
            
            days_remaining += 1
            
            # Mise à jour de la séquence glissante pour le pas suivant
            # On décale les jours et on ajoute la nouvelle prédiction en fin
            # On suppose ici des conditions climatiques stables (moyenne des 7 derniers jours)
            new_day = np.mean(simulated_seq[0], axis=0) 
            new_day[4] = predicted_weight # Mise à jour de la biomasse
            
            # Rotation : [J-6 ... J] -> [J-5 ... J+1]
            simulated_seq = np.append(simulated_seq[:, 1:, :], [[new_day]], axis=1)

        return {
            "rack_id": "R01", # À dynamiser
            "days_remaining": days_remaining,
            "predicted_final_biomass": float(predicted_weight),
            "status": "ON_TRACK" if days_remaining < 20 else "DELAYED"
        }

# --- Bloc de test unitaire ---
if __name__ == "__main__":
    # Génération de données factices pour tester la logique
    mock_data = pd.DataFrame(np.random.rand(100, 5), columns=['temp', 'dli', 'vpd', 'co2', 'biomass'])
    
    oracle = HarvestPredictor()
    oracle.train(mock_data)
    
    # Test de prédiction sur une séquence aléatoire
    test_seq = np.random.rand(1, 7, 5)
    result = oracle.predict_harvest_date(test_seq, target_weight=1.5)
    
    print(f"\nRÉSULTAT ORACLE : {result}")
```

## 4. Critères de Validation (Definition of Done)

- [ ] Le modèle converge lors de l'entraînement (la perte `loss` diminue).
- [ ] La fonction `predict_harvest_date` retourne un nombre de jours cohérent (pas négatif, pas infini).
- [ ] Le script peut charger des données depuis un fichier CSV ou une requête ClickHouse simulée.
- [ ] Les dépendances (`tensorflow`, `pandas`, `scikit-learn`) sont bien listées dans `requirements.txt`.

# 🧠 ALGORITHME A11 : OPTIMISATION DE RECETTE (GRADIENT DESCENT)

**Ticket JIRA :** `TICKET-029` **Responsable :** @Mounir (Scientifique) & @Mounir (Architecte) **Sprint :** Semaine 3 - Phase Intelligence

## 1. Emplacement dans l'Architecture

Cet algorithme réside dans le **Cerveau Supérieur (Cortex)** (Zone 5), module `cortex.py`. Il ferme la boucle de rétroaction en proposant de nouveaux paramètres de consigne.

- **Entrée :** Résultats des cycles précédents (ClickHouse - `basil_hourly_stats` et `harvest_results`).
- **Sortie :** Nouvelles cibles optimales (`ref_n_target`, `ref_temp_opt`, etc.) mises à jour dans MongoDB.
- **Composant Technique :** Scikit-Learn / Scipy (Optimisation).

## 2. Description Scientifique & Technique

L'objectif est de trouver la combinaison idéale de paramètres environnementaux ("Recette") qui maximise le rendement ou la rentabilité, sans intervention humaine constante.

### Problème : L'Espace de Recherche Vaste

Il existe une infinité de combinaisons possibles de Température, Lumière, EC, pH, etc. Tester chaque combinaison manuellement prendrait des siècles.

### Solution : Descente de Gradient (ou Algorithme Génétique)

L'algorithme modélise la fonction de rendement $f(x_1, x_2, ... x_n)$ où $x_i$ sont les paramètres contrôlables. Il cherche ensuite les valeurs de $x$ qui maximisent $f(x)$ en suivant la pente ascendante (Gradient Ascent).

**Fonction Objectif (à maximiser) :**

$$Score = \alpha \times \text{Yield} + \beta \times \text{Quality} - \gamma \times \text{Cost}$$

## 3. Implémentation (Code Python - Cortex)

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ALGORITHME A11 : OPTIMISATEUR DE RECETTE (CORTEX)
================================================================================
Description :
Analyse les performances passées pour recommander des ajustements
des paramètres de consigne (Cibles) afin de maximiser le Score de Performance.
================================================================================
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import logging

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Cortex-A11")

class RecipeOptimizer:
    def __init__(self):
        # Modèle de substitution (Surrogate Model) pour estimer la fonction de rendement
        # On utilise une régression polynomiale pour capturer les non-linéarités
        self.model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
        self.param_bounds = [
            (18.0, 28.0),  # Température (°C)
            (10.0, 20.0),  # DLI (mol/m²/d)
            (1.2, 2.5)     # EC (mS/cm)
        ]
        self.feature_names = ['avg_temp', 'dli', 'avg_ec']

    def train_surrogate_model(self, historical_data):
        """
        Entraîne un modèle simple qui prédit le score en fonction des paramètres.
        :param historical_data: DataFrame avec colonnes features + 'performance_score'.
        """
        X = historical_data[self.feature_names]
        y = historical_data['performance_score']
        
        self.model.fit(X, y)
        r2 = self.model.score(X, y)
        logger.info(f"🧠 Modèle de substitution entraîné. R2: {r2:.3f}")

    def _objective_function(self, params):
        """
        Fonction à maximiser (le modèle prédit le score).
        Note: minimize cherche le minimum, donc on retourne -score pour maximiser.
        """
        # Reshape pour faire une prédiction unique
        params_reshaped = np.array(params).reshape(1, -1)
        predicted_score = self.model.predict(params_reshaped)[0]
        return -predicted_score

    def find_optimal_recipe(self, current_recipe):
        """
        Cherche la meilleure recette à partir du point actuel.
        :param current_recipe: Liste [temp, dli, ec] actuels.
        """
        logger.info(f"🔍 Recherche de l'optimum local depuis {current_recipe}...")
        
        result = minimize(
            self._objective_function,
            x0=current_recipe,
            bounds=self.param_bounds,
            method='L-BFGS-B' # Méthode efficace pour problèmes bornés
        )

        if result.success:
            optimized_params = result.x
            predicted_gain = -result.fun
            logger.info(f"🚀 Optimum trouvé : {optimized_params}")
            logger.info(f"📈 Score prédit : {predicted_gain:.2f}")
            
            return {
                "new_targets": {
                    "ref_temp_opt": round(optimized_params[0], 1),
                    "ref_dli_target": round(optimized_params[1], 1),
                    "ref_ec_target": round(optimized_params[2], 1)
                },
                "predicted_score": predicted_gain,
                "confidence": "HIGH" # Simplifié
            }
        else:
            logger.warning("⚠️ L'optimisation a échoué.")
            return None

# --- Bloc de test unitaire ---
if __name__ == "__main__":
    # Données factices : On suppose que le score est max vers 24°C, 15 DLI, 1.8 EC
    # Formule : Score = 100 - (T-24)^2 - (DLI-15)^2 - 10*(EC-1.8)^2
    data_size = 50
    X_mock = np.random.uniform(low=[18, 10, 1.2], high=[28, 20, 2.5], size=(data_size, 3))
    y_mock = 100 - (X_mock[:,0]-24)**2 - (X_mock[:,1]-15)**2 - 10*(X_mock[:,2]-1.8)**2
    
    df = pd.DataFrame(X_mock, columns=['avg_temp', 'dli', 'avg_ec'])
    df['performance_score'] = y_mock

    optimizer = RecipeOptimizer()
    optimizer.train_surrogate_model(df)
    
    current = [20.0, 12.0, 1.5] # Point de départ sous-optimal
    res = optimizer.find_optimal_recipe(current)
    print(f"\n💡 RECOMMANDATION CORTEX : {res}")
```

## 4. Critères de Validation

- [ ] Le "Surrogate Model" capture correctement la tendance des données (R2 raisonnable).
- [ ] L'optimiseur propose des valeurs dans les bornes définies (pas de T > 28°C).
- [ ] L'algorithme converge vers un meilleur score que le point de départ.
- [ ] Les recommandations sont au format JSON prêt à être envoyé à MongoDB (Mise à jour des cibles).