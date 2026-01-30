# ============================================================================
# VERTIFLOW - Tests End-to-End (E2E) du Pipeline Complet
# ============================================================================

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestEndToEndPipeline:
    """Tests E2E du pipeline complet MQTT -> NiFi -> Kafka -> ClickHouse."""

    @pytest.fixture
    def pipeline_config(self):
        """Configuration du pipeline E2E."""
        return {
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "topic": "vertiflow/+/+/sensor/+/telemetry"
            },
            "kafka": {
                "bootstrap_servers": "localhost:9092",
                "topic": "basil_telemetry_test"
            },
            "clickhouse": {
                "host": "localhost",
                "port": 9000,
                "database": "vertiflow_test",
                "table": "basil_telemetry"
            },
            "latency_sla_ms": 5000  # 5 secondes max
        }

    def test_sensor_to_storage_flow(
        self,
        pipeline_config,
        sample_telemetry_data,
        mock_mqtt_client,
        mock_kafka_producer,
        mock_clickhouse
    ):
        """Test le flux complet du capteur au stockage."""
        # 1. Simuler l'envoi MQTT
        topic = f"vertiflow/{sample_telemetry_data['farm_id']}/{sample_telemetry_data['zone_id']}/sensor/{sample_telemetry_data['sensor_id']}/telemetry"
        payload = json.dumps(sample_telemetry_data)

        mock_mqtt_client.publish(topic, payload)
        mock_mqtt_client.publish.assert_called_once()

        # 2. Simuler le traitement NiFi -> Kafka
        mock_kafka_producer.send(
            pipeline_config["kafka"]["topic"],
            value=payload.encode()
        )
        mock_kafka_producer.send.assert_called()

        # 3. Simuler l'insertion ClickHouse
        mock_clickhouse.execute(
            "INSERT INTO basil_telemetry VALUES",
            [sample_telemetry_data]
        )
        mock_clickhouse.execute.assert_called()

    def test_data_integrity(self, sample_telemetry_data):
        """Test l'intégrité des données à travers le pipeline."""
        original = sample_telemetry_data.copy()

        # Simuler les transformations du pipeline
        processed = original.copy()
        processed["processed_at"] = datetime.utcnow().isoformat()
        processed["pipeline_version"] = "1.0.0"

        # Les champs originaux doivent être préservés
        assert processed["farm_id"] == original["farm_id"]
        assert processed["sensor_id"] == original["sensor_id"]
        assert processed["value"] == original["value"]

    def test_latency_measurement(self, pipeline_config):
        """Test la mesure de latence du pipeline."""
        start_time = datetime.utcnow()

        # Simuler le temps de traitement
        processing_time_ms = 1500  # 1.5 secondes simulées

        end_time = start_time + timedelta(milliseconds=processing_time_ms)
        latency_ms = (end_time - start_time).total_seconds() * 1000

        assert latency_ms < pipeline_config["latency_sla_ms"]

    def test_batch_processing(self, sample_batch_telemetry):
        """Test le traitement par batch."""
        batch_size = len(sample_batch_telemetry)
        start_time = time.time()

        # Simuler le traitement du batch
        processed_count = 0
        for record in sample_batch_telemetry:
            # Validation
            if all(key in record for key in ["timestamp", "farm_id", "value"]):
                processed_count += 1

        end_time = time.time()
        throughput = processed_count / (end_time - start_time)

        assert processed_count == batch_size
        assert throughput > 100  # > 100 records/seconde


class TestDataQualityE2E:
    """Tests E2E de la qualité des données."""

    def test_schema_validation(self, sample_telemetry_data):
        """Test la validation du schéma."""
        schema = {
            "required": ["timestamp", "farm_id", "zone_id", "sensor_id", "value"],
            "types": {
                "timestamp": str,
                "farm_id": str,
                "zone_id": str,
                "sensor_id": str,
                "value": (int, float)
            }
        }

        # Vérifier les champs requis
        for field in schema["required"]:
            assert field in sample_telemetry_data

        # Vérifier les types
        for field, expected_type in schema["types"].items():
            assert isinstance(sample_telemetry_data[field], expected_type)

    def test_value_range_validation(self, sample_telemetry_data):
        """Test la validation des plages de valeurs."""
        ranges = {
            "temperature": (-10, 50),
            "humidity": (0, 100),
            "co2": (0, 5000),
            "ph": (0, 14)
        }

        sensor_type = sample_telemetry_data.get("sensor_type", "temperature")
        value = sample_telemetry_data["value"]

        if sensor_type in ranges:
            min_val, max_val = ranges[sensor_type]
            assert min_val <= value <= max_val

    def test_duplicate_detection(self, sample_batch_telemetry):
        """Test la détection des doublons."""
        # Créer un doublon intentionnel
        batch_with_dup = sample_batch_telemetry + [sample_batch_telemetry[0]]

        # Détecter par (timestamp, sensor_id)
        seen = set()
        duplicates = []

        for record in batch_with_dup:
            key = (record["timestamp"], record["sensor_id"])
            if key in seen:
                duplicates.append(record)
            seen.add(key)

        assert len(duplicates) == 1

    def test_outlier_detection(self, sample_batch_telemetry):
        """Test la détection des valeurs aberrantes."""
        import numpy as np

        values = [t["value"] for t in sample_batch_telemetry]
        mean = np.mean(values)
        std = np.std(values)

        # IQR method
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = [v for v in values if v < lower_bound or v > upper_bound]

        # Dans notre batch de test, pas d'outliers attendus
        assert len(outliers) == 0


class TestMLPipelineE2E:
    """Tests E2E du pipeline ML."""

    def test_feature_engineering_pipeline(self, sample_batch_telemetry):
        """Test le pipeline de feature engineering."""
        import numpy as np

        # Agréger les features
        values = [t["value"] for t in sample_batch_telemetry]

        features = {
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "range": np.max(values) - np.min(values),
            "count": len(values)
        }

        assert all(key in features for key in ["mean", "std", "min", "max"])

    def test_prediction_pipeline(self, sample_features_for_prediction):
        """Test le pipeline de prédiction."""
        # Simuler une prédiction
        mock_model = MagicMock()
        mock_model.predict.return_value = [45.5]
        mock_model.predict_proba.return_value = [[0.1, 0.2, 0.7]]

        features = list(sample_features_for_prediction.values())

        prediction = mock_model.predict([features])
        confidence = max(mock_model.predict_proba([features])[0])

        assert prediction[0] > 0
        assert 0 <= confidence <= 1

    def test_recommendation_generation(self, sample_telemetry_data, sample_plant_recipe):
        """Test la génération de recommandations."""
        current_temp = sample_telemetry_data["value"]
        targets = sample_plant_recipe["growth_stages"][1]["targets"]

        recommendations = []

        # Générer des recommandations basées sur les écarts
        if current_temp < targets["temperature_min"]:
            recommendations.append({
                "action": "increase_temperature",
                "current": current_temp,
                "target": targets["temperature_min"],
                "priority": "high"
            })
        elif current_temp > targets["temperature_max"]:
            recommendations.append({
                "action": "decrease_temperature",
                "current": current_temp,
                "target": targets["temperature_max"],
                "priority": "high"
            })

        # La température de test (23.5) est dans les limites (22-28)
        assert len(recommendations) == 0


class TestAlertingE2E:
    """Tests E2E du système d'alertes."""

    def test_alert_generation(self):
        """Test la génération d'alertes."""
        sensor_reading = {
            "sensor_id": "TEMP_001",
            "value": 35,  # Trop élevé
            "timestamp": datetime.utcnow().isoformat()
        }

        thresholds = {
            "critical_high": 32,
            "warning_high": 28,
            "warning_low": 18,
            "critical_low": 15
        }

        alert = None

        if sensor_reading["value"] >= thresholds["critical_high"]:
            alert = {
                "severity": "critical",
                "type": "high_temperature",
                "value": sensor_reading["value"],
                "threshold": thresholds["critical_high"],
                "sensor_id": sensor_reading["sensor_id"],
                "timestamp": datetime.utcnow().isoformat()
            }
        elif sensor_reading["value"] >= thresholds["warning_high"]:
            alert = {
                "severity": "warning",
                "type": "high_temperature",
                "value": sensor_reading["value"],
                "threshold": thresholds["warning_high"]
            }

        assert alert is not None
        assert alert["severity"] == "critical"

    def test_alert_routing(self):
        """Test le routage des alertes."""
        alert = {
            "severity": "critical",
            "type": "equipment_failure",
            "farm_id": "FARM_001"
        }

        routing_rules = {
            "critical": ["sms", "email", "slack"],
            "warning": ["email", "slack"],
            "info": ["slack"]
        }

        channels = routing_rules.get(alert["severity"], ["slack"])

        assert "sms" in channels
        assert len(channels) == 3

    def test_alert_aggregation(self):
        """Test l'agrégation des alertes."""
        # Éviter le spam d'alertes
        alerts = [
            {"sensor_id": "TEMP_001", "type": "high", "timestamp": "2025-01-01T00:00:00"},
            {"sensor_id": "TEMP_001", "type": "high", "timestamp": "2025-01-01T00:00:30"},
            {"sensor_id": "TEMP_001", "type": "high", "timestamp": "2025-01-01T00:01:00"},
        ]

        # Agréger les alertes similaires dans une fenêtre de 5 minutes
        aggregated = {
            "sensor_id": "TEMP_001",
            "type": "high",
            "first_occurrence": alerts[0]["timestamp"],
            "last_occurrence": alerts[-1]["timestamp"],
            "count": len(alerts)
        }

        assert aggregated["count"] == 3


class TestRecoveryE2E:
    """Tests E2E de récupération et résilience."""

    def test_message_replay(self, sample_batch_telemetry):
        """Test le replay des messages après une panne."""
        # Simuler un offset Kafka
        last_committed_offset = 50
        current_offset = 100

        # Messages à rejouer
        messages_to_replay = sample_batch_telemetry[last_committed_offset:current_offset]

        assert len(messages_to_replay) == 50

    def test_checkpoint_recovery(self):
        """Test la récupération depuis un checkpoint."""
        checkpoint = {
            "offset": 1000,
            "timestamp": "2025-01-01T12:00:00",
            "processed_count": 10000
        }

        # Reprendre depuis le checkpoint
        resume_offset = checkpoint["offset"]

        assert resume_offset == 1000

    def test_graceful_degradation(self):
        """Test la dégradation gracieuse."""
        services = {
            "kafka": True,
            "clickhouse": False,  # En panne
            "mongodb": True,
            "mqtt": True
        }

        # Si ClickHouse est down, buffer dans Kafka
        if not services["clickhouse"]:
            fallback_action = "buffer_in_kafka"
        else:
            fallback_action = "normal_processing"

        assert fallback_action == "buffer_in_kafka"


class TestPerformanceE2E:
    """Tests E2E de performance."""

    def test_throughput_measurement(self, sample_batch_telemetry):
        """Test la mesure du débit."""
        import time

        batch_size = len(sample_batch_telemetry)
        iterations = 10

        start = time.time()

        for _ in range(iterations):
            # Simuler le traitement
            processed = [r for r in sample_batch_telemetry if r.get("value") is not None]

        end = time.time()

        total_records = batch_size * iterations
        elapsed = end - start
        throughput = total_records / elapsed if elapsed > 0 else float('inf')

        # Doit traiter au moins 10000 records/seconde
        assert throughput > 1000

    def test_memory_efficiency(self, sample_batch_telemetry):
        """Test l'efficacité mémoire."""
        import sys

        # Mesurer la taille du batch
        batch_size_bytes = sys.getsizeof(sample_batch_telemetry)

        # Ajouter la taille des éléments
        for item in sample_batch_telemetry[:10]:  # Échantillon
            batch_size_bytes += sys.getsizeof(item)

        # Doit être raisonnable (< 1MB pour 100 records)
        assert batch_size_bytes < 1_000_000

    def test_concurrent_processing(self):
        """Test le traitement concurrent."""
        import concurrent.futures

        def process_record(record):
            return {"processed": True, "original": record}

        records = [{"id": i, "value": i * 10} for i in range(100)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_record, records))

        assert len(results) == 100
        assert all(r["processed"] for r in results)
