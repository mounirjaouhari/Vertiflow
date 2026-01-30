#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
============================================================================
FICHIER: fetch_all_external_data.py
DESCRIPTION: Orchestrateur principal pour la recuperation de toutes les
             sources de donnees externes. Point d'entree unique pour:
             - APIs meteo (NASA, Open-Meteo, OpenWeather)
             - APIs energie (RTE, Electricity Maps, ONEE)
             - APIs marche (RNM, FAO FPMA)
             - APIs agronomiques (OpenFarm)
             - APIs qualite air (OpenAQ)

Developpe par       : @Mouhammed
Ticket(s) associe(s): TICKET-125, TICKET-133
Sprint              : Semaine 6 - Integration Complete
============================================================================
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Configuration du logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
LOGGER = logging.getLogger("vertiflow.orchestrator")

# Paths
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_BASE_DIR = BASE_DIR / "nifi_exchange" / "input" / "external"


@dataclass
class FetchResult:
    """Resultat d'une operation de fetch."""

    source: str
    success: bool
    duration_seconds: float = 0.0
    filepath: Optional[str] = None
    records_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class OrchestratorConfig:
    """Configuration de l'orchestrateur."""

    parallel_fetches: int = 4
    timeout_per_source: int = 60
    retry_count: int = 2
    retry_delay: int = 5
    output_dir: Path = OUTPUT_BASE_DIR


class ExternalDataOrchestrator:
    """
    Orchestrateur central pour toutes les sources de donnees externes.

    Gere l'execution parallele, les retries, et la consolidation des resultats.
    """

    # Definition des sources et leurs handlers
    SOURCES = {
        # Meteo - GRATUITS
        "nasa_power": {
            "category": "weather",
            "priority": "critical",
            "handler": "_fetch_nasa_power",
            "requires_key": False,
            "description": "NASA POWER - Donnees climatiques",
        },
        "open_meteo": {
            "category": "weather",
            "priority": "critical",
            "handler": "_fetch_open_meteo",
            "requires_key": False,
            "description": "Open-Meteo - Meteo gratuite",
        },
        "openweather": {
            "category": "weather",
            "priority": "high",
            "handler": "_fetch_openweather",
            "requires_key": True,
            "env_key": "OPENWEATHER_API_KEY",
            "description": "OpenWeather - Previsions detaillees",
        },

        # Energie
        "rte_eco2mix": {
            "category": "energy",
            "priority": "critical",
            "handler": "_fetch_rte_eco2mix",
            "requires_key": True,
            "env_key": "RTE_CLIENT_ID",
            "description": "RTE ECO2MIX - Reseau electrique francais",
        },
        "electricity_maps": {
            "category": "energy",
            "priority": "medium",
            "handler": "_fetch_electricity_maps",
            "requires_key": True,
            "env_key": "ELECTRICITY_MAPS_TOKEN",
            "description": "Electricity Maps - Intensite carbone",
        },
        "onee_tarifs": {
            "category": "energy",
            "priority": "high",
            "handler": "_fetch_onee_tarifs",
            "requires_key": False,
            "description": "ONEE - Tarifs electricite Maroc",
        },

        # Marche
        "rnm_prices": {
            "category": "market",
            "priority": "high",
            "handler": "_fetch_rnm_prices",
            "requires_key": False,
            "description": "RNM - Prix marche agricole France",
        },
        "fao_fpma": {
            "category": "market",
            "priority": "medium",
            "handler": "_fetch_fao_fpma",
            "requires_key": False,
            "description": "FAO FPMA - Prix alimentaires mondiaux",
        },

        # Agronomique
        "openfarm": {
            "category": "agronomic",
            "priority": "medium",
            "handler": "_fetch_openfarm",
            "requires_key": False,
            "description": "OpenFarm - Base cultures",
        },

        # Qualite air
        "openaq": {
            "category": "air_quality",
            "priority": "low",
            "handler": "_fetch_openaq",
            "requires_key": False,
            "description": "OpenAQ - Qualite de l'air",
        },
    }

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.results: List[FetchResult] = []

        LOGGER.info(
            "Orchestrator initialized (parallel=%d, timeout=%ds)",
            self.config.parallel_fetches,
            self.config.timeout_per_source,
        )

    def fetch_all(
        self,
        categories: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skip_missing_keys: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute la recuperation de toutes les sources de donnees.

        Args:
            categories: Filtrer par categorie (weather, energy, market, etc.)
            sources: Liste specifique de sources a recuperer
            skip_missing_keys: Ignorer les sources sans cle API configuree

        Returns:
            Resume de l'execution avec tous les resultats
        """
        LOGGER.info("=" * 60)
        LOGGER.info("VERTIFLOW EXTERNAL DATA ORCHESTRATOR")
        LOGGER.info("=" * 60)

        start_time = time.time()

        # Filtrage des sources
        active_sources = self._filter_sources(categories, sources, skip_missing_keys)

        LOGGER.info("Sources to fetch: %s", list(active_sources.keys()))

        # Execution parallele
        results = self._execute_parallel(active_sources)
        self.results = results

        # Resume
        total_time = time.time() - start_time
        summary = self._generate_summary(results, total_time)

        self._log_summary(summary)

        return summary

    def _filter_sources(
        self,
        categories: Optional[List[str]],
        sources: Optional[List[str]],
        skip_missing_keys: bool,
    ) -> Dict[str, Dict[str, Any]]:
        """Filtre les sources selon les criteres."""
        filtered = {}

        for name, config in self.SOURCES.items():
            # Filtre par nom
            if sources and name not in sources:
                continue

            # Filtre par categorie
            if categories and config["category"] not in categories:
                continue

            # Verification des cles API
            if skip_missing_keys and config.get("requires_key"):
                env_key = config.get("env_key")
                if env_key and not os.getenv(env_key):
                    LOGGER.warning(
                        "Skipping %s: %s not configured",
                        name, env_key
                    )
                    continue

            filtered[name] = config

        return filtered

    def _execute_parallel(
        self,
        sources: Dict[str, Dict[str, Any]],
    ) -> List[FetchResult]:
        """Execute les fetches en parallele."""
        results = []

        with ThreadPoolExecutor(max_workers=self.config.parallel_fetches) as executor:
            futures = {}

            for name, config in sources.items():
                handler_name = config["handler"]
                handler = getattr(self, handler_name, None)

                if handler:
                    future = executor.submit(
                        self._execute_with_retry,
                        name,
                        handler,
                    )
                    futures[future] = name

            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    result = future.result(timeout=self.config.timeout_per_source)
                    results.append(result)
                except Exception as e:
                    LOGGER.error("Source %s failed: %s", source_name, e)
                    results.append(FetchResult(
                        source=source_name,
                        success=False,
                        errors=[str(e)],
                    ))

        return results

    def _execute_with_retry(
        self,
        source_name: str,
        handler: Callable,
    ) -> FetchResult:
        """Execute un handler avec retry."""
        last_error = None

        for attempt in range(self.config.retry_count + 1):
            try:
                start = time.time()
                result = handler()
                duration = time.time() - start

                return FetchResult(
                    source=source_name,
                    success=True,
                    duration_seconds=round(duration, 2),
                    filepath=result.get("filepath"),
                    records_count=result.get("records_count", 0),
                )

            except Exception as e:
                last_error = e
                LOGGER.warning(
                    "Attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    self.config.retry_count + 1,
                    source_name,
                    e,
                )
                if attempt < self.config.retry_count:
                    time.sleep(self.config.retry_delay)

        return FetchResult(
            source=source_name,
            success=False,
            errors=[str(last_error)],
        )

    # =========================================================================
    # HANDLERS INDIVIDUELS
    # =========================================================================

    def _fetch_nasa_power(self) -> Dict[str, Any]:
        """Handler NASA POWER."""
        # Import de la fonction existante (pas une classe)
        scripts_dir = Path(__file__).parent
        sys.path.insert(0, str(scripts_dir))
        from download_nasa_power import fetch_nasa_data

        # Exécuter la fonction et retourner le résultat
        fetch_nasa_data()

        return {
            "filepath": str(scripts_dir.parent / "data_ingestion" / "nasa_weather"),
            "records_count": 1,
        }

    def _fetch_open_meteo(self) -> Dict[str, Any]:
        """Handler Open-Meteo."""
        # Import des fonctions existantes (pas une classe)
        scripts_dir = Path(__file__).parent
        sys.path.insert(0, str(scripts_dir))
        from fetch_open_meteo import fetch_forecast_data, transform_to_vertiflow_schema, save_to_nifi

        # Exécuter les fonctions
        forecast_data = fetch_forecast_data(days=7)
        if forecast_data:
            records = transform_to_vertiflow_schema(forecast_data, "forecast")
            filepath = save_to_nifi(records, "open_meteo_hourly") if records else None
            return {
                "filepath": filepath,
                "records_count": len(records),
            }

        return {
            "filepath": None,
            "records_count": 0,
        }

    def _fetch_openweather(self) -> Dict[str, Any]:
        """Handler OpenWeather (necessite cle API)."""
        # Import du loader existant
        sys.path.insert(0, str(SCRIPTS_DIR / "etl"))
        from load_external_data import ExternalDataLoader

        loader = ExternalDataLoader(
            config_path=BASE_DIR / "config" / "external_data_sources.yaml",
            output_dir=self.config.output_dir,
        )

        results = loader.run(selected=["OPENWEATHER_MAP"])

        return {
            "filepath": str(self.config.output_dir / "openweather_map"),
            "records_count": 1 if results.get("OPENWEATHER_MAP") == "ok" else 0,
        }

    def _fetch_rte_eco2mix(self) -> Dict[str, Any]:
        """Handler RTE ECO2MIX."""
        sys.path.insert(0, str(SCRIPTS_DIR / "data_sources" / "handlers"))
        from rte_eco2mix_handler import RTEECO2MixHandler

        handler = RTEECO2MixHandler(output_dir=self.config.output_dir / "rte_eco2mix")
        result = handler.run()

        return {
            "filepath": result.get("filepath"),
            "records_count": result.get("data_points", 0),
        }

    def _fetch_electricity_maps(self) -> Dict[str, Any]:
        """Handler Electricity Maps."""
        sys.path.insert(0, str(SCRIPTS_DIR / "data_sources" / "handlers"))
        from electricity_maps_handler import ElectricityMapsHandler

        handler = ElectricityMapsHandler(output_dir=self.config.output_dir / "electricity_maps")
        result = handler.run()

        return {
            "filepath": result.get("filepath"),
            "records_count": result.get("zones_count", 0),
        }

    def _fetch_onee_tarifs(self) -> Dict[str, Any]:
        """Handler ONEE Tarifs."""
        sys.path.insert(0, str(SCRIPTS_DIR / "data_sources" / "scrapers"))
        from onee_tarifs_scraper import ONEETarifsScraper

        scraper = ONEETarifsScraper(output_dir=self.config.output_dir / "onee_tarifs")
        result = scraper.run()

        return {
            "filepath": result.get("filepath"),
            "records_count": result.get("tariffs_count", 0),
        }

    def _fetch_rnm_prices(self) -> Dict[str, Any]:
        """Handler RNM Prices."""
        sys.path.insert(0, str(SCRIPTS_DIR / "data_sources" / "scrapers"))
        from rnm_prices_scraper import RNMPricesScraper

        scraper = RNMPricesScraper(output_dir=self.config.output_dir / "rnm_prices")
        result = scraper.run()

        return {
            "filepath": result.get("filepath"),
            "records_count": result.get("prices_count", 0),
        }

    def _fetch_fao_fpma(self) -> Dict[str, Any]:
        """Handler FAO FPMA."""
        sys.path.insert(0, str(SCRIPTS_DIR / "data_sources" / "handlers"))
        from fao_fpma_handler import FAOFPMAHandler

        handler = FAOFPMAHandler(output_dir=self.config.output_dir / "fao_fpma")
        result = handler.run()

        return {
            "filepath": result.get("filepath"),
            "records_count": result.get("markets_count", 0),
        }

    def _fetch_openfarm(self) -> Dict[str, Any]:
        """Handler OpenFarm."""
        sys.path.insert(0, str(SCRIPTS_DIR / "data_sources" / "handlers"))
        from openfarm_handler import OpenFarmHandler

        handler = OpenFarmHandler(output_dir=self.config.output_dir / "openfarm")
        result = handler.run()

        return {
            "filepath": result.get("filepath"),
            "records_count": result.get("crops_count", 0),
        }

    def _fetch_openaq(self) -> Dict[str, Any]:
        """Handler OpenAQ."""
        sys.path.insert(0, str(SCRIPTS_DIR / "data_sources" / "handlers"))
        from openaq_handler import OpenAQHandler

        handler = OpenAQHandler(output_dir=self.config.output_dir / "openaq")
        result = handler.run()

        return {
            "filepath": result.get("filepath"),
            "records_count": 1 if result.get("status") == "ok" else 0,
        }

    # =========================================================================
    # REPORTING
    # =========================================================================

    def _generate_summary(
        self,
        results: List[FetchResult],
        total_time: float,
    ) -> Dict[str, Any]:
        """Genere un resume de l'execution."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        by_category = {}
        for r in results:
            source_config = self.SOURCES.get(r.source, {})
            category = source_config.get("category", "unknown")
            if category not in by_category:
                by_category[category] = {"success": 0, "failed": 0}
            if r.success:
                by_category[category]["success"] += 1
            else:
                by_category[category]["failed"] += 1

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time_seconds": round(total_time, 2),
            "total_sources": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate_pct": round(len(successful) / len(results) * 100, 1) if results else 0,
            "by_category": by_category,
            "results": [
                {
                    "source": r.source,
                    "success": r.success,
                    "duration": r.duration_seconds,
                    "filepath": r.filepath,
                    "records": r.records_count,
                    "errors": r.errors,
                }
                for r in results
            ],
            "failed_sources": [r.source for r in failed],
        }

    def _log_summary(self, summary: Dict[str, Any]) -> None:
        """Affiche le resume dans les logs."""
        LOGGER.info("=" * 60)
        LOGGER.info("EXECUTION SUMMARY")
        LOGGER.info("=" * 60)
        LOGGER.info("Total sources: %d", summary["total_sources"])
        LOGGER.info("Successful: %d", summary["successful"])
        LOGGER.info("Failed: %d", summary["failed"])
        LOGGER.info("Success rate: %.1f%%", summary["success_rate_pct"])
        LOGGER.info("Total time: %.2fs", summary["execution_time_seconds"])

        if summary["failed_sources"]:
            LOGGER.warning("Failed sources: %s", summary["failed_sources"])

        LOGGER.info("=" * 60)

    def save_summary(self, summary: Dict[str, Any]) -> Path:
        """Sauvegarde le resume dans un fichier JSON."""
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filepath = self.config.output_dir / f"orchestrator_summary_{timestamp}.json"

        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        LOGGER.info("Summary saved to %s", filepath)
        return filepath


def main():
    """Point d'entree CLI."""
    parser = argparse.ArgumentParser(
        description="VertiFlow External Data Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all sources (skip those without API keys)
  python fetch_all_external_data.py

  # Fetch only weather data
  python fetch_all_external_data.py --category weather

  # Fetch specific sources
  python fetch_all_external_data.py --sources nasa_power open_meteo

  # Force fetch all (including missing keys - will fail)
  python fetch_all_external_data.py --no-skip-missing
        """
    )

    parser.add_argument(
        "--category",
        type=str,
        nargs="+",
        choices=["weather", "energy", "market", "agronomic", "air_quality"],
        help="Categories to fetch",
    )
    parser.add_argument(
        "--sources",
        type=str,
        nargs="+",
        help="Specific sources to fetch",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="Number of parallel fetches",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout per source in seconds",
    )
    parser.add_argument(
        "--no-skip-missing",
        action="store_true",
        help="Don't skip sources with missing API keys",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_BASE_DIR,
        help="Output directory",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List all available sources and exit",
    )

    args = parser.parse_args()

    # Liste des sources
    if args.list_sources:
        print("\nAvailable data sources:")
        print("-" * 60)
        for name, config in ExternalDataOrchestrator.SOURCES.items():
            key_status = ""
            if config.get("requires_key"):
                env_key = config.get("env_key")
                if env_key and os.getenv(env_key):
                    key_status = " [KEY OK]"
                else:
                    key_status = f" [NEEDS {env_key}]"
            print(f"  {name:20} {config['category']:12} {config['priority']:8}{key_status}")
            print(f"    {config['description']}")
        return 0

    # Configuration
    config = OrchestratorConfig(
        parallel_fetches=args.parallel,
        timeout_per_source=args.timeout,
        output_dir=args.output,
    )

    # Execution
    orchestrator = ExternalDataOrchestrator(config=config)
    summary = orchestrator.fetch_all(
        categories=args.category,
        sources=args.sources,
        skip_missing_keys=not args.no_skip_missing,
    )

    # Sauvegarde du resume
    orchestrator.save_summary(summary)

    # Output JSON
    print("\n" + json.dumps(summary, indent=2))

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
