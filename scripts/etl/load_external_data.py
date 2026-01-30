#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM                              ║
║                 EXTERNAL DATA LOADER / ENRICHMENT (TICKET-124)               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-03                                                 ║
║ Version         : 1.0.0                                                      ║
║ Author(s)       : @Mouhammed (Data Engineering Lead)                         ║
║ Reviewer(s)     : @Imrane (DevOps), @Asama (Domain)                          ║
║ Product Owner   : @MrZakaria                                                 ║
║ Classification  : Internal - Confidential                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PURPOSE                                                                     ║
║ -------                                                                      ║
║ - Read `config/external_data_sources.yaml` to discover upstream providers.   ║
║ - Orchestrate API calls (NASA, OpenWeather, ElectricityMap, RTE, etc.).       ║
║ - Persist normalized payloads to `nifi_exchange/input/external/` for NiFi.    ║
║ - Emit structured metadata for lineage (who, when, priority).                 ║
║ - Offer CLI filters + dry-run for testing from laptops/CI pipelines.          ║
║                                                                              ║
║ BUSINESS VALUE                                                               ║
║ ---------------                                                              ║
║ Adds macro-environmental, energy, and market signals that power              ║
║ forecasting models, energy optimization, and finance dashboards.             ║
║                                                                              ║
║ KEY FEATURES                                                                 ║
║ ------------                                                                 ║
║ 1. YAML-driven registry → zero-code onboarding of new providers.             ║
║ 2. Built-in adapters for GET, OAuth2, and placeholder scrapers.              ║
║ 3. Pluggable per-source handlers (NASA_POWER, OPENWEATHER_MAP, etc.).        ║
║ 4. Centralized persistence (JSON metadata + raw payload).                    ║
║ 5. Structured logging + exit codes suitable for Airflow / cron.              ║
║                                                                              ║
║ TICKET / TEAM                                                                ║
║ ---------------                                                              ║
║ - Ticket: TICKET-124                                                          ║
║ - Squad : Core Data Foundation                                                ║
║ - Members: @Mouhammed (owner), @Imrane (ops), @Mounir (architecture)          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
import yaml

LOGGER = logging.getLogger("external.loader")
logging.basicConfig(
    level=os.getenv("EXTERNAL_LOADER_LOG", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

DEFAULT_CONFIG = Path("config/external_data_sources.yaml")
DEFAULT_OUTPUT = Path("nifi_exchange/input/external")
DEFAULT_TIMEOUT = 25


@dataclass
class SourceSpec:
    """Represents one entry from external_data_sources.yaml."""

    name: str
    description: str
    provider: str
    url: str
    method: str
    format: str
    priority: str
    update_frequency: str
    parameters: List[Any] = field(default_factory=list)
    target_columns: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceSpec":
        missing = {key for key in ("name", "url", "method", "format") if key not in data}
        if missing:
            raise ValueError(f"Malformed source definition (missing {missing}): {data}")
        return cls(**data)


class ExternalDataLoader:
    """Core orchestrator for fetching and persisting external datasets."""

    def __init__(self, config_path: Path, output_dir: Path, dry_run: bool = False) -> None:
        self.config_path = config_path
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.session = requests.Session()
        self.sources = self._load_sources()
        LOGGER.info("Initialized loader (sources=%d, dry_run=%s)", len(self.sources), dry_run)

    # ------------------------------------------------------------------
    # Configuration / registry helpers
    # ------------------------------------------------------------------
    def _load_sources(self) -> Dict[str, SourceSpec]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        raw_sources = data.get("sources", [])
        specs = {entry["name"]: SourceSpec.from_dict(entry) for entry in raw_sources}
        return specs

    # ------------------------------------------------------------------
    # Public entrypoints
    # ------------------------------------------------------------------
    def available_sources(self) -> List[str]:
        return sorted(self.sources.keys())

    def run(self, selected: Optional[List[str]] = None) -> Dict[str, str]:
        targets = self.available_sources() if not selected else selected
        results: Dict[str, str] = {}
        for name in targets:
            spec = self.sources.get(name)
            if not spec:
                LOGGER.warning("Source %s not declared in %s", name, self.config_path)
                results[name] = "missing"
                continue
            start = time.time()
            try:
                payload, meta = self._dispatch(spec)
                if not self.dry_run:
                    self._persist(spec, payload, meta)
                duration = time.time() - start
                LOGGER.info("Fetched %s in %.2fs", spec.name, duration)
                results[spec.name] = "ok"
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Source %s failed: %s", spec.name, exc)
                results[spec.name] = f"error: {exc}"
        return results

    # ------------------------------------------------------------------
    # Fetch dispatching
    # ------------------------------------------------------------------
    def _dispatch(self, spec: SourceSpec) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        handler_name = f"_handle_{spec.name.lower()}"
        if hasattr(self, handler_name):
            return getattr(self, handler_name)(spec)
        method = spec.method.upper()
        if method == "GET":
            return self._handle_generic_get(spec)
        if method == "OAUTH2":
            return self._handle_oauth2(spec)
        if method == "SCRAPING":
            raise NotImplementedError(
                f"Source {spec.name} requires a scraper. Implement handler or ingest via NiFi."
            )
        raise ValueError(f"Unsupported method {spec.method} for {spec.name}")

    # ------------------------------------------------------------------
    # Specific handlers (custom logic per provider)
    # ------------------------------------------------------------------
    def _handle_nasa_power(self, spec: SourceSpec) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        params = spec.parameters or []
        param_string = ",".join(params) if params else "T2M,RH2M,ALLSKY_SFC_SW_DWN"
        lat = float(os.getenv("NASA_POWER_LAT", "33.5731"))
        lon = float(os.getenv("NASA_POWER_LON", "-7.5898"))
        days_back = int(os.getenv("NASA_POWER_DAYS", "2"))
        end_date = datetime.utcnow().strftime("%Y%m%d")
        start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y%m%d")
        url = (
            f"{spec.url}/temporal/hourly/point?parameters={param_string}&community=AG"
            f"&longitude={lon}&latitude={lat}&start={start_date}&end={end_date}&format=JSON"
        )
        response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        meta = {
            "fetch_url": url,
            "latitude": lat,
            "longitude": lon,
            "parameters": param_string,
            "start": start_date,
            "end": end_date,
        }
        return payload, meta

    def _handle_openweather_map(self, spec: SourceSpec) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENWEATHER_API_KEY not configured")
        base_params = {"appid": api_key, "units": "metric"}
        for entry in spec.parameters:
            if isinstance(entry, dict):
                base_params.update(entry)
        response = self.session.get(spec.url, params=base_params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        meta = {"request_params": base_params}
        return payload, meta

    def _handle_electricity_maps(self, spec: SourceSpec) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        api_token = os.getenv("ELECTRICITY_MAPS_TOKEN")
        if not api_token:
            raise EnvironmentError("ELECTRICITY_MAPS_TOKEN not configured")
        headers = {"auth-token": api_token}
        response = self.session.get(spec.url, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        meta = {"zone": payload.get("zone")}
        return payload, meta

    def _handle_rte_eco2mix(self, spec: SourceSpec) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        client_id = os.getenv("RTE_CLIENT_ID")
        client_secret = os.getenv("RTE_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise EnvironmentError("RTE_CLIENT_ID / RTE_CLIENT_SECRET not configured")
        token_resp = self.session.post(
            spec.url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=DEFAULT_TIMEOUT,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise RuntimeError("RTE OAuth2 token missing in response")
        data_url = os.getenv("RTE_DATA_URL", "https://digital.iservices.rte-france.com/open_api/eco2mix/v1/daily")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.session.get(data_url, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        meta = {"token_endpoint": spec.url, "data_url": data_url}
        return payload, meta

    # ------------------------------------------------------------------
    # Generic handlers
    # ------------------------------------------------------------------
    def _handle_generic_get(self, spec: SourceSpec) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        params = self._kv_params(spec.parameters)
        response = self.session.get(spec.url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = self._maybe_parse(response, spec.format)
        meta = {"request_params": params}
        return payload, meta

    def _handle_oauth2(self, spec: SourceSpec) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        raise NotImplementedError(
            "Generic OAuth2 handler not implemented. Use source-specific method or extend class."
        )

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _persist(self, spec: SourceSpec, payload: Dict[str, Any], meta: Dict[str, Any]) -> None:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        folder = self.output_dir / spec.name.lower()
        folder.mkdir(parents=True, exist_ok=True)
        json_path = folder / f"payload_{timestamp}.json"
        audit_path = folder / f"metadata_{timestamp}.json"
        enriched_meta = {
            "source": spec.name,
            "provider": spec.provider,
            "priority": spec.priority,
            "update_frequency": spec.update_frequency,
            "target_columns": spec.target_columns,
            "fetched_at": timestamp,
            "meta": meta,
        }
        with json_path.open("w", encoding="utf-8") as payload_file:
            json.dump(payload, payload_file, indent=2)
        with audit_path.open("w", encoding="utf-8") as meta_file:
            json.dump(enriched_meta, meta_file, indent=2)
        LOGGER.info("Persisted %s (%s, priority=%s)", spec.name, json_path, spec.priority)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _maybe_parse(response: requests.Response, expected_format: str) -> Dict[str, Any]:
        fmt = expected_format.upper()
        if fmt in {"JSON", "GEOJSON"}:
            return response.json()
        if fmt == "XML":
            return {"raw_xml": response.text}
        if fmt in {"CSV", "HTML"}:
            return {"raw_text": response.text}
        raise ValueError(f"Unsupported format {expected_format}")

    @staticmethod
    def _kv_params(entries: List[Any]) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        for entry in entries:
            if isinstance(entry, dict):
                params.update(entry)
            elif isinstance(entry, str) and "=" in entry:
                key, value = entry.split("=", 1)
                params[key.strip()] = value.strip()
        return params


# --------------------------------------------------------------------------
# CLI UTILITIES
# --------------------------------------------------------------------------
def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VertiFlow external data loader")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to YAML registry")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destination folder for payloads")
    parser.add_argument(
        "--sources",
        type=str,
        default=None,
        help="Comma-separated list of source names. Defaults to all registered sources.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch but skip persistence")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    loader = ExternalDataLoader(args.config, args.output, dry_run=args.dry_run)
    selected = args.sources.split(",") if args.sources else None
    summary = loader.run(selected)
    failures = {name: status for name, status in summary.items() if status != "ok"}
    if failures:
        LOGGER.error("Some sources failed: %s", failures)
        return 1
    LOGGER.info("All sources fetched successfully")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                 FOOTER                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Component        : scripts/etl/load_external_data.py                         ║
║ Ticket           : TICKET-124                                                ║
║ Squad            : Core Data Foundation                                      ║
║ Owner            : @Mouhammed                                                ║
║ Support          : @Imrane (DevOps), @Asama (Domain), @Mounir (Architecture) ║
║ Contact          : data@vertiflow.ai                                         ║
║ Dependencies     : requests, pyyaml                                          ║
║ Deployment       : Cron / Airflow / NiFi shell processor                     ║
║ Exit Codes       : 0 success, 1 partial/total failure                        ║
║ Last Updated     : 2026-01-03                                                ║
║ Next Review      : 2026-02-15                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
