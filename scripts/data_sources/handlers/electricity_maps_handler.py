#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
============================================================================
FICHIER: electricity_maps_handler.py
DESCRIPTION: Handler pour l'API Electricity Maps (intensite carbone electrique)

Developpe par       : @Mouhammed
Ticket(s) associe(s): TICKET-128
Sprint              : Semaine 6 - Integration Sources Externes
============================================================================
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger("vertiflow.handlers.electricity_maps")


@dataclass
class ElectricityMapsResult:
    """Resultat de la recuperation des donnees Electricity Maps."""

    success: bool
    timestamp: str
    source: str = "ELECTRICITY_MAPS"
    provider: str = "Electricity Maps"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class ElectricityMapsHandler:
    """
    Handler pour l'API Electricity Maps.

    Electricity Maps fournit des donnees en temps reel sur l'intensite
    carbone de l'electricite par zone geographique.

    Endpoints:
        - /carbon-intensity/latest: Intensite carbone actuelle
        - /power-breakdown/latest: Repartition de la production
        - /carbon-intensity/history: Historique

    Free tier: 100 requests/day (sans cle) ou via app.electricitymaps.com

    Documentation:
        https://static.electricitymaps.com/api/docs/index.html
    """

    BASE_URL = "https://api.electricitymap.org/v3"

    # Zones d'interet pour VertiFlow
    ZONES = {
        "morocco": "MA",
        "france": "FR",
        "spain": "ES",
        "portugal": "PT",
        "germany": "DE",
    }

    # Intensites carbone de reference (g CO2/kWh) - fallback
    REFERENCE_CARBON_INTENSITY = {
        "MA": 650,  # Maroc (mix fossile + renouvelable)
        "FR": 45,   # France (nucleaire dominant)
        "ES": 180,  # Espagne
        "PT": 200,  # Portugal
        "DE": 350,  # Allemagne
    }

    def __init__(
        self,
        api_token: Optional[str] = None,
        output_dir: Optional[Path] = None,
        timeout: int = 30,
    ):
        self.api_token = api_token or os.getenv("ELECTRICITY_MAPS_TOKEN")
        self.output_dir = output_dir or Path("nifi_exchange/input/external/electricity_maps")
        self.timeout = timeout
        self.session = requests.Session()

        if self.api_token:
            self.session.headers.update({"auth-token": self.api_token})

        LOGGER.info("Electricity Maps Handler initialized")

    def fetch_carbon_intensity(self, zone: str = "MA") -> Dict[str, Any]:
        """
        Recupere l'intensite carbone actuelle pour une zone.

        Args:
            zone: Code ISO de la zone (ex: MA, FR, ES)

        Returns:
            Donnees d'intensite carbone
        """
        url = f"{self.BASE_URL}/carbon-intensity/latest"
        params = {"zone": zone}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            LOGGER.warning("API request failed for zone %s: %s", zone, e)
            # Retourner donnees de reference
            return self._get_fallback_data(zone)

    def fetch_power_breakdown(self, zone: str = "MA") -> Dict[str, Any]:
        """
        Recupere la repartition de la production electrique.

        Args:
            zone: Code ISO de la zone

        Returns:
            Repartition par source (solaire, eolien, etc.)
        """
        url = f"{self.BASE_URL}/power-breakdown/latest"
        params = {"zone": zone}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            LOGGER.warning("Power breakdown request failed: %s", e)
            return {}

    def fetch_all_zones(self) -> ElectricityMapsResult:
        """
        Recupere les donnees pour toutes les zones d'interet.

        Returns:
            ElectricityMapsResult avec donnees multi-zones
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        result = ElectricityMapsResult(
            success=False,
            timestamp=timestamp,
        )

        zones_data = {}

        for zone_name, zone_code in self.ZONES.items():
            try:
                carbon_data = self.fetch_carbon_intensity(zone_code)
                power_data = self.fetch_power_breakdown(zone_code)

                zones_data[zone_name] = {
                    "zone_code": zone_code,
                    "carbon_intensity": carbon_data,
                    "power_breakdown": power_data,
                }

                LOGGER.info("Fetched data for zone %s (%s)", zone_name, zone_code)

            except Exception as e:
                error_msg = f"Error fetching {zone_name}: {str(e)}"
                LOGGER.warning(error_msg)
                result.errors.append(error_msg)

        result.data = {
            "zones": zones_data,
            "primary_zone": "morocco",
            "summary": self._compute_summary(zones_data),
        }

        result.success = len(zones_data) > 0
        result.metadata = {
            "zones_requested": list(self.ZONES.keys()),
            "zones_fetched": list(zones_data.keys()),
            "api_version": "v3",
        }

        return result

    def _get_fallback_data(self, zone: str) -> Dict[str, Any]:
        """Retourne des donnees de reference quand l'API n'est pas disponible."""
        carbon_intensity = self.REFERENCE_CARBON_INTENSITY.get(zone, 400)

        return {
            "zone": zone,
            "carbonIntensity": carbon_intensity,
            "datetime": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            "source": "reference",
            "note": "Donnees de reference - API non disponible",
        }

    def _compute_summary(self, zones_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule un resume des donnees multi-zones."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "zones_count": len(zones_data),
        }

        # Extraction des intensites carbone
        intensities = {}
        for zone_name, data in zones_data.items():
            carbon_data = data.get("carbon_intensity", {})
            intensity = carbon_data.get("carbonIntensity")
            if intensity:
                intensities[zone_name] = intensity

        if intensities:
            summary["carbon_intensities_g_kwh"] = intensities
            summary["lowest_carbon_zone"] = min(intensities, key=intensities.get)
            summary["highest_carbon_zone"] = max(intensities, key=intensities.get)
            summary["average_intensity"] = round(sum(intensities.values()) / len(intensities), 2)

        return summary

    def get_morocco_data(self) -> Dict[str, Any]:
        """
        Raccourci pour recuperer les donnees du Maroc.
        Zone principale pour VertiFlow.
        """
        carbon_data = self.fetch_carbon_intensity("MA")
        power_data = self.fetch_power_breakdown("MA")

        return {
            "zone": "Morocco",
            "zone_code": "MA",
            "carbon_intensity_g_kwh": carbon_data.get("carbonIntensity", 650),
            "power_breakdown": power_data,
            "timestamp": datetime.utcnow().isoformat(),
            "recommendations": self._get_recommendations(carbon_data.get("carbonIntensity", 650)),
        }

    def _get_recommendations(self, intensity: float) -> List[str]:
        """Genere des recommandations basees sur l'intensite carbone."""
        recommendations = []

        if intensity < 100:
            recommendations.append("Intensite carbone faible - Periode optimale pour operations intensives")
        elif intensity < 300:
            recommendations.append("Intensite carbone moderee - Operations normales")
        else:
            recommendations.append("Intensite carbone elevee - Privilegier heures creuses si possible")

        if intensity > 500:
            recommendations.append("Considerez le stockage d'energie pour periodes a faible intensite")

        return recommendations

    def save_results(self, result: ElectricityMapsResult) -> Path:
        """Sauvegarde les resultats au format JSON pour NiFi."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"electricity_maps_{timestamp}.json"
        filepath = self.output_dir / filename

        output_data = {
            "source": result.source,
            "provider": result.provider,
            "timestamp": result.timestamp,
            "success": result.success,
            "data": result.data,
            "metadata": result.metadata,
            "errors": result.errors,
            "target_columns": ["carbon_intensity_g_co2_kwh"],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        LOGGER.info("Saved Electricity Maps data to %s", filepath)
        return filepath

    def run(self) -> Dict[str, Any]:
        """Point d'entree principal pour l'orchestrateur."""
        result = self.fetch_all_zones()
        filepath = self.save_results(result)

        return {
            "status": "ok" if result.success else "partial",
            "filepath": str(filepath),
            "zones_count": len(result.data.get("zones", {})),
            "errors": result.errors,
        }


def main():
    """Point d'entree CLI."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="Electricity Maps Handler")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("nifi_exchange/input/external/electricity_maps"),
        help="Output directory",
    )
    parser.add_argument(
        "--zone",
        type=str,
        default="MA",
        help="Zone code (MA, FR, ES, etc.)",
    )
    args = parser.parse_args()

    handler = ElectricityMapsHandler(output_dir=args.output)
    output = handler.run()

    print(json.dumps(output, indent=2))
    return 0 if output["status"] == "ok" else 1


if __name__ == "__main__":
    exit(main())
