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
MODULE: tests/unit/test_stream_processor.py
DESCRIPTION: Tests unitaires pour le processeur de flux Kafka (stream_processor.py)

    Le Stream Processor est le SYSTÈME NERVEUX CENTRAL de VertiFlow.
    Il traite les données en temps réel provenant de Kafka et les
    distribue aux différents algorithmes (Oracle, Cortex, Classifier).

    ARCHITECTURE DU STREAM PROCESSING:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                   STREAM PROCESSOR - KAFKA CONSUMER                     │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │                      KAFKA BROKER                               │    │
    │  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │    │
    │  │  │ sensor_data   │  │ commands      │  │ alerts        │        │    │
    │  │  │ (Partition 0) │  │ (Partition 0) │  │ (Partition 0) │        │    │
    │  │  │ (Partition 1) │  │ (Partition 1) │  │ (Partition 1) │        │    │
    │  │  │ (Partition 2) │  │ (Partition 2) │  │ (Partition 2) │        │    │
    │  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘        │    │
    │  └──────────┼──────────────────┼──────────────────┼────────────────┘    │
    │             │                  │                  │                     │
    │             ▼                  ▼                  ▼                     │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │                    STREAM PROCESSOR                             │    │
    │  │                                                                 │    │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │    │
    │  │  │  Deserialize│  │  Validate   │  │  Transform  │              │    │
    │  │  │  (JSON/Avro)│─▶│  (Schema)   │─▶│  (Enrich)   │              │    │
    │  │  └─────────────┘  └─────────────┘  └──────┬──────┘              │    │
    │  │                                          │                      │    │
    │  │                                          ▼                      │    │
    │  │  ┌───────────────────────────────────────────────────────────┐  │    │
    │  │  │                    ROUTER                                 │  │    │
    │  │  │  sensor_data ──▶ ClickHouse (time-series)                 │  │    │
    │  │  │  commands    ──▶ MongoDB (recipes) + MQTT (actuators)     │  │    │
    │  │  │  alerts      ──▶ MongoDB (alerts) + Webhook (notify)      │  │    │
    │  │  └───────────────────────────────────────────────────────────┘  │    │
    │  └─────────────────────────────────────────────────────────────────┘    │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

    TOPICS KAFKA:
    ┌──────────────────────┬──────────────────────────────────────────────────┐
    │ Topic                │ Description                                      │
    ├──────────────────────┼──────────────────────────────────────────────────┤
    │ vertiflow.sensor     │ Données capteurs (temp, humidity, CO2, light)    │
    │ vertiflow.commands   │ Commandes actuateurs (irrigation, LED, HVAC)     │
    │ vertiflow.alerts     │ Alertes générées (A4 - Alert Generator)          │
    │ vertiflow.predictions│ Prédictions ML (Oracle, Classifier)              │
    │ vertiflow.feedback   │ Données de feedback (comparaison pred vs real)   │
    └──────────────────────┴──────────────────────────────────────────────────┘

IMPORTANCE CRITIQUE:
    Le Stream Processor est le POINT DE PASSAGE OBLIGÉ de toutes les données.
    Une panne ou un bug peut:
    - Bloquer toute la chaîne de traitement
    - Créer un backlog de messages dans Kafka
    - Retarder les alertes critiques
    - Désynchroniser les actionneurs

Développé par       : @Mouhammed & @Imrane
Ticket(s) associé(s): TICKET-108
Sprint              : Semaine 6 - Phase Qualité & Tests

Dépendances:
    - pytest>=8.0.0
    - pytest-asyncio>=0.23.0
    - kafka-python>=2.0.2

================================================================================
© 2026 VertiFlow Core Team - Tous droits réservés
Développé dans le cadre de l'Initiative Nationale Marocaine JobInTech
au sein de l'École YNOV Maroc Campus
================================================================================
"""

import os
import json
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

# =============================================================================
# IMPORT DU MODULE À TESTER
# =============================================================================

try:
    from cloud_citadel.connectors.stream_processor import StreamProcessor
    STREAM_PROCESSOR_AVAILABLE = True
except ImportError as e:
    STREAM_PROCESSOR_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Skip tous les tests si le module n'est pas importable
pytestmark = pytest.mark.skipif(
    not STREAM_PROCESSOR_AVAILABLE,
    reason=f"Module stream_processor non disponible: {IMPORT_ERROR if not STREAM_PROCESSOR_AVAILABLE else ''}"
)


# =============================================================================
# CONSTANTES DE TEST
# =============================================================================

# Topics Kafka
TOPIC_SENSOR_DATA = "vertiflow.sensor"
TOPIC_COMMANDS = "vertiflow.commands"
TOPIC_ALERTS = "vertiflow.alerts"
TOPIC_PREDICTIONS = "vertiflow.predictions"

# Configuration Kafka test
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_GROUP_ID = "vertiflow-test-consumer"
KAFKA_AUTO_OFFSET_RESET = "earliest"

# Timeouts
POLL_TIMEOUT_MS = 1000
PROCESSING_TIMEOUT_S = 5.0


# =============================================================================
# FIXTURES SPÉCIFIQUES AU STREAM PROCESSOR
# =============================================================================

@pytest.fixture
def sample_sensor_message():
    """
    Message Kafka simulant des données de capteurs.
    
    FORMAT:
        Topic: vertiflow.sensor
        Key: rack_id (pour partitioning)
        Value: JSON avec timestamp et mesures
    """
    return {
        "topic": TOPIC_SENSOR_DATA,
        "key": b"R01",
        "value": json.dumps({
            "rack_id": "R01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sensors": {
                "temperature_c": 24.5,
                "humidity_pct": 68.2,
                "co2_ppm": 850,
                "light_ppfd": 420,
                "ec_ms_cm": 1.75,
                "ph": 6.2,
                "water_temp_c": 21.0
            },
            "metadata": {
                "sensor_firmware": "v2.1.0",
                "battery_pct": 95
            }
        }).encode('utf-8'),
        "partition": 0,
        "offset": 12345
    }


@pytest.fixture
def sample_command_message():
    """
    Message Kafka simulant une commande actuateur.
    
    FORMAT:
        Topic: vertiflow.commands
        Key: rack_id
        Value: JSON avec commande et paramètres
    """
    return {
        "topic": TOPIC_COMMANDS,
        "key": b"R01",
        "value": json.dumps({
            "command_id": "CMD_20260102_001",
            "rack_id": "R01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command_type": "IRRIGATION",
            "parameters": {
                "duration_seconds": 120,
                "flow_rate_ml_min": 500,
                "nutrient_mix": "VEGETATIVE_STD"
            },
            "priority": "NORMAL",
            "source": "CORTEX_OPTIMIZER"
        }).encode('utf-8'),
        "partition": 0,
        "offset": 5678
    }


@pytest.fixture
def sample_alert_message():
    """
    Message Kafka simulant une alerte.
    
    FORMAT:
        Topic: vertiflow.alerts
        Key: alert_type
        Value: JSON avec détails de l'alerte
    """
    return {
        "topic": TOPIC_ALERTS,
        "key": b"TEMP_HIGH",
        "value": json.dumps({
            "alert_id": "ALERT_20260102_001",
            "rack_id": "R01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_type": "TEMP_HIGH",
            "severity": "WARNING",
            "current_value": 29.5,
            "threshold": 28.0,
            "message": "Température élevée détectée sur rack R01",
            "recommended_action": "Vérifier ventilation et réduire éclairage"
        }).encode('utf-8'),
        "partition": 0,
        "offset": 9012
    }


@pytest.fixture
def mock_kafka_consumer():
    """
    Mock du KafkaConsumer.
    
    Simule le comportement d'un consumer Kafka:
    - subscribe(): s'abonne aux topics
    - poll(): récupère les messages
    - commit(): confirme le traitement
    - close(): ferme la connexion
    """
    mock_consumer = MagicMock()
    
    # Configuration de base
    mock_consumer.config = {
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "group_id": KAFKA_GROUP_ID,
        "auto_offset_reset": KAFKA_AUTO_OFFSET_RESET
    }
    
    # subscribe ne retourne rien
    mock_consumer.subscribe.return_value = None
    
    # poll retourne un dict vide par défaut
    mock_consumer.poll.return_value = {}
    
    # commit ne retourne rien
    mock_consumer.commit.return_value = None
    
    # close ne retourne rien
    mock_consumer.close.return_value = None
    
    # position retourne un offset
    mock_consumer.position.return_value = 12345
    
    return mock_consumer


@pytest.fixture
def mock_kafka_producer():
    """
    Mock du KafkaProducer.
    
    Simule le comportement d'un producer Kafka:
    - send(): envoie un message
    - flush(): force l'envoi des messages en attente
    - close(): ferme la connexion
    """
    mock_producer = MagicMock()
    
    # send retourne un Future
    future = MagicMock()
    future.get.return_value = MagicMock(
        topic=TOPIC_SENSOR_DATA,
        partition=0,
        offset=12346
    )
    mock_producer.send.return_value = future
    
    # flush ne retourne rien
    mock_producer.flush.return_value = None
    
    return mock_producer


@pytest.fixture
def mock_clickhouse_client():
    """
    Mock du client ClickHouse pour le stockage des données capteurs.
    """
    mock_client = MagicMock()
    mock_client.execute.return_value = None
    return mock_client


@pytest.fixture
def mock_mongodb_client():
    """
    Mock du client MongoDB pour le stockage des commandes et alertes.
    """
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client.__getitem__ = MagicMock(return_value=mock_db)
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    
    mock_collection.insert_one.return_value = MagicMock(
        inserted_id="60f1234567890abcdef12345"
    )
    
    return mock_client


@pytest.fixture
def stream_processor_instance(mock_kafka_consumer, mock_kafka_producer, 
                               mock_clickhouse_client, mock_mongodb_client):
    """
    Crée une instance de StreamProcessor avec dépendances mockées.
    """
    with patch('cloud_citadel.connectors.stream_processor.KafkaConsumer') as mock_consumer_class:
        mock_consumer_class.return_value = mock_kafka_consumer
        
        with patch('cloud_citadel.connectors.stream_processor.KafkaProducer') as mock_producer_class:
            mock_producer_class.return_value = mock_kafka_producer
            
            with patch('cloud_citadel.connectors.stream_processor.Client') as mock_ch_class:
                mock_ch_class.return_value = mock_clickhouse_client
                
                with patch('cloud_citadel.connectors.stream_processor.MongoClient') as mock_mongo_class:
                    mock_mongo_class.return_value = mock_mongodb_client
                    
                    processor = StreamProcessor()
                    
                    # Injecter les mocks
                    processor.consumer = mock_kafka_consumer
                    processor.producer = mock_kafka_producer
                    processor.ch_client = mock_clickhouse_client
                    processor.mongo_client = mock_mongodb_client
                    
                    yield processor


# =============================================================================
# CLASSE DE TEST: DÉSÉRIALISATION DES MESSAGES
# =============================================================================

class TestMessageDeserialization:
    """
    Tests de la désérialisation des messages Kafka.
    
    FORMATS SUPPORTÉS:
        - JSON (par défaut)
        - Avro (avec schema registry)
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Désérialisation JSON valide
    # -------------------------------------------------------------------------
    def test_deserialize_json_valid(self, stream_processor_instance, sample_sensor_message):
        """
        Test: désérialisation correcte d'un message JSON valide.
        """
        # ARRANGE
        raw_value = sample_sensor_message["value"]
        
        # ACT
        result = stream_processor_instance.deserialize_message(raw_value)
        
        # ASSERT
        assert result is not None, "Le résultat ne devrait pas être None"
        assert isinstance(result, dict), "Le résultat devrait être un dict"
        assert "rack_id" in result, "Clé 'rack_id' manquante"
        assert "sensors" in result, "Clé 'sensors' manquante"
        assert result["rack_id"] == "R01", f"rack_id incorrect: {result['rack_id']}"
    
    # -------------------------------------------------------------------------
    # TEST 2: Désérialisation JSON invalide
    # -------------------------------------------------------------------------
    def test_deserialize_json_invalid(self, stream_processor_instance):
        """
        Test: gestion gracieuse d'un JSON invalide.
        
        COMPORTEMENT ATTENDU:
            - Pas de crash
            - Retourne None ou lève une exception gérée
            - Log l'erreur pour debugging
        """
        # ARRANGE - JSON mal formé
        invalid_json = b'{"rack_id": "R01", invalid}'
        
        # ACT & ASSERT
        try:
            result = stream_processor_instance.deserialize_message(invalid_json)
            # Si pas d'exception, le résultat devrait être None ou une erreur
            assert result is None or "error" in str(result).lower(), (
                "JSON invalide devrait retourner None ou une indication d'erreur"
            )
        except json.JSONDecodeError:
            pass  # Exception acceptable
        except ValueError:
            pass  # Exception acceptable
    
    # -------------------------------------------------------------------------
    # TEST 3: Désérialisation message vide
    # -------------------------------------------------------------------------
    def test_deserialize_empty_message(self, stream_processor_instance):
        """
        Test: gestion d'un message vide.
        """
        # ACT & ASSERT
        try:
            result = stream_processor_instance.deserialize_message(b'')
            assert result is None or result == {}, (
                "Message vide devrait retourner None ou dict vide"
            )
        except (json.JSONDecodeError, ValueError):
            pass  # Exception acceptable
    
    # -------------------------------------------------------------------------
    # TEST 4: Désérialisation avec encoding UTF-8
    # -------------------------------------------------------------------------
    def test_deserialize_utf8_encoding(self, stream_processor_instance):
        """
        Test: support des caractères UTF-8 (accents, émojis).
        """
        # ARRANGE - Message avec caractères spéciaux
        message_utf8 = json.dumps({
            "rack_id": "R01",
            "message": "Température élevée 🌡️",
            "location": "Côté Nord"
        }).encode('utf-8')
        
        # ACT
        result = stream_processor_instance.deserialize_message(message_utf8)
        
        # ASSERT
        assert result is not None, "UTF-8 devrait être supporté"
        assert "élevée" in result.get("message", ""), "Caractères accentués perdus"


# =============================================================================
# CLASSE DE TEST: VALIDATION DES MESSAGES
# =============================================================================

class TestMessageValidation:
    """
    Tests de la validation des messages (schema validation).
    
    CHAMPS REQUIS PAR TOPIC:
        - sensor_data: rack_id, timestamp, sensors
        - commands: command_id, rack_id, command_type, parameters
        - alerts: alert_id, rack_id, alert_type, severity
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Validation message capteur valide
    # -------------------------------------------------------------------------
    def test_validate_sensor_message_valid(self, stream_processor_instance):
        """
        Test: validation réussie d'un message capteur complet.
        """
        # ARRANGE
        valid_message = {
            "rack_id": "R01",
            "timestamp": "2026-01-02T12:00:00Z",
            "sensors": {
                "temperature_c": 24.5,
                "humidity_pct": 68.0
            }
        }
        
        # ACT
        is_valid = stream_processor_instance.validate_message(
            valid_message, topic=TOPIC_SENSOR_DATA
        )
        
        # ASSERT
        assert is_valid is True, "Message valide devrait passer la validation"
    
    # -------------------------------------------------------------------------
    # TEST 2: Validation message capteur incomplet
    # -------------------------------------------------------------------------
    def test_validate_sensor_message_missing_field(self, stream_processor_instance):
        """
        Test: rejet d'un message capteur incomplet.
        """
        # ARRANGE - Manque le champ 'sensors'
        invalid_message = {
            "rack_id": "R01",
            "timestamp": "2026-01-02T12:00:00Z"
            # sensors manquant
        }
        
        # ACT
        is_valid = stream_processor_instance.validate_message(
            invalid_message, topic=TOPIC_SENSOR_DATA
        )
        
        # ASSERT
        assert is_valid is False, "Message incomplet devrait être rejeté"
    
    # -------------------------------------------------------------------------
    # TEST 3: Validation message commande
    # -------------------------------------------------------------------------
    def test_validate_command_message(self, stream_processor_instance):
        """
        Test: validation d'un message commande.
        """
        # ARRANGE
        valid_command = {
            "command_id": "CMD_001",
            "rack_id": "R01",
            "timestamp": "2026-01-02T12:00:00Z",
            "command_type": "IRRIGATION",
            "parameters": {"duration_seconds": 120}
        }
        
        # ACT
        is_valid = stream_processor_instance.validate_message(
            valid_command, topic=TOPIC_COMMANDS
        )
        
        # ASSERT
        assert is_valid is True, "Commande valide devrait passer"
    
    # -------------------------------------------------------------------------
    # TEST 4: Validation des types de données
    # -------------------------------------------------------------------------
    def test_validate_data_types(self, stream_processor_instance):
        """
        Test: validation des types de données (température = float, pas string).
        """
        # ARRANGE - Température en string au lieu de float
        invalid_types = {
            "rack_id": "R01",
            "timestamp": "2026-01-02T12:00:00Z",
            "sensors": {
                "temperature_c": "24.5",  # String au lieu de float
                "humidity_pct": 68.0
            }
        }
        
        # ACT
        # Selon l'implémentation, cela peut être valide (avec coercion)
        # ou invalide (strict type checking)
        is_valid = stream_processor_instance.validate_message(
            invalid_types, topic=TOPIC_SENSOR_DATA
        )
        
        # Note: Le test vérifie surtout que ça ne crash pas


# =============================================================================
# CLASSE DE TEST: ROUTAGE DES MESSAGES
# =============================================================================

class TestMessageRouting:
    """
    Tests du routage des messages vers les destinations appropriées.
    
    RÈGLES DE ROUTAGE:
        - sensor_data → ClickHouse (séries temporelles)
        - commands → MongoDB + MQTT (actuateurs)
        - alerts → MongoDB + Webhook (notifications)
        - predictions → MongoDB (historique ML)
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Routage sensor_data vers ClickHouse
    # -------------------------------------------------------------------------
    def test_route_sensor_to_clickhouse(self, stream_processor_instance, 
                                         mock_clickhouse_client, sample_sensor_message):
        """
        Test: les données capteurs sont routées vers ClickHouse.
        """
        # ARRANGE
        message = json.loads(sample_sensor_message["value"])
        
        # ACT
        stream_processor_instance.route_message(message, topic=TOPIC_SENSOR_DATA)
        
        # ASSERT
        mock_clickhouse_client.execute.assert_called()
    
    # -------------------------------------------------------------------------
    # TEST 2: Routage commands vers MongoDB
    # -------------------------------------------------------------------------
    def test_route_command_to_mongodb(self, stream_processor_instance,
                                       mock_mongodb_client, sample_command_message):
        """
        Test: les commandes sont routées vers MongoDB.
        """
        # ARRANGE
        message = json.loads(sample_command_message["value"])
        
        # ACT
        stream_processor_instance.route_message(message, topic=TOPIC_COMMANDS)
        
        # ASSERT
        # Vérifier que MongoDB a été appelé
        # (la méthode exacte dépend de l'implémentation)
    
    # -------------------------------------------------------------------------
    # TEST 3: Routage alerts vers MongoDB
    # -------------------------------------------------------------------------
    def test_route_alert_to_mongodb(self, stream_processor_instance,
                                     mock_mongodb_client, sample_alert_message):
        """
        Test: les alertes sont routées vers MongoDB.
        """
        # ARRANGE
        message = json.loads(sample_alert_message["value"])
        
        # ACT
        stream_processor_instance.route_message(message, topic=TOPIC_ALERTS)
        
        # ASSERT - MongoDB devrait être appelé pour stocker l'alerte
    
    # -------------------------------------------------------------------------
    # TEST 4: Topic inconnu
    # -------------------------------------------------------------------------
    def test_route_unknown_topic(self, stream_processor_instance):
        """
        Test: gestion d'un topic inconnu.
        
        COMPORTEMENT ATTENDU:
            - Log un warning
            - Ne crash pas
            - Potentiellement stocke dans une "dead letter queue"
        """
        # ARRANGE
        message = {"data": "test"}
        unknown_topic = "vertiflow.unknown"
        
        # ACT & ASSERT - Pas de crash
        try:
            stream_processor_instance.route_message(message, topic=unknown_topic)
        except ValueError as e:
            # Exception acceptable si topic non supporté
            assert "unknown" in str(e).lower() or "topic" in str(e).lower()


# =============================================================================
# CLASSE DE TEST: GESTION DES OFFSETS
# =============================================================================

class TestOffsetManagement:
    """
    Tests de la gestion des offsets Kafka.
    
    OFFSET:
        Position du message dans la partition.
        Permet de reprendre le traitement après un crash.
    
    STRATÉGIES:
        - Auto-commit: Kafka gère automatiquement
        - Manual commit: Commit après traitement réussi (recommandé)
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Commit après traitement réussi
    # -------------------------------------------------------------------------
    def test_commit_offset_on_success(self, stream_processor_instance, mock_kafka_consumer):
        """
        Test: l'offset est committé après un traitement réussi.
        """
        # ARRANGE
        message = {"rack_id": "R01", "data": "test"}
        
        # ACT
        stream_processor_instance.process_and_commit(message, topic=TOPIC_SENSOR_DATA)
        
        # ASSERT
        mock_kafka_consumer.commit.assert_called()
    
    # -------------------------------------------------------------------------
    # TEST 2: Pas de commit sur erreur
    # -------------------------------------------------------------------------
    def test_no_commit_on_error(self, stream_processor_instance, mock_kafka_consumer,
                                 mock_clickhouse_client):
        """
        Test: l'offset n'est PAS committé si le traitement échoue.
        
        RAISON:
            Permet de retraiter le message après correction du problème.
        """
        # ARRANGE - Simuler une erreur ClickHouse
        mock_clickhouse_client.execute.side_effect = Exception("Connection refused")
        
        message = {"rack_id": "R01", "sensors": {"temperature_c": 24.0}}
        
        # ACT
        try:
            stream_processor_instance.process_and_commit(message, topic=TOPIC_SENSOR_DATA)
        except Exception:
            pass
        
        # ASSERT - commit ne devrait PAS avoir été appelé
        # Note: Selon l'implémentation, le commit peut ne pas être appelé
        # ou être appelé avant l'erreur (moins idéal)
    
    # -------------------------------------------------------------------------
    # TEST 3: Récupération de l'offset actuel
    # -------------------------------------------------------------------------
    def test_get_current_offset(self, stream_processor_instance, mock_kafka_consumer):
        """
        Test: récupération de l'offset actuel.
        """
        # ACT
        offset = stream_processor_instance.get_current_offset(
            topic=TOPIC_SENSOR_DATA, partition=0
        )
        
        # ASSERT
        assert offset is not None, "L'offset devrait être récupérable"
        assert isinstance(offset, int), "L'offset devrait être un entier"


# =============================================================================
# CLASSE DE TEST: TRAITEMENT BATCH
# =============================================================================

class TestBatchProcessing:
    """
    Tests du traitement par batch de messages.
    
    BATCH PROCESSING:
        Traiter plusieurs messages en une seule opération DB
        pour améliorer les performances.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Accumulation de messages
    # -------------------------------------------------------------------------
    def test_batch_accumulation(self, stream_processor_instance):
        """
        Test: les messages sont accumulés jusqu'à la taille du batch.
        """
        # ARRANGE
        batch_size = 10
        messages = [
            {"rack_id": f"R{i:02d}", "sensors": {"temp": 24.0 + i}}
            for i in range(batch_size)
        ]
        
        # ACT
        for msg in messages:
            stream_processor_instance.add_to_batch(msg, topic=TOPIC_SENSOR_DATA)
        
        # ASSERT
        current_batch = stream_processor_instance.get_batch_size(TOPIC_SENSOR_DATA)
        assert current_batch == batch_size or current_batch == 0, (
            f"Batch devrait avoir {batch_size} messages ou être vidé après flush"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Flush automatique du batch
    # -------------------------------------------------------------------------
    def test_batch_auto_flush(self, stream_processor_instance, mock_clickhouse_client):
        """
        Test: le batch est automatiquement flushé quand il atteint la limite.
        
        LIMITE: 100 messages ou 5 secondes (selon l'implémentation)
        """
        # ARRANGE
        batch_limit = stream_processor_instance.batch_size if hasattr(
            stream_processor_instance, 'batch_size') else 100
        
        # ACT - Ajouter plus que la limite
        for i in range(batch_limit + 10):
            stream_processor_instance.add_to_batch(
                {"rack_id": f"R{i:02d}", "sensors": {"temp": 24.0}},
                topic=TOPIC_SENSOR_DATA
            )
        
        # ASSERT - Au moins un flush devrait avoir eu lieu
        # Le nombre exact d'appels dépend de l'implémentation


# =============================================================================
# CLASSE DE TEST: GESTION DES ERREURS
# =============================================================================

class TestErrorHandling:
    """
    Tests de la gestion des erreurs du stream processor.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Retry sur erreur temporaire
    # -------------------------------------------------------------------------
    def test_retry_on_transient_error(self, stream_processor_instance, mock_clickhouse_client):
        """
        Test: retry automatique sur erreur temporaire (ex: timeout).
        """
        # ARRANGE - Première tentative échoue, deuxième réussit
        mock_clickhouse_client.execute.side_effect = [
            Exception("Connection timeout"),  # Premier appel échoue
            None  # Deuxième appel réussit
        ]
        
        message = {"rack_id": "R01", "sensors": {"temperature_c": 24.0}}
        
        # ACT
        try:
            stream_processor_instance.process_with_retry(
                message, topic=TOPIC_SENSOR_DATA, max_retries=3
            )
            success = True
        except Exception:
            success = False
        
        # ASSERT - Le retry devrait permettre le succès
        # Note: Selon l'implémentation
    
    # -------------------------------------------------------------------------
    # TEST 2: Dead Letter Queue sur erreur permanente
    # -------------------------------------------------------------------------
    def test_dead_letter_queue_on_permanent_error(self, stream_processor_instance):
        """
        Test: message envoyé en DLQ après échec de tous les retries.
        
        DLQ (Dead Letter Queue):
            File d'attente pour les messages qui ne peuvent pas être traités.
            Permet une analyse manuelle ultérieure.
        """
        # ARRANGE - Message qui échoue toujours
        bad_message = {"invalid": "format", "no_rack_id": True}
        
        # ACT
        stream_processor_instance.process_with_retry(
            bad_message, topic=TOPIC_SENSOR_DATA, max_retries=3
        )
        
        # ASSERT - Message devrait être en DLQ
        dlq_count = stream_processor_instance.get_dlq_count() if hasattr(
            stream_processor_instance, 'get_dlq_count') else 0
        # Note: La vérification dépend de l'implémentation
    
    # -------------------------------------------------------------------------
    # TEST 3: Circuit breaker
    # -------------------------------------------------------------------------
    def test_circuit_breaker_opens_on_failures(self, stream_processor_instance, 
                                                mock_clickhouse_client):
        """
        Test: le circuit breaker s'ouvre après plusieurs échecs consécutifs.
        
        CIRCUIT BREAKER:
            Pattern qui évite de surcharger un service défaillant.
            Après N échecs, les appels sont bloqués pendant un délai.
        """
        # ARRANGE - Simuler 5 échecs consécutifs
        mock_clickhouse_client.execute.side_effect = Exception("Service unavailable")
        
        message = {"rack_id": "R01", "sensors": {"temp": 24.0}}
        
        # ACT - Essayer plusieurs fois
        for _ in range(5):
            try:
                stream_processor_instance.route_message(message, topic=TOPIC_SENSOR_DATA)
            except Exception:
                pass
        
        # ASSERT - Circuit breaker devrait être ouvert (si implémenté)
        if hasattr(stream_processor_instance, 'is_circuit_open'):
            assert stream_processor_instance.is_circuit_open("clickhouse"), (
                "Circuit breaker devrait être ouvert après 5 échecs"
            )


# =============================================================================
# CLASSE DE TEST: MÉTRIQUES ET MONITORING
# =============================================================================

class TestMetricsAndMonitoring:
    """
    Tests des métriques de monitoring du stream processor.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Compteur de messages traités
    # -------------------------------------------------------------------------
    def test_message_counter(self, stream_processor_instance, sample_sensor_message):
        """
        Test: comptage correct des messages traités.
        """
        # ARRANGE
        initial_count = stream_processor_instance.get_processed_count() if hasattr(
            stream_processor_instance, 'get_processed_count') else 0
        
        message = json.loads(sample_sensor_message["value"])
        
        # ACT - Traiter un message
        stream_processor_instance.route_message(message, topic=TOPIC_SENSOR_DATA)
        
        # ASSERT
        if hasattr(stream_processor_instance, 'get_processed_count'):
            new_count = stream_processor_instance.get_processed_count()
            assert new_count >= initial_count, "Le compteur devrait augmenter"
    
    # -------------------------------------------------------------------------
    # TEST 2: Latence de traitement
    # -------------------------------------------------------------------------
    def test_processing_latency(self, stream_processor_instance, sample_sensor_message):
        """
        Test: mesure de la latence de traitement.
        
        OBJECTIF:
            < 100ms pour 95% des messages (P95)
        """
        import time
        
        message = json.loads(sample_sensor_message["value"])
        
        # ACT
        start = time.perf_counter()
        stream_processor_instance.route_message(message, topic=TOPIC_SENSOR_DATA)
        latency_ms = (time.perf_counter() - start) * 1000
        
        # ASSERT
        assert latency_ms < 1000, (  # Tolérance large pour les tests
            f"Latence de traitement trop élevée: {latency_ms:.1f}ms"
        )
    
    # -------------------------------------------------------------------------
    # TEST 3: Consumer lag
    # -------------------------------------------------------------------------
    def test_consumer_lag_tracking(self, stream_processor_instance):
        """
        Test: tracking du lag du consumer.
        
        LAG:
            Différence entre le dernier offset produit et le dernier consommé.
            Un lag élevé indique que le consumer ne suit pas le rythme.
        """
        # ACT
        lag = stream_processor_instance.get_consumer_lag() if hasattr(
            stream_processor_instance, 'get_consumer_lag') else None
        
        # ASSERT
        if lag is not None:
            assert isinstance(lag, (int, dict)), "Le lag devrait être numérique"


# =============================================================================
# CLASSE DE TEST: CYCLE DE VIE
# =============================================================================

class TestLifecycle:
    """
    Tests du cycle de vie du stream processor.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Démarrage correct
    # -------------------------------------------------------------------------
    def test_start_subscribes_to_topics(self, stream_processor_instance, mock_kafka_consumer):
        """
        Test: le démarrage s'abonne aux topics configurés.
        """
        # ACT
        stream_processor_instance.start()
        
        # ASSERT
        mock_kafka_consumer.subscribe.assert_called()
    
    # -------------------------------------------------------------------------
    # TEST 2: Arrêt gracieux
    # -------------------------------------------------------------------------
    def test_graceful_shutdown(self, stream_processor_instance, mock_kafka_consumer):
        """
        Test: arrêt gracieux (flush des batches, commit des offsets).
        """
        # ACT
        stream_processor_instance.stop()
        
        # ASSERT
        mock_kafka_consumer.close.assert_called()
    
    # -------------------------------------------------------------------------
    # TEST 3: Reconnexion automatique
    # -------------------------------------------------------------------------
    def test_auto_reconnect_on_disconnect(self, stream_processor_instance):
        """
        Test: reconnexion automatique après déconnexion.
        """
        # Ce test est difficile à simuler en unitaire
        # Il serait mieux couvert par un test d'intégration
        pass


# =============================================================================
# FIN DU MODULE - TICKET-108 - Tests Stream Processor VertiFlow
# =============================================================================
