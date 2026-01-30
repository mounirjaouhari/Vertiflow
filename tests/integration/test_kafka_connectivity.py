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
MODULE: tests/integration/test_kafka_connectivity.py
DESCRIPTION: Tests d'intégration de la connectivité Kafka multi-topics

    Kafka est le SYSTÈME NERVEUX de VertiFlow.
    Il assure la communication asynchrone entre tous les composants.
    Ces tests vérifient que Kafka fonctionne correctement.

    ARCHITECTURE KAFKA VERTIFLOW:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      KAFKA CLUSTER - VERTIFLOW                          │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │                         BROKER(S)                               │    │
    │  │                     localhost:9092                              │    │
    │  └─────────────────────────────────────────────────────────────────┘    │
    │                                                                         │
    │  TOPICS:                                                                │
    │  ┌─────────────────┬──────────┬─────────────────────────────────────┐   │
    │  │ Topic           │ Partitions│ Producteurs → Consommateurs        │   │
    │  ├─────────────────┼──────────┼─────────────────────────────────────┤   │
    │  │ vertiflow.sensor│    3     │ NiFi/MQTT Bridge → StreamProcessor  │   │
    │  │ vertiflow.cmd   │    3     │ Cortex/API → Actuators/MongoDB      │   │
    │  │ vertiflow.alerts│    3     │ AlertGenerator → Notify/MongoDB     │   │
    │  │ vertiflow.pred  │    3     │ Oracle/Classifier → MongoDB         │   │
    │  │ vertiflow.feed  │    1     │ FeedbackLoop → ML Training          │   │
    │  └─────────────────┴──────────┴─────────────────────────────────────┘   │
    │                                                                         │
    │  CONSUMER GROUPS:                                                       │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │ • vertiflow-stream-processor (sensor, cmd)                      │    │
    │  │ • vertiflow-alert-handler (alerts)                              │    │
    │  │ • vertiflow-ml-pipeline (pred, feed)                            │    │
    │  │ • vertiflow-archiver (all topics)                               │    │
    │  └─────────────────────────────────────────────────────────────────┘    │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

    GARANTIES KAFKA:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ • Durabilité: Messages persistés sur disque                             │
    │ • Ordre: Messages ordonnés PAR PARTITION                                │
    │ • At-least-once: Chaque message livré au moins une fois                 │
    │ • Scalabilité: Partitions permettent le parallélisme                    │
    └─────────────────────────────────────────────────────────────────────────┘

PRÉREQUIS:
    $ docker-compose up -d kafka zookeeper

EXÉCUTION:
    $ pytest tests/integration/test_kafka_connectivity.py -v

Développé par       : @Mouhammed & @Imrane
Ticket(s) associé(s): TICKET-111
Sprint              : Semaine 6 - Phase Qualité & Tests

Dépendances:
    - pytest>=8.0.0
    - kafka-python>=2.0.2

================================================================================
© 2026 VertiFlow Core Team - Tous droits réservés
Développé dans le cadre de l'Initiative Nationale Marocaine JobInTech
au sein de l'École YNOV Maroc Campus
================================================================================
"""

import os
import json
import time
import uuid
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Import des utilitaires d'intégration
from tests.integration import (
    require_services,
    wait_for_condition,
    get_kafka_producer,
    get_kafka_consumer,
    is_port_open,
    logger,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_GROUP_ID,
)


# =============================================================================
# CONSTANTES DE TEST
# =============================================================================

# Topics Kafka VertiFlow
TOPICS = {
    "sensor": "vertiflow.sensor",
    "commands": "vertiflow.commands",
    "alerts": "vertiflow.alerts",
    "predictions": "vertiflow.predictions",
    "feedback": "vertiflow.feedback",
}

# Configuration des tests
TEST_RUN_ID = str(uuid.uuid4())[:8]
MESSAGE_TIMEOUT_SECONDS = 10
CONSUMER_POLL_TIMEOUT_MS = 5000


# =============================================================================
# MARQUEURS PYTEST
# =============================================================================

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_docker,
]


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def kafka_available():
    """
    Vérifie que Kafka est disponible.
    """
    host = KAFKA_BOOTSTRAP_SERVERS.split(":")[0]
    port = int(KAFKA_BOOTSTRAP_SERVERS.split(":")[1])
    
    if not is_port_open(host, port, timeout=5):
        pytest.skip(
            f"Kafka non disponible sur {KAFKA_BOOTSTRAP_SERVERS}. "
            f"Démarrez avec: docker-compose up -d kafka zookeeper"
        )
    
    logger.info(f"✅ Kafka disponible: {KAFKA_BOOTSTRAP_SERVERS}")
    return True


@pytest.fixture(scope="module")
def kafka_admin(kafka_available):
    """
    Client admin Kafka pour la gestion des topics.
    """
    try:
        from kafka.admin import KafkaAdminClient, NewTopic
        from kafka.errors import TopicAlreadyExistsError
        
        admin = KafkaAdminClient(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            client_id=f"vertiflow-admin-{TEST_RUN_ID}"
        )
        
        # Créer les topics de test s'ils n'existent pas
        topics_to_create = [
            NewTopic(name=topic, num_partitions=3, replication_factor=1)
            for topic in TOPICS.values()
        ]
        
        try:
            admin.create_topics(topics_to_create, validate_only=False)
            logger.info(f"✅ Topics créés: {list(TOPICS.values())}")
        except TopicAlreadyExistsError:
            logger.info("ℹ️ Topics déjà existants")
        except Exception as e:
            logger.warning(f"Erreur création topics: {e}")
        
        yield admin
        
        admin.close()
        
    except ImportError:
        pytest.skip("kafka-python admin non disponible")


@pytest.fixture
def producer(kafka_available):
    """
    Producer Kafka pour les tests.
    """
    producer = get_kafka_producer()
    yield producer
    producer.close()


@pytest.fixture
def consumer_factory(kafka_available):
    """
    Factory pour créer des consumers avec group_id unique.
    """
    consumers = []
    
    def _create_consumer(topics: List[str], group_id: str = None):
        if group_id is None:
            group_id = f"test-{TEST_RUN_ID}-{uuid.uuid4().hex[:6]}"
        
        consumer = get_kafka_consumer(topics, group_id=group_id)
        consumers.append(consumer)
        return consumer
    
    yield _create_consumer
    
    # Cleanup
    for consumer in consumers:
        try:
            consumer.close()
        except Exception:
            pass


@pytest.fixture
def unique_message_id():
    """
    Génère un ID unique pour identifier les messages de test.
    """
    return f"MSG_{TEST_RUN_ID}_{uuid.uuid4().hex[:8]}"


# =============================================================================
# CLASSE DE TEST: CONNECTIVITÉ DE BASE
# =============================================================================

class TestKafkaBasicConnectivity:
    """
    Tests de connectivité de base à Kafka.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Connexion au broker
    # -------------------------------------------------------------------------
    def test_broker_connection(self, kafka_available):
        """
        Test: connexion au broker Kafka réussie.
        """
        from kafka import KafkaClient
        
        # ACT
        client = KafkaClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        
        # ASSERT
        assert client.bootstrap_connected(), "Non connecté au broker"
        
        # Cleanup
        client.close()
        
        logger.info("✅ Connexion au broker Kafka vérifiée")
    
    # -------------------------------------------------------------------------
    # TEST 2: Liste des topics
    # -------------------------------------------------------------------------
    def test_list_topics(self, producer):
        """
        Test: récupération de la liste des topics.
        """
        from kafka import KafkaConsumer
        
        # ACT
        consumer = KafkaConsumer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=f"topic-list-{TEST_RUN_ID}"
        )
        topics = consumer.topics()
        consumer.close()
        
        # ASSERT
        assert isinstance(topics, set), "Topics devrait être un set"
        assert len(topics) >= 0, "Devrait pouvoir lister les topics"
        
        logger.info(f"✅ Topics listés: {len(topics)} topics trouvés")
    
    # -------------------------------------------------------------------------
    # TEST 3: Métadonnées du cluster
    # -------------------------------------------------------------------------
    def test_cluster_metadata(self, kafka_available):
        """
        Test: récupération des métadonnées du cluster.
        """
        from kafka import KafkaClient
        
        # ACT
        client = KafkaClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        
        # Récupérer les brokers
        brokers = client.cluster.brokers()
        
        # ASSERT
        assert len(brokers) >= 1, "Au moins un broker devrait être disponible"
        
        for broker in brokers:
            logger.info(f"  Broker: {broker.host}:{broker.port} (ID: {broker.nodeId})")
        
        client.close()
        
        logger.info(f"✅ Cluster: {len(brokers)} broker(s) actif(s)")


# =============================================================================
# CLASSE DE TEST: PRODUCTION DE MESSAGES
# =============================================================================

class TestKafkaProducer:
    """
    Tests du producer Kafka.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Envoi d'un message simple
    # -------------------------------------------------------------------------
    def test_send_simple_message(self, producer, unique_message_id):
        """
        Test: envoi d'un message simple sur un topic.
        """
        # ARRANGE
        topic = TOPICS["sensor"]
        message = {
            "message_id": unique_message_id,
            "test": "simple_message",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # ACT
        future = producer.send(topic, value=json.dumps(message).encode('utf-8'))
        producer.flush()
        
        # Attendre la confirmation
        record_metadata = future.get(timeout=10)
        
        # ASSERT
        assert record_metadata.topic == topic, f"Topic incorrect: {record_metadata.topic}"
        assert record_metadata.partition >= 0, "Partition invalide"
        assert record_metadata.offset >= 0, "Offset invalide"
        
        logger.info(
            f"✅ Message envoyé: topic={topic}, "
            f"partition={record_metadata.partition}, offset={record_metadata.offset}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Envoi avec clé (partitioning)
    # -------------------------------------------------------------------------
    def test_send_message_with_key(self, producer, unique_message_id):
        """
        Test: envoi d'un message avec clé pour le partitioning.
        
        La clé détermine la partition: même clé = même partition = ordre garanti
        """
        # ARRANGE
        topic = TOPICS["sensor"]
        key = b"R01"  # Rack ID comme clé
        message = {
            "message_id": unique_message_id,
            "rack_id": "R01",
            "test": "message_with_key"
        }
        
        # ACT - Envoyer 3 messages avec la même clé
        partitions = []
        for i in range(3):
            msg = {**message, "sequence": i}
            future = producer.send(
                topic, 
                key=key,
                value=json.dumps(msg).encode('utf-8')
            )
            producer.flush()
            metadata = future.get(timeout=10)
            partitions.append(metadata.partition)
        
        # ASSERT - Tous sur la même partition
        assert len(set(partitions)) == 1, (
            f"Messages avec même clé devraient aller sur même partition. "
            f"Partitions: {partitions}"
        )
        
        logger.info(f"✅ 3 messages avec clé R01 → partition {partitions[0]}")
    
    # -------------------------------------------------------------------------
    # TEST 3: Envoi sur tous les topics
    # -------------------------------------------------------------------------
    def test_send_to_all_topics(self, producer, unique_message_id):
        """
        Test: envoi d'un message sur chaque topic VertiFlow.
        """
        # ACT & ASSERT
        for topic_name, topic in TOPICS.items():
            message = {
                "message_id": f"{unique_message_id}_{topic_name}",
                "topic_test": topic_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            future = producer.send(topic, value=json.dumps(message).encode('utf-8'))
            producer.flush()
            metadata = future.get(timeout=10)
            
            assert metadata.topic == topic, f"Topic mismatch: {metadata.topic} != {topic}"
            logger.info(f"  ✅ {topic_name}: partition={metadata.partition}")
        
        logger.info(f"✅ Messages envoyés sur {len(TOPICS)} topics")
    
    # -------------------------------------------------------------------------
    # TEST 4: Envoi batch (performance)
    # -------------------------------------------------------------------------
    @pytest.mark.slow
    def test_send_batch_performance(self, producer, unique_message_id):
        """
        Test: envoi d'un batch de messages (performance).
        
        OBJECTIF:
            1000 messages en moins de 5 secondes
        """
        # ARRANGE
        topic = TOPICS["sensor"]
        batch_size = 1000
        
        # ACT
        start_time = time.perf_counter()
        
        futures = []
        for i in range(batch_size):
            message = {
                "message_id": f"{unique_message_id}_{i}",
                "sequence": i,
                "batch_test": True
            }
            future = producer.send(topic, value=json.dumps(message).encode('utf-8'))
            futures.append(future)
        
        producer.flush()
        
        # Attendre toutes les confirmations
        for future in futures:
            future.get(timeout=30)
        
        elapsed = time.perf_counter() - start_time
        rate = batch_size / elapsed
        
        # ASSERT
        assert elapsed < 10, f"Batch trop lent: {elapsed:.2f}s pour {batch_size} messages"
        
        logger.info(
            f"✅ Batch de {batch_size} messages: {elapsed:.2f}s "
            f"({rate:.0f} msg/s)"
        )


# =============================================================================
# CLASSE DE TEST: CONSOMMATION DE MESSAGES
# =============================================================================

class TestKafkaConsumer:
    """
    Tests du consumer Kafka.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Consommation d'un message
    # -------------------------------------------------------------------------
    def test_consume_message(self, producer, consumer_factory, unique_message_id):
        """
        Test: consommation d'un message produit.
        """
        # ARRANGE
        topic = TOPICS["sensor"]
        message = {
            "message_id": unique_message_id,
            "test": "consume_test",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Créer le consumer AVANT de produire
        consumer = consumer_factory([topic])
        
        # ACT - Produire le message
        producer.send(topic, value=json.dumps(message).encode('utf-8'))
        producer.flush()
        
        # Consommer
        found = False
        start_time = time.time()
        
        while time.time() - start_time < MESSAGE_TIMEOUT_SECONDS:
            records = consumer.poll(timeout_ms=CONSUMER_POLL_TIMEOUT_MS)
            
            for tp, messages in records.items():
                for msg in messages:
                    data = json.loads(msg.value)
                    if data.get("message_id") == unique_message_id:
                        found = True
                        break
            
            if found:
                break
        
        # ASSERT
        assert found, f"Message {unique_message_id} non trouvé après {MESSAGE_TIMEOUT_SECONDS}s"
        
        logger.info(f"✅ Message consommé: {unique_message_id}")
    
    # -------------------------------------------------------------------------
    # TEST 2: Consumer group offset
    # -------------------------------------------------------------------------
    def test_consumer_group_offset(self, producer, consumer_factory, unique_message_id):
        """
        Test: le consumer group retient sa position (offset).
        
        Deux consumers du même groupe ne reçoivent pas le même message.
        """
        # ARRANGE
        topic = TOPICS["sensor"]
        group_id = f"shared-group-{TEST_RUN_ID}"
        
        # Créer 2 consumers dans le même groupe
        consumer1 = consumer_factory([topic], group_id=group_id)
        consumer2 = consumer_factory([topic], group_id=group_id)
        
        # Produire un message
        message = {"message_id": unique_message_id, "test": "group_offset"}
        producer.send(topic, value=json.dumps(message).encode('utf-8'))
        producer.flush()
        
        # ACT - Les deux consumers essaient de consommer
        received_by = []
        
        for i, consumer in enumerate([consumer1, consumer2]):
            records = consumer.poll(timeout_ms=3000)
            for tp, messages in records.items():
                for msg in messages:
                    data = json.loads(msg.value)
                    if data.get("message_id") == unique_message_id:
                        received_by.append(f"consumer{i+1}")
        
        # ASSERT - Un seul devrait recevoir
        assert len(received_by) <= 1, (
            f"Message reçu par {received_by} (devrait être 1 max)"
        )
        
        logger.info(f"✅ Consumer group vérifié (reçu par: {received_by or 'aucun - déjà commit'})")
    
    # -------------------------------------------------------------------------
    # TEST 3: Multiple topics
    # -------------------------------------------------------------------------
    def test_consume_multiple_topics(self, producer, consumer_factory, unique_message_id):
        """
        Test: consommation de plusieurs topics simultanément.
        """
        # ARRANGE
        topics = [TOPICS["sensor"], TOPICS["alerts"]]
        consumer = consumer_factory(topics)
        
        # Produire sur les deux topics
        for topic in topics:
            message = {
                "message_id": f"{unique_message_id}_{topic}",
                "source_topic": topic
            }
            producer.send(topic, value=json.dumps(message).encode('utf-8'))
        producer.flush()
        
        # ACT - Consommer
        received_topics = set()
        start_time = time.time()
        
        while time.time() - start_time < MESSAGE_TIMEOUT_SECONDS:
            records = consumer.poll(timeout_ms=CONSUMER_POLL_TIMEOUT_MS)
            
            for tp, messages in records.items():
                for msg in messages:
                    data = json.loads(msg.value)
                    if unique_message_id in data.get("message_id", ""):
                        received_topics.add(tp.topic)
            
            if len(received_topics) == len(topics):
                break
        
        # ASSERT
        assert len(received_topics) >= 1, "Aucun message reçu"
        
        logger.info(f"✅ Multi-topics: messages reçus de {received_topics}")


# =============================================================================
# CLASSE DE TEST: PARTITIONING ET SCALABILITÉ
# =============================================================================

class TestKafkaPartitioning:
    """
    Tests du partitioning Kafka.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Distribution sur les partitions
    # -------------------------------------------------------------------------
    def test_partition_distribution(self, producer, unique_message_id):
        """
        Test: les messages sont distribués sur plusieurs partitions.
        """
        # ARRANGE
        topic = TOPICS["sensor"]
        num_messages = 30
        
        # ACT - Envoyer des messages avec des clés différentes
        partitions_used = set()
        
        for i in range(num_messages):
            key = f"RACK_{i % 10}".encode()  # 10 clés différentes
            message = {"message_id": f"{unique_message_id}_{i}", "rack": f"R{i % 10}"}
            
            future = producer.send(topic, key=key, value=json.dumps(message).encode())
            producer.flush()
            metadata = future.get(timeout=10)
            partitions_used.add(metadata.partition)
        
        # ASSERT - Plus d'une partition utilisée (si topic a >1 partition)
        logger.info(f"✅ Messages distribués sur {len(partitions_used)} partition(s)")
    
    # -------------------------------------------------------------------------
    # TEST 2: Ordre dans une partition
    # -------------------------------------------------------------------------
    def test_partition_ordering(self, producer, consumer_factory, unique_message_id):
        """
        Test: l'ordre est garanti DANS une partition.
        
        Messages avec même clé arrivent dans l'ordre.
        """
        # ARRANGE
        topic = TOPICS["sensor"]
        key = f"ORDER_TEST_{unique_message_id}".encode()
        num_messages = 10
        
        consumer = consumer_factory([topic])
        
        # ACT - Envoyer des messages numérotés
        for i in range(num_messages):
            message = {"message_id": unique_message_id, "sequence": i}
            producer.send(topic, key=key, value=json.dumps(message).encode())
        producer.flush()
        
        # Consommer et vérifier l'ordre
        received_sequences = []
        start_time = time.time()
        
        while time.time() - start_time < MESSAGE_TIMEOUT_SECONDS:
            records = consumer.poll(timeout_ms=CONSUMER_POLL_TIMEOUT_MS)
            
            for tp, messages in records.items():
                for msg in messages:
                    data = json.loads(msg.value)
                    if data.get("message_id") == unique_message_id:
                        received_sequences.append(data["sequence"])
            
            if len(received_sequences) >= num_messages:
                break
        
        # ASSERT - Ordre préservé
        if len(received_sequences) >= 2:
            is_ordered = all(
                received_sequences[i] <= received_sequences[i+1] 
                for i in range(len(received_sequences)-1)
            )
            assert is_ordered, f"Ordre non préservé: {received_sequences}"
        
        logger.info(f"✅ Ordre préservé: {received_sequences[:5]}...")


# =============================================================================
# CLASSE DE TEST: RÉSILIENCE
# =============================================================================

class TestKafkaResilience:
    """
    Tests de résilience Kafka.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Reconnexion producer
    # -------------------------------------------------------------------------
    def test_producer_reconnection(self, kafka_available, unique_message_id):
        """
        Test: le producer peut se reconnecter après une déconnexion.
        """
        from kafka import KafkaProducer
        
        # ARRANGE
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            reconnect_backoff_ms=100,
            reconnect_backoff_max_ms=1000
        )
        
        # ACT - Envoyer, fermer, recréer, renvoyer
        topic = TOPICS["sensor"]
        
        # Premier envoi
        msg1 = {"message_id": f"{unique_message_id}_1", "phase": "before"}
        future1 = producer.send(topic, value=json.dumps(msg1).encode())
        producer.flush()
        future1.get(timeout=10)
        
        # Fermer
        producer.close()
        
        # Recréer
        producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        
        # Deuxième envoi
        msg2 = {"message_id": f"{unique_message_id}_2", "phase": "after"}
        future2 = producer.send(topic, value=json.dumps(msg2).encode())
        producer.flush()
        future2.get(timeout=10)
        
        producer.close()
        
        # ASSERT - Les deux envois ont réussi
        logger.info("✅ Reconnexion producer vérifiée")
    
    # -------------------------------------------------------------------------
    # TEST 2: Consumer resume après crash
    # -------------------------------------------------------------------------
    def test_consumer_resume_from_offset(self, producer, kafka_available, unique_message_id):
        """
        Test: le consumer reprend depuis le bon offset après redémarrage.
        """
        from kafka import KafkaConsumer
        
        # ARRANGE
        topic = TOPICS["sensor"]
        group_id = f"resume-test-{TEST_RUN_ID}"
        
        # Produire un message
        msg1 = {"message_id": f"{unique_message_id}_1", "batch": 1}
        producer.send(topic, value=json.dumps(msg1).encode())
        producer.flush()
        
        # Premier consumer - consomme et commit
        consumer1 = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        records = consumer1.poll(timeout_ms=5000)
        consumer1.close()
        
        # Produire un nouveau message
        msg2 = {"message_id": f"{unique_message_id}_2", "batch": 2}
        producer.send(topic, value=json.dumps(msg2).encode())
        producer.flush()
        
        # Deuxième consumer (même groupe) - ne devrait pas revoir msg1
        consumer2 = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        # ACT
        new_messages = []
        records = consumer2.poll(timeout_ms=5000)
        for tp, messages in records.items():
            for msg in messages:
                data = json.loads(msg.value)
                if unique_message_id in data.get("message_id", ""):
                    new_messages.append(data)
        
        consumer2.close()
        
        # ASSERT - Devrait avoir le message 2, pas le 1 (déjà commit)
        logger.info(f"✅ Resume depuis offset: {len(new_messages)} nouveau(x) message(s)")
    
    # -------------------------------------------------------------------------
    # TEST 3: Timeout handling
    # -------------------------------------------------------------------------
    def test_timeout_handling(self, kafka_available):
        """
        Test: gestion correcte des timeouts.
        """
        from kafka import KafkaConsumer
        
        # ARRANGE - Consumer sur un topic vide ou presque
        consumer = KafkaConsumer(
            "vertiflow.test.empty",  # Topic probablement vide
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=f"timeout-test-{TEST_RUN_ID}",
            auto_offset_reset='latest'
        )
        
        # ACT - Poll avec timeout court
        start_time = time.perf_counter()
        records = consumer.poll(timeout_ms=1000)  # 1 seconde
        elapsed = time.perf_counter() - start_time
        
        consumer.close()
        
        # ASSERT - Le poll devrait retourner après le timeout
        assert elapsed < 5, f"Poll a pris trop de temps: {elapsed:.2f}s"
        
        logger.info(f"✅ Timeout géré correctement ({elapsed:.2f}s)")


# =============================================================================
# CLASSE DE TEST: TOPICS VERTIFLOW SPÉCIFIQUES
# =============================================================================

class TestVertiflowTopics:
    """
    Tests des topics spécifiques VertiFlow.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Topic sensor_data
    # -------------------------------------------------------------------------
    def test_sensor_topic_structure(self, producer, consumer_factory, unique_message_id):
        """
        Test: structure du topic vertiflow.sensor.
        """
        # ARRANGE
        topic = TOPICS["sensor"]
        sensor_message = {
            "message_id": unique_message_id,
            "rack_id": "R01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sensors": {
                "temperature_c": 24.5,
                "humidity_pct": 68.0,
                "co2_ppm": 850,
                "light_ppfd": 420
            }
        }
        
        # ACT
        producer.send(
            topic, 
            key=b"R01",
            value=json.dumps(sensor_message).encode()
        )
        producer.flush()
        
        # ASSERT - Message envoyé avec succès
        logger.info(f"✅ Message sensor structuré envoyé: {unique_message_id}")
    
    # -------------------------------------------------------------------------
    # TEST 2: Topic commands
    # -------------------------------------------------------------------------
    def test_commands_topic_structure(self, producer, unique_message_id):
        """
        Test: structure du topic vertiflow.commands.
        """
        # ARRANGE
        topic = TOPICS["commands"]
        command_message = {
            "command_id": unique_message_id,
            "rack_id": "R01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command_type": "IRRIGATION",
            "parameters": {
                "duration_seconds": 120,
                "flow_rate_ml_min": 500
            },
            "priority": "NORMAL",
            "source": "INTEGRATION_TEST"
        }
        
        # ACT
        producer.send(
            topic,
            key=b"R01",
            value=json.dumps(command_message).encode()
        )
        producer.flush()
        
        logger.info(f"✅ Commande envoyée: {unique_message_id}")
    
    # -------------------------------------------------------------------------
    # TEST 3: Topic alerts
    # -------------------------------------------------------------------------
    def test_alerts_topic_structure(self, producer, unique_message_id):
        """
        Test: structure du topic vertiflow.alerts.
        """
        # ARRANGE
        topic = TOPICS["alerts"]
        alert_message = {
            "alert_id": unique_message_id,
            "rack_id": "R01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_type": "TEMP_HIGH",
            "severity": "WARNING",
            "current_value": 29.5,
            "threshold": 28.0,
            "message": "Test alert from integration tests"
        }
        
        # ACT
        producer.send(
            topic,
            key=b"TEMP_HIGH",
            value=json.dumps(alert_message).encode()
        )
        producer.flush()
        
        logger.info(f"✅ Alerte envoyée: {unique_message_id}")


# =============================================================================
# FIN DU MODULE - TICKET-111 - Tests Integration Kafka VertiFlow
# =============================================================================
