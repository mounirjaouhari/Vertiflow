#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de creation    : 04/01/2026
Equipe              : VertiFlow Core Team

--------------------------------------------------------------------------------
MODULE: fetch_open_meteo.py
DESCRIPTION: Script d'integration Open-Meteo API pour enrichissement meteo

Fonctionnalites principales:
    - Recuperation donnees meteo temps reel (GRATUIT, sans cle API)
    - Donnees horaires et journalieres
    - Evapotranspiration FAO (ET0) pour calcul besoins eau
    - Export JSON pour ingestion NiFi
    - Support historique et previsions

Colonnes ClickHouse alimentees:
    - ext_temp_nasa (remplacement/complement)
    - ext_humidity_nasa
    - ext_solar_radiation
    - ext_uv_index
    - ext_wind_speed
    - ext_evapotranspiration

API: https://open-meteo.com/en/docs
Avantages: GRATUIT, pas de cle API, pas de limite stricte

Developpe par        : @Mouhammed
Ticket(s) associe(s): TICKET-057
Sprint              : Semaine 6 - Integration APIs

================================================================================
2025-2026 VertiFlow Core Team
================================================================================
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Gestion des imports avec fallback
try:
    import requests
except ImportError:
    print("ERROR: requests non installe. Executez: pip install requests")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Chemin racine du projet (robuste quel que soit le cwd)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Localisation: Casablanca, Maroc (VertiFlow Farm)
LOCATION = {
    "latitude": 33.5731,
    "longitude": -7.5898,
    "timezone": "Africa/Casablanca",
    "name": "Casablanca_Morocco"
}

# Dossier de sortie pour NiFi (chemin robuste)
OUTPUT_DIR = str(PROJECT_ROOT / "nifi_exchange" / "input" / "external" / "weather_api")

# URLs Open-Meteo
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# Parametres horaires demandes
HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "uv_index",
    "is_day",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
    "soil_temperature_0cm",
    "soil_moisture_0_to_1cm"
]

# Parametres journaliers demandes
DAILY_PARAMS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "sunrise",
    "sunset",
    "daylight_duration",
    "uv_index_max",
    "precipitation_sum",
    "rain_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "et0_fao_evapotranspiration",
    "shortwave_radiation_sum"
]


# ============================================================================
# FONCTIONS API
# ============================================================================

def fetch_forecast_data(days: int = 7) -> Optional[Dict[str, Any]]:
    """
    Recupere les donnees de prevision meteo.

    Args:
        days: Nombre de jours de prevision (1-16)

    Returns:
        Donnees JSON ou None si erreur
    """
    params = {
        "latitude": LOCATION["latitude"],
        "longitude": LOCATION["longitude"],
        "timezone": LOCATION["timezone"],
        "hourly": ",".join(HOURLY_PARAMS),
        "daily": ",".join(DAILY_PARAMS),
        "forecast_days": min(days, 16)
    }

    try:
        print(f"Fetching forecast data from Open-Meteo...")
        response = requests.get(FORECAST_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        print(f"  OK - Received {len(data.get('hourly', {}).get('time', []))} hourly records")
        return data

    except requests.exceptions.RequestException as e:
        print(f"  ERROR fetching forecast: {e}")
        return None


def fetch_historical_data(start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """
    Recupere les donnees meteo historiques.

    Args:
        start_date: Date debut (YYYY-MM-DD)
        end_date: Date fin (YYYY-MM-DD)

    Returns:
        Donnees JSON ou None si erreur
    """
    params = {
        "latitude": LOCATION["latitude"],
        "longitude": LOCATION["longitude"],
        "timezone": LOCATION["timezone"],
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(HOURLY_PARAMS[:10]),  # Limite pour historique
        "daily": ",".join(DAILY_PARAMS)
    }

    try:
        print(f"Fetching historical data {start_date} to {end_date}...")
        response = requests.get(HISTORICAL_URL, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        print(f"  OK - Received {len(data.get('daily', {}).get('time', []))} daily records")
        return data

    except requests.exceptions.RequestException as e:
        print(f"  ERROR fetching historical: {e}")
        return None


def transform_to_vertiflow_schema(raw_data: Dict[str, Any], data_type: str = "forecast") -> List[Dict[str, Any]]:
    """
    Transforme les donnees Open-Meteo vers le schema VertiFlow.

    Args:
        raw_data: Donnees brutes de l'API
        data_type: "forecast" ou "historical"

    Returns:
        Liste de records au format VertiFlow
    """
    records = []

    if not raw_data:
        return records

    # Extraction donnees horaires
    hourly = raw_data.get("hourly", {})
    times = hourly.get("time", [])

    for i, timestamp in enumerate(times):
        record = {
            # Identification
            "timestamp": f"{timestamp}:00Z" if "T" in timestamp else timestamp,
            "farm_id": "VERT-MAROC-01",
            "data_source_type": "API",
            "api_source": "OPEN_METEO",
            "data_type": data_type,

            # Meteo externe -> colonnes ClickHouse
            "ext_temp_openmeteo": hourly.get("temperature_2m", [None])[i] if i < len(hourly.get("temperature_2m", [])) else None,
            "ext_humidity_openmeteo": hourly.get("relative_humidity_2m", [None])[i] if i < len(hourly.get("relative_humidity_2m", [])) else None,
            "ext_dew_point": hourly.get("dew_point_2m", [None])[i] if i < len(hourly.get("dew_point_2m", [])) else None,
            "ext_apparent_temp": hourly.get("apparent_temperature", [None])[i] if i < len(hourly.get("apparent_temperature", [])) else None,
            "ext_precipitation": hourly.get("precipitation", [None])[i] if i < len(hourly.get("precipitation", [])) else None,
            "ext_pressure": hourly.get("surface_pressure", [None])[i] if i < len(hourly.get("surface_pressure", [])) else None,
            "ext_cloud_cover": hourly.get("cloud_cover", [None])[i] if i < len(hourly.get("cloud_cover", [])) else None,
            "ext_wind_speed": hourly.get("wind_speed_10m", [None])[i] if i < len(hourly.get("wind_speed_10m", [])) else None,
            "ext_wind_direction": hourly.get("wind_direction_10m", [None])[i] if i < len(hourly.get("wind_direction_10m", [])) else None,
            "ext_uv_index": hourly.get("uv_index", [None])[i] if i < len(hourly.get("uv_index", [])) else None,
            "ext_is_day": hourly.get("is_day", [None])[i] if i < len(hourly.get("is_day", [])) else None,

            # Radiation solaire
            "ext_solar_radiation": hourly.get("shortwave_radiation", [None])[i] if i < len(hourly.get("shortwave_radiation", [])) else None,
            "ext_direct_radiation": hourly.get("direct_radiation", [None])[i] if i < len(hourly.get("direct_radiation", [])) else None,
            "ext_diffuse_radiation": hourly.get("diffuse_radiation", [None])[i] if i < len(hourly.get("diffuse_radiation", [])) else None,

            # Sol (si disponible)
            "ext_soil_temp": hourly.get("soil_temperature_0cm", [None])[i] if i < len(hourly.get("soil_temperature_0cm", [])) else None,
            "ext_soil_moisture": hourly.get("soil_moisture_0_to_1cm", [None])[i] if i < len(hourly.get("soil_moisture_0_to_1cm", [])) else None,

            # Metadonnees
            "location_latitude": LOCATION["latitude"],
            "location_longitude": LOCATION["longitude"],
            "location_name": LOCATION["name"],
            "data_integrity_flag": 0,
            "lineage_uuid": f"openmeteo-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}"
        }

        # Filtrer les None
        record = {k: v for k, v in record.items() if v is not None}
        records.append(record)

    return records


def transform_daily_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transforme les donnees journalieres Open-Meteo.
    """
    records = []

    if not raw_data:
        return records

    daily = raw_data.get("daily", {})
    times = daily.get("time", [])

    for i, date in enumerate(times):
        record = {
            "date": date,
            "farm_id": "VERT-MAROC-01",
            "data_source_type": "API",
            "api_source": "OPEN_METEO_DAILY",

            # Temperatures
            "daily_temp_max": daily.get("temperature_2m_max", [None])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
            "daily_temp_min": daily.get("temperature_2m_min", [None])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
            "daily_temp_mean": daily.get("temperature_2m_mean", [None])[i] if i < len(daily.get("temperature_2m_mean", [])) else None,

            # Soleil
            "sunrise": daily.get("sunrise", [None])[i] if i < len(daily.get("sunrise", [])) else None,
            "sunset": daily.get("sunset", [None])[i] if i < len(daily.get("sunset", [])) else None,
            "daylight_duration_s": daily.get("daylight_duration", [None])[i] if i < len(daily.get("daylight_duration", [])) else None,

            # UV et radiation
            "daily_uv_max": daily.get("uv_index_max", [None])[i] if i < len(daily.get("uv_index_max", [])) else None,
            "daily_radiation_sum": daily.get("shortwave_radiation_sum", [None])[i] if i < len(daily.get("shortwave_radiation_sum", [])) else None,

            # Precipitation
            "daily_precipitation": daily.get("precipitation_sum", [None])[i] if i < len(daily.get("precipitation_sum", [])) else None,
            "daily_rain": daily.get("rain_sum", [None])[i] if i < len(daily.get("rain_sum", [])) else None,
            "precipitation_hours": daily.get("precipitation_hours", [None])[i] if i < len(daily.get("precipitation_hours", [])) else None,

            # Vent
            "daily_wind_max": daily.get("wind_speed_10m_max", [None])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,

            # IMPORTANT: Evapotranspiration FAO (ET0)
            # Utilise pour calculer les besoins en eau des cultures
            "ext_evapotranspiration": daily.get("et0_fao_evapotranspiration", [None])[i] if i < len(daily.get("et0_fao_evapotranspiration", [])) else None,

            "data_integrity_flag": 0
        }

        record = {k: v for k, v in record.items() if v is not None}
        records.append(record)

    return records


def save_to_nifi(records: List[Dict[str, Any]], filename_prefix: str) -> str:
    """
    Sauvegarde les donnees dans un fichier JSON pour NiFi.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"  Saved {len(records)} records to {filepath}")
    return filepath


def main():
    """Point d'entree principal."""
    print("=" * 70)
    print("VERTIFLOW - Integration Open-Meteo API")
    print("=" * 70)
    print(f"Location: {LOCATION['name']} ({LOCATION['latitude']}, {LOCATION['longitude']})")
    print(f"Output directory: {OUTPUT_DIR}")
    print("-" * 70)

    # 1. Recuperer les previsions (7 jours)
    print("\n[1/3] Fetching forecast data...")
    forecast_data = fetch_forecast_data(days=7)

    if forecast_data:
        # Transformer donnees horaires
        hourly_records = transform_to_vertiflow_schema(forecast_data, "forecast")
        if hourly_records:
            save_to_nifi(hourly_records, "open_meteo_hourly")

        # Transformer donnees journalieres
        daily_records = transform_daily_data(forecast_data)
        if daily_records:
            save_to_nifi(daily_records, "open_meteo_daily")

    # 2. Recuperer donnees historiques (30 derniers jours)
    print("\n[2/3] Fetching historical data (last 30 days)...")
    from datetime import timedelta
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    historical_data = fetch_historical_data(start_date, end_date)

    if historical_data:
        historical_records = transform_daily_data(historical_data)
        if historical_records:
            save_to_nifi(historical_records, "open_meteo_historical")

    # 3. Resume
    print("\n[3/3] Summary")
    print("-" * 70)
    print(f"  Hourly records: {len(hourly_records) if forecast_data else 0}")
    print(f"  Daily records: {len(daily_records) if forecast_data else 0}")
    print(f"  Historical records: {len(historical_records) if historical_data else 0}")
    print("\nFiles ready for NiFi ingestion in:", OUTPUT_DIR)
    print("=" * 70)


def run_continuous(interval_minutes: int = 60):
    """
    Mode continu pour integration NiFi.

    Args:
        interval_minutes: Intervalle entre les recuperations
    """
    print(f"Starting continuous mode (interval: {interval_minutes} min)")
    print("Press Ctrl+C to stop")

    while True:
        try:
            main()
            print(f"\nNext fetch in {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            print(f"Retrying in 5 minutes...")
            time.sleep(300)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VertiFlow Open-Meteo Integration")
    parser.add_argument("--continuous", "-c", action="store_true",
                       help="Run continuously")
    parser.add_argument("--interval", "-i", type=int, default=60,
                       help="Interval in minutes for continuous mode (default: 60)")

    args = parser.parse_args()

    if args.continuous:
        run_continuous(args.interval)
    else:
        main()
