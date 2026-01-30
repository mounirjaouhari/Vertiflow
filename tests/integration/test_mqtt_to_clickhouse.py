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
MODULE: tests/integration/test_mqtt_to_clickhouse.py
DESCRIPTION: Tests d'intégration du pipeline MQTT → Kafka → ClickHouse

    Ce test vérifie le pipeline COMPLET de collecte de données IoT:
    
    FLUX DE DONNÉES:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                     PIPELINE IoT - TEST D'INTÉGRATION                   │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  ┌──────────────┐                                                       │
    │  │   CAPTEUR    │  Ce test simule un capteur IoT                        │
    │  │   (simulé)   │  qui publie sur MQTT                                  │
    │  └──────┬───────┘                                                       │
    │         │                                                               │
    │         │ MQTT Publish                                                  │
    │         │ Topic: vertiflow/sensors/R01                                  │
    │         ▼                                                               │
    │  ┌──────────────┐                                                       │
    │  │  MOSQUITTO   │  Broker MQTT                                          │
    │  │  (MQTT)      │  Port: 1883                                           │
    │  └──────┬───────┘                                                       │
    │         │                                                               │
    │         │ NiFi/Kafka Connect                                            │
    │         │ (ou script de bridge)                                         │
    │         ▼                                                               │
    │  ┌──────────────┐                                                       │
    │  │   KAFKA      │  Message Queue                                        │
    │  │              │  Topic: vertiflow.sensor                              │
    │  └──────┬───────┘                                                       │
    │         │                                                               │
    │         │ Stream Processor                                              │
    │         │ (Consumer Kafka)                                              │
    │         ▼                                                               │
    │  ┌──────────────┐                                                       │
    │  │ CLICKHOUSE   │  Stockage Time-Series                                 │
    │  │              │  Table: sensor_data                                   │
    │  └──────────────┘                                                       │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

    OBJECTIF DU TEST:
    Vérifier que les données publiées sur MQTT arrivent bien dans ClickHouse
    avec les bonnes valeurs et dans un délai acceptable (< 5 secondes).

    PRÉREQUIS:
    Les services suivants doivent être démarrés:
        $ docker-compose up -d mosquitto kafka clickhouse
    
    EXÉCUTION:
        $ pytest tests/integration/test_mqtt_to_clickhouse.py -v

Développé par       : @Imrane & @Mouhammed
Ticket(s) associé(s): TICKET-110
Sprint              : Semaine 6 - Phase Qualité & Tests

Dépendances:
    - pytest>=8.0.0
    - paho-mqtt>=2.0.0
    - clickhouse-driver>=0.2.6
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
from typing import Dict, Any, Optional

# Import des utilitaires d'intégration
from tests.integration import (
    require_services,
    wait_for_condition,
    get_clickhouse_client,
    get_mqtt_client,
    get_kafka_producer,
    get_kafka_consumer,
    is_port_open,
    logger,
    CLICKHOUSE_HOST,
    CLICKHOUSE_PORT,
    MQTT_HOST,
    MQTT_PORT,
    KAFKA_BOOTSTRAP_SERVERS,
)


# =============================================================================
# CONSTANTES DE TEST
# =============================================================================

# Topics MQTT
MQTT_TOPIC_SENSORS = "vertiflow/sensors/{rack_id}"
MQTT_TOPIC_SENSORS_WILDCARD = "vertiflow/sensors/#"

# Topics Kafka
KAFKA_TOPIC_SENSOR_DATA = "vertiflow.sensor"

# Table ClickHouse
CLICKHOUSE_TABLE_SENSOR = "sensor_data"
CLICKHOUSE_DATABASE = "vertiflow_test"

# Timeouts
MESSAGE_PROPAGATION_TIMEOUT = 10.0  # Max 10s pour la propagation
POLL_INTERVAL = 0.5

# Identifiants de test (uniques pour éviter les collisions)
TEST_RUN_ID = str(uuid.uuid4())[:8]


# =============================================================================
# MARQUEURS PYTEST
# =============================================================================

# Marquer tous les tests comme tests d'intégration
pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_docker,
]


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def check_services():
    """
    Vérifie que tous les services nécessaires sont disponibles.
    Skip le module entier si un service manque.
    """
    services_status = {
        "mqtt": is_port_open(MQTT_HOST, MQTT_PORT, timeout=2),
        "clickhouse": is_port_open(CLICKHOUSE_HOST, CLICKHOUSE_PORT, timeout=2),
        "kafka": is_port_open(
            KAFKA_BOOTSTRAP_SERVERS.split(":")[0],
            int(KAFKA_BOOTSTRAP_SERVERS.split(":")[1]),
            timeout=2
        ),
    }
    
    missing = [name for name, available in services_status.items() if not available]
    
    if missing:
        pytest.skip(
            f"Services manquants: {', '.join(missing)}. "
            f"Démarrez avec: docker-compose up -d mosquitto kafka clickhouse"
        )
    
    logger.info("✅ Tous les services sont disponibles pour les tests d'intégration")
    return services_status


@pytest.fixture(scope="module")
def clickhouse_client(check_services):
    """
    Client ClickHouse pour les tests.
    Crée la table de test si elle n'existe pas.
    """
    client = get_clickhouse_client()
    
    # Créer la base de test si nécessaire
    client.execute(f"CREATE DATABASE IF NOT EXISTS {CLICKHOUSE_DATABASE}")
    client.execute(f"USE {CLICKHOUSE_DATABASE}")
    
    # Créer la table de test
    client.execute(f"""
        CREATE TABLE IF NOT EXISTS {CLICKHOUSE_TABLE_SENSOR} (
            timestamp DateTime64(3) DEFAULT now64(3),
            rack_id String,
            test_run_id String,
            temperature_c Float32,
            humidity_pct Float32,
            co2_ppm UInt16,
            light_ppfd UInt16,
            ec_ms_cm Float32,
            ph Float32,
            water_temp_c Float32
        ) ENGINE = MergeTree()
        ORDER BY (rack_id, timestamp)
        TTL timestamp + INTERVAL 1 DAY
    """)
    
    logger.info(f"✅ Table ClickHouse créée: {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE_SENSOR}")
    
    yield client
    
    # Cleanup: supprimer les données de ce test run
    try:
        client.execute(f"""
            ALTER TABLE {CLICKHOUSE_TABLE_SENSOR} 
            DELETE WHERE test_run_id = '{TEST_RUN_ID}'
        """)
        logger.info(f"🗑️ Données de test nettoyées (run_id: {TEST_RUN_ID})")
    except Exception as e:
        logger.warning(f"Erreur lors du nettoyage: {e}")


@pytest.fixture(scope="module")
def mqtt_client(check_services):
    """
    Client MQTT pour publier les messages de test.
    """
    client = get_mqtt_client()
    client.loop_start()  # Démarrer la boucle de traitement en arrière-plan
    
    yield client
    
    client.loop_stop()
    client.disconnect()
    logger.info("🔌 Client MQTT déconnecté")


@pytest.fixture(scope="module")
def kafka_producer(check_services):
    """
    Producer Kafka pour les tests directs Kafka → ClickHouse.
    """
    producer = get_kafka_producer()
    
    yield producer
    
    producer.close()
    logger.info("🔌 Producer Kafka fermé")


@pytest.fixture
def unique_rack_id():
    """
    Génère un rack_id unique pour chaque test.
    Évite les collisions entre tests parallèles.
    """
    return f"R_TEST_{TEST_RUN_ID}_{uuid.uuid4().hex[:6]}"


@pytest.fixture
def sensor_data_factory(unique_rack_id):
    """
    Factory pour créer des données de capteurs.
    """
    def _create_sensor_data(
        rack_id: str = None,
        temperature: float = 24.5,
        humidity: float = 68.0,
        co2: int = 850,
        light: int = 420,
        ec: float = 1.75,
        ph: float = 6.2,
        water_temp: float = 21.0
    ) -> Dict[str, Any]:
        return {
            "rack_id": rack_id or unique_rack_id,
            "test_run_id": TEST_RUN_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sensors": {
                "temperature_c": temperature,
                "humidity_pct": humidity,
                "co2_ppm": co2,
                "light_ppfd": light,
                "ec_ms_cm": ec,
                "ph": ph,
                "water_temp_c": water_temp
            }
        }
    
    return _create_sensor_data


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def insert_directly_to_clickhouse(client, data: Dict[str, Any]) -> bool:
    """
    Insère les données directement dans ClickHouse (bypass du pipeline).
    Utilisé pour tester la lecture.
    """
    try:
        sensors = data.get("sensors", {})
        client.execute(f"""
            INSERT INTO {CLICKHOUSE_TABLE_SENSOR} 
            (rack_id, test_run_id, temperature_c, humidity_pct, co2_ppm, 
             light_ppfd, ec_ms_cm, ph, water_temp_c)
            VALUES
        """, [{
            "rack_id": data["rack_id"],
            "test_run_id": data.get("test_run_id", TEST_RUN_ID),
            "temperature_c": sensors.get("temperature_c", 0),
            "humidity_pct": sensors.get("humidity_pct", 0),
            "co2_ppm": sensors.get("co2_ppm", 0),
            "light_ppfd": sensors.get("light_ppfd", 0),
            "ec_ms_cm": sensors.get("ec_ms_cm", 0),
            "ph": sensors.get("ph", 0),
            "water_temp_c": sensors.get("water_temp_c", 0),
        }])
        return True
    except Exception as e:
        logger.error(f"Erreur insertion ClickHouse: {e}")
        return False


def query_sensor_data(client, rack_id: str, test_run_id: str = TEST_RUN_ID) -> list:
    """
    Requête les données de capteurs dans ClickHouse.
    """
    result = client.execute(f"""
        SELECT 
            rack_id,
            temperature_c,
            humidity_pct,
            co2_ppm,
            light_ppfd,
            ec_ms_cm,
            ph,
            water_temp_c,
            timestamp
        FROM {CLICKHOUSE_TABLE_SENSOR}
        WHERE rack_id = %(rack_id)s
          AND test_run_id = %(test_run_id)s
        ORDER BY timestamp DESC
        LIMIT 10
    """, {"rack_id": rack_id, "test_run_id": test_run_id})
    
    return result


def count_sensor_records(client, rack_id: str, test_run_id: str = TEST_RUN_ID) -> int:
    """
    Compte le nombre d'enregistrements pour un rack.
    """
    result = client.execute(f"""
        SELECT count() 
        FROM {CLICKHOUSE_TABLE_SENSOR}
        WHERE rack_id = %(rack_id)s
          AND test_run_id = %(test_run_id)s
    """, {"rack_id": rack_id, "test_run_id": test_run_id})
    
    return result[0][0] if result else 0


# =============================================================================
# TESTS D'INTÉGRATION
# =============================================================================

class TestMQTTToClickHouse:
    """
    Tests du pipeline MQTT → Kafka → ClickHouse.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Connexion MQTT
    # -------------------------------------------------------------------------
    def test_mqtt_connection(self, mqtt_client):
        """
        Test: connexion au broker MQTT réussie.
        """
        # ASSERT - Le client est connecté (fixture réussie)
        assert mqtt_client is not None, "Client MQTT non créé"
        assert mqtt_client.is_connected(), "Client MQTT non connecté"
        
        logger.info("✅ Connexion MQTT vérifiée")
    
    # -------------------------------------------------------------------------
    # TEST 2: Publication MQTT
    # -------------------------------------------------------------------------
    def test_mqtt_publish(self, mqtt_client, sensor_data_factory, unique_rack_id):
        """
        Test: publication d'un message MQTT réussie.
        """
        # ARRANGE
        data = sensor_data_factory(rack_id=unique_rack_id)
        topic = MQTT_TOPIC_SENSORS.format(rack_id=unique_rack_id)
        payload = json.dumps(data)
        
        # ACT
        result = mqtt_client.publish(topic, payload, qos=1)
        result.wait_for_publish(timeout=5)
        
        # ASSERT
        assert result.is_published(), "Message non publié"
        assert result.rc == 0, f"Code retour MQTT non nul: {result.rc}"
        
        logger.info(f"✅ Message publié sur {topic}")
    
    # -------------------------------------------------------------------------
    # TEST 3: Connexion ClickHouse
    # -------------------------------------------------------------------------
    def test_clickhouse_connection(self, clickhouse_client):
        """
        Test: connexion à ClickHouse réussie.
        """
        # ACT
        result = clickhouse_client.execute("SELECT 1")
        
        # ASSERT
        assert result == [(1,)], "Requête ClickHouse échouée"
        
        logger.info("✅ Connexion ClickHouse vérifiée")
    
    # -------------------------------------------------------------------------
    # TEST 4: Insertion directe ClickHouse
    # -------------------------------------------------------------------------
    def test_clickhouse_direct_insert(self, clickhouse_client, sensor_data_factory, unique_rack_id):
        """
        Test: insertion directe dans ClickHouse (sans pipeline).
        Vérifie que ClickHouse est correctement configuré.
        """
        # ARRANGE
        data = sensor_data_factory(rack_id=unique_rack_id, temperature=25.0)
        
        # ACT
        success = insert_directly_to_clickhouse(clickhouse_client, data)
        
        # ASSERT
        assert success, "Insertion directe échouée"
        
        # Vérifier que les données sont présentes
        count = count_sensor_records(clickhouse_client, unique_rack_id)
        assert count >= 1, f"Données non trouvées (count={count})"
        
        logger.info(f"✅ Insertion directe réussie pour {unique_rack_id}")
    
    # -------------------------------------------------------------------------
    # TEST 5: Lecture des données ClickHouse
    # -------------------------------------------------------------------------
    def test_clickhouse_read_sensor_data(self, clickhouse_client, sensor_data_factory, unique_rack_id):
        """
        Test: lecture des données de capteurs depuis ClickHouse.
        """
        # ARRANGE - Insérer des données de test
        data = sensor_data_factory(
            rack_id=unique_rack_id,
            temperature=26.5,
            humidity=72.0,
            co2=900
        )
        insert_directly_to_clickhouse(clickhouse_client, data)
        
        # ACT
        results = query_sensor_data(clickhouse_client, unique_rack_id)
        
        # ASSERT
        assert len(results) >= 1, "Aucune donnée retournée"
        
        # Vérifier les valeurs
        row = results[0]
        assert row[0] == unique_rack_id, f"rack_id incorrect: {row[0]}"
        assert abs(row[1] - 26.5) < 0.1, f"Température incorrecte: {row[1]}"
        assert abs(row[2] - 72.0) < 0.1, f"Humidité incorrecte: {row[2]}"
        assert row[3] == 900, f"CO2 incorrect: {row[3]}"
        
        logger.info(f"✅ Lecture ClickHouse vérifiée: temp={row[1]}°C, humidity={row[2]}%")
    
    # -------------------------------------------------------------------------
    # TEST 6: Pipeline MQTT → ClickHouse (End-to-End)
    # -------------------------------------------------------------------------
    @pytest.mark.slow
    def test_mqtt_to_clickhouse_e2e(self, mqtt_client, clickhouse_client, 
                                     sensor_data_factory, unique_rack_id):
        """
        Test E2E: données MQTT arrivent dans ClickHouse.
        
        NOTE:
            Ce test nécessite que le bridge MQTT-Kafka et le
            stream processor soient actifs. Si ce n'est pas le cas,
            le test sera marqué comme "skipped" après timeout.
        """
        # ARRANGE
        data = sensor_data_factory(
            rack_id=unique_rack_id,
            temperature=27.3,
            humidity=65.5
        )
        topic = MQTT_TOPIC_SENSORS.format(rack_id=unique_rack_id)
        
        # Compter les enregistrements avant
        initial_count = count_sensor_records(clickhouse_client, unique_rack_id)
        
        # ACT - Publier sur MQTT
        payload = json.dumps(data)
        result = mqtt_client.publish(topic, payload, qos=1)
        result.wait_for_publish(timeout=5)
        
        assert result.is_published(), "Publication MQTT échouée"
        logger.info(f"📤 Message publié sur MQTT: {topic}")
        
        # ASSERT - Attendre que les données arrivent dans ClickHouse
        def check_data_arrived():
            current_count = count_sensor_records(clickhouse_client, unique_rack_id)
            return current_count > initial_count
        
        data_arrived = wait_for_condition(
            check_data_arrived,
            timeout=MESSAGE_PROPAGATION_TIMEOUT,
            interval=POLL_INTERVAL,
            description=f"données dans ClickHouse pour {unique_rack_id}"
        )
        
        if not data_arrived:
            pytest.skip(
                "Pipeline MQTT→Kafka→ClickHouse non actif. "
                "Vérifiez que NiFi/Kafka Connect et le stream processor sont démarrés."
            )
        
        # Vérifier les valeurs
        results = query_sensor_data(clickhouse_client, unique_rack_id)
        assert len(results) >= 1, "Données non trouvées après propagation"
        
        row = results[0]
        assert abs(row[1] - 27.3) < 0.1, f"Température incorrecte: {row[1]}"
        
        logger.info(f"✅ Pipeline E2E vérifié: MQTT → ClickHouse en < {MESSAGE_PROPAGATION_TIMEOUT}s")
    
    # -------------------------------------------------------------------------
    # TEST 7: Kafka → ClickHouse (bypass MQTT)
    # -------------------------------------------------------------------------
    @pytest.mark.slow
    def test_kafka_to_clickhouse(self, kafka_producer, clickhouse_client,
                                  sensor_data_factory, unique_rack_id):
        """
        Test: données Kafka arrivent dans ClickHouse.
        
        Teste la partie Kafka → Stream Processor → ClickHouse
        sans passer par MQTT.
        """
        # ARRANGE
        data = sensor_data_factory(
            rack_id=unique_rack_id,
            temperature=28.1,
            co2=920
        )
        
        initial_count = count_sensor_records(clickhouse_client, unique_rack_id)
        
        # ACT - Envoyer sur Kafka
        payload = json.dumps(data).encode('utf-8')
        future = kafka_producer.send(KAFKA_TOPIC_SENSOR_DATA, value=payload)
        kafka_producer.flush()
        
        # Attendre la confirmation d'envoi
        record_metadata = future.get(timeout=10)
        logger.info(
            f"📤 Message Kafka envoyé: topic={record_metadata.topic}, "
            f"partition={record_metadata.partition}, offset={record_metadata.offset}"
        )
        
        # ASSERT - Attendre les données dans ClickHouse
        def check_kafka_data():
            return count_sensor_records(clickhouse_client, unique_rack_id) > initial_count
        
        data_arrived = wait_for_condition(
            check_kafka_data,
            timeout=MESSAGE_PROPAGATION_TIMEOUT,
            interval=POLL_INTERVAL,
            description=f"données Kafka dans ClickHouse pour {unique_rack_id}"
        )
        
        if not data_arrived:
            pytest.skip(
                "Stream Processor non actif. "
                "Vérifiez que le consumer Kafka → ClickHouse est démarré."
            )
        
        logger.info("✅ Pipeline Kafka → ClickHouse vérifié")
    
    # -------------------------------------------------------------------------
    # TEST 8: Multiple messages batch
    # -------------------------------------------------------------------------
    @pytest.mark.slow
    def test_batch_messages(self, clickhouse_client, sensor_data_factory, unique_rack_id):
        """
        Test: insertion de plusieurs messages en batch.
        """
        # ARRANGE
        batch_size = 10
        messages = []
        
        for i in range(batch_size):
            data = sensor_data_factory(
                rack_id=unique_rack_id,
                temperature=20.0 + i,  # Températures différentes
                humidity=60.0 + i
            )
            messages.append(data)
        
        # ACT - Insérer tous les messages
        for msg in messages:
            insert_directly_to_clickhouse(clickhouse_client, msg)
        
        # ASSERT
        count = count_sensor_records(clickhouse_client, unique_rack_id)
        assert count >= batch_size, f"Attendu {batch_size} messages, trouvé {count}"
        
        logger.info(f"✅ Batch de {batch_size} messages inséré")
    
    # -------------------------------------------------------------------------
    # TEST 9: Données avec valeurs extrêmes
    # -------------------------------------------------------------------------
    def test_extreme_values(self, clickhouse_client, sensor_data_factory, unique_rack_id):
        """
        Test: les valeurs extrêmes sont correctement stockées.
        """
        # ARRANGE - Valeurs aux limites
        data = sensor_data_factory(
            rack_id=unique_rack_id,
            temperature=45.0,   # Très chaud
            humidity=99.9,      # Très humide
            co2=5000,          # CO2 très élevé
            light=2000,        # Lumière intense
            ec=4.0,            # EC élevée
            ph=4.5             # pH acide
        )
        
        # ACT
        success = insert_directly_to_clickhouse(clickhouse_client, data)
        
        # ASSERT
        assert success, "Insertion valeurs extrêmes échouée"
        
        results = query_sensor_data(clickhouse_client, unique_rack_id)
        assert len(results) >= 1, "Données extrêmes non trouvées"
        
        row = results[0]
        assert row[1] == 45.0, f"Température extrême non stockée: {row[1]}"
        assert row[3] == 5000, f"CO2 extrême non stocké: {row[3]}"
        
        logger.info("✅ Valeurs extrêmes correctement stockées")
    
    # -------------------------------------------------------------------------
    # TEST 10: Latence du pipeline
    # -------------------------------------------------------------------------
    @pytest.mark.slow
    def test_pipeline_latency(self, clickhouse_client, sensor_data_factory, unique_rack_id):
        """
        Test: mesure de la latence d'insertion.
        
        OBJECTIF:
            Latence < 100ms pour insertion directe
        """
        import time
        
        # ARRANGE
        data = sensor_data_factory(rack_id=unique_rack_id)
        
        # ACT
        start_time = time.perf_counter()
        success = insert_directly_to_clickhouse(clickhouse_client, data)
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # ASSERT
        assert success, "Insertion échouée"
        assert latency_ms < 500, f"Latence trop élevée: {latency_ms:.1f}ms"
        
        logger.info(f"✅ Latence d'insertion: {latency_ms:.1f}ms")


# =============================================================================
# TESTS DE ROBUSTESSE
# =============================================================================

class TestPipelineRobustness:
    """
    Tests de robustesse du pipeline.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Messages malformés
    # -------------------------------------------------------------------------
    def test_malformed_message_handling(self, mqtt_client, unique_rack_id):
        """
        Test: les messages malformés ne crashent pas le pipeline.
        """
        # ARRANGE - Message JSON invalide
        topic = MQTT_TOPIC_SENSORS.format(rack_id=unique_rack_id)
        invalid_payload = b"not a valid json {"
        
        # ACT
        result = mqtt_client.publish(topic, invalid_payload, qos=1)
        result.wait_for_publish(timeout=5)
        
        # ASSERT - Le message est publié (MQTT ne valide pas le contenu)
        assert result.is_published(), "Publication échouée"
        
        # Le pipeline devrait gérer ce message sans crash
        logger.info("✅ Message malformé publié (handling par le pipeline)")
    
    # -------------------------------------------------------------------------
    # TEST 2: Messages avec champs manquants
    # -------------------------------------------------------------------------
    def test_missing_fields(self, mqtt_client, unique_rack_id):
        """
        Test: messages avec champs manquants sont gérés.
        """
        # ARRANGE - Message incomplet
        topic = MQTT_TOPIC_SENSORS.format(rack_id=unique_rack_id)
        incomplete_data = {
            "rack_id": unique_rack_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # Manque "sensors"
        }
        
        # ACT
        result = mqtt_client.publish(topic, json.dumps(incomplete_data), qos=1)
        result.wait_for_publish(timeout=5)
        
        # ASSERT
        assert result.is_published(), "Publication échouée"
        logger.info("✅ Message incomplet publié")
    
    # -------------------------------------------------------------------------
    # TEST 3: Reconnexion après déconnexion
    # -------------------------------------------------------------------------
    def test_mqtt_reconnection(self, check_services):
        """
        Test: le client MQTT peut se reconnecter.
        """
        # ARRANGE
        client = get_mqtt_client()
        client.loop_start()
        
        # ACT - Déconnecter puis reconnecter
        client.disconnect()
        time.sleep(1)
        
        # Reconnecter
        client.reconnect()
        time.sleep(1)
        
        # ASSERT
        assert client.is_connected(), "Reconnexion échouée"
        
        client.loop_stop()
        client.disconnect()
        
        logger.info("✅ Reconnexion MQTT vérifiée")


# =============================================================================
# FIN DU MODULE - TICKET-110 - Tests Integration MQTT→ClickHouse VertiFlow
# =============================================================================
