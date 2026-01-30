#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
============================================================================
FICHIER: openfarm_handler.py
DESCRIPTION: Handler pour l'API OpenFarm (base de donnees cultures)

Developpe par       : @Mouhammed
Ticket(s) associe(s): TICKET-130
Sprint              : Semaine 6 - Integration Sources Externes
============================================================================
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger("vertiflow.handlers.openfarm")


@dataclass
class OpenFarmResult:
    """Resultat de la recuperation des donnees OpenFarm."""

    success: bool
    timestamp: str
    source: str = "OPENFARM"
    provider: str = "OpenFarm.cc"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class OpenFarmHandler:
    """
    Handler pour l'API OpenFarm.

    OpenFarm est une base de donnees communautaire open source
    avec des informations detaillees sur la culture des plantes.

    API publique sans authentification.

    Documentation:
        https://github.com/openfarmcc/OpenFarm/blob/master/docs/api.apib
    """

    BASE_URL = "https://openfarm.cc/api/v1"

    # Cultures d'interet pour VertiFlow (herbes et legumes feuilles)
    CROPS_OF_INTEREST = [
        "basil",
        "lettuce",
        "spinach",
        "arugula",
        "mint",
        "cilantro",
        "parsley",
        "chives",
        "dill",
        "kale",
        "chard",
    ]

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        timeout: int = 30,
    ):
        self.output_dir = output_dir or Path("nifi_exchange/input/external/openfarm")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "VertiFlow-DataPlatform/1.0",
        })

        LOGGER.info("OpenFarm Handler initialized")

    def search_crop(self, query: str) -> Dict[str, Any]:
        """
        Recherche une culture par nom.

        Args:
            query: Nom de la culture (ex: "basil")

        Returns:
            Resultats de recherche
        """
        url = f"{self.BASE_URL}/crops"
        params = {"filter": query}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            LOGGER.warning("OpenFarm search failed for %s: %s", query, e)
            return {"data": []}

    def get_crop_details(self, crop_slug: str) -> Dict[str, Any]:
        """
        Recupere les details d'une culture specifique.

        Args:
            crop_slug: Identifiant de la culture

        Returns:
            Details complets de la culture
        """
        url = f"{self.BASE_URL}/crops/{crop_slug}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            LOGGER.warning("OpenFarm details failed for %s: %s", crop_slug, e)
            return {}

    def fetch_all_crops(self) -> OpenFarmResult:
        """
        Recupere les donnees pour toutes les cultures d'interet.

        Returns:
            OpenFarmResult avec donnees agronomiques
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        result = OpenFarmResult(
            success=False,
            timestamp=timestamp,
        )

        crops_data = {}

        for crop_name in self.CROPS_OF_INTEREST:
            try:
                # Recherche
                search_results = self.search_crop(crop_name)
                crop_list = search_results.get("data", [])

                if crop_list:
                    # Prendre le premier resultat
                    crop_info = crop_list[0]
                    crop_slug = crop_info.get("attributes", {}).get("slug", crop_name)

                    # Details complets
                    details = self.get_crop_details(crop_slug)

                    if details:
                        processed = self._process_crop_data(details)
                        crops_data[crop_name] = processed
                        LOGGER.info("Fetched data for crop: %s", crop_name)
                    else:
                        # Utiliser les donnees de base
                        crops_data[crop_name] = self._process_crop_data({"data": crop_info})

            except Exception as e:
                error_msg = f"Error fetching {crop_name}: {str(e)}"
                LOGGER.warning(error_msg)
                result.errors.append(error_msg)

        # Ajouter donnees de reference VertiFlow si OpenFarm incomplet
        crops_data = self._enrich_with_reference_data(crops_data)

        result.data = {
            "crops": crops_data,
            "summary": self._compute_summary(crops_data),
        }

        result.success = len(crops_data) > 0
        result.metadata = {
            "crops_requested": self.CROPS_OF_INTEREST,
            "crops_found": list(crops_data.keys()),
            "source": "openfarm.cc",
        }

        return result

    def _process_crop_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite et normalise les donnees d'une culture."""
        data = raw_data.get("data", {})
        attributes = data.get("attributes", {}) if isinstance(data, dict) else {}

        processed = {
            "name": attributes.get("name", "Unknown"),
            "slug": attributes.get("slug"),
            "binomial_name": attributes.get("binomial_name"),
            "description": attributes.get("description"),
            "sun_requirements": attributes.get("sun_requirements"),
            "sowing_method": attributes.get("sowing_method"),
            "spread": attributes.get("spread"),
            "row_spacing": attributes.get("row_spacing"),
            "height": attributes.get("height"),
            "growing_degree_days": attributes.get("growing_degree_days"),
            "svg_icon": attributes.get("svg_icon"),
            "main_image_path": attributes.get("main_image_path"),
            "tags": attributes.get("tags_array", []),
        }

        # Extraction des companions (plantes compagnes)
        companions = data.get("relationships", {}).get("companions", {}).get("data", [])
        processed["companions"] = [c.get("id") for c in companions if c.get("id")]

        return processed

    def _enrich_with_reference_data(self, crops_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrichit les donnees avec des references agronomiques VertiFlow.
        Ces donnees sont validees pour la culture verticale.
        """
        # Donnees de reference pour l'agriculture verticale
        reference_data = {
            "basil": {
                "optimal_temp_c": {"min": 18, "max": 24, "optimal": 21},
                "optimal_humidity_pct": {"min": 50, "max": 70, "optimal": 60},
                "optimal_ec_ms_cm": {"min": 1.2, "max": 2.0, "optimal": 1.6},
                "optimal_ph": {"min": 5.5, "max": 6.5, "optimal": 6.0},
                "dli_mol_m2_day": {"min": 12, "max": 20, "optimal": 17},
                "photoperiod_hours": 16,
                "days_to_harvest": {"min": 21, "max": 35, "optimal": 28},
                "yield_g_m2": {"min": 2000, "max": 4000, "optimal": 3000},
                "vertical_farming_suitability": "excellent",
            },
            "lettuce": {
                "optimal_temp_c": {"min": 15, "max": 22, "optimal": 18},
                "optimal_humidity_pct": {"min": 50, "max": 70, "optimal": 60},
                "optimal_ec_ms_cm": {"min": 0.8, "max": 1.4, "optimal": 1.1},
                "optimal_ph": {"min": 5.8, "max": 6.5, "optimal": 6.2},
                "dli_mol_m2_day": {"min": 10, "max": 17, "optimal": 14},
                "photoperiod_hours": 14,
                "days_to_harvest": {"min": 28, "max": 45, "optimal": 35},
                "yield_g_m2": {"min": 3000, "max": 5000, "optimal": 4000},
                "vertical_farming_suitability": "excellent",
            },
            "spinach": {
                "optimal_temp_c": {"min": 12, "max": 20, "optimal": 16},
                "optimal_humidity_pct": {"min": 50, "max": 70, "optimal": 60},
                "optimal_ec_ms_cm": {"min": 1.5, "max": 2.3, "optimal": 1.8},
                "optimal_ph": {"min": 6.0, "max": 7.0, "optimal": 6.5},
                "dli_mol_m2_day": {"min": 10, "max": 16, "optimal": 13},
                "photoperiod_hours": 12,
                "days_to_harvest": {"min": 25, "max": 40, "optimal": 32},
                "yield_g_m2": {"min": 2500, "max": 4500, "optimal": 3500},
                "vertical_farming_suitability": "excellent",
            },
            "arugula": {
                "optimal_temp_c": {"min": 15, "max": 22, "optimal": 18},
                "optimal_humidity_pct": {"min": 50, "max": 65, "optimal": 55},
                "optimal_ec_ms_cm": {"min": 1.0, "max": 1.8, "optimal": 1.4},
                "optimal_ph": {"min": 6.0, "max": 7.0, "optimal": 6.5},
                "dli_mol_m2_day": {"min": 10, "max": 16, "optimal": 13},
                "photoperiod_hours": 14,
                "days_to_harvest": {"min": 21, "max": 35, "optimal": 28},
                "yield_g_m2": {"min": 2000, "max": 3500, "optimal": 2750},
                "vertical_farming_suitability": "excellent",
            },
            "mint": {
                "optimal_temp_c": {"min": 18, "max": 25, "optimal": 21},
                "optimal_humidity_pct": {"min": 55, "max": 75, "optimal": 65},
                "optimal_ec_ms_cm": {"min": 1.6, "max": 2.4, "optimal": 2.0},
                "optimal_ph": {"min": 6.0, "max": 7.0, "optimal": 6.5},
                "dli_mol_m2_day": {"min": 12, "max": 18, "optimal": 15},
                "photoperiod_hours": 16,
                "days_to_harvest": {"min": 28, "max": 42, "optimal": 35},
                "yield_g_m2": {"min": 1800, "max": 3000, "optimal": 2400},
                "vertical_farming_suitability": "good",
            },
            "cilantro": {
                "optimal_temp_c": {"min": 15, "max": 23, "optimal": 19},
                "optimal_humidity_pct": {"min": 50, "max": 70, "optimal": 60},
                "optimal_ec_ms_cm": {"min": 1.2, "max": 2.0, "optimal": 1.6},
                "optimal_ph": {"min": 6.2, "max": 6.8, "optimal": 6.5},
                "dli_mol_m2_day": {"min": 10, "max": 16, "optimal": 13},
                "photoperiod_hours": 12,
                "days_to_harvest": {"min": 21, "max": 35, "optimal": 28},
                "yield_g_m2": {"min": 1500, "max": 2500, "optimal": 2000},
                "vertical_farming_suitability": "good",
            },
            "parsley": {
                "optimal_temp_c": {"min": 15, "max": 22, "optimal": 18},
                "optimal_humidity_pct": {"min": 50, "max": 70, "optimal": 60},
                "optimal_ec_ms_cm": {"min": 1.4, "max": 2.2, "optimal": 1.8},
                "optimal_ph": {"min": 5.5, "max": 6.5, "optimal": 6.0},
                "dli_mol_m2_day": {"min": 12, "max": 18, "optimal": 15},
                "photoperiod_hours": 14,
                "days_to_harvest": {"min": 35, "max": 50, "optimal": 42},
                "yield_g_m2": {"min": 1500, "max": 2800, "optimal": 2150},
                "vertical_farming_suitability": "good",
            },
            "chives": {
                "optimal_temp_c": {"min": 15, "max": 23, "optimal": 19},
                "optimal_humidity_pct": {"min": 50, "max": 70, "optimal": 60},
                "optimal_ec_ms_cm": {"min": 1.2, "max": 1.8, "optimal": 1.5},
                "optimal_ph": {"min": 6.0, "max": 7.0, "optimal": 6.5},
                "dli_mol_m2_day": {"min": 10, "max": 16, "optimal": 13},
                "photoperiod_hours": 14,
                "days_to_harvest": {"min": 60, "max": 90, "optimal": 75},
                "yield_g_m2": {"min": 1000, "max": 2000, "optimal": 1500},
                "vertical_farming_suitability": "good",
            },
            "dill": {
                "optimal_temp_c": {"min": 15, "max": 22, "optimal": 18},
                "optimal_humidity_pct": {"min": 45, "max": 65, "optimal": 55},
                "optimal_ec_ms_cm": {"min": 1.0, "max": 1.6, "optimal": 1.3},
                "optimal_ph": {"min": 5.5, "max": 6.5, "optimal": 6.0},
                "dli_mol_m2_day": {"min": 12, "max": 18, "optimal": 15},
                "photoperiod_hours": 14,
                "days_to_harvest": {"min": 28, "max": 45, "optimal": 35},
                "yield_g_m2": {"min": 1200, "max": 2200, "optimal": 1700},
                "vertical_farming_suitability": "good",
            },
            "kale": {
                "optimal_temp_c": {"min": 12, "max": 20, "optimal": 16},
                "optimal_humidity_pct": {"min": 50, "max": 70, "optimal": 60},
                "optimal_ec_ms_cm": {"min": 1.4, "max": 2.2, "optimal": 1.8},
                "optimal_ph": {"min": 6.0, "max": 7.0, "optimal": 6.5},
                "dli_mol_m2_day": {"min": 12, "max": 18, "optimal": 15},
                "photoperiod_hours": 14,
                "days_to_harvest": {"min": 35, "max": 55, "optimal": 45},
                "yield_g_m2": {"min": 2500, "max": 4000, "optimal": 3250},
                "vertical_farming_suitability": "excellent",
            },
            "chard": {
                "optimal_temp_c": {"min": 14, "max": 22, "optimal": 18},
                "optimal_humidity_pct": {"min": 50, "max": 70, "optimal": 60},
                "optimal_ec_ms_cm": {"min": 1.6, "max": 2.4, "optimal": 2.0},
                "optimal_ph": {"min": 6.0, "max": 7.0, "optimal": 6.5},
                "dli_mol_m2_day": {"min": 12, "max": 18, "optimal": 15},
                "photoperiod_hours": 14,
                "days_to_harvest": {"min": 40, "max": 60, "optimal": 50},
                "yield_g_m2": {"min": 2800, "max": 4500, "optimal": 3650},
                "vertical_farming_suitability": "excellent",
            },
        }

        # Enrichissement
        for crop_name, ref_data in reference_data.items():
            if crop_name in crops_data:
                crops_data[crop_name]["vertiflow_reference"] = ref_data
            else:
                crops_data[crop_name] = {
                    "name": crop_name.capitalize(),
                    "source": "vertiflow_reference",
                    "vertiflow_reference": ref_data,
                }

        return crops_data

    def _compute_summary(self, crops_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule un resume des donnees agronomiques."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_crops": len(crops_data),
            "crops_with_openfarm_data": 0,
            "crops_with_reference_data": 0,
            "excellent_suitability": [],
            "good_suitability": [],
        }

        for crop_name, data in crops_data.items():
            if data.get("binomial_name"):
                summary["crops_with_openfarm_data"] += 1

            ref = data.get("vertiflow_reference", {})
            if ref:
                summary["crops_with_reference_data"] += 1

                suitability = ref.get("vertical_farming_suitability")
                if suitability == "excellent":
                    summary["excellent_suitability"].append(crop_name)
                elif suitability == "good":
                    summary["good_suitability"].append(crop_name)

        return summary

    def save_results(self, result: OpenFarmResult) -> Path:
        """Sauvegarde les resultats au format JSON pour NiFi."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"openfarm_{timestamp}.json"
        filepath = self.output_dir / filename

        output_data = {
            "source": result.source,
            "provider": result.provider,
            "timestamp": result.timestamp,
            "success": result.success,
            "data": result.data,
            "metadata": result.metadata,
            "errors": result.errors,
            "target_columns": [
                "growing_degree_days",
                "sun_requirements",
                "spread_cm",
                "row_spacing_cm",
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        LOGGER.info("Saved OpenFarm data to %s", filepath)
        return filepath

    def run(self) -> Dict[str, Any]:
        """Point d'entree principal pour l'orchestrateur."""
        result = self.fetch_all_crops()
        filepath = self.save_results(result)

        return {
            "status": "ok" if result.success else "partial",
            "filepath": str(filepath),
            "crops_count": len(result.data.get("crops", {})),
            "errors": result.errors,
        }


def main():
    """Point d'entree CLI."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="OpenFarm Crops Handler")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("nifi_exchange/input/external/openfarm"),
        help="Output directory",
    )
    parser.add_argument(
        "--crop",
        type=str,
        help="Search specific crop",
    )
    args = parser.parse_args()

    handler = OpenFarmHandler(output_dir=args.output)

    if args.crop:
        result = handler.search_crop(args.crop)
        print(json.dumps(result, indent=2))
    else:
        output = handler.run()
        print(json.dumps(output, indent=2))

    return 0


if __name__ == "__main__":
    exit(main())
