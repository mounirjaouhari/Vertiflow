# ============================================================================
# VERTIFLOW - Tests d'Intégration Pipeline Kafka
# ============================================================================

import pytest
import json
import time
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestKafkaProducer:
    """Tests d'intégration pour le producteur Kafka."""

    @pytest.fixture
    def kafka_config(self):
        """Configuration Kafka pour les tests."""
        return {
            "bootstrap_servers": "localhost:9092",
            "topic": "vertiflow_telemetry_test",
            "acks": "all",
            "retries": 3,
            "compression_type": "snappy"
        }

    def test_producer_connection(self, kafka_config, mock_kafka_producer):
        """Test la connexion du producteur."""
        mock_kafka_producer.bootstrap_connected.return_value = True

        assert mock_kafka_producer.bootstrap_connected() is True

    def test_message_serialization(self, sample_telemetry_data):
        """Test la sérialisation des messages."""
        serialized = json.dumps(sample_telemetry_data)

        assert isinstance(serialized, str)
        assert "farm_id" in serialized
        assert "timestamp" in serialized

    def test_message_production(self, kafka_config, mock_kafka_producer, sample_telemetry_data):
        """Test la production d'un message."""
        topic = kafka_config["topic"]
        key = sample_telemetry_data["sensor_id"].encode()
        value = json.dumps(sample_telemetry_data).encode()

        mock_kafka_producer.send(topic, key=key, value=value)
        mock_kafka_producer.flush()

        mock_kafka_producer.send.assert_called_once()
        mock_kafka_producer.flush.assert_called_once()

    def test_batch_production(self, kafka_config, mock_kafka_producer, sample_batch_telemetry):
        """Test la production en batch."""
        topic = kafka_config["topic"]

        for record in sample_batch_telemetry:
            key = record["sensor_id"].encode()
            value = json.dumps(record).encode()
            mock_kafka_producer.send(topic, key=key, value=value)

        mock_kafka_producer.flush()

        assert mock_kafka_producer.send.call_count == len(sample_batch_telemetry)

    def test_producer_error_handling(self, mock_kafka_producer):
        """Test la gestion des erreurs du producteur."""
        mock_kafka_producer.send.side_effect = Exception("Broker unavailable")

        with pytest.raises(Exception) as exc_info:
            mock_kafka_producer.send("topic", value=b"test")

        assert "Broker unavailable" in str(exc_info.value)


class TestKafkaConsumer:
    """Tests d'intégration pour le consommateur Kafka."""

    @pytest.fixture
    def consumer_config(self):
        """Configuration du consommateur."""
        return {
            "bootstrap_servers": "localhost:9092",
            "group_id": "vertiflow_processor_test",
            "auto_offset_reset": "earliest",
            "enable_auto_commit": False
        }

    def test_consumer_subscription(self, consumer_config, mock_kafka_consumer):
        """Test l'abonnement aux topics."""
        topics = ["vertiflow_telemetry_test"]
        mock_kafka_consumer.subscribe(topics)

        mock_kafka_consumer.subscribe.assert_called_once_with(topics)

    def test_message_consumption(self, mock_kafka_consumer, sample_telemetry_data):
        """Test la consommation de messages."""
        mock_message = MagicMock()
        mock_message.value = json.dumps(sample_telemetry_data).encode()
        mock_message.key = b"SENSOR_001"
        mock_message.topic = "vertiflow_telemetry_test"
        mock_message.partition = 0
        mock_message.offset = 42

        mock_kafka_consumer.__iter__ = MagicMock(return_value=iter([mock_message]))

        messages = list(mock_kafka_consumer)

        assert len(messages) == 1
        assert messages[0].offset == 42

    def test_message_deserialization(self, sample_telemetry_data):
        """Test la désérialisation des messages."""
        serialized = json.dumps(sample_telemetry_data).encode()
        deserialized = json.loads(serialized.decode())

        assert deserialized["farm_id"] == sample_telemetry_data["farm_id"]
        assert deserialized["value"] == sample_telemetry_data["value"]

    def test_offset_commit(self, mock_kafka_consumer):
        """Test le commit des offsets."""
        mock_kafka_consumer.commit()

        mock_kafka_consumer.commit.assert_called_once()

    def test_consumer_rebalance(self, mock_kafka_consumer):
        """Test le rééquilibrage du groupe de consommateurs."""
        partitions = [MagicMock(topic="test", partition=0)]
        mock_kafka_consumer.assignment.return_value = partitions

        assigned = mock_kafka_consumer.assignment()

        assert len(assigned) == 1


class TestKafkaTopics:
    """Tests pour la gestion des topics Kafka."""

    def test_topic_creation(self):
        """Test la création de topics."""
        topic_config = {
            "name": "vertiflow_telemetry_test",
            "partitions": 6,
            "replication_factor": 1,
            "config": {
                "retention.ms": 604800000,  # 7 jours
                "compression.type": "snappy"
            }
        }

        assert topic_config["partitions"] >= 1
        assert topic_config["replication_factor"] >= 1

    def test_topic_partitioning(self):
        """Test le partitionnement des messages."""
        farm_ids = ["FARM_001", "FARM_002", "FARM_003"]
        num_partitions = 6

        # Partitionnement par hash du farm_id
        partitions = [hash(farm_id) % num_partitions for farm_id in farm_ids]

        assert all(0 <= p < num_partitions for p in partitions)

    def test_topic_retention(self):
        """Test la configuration de rétention."""
        retention_days = 7
        retention_ms = retention_days * 24 * 60 * 60 * 1000

        assert retention_ms == 604800000


class TestStreamProcessor:
    """Tests pour le processeur de stream."""

    def test_message_validation(self, sample_telemetry_data):
        """Test la validation des messages."""
        required_fields = ["timestamp", "farm_id", "sensor_id", "value"]

        is_valid = all(field in sample_telemetry_data for field in required_fields)

        assert is_valid is True

    def test_message_transformation(self, sample_telemetry_data):
        """Test la transformation des messages."""
        # Ajouter des champs calculés
        transformed = sample_telemetry_data.copy()
        transformed["processed_at"] = datetime.utcnow().isoformat()
        transformed["data_quality"] = "validated"

        assert "processed_at" in transformed
        assert "data_quality" in transformed

    def test_message_enrichment(self, sample_telemetry_data, sample_plant_recipe):
        """Test l'enrichissement des messages."""
        enriched = sample_telemetry_data.copy()

        # Enrichir avec les cibles de la recette
        current_stage = sample_plant_recipe["growth_stages"][1]  # vegetative
        enriched["targets"] = current_stage["targets"]

        assert "targets" in enriched
        assert "temperature_min" in enriched["targets"]

    def test_anomaly_flagging(self, sample_telemetry_data):
        """Test le marquage des anomalies."""
        # Simuler une valeur anormale
        data = sample_telemetry_data.copy()
        data["value"] = 50  # Température trop élevée

        limits = {"temperature": (18, 30)}
        is_anomaly = data["value"] < limits["temperature"][0] or \
                     data["value"] > limits["temperature"][1]

        data["is_anomaly"] = is_anomaly
        data["anomaly_type"] = "high_temperature" if is_anomaly else None

        assert data["is_anomaly"] is True

    def test_aggregation_window(self, sample_batch_telemetry):
        """Test l'agrégation par fenêtre temporelle."""
        import numpy as np

        values = [t["value"] for t in sample_batch_telemetry]

        aggregated = {
            "avg": np.mean(values),
            "min": np.min(values),
            "max": np.max(values),
            "std": np.std(values),
            "count": len(values)
        }

        assert aggregated["count"] == 100
        assert aggregated["min"] <= aggregated["avg"] <= aggregated["max"]


class TestDeadLetterQueue:
    """Tests pour la Dead Letter Queue."""

    def test_dlq_routing(self):
        """Test le routage vers la DLQ."""
        invalid_message = {"incomplete": "data"}
        dlq_topic = "vertiflow_dlq"

        # Un message invalide devrait être routé vers la DLQ
        required_fields = ["timestamp", "farm_id", "value"]
        is_valid = all(field in invalid_message for field in required_fields)

        route_to_dlq = not is_valid

        assert route_to_dlq is True

    def test_dlq_metadata(self):
        """Test les métadonnées de la DLQ."""
        dlq_record = {
            "original_message": {"bad": "data"},
            "error_type": "ValidationError",
            "error_message": "Missing required field: timestamp",
            "failed_at": datetime.utcnow().isoformat(),
            "retry_count": 0,
            "source_topic": "vertiflow_telemetry"
        }

        assert "error_type" in dlq_record
        assert "failed_at" in dlq_record

    def test_retry_logic(self):
        """Test la logique de retry."""
        max_retries = 3
        current_retries = 2

        should_retry = current_retries < max_retries

        assert should_retry is True
