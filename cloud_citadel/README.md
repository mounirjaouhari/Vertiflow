# Cloud Citadel - Intelligence & ML

Ce dossier contient les algorithmes d'intelligence artificielle et de machine learning de VertiFlow.

## Structure

```
cloud_citadel/
├── __init__.py
├── connectors/                      # Connecteurs de donnees
│   ├── feedback_loop.py             # Pipeline de re-entrainement
│   └── stream_processor.py          # Kafka -> ClickHouse
└── nervous_system/                  # Algorithmes ML (A9-A11)
    ├── connectors/                  # Connecteurs DB
    │   └── clickhouse_sink.json
    ├── classifier.py                # A10 - Classification qualite
    ├── cortex.py                    # A11 - Optimisation recettes
    ├── harvest_predictor.py         # A9b - Prediction recolte (GDD+Gompertz)
    ├── oracle.py                    # A9 - Prediction rendement
    ├── nervous_system.py            # Predictions LSTM
    └── simulator.py                 # Modeles bio-physiques
```

## Configuration

Les parametres agronomiques sont centralises dans `config/agronomic_parameters.yaml`.
Voir le dossier [config/](../config/) pour la configuration globale.

## Algorithmes

### A9 - Oracle (Prediction de rendement)
**Fichier:** `nervous_system/oracle.py`

- **Modele:** RandomForest Regressor
- **Input:** Temperature, Humidite, DLI, EC, pH
- **Output:** Rendement predit (g/m2)
- **Performance:** R2 > 0.87
- **Mapping Zones:** ZONE_A→Z1, ZONE_B→Z2, NURSERY→Z3 (voir ZONE_MAPPING dans oracle.py)
- **Service Docker:** `ml-engine` (continu, cycle 5min)

### A9b - Harvest Predictor (Prediction date de recolte)
**Fichier:** `nervous_system/harvest_predictor.py`

Modele scientifique base sur GDD (Growing Degree Days) et courbe de Gompertz.

- **Methode:** GDD + Gompertz Growth Model
- **References scientifiques:**
  - McMaster & Wilhelm (1997) - Growing Degree Days calculation
  - Zwietering et al. (1990) - Gompertz growth model
  - Tetens (1930) - VPD calculation
  - Faust & Logan (2018) - DLI optimal ranges
- **Parametres Basilic:**
  - T_base = 10°C (temperature de base)
  - GDD_harvest = 550 (cumul GDD pour recolte)
  - VPD_optimal = 1.0 kPa (0.8-1.2 kPa)
  - DLI_optimal = 17 mol/m²/jour
  - Biomasse_max = 120g (par plant)
- **Input:** Temperature, Humidite, PPFD depuis ClickHouse (telemetry_enriched)
- **Output:** 
  - Jours restants avant recolte
  - Date de recolte predite
  - Biomasse estimee (g)
  - Stade de croissance (SEEDLING, VEGETATIVE, PRE_HARVEST, READY)
  - VPD et DLI calcules
  - Facteur de stress (0-1)
  - Niveau de confiance
- **Stockage:** ClickHouse table `harvest_predictions`
- **Service Docker:** `ml-harvest` (continu, cycle 30min)

### A10 - Classifier (Classification qualite)
**Fichier:** `nervous_system/classifier.py`

- **Modele:** Gradient Boosting Classifier (ou Mock si modele absent)
- **Input:** Biomasse, couleur, defauts (depuis Kafka topic basil_telemetry_full)
- **Output:** Grade (Premium, Standard, Reject) → Kafka + ClickHouse (quality_classifications)
- **Performance:** Accuracy > 92%
- **Service Docker:** `ml-classifier` (continu, ecoute Kafka)

### A11 - Cortex (Optimisation recettes)
**Fichier:** `nervous_system/cortex.py`

- **Methode:** Scipy L-BFGS-B + contraintes agronomiques
- **Input:** Performances passees depuis ClickHouse (30 jours)
- **Output:** Recette optimisee (EC, pH, DLI, T) → MongoDB plant_recipes
- **Service Docker:** `ml-cortex` (cycle 24h)

### Simulator (Modeles bio-physiques)
**Fichier:** `nervous_system/simulator.py`

Modeles scientifiques :
- **VPD:** Deficit de pression de vapeur (Tetens)
- **Photosynthese:** Modele Farquhar-von Caemmerer-Berry
- **Transpiration:** Penman-Monteith
- **Croissance:** Modele exponentiel-logistique

## Connecteurs

### Stream Processor
Traitement temps reel Kafka -> ClickHouse

### Feedback Loop
Pipeline de re-entrainement automatique
