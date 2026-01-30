#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
MODULE: vertiflow_constants.py
DESCRIPTION: Constantes centralisees pour harmoniser tout le projet.
             Ce fichier est la SOURCE DE VERITE pour tous les noms de:
             - Topics Kafka
             - Tables/Vues ClickHouse
             - Collections MongoDB
             - Schemas JSON

Developpe par       : VertiFlow Core Team
Ticket(s) associe(s): TICKET-005 (Hygiene du Code)
================================================================================
"""

import os

# =============================================================================
# KAFKA TOPICS (Source de verite)
# =============================================================================
# Ces noms doivent correspondre a init_infrastructure.py

class KafkaTopics:
    """Noms des topics Kafka utilises dans le projet."""

    # Topic principal - Telemetrie complete (157 colonnes)
    TELEMETRY_FULL = "basil_telemetry_full"

    # Topic de commandes vers les actionneurs IoT
    COMMANDS = "vertiflow.commands"

    # Topic d'alertes prioritaires
    ALERTS = "vertiflow.alerts"

    # Dead Letter Queue (erreurs NiFi)
    DLQ = "dead_letter_queue"

    # Predictions de qualite (Algo A10)
    QUALITY_PREDICTIONS = "vertiflow.quality_predictions"

    # Mises a jour des recettes (Algo A11)
    RECIPE_UPDATES = "vertiflow.recipe_updates"


# =============================================================================
# CLICKHOUSE TABLES & VIEWS (Source de verite)
# =============================================================================

class ClickHouseTables:
    """Noms des tables ClickHouse."""

    # Base de donnees
    DATABASE = "vertiflow"

    # Table principale - Golden Record 157 colonnes
    MAIN_TABLE = "basil_ultimate_realtime"

    # Tables externes
    WEATHER_HISTORY = "ext_weather_history"
    ENERGY_MARKET = "ext_energy_market"
    PLANT_RECIPES = "ref_plant_recipes"
    LAND_REGISTRY = "ext_land_registry"
    MARKET_PRICES = "ext_market_prices"


class ClickHouseViews:
    """Noms des vues Power BI."""

    OPERATIONAL_COCKPIT = "view_pbi_operational_cockpit"
    SCIENCE_LAB = "view_pbi_science_lab"
    EXECUTIVE_FINANCE = "view_pbi_executive_finance"
    ANOMALIES_LOG = "view_pbi_anomalies_log"
    CROP_CYCLE = "view_pbi_crop_cycle_analysis"
    VERTICAL_ENERGY = "view_pbi_vertical_energy_efficiency"
    DISEASE_WARNING = "view_pbi_disease_early_warning"
    NUTRIENT_BALANCE = "view_pbi_nutrient_balance"
    LABOR_EFFICIENCY = "view_pbi_labor_efficiency"
    COMPLIANCE_AUDIT = "view_pbi_compliance_audit"
    LIVE_INVENTORY = "view_pbi_live_inventory"


# =============================================================================
# MONGODB COLLECTIONS (Source de verite)
# =============================================================================

class MongoDBCollections:
    """Noms des collections MongoDB."""

    # Base de donnees
    DATABASE = "vertiflow_ops"

    # Collections
    LIVE_STATE = "live_state"
    INCIDENT_LOGS = "incident_logs"
    PLANT_RECIPES = "plant_recipes"
    QUALITY_PREDICTIONS = "quality_predictions"
    RECIPE_OPTIMIZATIONS = "recipe_optimizations"


# =============================================================================
# MQTT TOPICS (Source de verite)
# =============================================================================

class MQTTTopics:
    """Patterns des topics MQTT."""

    # Pattern de base pour la telemetrie
    TELEMETRY_BASE = "vertiflow/telemetry"

    # Pattern avec wildcards pour NiFi
    TELEMETRY_FILTER = "vertiflow/telemetry/#"

    # Format: vertiflow/telemetry/{rack_id}/{module_id}


# =============================================================================
# INFRASTRUCTURE (Hosts et Ports)
# =============================================================================

class Infrastructure:
    """Configuration de l'infrastructure."""

    # ClickHouse
    CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 9000))
    CLICKHOUSE_HTTP_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", 8123))

    # MongoDB
    MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
    MONGODB_PORT = int(os.getenv("MONGODB_PORT", 27017))
    MONGODB_URI = os.getenv("MONGODB_URI", f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_INTERNAL_SERVERS = os.getenv("KAFKA_INTERNAL_SERVERS", "kafka:29092")

    # MQTT (Mosquitto)
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

    # NiFi
    NIFI_URL = os.getenv("NIFI_URL", "https://localhost:8443/nifi")


# =============================================================================
# ALGORITHMES (Identification)
# =============================================================================

class Algorithms:
    """Identifiants des algorithmes scientifiques."""

    A1_JSON_NORMALIZATION = "A1"
    A2_ZSCORE_OUTLIER = "A2"
    A3_CONTEXTUAL_ENRICHMENT = "A3"
    A4_DYNAMIC_THRESHOLDING = "A4"
    A5_RULE_ENGINE = "A5"
    A6_TEMPORAL_AGGREGATION = "A6"
    A7_PEARSON_CORRELATION = "A7"
    A8_ANOVA_SEGMENTATION = "A8"
    A9_LSTM_PREDICTION = "A9"  # oracle.py
    A10_RF_CLASSIFICATION = "A10"  # classifier.py
    A11_OPTIMIZATION = "A11"  # cortex.py


# =============================================================================
# ZONES ET FARM IDS
# =============================================================================

class FarmConfig:
    """Configuration par defaut de la ferme."""

    DEFAULT_FARM_ID = "VERT-MAROC-01"

    ZONES = ["ZONE_A", "ZONE_B", "NURSERY", "ZONE_GERMINATION", "ZONE_CROISSANCE"]

    RACKS = ["R01", "R02", "R03", "R04", "R05"]

    MODULES_PER_RACK = 4


# =============================================================================
# QUALITY GRADES
# =============================================================================

class QualityGrades:
    """Grades de qualite pour la classification (Algo A10)."""

    PREMIUM = "PREMIUM"
    STANDARD = "STANDARD"
    REJECT = "REJECT"


# =============================================================================
# GROWTH STAGES
# =============================================================================

class GrowthStages:
    """Stades de croissance des plantes."""

    SEEDLING = "Semis"
    VEGETATIVE = "Vegetatif"
    FLOWERING = "Bouton"
    HARVEST = "Recolte"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_kafka_topic(topic_name: str) -> str:
    """Retourne le nom complet du topic Kafka."""
    topics = {
        "telemetry": KafkaTopics.TELEMETRY_FULL,
        "commands": KafkaTopics.COMMANDS,
        "alerts": KafkaTopics.ALERTS,
        "dlq": KafkaTopics.DLQ,
        "quality": KafkaTopics.QUALITY_PREDICTIONS,
        "recipes": KafkaTopics.RECIPE_UPDATES,
    }
    return topics.get(topic_name, topic_name)


def get_clickhouse_table(table_name: str) -> str:
    """Retourne le nom complet de la table ClickHouse avec database."""
    return f"{ClickHouseTables.DATABASE}.{table_name}"
