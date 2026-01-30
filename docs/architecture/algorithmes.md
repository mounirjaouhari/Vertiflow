# GUIDE DES ALGORITHMES - PROJET VERTIFLOW

**Agriculture Verticale Intelligente & Data-Driven**

## 📋 Table des Matières

1. [Introduction](https://www.google.com/search?q=%23introduction)
2. [Cartographie des Algorithmes](https://www.google.com/search?q=%23cartographie-des-algorithmes)
3. [Détail des Algorithmes & Implémentation](https://www.google.com/search?q=%23détail-des-algorithmes--implémentation)
   - [Phase 1 : Hygiène & Qualité (NiFi)](https://www.google.com/search?q=%23phase-1--hygiène--qualité-nifi)
   - [Phase 2 : Survie & Contrôle (MongoDB)](https://www.google.com/search?q=%23phase-2--survie--contrôle-mongodb)
   - [Phase 3 : Analyse Scientifique (ClickHouse)](https://www.google.com/search?q=%23phase-3--analyse-scientifique-clickhouse)
   - [Phase 4 : Intelligence Prédictive (Python/ML)](https://www.google.com/search?q=%23phase-4--intelligence-prédictive-pythonml)

## 1. Introduction

Ce document détaille les **11 Algorithmes Scientifiques** qui constituent le "Cerveau Numérique" de la plateforme VertiFlow. Chaque algorithme répond à un besoin précis de l'étude scientifique : **Fiabilité**, **Survie**, **Compréhension** et **Prédiction**.

## 2. Cartographie des Algorithmes

| **ID**  | **Nom de l'Algorithme**          | **Type**      | **Emplacement** | **Rôle Scientifique**                    |
| ------- | -------------------------------- | ------------- | --------------- | ---------------------------------------- |
| **A1**  | Normalisation JSON               | ETL           | NiFi            | Standardisation des formats hétérogènes. |
| **A2**  | Détection d'Aberration (Z-Score) | Statistique   | NiFi            | Rejet des données capteurs défaillants.  |
| **A3**  | Enrichissement Contextuel        | Fusion        | NiFi            | Ajout des métadonnées légales (Bail).    |
| **A4**  | Seuillage (Thresholding)         | Logique       | MongoDB         | Comparaison Temps Réel vs Cibles Expert. |
| **A5**  | Règles Métier (Rule Engine)      | Booléen       | MongoDB         | Actions réflexes (Arrêt Urgence).        |
| **A6**  | Agrégation Temporelle            | SQL           | ClickHouse      | Réduction du bruit (Moyennes horaires).  |
| **A7**  | Corrélation (Pearson)            | SQL           | ClickHouse      | Preuve des liens (Lumière vs Poids).     |
| **A8**  | Segmentation (ANOVA)             | SQL           | ClickHouse      | Comparaison A/B Testing (Racks).         |
| **A9**  | Séries Temporelles (LSTM)        | Deep Learning | Python (Oracle) | Prédiction date de récolte.              |
| **A10** | Classification (Random Forest)   | ML Supervisé  | Python (Oracle) | Prédiction qualité (Premium/Standard).   |
| **A11** | Optimisation (Gradient Descent)  | Math          | Python (Cortex) | Recherche de la recette idéale.          |

## 3. Détail des Algorithmes & Implémentation

### Phase 1 : Hygiène & Qualité (NiFi)

#### ⚙️ Algorithme A2 : Détection d'Aberration (Z-Score)

- **Ticket :** `TICKET-020`
- **Emplacement :** NiFi (Processeur `ExecuteScript` - Groovy/Python)
- **Objectif :** Garantir que l'étude ne se base pas sur des données fausses. Si une valeur est à plus de 3 écarts-types de la moyenne glissante, elle est marquée comme suspecte.

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ALGORITHME A2 : Z-SCORE OUTLIER DETECTION
================================================================================
Projet              : VertiFlow
Ticket              : TICKET-020
Responsable         : @Mouhammed (Data Engineer)
Emplacement         : NiFi / Zone 2 / Groupe Validation
Type                : Script Python (Jython) pour ExecuteScript Processor

DESCRIPTION SCIENTIFIQUE:
Implémente le test de Z-Score pour filtrer les anomalies statistiques en temps réel.
Z = (X - μ) / σ
Si |Z| > 3, la donnée est considérée comme une erreur de capteur (99.7% confiance).

ENTRÉES:
    - flowFile (JSON): { "temp_c": 24.5, "sensor_id": "S1", ... }
    - State Manager: Stocke μ (moyenne) et σ (écart-type) par capteur.

SORTIES:
    - Attribut 'data_integrity_flag': 'VALID' ou 'INVALID_OUTLIER'
================================================================================
"""

import json
import math
from org.apache.commons.io import IOUtils
from java.nio.charset import StandardCharsets
from org.apache.nifi.processor.io import StreamCallback

class ZScoreFilter(StreamCallback):
    def __init__(self):
        pass

    def process(self, inputStream, outputStream):
        text = IOUtils.toString(inputStream, StandardCharsets.UTF_8)
        record = json.loads(text)
        
        # --- PARAMÈTRES SCIENTIFIQUES (Calibrés par @Asama) ---
        # Dans un vrai cas, ces valeurs viendraient du State Manager (Cache)
        # Exemple pour la Température (°C)
        MEAN_TEMP = 24.0  # Moyenne historique
        STD_DEV_TEMP = 2.5 # Écart-type toléré
        THRESHOLD = 3.0   # Seuil de rejet (Sigma)

        val = record.get('air_temp_internal')
        
        status = "VALID"
        z_score = 0.0

        if val is not None:
            try:
                float_val = float(val)
                # Calcul du Z-Score
                z_score = (float_val - MEAN_TEMP) / STD_DEV_TEMP
                
                if abs(z_score) > THRESHOLD:
                    status = "INVALID_OUTLIER"
                    # On ne rejette pas le flowfile, on le marque pour analyse
                    record['anomaly_confidence_score'] = 1.0 # 100% anomalie
                else:
                    record['anomaly_confidence_score'] = 0.0
                    
                record['z_score_temp'] = round(z_score, 2)
                
            except ValueError:
                status = "ERROR_TYPE"

        # Mise à jour du flag de qualité (Col 150)
        record['data_integrity_flag'] = status
        
        outputStream.write(json.dumps(record).encode('utf-8'))

flowFile = session.get()
if flowFile is not None:
    # Lecture & Écriture
    callback = ZScoreFilter()
    flowFile = session.write(flowFile, callback)
    
    # Lecture du status pour le routage NiFi
    # On lit le contenu pour extraire le flag (simplification pour l'exemple)
    # En prod, on utiliserait un attribut dédié.
    session.transfer(flowFile, REL_SUCCESS)
```

### Phase 2 : Survie & Contrôle (MongoDB)

#### 🛡️ Algorithme A4 : Seuillage & Alerte (Thresholding)

- **Ticket :** `TICKET-021`
- **Emplacement :** MongoDB (Trigger / Change Stream) ou Microservice Node.js
- **Objectif :** Protéger l'actif biologique. Compare la valeur entrante aux bornes définies par l'agronome.

```
/**
 * ================================================================================
 * ALGORITHME A4 : DYNAMIC THRESHOLDING (SURVIE)
 * ================================================================================
 * Projet              : VertiFlow
 * Ticket              : TICKET-021
 * Responsable         : @Asama (Biologiste) & @Imrane (DevOps)
 * Emplacement         : Cloud Citadel / Microservice Cortex
 * Type                : JavaScript (Node.js Logic)
 *
 * DESCRIPTION SCIENTIFIQUE:
 * Compare les métriques temps réel aux "Cibles Référentielles" (Colonnes 131-145).
 * Applique la Loi de Liebig (Facteur limitant) : Si un seul nutriment est critique,
 * l'alerte est maximale.
 *
 * ENTRÉES:
 * - Telemetry Document (Kafka Stream)
 *
 * SORTIES:
 * - Alert Object (envoyé à Power BI & Slack)
 * - Commande MQTT (Arrêt pompe)
 * ================================================================================
 */

function checkVitalSigns(telemetryData) {
    const alerts = [];
    const nutrients = telemetryData.nutrition; // Bloc II
    const targets = telemetryData.targets;     // Bloc XI (Cibles Expert)

    // 1. Vérification Azote (Nutrient N)
    // Tolérance : +/- 10% de la cible
    const n_min = targets.ref_n_target * 0.90;
    const n_max = targets.ref_n_target * 1.10;

    if (nutrients.nutrient_n_total < n_min) {
        alerts.push({
            level: "CRITICAL",
            code: "N_DEFICIENCY",
            message: `Carence Azote détectée: ${nutrients.nutrient_n_total} ppm (Cible > ${n_min})`,
            action: "INJECT_N_SOLUTION" // Ordre pour l'automate
        });
    }

    // 2. Vérification VPD (Vapor Pressure Deficit) - Moteur de transpiration
    // Cible : 0.8 - 1.2 kPa
    const vpd = telemetryData.environment.vapor_pressure_deficit;
    
    if (vpd > 1.5) {
        alerts.push({
            level: "WARNING",
            code: "HIGH_VPD_STRESS",
            message: `Stress hydrique (VPD élevé): ${vpd} kPa. Risque fermeture stomates.`,
            action: "ACTIVATE_MISTING" // Ordre brumisation
        });
    } else if (vpd < 0.4) {
        alerts.push({
            level: "WARNING",
            code: "LOW_VPD_RISK",
            message: `VPD trop bas: ${vpd} kPa. Risque fongique (Botrytis).`,
            action: "INCREASE_VENTILATION" // Ordre ventilateurs
        });
    }

    return {
        hasAlerts: alerts.length > 0,
        alerts: alerts,
        timestamp: new Date()
    };
}
```

### Phase 3 : Analyse Scientifique (ClickHouse)

#### 📊 Algorithme A7 : Corrélation de Pearson

- **Ticket :** `TICKET-022`
- **Emplacement :** ClickHouse (Vue Matérialisée SQL)
- **Objectif :** Prouver les hypothèses scientifiques. "Est-ce que l'ajout de lumière augmente vraiment la biomasse pour CETTE variété ?"

```
/*
================================================================================
ALGORITHME A7 : MATRICE DE CORRÉLATION (PEARSON)
================================================================================
Projet              : VertiFlow
Ticket              : TICKET-022
Responsable         : @Mounir (Architecte / Scientifique)
Emplacement         : ClickHouse / Init Scripts
Type                : SQL (Analytical Query)

DESCRIPTION SCIENTIFIQUE:
Calcule le coefficient de corrélation (r) entre les facteurs environnementaux (X)
et les résultats de croissance (Y).
-1 <= r <= 1.
Si r > 0.8 : Forte corrélation positive (Preuve validée).

REQUÊTE:
Analyse sur les 30 derniers jours, agrégée par Variété de Basilic.
================================================================================
*/

CREATE OR REPLACE VIEW smart_farming.view_algo_7_correlation AS
SELECT
    species_variety,
    
    -- Corrélation 1 : Lumière (DLI) vs Poids (Biomasse)
    -- Hypothèse : + de lumière = + de poids
    corr(light_dli_accumulated, fresh_biomass_est) AS r_light_growth,
    
    -- Corrélation 2 : Température vs Qualité (Huiles)
    -- Hypothèse : Température trop haute détruit les arômes
    corr(air_temp_internal, essential_oil_yield) AS r_temp_quality,
    
    -- Corrélation 3 : CO2 vs Vitesse de Croissance (RGR)
    corr(co2_level_ambient, relative_growth_rate) AS r_co2_speed,
    
    -- Métriques de fiabilité statistique
    count() AS sample_size,
    bar(r_light_growth, -1, 1, 50) AS viz_bar_light -- Visualisation ASCII dans la console

FROM smart_farming.basil_ultimate_realtime
WHERE 
    timestamp > now() - INTERVAL 30 DAY
    AND data_integrity_flag = 0 -- Uniquement données valides (Algo A2)
GROUP BY 
    species_variety
ORDER BY 
    species_variety;
```

### Phase 4 : Intelligence Prédictive (Python/ML)

#### 🔮 Algorithme A9 : Prédiction de Récolte (LSTM)

- **Ticket :** `TICKET-023`
- **Emplacement :** Cloud Citadel / `oracle.py`
- **Objectif :** Prédire la date exacte de récolte (`expected_harvest_date`) en analysant la courbe temporelle de croissance. Permet d'optimiser la logistique de vente.

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ALGORITHME A9 : LSTM HARVEST PREDICTOR
================================================================================
Projet              : VertiFlow
Ticket              : TICKET-023
Responsable         : @Mounir (Scientifique) & @Mouhammed (Data)
Emplacement         : cloud_citadel/nervous_system/oracle.py
Type                : Python (TensorFlow/Keras)

DESCRIPTION SCIENTIFIQUE:
Utilise un réseau de neurones récurrents (LSTM - Long Short-Term Memory) pour
modéliser la dynamique non-linéaire de la croissance du basilic.
Le modèle prend en entrée une séquence de 7 jours (T, H, PAR, CO2) et prédit
le 'fresh_biomass_est' à J+7.
Si Biomasse > Target, alors Date Récolte = Date actuelle + Jours prédits.

ENTRÉES:
    - Séquence temporelle (n_samples, 7 jours, 5 features)
    - Features: [air_temp, ppfd, vpd, co2, current_biomass]

SORTIES:
    - Prédiction: { "rack_id": "R1", "days_to_harvest": 4.5, "confidence": 0.92 }
================================================================================
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

class HarvestOracle:
    def __init__(self):
        self.model = self._build_model()
        
    def _build_model(self):
        """Construction de l'architecture neuronale."""
        model = Sequential()
        # Couche LSTM capable de retenir les dépendances temporelles (mémoire de la plante)
        model.add(LSTM(units=50, return_sequences=True, input_shape=(7, 5)))
        model.add(Dropout(0.2)) # Prévention du sur-apprentissage
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))
        
        # Couche de sortie : Prédiction de la biomasse (Régression)
        model.add(Dense(units=1)) 
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def predict_harvest_date(self, time_series_data, target_weight):
        """
        Calcule les jours restants avant récolte.
        
        :param time_series_data: Array (1, 7, 5) - Données des 7 derniers jours
        :param target_weight: Float - Poids cible (ex: 50g)
        """
        # 1. Prédiction de la croissance future (Simulation J+1, J+2...)
        current_weight = time_series_data[0, -1, 4] # Dernier poids connu
        days_remaining = 0
        predicted_weight = current_weight
        
        # Simulation itérative simplifiée pour l'exemple
        # (Dans la réalité, on prédit la séquence complète)
        while predicted_weight < target_weight and days_remaining < 30:
            growth_step = self.model.predict(time_series_data, verbose=0)
            predicted_weight += growth_step[0][0]
            days_remaining += 1
            
            # Mise à jour glissante de la fenêtre temporelle pour le pas suivant
            # (On suppose des conditions stables pour la simulation)
            
        return {
            "days_remaining": days_remaining,
            "predicted_final_biomass": float(predicted_weight),
            "status": "OPTIMAL" if days_remaining < 15 else "SLOW_GROWTH"
        }

# Exemple d'utilisation (Mock)
if __name__ == "__main__":
    oracle = HarvestOracle()
    print("🧠 Oracle LSTM initialisé. Prêt pour l'inférence.")
    # data = get_data_from_clickhouse(...)
    # res = oracle.predict_harvest_date(data, 50.0)
```

### Conclusion

Ce document rassemble la logique intellectuelle de votre projet.

- **NiFi (A2)** filtre le bruit.
- **MongoDB (A4)** protège la vie.
- **ClickHouse (A7)** valide la science.
- **Python (A9)** anticipe le marché.

C'est cette synergie qui fait de VertiFlow une plateforme unique.