# ============================================================================
# VERTIFLOW - Configuration Pytest
# ============================================================================
# Fixtures partagées pour tous les tests
# ============================================================================

import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, Generator

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Fixtures de configuration
# =============================================================================

@pytest.fixture(scope="session")
def project_root() -> str:
    """Retourne le chemin racine du projet."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def config_dir(project_root: str) -> str:
    """Retourne le chemin du répertoire de configuration."""
    return os.path.join(project_root, "config")


@pytest.fixture
def sample_env_vars() -> Dict[str, str]:
    """Variables d'environnement de test."""
    return {
        "CLICKHOUSE_HOST": "localhost",
        "CLICKHOUSE_PORT": "9000",
        "CLICKHOUSE_USER": "default",
        "CLICKHOUSE_PASSWORD": "test",
        "CLICKHOUSE_DATABASE": "vertiflow_test",
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "27017",
        "MONGODB_DATABASE": "vertiflow_test",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "MQTT_HOST": "localhost",
        "MQTT_PORT": "1883",
    }


# =============================================================================
# Fixtures de données de test
# =============================================================================

@pytest.fixture
def sample_telemetry_data() -> Dict[str, Any]:
    """Données de télémétrie de test."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "farm_id": "FARM_001",
        "zone_id": "ZONE_A",
        "rack_id": "RACK_01",
        "sensor_id": "SENSOR_TEMP_001",
        "sensor_type": "temperature",
        "value": 23.5,
        "unit": "celsius",
        "quality_score": 0.98,
        "metadata": {
            "firmware_version": "1.2.3",
            "battery_level": 85
        }
    }


@pytest.fixture
def sample_batch_telemetry(sample_telemetry_data: Dict[str, Any]) -> list:
    """Batch de données de télémétrie."""
    batch = []
    base_time = datetime.utcnow()

    for i in range(100):
        data = sample_telemetry_data.copy()
        data["timestamp"] = (base_time + timedelta(seconds=i * 30)).isoformat()
        data["value"] = 20 + (i % 10) * 0.5
        data["sensor_id"] = f"SENSOR_TEMP_{i % 10:03d}"
        batch.append(data)

    return batch


@pytest.fixture
def sample_command_data() -> Dict[str, Any]:
    """Données de commande de test."""
    return {
        "command_id": "CMD_001",
        "timestamp": datetime.utcnow().isoformat(),
        "farm_id": "FARM_001",
        "zone_id": "ZONE_A",
        "actuator_id": "ACTUATOR_LED_001",
        "command_type": "set_intensity",
        "parameters": {
            "intensity": 75,
            "duration_minutes": 120
        },
        "priority": "normal",
        "source": "cortex_optimizer"
    }


@pytest.fixture
def sample_plant_recipe() -> Dict[str, Any]:
    """Recette de culture de test."""
    return {
        "recipe_id": "RECIPE_BASIL_001",
        "plant_type": "basil",
        "variety": "genovese",
        "growth_stages": [
            {
                "stage": "germination",
                "duration_days": 7,
                "targets": {
                    "temperature_min": 20,
                    "temperature_max": 25,
                    "humidity_min": 70,
                    "humidity_max": 80,
                    "light_hours": 16,
                    "ppfd": 150
                }
            },
            {
                "stage": "vegetative",
                "duration_days": 21,
                "targets": {
                    "temperature_min": 22,
                    "temperature_max": 28,
                    "humidity_min": 60,
                    "humidity_max": 70,
                    "light_hours": 16,
                    "ppfd": 400
                }
            }
        ],
        "nutrient_profile": {
            "nitrogen": 150,
            "phosphorus": 50,
            "potassium": 200,
            "ec_target": 1.8,
            "ph_target": 6.0
        }
    }


# =============================================================================
# Fixtures Mock des services
# =============================================================================

@pytest.fixture
def mock_clickhouse():
    """Mock du client ClickHouse."""
    mock = MagicMock()
    mock.execute.return_value = []
    mock.execute_with_progress.return_value = []
    return mock


@pytest.fixture
def mock_mongodb():
    """Mock du client MongoDB."""
    mock = MagicMock()
    mock.find.return_value = []
    mock.find_one.return_value = None
    mock.insert_one.return_value = MagicMock(inserted_id="test_id")
    mock.insert_many.return_value = MagicMock(inserted_ids=["id1", "id2"])
    return mock


@pytest.fixture
def mock_kafka_producer():
    """Mock du producteur Kafka."""
    mock = MagicMock()
    mock.send.return_value = MagicMock()
    mock.flush.return_value = None
    return mock


@pytest.fixture
def mock_kafka_consumer():
    """Mock du consommateur Kafka."""
    mock = MagicMock()
    mock.__iter__ = MagicMock(return_value=iter([]))
    return mock


@pytest.fixture
def mock_mqtt_client():
    """Mock du client MQTT."""
    mock = MagicMock()
    mock.connect.return_value = 0
    mock.publish.return_value = MagicMock(rc=0)
    mock.subscribe.return_value = (0, 1)
    return mock


# =============================================================================
# Fixtures pour les tests ML
# =============================================================================

@pytest.fixture
def sample_features_for_prediction() -> Dict[str, float]:
    """Features pour la prédiction ML."""
    return {
        "temperature_avg": 24.5,
        "humidity_avg": 65.0,
        "co2_ppm": 800,
        "ppfd_avg": 350,
        "vpd": 1.2,
        "ec": 1.8,
        "ph": 6.0,
        "days_since_germination": 21,
        "light_hours_cumulative": 336,
        "dli_cumulative": 12.6
    }


@pytest.fixture
def sample_agronomic_parameters() -> Dict[str, Any]:
    """Paramètres agronomiques de test."""
    return {
        "basil": {
            "optimal_temperature": {"min": 20, "max": 28, "optimal": 24},
            "optimal_humidity": {"min": 50, "max": 70, "optimal": 60},
            "optimal_co2": {"min": 400, "max": 1200, "optimal": 800},
            "optimal_ppfd": {"min": 200, "max": 600, "optimal": 400},
            "growth_rate": 0.05,
            "harvest_days": 35
        }
    }
