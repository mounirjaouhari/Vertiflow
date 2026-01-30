#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
============================================================================
FICHIER: onee_tarifs_scraper.py
DESCRIPTION: Scraper pour les tarifs electricite ONEE (Office National
             de l'Electricite et de l'Eau potable - Maroc)

Developpe par       : @Mouhammed
Ticket(s) associe(s): TICKET-126
Sprint              : Semaine 6 - Integration Sources Externes
============================================================================
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger("vertiflow.scrapers.onee")


@dataclass
class ElectricityTariff:
    """Structure pour un tarif electricite."""

    category: str  # Residentiel, Professionnel, Industriel
    voltage_level: str  # BT (Basse Tension), MT (Moyenne Tension), HT (Haute Tension)
    time_period: str  # Heures Pleines, Heures Creuses, Pointe
    price_dh_kwh: float  # Prix en Dirhams/kWh
    price_eur_kwh: float  # Prix converti en EUR/kWh
    vat_included: bool
    effective_date: str
    notes: Optional[str] = None


@dataclass
class ONEEScrapingResult:
    """Resultat du scraping ONEE."""

    success: bool
    timestamp: str
    source: str = "ONEE_TARIFS"
    provider: str = "Office National de l'Electricite et de l'Eau potable (Maroc)"
    tariffs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class ONEETarifsScraper:
    """
    Scraper pour les tarifs electricite ONEE Maroc.

    L'ONEE publie les tarifs sur son site officiel. Ce scraper recupere
    les grilles tarifaires pour les differentes categories de clients.

    Sources:
        - https://www.one.org.ma/FR/pages/tarifs.asp
        - Documents PDF officiels ONEE
    """

    BASE_URL = "https://www.one.org.ma"
    TARIFS_URL = "https://www.one.org.ma/FR/pages/tarifs.asp"

    # Taux de conversion MAD -> EUR (approximatif, a actualiser)
    MAD_TO_EUR = 0.092  # 1 MAD = ~0.092 EUR (janvier 2026)

    # Tarifs officiels ONEE 2024-2025 (source: documents ONEE)
    # Ces valeurs sont utilisees comme fallback ou reference
    OFFICIAL_TARIFFS = {
        "industriel_mt": {
            "heures_pleines": {
                "pointe": 1.4691,  # DH/kWh TTC
                "jour": 1.0542,
                "soir": 1.0542,
            },
            "heures_creuses": {
                "nuit": 0.6792,
            },
            "prime_fixe": 27.95,  # DH/kVA/mois
        },
        "professionnel_bt": {
            "tranche_1": 1.0847,  # 0-100 kWh
            "tranche_2": 1.1989,  # 101-500 kWh
            "tranche_3": 1.4216,  # > 500 kWh
        },
        "residentiel_bt": {
            "tranche_1": 0.9010,  # 0-100 kWh
            "tranche_2": 1.0847,  # 101-150 kWh
            "tranche_3": 1.1989,  # 151-200 kWh
            "tranche_4": 1.3687,  # 201-300 kWh
            "tranche_5": 1.5981,  # 301-500 kWh
            "tranche_6": 1.6905,  # > 500 kWh
        },
        "agricole": {
            "pompage_bt": 0.8413,
            "pompage_mt": 0.6521,
        },
    }

    # Periodes horaires (tarification Moyenne Tension)
    TIME_PERIODS = {
        "pointe": {"start": "17:00", "end": "22:00", "months": [12, 1, 2]},  # Hiver soir
        "heures_pleines_jour": {"start": "07:00", "end": "17:00"},
        "heures_pleines_soir": {"start": "22:00", "end": "23:00"},
        "heures_creuses": {"start": "23:00", "end": "07:00"},
    }

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        timeout: int = 30,
    ):
        self.output_dir = output_dir or Path("nifi_exchange/input/external/onee_tarifs")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,ar;q=0.8,en;q=0.7",
        })
        LOGGER.info("ONEE Scraper initialized (output=%s)", self.output_dir)

    def fetch_tariffs(self) -> ONEEScrapingResult:
        """
        Recupere les tarifs electricite depuis le site ONEE.

        Returns:
            ONEEScrapingResult avec les tarifs et metadonnees
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        result = ONEEScrapingResult(
            success=False,
            timestamp=timestamp,
            metadata={
                "currency": "MAD",
                "exchange_rate_eur": self.MAD_TO_EUR,
            }
        )

        try:
            # Tentative de scraping du site ONEE
            tariffs = self._scrape_onee_website()

            if not tariffs:
                # Fallback vers les tarifs officiels pre-configures
                LOGGER.warning("Web scraping failed, using official reference tariffs")
                tariffs = self._get_official_tariffs()

            result.tariffs = tariffs
            result.success = len(tariffs) > 0
            result.metadata["total_tariffs"] = len(tariffs)
            result.metadata["source_type"] = "scraped" if self._last_scrape_success else "reference"

        except Exception as e:
            error_msg = f"Error fetching ONEE tariffs: {str(e)}"
            LOGGER.error(error_msg)
            result.errors.append(error_msg)

            # Fallback en cas d'erreur
            tariffs = self._get_official_tariffs()
            result.tariffs = tariffs
            result.success = len(tariffs) > 0

        return result

    _last_scrape_success = False

    def _scrape_onee_website(self) -> List[Dict[str, Any]]:
        """Tente de scraper le site web ONEE."""
        tariffs: List[Dict[str, Any]] = []
        self._last_scrape_success = False

        try:
            response = self.session.get(self.TARIFS_URL, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            tariffs = self._parse_tariff_tables(soup)

            if tariffs:
                self._last_scrape_success = True

        except requests.RequestException as e:
            LOGGER.warning("Failed to scrape ONEE website: %s", e)

        return tariffs

    def _parse_tariff_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse les tableaux de tarifs du site ONEE."""
        tariffs: List[Dict[str, Any]] = []

        # Recherche des tableaux contenant les tarifs
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                cells = row.find_all(["th", "td"])
                cell_texts = [cell.get_text(strip=True) for cell in cells]

                # Detection des lignes contenant des tarifs
                for text in cell_texts:
                    price_match = re.search(r"(\d+[.,]\d+)\s*(DH|MAD)?", text)
                    if price_match:
                        # Extraction et structuration du tarif
                        tariff_entry = self._extract_tariff_entry(cell_texts)
                        if tariff_entry:
                            tariffs.append(tariff_entry)
                        break

        return tariffs

    def _extract_tariff_entry(self, cells: List[str]) -> Optional[Dict[str, Any]]:
        """Extrait une entree de tarif depuis une ligne de tableau."""
        try:
            # Recherche du prix dans les cellules
            price_dh = None
            category = "Non specifie"

            for cell in cells:
                # Extraction du prix
                price_match = re.search(r"(\d+[.,]\d+)", cell)
                if price_match and not price_dh:
                    price_str = price_match.group(1).replace(",", ".")
                    price_dh = float(price_str)

                # Detection de la categorie
                cell_lower = cell.lower()
                if "industriel" in cell_lower:
                    category = "Industriel"
                elif "professionnel" in cell_lower:
                    category = "Professionnel"
                elif "residentiel" in cell_lower or "domestique" in cell_lower:
                    category = "Residentiel"
                elif "agricole" in cell_lower:
                    category = "Agricole"

            if price_dh:
                return {
                    "category": category,
                    "price_dh_kwh": price_dh,
                    "price_eur_kwh": round(price_dh * self.MAD_TO_EUR, 4),
                    "currency": "MAD",
                    "source": "ONEE_WEB",
                    "scraped_at": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            LOGGER.debug("Failed to extract tariff entry: %s", e)

        return None

    def _get_official_tariffs(self) -> List[Dict[str, Any]]:
        """
        Retourne les tarifs officiels ONEE pre-configures.
        Source: Grille tarifaire ONEE 2024-2025
        """
        tariffs: List[Dict[str, Any]] = []
        current_date = datetime.utcnow().strftime("%Y-%m-%d")

        # Tarifs Industriel Moyenne Tension (pertinent pour VertiFlow)
        mt_tariffs = self.OFFICIAL_TARIFFS["industriel_mt"]

        # Heures de pointe
        tariffs.append({
            "category": "Industriel",
            "voltage_level": "MT",
            "time_period": "Pointe (17h-22h hiver)",
            "price_dh_kwh": mt_tariffs["heures_pleines"]["pointe"],
            "price_eur_kwh": round(mt_tariffs["heures_pleines"]["pointe"] * self.MAD_TO_EUR, 4),
            "currency": "MAD",
            "vat_included": True,
            "effective_date": "2024-01-01",
            "source": "ONEE_OFFICIAL",
            "scraped_at": current_date,
            "notes": "Tarif pointe hiver (decembre-fevrier, 17h-22h)",
        })

        # Heures pleines jour
        tariffs.append({
            "category": "Industriel",
            "voltage_level": "MT",
            "time_period": "Heures Pleines Jour (07h-17h)",
            "price_dh_kwh": mt_tariffs["heures_pleines"]["jour"],
            "price_eur_kwh": round(mt_tariffs["heures_pleines"]["jour"] * self.MAD_TO_EUR, 4),
            "currency": "MAD",
            "vat_included": True,
            "effective_date": "2024-01-01",
            "source": "ONEE_OFFICIAL",
            "scraped_at": current_date,
        })

        # Heures pleines soir
        tariffs.append({
            "category": "Industriel",
            "voltage_level": "MT",
            "time_period": "Heures Pleines Soir (22h-23h)",
            "price_dh_kwh": mt_tariffs["heures_pleines"]["soir"],
            "price_eur_kwh": round(mt_tariffs["heures_pleines"]["soir"] * self.MAD_TO_EUR, 4),
            "currency": "MAD",
            "vat_included": True,
            "effective_date": "2024-01-01",
            "source": "ONEE_OFFICIAL",
            "scraped_at": current_date,
        })

        # Heures creuses
        tariffs.append({
            "category": "Industriel",
            "voltage_level": "MT",
            "time_period": "Heures Creuses (23h-07h)",
            "price_dh_kwh": mt_tariffs["heures_creuses"]["nuit"],
            "price_eur_kwh": round(mt_tariffs["heures_creuses"]["nuit"] * self.MAD_TO_EUR, 4),
            "currency": "MAD",
            "vat_included": True,
            "effective_date": "2024-01-01",
            "source": "ONEE_OFFICIAL",
            "scraped_at": current_date,
            "notes": "Tarif optimal pour operations nocturnes (LED, climatisation)",
        })

        # Prime fixe MT
        tariffs.append({
            "category": "Industriel",
            "voltage_level": "MT",
            "time_period": "Prime Fixe Mensuelle",
            "price_dh_kwh": mt_tariffs["prime_fixe"],
            "price_eur_kwh": round(mt_tariffs["prime_fixe"] * self.MAD_TO_EUR, 4),
            "currency": "MAD",
            "unit": "DH/kVA/mois",
            "vat_included": True,
            "effective_date": "2024-01-01",
            "source": "ONEE_OFFICIAL",
            "scraped_at": current_date,
            "notes": "Prime fixe par kVA souscrit",
        })

        # Tarif agricole (pompage)
        for pump_type, price in self.OFFICIAL_TARIFFS["agricole"].items():
            voltage = "BT" if "bt" in pump_type else "MT"
            tariffs.append({
                "category": "Agricole",
                "voltage_level": voltage,
                "time_period": f"Pompage {voltage}",
                "price_dh_kwh": price,
                "price_eur_kwh": round(price * self.MAD_TO_EUR, 4),
                "currency": "MAD",
                "vat_included": True,
                "effective_date": "2024-01-01",
                "source": "ONEE_OFFICIAL",
                "scraped_at": current_date,
                "notes": "Tarif special agriculture/irrigation",
            })

        return tariffs

    def get_optimal_tariff_periods(self) -> Dict[str, Any]:
        """
        Retourne les periodes optimales pour la consommation electrique.
        Utile pour l'optimisation energetique de VertiFlow.
        """
        return {
            "optimal_periods": [
                {
                    "period": "Heures Creuses",
                    "start": "23:00",
                    "end": "07:00",
                    "price_dh_kwh": 0.6792,
                    "savings_pct": 36,  # vs heures pleines jour
                    "recommended_operations": [
                        "Climatisation pre-conditionnement",
                        "Eclairage LED intensif",
                        "Pompes circulation nutriments",
                        "Backup systemes",
                    ],
                },
                {
                    "period": "Heures Pleines Jour",
                    "start": "07:00",
                    "end": "17:00",
                    "price_dh_kwh": 1.0542,
                    "recommended_operations": [
                        "Operations normales",
                        "Photoperiode principale",
                    ],
                },
            ],
            "avoid_periods": [
                {
                    "period": "Pointe Hiver",
                    "start": "17:00",
                    "end": "22:00",
                    "months": ["Decembre", "Janvier", "Fevrier"],
                    "price_dh_kwh": 1.4691,
                    "surcharge_pct": 39,  # vs heures pleines
                    "recommendations": [
                        "Reduire consommation LED",
                        "Reporter operations non-critiques",
                        "Utiliser stockage thermique",
                    ],
                },
            ],
            "monthly_prime_fixed": {
                "price_dh_kva": 27.95,
                "note": "Optimiser puissance souscrite pour minimiser prime fixe",
            },
        }

    def save_results(self, result: ONEEScrapingResult) -> Path:
        """Sauvegarde les resultats au format JSON pour NiFi."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"onee_tarifs_{timestamp}.json"
        filepath = self.output_dir / filename

        output_data = {
            "source": result.source,
            "provider": result.provider,
            "timestamp": result.timestamp,
            "success": result.success,
            "data": {
                "tariffs": result.tariffs,
                "optimal_periods": self.get_optimal_tariff_periods(),
                "summary": {
                    "total_tariffs": len(result.tariffs),
                    "categories": list(set(t.get("category", "") for t in result.tariffs)),
                    "voltage_levels": list(set(t.get("voltage_level", "") for t in result.tariffs)),
                },
            },
            "metadata": result.metadata,
            "errors": result.errors,
            "target_columns": ["energy_price_kwh", "peak_hours_tariff", "off_peak_tariff"],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        LOGGER.info("Saved ONEE tariffs to %s", filepath)
        return filepath

    def run(self) -> Dict[str, Any]:
        """Point d'entree principal pour l'orchestrateur."""
        result = self.fetch_tariffs()
        filepath = self.save_results(result)

        return {
            "status": "ok" if result.success else "error",
            "filepath": str(filepath),
            "tariffs_count": len(result.tariffs),
            "errors": result.errors,
        }


def main():
    """Point d'entree CLI."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="ONEE Tariffs Scraper")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("nifi_exchange/input/external/onee_tarifs"),
        help="Output directory",
    )
    args = parser.parse_args()

    scraper = ONEETarifsScraper(output_dir=args.output)
    result = scraper.run()

    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    exit(main())
