# MLOps - Machine Learning Operations

Ce dossier contient la configuration MLOps pour VertiFlow.

## Structure

```
mlops/
├── __init__.py
└── mlflow/
    ├── __init__.py
    └── mlflow_config.py             # Configuration MLflow
```

## Status

**En cours de developpement** - Infrastructure MLflow en preparation.

## MLflow

### Configuration
```python
# mlflow_config.py
MLFLOW_TRACKING_URI = "http://mlflow:5000"
MLFLOW_EXPERIMENT_NAME = "vertiflow-models"
MLFLOW_ARTIFACT_LOCATION = "s3://vertiflow-mlflow/artifacts"
```

### Modeles suivis

| Modele | Experiment | Metriques |
|--------|------------|-----------|
| Oracle (A9) | yield-prediction | R2, MAE, RMSE |
| Classifier (A10) | quality-classification | Accuracy, F1, AUC |
| Cortex (A11) | recipe-optimization | Convergence, Cost |

## Utilisation prevue

### Entrainement avec tracking
```python
import mlflow
from mlflow.sklearn import log_model

mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("yield-prediction")

with mlflow.start_run():
    # Entrainement
    model = train_oracle_model(X, y)

    # Logging
    mlflow.log_params({"n_estimators": 100, "max_depth": 10})
    mlflow.log_metrics({"r2": 0.87, "mae": 5.2})
    log_model(model, "oracle_model")
```

### Serving
```bash
# Deployer un modele
mlflow models serve -m "models:/oracle_model/Production" -p 5001
```

## Architecture cible

```
┌─────────────────────────────────────────────────┐
│                    MLflow Server                 │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐              │
│  │  Tracking   │  │  Registry   │              │
│  │   Server    │  │   Server    │              │
│  └─────────────┘  └─────────────┘              │
│  ┌─────────────────────────────────┐           │
│  │        Artifact Store (S3)      │           │
│  └─────────────────────────────────┘           │
└─────────────────────────────────────────────────┘
```

## Roadmap

- [ ] Deploiement MLflow Server
- [ ] Integration CI/CD pour entrainement
- [ ] Model Registry avec versions
- [ ] A/B Testing pour modeles
- [ ] Monitoring des predictions (drift)
