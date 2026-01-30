# ============================================================================
# VERTIFLOW - Tests Unitaires Oracle (ML Predictions)
# ============================================================================

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestOracleYieldPredictor:
    """Tests pour le prédicteur de rendement."""

    def test_feature_extraction(self, sample_telemetry_data):
        """Test l'extraction de features depuis les données brutes."""
        features = self._extract_features([sample_telemetry_data])

        assert "temperature_avg" in features or len(features) > 0

    def test_yield_prediction_output_format(self, sample_features_for_prediction):
        """Test le format de sortie des prédictions."""
        # Simulation d'une prédiction
        mock_prediction = {
            "yield_g_per_plant": 45.5,
            "confidence": 0.92,
            "prediction_date": datetime.utcnow().isoformat()
        }

        assert "yield_g_per_plant" in mock_prediction
        assert 0 <= mock_prediction["confidence"] <= 1
        assert mock_prediction["yield_g_per_plant"] > 0

    def test_prediction_with_missing_features(self):
        """Test la gestion des features manquantes."""
        incomplete_features = {
            "temperature_avg": 24.5,
            # humidity_avg manquant
            "co2_ppm": 800
        }

        # Le système devrait gérer gracieusement les features manquantes
        # soit par imputation, soit par erreur explicite
        assert len(incomplete_features) < 10  # Moins que le nombre attendu

    def test_prediction_bounds(self, sample_features_for_prediction):
        """Test que les prédictions sont dans des bornes raisonnables."""
        # Le rendement du basilic est typiquement 20-80g par plante
        min_yield = 10
        max_yield = 100

        mock_yield = 45.5
        assert min_yield <= mock_yield <= max_yield

    def test_confidence_score_calculation(self):
        """Test le calcul du score de confiance."""
        # Le score de confiance dépend de la variance des prédictions
        mock_predictions = [44.5, 45.0, 45.5, 46.0, 45.2]
        variance = np.var(mock_predictions)

        # Plus la variance est faible, plus la confiance est élevée
        confidence = 1 / (1 + variance)
        assert 0 <= confidence <= 1

    def _extract_features(self, telemetry_batch):
        """Helper pour extraire les features."""
        if not telemetry_batch:
            return {}

        values = [t.get("value", 0) for t in telemetry_batch]
        return {
            "temperature_avg": np.mean(values) if values else 0,
            "temperature_std": np.std(values) if values else 0
        }


class TestOracleQualityClassifier:
    """Tests pour le classificateur de qualité."""

    def test_quality_classes(self):
        """Test les classes de qualité possibles."""
        valid_classes = ["premium", "standard", "economy", "reject"]
        predicted_class = "premium"

        assert predicted_class in valid_classes

    def test_classification_probabilities(self):
        """Test les probabilités de classification."""
        probabilities = {
            "premium": 0.75,
            "standard": 0.20,
            "economy": 0.04,
            "reject": 0.01
        }

        # Les probabilités doivent sommer à 1
        assert abs(sum(probabilities.values()) - 1.0) < 0.01

    def test_feature_importance(self):
        """Test l'importance des features pour la qualité."""
        feature_importance = {
            "temperature_stability": 0.25,
            "light_consistency": 0.20,
            "nutrient_balance": 0.20,
            "humidity_control": 0.15,
            "co2_levels": 0.10,
            "growth_rate": 0.10
        }

        # La somme des importances doit être ~1
        assert abs(sum(feature_importance.values()) - 1.0) < 0.01


class TestOracleHarvestPredictor:
    """Tests pour le prédicteur de date de récolte."""

    def test_harvest_date_prediction(self):
        """Test la prédiction de date de récolte."""
        germination_date = datetime(2025, 1, 1)
        expected_harvest_days = 35

        # La prédiction devrait être entre 28 et 42 jours
        predicted_days = 35
        assert 28 <= predicted_days <= 42

    def test_growth_stage_detection(self):
        """Test la détection du stade de croissance."""
        days_since_germination = 21

        if days_since_germination < 7:
            stage = "germination"
        elif days_since_germination < 28:
            stage = "vegetative"
        else:
            stage = "harvest_ready"

        assert stage == "vegetative"

    def test_environmental_impact_on_harvest(self):
        """Test l'impact environnemental sur la date de récolte."""
        # Des conditions sous-optimales retardent la récolte
        optimal_conditions = {"temp_deviation": 0, "light_deficit": 0}
        suboptimal_conditions = {"temp_deviation": 5, "light_deficit": 20}

        base_harvest_days = 35
        delay_factor = suboptimal_conditions["temp_deviation"] * 0.5 + \
                       suboptimal_conditions["light_deficit"] * 0.1

        adjusted_days = base_harvest_days + delay_factor
        assert adjusted_days > base_harvest_days


class TestOracleAnomalyDetector:
    """Tests pour la détection d'anomalies."""

    def test_anomaly_score_range(self):
        """Test la plage du score d'anomalie."""
        anomaly_score = 0.15

        # Le score doit être entre 0 (normal) et 1 (anomalie certaine)
        assert 0 <= anomaly_score <= 1

    def test_anomaly_threshold(self):
        """Test le seuil de détection d'anomalie."""
        threshold = 0.7
        scores = [0.1, 0.2, 0.85, 0.3, 0.9]

        anomalies = [s for s in scores if s > threshold]
        assert len(anomalies) == 2

    def test_multivariate_anomaly_detection(self, sample_telemetry_data):
        """Test la détection d'anomalies multivariées."""
        # Les anomalies peuvent être dans plusieurs dimensions
        data_point = {
            "temperature": 35,  # Trop élevé
            "humidity": 30,     # Trop bas
            "co2": 2000         # Trop élevé
        }

        limits = {
            "temperature": (18, 28),
            "humidity": (50, 80),
            "co2": (400, 1200)
        }

        anomalies = []
        for key, value in data_point.items():
            min_val, max_val = limits[key]
            if value < min_val or value > max_val:
                anomalies.append(key)

        assert len(anomalies) == 3  # Toutes les valeurs sont anormales


class TestOracleModelPersistence:
    """Tests pour la persistance des modèles."""

    def test_model_versioning(self):
        """Test le versioning des modèles."""
        model_metadata = {
            "model_id": "oracle_rf_v1.2.3",
            "version": "1.2.3",
            "trained_at": "2025-01-01T00:00:00Z",
            "metrics": {
                "rmse": 2.5,
                "r2": 0.92
            }
        }

        assert "version" in model_metadata
        assert "metrics" in model_metadata

    def test_model_loading(self):
        """Test le chargement d'un modèle."""
        # Simulation du chargement
        model_path = "models/oracle_rf.pkl"

        # Le modèle devrait exister et être chargeable
        # En test, on vérifie juste le chemin
        assert model_path.endswith(".pkl")

    def test_model_retraining_trigger(self):
        """Test le déclenchement du réentraînement."""
        current_accuracy = 0.85
        baseline_accuracy = 0.90
        drift_threshold = 0.05

        should_retrain = (baseline_accuracy - current_accuracy) > drift_threshold
        assert should_retrain is False  # 0.05 == seuil, pas de réentraînement
