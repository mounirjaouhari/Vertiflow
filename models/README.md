# Models - Entrainement ML

Ce dossier contient les scripts d'entrainement des modeles ML VertiFlow.

## Structure

```
models/
├── __init__.py
├── model_registry.yaml              # Registre des modeles
├── train_all_models.py              # Orchestrateur d'entrainement
├── train_oracle_model.py            # A9 - Prediction rendement
├── train_quality_classifier.py      # A10 - Classification qualite
└── train_harvest_lstm.py            # A9 - Date de recolte (LSTM)
```

## Modeles

### A9 - Oracle (Yield Prediction)
**Fichier:** `train_oracle_model.py`

```bash
python models/train_oracle_model.py
# ou via Makefile
make train-oracle
```

| Parametre | Valeur |
|-----------|--------|
| Algorithme | RandomForest |
| Features | temp, humidity, DLI, EC, pH, CO2 |
| Target | yield_g_m2 |
| R2 Score | > 0.87 |

### A10 - Quality Classifier
**Fichier:** `train_quality_classifier.py`

```bash
python models/train_quality_classifier.py
# ou via Makefile
make train-quality
```

| Parametre | Valeur |
|-----------|--------|
| Algorithme | GradientBoosting |
| Features | biomass, color, defects |
| Classes | Premium, Standard, Reject |
| Accuracy | > 92% |

### A9 - Harvest LSTM
**Fichier:** `train_harvest_lstm.py`

```bash
python models/train_harvest_lstm.py
# ou via Makefile
make train-harvest
```

| Parametre | Valeur |
|-----------|--------|
| Algorithme | LSTM |
| Sequence | 7 jours |
| Target | days_to_harvest |
| MAE | < 2 jours |

## Orchestrateur

### train_all_models.py
Entraine tous les modeles sequentiellement :

```bash
python models/train_all_models.py

# Options
python models/train_all_models.py --model oracle     # Un seul modele
python models/train_all_models.py --skip-lstm        # Sauter LSTM
python models/train_all_models.py --data-path ./data # Chemin donnees
```

## Model Registry

### model_registry.yaml
```yaml
models:
  oracle_yield:
    version: "1.2.0"
    algorithm: "RandomForest"
    trained_at: "2026-01-04"
    metrics:
      r2: 0.87
      mae: 5.2
    artifact: "models/artifacts/oracle_yield_v1.2.0.pkl"

  quality_classifier:
    version: "1.0.0"
    algorithm: "GradientBoosting"
    trained_at: "2026-01-03"
    metrics:
      accuracy: 0.92
      f1_macro: 0.89
    artifact: "models/artifacts/quality_classifier_v1.0.0.pkl"
```

## Artefacts

Les modeles entraines sont sauvegardes dans :
```
models/artifacts/
├── oracle_yield_v*.pkl
├── quality_classifier_v*.pkl
└── harvest_lstm_v*.h5
```
