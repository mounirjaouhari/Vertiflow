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

### A10 - Classifier (Classification qualite)
**Fichier:** `nervous_system/classifier.py`

- **Modele:** Gradient Boosting Classifier
- **Input:** Biomasse, couleur, defauts
- **Output:** Grade (Premium, Standard, Reject)
- **Performance:** Accuracy > 92%

### A11 - Cortex (Optimisation recettes)
**Fichier:** `nervous_system/cortex.py`

- **Methode:** Gradient descent + contraintes agronomiques
- **Input:** Objectif (rendement, qualite, energie)
- **Output:** Recette optimisee (EC, pH, DLI, T)

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
