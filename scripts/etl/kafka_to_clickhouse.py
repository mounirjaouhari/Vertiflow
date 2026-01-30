#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
MODULE: kafka_to_clickhouse.py
DESCRIPTION: ETL simplifié Kafka → ClickHouse pour le Golden Record (157 colonnes).
             Consomme depuis basil_telemetry_full et insère dans basil_ultimate_realtime.

Pipeline: Kafka (basil_telemetry_full) → ETL → ClickHouse (basil_ultimate_realtime)

Développé par       : VertiFlow Core Team
Ticket(s) associé(s): TICKET-051
================================================================================
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
except ImportError:
    print("[ERROR] kafka-python non installé. Exécuter: pip install kafka-python")
    sys.exit(1)

try:
    from clickhouse_driver import Client as ClickHouseClient
except ImportError:
    print("[ERROR] clickhouse-driver non installé. Exécuter: pip install clickhouse-driver")
    sys.exit(1)

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ETL] - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VertiFlowETL")

# Kafka Configuration (via environnement ou défauts)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "basil_telemetry_full")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "vertiflow-etl-clickhouse")

# ClickHouse Configuration (via environnement ou défauts)
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "9000"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "default")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DATABASE", "vertiflow")
CLICKHOUSE_TABLE = os.getenv("CLICKHOUSE_TABLE", "basil_ultimate_realtime")

# Batch Configuration
BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", "100"))
FLUSH_INTERVAL_SECONDS = int(os.getenv("ETL_FLUSH_INTERVAL", "5"))


class GracefulKiller:
    """Gestion propre des signaux d'arrêt."""
    def __init__(self):
        self.should_stop = False
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

    def _exit_gracefully(self, *args):
        logger.warning("Signal d'arrêt reçu. Finalisation en cours...")
        self.should_stop = True


class KafkaToClickHouseETL:
    """ETL pour transférer les données de Kafka vers ClickHouse."""

    # Mapping des colonnes ClickHouse (ordre important pour l'insertion)
    COLUMNS = [
        "timestamp", "farm_id", "parcel_id", "latitude", "longitude", "zone_id",
        "rack_id", "level_index", "module_id", "batch_id", "species_variety",
        "position_x_y", "structural_weight_load",
        # Nutrition
        "nutrient_n_total", "nutrient_p_phosphorus", "nutrient_k_potassium",
        "nutrient_ca_calcium", "nutrient_mg_magnesium", "nutrient_s_sulfur",
        "nutrient_fe_iron", "nutrient_mn_manganese", "nutrient_zn_zinc",
        "nutrient_cu_copper", "nutrient_b_boron", "nutrient_mo_molybdenum",
        "nutrient_cl_chlorine", "nutrient_ni_nickel", "nutrient_solution_ec",
        # Photosynthèse
        "light_intensity_ppfd", "light_compensation_point", "light_saturation_point",
        "light_ratio_red_blue", "light_far_red_intensity", "light_dli_accumulated",
        "light_photoperiod", "quantum_yield_psii", "photosynthetic_rate_max",
        "co2_level_ambient", "co2_consumption_rate", "night_respiration_rate",
        "light_use_efficiency", "leaf_absorption_pct", "spectral_recipe_id",
        # Biomasse
        "fresh_biomass_est", "dry_biomass_est", "leaf_area_index_lai",
        "root_shoot_ratio", "relative_growth_rate", "net_assimilation_rate",
        "canopy_height", "harvest_index", "days_since_planting",
        "thermal_sum_accumulated", "growth_stage", "predicted_yield_kg_m2",
        "expected_harvest_date", "biomass_accumulation_daily", "target_harvest_weight",
        # Physiologie
        "health_score", "chlorophyll_index_spad", "stomatal_conductance",
        "anthocyanin_index", "tip_burn_risk", "leaf_temp_delta", "stem_diameter_micro",
        "sap_flow_rate", "leaf_wetness_duration", "potential_hydrique_foliaire",
        "ethylene_level", "ascorbic_acid_content", "phenolic_content",
        "essential_oil_yield", "aroma_compounds_ratio",
        # Environnement
        "air_temp_internal", "air_humidity", "vapor_pressure_deficit",
        "airflow_velocity", "air_pressure", "fan_speed_pct", "ext_temp_nasa",
        "ext_humidity_nasa", "ext_solar_radiation", "oxygen_level", "dew_point",
        "hvac_load_pct", "co2_injection_status", "energy_footprint_hourly",
        "renewable_energy_pct", "ambient_light_pollution",
        # Rhizosphère
        "water_temp", "water_ph", "dissolved_oxygen", "water_turbidity",
        "wue_current", "water_recycled_rate", "coefficient_cultural_kc",
        "microbial_density", "beneficial_microbes_ratio", "root_fungal_pressure",
        "biofilm_thickness", "algae_growth_index", "redox_potential",
        "irrigation_line_pressure", "leaching_fraction",
        # Économie
        "energy_price_kwh", "market_price_kg", "lease_index_value", "daily_rent_cost",
        "lease_profitability_index", "is_compliant_lease", "labor_cost_pro_rata",
        "carbon_credit_value", "operational_cost_total", "carbon_footprint_per_kg",
        # Hardware
        "pump_vibration_level", "fan_current_draw", "led_driver_temp",
        "filter_differential_pressure", "ups_battery_health", "leak_detection_status",
        "emergency_stop_status", "network_latency_ms", "sensor_calibration_offset",
        "module_integrity_score",
        # Intelligence
        "ai_decision_mode", "anomaly_confidence_score", "predicted_energy_need_24h",
        "risk_pest_outbreak", "irrigation_strategy_id", "master_compliance_index",
        "blockchain_hash", "audit_trail_signature", "quality_grade_prediction",
        "system_reboot_count",
        # Cibles
        "ref_n_target", "ref_p_target", "ref_k_target", "ref_ca_target",
        "ref_mg_target", "ref_temp_opt", "ref_lai_target", "ref_oil_target",
        "ref_wue_target", "ref_microbial_target", "ref_photoperiod_opt",
        "ref_sum_thermal_target", "ref_brix_target", "ref_nitrate_limit",
        "ref_humidity_opt",
        # Traçabilité
        "data_source_type", "sensor_hardware_id", "api_endpoint_version",
        "source_reliability_score", "data_integrity_flag", "last_calibration_date",
        "maintenance_urgency_score", "lineage_uuid"
    ]

    # Mapping des growth_stage vers les valeurs Enum
    GROWTH_STAGE_MAP = {
        "Semis": 1, "Végétatif": 2, "Bouton": 3, "Récolte": 4
    }

    # Mapping des quality_grade vers les valeurs Enum
    QUALITY_GRADE_MAP = {
        "Premium": 1, "Standard": 2, "Rejet": 3
    }

    # Mapping des data_source_type vers les valeurs Enum
    DATA_SOURCE_MAP = {
        "IoT": 1, "API": 2, "ML": 3, "Lab": 4
    }

    def __init__(self):
        self.consumer: Optional[KafkaConsumer] = None
        self.ch_client: Optional[ClickHouseClient] = None
        self.batch: List[tuple] = []
        self.last_flush_time = time.time()
        self.total_inserted = 0

    def connect(self) -> bool:
        """Établit les connexions Kafka et ClickHouse."""
        # Connexion Kafka
        try:
            self.consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                max_poll_records=BATCH_SIZE
            )
            logger.info(f"Connecté à Kafka: {KAFKA_BOOTSTRAP}, topic: {KAFKA_TOPIC}")
        except KafkaError as e:
            logger.error(f"Erreur connexion Kafka: {e}")
            return False

        # Connexion ClickHouse
        try:
            self.ch_client = ClickHouseClient(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                user=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASSWORD,
                database=CLICKHOUSE_DB
            )
            # Test de connexion
            result = self.ch_client.execute("SELECT 1")
            logger.info(f"Connecté à ClickHouse: {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/{CLICKHOUSE_DB}")
        except Exception as e:
            logger.error(f"Erreur connexion ClickHouse: {e}")
            return False

        return True

    def transform_record(self, record: Dict[str, Any]) -> tuple:
        """Transforme un record JSON en tuple pour insertion ClickHouse."""
        # Parsing du timestamp
        ts = record.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        # Transformation des Enums
        growth_stage = self.GROWTH_STAGE_MAP.get(record.get("growth_stage", "Végétatif"), 2)
        quality_grade = self.QUALITY_GRADE_MAP.get(record.get("quality_grade_prediction", "Standard"), 2)
        data_source = self.DATA_SOURCE_MAP.get(record.get("data_source_type", "IoT"), 1)

        # Parsing de la date de récolte prévue
        expected_harvest = record.get("expected_harvest_date", "2026-01-01")
        if isinstance(expected_harvest, str):
            try:
                expected_harvest = datetime.strptime(expected_harvest, "%Y-%m-%d").date()
            except ValueError:
                expected_harvest = datetime.now().date()

        # Parsing de la date de calibration
        last_calibration = record.get("last_calibration_date", "2026-01-01")
        if isinstance(last_calibration, str):
            try:
                last_calibration = datetime.strptime(last_calibration, "%Y-%m-%d").date()
            except ValueError:
                last_calibration = datetime.now().date()

        # Construction du tuple dans l'ordre des colonnes
        return (
            ts,
            record.get("farm_id", ""),
            record.get("parcel_id", ""),
            record.get("latitude", 0.0),
            record.get("longitude", 0.0),
            record.get("zone_id", ""),
            record.get("rack_id", ""),
            record.get("level_index", 1),
            record.get("module_id", ""),
            record.get("batch_id", ""),
            record.get("species_variety", ""),
            record.get("position_x_y", ""),
            record.get("structural_weight_load", 0.0),
            # Nutrition
            record.get("nutrient_n_total", 0.0),
            record.get("nutrient_p_phosphorus", 0.0),
            record.get("nutrient_k_potassium", 0.0),
            record.get("nutrient_ca_calcium", 0.0),
            record.get("nutrient_mg_magnesium", 0.0),
            record.get("nutrient_s_sulfur", 0.0),
            record.get("nutrient_fe_iron", 0.0),
            record.get("nutrient_mn_manganese", 0.0),
            record.get("nutrient_zn_zinc", 0.0),
            record.get("nutrient_cu_copper", 0.0),
            record.get("nutrient_b_boron", 0.0),
            record.get("nutrient_mo_molybdenum", 0.0),
            record.get("nutrient_cl_chlorine", 0.0),
            record.get("nutrient_ni_nickel", 0.0),
            record.get("nutrient_solution_ec", 0.0),
            # Photosynthèse
            record.get("light_intensity_ppfd", 0.0),
            record.get("light_compensation_point", 0.0),
            record.get("light_saturation_point", 0.0),
            record.get("light_ratio_red_blue", 0.0),
            record.get("light_far_red_intensity", 0.0),
            record.get("light_dli_accumulated", 0.0),
            record.get("light_photoperiod", 0.0),
            record.get("quantum_yield_psii", 0.0),
            record.get("photosynthetic_rate_max", 0.0),
            record.get("co2_level_ambient", 0),
            record.get("co2_consumption_rate", 0.0),
            record.get("night_respiration_rate", 0.0),
            record.get("light_use_efficiency", 0.0),
            record.get("leaf_absorption_pct", 0.0),
            record.get("spectral_recipe_id", ""),
            # Biomasse
            record.get("fresh_biomass_est", 0.0),
            record.get("dry_biomass_est", 0.0),
            record.get("leaf_area_index_lai", 0.0),
            record.get("root_shoot_ratio", 0.0),
            record.get("relative_growth_rate", 0.0),
            record.get("net_assimilation_rate", 0.0),
            record.get("canopy_height", 0.0),
            record.get("harvest_index", 0.0),
            record.get("days_since_planting", 0),
            record.get("thermal_sum_accumulated", 0.0),
            growth_stage,
            record.get("predicted_yield_kg_m2", 0.0),
            expected_harvest,
            record.get("biomass_accumulation_daily", 0.0),
            record.get("target_harvest_weight", 0.0),
            # Physiologie
            record.get("health_score", 0.0),
            record.get("chlorophyll_index_spad", 0.0),
            record.get("stomatal_conductance", 0.0),
            record.get("anthocyanin_index", 0.0),
            record.get("tip_burn_risk", 0.0),
            record.get("leaf_temp_delta", 0.0),
            record.get("stem_diameter_micro", 0.0),
            record.get("sap_flow_rate", 0.0),
            record.get("leaf_wetness_duration", 0.0),
            record.get("potential_hydrique_foliaire", 0.0),
            record.get("ethylene_level", 0.0),
            record.get("ascorbic_acid_content", 0.0),
            record.get("phenolic_content", 0.0),
            record.get("essential_oil_yield", 0.0),
            record.get("aroma_compounds_ratio", 0.0),
            # Environnement
            record.get("air_temp_internal", 0.0),
            record.get("air_humidity", 0.0),
            record.get("vapor_pressure_deficit", 0.0),
            record.get("airflow_velocity", 0.0),
            record.get("air_pressure", 0.0),
            record.get("fan_speed_pct", 0.0),
            record.get("ext_temp_nasa", 0.0),
            record.get("ext_humidity_nasa", 0.0),
            record.get("ext_solar_radiation", 0.0),
            record.get("oxygen_level", 0.0),
            record.get("dew_point", 0.0),
            record.get("hvac_load_pct", 0.0),
            record.get("co2_injection_status", 0),
            record.get("energy_footprint_hourly", 0.0),
            record.get("renewable_energy_pct", 0.0),
            record.get("ambient_light_pollution", 0.0),
            # Rhizosphère
            record.get("water_temp", 0.0),
            record.get("water_ph", 0.0),
            record.get("dissolved_oxygen", 0.0),
            record.get("water_turbidity", 0.0),
            record.get("wue_current", 0.0),
            record.get("water_recycled_rate", 0.0),
            record.get("coefficient_cultural_kc", 0.0),
            record.get("microbial_density", 0.0),
            record.get("beneficial_microbes_ratio", 0.0),
            record.get("root_fungal_pressure", 0.0),
            record.get("biofilm_thickness", 0.0),
            record.get("algae_growth_index", 0.0),
            record.get("redox_potential", 0.0),
            record.get("irrigation_line_pressure", 0.0),
            record.get("leaching_fraction", 0.0),
            # Économie
            record.get("energy_price_kwh", 0.0),
            record.get("market_price_kg", 0.0),
            record.get("lease_index_value", 0.0),
            record.get("daily_rent_cost", 0.0),
            record.get("lease_profitability_index", 0.0),
            record.get("is_compliant_lease", 0),
            record.get("labor_cost_pro_rata", 0.0),
            record.get("carbon_credit_value", 0.0),
            record.get("operational_cost_total", 0.0),
            record.get("carbon_footprint_per_kg", 0.0),
            # Hardware
            record.get("pump_vibration_level", 0.0),
            record.get("fan_current_draw", 0.0),
            record.get("led_driver_temp", 0.0),
            record.get("filter_differential_pressure", 0.0),
            record.get("ups_battery_health", 0.0),
            record.get("leak_detection_status", 0),
            record.get("emergency_stop_status", 0),
            record.get("network_latency_ms", 0),
            record.get("sensor_calibration_offset", 0.0),
            record.get("module_integrity_score", 0.0),
            # Intelligence
            record.get("ai_decision_mode", ""),
            record.get("anomaly_confidence_score", 0.0),
            record.get("predicted_energy_need_24h", 0.0),
            record.get("risk_pest_outbreak", 0.0),
            record.get("irrigation_strategy_id", ""),
            record.get("master_compliance_index", 0.0),
            record.get("blockchain_hash", ""),
            record.get("audit_trail_signature", ""),
            quality_grade,
            record.get("system_reboot_count", 0),
            # Cibles
            record.get("ref_n_target", 0.0),
            record.get("ref_p_target", 0.0),
            record.get("ref_k_target", 0.0),
            record.get("ref_ca_target", 0.0),
            record.get("ref_mg_target", 0.0),
            record.get("ref_temp_opt", 0.0),
            record.get("ref_lai_target", 0.0),
            record.get("ref_oil_target", 0.0),
            record.get("ref_wue_target", 0.0),
            record.get("ref_microbial_target", 0.0),
            record.get("ref_photoperiod_opt", 0.0),
            record.get("ref_sum_thermal_target", 0.0),
            record.get("ref_brix_target", 0.0),
            record.get("ref_nitrate_limit", 0.0),
            record.get("ref_humidity_opt", 0.0),
            # Traçabilité
            data_source,
            record.get("sensor_hardware_id", ""),
            record.get("api_endpoint_version", ""),
            record.get("source_reliability_score", 0.0),
            record.get("data_integrity_flag", 0),
            last_calibration,
            record.get("maintenance_urgency_score", 0.0),
            record.get("lineage_uuid", "")
        )

    def flush_batch(self):
        """Insère le batch actuel dans ClickHouse."""
        if not self.batch:
            return

        try:
            columns_str = ", ".join(self.COLUMNS)
            query = f"INSERT INTO {CLICKHOUSE_TABLE} ({columns_str}) VALUES"

            self.ch_client.execute(query, self.batch)

            self.total_inserted += len(self.batch)
            logger.info(f"Inséré {len(self.batch)} enregistrements. Total: {self.total_inserted}")

            # Commit Kafka
            self.consumer.commit()

            self.batch.clear()
            self.last_flush_time = time.time()

        except Exception as e:
            logger.error(f"Erreur insertion ClickHouse: {e}")
            # Ne pas clear le batch en cas d'erreur pour retry

    def should_flush(self) -> bool:
        """Vérifie si le batch doit être flushé."""
        if len(self.batch) >= BATCH_SIZE:
            return True
        if time.time() - self.last_flush_time >= FLUSH_INTERVAL_SECONDS:
            return True
        return False

    def run(self, killer: GracefulKiller):
        """Boucle principale de l'ETL."""
        logger.info("=" * 60)
        logger.info("VERTIFLOW ETL - Kafka → ClickHouse")
        logger.info("=" * 60)
        logger.info(f"Source: {KAFKA_TOPIC}")
        logger.info(f"Destination: {CLICKHOUSE_DB}.{CLICKHOUSE_TABLE}")
        logger.info(f"Batch size: {BATCH_SIZE}, Flush interval: {FLUSH_INTERVAL_SECONDS}s")
        logger.info("=" * 60)

        while not killer.should_stop:
            try:
                # Poll avec timeout
                messages = self.consumer.poll(timeout_ms=1000)

                for tp, records in messages.items():
                    for record in records:
                        try:
                            transformed = self.transform_record(record.value)
                            self.batch.append(transformed)
                        except Exception as e:
                            logger.error(f"Erreur transformation: {e}")
                            continue

                # Flush si nécessaire
                if self.should_flush():
                    self.flush_batch()

            except Exception as e:
                logger.error(f"Erreur dans la boucle: {e}")
                time.sleep(1)

        # Flush final
        self.flush_batch()

    def close(self):
        """Ferme les connexions proprement."""
        if self.consumer:
            self.consumer.close()
        logger.info(f"ETL terminé. Total enregistrements insérés: {self.total_inserted}")


def main():
    """Point d'entrée principal."""
    killer = GracefulKiller()
    etl = KafkaToClickHouseETL()

    if not etl.connect():
        logger.error("Impossible d'établir les connexions. Arrêt.")
        sys.exit(1)

    try:
        etl.run(killer)
    finally:
        etl.close()


if __name__ == "__main__":
    main()
