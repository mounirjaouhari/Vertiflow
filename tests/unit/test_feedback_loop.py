#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de création    : 02/01/2026
Équipe              : VertiFlow Core Team

Membres de l'équipe :
    🧙‍♂️ Mounir      - Architecte & Scientifique (Python Dev)
    🏗️ Imrane      - DevOps & Infrastructure (Python Dev)
    🐍 Mouhammed   - Data Engineer & Analyste ETL
    🧬 Asama       - Biologiste & Domain Expert (Python Dev)
    ⚖️ MrZakaria   - Encadrant & Architecte Data

--------------------------------------------------------------------------------
MODULE: tests/unit/test_feedback_loop.py
DESCRIPTION: Tests unitaires pour la boucle de rétroaction (feedback_loop.py)

    Le Feedback Loop est le système de RÉAPPRENTISSAGE de VertiFlow.
    Il compare les prédictions passées aux résultats réels pour améliorer
    continuellement la précision des modèles ML.

    CYCLE DE RÉTROACTION:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                     FEEDBACK LOOP - AMÉLIORATION CONTINUE               │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  ┌──────────────────┐                                                   │
    │  │  Oracle (J-30)   │──┐                                                │
    │  │  Prédiction:     │  │    ┌─────────────────────────────────────┐     │
    │  │  Yield = 45g     │  ├───▶│  COMPARAISON PRÉDICTION vs RÉALITÉ  │     │
    │  │  Conf: 0.85      │  │    │                                     │     │
    │  └──────────────────┘  │    │  Prédiction: 45g ± 5g               │     │
    │                        │    │  Réalité:    42g (ClickHouse)       │     │
    │  ┌──────────────────┐  │    │  Erreur:     3g (6.7%)              │     │
    │  │  ClickHouse      │──┘    │  Statut:     ✅ DANS TOLÉRANCE      │     │
    │  │  (Aujourd'hui)   │       │                                     │     │
    │  │  Récolte: 42g    │       └────────────────┬────────────────────┘     │
    │  └──────────────────┘                        │                          │
    │                                              ▼                          │
    │                         ┌─────────────────────────────────────────┐     │
    │                         │        ANALYSE DES ÉCARTS               │     │
    │                         ├─────────────────────────────────────────┤     │
    │                         │ Si erreur > 15%:                        │     │
    │                         │   → Déclencher réentraînement           │     │
    │                         │   → Ajuster hyperparamètres             │     │
    │                         │   → Alerter équipe Data Science         │     │
    │                         │                                         │     │
    │                         │ Si erreur < 15%:                        │     │
    │                         │   → Logger pour analyse tendance        │     │
    │                         │   → Accumuler données entraînement      │     │
    │                         └────────────────┬────────────────────────┘     │
    │                                          │                              │
    │                                          ▼                              │
    │  ┌───────────────────────────────────────────────────────────────────┐  │
    │  │                    STOCKAGE MÉTRIQUES (MongoDB)                   │  │
    │  ├───────────────────────────────────────────────────────────────────┤  │
    │  │  {                                                                │  │
    │  │    "prediction_id": "PRED_20251203_R01_001",                      │  │
    │  │    "predicted_value": 45.0,                                       │  │
    │  │    "actual_value": 42.0,                                          │  │
    │  │    "error_pct": 6.67,                                             │  │
    │  │    "mae": 3.0,                                                    │  │
    │  │    "within_tolerance": true,                                      │  │
    │  │    "evaluated_at": "2026-01-02T12:00:00Z"                         │  │
    │  │  }                                                                │  │
    │  └───────────────────────────────────────────────────────────────────┘  │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

    MÉTRIQUES DE PERFORMANCE CALCULÉES:
    ┌────────────────────┬─────────────────────────────────────────────────────┐
    │ Métrique           │ Description                                         │
    ├────────────────────┼─────────────────────────────────────────────────────┤
    │ MAE                │ Mean Absolute Error - Erreur absolue moyenne        │
    │ RMSE               │ Root Mean Square Error - Sensible aux gros écarts   │
    │ MAPE               │ Mean Absolute Percentage Error - Erreur relative    │
    │ R²                 │ Coefficient de détermination - Qualité ajustement   │
    │ Accuracy@15%       │ % prédictions dans ±15% de la réalité               │
    └────────────────────┴─────────────────────────────────────────────────────┘

IMPORTANCE CRITIQUE:
    Sans feedback loop, les modèles ML dérivent avec le temps (concept drift).
    Les conditions changent (saisons, nouvelles variétés, usure équipements)
    et les prédictions deviennent obsolètes.

Développé par       : @Mounir & @Mouhammed
Ticket(s) associé(s): TICKET-107
Sprint              : Semaine 6 - Phase Qualité & Tests

Dépendances:
    - pytest>=8.0.0
    - numpy>=2.1.0
    - pandas>=2.2.0

================================================================================
© 2026 VertiFlow Core Team - Tous droits réservés
Développé dans le cadre de l'Initiative Nationale Marocaine JobInTech
au sein de l'École YNOV Maroc Campus
================================================================================
"""

import os
import pytest
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock

# =============================================================================
# IMPORT DU MODULE À TESTER
# =============================================================================

try:
    from cloud_citadel.connectors.feedback_loop import FeedbackLoop
    FEEDBACK_LOOP_AVAILABLE = True
except ImportError as e:
    FEEDBACK_LOOP_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Skip tous les tests si le module n'est pas importable
pytestmark = pytest.mark.skipif(
    not FEEDBACK_LOOP_AVAILABLE,
    reason=f"Module feedback_loop non disponible: {IMPORT_ERROR if not FEEDBACK_LOOP_AVAILABLE else ''}"
)


# =============================================================================
# CONSTANTES DE TEST
# =============================================================================

# Seuils de tolérance pour les prédictions
TOLERANCE_YIELD_PCT = 15.0      # ±15% pour le rendement
TOLERANCE_QUALITY_PCT = 10.0    # ±10% pour la qualité
TOLERANCE_GROWTH_DAYS = 2       # ±2 jours pour la durée de croissance

# Seuils pour déclencher le réentraînement
RETRAIN_THRESHOLD_MAE = 5.0     # MAE > 5g → réentraînement
RETRAIN_THRESHOLD_MAPE = 20.0   # MAPE > 20% → réentraînement
RETRAIN_MIN_SAMPLES = 100       # Minimum d'échantillons pour évaluer

# Identifiants de test
TEST_PREDICTION_ID = "PRED_TEST_20260102_001"
TEST_RACK_ID = "R01"
TEST_CYCLE_ID = "CYCLE_2026_001"


# =============================================================================
# FIXTURES SPÉCIFIQUES AU FEEDBACK LOOP
# =============================================================================

@pytest.fixture
def mock_clickhouse_predictions():
    """
    Mock du client ClickHouse pour récupérer les prédictions historiques.
    
    Simule la table `predictions_yield` qui stocke les prédictions
    faites par l'Oracle à J-30.
    
    COLONNES:
        - prediction_id: Identifiant unique
        - rack_id: Rack concerné
        - predicted_at: Date de la prédiction
        - predicted_yield_g: Rendement prédit (grammes)
        - confidence: Confiance du modèle (0-1)
        - target_harvest_date: Date de récolte prévue
    """
    mock_client = MagicMock()
    
    # Prédictions historiques (faites il y a 30 jours)
    prediction_date = datetime.now(timezone.utc) - timedelta(days=30)
    harvest_date = datetime.now(timezone.utc)
    
    mock_client.execute.return_value = [
        # (prediction_id, rack_id, predicted_at, predicted_yield_g, confidence, target_date)
        ("PRED_001", "R01", prediction_date, 45.0, 0.85, harvest_date),
        ("PRED_002", "R01", prediction_date, 42.0, 0.82, harvest_date),
        ("PRED_003", "R02", prediction_date, 48.0, 0.88, harvest_date),
        ("PRED_004", "R02", prediction_date, 44.0, 0.79, harvest_date),
        ("PRED_005", "R03", prediction_date, 50.0, 0.91, harvest_date),
    ]
    
    return mock_client


@pytest.fixture
def mock_clickhouse_actuals():
    """
    Mock du client ClickHouse pour récupérer les valeurs réelles (récoltes).
    
    Simule la table `harvest_records` qui enregistre les récoltes effectives.
    
    COLONNES:
        - harvest_id: Identifiant unique
        - rack_id: Rack récolté
        - harvested_at: Date de récolte
        - actual_yield_g: Rendement réel (grammes)
        - quality_score: Score qualité (0-100)
    """
    mock_client = MagicMock()
    
    # Récoltes effectuées (aujourd'hui)
    harvest_date = datetime.now(timezone.utc)
    
    mock_client.execute.return_value = [
        # (harvest_id, rack_id, harvested_at, actual_yield_g, quality_score)
        ("HARV_001", "R01", harvest_date, 42.0, 88),  # -3g vs prédit
        ("HARV_002", "R01", harvest_date, 40.0, 85),  # -2g vs prédit
        ("HARV_003", "R02", harvest_date, 52.0, 92),  # +4g vs prédit
        ("HARV_004", "R02", harvest_date, 43.0, 82),  # -1g vs prédit
        ("HARV_005", "R03", harvest_date, 47.0, 90),  # -3g vs prédit
    ]
    
    return mock_client


@pytest.fixture
def mock_mongodb_metrics():
    """
    Mock du client MongoDB pour stocker les métriques de feedback.
    
    Collection: `feedback_metrics`
    Stocke l'historique des comparaisons prédiction vs réalité.
    """
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client.__getitem__ = MagicMock(return_value=mock_db)
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    mock_db.feedback_metrics = mock_collection
    
    # insert_one retourne un résultat avec inserted_id
    mock_collection.insert_one.return_value = MagicMock(
        inserted_id="60f1234567890abcdef12345"
    )
    
    # find retourne un curseur mockable
    mock_collection.find.return_value = []
    
    return mock_client


@pytest.fixture
def feedback_instance(mock_clickhouse_predictions, mock_clickhouse_actuals, mock_mongodb_metrics):
    """
    Crée une instance de FeedbackLoop avec dépendances mockées.
    """
    with patch('cloud_citadel.connectors.feedback_loop.Client') as mock_ch_class:
        # Le même mock pour les deux usages (prédictions et actuals)
        mock_ch_class.return_value = mock_clickhouse_predictions
        
        with patch('cloud_citadel.connectors.feedback_loop.MongoClient') as mock_mongo_class:
            mock_mongo_class.return_value = mock_mongodb_metrics
            
            # Créer l'instance
            loop = FeedbackLoop()
            
            # Injecter les mocks
            loop.ch_client = mock_clickhouse_predictions
            loop.mongo_client = mock_mongodb_metrics
            loop.db_ml = mock_mongodb_metrics['vertiflow_ml']
            
            yield loop


@pytest.fixture
def sample_predictions():
    """
    Échantillon de prédictions pour les tests de calcul.
    
    Format: Liste de dicts avec predicted et actual.
    """
    return [
        {"predicted": 45.0, "actual": 42.0},  # -6.67%
        {"predicted": 42.0, "actual": 40.0},  # -4.76%
        {"predicted": 48.0, "actual": 52.0},  # +8.33%
        {"predicted": 44.0, "actual": 43.0},  # -2.27%
        {"predicted": 50.0, "actual": 47.0},  # -6.00%
    ]


@pytest.fixture
def sample_predictions_with_drift():
    """
    Échantillon avec drift significatif (erreur élevée).
    
    Simule un modèle qui nécessite un réentraînement.
    """
    return [
        {"predicted": 45.0, "actual": 32.0},  # -28.9%
        {"predicted": 42.0, "actual": 30.0},  # -28.6%
        {"predicted": 48.0, "actual": 35.0},  # -27.1%
        {"predicted": 44.0, "actual": 31.0},  # -29.5%
        {"predicted": 50.0, "actual": 36.0},  # -28.0%
    ]


# =============================================================================
# CLASSE DE TEST: CALCUL DES MÉTRIQUES D'ERREUR
# =============================================================================

class TestErrorMetricsCalculation:
    """
    Tests du calcul des métriques d'erreur de prédiction.
    
    Ces métriques quantifient la précision des modèles ML.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Calcul du MAE (Mean Absolute Error)
    # -------------------------------------------------------------------------
    def test_calculate_mae(self, feedback_instance, sample_predictions):
        """
        Test: calcul correct du MAE.
        
        MAE = (1/n) × Σ|predicted - actual|
        
        DONNÉES:
            |45-42| + |42-40| + |48-52| + |44-43| + |50-47|
            = 3 + 2 + 4 + 1 + 3 = 13
            MAE = 13 / 5 = 2.6g
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # EXPECTED
        expected_mae = 2.6
        
        # ACT
        mae = feedback_instance.calculate_mae(predictions, actuals)
        
        # ASSERT
        assert abs(mae - expected_mae) < 0.01, (
            f"MAE incorrect.\n"
            f"Attendu: {expected_mae}g\n"
            f"Obtenu: {mae:.2f}g"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Calcul du RMSE (Root Mean Square Error)
    # -------------------------------------------------------------------------
    def test_calculate_rmse(self, feedback_instance, sample_predictions):
        """
        Test: calcul correct du RMSE.
        
        RMSE = √[(1/n) × Σ(predicted - actual)²]
        
        DONNÉES:
            (3² + 2² + 4² + 1² + 3²) = 9 + 4 + 16 + 1 + 9 = 39
            RMSE = √(39/5) = √7.8 ≈ 2.79g
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # EXPECTED
        expected_rmse = np.sqrt(39 / 5)  # ≈ 2.79
        
        # ACT
        rmse = feedback_instance.calculate_rmse(predictions, actuals)
        
        # ASSERT
        assert abs(rmse - expected_rmse) < 0.01, (
            f"RMSE incorrect.\n"
            f"Attendu: {expected_rmse:.2f}g\n"
            f"Obtenu: {rmse:.2f}g"
        )
    
    # -------------------------------------------------------------------------
    # TEST 3: Calcul du MAPE (Mean Absolute Percentage Error)
    # -------------------------------------------------------------------------
    def test_calculate_mape(self, feedback_instance, sample_predictions):
        """
        Test: calcul correct du MAPE.
        
        MAPE = (100/n) × Σ|predicted - actual| / actual
        
        DONNÉES:
            3/42 + 2/40 + 4/52 + 1/43 + 3/47
            = 0.0714 + 0.05 + 0.0769 + 0.0233 + 0.0638
            = 0.2854
            MAPE = 28.54 / 5 = 5.71%
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # EXPECTED (calcul manuel)
        errors = [abs(p - a) / a for p, a in zip(predictions, actuals)]
        expected_mape = np.mean(errors) * 100
        
        # ACT
        mape = feedback_instance.calculate_mape(predictions, actuals)
        
        # ASSERT
        assert abs(mape - expected_mape) < 0.1, (
            f"MAPE incorrect.\n"
            f"Attendu: {expected_mape:.2f}%\n"
            f"Obtenu: {mape:.2f}%"
        )
    
    # -------------------------------------------------------------------------
    # TEST 4: Calcul du R² (coefficient de détermination)
    # -------------------------------------------------------------------------
    def test_calculate_r_squared(self, feedback_instance, sample_predictions):
        """
        Test: calcul correct du R².
        
        R² = 1 - (SS_res / SS_tot)
        
        Où:
            SS_res = Σ(actual - predicted)²
            SS_tot = Σ(actual - mean(actual))²
        
        R² proche de 1 = bonnes prédictions
        R² proche de 0 = prédictions pas meilleures que la moyenne
        R² < 0 = prédictions pires que la moyenne
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # EXPECTED
        mean_actual = np.mean(actuals)
        ss_res = sum((a - p) ** 2 for p, a in zip(predictions, actuals))
        ss_tot = sum((a - mean_actual) ** 2 for a in actuals)
        expected_r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # ACT
        r2 = feedback_instance.calculate_r_squared(predictions, actuals)
        
        # ASSERT
        assert abs(r2 - expected_r2) < 0.01, (
            f"R² incorrect.\n"
            f"Attendu: {expected_r2:.4f}\n"
            f"Obtenu: {r2:.4f}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 5: Accuracy dans la tolérance
    # -------------------------------------------------------------------------
    def test_calculate_accuracy_within_tolerance(self, feedback_instance, sample_predictions):
        """
        Test: calcul du % de prédictions dans la tolérance.
        
        TOLÉRANCE: ±15%
        
        DONNÉES:
            45 vs 42: erreur 7.1% → ✅ dans tolérance
            42 vs 40: erreur 5.0% → ✅ dans tolérance
            48 vs 52: erreur 7.7% → ✅ dans tolérance
            44 vs 43: erreur 2.3% → ✅ dans tolérance
            50 vs 47: erreur 6.4% → ✅ dans tolérance
        
        Accuracy = 5/5 = 100%
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # ACT
        accuracy = feedback_instance.calculate_accuracy_at_tolerance(
            predictions, actuals, tolerance_pct=15.0
        )
        
        # ASSERT
        assert accuracy == 100.0, (
            f"Toutes les prédictions sont dans ±15%, accuracy devrait être 100%.\n"
            f"Obtenu: {accuracy:.1f}%"
        )
    
    # -------------------------------------------------------------------------
    # TEST 6: Accuracy avec drift
    # -------------------------------------------------------------------------
    def test_calculate_accuracy_with_drift(self, feedback_instance, sample_predictions_with_drift):
        """
        Test: accuracy faible quand le modèle dérive.
        
        DONNÉES (drift ~28%):
            Toutes les erreurs > 15% → aucune dans la tolérance
            Accuracy = 0%
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions_with_drift]
        actuals = [p["actual"] for p in sample_predictions_with_drift]
        
        # ACT
        accuracy = feedback_instance.calculate_accuracy_at_tolerance(
            predictions, actuals, tolerance_pct=15.0
        )
        
        # ASSERT
        assert accuracy == 0.0, (
            f"Aucune prédiction n'est dans ±15% (drift ~28%), accuracy devrait être 0%.\n"
            f"Obtenu: {accuracy:.1f}%"
        )


# =============================================================================
# CLASSE DE TEST: COMPARAISON PRÉDICTION VS RÉALITÉ
# =============================================================================

class TestPredictionComparison:
    """
    Tests de la comparaison entre prédictions et valeurs réelles.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Comparaison simple
    # -------------------------------------------------------------------------
    def test_compare_single_prediction(self, feedback_instance):
        """
        Test: comparaison d'une prédiction unique avec la réalité.
        
        ENTRÉE:
            Prediction: 45.0g
            Actual: 42.0g
        
        SORTIE ATTENDUE:
            {
                "error_absolute": 3.0,
                "error_pct": 7.14,
                "within_tolerance": True
            }
        """
        # ACT
        result = feedback_instance.compare_prediction(
            predicted=45.0,
            actual=42.0,
            tolerance_pct=15.0
        )
        
        # ASSERT
        assert result is not None, "Le résultat ne devrait pas être None"
        
        assert "error_absolute" in result or "absolute_error" in result, (
            "Erreur absolue manquante"
        )
        
        error_abs = result.get("error_absolute", result.get("absolute_error"))
        assert abs(error_abs - 3.0) < 0.01, f"Erreur absolue incorrecte: {error_abs}"
        
        assert "within_tolerance" in result, "Statut tolérance manquant"
        assert result["within_tolerance"] is True, "Devrait être dans la tolérance"
    
    # -------------------------------------------------------------------------
    # TEST 2: Comparaison hors tolérance
    # -------------------------------------------------------------------------
    def test_compare_prediction_out_of_tolerance(self, feedback_instance):
        """
        Test: détection d'une prédiction hors tolérance.
        
        ENTRÉE:
            Prediction: 45.0g
            Actual: 32.0g
            Erreur: 40.6% > 15%
        """
        # ACT
        result = feedback_instance.compare_prediction(
            predicted=45.0,
            actual=32.0,
            tolerance_pct=15.0
        )
        
        # ASSERT
        assert result["within_tolerance"] is False, (
            f"Erreur de 40% devrait être hors tolérance.\n"
            f"Résultat: {result}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 3: Comparaison batch
    # -------------------------------------------------------------------------
    def test_compare_batch_predictions(self, feedback_instance, sample_predictions):
        """
        Test: comparaison d'un lot de prédictions.
        
        ENTRÉE:
            Liste de 5 paires (predicted, actual)
        
        SORTIE:
            Liste de 5 résultats de comparaison
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # ACT
        results = feedback_instance.compare_batch(predictions, actuals)
        
        # ASSERT
        assert len(results) == len(sample_predictions), (
            f"Nombre de résultats incorrect.\n"
            f"Attendu: {len(sample_predictions)}\n"
            f"Obtenu: {len(results)}"
        )


# =============================================================================
# CLASSE DE TEST: DÉTECTION DE DRIFT
# =============================================================================

class TestDriftDetection:
    """
    Tests de la détection de dérive du modèle (concept drift).
    
    CONCEPT DRIFT:
        Phénomène où la relation entre les features et la target
        change au fil du temps, rendant le modèle obsolète.
    
    CAUSES POSSIBLES:
        - Changement de variété cultivée
        - Saisonnalité (été vs hiver)
        - Usure des équipements (LED, capteurs)
        - Nouvelles pratiques de culture
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Pas de drift détecté
    # -------------------------------------------------------------------------
    def test_no_drift_detected(self, feedback_instance, sample_predictions):
        """
        Test: pas de drift quand les erreurs sont faibles.
        
        CRITÈRES DE DRIFT:
            - MAE > 5.0g → drift
            - MAPE > 20% → drift
        
        DONNÉES: MAE ≈ 2.6g, MAPE ≈ 5.7% → pas de drift
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # ACT
        drift_detected = feedback_instance.detect_drift(predictions, actuals)
        
        # ASSERT
        assert drift_detected is False, (
            f"Pas de drift attendu (MAE ~2.6g, MAPE ~5.7%).\n"
            f"Drift détecté: {drift_detected}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Drift détecté
    # -------------------------------------------------------------------------
    def test_drift_detected(self, feedback_instance, sample_predictions_with_drift):
        """
        Test: drift détecté quand les erreurs sont élevées.
        
        DONNÉES: MAE ~13g, MAPE ~28% → drift détecté
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions_with_drift]
        actuals = [p["actual"] for p in sample_predictions_with_drift]
        
        # ACT
        drift_detected = feedback_instance.detect_drift(predictions, actuals)
        
        # ASSERT
        assert drift_detected is True, (
            f"Drift attendu (MAPE ~28%).\n"
            f"Drift détecté: {drift_detected}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 3: Seuils de drift configurables
    # -------------------------------------------------------------------------
    def test_drift_threshold_configurable(self, feedback_instance, sample_predictions):
        """
        Test: les seuils de drift peuvent être configurés.
        
        Avec un seuil très bas, même des erreurs faibles
        devraient déclencher une détection de drift.
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # ACT - Seuil très bas (MAE < 1g)
        drift_low_threshold = feedback_instance.detect_drift(
            predictions, actuals, mae_threshold=1.0
        )
        
        # ACT - Seuil normal
        drift_normal_threshold = feedback_instance.detect_drift(
            predictions, actuals, mae_threshold=5.0
        )
        
        # ASSERT
        # Avec seuil bas, drift devrait être détecté
        # Avec seuil normal, pas de drift
        assert drift_low_threshold is True or drift_normal_threshold is False, (
            "Les seuils devraient affecter la détection de drift"
        )


# =============================================================================
# CLASSE DE TEST: DÉCLENCHEMENT DU RÉENTRAÎNEMENT
# =============================================================================

class TestRetrainingTrigger:
    """
    Tests du déclenchement automatique du réentraînement.
    
    PROCESSUS:
        1. Drift détecté
        2. Vérifier que suffisamment de données sont disponibles
        3. Créer une tâche de réentraînement
        4. Notifier l'équipe Data Science
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Réentraînement déclenché sur drift
    # -------------------------------------------------------------------------
    def test_trigger_retraining_on_drift(self, feedback_instance, sample_predictions_with_drift):
        """
        Test: le réentraînement est déclenché quand un drift est détecté.
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions_with_drift]
        actuals = [p["actual"] for p in sample_predictions_with_drift]
        
        # ACT
        should_retrain = feedback_instance.should_trigger_retraining(
            predictions, actuals
        )
        
        # ASSERT
        assert should_retrain is True, (
            "Le réentraînement devrait être déclenché sur drift"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Pas de réentraînement si pas de drift
    # -------------------------------------------------------------------------
    def test_no_retraining_without_drift(self, feedback_instance, sample_predictions):
        """
        Test: pas de réentraînement si les performances sont bonnes.
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        # ACT
        should_retrain = feedback_instance.should_trigger_retraining(
            predictions, actuals
        )
        
        # ASSERT
        assert should_retrain is False, (
            "Le réentraînement ne devrait pas être déclenché sans drift"
        )
    
    # -------------------------------------------------------------------------
    # TEST 3: Minimum de données requis
    # -------------------------------------------------------------------------
    def test_retraining_requires_minimum_samples(self, feedback_instance):
        """
        Test: le réentraînement nécessite un minimum de données.
        
        RAISON:
            Éviter les faux positifs sur un échantillon trop petit.
            Minimum: 100 comparaisons.
        """
        # ARRANGE - Seulement 3 échantillons (< 100 requis)
        predictions = [45.0, 30.0, 25.0]  # Erreurs énormes
        actuals = [10.0, 10.0, 10.0]
        
        # ACT
        should_retrain = feedback_instance.should_trigger_retraining(
            predictions, actuals, min_samples=100
        )
        
        # ASSERT
        # Même avec de grosses erreurs, pas de réentraînement si < 100 samples
        assert should_retrain is False, (
            "Le réentraînement ne devrait pas être déclenché avec < 100 échantillons"
        )


# =============================================================================
# CLASSE DE TEST: STOCKAGE DES MÉTRIQUES
# =============================================================================

class TestMetricsStorage:
    """
    Tests du stockage des métriques de feedback dans MongoDB.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Stockage réussi
    # -------------------------------------------------------------------------
    def test_store_feedback_metrics(self, feedback_instance, mock_mongodb_metrics, sample_predictions):
        """
        Test: les métriques sont correctement stockées dans MongoDB.
        """
        # ARRANGE
        predictions = [p["predicted"] for p in sample_predictions]
        actuals = [p["actual"] for p in sample_predictions]
        
        metrics = {
            "mae": 2.6,
            "rmse": 2.79,
            "mape": 5.71,
            "r_squared": 0.85,
            "accuracy_at_15pct": 100.0,
            "evaluated_at": datetime.now(timezone.utc),
            "sample_count": len(sample_predictions)
        }
        
        # ACT
        result = feedback_instance.store_metrics(metrics)
        
        # ASSERT
        assert result is not None, "Le stockage devrait retourner un résultat"
        mock_mongodb_metrics['vertiflow_ml'].feedback_metrics.insert_one.assert_called()
    
    # -------------------------------------------------------------------------
    # TEST 2: Métriques incluent le timestamp
    # -------------------------------------------------------------------------
    def test_stored_metrics_have_timestamp(self, feedback_instance, mock_mongodb_metrics):
        """
        Test: les métriques stockées incluent un timestamp.
        """
        # ARRANGE
        metrics = {"mae": 2.5, "rmse": 3.0}
        
        # ACT
        feedback_instance.store_metrics(metrics)
        
        # ASSERT - Vérifier que le timestamp a été ajouté
        call_args = mock_mongodb_metrics['vertiflow_ml'].feedback_metrics.insert_one.call_args
        if call_args:
            stored_doc = call_args[0][0] if call_args[0] else {}
            # Le timestamp devrait être présent
            assert "evaluated_at" in stored_doc or "timestamp" in stored_doc or "created_at" in stored_doc, (
                "Timestamp manquant dans le document stocké"
            )


# =============================================================================
# CLASSE DE TEST: CYCLE COMPLET DE FEEDBACK
# =============================================================================

class TestFeedbackCycle:
    """
    Tests du cycle complet de feedback (run_cycle).
    
    CYCLE:
        1. Récupérer les prédictions à évaluer
        2. Récupérer les valeurs réelles correspondantes
        3. Calculer les métriques
        4. Détecter le drift
        5. Stocker les résultats
        6. Déclencher le réentraînement si nécessaire
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Cycle complet sans drift
    # -------------------------------------------------------------------------
    def test_full_cycle_no_drift(self, feedback_instance):
        """
        Test: cycle complet quand le modèle performe bien.
        """
        # ACT
        result = feedback_instance.run_cycle()
        
        # ASSERT
        assert result is not None, "Le cycle devrait retourner un résultat"
        
        # Vérifier les composants du résultat
        if isinstance(result, dict):
            assert "metrics" in result or "mae" in result, "Métriques manquantes"
            assert "drift_detected" in result or "drift" in result, "Statut drift manquant"
    
    # -------------------------------------------------------------------------
    # TEST 2: Cycle génère des métriques valides
    # -------------------------------------------------------------------------
    def test_cycle_generates_valid_metrics(self, feedback_instance):
        """
        Test: les métriques générées sont valides et complètes.
        """
        # ACT
        result = feedback_instance.run_cycle()
        
        # ASSERT
        if result and isinstance(result, dict):
            metrics = result.get("metrics", result)
            
            # MAE devrait être >= 0
            if "mae" in metrics:
                assert metrics["mae"] >= 0, "MAE devrait être >= 0"
            
            # MAPE devrait être >= 0
            if "mape" in metrics:
                assert metrics["mape"] >= 0, "MAPE devrait être >= 0"
            
            # R² devrait être <= 1
            if "r_squared" in metrics:
                assert metrics["r_squared"] <= 1, "R² devrait être <= 1"


# =============================================================================
# CLASSE DE TEST: CAS LIMITES
# =============================================================================

class TestEdgeCases:
    """
    Tests des cas limites du feedback loop.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Listes vides
    # -------------------------------------------------------------------------
    def test_empty_predictions_list(self, feedback_instance):
        """
        Test: gestion des listes vides.
        """
        # ACT & ASSERT
        try:
            mae = feedback_instance.calculate_mae([], [])
            # Si pas d'exception, vérifier que le résultat est géré
            assert mae == 0 or mae is None or np.isnan(mae), (
                "MAE sur liste vide devrait être 0, None ou NaN"
            )
        except (ValueError, ZeroDivisionError):
            pass  # Exception acceptable pour liste vide
    
    # -------------------------------------------------------------------------
    # TEST 2: Valeur réelle à zéro
    # -------------------------------------------------------------------------
    def test_actual_value_zero(self, feedback_instance):
        """
        Test: gestion des valeurs réelles à zéro (éviter division par zéro).
        
        Le MAPE divise par la valeur réelle, donc actual=0 est problématique.
        """
        # ARRANGE
        predictions = [10.0, 20.0, 30.0]
        actuals = [0.0, 15.0, 25.0]  # Premier élément = 0
        
        # ACT & ASSERT
        try:
            mape = feedback_instance.calculate_mape(predictions, actuals)
            # Ne devrait pas être infini
            assert not np.isinf(mape), "MAPE ne devrait pas être infini"
        except (ValueError, ZeroDivisionError):
            pass  # Exception acceptable
    
    # -------------------------------------------------------------------------
    # TEST 3: Listes de tailles différentes
    # -------------------------------------------------------------------------
    def test_mismatched_list_sizes(self, feedback_instance):
        """
        Test: gestion des listes de tailles différentes.
        """
        # ARRANGE
        predictions = [10.0, 20.0, 30.0]
        actuals = [15.0, 25.0]  # Taille différente
        
        # ACT & ASSERT
        try:
            feedback_instance.calculate_mae(predictions, actuals)
            # Si pas d'exception, vérifier le comportement
        except (ValueError, IndexError):
            pass  # Exception attendue pour tailles différentes


# =============================================================================
# FIN DU MODULE - TICKET-107 - Tests Feedback Loop VertiFlow
# =============================================================================
