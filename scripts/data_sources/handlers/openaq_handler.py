#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
============================================================================
FICHIER: openaq_handler.py
DESCRIPTION: Handler pour l'API OpenAQ (qualite de l'air mondiale)

Developpe par       : @Mouhammed
Ticket(s) associe(s): TICKET-129
Sprint              : Semaine 6 - Integration Sources Externes
============================================================================
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger("vertiflow.handlers.openaq")


@dataclass
class OpenAQResult:
    """Resultat de la recuperation des donnees OpenAQ."""

    success: bool
    timestamp: str
    source: str = "OPENAQ"
    provider: str = "OpenAQ"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class OpenAQHandler:
    """
    Handler pour l'API OpenAQ.

    OpenAQ agregge les donnees de qualite de l'air de sources mondiales.
    API gratuite et open source.

    Parametres mesures:
        - PM2.5: Particules fines < 2.5 microns
        - PM10: Particules < 10 microns
        - CO2: Dioxyde de carbone
        - NO2: Dioxyde d'azote
        - O3: Ozone
        - SO2: Dioxyde de soufre

    Documentation:
        https://docs.openaq.org/
    """

    BASE_URL = "https://api.openaq.org/v2"

    # Coordonnees par defaut (Casablanca, Maroc)
    DEFAULT_COORDS = {
        "latitude": 33.5731,
        "longitude": -7.5898,
    }

    # Parametres d'interet pour l'agriculture
    PARAMETERS = ["pm25", "pm10", "co2", "no2", "o3"]

    # Seuils de qualite de l'air (OMS)
    AIR_QUALITY_THRESHOLDS = {
        "pm25": {
            "good": 15,      # ug/m3
            "moderate": 35,
            "poor": 55,
            "very_poor": 150,
        },
        "pm10": {
            "good": 45,
            "moderate": 75,
            "poor": 100,
            "very_poor": 200,
        },
        "no2": {
            "good": 40,      # ug/m3
            "moderate": 100,
            "poor": 200,
            "very_poor": 400,
        },
        "o3": {
            "good": 60,
            "moderate": 100,
            "poor": 140,
            "very_poor": 180,
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: Optional[Path] = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("OPENAQ_API_KEY")  # Optionnel
        self.output_dir = output_dir or Path("nifi_exchange/input/external/openaq")
        self.timeout = timeout
        self.session = requests.Session()

        # API key optionnelle (augmente rate limits)
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})

        self.session.headers.update({
            "Accept": "application/json",
        })

        LOGGER.info("OpenAQ Handler initialized")

    def fetch_latest_measurements(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: int = 25000,  # metres
        parameters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Recupere les dernieres mesures de qualite de l'air.

        Args:
            latitude: Latitude du point central
            longitude: Longitude du point central
            radius: Rayon de recherche en metres
            parameters: Liste des parametres (pm25, pm10, etc.)

        Returns:
            Mesures les plus recentes
        """
        lat = latitude or self.DEFAULT_COORDS["latitude"]
        lon = longitude or self.DEFAULT_COORDS["longitude"]
        params_list = parameters or self.PARAMETERS

        url = f"{self.BASE_URL}/latest"

        params = {
            "coordinates": f"{lat},{lon}",
            "radius": radius,
            "parameter": params_list,
            "limit": 100,
            "order_by": "lastUpdated",
            "sort": "desc",
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            LOGGER.warning("OpenAQ API request failed: %s", e)
            return {"results": []}

    def fetch_measurements_history(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        hours_back: int = 24,
        parameters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Recupere l'historique des mesures.

        Args:
            latitude: Latitude
            longitude: Longitude
            hours_back: Nombre d'heures d'historique
            parameters: Parametres a recuperer

        Returns:
            Historique des mesures
        """
        lat = latitude or self.DEFAULT_COORDS["latitude"]
        lon = longitude or self.DEFAULT_COORDS["longitude"]
        params_list = parameters or self.PARAMETERS

        url = f"{self.BASE_URL}/measurements"

        date_from = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()

        params = {
            "coordinates": f"{lat},{lon}",
            "radius": 50000,
            "parameter": params_list,
            "date_from": date_from,
            "limit": 1000,
            "order_by": "datetime",
            "sort": "desc",
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            LOGGER.warning("OpenAQ history request failed: %s", e)
            return {"results": []}

    def fetch_all_data(self) -> OpenAQResult:
        """
        Recupere toutes les donnees de qualite de l'air.

        Returns:
            OpenAQResult avec mesures et analyses
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        result = OpenAQResult(
            success=False,
            timestamp=timestamp,
        )

        try:
            # Mesures actuelles
            latest_data = self.fetch_latest_measurements()

            # Historique 24h
            history_data = self.fetch_measurements_history(hours_back=24)

            # Analyse des donnees
            analysis = self._analyze_air_quality(latest_data)

            result.data = {
                "latest": latest_data,
                "history_24h": history_data,
                "analysis": analysis,
                "location": self.DEFAULT_COORDS,
            }

            result.success = len(latest_data.get("results", [])) > 0
            result.metadata = {
                "parameters_requested": self.PARAMETERS,
                "location": "Casablanca, Morocco",
                "measurements_count": len(latest_data.get("results", [])),
            }

        except Exception as e:
            error_msg = f"Error fetching air quality data: {str(e)}"
            LOGGER.error(error_msg)
            result.errors.append(error_msg)

        return result

    def _analyze_air_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les donnees de qualite de l'air."""
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_quality": "unknown",
            "parameters": {},
            "recommendations": [],
        }

        results = data.get("results", [])

        if not results:
            analysis["overall_quality"] = "no_data"
            analysis["recommendations"].append("Aucune station de mesure proche trouvee")
            return analysis

        # Agregation par parametre
        param_values = {}
        for measurement in results:
            param = measurement.get("parameter")
            value = measurement.get("value")

            if param and value is not None:
                if param not in param_values:
                    param_values[param] = []
                param_values[param].append(value)

        # Calcul des moyennes et evaluation
        worst_quality = "good"
        quality_order = ["good", "moderate", "poor", "very_poor"]

        for param, values in param_values.items():
            avg_value = sum(values) / len(values)
            quality = self._evaluate_parameter_quality(param, avg_value)

            analysis["parameters"][param] = {
                "average": round(avg_value, 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "measurements_count": len(values),
                "quality": quality,
                "unit": "ug/m3",
            }

            # Mise a jour de la qualite globale
            if quality_order.index(quality) > quality_order.index(worst_quality):
                worst_quality = quality

        analysis["overall_quality"] = worst_quality

        # Recommandations pour l'agriculture verticale
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    def _evaluate_parameter_quality(self, param: str, value: float) -> str:
        """Evalue la qualite pour un parametre donne."""
        thresholds = self.AIR_QUALITY_THRESHOLDS.get(param)

        if not thresholds:
            return "unknown"

        if value <= thresholds["good"]:
            return "good"
        elif value <= thresholds["moderate"]:
            return "moderate"
        elif value <= thresholds["poor"]:
            return "poor"
        else:
            return "very_poor"

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Genere des recommandations pour l'agriculture verticale."""
        recommendations = []
        overall = analysis.get("overall_quality", "unknown")

        if overall == "good":
            recommendations.append("Qualite de l'air excellente - Ventilation naturelle recommandee")
        elif overall == "moderate":
            recommendations.append("Qualite de l'air acceptable - Filtration standard suffisante")
        elif overall == "poor":
            recommendations.append("Qualite de l'air degradee - Augmenter la filtration HEPA")
            recommendations.append("Limiter les echanges air exterieur/interieur")
        elif overall == "very_poor":
            recommendations.append("ALERTE: Qualite de l'air mauvaise - Mode recirculation active")
            recommendations.append("Filtration HEPA maximale recommandee")
            recommendations.append("Reporter les operations de ventilation")

        # Recommandations specifiques PM2.5
        pm25_data = analysis.get("parameters", {}).get("pm25", {})
        if pm25_data.get("average", 0) > 35:
            recommendations.append("PM2.5 eleve - Verifier les filtres de l'installation")

        return recommendations

    def save_results(self, result: OpenAQResult) -> Path:
        """Sauvegarde les resultats au format JSON pour NiFi."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"openaq_{timestamp}.json"
        filepath = self.output_dir / filename

        output_data = {
            "source": result.source,
            "provider": result.provider,
            "timestamp": result.timestamp,
            "success": result.success,
            "data": result.data,
            "metadata": result.metadata,
            "errors": result.errors,
            "target_columns": ["ext_air_quality_pm25", "ext_air_quality_pm10"],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        LOGGER.info("Saved OpenAQ data to %s", filepath)
        return filepath

    def run(self) -> Dict[str, Any]:
        """Point d'entree principal pour l'orchestrateur."""
        result = self.fetch_all_data()
        filepath = self.save_results(result)

        return {
            "status": "ok" if result.success else "partial",
            "filepath": str(filepath),
            "overall_quality": result.data.get("analysis", {}).get("overall_quality", "unknown"),
            "errors": result.errors,
        }


def main():
    """Point d'entree CLI."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="OpenAQ Air Quality Handler")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("nifi_exchange/input/external/openaq"),
        help="Output directory",
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=33.5731,
        help="Latitude",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=-7.5898,
        help="Longitude",
    )
    args = parser.parse_args()

    handler = OpenAQHandler(output_dir=args.output)
    output = handler.run()

    print(json.dumps(output, indent=2))
    return 0 if output["status"] == "ok" else 1


if __name__ == "__main__":
    exit(main())
