#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
============================================================================
FICHIER: fao_fpma_handler.py
DESCRIPTION: Handler pour FAO FPMA (Food Price Monitoring and Analysis)
             Systeme de suivi des prix alimentaires mondiaux

Developpe par       : @Mouhammed
Ticket(s) associe(s): TICKET-131
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

LOGGER = logging.getLogger("vertiflow.handlers.fao_fpma")


@dataclass
class FAOFPMAResult:
    """Resultat de la recuperation des donnees FAO FPMA."""

    success: bool
    timestamp: str
    source: str = "FAO_FPMA"
    provider: str = "FAO Food Price Monitoring"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class FAOFPMAHandler:
    """
    Handler pour le systeme FPMA de la FAO.

    Le FPMA (Food Price Monitoring and Analysis) suit les prix
    alimentaires sur les marches mondiaux.

    Sources de donnees:
        - GIEWS (Global Information and Early Warning System)
        - Marches nationaux et regionaux

    Documentation:
        https://fpma.fao.org/giews/fpmat4
    """

    BASE_URL = "https://fpma.fao.org/giews/fpmat4"
    DATA_URL = "https://fpma.fao.org/giews/fpmat4/download"

    # Marches d'interet pour VertiFlow
    MARKETS = {
        "morocco": {
            "casablanca": {"market_id": "MA_CAS", "currency": "MAD"},
            "rabat": {"market_id": "MA_RAB", "currency": "MAD"},
            "marrakech": {"market_id": "MA_MAR", "currency": "MAD"},
        },
        "france": {
            "rungis": {"market_id": "FR_RUN", "currency": "EUR"},
            "paris": {"market_id": "FR_PAR", "currency": "EUR"},
        },
        "spain": {
            "madrid": {"market_id": "ES_MAD", "currency": "EUR"},
            "barcelona": {"market_id": "ES_BAR", "currency": "EUR"},
        },
    }

    # Produits d'interet (herbes aromatiques et legumes feuilles)
    PRODUCTS = {
        "basil": {"fao_code": "BASIL", "category": "herbs"},
        "lettuce": {"fao_code": "LETTUC", "category": "vegetables"},
        "spinach": {"fao_code": "SPINAC", "category": "vegetables"},
        "mint": {"fao_code": "MINT", "category": "herbs"},
        "parsley": {"fao_code": "PARSLE", "category": "herbs"},
    }

    # Prix de reference (EUR/kg) - utilises comme fallback
    REFERENCE_PRICES = {
        "basil": {
            "morocco": {"min": 0.8, "max": 1.5, "avg": 1.1, "unit": "EUR/kg"},
            "france": {"min": 8.0, "max": 15.0, "avg": 11.5, "unit": "EUR/kg"},
            "spain": {"min": 6.0, "max": 12.0, "avg": 9.0, "unit": "EUR/kg"},
        },
        "lettuce": {
            "morocco": {"min": 0.3, "max": 0.6, "avg": 0.45, "unit": "EUR/kg"},
            "france": {"min": 1.5, "max": 3.0, "avg": 2.25, "unit": "EUR/kg"},
            "spain": {"min": 1.2, "max": 2.5, "avg": 1.85, "unit": "EUR/kg"},
        },
        "spinach": {
            "morocco": {"min": 0.4, "max": 0.8, "avg": 0.6, "unit": "EUR/kg"},
            "france": {"min": 3.0, "max": 6.0, "avg": 4.5, "unit": "EUR/kg"},
            "spain": {"min": 2.5, "max": 5.0, "avg": 3.75, "unit": "EUR/kg"},
        },
        "mint": {
            "morocco": {"min": 0.5, "max": 1.0, "avg": 0.75, "unit": "EUR/kg"},
            "france": {"min": 6.0, "max": 12.0, "avg": 9.0, "unit": "EUR/kg"},
            "spain": {"min": 5.0, "max": 10.0, "avg": 7.5, "unit": "EUR/kg"},
        },
        "parsley": {
            "morocco": {"min": 0.3, "max": 0.6, "avg": 0.45, "unit": "EUR/kg"},
            "france": {"min": 4.0, "max": 8.0, "avg": 6.0, "unit": "EUR/kg"},
            "spain": {"min": 3.5, "max": 7.0, "avg": 5.25, "unit": "EUR/kg"},
        },
    }

    # Taux de conversion (approximatifs)
    EXCHANGE_RATES = {
        "MAD_EUR": 0.092,  # 1 MAD = 0.092 EUR
        "USD_EUR": 0.92,   # 1 USD = 0.92 EUR
    }

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        timeout: int = 30,
    ):
        self.output_dir = output_dir or Path("nifi_exchange/input/external/fao_fpma")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json, text/csv",
            "User-Agent": "VertiFlow-DataPlatform/1.0",
        })

        LOGGER.info("FAO FPMA Handler initialized")

    def fetch_market_prices(
        self,
        country: str = "morocco",
        products: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Recupere les prix du marche pour un pays.

        Args:
            country: Pays (morocco, france, spain)
            products: Liste des produits

        Returns:
            Prix du marche
        """
        products = products or list(self.PRODUCTS.keys())
        markets = self.MARKETS.get(country, {})

        try:
            # Tentative d'appel API FAO
            url = f"{self.DATA_URL}/prices"
            params = {
                "country": country.upper()[:2],
                "format": "json",
            }

            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            LOGGER.warning("FAO API request failed: %s - Using reference data", e)
            return self._get_reference_prices(country, products)

    def _get_reference_prices(
        self,
        country: str,
        products: List[str],
    ) -> Dict[str, Any]:
        """Retourne les prix de reference quand l'API n'est pas disponible."""
        prices = []
        current_date = datetime.utcnow().strftime("%Y-%m-%d")

        for product in products:
            product_prices = self.REFERENCE_PRICES.get(product, {})
            country_prices = product_prices.get(country)

            if country_prices:
                prices.append({
                    "product": product,
                    "country": country,
                    "price_min": country_prices["min"],
                    "price_max": country_prices["max"],
                    "price_avg": country_prices["avg"],
                    "unit": country_prices["unit"],
                    "currency": "EUR",
                    "date": current_date,
                    "source": "FAO_REFERENCE",
                    "note": "Prix de reference - API FAO non disponible",
                })

        return {
            "country": country,
            "date": current_date,
            "prices": prices,
            "source_type": "reference",
        }

    def fetch_all_markets(self) -> FAOFPMAResult:
        """
        Recupere les prix pour tous les marches d'interet.

        Returns:
            FAOFPMAResult avec prix multi-marches
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        result = FAOFPMAResult(
            success=False,
            timestamp=timestamp,
        )

        all_data = {}
        products = list(self.PRODUCTS.keys())

        for country in self.MARKETS.keys():
            try:
                market_data = self.fetch_market_prices(country, products)
                all_data[country] = market_data
                LOGGER.info("Fetched prices for %s", country)

            except Exception as e:
                error_msg = f"Error fetching {country}: {str(e)}"
                LOGGER.warning(error_msg)
                result.errors.append(error_msg)

        # Analyse et comparaison
        analysis = self._analyze_prices(all_data)

        result.data = {
            "markets": all_data,
            "analysis": analysis,
            "exchange_rates": self.EXCHANGE_RATES,
        }

        result.success = len(all_data) > 0
        result.metadata = {
            "countries": list(all_data.keys()),
            "products": products,
            "data_source": "FAO FPMA / Reference",
        }

        return result

    def _analyze_prices(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse comparative des prix entre marches."""
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "price_comparison": {},
            "arbitrage_opportunities": [],
            "market_recommendations": [],
        }

        # Comparaison par produit
        product_prices = {}

        for country, data in all_data.items():
            prices = data.get("prices", [])
            for price_entry in prices:
                product = price_entry.get("product")
                avg_price = price_entry.get("price_avg")

                if product and avg_price:
                    if product not in product_prices:
                        product_prices[product] = {}
                    product_prices[product][country] = avg_price

        # Calcul des ecarts de prix
        for product, country_prices in product_prices.items():
            if len(country_prices) >= 2:
                min_country = min(country_prices, key=country_prices.get)
                max_country = max(country_prices, key=country_prices.get)

                min_price = country_prices[min_country]
                max_price = country_prices[max_country]

                spread = max_price - min_price
                spread_pct = (spread / min_price) * 100 if min_price > 0 else 0

                analysis["price_comparison"][product] = {
                    "prices_by_country": country_prices,
                    "lowest": {"country": min_country, "price": min_price},
                    "highest": {"country": max_country, "price": max_price},
                    "spread_eur": round(spread, 2),
                    "spread_pct": round(spread_pct, 1),
                }

                # Detection opportunites d'arbitrage
                if spread_pct > 50:
                    analysis["arbitrage_opportunities"].append({
                        "product": product,
                        "buy_market": min_country,
                        "sell_market": max_country,
                        "potential_margin_pct": round(spread_pct, 1),
                        "note": "Ecart de prix significatif",
                    })

        # Recommandations
        analysis["market_recommendations"] = self._generate_market_recommendations(analysis)

        return analysis

    def _generate_market_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Genere des recommandations basees sur l'analyse des prix."""
        recommendations = []

        # Analyse des opportunites
        opportunities = analysis.get("arbitrage_opportunities", [])

        if opportunities:
            recommendations.append(
                f"Opportunites detectees sur {len(opportunities)} produit(s) avec marges > 50%"
            )

        # Comparaison Morocco vs Europe
        comparisons = analysis.get("price_comparison", {})

        for product, data in comparisons.items():
            morocco_price = data.get("prices_by_country", {}).get("morocco")
            france_price = data.get("prices_by_country", {}).get("france")

            if morocco_price and france_price:
                ratio = france_price / morocco_price
                if ratio > 5:
                    recommendations.append(
                        f"{product.capitalize()}: Prix France {ratio:.1f}x plus eleve que Maroc - "
                        f"Export potentiel interessant"
                    )

        if not recommendations:
            recommendations.append("Marches stables - Pas d'opportunites majeures detectees")

        return recommendations

    def get_vertiflow_pricing_strategy(self) -> Dict[str, Any]:
        """
        Genere une strategie de pricing pour VertiFlow basee sur les donnees marche.
        """
        result = self.fetch_all_markets()

        strategy = {
            "timestamp": datetime.utcnow().isoformat(),
            "target_market": "morocco_local",
            "export_potential": [],
            "pricing_recommendations": {},
        }

        # Analyse des marges potentielles
        for product in self.PRODUCTS.keys():
            morocco_ref = self.REFERENCE_PRICES.get(product, {}).get("morocco", {})
            france_ref = self.REFERENCE_PRICES.get(product, {}).get("france", {})

            if morocco_ref and france_ref:
                # Prix de production estime (agriculture verticale)
                # Hypothese: cout de production = 80% du prix local moyen
                production_cost = morocco_ref.get("avg", 0) * 0.8

                local_margin = morocco_ref.get("avg", 0) - production_cost
                export_margin = france_ref.get("avg", 0) - production_cost - 2.0  # -2 EUR transport

                strategy["pricing_recommendations"][product] = {
                    "estimated_production_cost_eur_kg": round(production_cost, 2),
                    "local_price_avg": morocco_ref.get("avg"),
                    "local_margin_eur_kg": round(local_margin, 2),
                    "export_price_avg": france_ref.get("avg"),
                    "export_margin_eur_kg": round(export_margin, 2),
                    "recommended_strategy": "export" if export_margin > local_margin * 2 else "local",
                }

                if export_margin > local_margin * 2:
                    strategy["export_potential"].append({
                        "product": product,
                        "target_market": "france",
                        "margin_multiplier": round(export_margin / local_margin, 1) if local_margin > 0 else 0,
                    })

        return strategy

    def save_results(self, result: FAOFPMAResult) -> Path:
        """Sauvegarde les resultats au format JSON pour NiFi."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"fao_fpma_{timestamp}.json"
        filepath = self.output_dir / filename

        output_data = {
            "source": result.source,
            "provider": result.provider,
            "timestamp": result.timestamp,
            "success": result.success,
            "data": result.data,
            "pricing_strategy": self.get_vertiflow_pricing_strategy(),
            "metadata": result.metadata,
            "errors": result.errors,
            "target_columns": ["market_price_kg", "price_volatility_index"],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        LOGGER.info("Saved FAO FPMA data to %s", filepath)
        return filepath

    def run(self) -> Dict[str, Any]:
        """Point d'entree principal pour l'orchestrateur."""
        result = self.fetch_all_markets()
        filepath = self.save_results(result)

        return {
            "status": "ok" if result.success else "partial",
            "filepath": str(filepath),
            "markets_count": len(result.data.get("markets", {})),
            "errors": result.errors,
        }


def main():
    """Point d'entree CLI."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="FAO FPMA Price Handler")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("nifi_exchange/input/external/fao_fpma"),
        help="Output directory",
    )
    parser.add_argument(
        "--country",
        type=str,
        default="morocco",
        help="Country to fetch (morocco, france, spain)",
    )
    args = parser.parse_args()

    handler = FAOFPMAHandler(output_dir=args.output)
    output = handler.run()

    print(json.dumps(output, indent=2))
    return 0 if output["status"] == "ok" else 1


if __name__ == "__main__":
    exit(main())
