# ============================================================================
# VERTIFLOW - Configuration MLflow pour MLOps
# ============================================================================

import os
import mlflow
from mlflow.tracking import MlflowClient
import logging

logger = logging.getLogger(__name__)


class MLflowConfig:
    """Configuration et utilitaires MLflow pour VertiFlow."""

    def __init__(self):
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        self.experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "vertiflow-models")
        self.artifact_location = os.getenv("MLFLOW_ARTIFACT_ROOT", "s3://mlflow-artifacts")

        # Configurer MLflow
        mlflow.set_tracking_uri(self.tracking_uri)

    def get_or_create_experiment(self, name: str = None) -> str:
        """Crée ou récupère un experiment MLflow."""
        exp_name = name or self.experiment_name
        experiment = mlflow.get_experiment_by_name(exp_name)

        if experiment is None:
            experiment_id = mlflow.create_experiment(
                exp_name,
                artifact_location=self.artifact_location
            )
            logger.info(f"Created experiment: {exp_name} (ID: {experiment_id})")
        else:
            experiment_id = experiment.experiment_id
            logger.info(f"Using existing experiment: {exp_name} (ID: {experiment_id})")

        mlflow.set_experiment(exp_name)
        return experiment_id

    def log_model_metrics(self, metrics: dict, step: int = None):
        """Log des métriques du modèle."""
        for key, value in metrics.items():
            mlflow.log_metric(key, value, step=step)

    def log_model_params(self, params: dict):
        """Log des paramètres du modèle."""
        mlflow.log_params(params)

    def log_model(self, model, model_name: str, registered_name: str = None):
        """Enregistre un modèle dans MLflow."""
        # Log le modèle
        if hasattr(model, 'predict'):
            mlflow.sklearn.log_model(model, model_name)
        else:
            mlflow.pyfunc.log_model(model_name, python_model=model)

        # Optionnellement, enregistrer dans le Model Registry
        if registered_name:
            run_id = mlflow.active_run().info.run_id
            model_uri = f"runs:/{run_id}/{model_name}"
            mlflow.register_model(model_uri, registered_name)
            logger.info(f"Registered model: {registered_name}")

    def get_latest_model_version(self, model_name: str, stage: str = "Production") -> str:
        """Récupère la dernière version d'un modèle en production."""
        client = MlflowClient()
        try:
            versions = client.get_latest_versions(model_name, stages=[stage])
            if versions:
                return versions[0].version
        except Exception as e:
            logger.error(f"Error getting model version: {e}")
        return None

    def transition_model_stage(self, model_name: str, version: str, stage: str):
        """Transite un modèle vers un nouveau stage."""
        client = MlflowClient()
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=True
        )
        logger.info(f"Transitioned {model_name} v{version} to {stage}")


class DriftDetector:
    """Détecteur de drift pour les modèles ML."""

    def __init__(self, baseline_metrics: dict, threshold: float = 0.05):
        self.baseline_metrics = baseline_metrics
        self.threshold = threshold

    def check_drift(self, current_metrics: dict) -> dict:
        """Vérifie le drift entre les métriques actuelles et la baseline."""
        drift_report = {
            "has_drift": False,
            "drifted_metrics": [],
            "details": {}
        }

        for metric, baseline_value in self.baseline_metrics.items():
            if metric in current_metrics:
                current_value = current_metrics[metric]
                drift = abs(current_value - baseline_value) / baseline_value

                drift_report["details"][metric] = {
                    "baseline": baseline_value,
                    "current": current_value,
                    "drift_pct": drift * 100
                }

                if drift > self.threshold:
                    drift_report["has_drift"] = True
                    drift_report["drifted_metrics"].append(metric)

        return drift_report

    def should_retrain(self, drift_report: dict) -> bool:
        """Détermine si le modèle doit être réentraîné."""
        critical_metrics = ["rmse", "accuracy", "r2"]

        for metric in drift_report.get("drifted_metrics", []):
            if metric in critical_metrics:
                return True

        return False


class ModelRegistry:
    """Gestionnaire du registre de modèles."""

    MODELS = {
        "oracle_yield": {
            "description": "Prédiction du rendement (g/plante)",
            "type": "regression",
            "metrics": ["rmse", "mae", "r2"]
        },
        "quality_classifier": {
            "description": "Classification de la qualité (premium/standard/economy)",
            "type": "classification",
            "metrics": ["accuracy", "precision", "recall", "f1"]
        },
        "harvest_predictor": {
            "description": "Prédiction de la date de récolte",
            "type": "regression",
            "metrics": ["mae_days", "r2"]
        },
        "anomaly_detector": {
            "description": "Détection d'anomalies environnementales",
            "type": "anomaly",
            "metrics": ["precision", "recall", "f1"]
        }
    }

    @classmethod
    def get_model_info(cls, model_name: str) -> dict:
        """Récupère les informations d'un modèle."""
        return cls.MODELS.get(model_name, {})

    @classmethod
    def list_models(cls) -> list:
        """Liste tous les modèles enregistrés."""
        return list(cls.MODELS.keys())
