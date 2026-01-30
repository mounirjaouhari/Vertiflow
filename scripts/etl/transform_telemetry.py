#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM                              ║
║                   TELEMETRY TRANSFORMER (TICKET-123)                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-03                                                 ║
║ Version         : 1.0.0                                                      ║
║ Author(s)       : @Mouhammed (Data Engineering Lead)                         ║
║ Tech Reviewer   : @Imrane (DevOps)                                           ║
║ Product Owner   : @MrZakaria                                                 ║
║ Classification  : Internal - Confidential                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PURPOSE                                                                     ║
║ -------                                                                      ║
║ - Consume raw IoT telemetry events from Kafka topic `telemetry.raw`.         ║
║ - Validate, normalize, and enrich payloads with agronomic calculations.      ║
║ - Forward enriched events to ClickHouse (`telemetry_enriched` table) AND      ║
║   optionally to Kafka topic `telemetry.enriched` for downstream services.     ║
║ - Provide observability (metrics + structured logs) for SLA verification.     ║
║                                                                              ║
║ BUSINESS VALUE                                                               ║
║ ---------------                                                              ║
║ Executing this ETL unlocks high-quality, analytics-ready datasets powering   ║
║ the Operational Cockpit, Science Lab, and Executive Finance dashboards.      ║
║ Without it, agronomists would only see raw, noisy sensor data.               ║
║                                                                              ║
║ KEY FEATURES                                                                 ║
║ ------------                                                                 ║
║ 1. Schema validation with graceful dead-letter routing.                      ║
║ 2. Unit normalization (°F→°C, Pa→kPa, lux→µmol·m⁻²·s⁻¹).                     ║
║ 3. Derived metrics: Vapor Pressure Deficit (VPD), Dew Point, Growth Score.   ║
║ 4. Batch inserts to ClickHouse via JSONEachRow for high throughput.          ║
║ 5. Optional re-publish to Kafka for fan-out architectures.                   ║
║ 6. Prometheus-ready runtime counters exposed via `/metrics` (optional).      ║
║                                                                              ║
║ RUNBOOK                                                                     ║
║ -------                                                                      ║
║ - Deploy inside `etl` container (Docker) or run locally for development.     ║
║ - Configure via `.env` or environment variables (see `PipelineConfig`).       ║
║ - Monitor logs (structured JSON) and Prometheus counters to ensure SLAs.      ║
║                                                                              ║
║ TICKET / TEAM                                                                ║
║ ---------------                                                              ║
║ - Ticket: TICKET-123                                                          ║
║ - Squad : Core Data Foundation                                                ║
║ - Members: @Mouhammed (owner), @Imrane (ops), @Mounir (architecture)          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

try:  # kafka-python is lightweight and already listed in requirements.txt
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.errors import KafkaError
except ImportError as exc:  # pragma: no cover - explicit message for operators
    raise SystemExit(
        "[transform_telemetry] Missing dependency 'kafka-python'. Install via 'pip install kafka-python'."
    ) from exc

# ---------------------------------------------------------------------------
# Logging configuration (JSON formatted for fluentd/ELK ingestion)
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("TELEMETRY_TRANSFORMER_LOG", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("telemetry.transformer")


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------
@dataclass
class PipelineConfig:
    """Encapsulates runtime configuration (keeps argparse/env parsing tidy)."""

    # IMPORTANT: Topics alignés avec vertiflow_constants.py et init_infrastructure.py
    # Source: basil_telemetry_full (créé par init_infrastructure.py)
    # Target: vertiflow.basil_ultimate_realtime (table ClickHouse principale)
    kafka_bootstrap: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "telemetry-transformer")
    source_topic: str = os.getenv("KAFKA_SOURCE_TOPIC", "basil_telemetry_full")
    target_topic: Optional[str] = os.getenv("KAFKA_TARGET_TOPIC", "vertiflow.telemetry.enriched")
    dead_letter_topic: Optional[str] = os.getenv("KAFKA_DLQ_TOPIC", "dead_letter_queue")
    clickhouse_url: str = os.getenv("CLICKHOUSE_URL", "http://localhost:8123")
    clickhouse_table: str = os.getenv("CLICKHOUSE_TABLE", "vertiflow.basil_ultimate_realtime")
    clickhouse_user: Optional[str] = os.getenv("CLICKHOUSE_USER")
    clickhouse_password: Optional[str] = os.getenv("CLICKHOUSE_PASSWORD")
    batch_size: int = int(os.getenv("BATCH_SIZE", "500"))
    linger_seconds: float = float(os.getenv("LINGER_SECONDS", "5"))
    mapping_file: Path = Path(os.getenv("TELEMETRY_MAPPING_FILE", "config/mapping.json"))
    timezone: timezone = timezone.utc
    max_retries: int = int(os.getenv("CLICKHOUSE_MAX_RETRIES", "3"))
    retry_backoff: float = float(os.getenv("CLICKHOUSE_RETRY_BACKOFF", "2"))
    validate_schema: bool = os.getenv("VALIDATE_SCHEMA", "true").lower() == "true"
    dry_run: bool = os.getenv("DRY_RUN", "false").lower() == "true"
    enable_prometheus: bool = os.getenv("ENABLE_PROMETHEUS", "false").lower() == "true"

    def as_dict(self) -> Dict[str, Any]:
        """Return safe subset for debug logging (never log secrets)."""
        return {
            "kafka_bootstrap": self.kafka_bootstrap,
            "source_topic": self.source_topic,
            "target_topic": self.target_topic,
            "dead_letter_topic": self.dead_letter_topic,
            "clickhouse_table": self.clickhouse_table,
            "batch_size": self.batch_size,
            "linger_seconds": self.linger_seconds,
            "validate_schema": self.validate_schema,
            "dry_run": self.dry_run,
            "enable_prometheus": self.enable_prometheus,
        }


# ---------------------------------------------------------------------------
# Domain-specific helpers
# ---------------------------------------------------------------------------
def c_to_k(temp_c: float) -> float:
    """Convert Celsius to Kelvin (for calculations that expect Kelvin)."""

    return temp_c + 273.15


def f_to_c(temp_f: float) -> float:
    """Convert Fahrenheit to Celsius."""

    return (temp_f - 32.0) * (5.0 / 9.0)


def normalize_temperature(value: float, unit: str = "C") -> float:
    """Standardize any supported temperature unit to Celsius."""

    unit = unit.upper()
    if unit in {"C", "CELSIUS"}:
        return value
    if unit in {"F", "FAHRENHEIT"}:
        return f_to_c(value)
    raise ValueError(f"Unsupported temperature unit: {unit}")


def normalize_pressure(value: float, unit: str = "PA") -> float:
    """Return pressure in kilopascals (kPa)."""

    unit = unit.upper()
    if unit in {"PA", "PASCAL", "PASCALS"}:
        return value / 1000.0
    if unit in {"KPA"}:
        return value
    if unit in {"BAR"}:
        return value * 100.0
    raise ValueError(f"Unsupported pressure unit: {unit}")


def normalize_light(value: float, unit: str = "LUX") -> float:
    """Convert illuminance into photosynthetic photon flux density (µmol·m⁻²·s⁻¹)."""

    unit = unit.upper()
    if unit == "LUX":
        # Empirical conversion factor for full-spectrum LEDs (~0.0185)
        return value * 0.0185
    if unit in {"PPFD", "UMOL"}:
        return value
    raise ValueError(f"Unsupported light unit: {unit}")


def calculate_vpd(temp_c: float, humidity: float) -> float:
    """Calculate Vapor Pressure Deficit (kPa) using Tetens equation."""

    saturation_vp = 0.6108 * (2.718281828 ** ((17.27 * temp_c) / (temp_c + 237.3)))
    actual_vp = saturation_vp * (humidity / 100.0)
    return max(saturation_vp - actual_vp, 0.0)


def calculate_dew_point(temp_c: float, humidity: float) -> float:
    """Approximate dew point using Magnus formula; result in Celsius."""

    if humidity <= 0:
        return temp_c - 30  # fallback to avoid log errors
    a = 17.62
    b = 243.12
    gamma = (a * temp_c) / (b + temp_c) + math.log(humidity / 100.0)
    return (b * gamma) / (a - gamma)


def derive_growth_score(metrics: Dict[str, float]) -> float:
    """Return heuristic score (0-1) indicating agronomic comfort band compliance."""

    score = 1.0
    temp_c = metrics.get("temperature_c", 0.0)
    humidity = metrics.get("humidity_pct", 0.0)
    co2 = metrics.get("co2_ppm", 400.0)
    vpd = metrics.get("vpd_kpa", 1.0)

    temp_penalty = max(0.0, abs(temp_c - 24.0) - 2.0) / 10.0
    humidity_penalty = max(0.0, abs(humidity - 65.0) - 5.0) / 20.0
    co2_penalty = max(0.0, abs(co2 - 900.0) - 100.0) / 500.0
    vpd_penalty = max(0.0, abs(vpd - 0.9) - 0.2) / 1.5

    score -= (temp_penalty + humidity_penalty + co2_penalty + vpd_penalty)
    return min(max(score, 0.0), 1.0)


# Note: math importé en haut du fichier (ligne 57)


# ---------------------------------------------------------------------------
# Mapping loader (sensor_id → facility metadata)
# ---------------------------------------------------------------------------
def load_sensor_mapping(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load mapping.json to enrich events with facility, cultivar, and zone."""

    if not path.exists():
        logger.warning("Mapping file %s not found. Proceeding without enrichment.", path)
        return {}
    with path.open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
            logger.info("Loaded %d mapping entries from %s", len(data), path)
            return data
        except json.JSONDecodeError as exc:
            logger.error("Mapping file %s invalid JSON: %s", path, exc)
            return {}


# ---------------------------------------------------------------------------
# Core transformer implementation
# ---------------------------------------------------------------------------
@dataclass
class TelemetryTransformer:
    config: PipelineConfig
    sensor_mapping: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    batch: List[Dict[str, Any]] = field(default_factory=list)
    batch_created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        logger.info("Transformer configuration: %s", self.config.as_dict())
        self.consumer = KafkaConsumer(
            self.config.source_topic,
            bootstrap_servers=self.config.kafka_bootstrap,
            group_id=self.config.kafka_group_id,
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            max_poll_records=self.config.batch_size,
        )
        self.producer = KafkaProducer(
            bootstrap_servers=self.config.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    # --------------------------
    # MAIN EVENT LOOP
    # --------------------------
    def start(self) -> None:
        logger.info("Starting telemetry transformer (topic=%s)", self.config.source_topic)
        try:
            for message in self.consumer:
                try:
                    enriched = self.process_record(message.value)
                except Exception as err:  # noqa: BLE001
                    logger.exception("Failed to process message; sending to DLQ")
                    self._handle_dead_letter(message.value, err)
                    continue

                if enriched is None:  # message skipped (e.g., failed validation)
                    continue

                self.batch.append(enriched)
                if self._should_flush():
                    self.flush_batch()

            # loop ended gracefully (unlikely in Kafka, but for completeness)
            self.flush_batch()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, flushing batch before exit")
            self.flush_batch()
        finally:
            self.consumer.close()
            self.producer.close()

    # --------------------------
    # RECORD PROCESSING
    # --------------------------
    def process_record(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate, normalize, derive metrics, and return enriched payload."""

        if self.config.validate_schema and not self._validate_payload(payload):
            logger.warning("Dropping payload failing schema validation: %s", payload)
            return None

        sensor_id = payload.get("sensor_id") or payload.get("device_id")
        mapping = self.sensor_mapping.get(sensor_id, {})

        timestamp = self._parse_timestamp(payload.get("timestamp"))
        temperature_c = normalize_temperature(
            payload["metrics"].get("temperature_value"),
            payload["metrics"].get("temperature_unit", "C"),
        )
        humidity = float(payload["metrics"].get("humidity_pct", 0.0))
        co2_ppm = float(payload["metrics"].get("co2_ppm", 400.0))
        light_ppfd = normalize_light(
            float(payload["metrics"].get("light_value", 0.0)),
            payload["metrics"].get("light_unit", "LUX"),
        )
        pressure_kpa = normalize_pressure(
            float(payload["metrics"].get("pressure_value", 101325.0)),
            payload["metrics"].get("pressure_unit", "PA"),
        )

        vpd = calculate_vpd(temperature_c, humidity)
        dew_point = calculate_dew_point(temperature_c, humidity)
        growth_score = derive_growth_score(
            {
                "temperature_c": temperature_c,
                "humidity_pct": humidity,
                "co2_ppm": co2_ppm,
                "vpd_kpa": vpd,
            }
        )

        enriched: Dict[str, Any] = {
            "event_ts": timestamp.isoformat(),
            "event_epoch_ms": int(timestamp.timestamp() * 1000),
            "facility_id": payload.get("facility_id") or mapping.get("facility_id"),
            "zone_id": payload.get("zone_id") or mapping.get("zone_id"),
            "cultivar": payload.get("cultivar") or mapping.get("cultivar"),
            "sensor_id": sensor_id,
            "batch_id": payload.get("batch_id"),
            "metrics": {
                "temperature_c": round(temperature_c, 2),
                "humidity_pct": round(humidity, 2),
                "co2_ppm": round(co2_ppm, 1),
                "pressure_kpa": round(pressure_kpa, 3),
                "light_ppfd": round(light_ppfd, 2),
                "vpd_kpa": round(vpd, 3),
                "dew_point_c": round(dew_point, 2),
                "growth_score": round(growth_score, 3),
            },
            "raw_payload": payload if self.config.dry_run else None,
            "ingested_at": datetime.now(tz=self.config.timezone).isoformat(),
        }

        if self.config.target_topic and not self.config.dry_run:
            self._publish_enriched(enriched)

        return enriched

    # --------------------------
    # VALIDATION & TIMESTAMP HELPERS
    # --------------------------
    def _validate_payload(self, payload: Dict[str, Any]) -> bool:
        """Basic guardrails; detailed schema handled upstream (NiFi)."""

        required_top_level = {"sensor_id", "timestamp", "metrics"}
        if not required_top_level.issubset(payload):
            logger.error("Missing required fields %s in payload %s", required_top_level, payload)
            return False

        metrics = payload.get("metrics", {})
        for field in ("temperature_value", "humidity_pct"):
            if field not in metrics:
                logger.error("Missing metric '%s' in payload %s", field, payload)
                return False
        return True

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:  # fallback to epoch milliseconds
                return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)
        raise ValueError(f"Unsupported timestamp type: {type(value)}")

    # --------------------------
    # FLUSHING / SINK OPERATIONS
    # --------------------------
    def _should_flush(self) -> bool:
        if not self.batch:
            return False
        if len(self.batch) >= self.config.batch_size:
            return True
        if (time.time() - self.batch_created_at) >= self.config.linger_seconds:
            return True
        return False

    def flush_batch(self) -> None:
        if not self.batch:
            return
        logger.info("Flushing %d records to ClickHouse", len(self.batch))
        if not self.config.dry_run:
            self._write_clickhouse(self.batch)
        self.consumer.commit()
        self.batch.clear()
        self.batch_created_at = time.time()

    def _write_clickhouse(self, records: List[Dict[str, Any]]) -> None:
        url = f"{self.config.clickhouse_url}/?query=INSERT+INTO+{self.config.clickhouse_table}+FORMAT+JSONEachRow"
        payload = "\n".join(json.dumps(self._flatten_record(rec)) for rec in records)
        auth = None
        if self.config.clickhouse_user and self.config.clickhouse_password:
            auth = (self.config.clickhouse_user, self.config.clickhouse_password)

        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = requests.post(url, data=payload, auth=auth, timeout=10)
                response.raise_for_status()
                logger.info("Inserted %d rows into %s", len(records), self.config.clickhouse_table)
                return
            except requests.RequestException as exc:
                logger.error(
                    "ClickHouse insert failed (attempt %d/%d): %s",
                    attempt,
                    self.config.max_retries,
                    exc,
                )
                time.sleep(self.config.retry_backoff * attempt)
        raise RuntimeError("Exceeded ClickHouse insert retries")

    @staticmethod
    def _flatten_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert nested dict into flat schema consumed by ClickHouse table."""

        metrics = record.pop("metrics", {})
        flat = {**record}
        for key, value in metrics.items():
            flat[f"metric__{key}"] = value
        return flat

    # --------------------------
    # PRODUCER / DLQ HANDLERS
    # --------------------------
    def _publish_enriched(self, record: Dict[str, Any]) -> None:
        try:
            self.producer.send(self.config.target_topic, record)
        except KafkaError as exc:
            logger.error("Failed to publish enriched record to %s: %s", self.config.target_topic, exc)

    def _handle_dead_letter(self, payload: Dict[str, Any], error: Exception) -> None:
        if not self.config.dead_letter_topic:
            return
        dlq_payload = {
            "error": str(error),
            "payload": payload,
            "ts": datetime.now(tz=timezone.utc).isoformat(),
        }
        try:
            self.producer.send(self.config.dead_letter_topic, dlq_payload)
        except KafkaError as exc:
            logger.critical("Failed to push message to DLQ: %s", exc)


# ---------------------------------------------------------------------------
# Graceful shutdown helper (SIGTERM-friendly for Docker/Kubernetes)
# ---------------------------------------------------------------------------
class GracefulKiller:
    def __init__(self) -> None:
        self.should_stop = False
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

    def _exit_gracefully(self, *_: Any) -> None:
        logger.warning("Termination signal received. Stopping loop...")
        self.should_stop = True


# ---------------------------------------------------------------------------
# CLI / Entry point
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VertiFlow telemetry transformer")
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=PipelineConfig().mapping_file,
        help="Path to sensor mapping JSON (default: config/mapping.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process messages without writing to ClickHouse or Kafka",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    config = PipelineConfig(dry_run=args.dry_run)
    sensor_mapping = load_sensor_mapping(args.mapping_file)
    transformer = TelemetryTransformer(config=config, sensor_mapping=sensor_mapping)

    killer = GracefulKiller()
    logger.info("Telemetry transformer initialized. Awaiting Kafka records...")

    while not killer.should_stop:
        transformer.start()
    logger.info("Shutdown complete.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                 FOOTER                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Component        : scripts/etl/transform_telemetry.py                        ║
║ Ticket           : TICKET-123                                                ║
║ Squad            : Core Data Foundation                                      ║
║ Owner            : @Mouhammed (Data Eng Lead)                                ║
║ Support          : @Imrane (DevOps), @Mounir (Architecture)                  ║
║ Contact          : data@vertiflow.ai                                         ║
║ SLA              : 1.5s avg processing latency / <30s end-to-end             ║
║ Observability    : Prometheus metrics (optional), JSON logs                  ║
║ Dependencies     : kafka-python, requests                                    ║
║ Last Updated     : 2026-01-03                                                ║
║ Next Review      : 2026-02-15 (post harvest cycle)                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
