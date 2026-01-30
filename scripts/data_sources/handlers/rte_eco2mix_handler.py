#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
============================================================================
FICHIER: rte_eco2mix_handler.py
DESCRIPTION: Handler OAuth2 pour l'API RTE ECO2MIX (reseau electrique francais)
             Donnees temps reel: production, consommation, prix, CO2

Developpe par       : @Mouhammed
Ticket(s) associe(s): TICKET-127
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
import base64

import requests

LOGGER = logging.getLogger("vertiflow.handlers.rte")


@dataclass
class RTEDataResult:
    """Resultat de la recuperation des donnees RTE."""

    success: bool
    timestamp: str
    source: str = "RTE_ECO2MIX"
    provider: str = "RTE France"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class RTEECO2MixHandler:
    """
    Handler OAuth2 pour l'API RTE ECO2MIX.

    RTE (Reseau de Transport d'Electricite) fournit des donnees en temps reel
    sur le reseau electrique francais via l'API Open Data.

    Endpoints disponibles:
        - /actual_generation: Production par filiere
        - /consumption: Consommation nationale
        - /co2_rate: Taux de CO2 de l'electricite
        - /exchange: Echanges transfrontaliers

    Authentication:
        OAuth2 Client Credentials Flow
        - Token endpoint: https://digital.iservices.rte-france.com/token/oauth/
        - Scopes: openid, eco2mix

    Documentation:
        https://data.rte-france.com/catalog/-/api/doc/user-guide/index.html
    """

    TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
    API_BASE_URL = "https://digital.iservices.rte-france.com/open_api/eco2mix/v2"

    # Endpoints disponibles
    ENDPOINTS = {
        "actual_generation": "/actual_generation",
        "consumption": "/consumption",
        "co2_rate": "/co2_rate",
        "exchange": "/exchange",
        "short_term": "/short_term",
    }

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        output_dir: Optional[Path] = None,
        timeout: int = 30,
    ):
        self.client_id = client_id or os.getenv("RTE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("RTE_CLIENT_SECRET")
        self.output_dir = output_dir or Path("nifi_exchange/input/external/rte_eco2mix")
        self.timeout = timeout
        self.session = requests.Session()
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

        LOGGER.info("RTE ECO2MIX Handler initialized")

    def _get_access_token(self) -> str:
        """
        Obtient un token d'acces OAuth2.
        Utilise le flow Client Credentials.
        """
        if self._access_token and self._token_expiry:
            if datetime.utcnow() < self._token_expiry - timedelta(minutes=5):
                return self._access_token

        if not self.client_id or not self.client_secret:
            raise EnvironmentError(
                "RTE_CLIENT_ID and RTE_CLIENT_SECRET must be configured. "
                "Register at https://data.rte-france.com/"
            )

        # Encodage Base64 des credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "client_credentials"}

        try:
            response = self.session.post(
                self.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=self.timeout,
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 7200)  # Default 2h
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            LOGGER.info("RTE OAuth2 token obtained (expires in %ds)", expires_in)
            return self._access_token

        except requests.RequestException as e:
            LOGGER.error("Failed to obtain RTE token: %s", e)
            raise

    def _make_api_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Effectue une requete authentifiee vers l'API RTE."""
        token = self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        url = f"{self.API_BASE_URL}{endpoint}"

        response = self.session.get(
            url,
            headers=headers,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()

        return response.json()

    def fetch_actual_generation(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Recupere la production electrique par filiere.

        Returns:
            Production par type (nucleaire, eolien, solaire, etc.)
        """
        params = {}

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._make_api_request(
            self.ENDPOINTS["actual_generation"],
            params=params,
        )

    def fetch_consumption(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Recupere la consommation electrique nationale.

        Returns:
            Consommation en MW
        """
        params = {}

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._make_api_request(
            self.ENDPOINTS["consumption"],
            params=params,
        )

    def fetch_co2_rate(self) -> Dict[str, Any]:
        """
        Recupere le taux de CO2 de l'electricite.

        Returns:
            Taux de CO2 en g/kWh
        """
        return self._make_api_request(self.ENDPOINTS["co2_rate"])

    def fetch_all_data(self) -> RTEDataResult:
        """
        Recupere toutes les donnees disponibles.

        Returns:
            RTEDataResult avec production, consommation, CO2
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        result = RTEDataResult(
            success=False,
            timestamp=timestamp,
        )

        try:
            # Production par filiere
            generation_data = self.fetch_actual_generation()
            result.data["generation"] = generation_data

            # Consommation
            consumption_data = self.fetch_consumption()
            result.data["consumption"] = consumption_data

            # Taux CO2
            co2_data = self.fetch_co2_rate()
            result.data["co2_rate"] = co2_data

            # Calcul des metriques agregees
            result.data["summary"] = self._compute_summary(generation_data)

            result.success = True
            result.metadata = {
                "endpoints_called": list(result.data.keys()),
                "api_version": "v2",
            }

        except requests.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            LOGGER.error(error_msg)
            result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            LOGGER.error(error_msg)
            result.errors.append(error_msg)

        return result

    def _compute_summary(self, generation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule des metriques agregees depuis les donnees de production."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "renewable_pct": 0.0,
            "nuclear_pct": 0.0,
            "fossil_pct": 0.0,
            "total_mw": 0.0,
        }

        try:
            # Extraction des valeurs (structure RTE)
            if "actual_generations_per_production_type" in generation_data:
                generations = generation_data["actual_generations_per_production_type"]

                renewable_sources = ["WIND", "SOLAR", "HYDRAULIC", "BIOENERGY"]
                fossil_sources = ["GAS", "COAL", "OIL"]

                total = 0
                renewable = 0
                nuclear = 0
                fossil = 0

                for gen in generations:
                    production_type = gen.get("production_type", "")
                    values = gen.get("values", [])

                    if values:
                        # Derniere valeur disponible
                        latest_value = values[-1].get("value", 0)
                        total += latest_value

                        if production_type == "NUCLEAR":
                            nuclear += latest_value
                        elif production_type in renewable_sources:
                            renewable += latest_value
                        elif production_type in fossil_sources:
                            fossil += latest_value

                if total > 0:
                    summary["total_mw"] = total
                    summary["renewable_pct"] = round((renewable / total) * 100, 2)
                    summary["nuclear_pct"] = round((nuclear / total) * 100, 2)
                    summary["fossil_pct"] = round((fossil / total) * 100, 2)

        except Exception as e:
            LOGGER.warning("Failed to compute summary: %s", e)

        return summary

    def get_demo_data(self) -> RTEDataResult:
        """
        Retourne des donnees de demonstration quand les credentials ne sont pas configures.
        Basees sur les moyennes du mix electrique francais.
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Mix electrique francais typique (source: RTE bilan 2024)
        demo_data = {
            "generation": {
                "actual_generations_per_production_type": [
                    {"production_type": "NUCLEAR", "values": [{"value": 42000}]},
                    {"production_type": "WIND", "values": [{"value": 8500}]},
                    {"production_type": "SOLAR", "values": [{"value": 4200}]},
                    {"production_type": "HYDRAULIC", "values": [{"value": 7800}]},
                    {"production_type": "GAS", "values": [{"value": 3500}]},
                    {"production_type": "BIOENERGY", "values": [{"value": 1200}]},
                ]
            },
            "consumption": {
                "values": [{"value": 58000, "updated_date": timestamp}]
            },
            "co2_rate": {
                "values": [{"value": 45, "updated_date": timestamp}]  # g CO2/kWh
            },
            "summary": {
                "timestamp": timestamp,
                "total_mw": 67200,
                "renewable_pct": 32.3,  # (8500+4200+7800+1200)/67200
                "nuclear_pct": 62.5,
                "fossil_pct": 5.2,
                "co2_intensity_g_kwh": 45,
            },
        }

        return RTEDataResult(
            success=True,
            timestamp=timestamp,
            data=demo_data,
            metadata={
                "source_type": "demo",
                "note": "Donnees de demonstration - configurez RTE_CLIENT_ID/SECRET pour donnees reelles",
            },
        )

    def save_results(self, result: RTEDataResult) -> Path:
        """Sauvegarde les resultats au format JSON pour NiFi."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"rte_eco2mix_{timestamp}.json"
        filepath = self.output_dir / filename

        output_data = {
            "source": result.source,
            "provider": result.provider,
            "timestamp": result.timestamp,
            "success": result.success,
            "data": result.data,
            "metadata": result.metadata,
            "errors": result.errors,
            "target_columns": ["energy_price_kwh", "renewable_energy_pct", "carbon_intensity_g_co2_kwh"],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        LOGGER.info("Saved RTE data to %s", filepath)
        return filepath

    def run(self) -> Dict[str, Any]:
        """Point d'entree principal pour l'orchestrateur."""
        # Verification des credentials
        if not self.client_id or not self.client_secret:
            LOGGER.warning("RTE credentials not configured, using demo data")
            result = self.get_demo_data()
        else:
            result = self.fetch_all_data()

        filepath = self.save_results(result)

        return {
            "status": "ok" if result.success else "error",
            "filepath": str(filepath),
            "data_points": len(result.data),
            "errors": result.errors,
        }


def main():
    """Point d'entree CLI."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="RTE ECO2MIX Handler")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("nifi_exchange/input/external/rte_eco2mix"),
        help="Output directory",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo data instead of live API",
    )
    args = parser.parse_args()

    handler = RTEECO2MixHandler(output_dir=args.output)

    if args.demo:
        result = handler.get_demo_data()
        filepath = handler.save_results(result)
        output = {"status": "ok", "filepath": str(filepath), "mode": "demo"}
    else:
        output = handler.run()

    print(json.dumps(output, indent=2))
    return 0 if output["status"] == "ok" else 1


if __name__ == "__main__":
    exit(main())
