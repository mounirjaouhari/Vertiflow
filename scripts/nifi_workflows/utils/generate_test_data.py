#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de creation    : 04/01/2026
Equipe              : VertiFlow Core Team

--------------------------------------------------------------------------------
MODULE: generate_nifi_test_data.py
DESCRIPTION: Generateur de donnees de test completes pour NiFi

Fonctionnalites principales:
    - Genere des fichiers JSON conformes au schema telemetry_v3
    - Couvre les 153 colonnes du Golden Record
    - Simule differents scenarios (normal, anomalie, maintenance)
    - Place les fichiers dans les dossiers surveilles par NiFi

Dossiers de sortie:
    - data_ingestion/iot_telemetry/      : Donnees capteurs IoT
    - data_ingestion/led_spectrum/       : Donnees spectrales LED
    - data_ingestion/nutrient_data/      : Donnees nutrition
    - data_ingestion/weather_api/        : Donnees meteo externes
    - data_ingestion/lab_input/          : Donnees laboratoire

Developpe par        : @Mouhammed
Ticket(s) associe(s): TICKET-060
Sprint              : Semaine 6 - Tests Integration

================================================================================
2025-2026 VertiFlow Core Team
================================================================================
"""

import json
import os
import random
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_INGESTION_DIR = os.path.join(BASE_DIR, "data_ingestion")

OUTPUT_DIRS = {
    "iot_telemetry": os.path.join(DATA_INGESTION_DIR, "iot_telemetry"),
    "led_spectrum": os.path.join(DATA_INGESTION_DIR, "led_spectrum"),
    "nutrient_data": os.path.join(DATA_INGESTION_DIR, "nutrient_data"),
    "weather_api": os.path.join(DATA_INGESTION_DIR, "weather_api"),
    "lab_input": os.path.join(DATA_INGESTION_DIR, "lab_input")
}

FARM_CONFIG = {
    "farm_id": "VERT-MAROC-01",
    "parcel_id": "830-AB-123",
    "latitude": 33.5731,
    "longitude": -7.5898,
    "racks": ["R01", "R02", "R03", "R04", "R05"],
    "zones": {
        "R01": "ZONE_GERMINATION",
        "R02": "ZONE_GERMINATION",
        "R03": "ZONE_CROISSANCE",
        "R04": "ZONE_CROISSANCE",
        "R05": "ZONE_FLORAISON"
    },
    "levels_per_rack": 4,
    "modules_per_level": 2
}


# ============================================================================
# FONCTIONS DE GENERATION
# ============================================================================

def generate_uuid() -> str:
    """Genere un UUID v4."""
    return str(uuid.uuid4())


def generate_blockchain_hash(data: Dict) -> str:
    """Genere un hash SHA-256 pour audit."""
    content = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def generate_iot_telemetry(rack_id: str, level: int, module: int,
                           scenario: str = "normal") -> Dict[str, Any]:
    """
    Genere un enregistrement de telemetrie IoT complet.

    Args:
        rack_id: ID du rack
        level: Niveau dans le rack
        module: ID du module
        scenario: "normal", "anomaly", "maintenance"
    """
    now = datetime.now(timezone.utc)
    hour = now.hour
    is_day = 6 <= hour < 22

    zone = FARM_CONFIG["zones"].get(rack_id, "ZONE_CROISSANCE")

    # Parametres selon le scenario
    if scenario == "anomaly":
        temp_offset = random.choice([-8, 10])  # Temperature anormale
        anomaly_score = random.uniform(0.7, 0.95)
        data_flag = 1
    elif scenario == "maintenance":
        temp_offset = 0
        anomaly_score = 0.1
        data_flag = 1
    else:
        temp_offset = 0
        anomaly_score = random.uniform(0, 0.1)
        data_flag = 0

    # Temperature de base selon la zone
    base_temp = {
        "ZONE_GERMINATION": 22,
        "ZONE_CROISSANCE": 24,
        "ZONE_FLORAISON": 22
    }.get(zone, 24)

    # Generation des donnees
    air_temp = round(random.gauss(base_temp + temp_offset, 0.5) + (2 if is_day else -2), 2)
    humidity = round(random.gauss(62, 3), 1)

    # Calcul VPD
    es = 0.6108 * (2.71828 ** ((17.27 * air_temp) / (air_temp + 237.3)))
    ea = es * (humidity / 100)
    vpd = round(es - ea, 3)

    # PPFD selon jour/nuit et zone
    ppfd_targets = {
        "ZONE_GERMINATION": 150,
        "ZONE_CROISSANCE": 380,
        "ZONE_FLORAISON": 450
    }
    ppfd_base = ppfd_targets.get(zone, 300)
    ppfd = round(random.gauss(ppfd_base, 20), 1) if is_day else round(random.uniform(0, 2), 1)

    # DLI accumule (simule progression journaliere)
    hours_elapsed = hour - 6 if is_day else 0
    dli = round((ppfd * hours_elapsed * 3600) / 1_000_000, 2) if is_day else 0

    telemetry = {
        # I. IDENTIFICATION
        "timestamp": now.isoformat(),
        "farm_id": FARM_CONFIG["farm_id"],
        "parcel_id": FARM_CONFIG["parcel_id"],
        "latitude": FARM_CONFIG["latitude"],
        "longitude": FARM_CONFIG["longitude"],
        "zone_id": zone,
        "rack_id": rack_id,
        "level_index": level,
        "module_id": f"M{module:02d}",
        "batch_id": f"BATCH-2026-{random.choice(['A', 'B', 'C'])}",
        "species_variety": "Ocimum basilicum Genovese",
        "sensor_hardware_id": f"SN-{rack_id}-L{level}-M{module}",
        "data_source_type": "IoT",

        # VI. ENVIRONNEMENT & CLIMAT
        "air_temp_internal": air_temp,
        "air_humidity": humidity,
        "co2_level_ambient": int(random.gauss(900 if is_day else 500, 30)),
        "vapor_pressure_deficit": vpd,
        "airflow_velocity": round(random.uniform(0.3, 0.8), 2),
        "air_pressure": round(random.gauss(1013, 3), 1),
        "fan_speed_pct": round(random.uniform(40, 70), 1) if is_day else round(random.uniform(20, 40), 1),
        "dew_point": round(air_temp - ((100 - humidity) / 5), 1),
        "hvac_load_pct": round(random.uniform(30, 60), 1),
        "co2_injection_status": 1 if is_day and random.random() > 0.3 else 0,
        "oxygen_level": round(random.gauss(20.9, 0.1), 1),

        # III. PHOTOSYNTHESE & LUMIERE
        "light_intensity_ppfd": ppfd,
        "light_compensation_point": round(random.gauss(25, 3), 1),
        "light_saturation_point": round(random.gauss(800, 50), 1),
        "light_ratio_red_blue": round(random.uniform(2.0, 2.4), 2),
        "light_far_red_intensity": round(ppfd * 0.08, 1) if is_day else 0,
        "light_dli_accumulated": dli,
        "light_photoperiod": 16,
        "quantum_yield_psii": round(random.gauss(0.82, 0.02), 3) if ppfd > 0 else 0,
        "photosynthetic_rate_max": round(random.gauss(15, 2), 1) if is_day else 0,
        "light_use_efficiency": round(random.gauss(0.8, 0.05), 2) if is_day else 0,
        "leaf_absorption_pct": round(random.gauss(85, 2), 1),
        "spectral_recipe_id": f"SPR-{zone.split('_')[1][:3]}-001",

        # II. NUTRITION MINERALE
        "nutrient_n_total": round(random.gauss(155, 5), 1),
        "nutrient_p_phosphorus": round(random.gauss(52, 2), 1),
        "nutrient_k_potassium": round(random.gauss(205, 8), 1),
        "nutrient_ca_calcium": round(random.gauss(118, 4), 1),
        "nutrient_mg_magnesium": round(random.gauss(40, 2), 1),
        "nutrient_s_sulfur": round(random.gauss(52, 2), 1),
        "nutrient_fe_iron": round(random.gauss(3.0, 0.2), 2),
        "nutrient_mn_manganese": round(random.gauss(0.7, 0.05), 2),
        "nutrient_zn_zinc": round(random.gauss(0.4, 0.03), 2),
        "nutrient_cu_copper": round(random.gauss(0.08, 0.01), 3),
        "nutrient_b_boron": round(random.gauss(0.5, 0.03), 2),
        "nutrient_mo_molybdenum": round(random.gauss(0.08, 0.01), 3),
        "nutrient_cl_chlorine": round(random.gauss(8, 1), 1),
        "nutrient_ni_nickel": round(random.gauss(0.02, 0.005), 3),
        "nutrient_solution_ec": round(random.gauss(1.6, 0.08), 2),

        # VII. RHIZOSPHERE & EAU
        "water_temp": round(random.gauss(20, 0.5), 1),
        "water_ph": round(random.gauss(6.0, 0.1), 2),
        "dissolved_oxygen": round(random.gauss(8.5, 0.3), 1),
        "water_turbidity": round(random.uniform(0.5, 2.0), 2),
        "wue_current": round(random.gauss(4.5, 0.3), 2),
        "water_recycled_rate": round(random.gauss(95, 2), 1),
        "coefficient_cultural_kc": round(random.uniform(0.7, 1.0), 2),
        "microbial_density": round(random.gauss(450000, 50000), 0),
        "beneficial_microbes_ratio": round(random.gauss(0.85, 0.03), 3),
        "root_fungal_pressure": round(random.gauss(0.1, 0.02), 3),
        "biofilm_thickness": round(random.gauss(0.5, 0.1), 2),
        "algae_growth_index": round(random.uniform(0.1, 0.3), 2),
        "redox_potential": round(random.gauss(250, 15), 1),
        "irrigation_line_pressure": round(random.gauss(2.5, 0.1), 2),
        "leaching_fraction": round(random.uniform(0.12, 0.18), 2),

        # IV. BIOMASSE & CROISSANCE
        "fresh_biomass_est": round(random.gauss(45, 8), 1),
        "dry_biomass_est": round(random.gauss(4.5, 0.8), 2),
        "leaf_area_index_lai": round(random.gauss(3.2, 0.4), 2),
        "root_shoot_ratio": round(random.gauss(0.15, 0.02), 3),
        "relative_growth_rate": round(random.gauss(0.12, 0.02), 3),
        "net_assimilation_rate": round(random.gauss(8, 1), 1),
        "canopy_height": round(random.gauss(18, 3), 1),
        "harvest_index": round(random.uniform(0.6, 0.75), 2),
        "days_since_planting": random.randint(15, 28),
        "thermal_sum_accumulated": round(random.gauss(450, 50), 1),
        "growth_stage": random.choice(["Vegetatif", "Bouton"]),
        "predicted_yield_kg_m2": round(random.gauss(3.5, 0.4), 2),
        "expected_harvest_date": (now + timedelta(days=random.randint(5, 12))).strftime("%Y-%m-%d"),
        "biomass_accumulation_daily": round(random.gauss(2.5, 0.4), 2),
        "target_harvest_weight": 80,

        # V. PHYSIOLOGIE & SANTE
        "health_score": round(random.gauss(0.88, 0.05), 3),
        "chlorophyll_index_spad": round(random.gauss(42, 3), 1),
        "stomatal_conductance": round(random.gauss(0.25, 0.03), 3),
        "anthocyanin_index": round(random.gauss(0.3, 0.05), 2),
        "tip_burn_risk": round(random.uniform(0.05, 0.15), 3),
        "leaf_temp_delta": round(random.gauss(-1.5, 0.5), 2),
        "essential_oil_yield": round(random.gauss(0.75, 0.1), 2),

        # IX. HARDWARE & MAINTENANCE
        "pump_vibration_level": round(random.uniform(0.1, 0.4), 2),
        "fan_current_draw": round(random.gauss(1.5, 0.1), 2),
        "led_driver_temp": round(random.gauss(48 if is_day else 25, 3), 1),
        "filter_differential_pressure": round(random.uniform(0.1, 0.25), 2),
        "ups_battery_health": round(random.uniform(96, 100), 1),
        "leak_detection_status": 0,
        "emergency_stop_status": 0,
        "network_latency_ms": random.randint(5, 25),
        "sensor_calibration_offset": round(random.gauss(0, 0.1), 3),
        "module_integrity_score": round(random.uniform(0.95, 1.0), 3),

        # VIII. ECONOMIE
        "energy_price_kwh": 1.2 if 7 <= hour < 23 else 0.8,
        "energy_footprint_hourly": round(random.gauss(2.5, 0.3), 2),
        "renewable_energy_pct": round(random.uniform(15, 35), 1),
        "market_price_kg": round(random.gauss(45, 5), 1),
        "carbon_intensity_g_co2_kwh": round(random.gauss(450, 30), 1),
        "daily_rent_cost": round(random.gauss(15, 2), 2),
        "labor_cost_pro_rata": round(random.gauss(8, 1), 2),
        "operational_cost_total": round(random.gauss(25, 3), 2),
        "carbon_footprint_per_kg": round(random.gauss(1.2, 0.2), 2),

        # X. INTELLIGENCE & DECISION
        "ai_decision_mode": "AUTONOMOUS" if random.random() > 0.3 else "ASSISTED",
        "anomaly_confidence_score": anomaly_score,
        "predicted_energy_need_24h": round(random.gauss(55, 5), 1),
        "risk_pest_outbreak": round(random.uniform(0.02, 0.08), 3),
        "quality_grade_prediction": random.choices(["Premium", "Standard", "Rejet"], weights=[70, 25, 5])[0],

        # XI. CIBLES REFERENTIELLES
        "ref_n_target": 160,
        "ref_p_target": 55,
        "ref_k_target": 210,
        "ref_ca_target": 120,
        "ref_mg_target": 42,
        "ref_temp_opt": 24,
        "ref_humidity_opt": 62,

        # XII. TRACABILITE
        "data_integrity_flag": data_flag,
        "lineage_uuid": generate_uuid(),
        "source_reliability_score": round(random.uniform(0.95, 1.0), 3),
        "api_endpoint_version": "v3.0"
    }

    # Ajouter le hash blockchain
    telemetry["blockchain_hash"] = generate_blockchain_hash(telemetry)

    return telemetry


def generate_batch(count: int = 20, scenarios: Dict[str, float] = None) -> List[Dict]:
    """
    Genere un lot de donnees de telemetrie.

    Args:
        count: Nombre d'enregistrements
        scenarios: Distribution des scenarios {"normal": 0.9, "anomaly": 0.08, "maintenance": 0.02}
    """
    if scenarios is None:
        scenarios = {"normal": 0.90, "anomaly": 0.08, "maintenance": 0.02}

    records = []

    for _ in range(count):
        # Selectionner un scenario selon la distribution
        scenario = random.choices(
            list(scenarios.keys()),
            weights=list(scenarios.values())
        )[0]

        # Selectionner rack/level/module aleatoirement
        rack = random.choice(FARM_CONFIG["racks"])
        level = random.randint(1, FARM_CONFIG["levels_per_rack"])
        module = random.randint(1, FARM_CONFIG["modules_per_level"])

        record = generate_iot_telemetry(rack, level, module, scenario)
        records.append(record)

    return records


def save_records(records: List[Dict], output_dir: str, prefix: str = "telemetry") -> List[str]:
    """Sauvegarde les enregistrements en fichiers JSON."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files_created = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, record in enumerate(records):
        filename = f"{prefix}_{timestamp}_{i:04d}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        files_created.append(filepath)

    return files_created


def main():
    """Point d'entree principal."""
    print("=" * 70)
    print("VERTIFLOW - Generateur de Donnees de Test pour NiFi")
    print("=" * 70)
    print(f"Base directory: {BASE_DIR}")
    print("-" * 70)

    # Creer les dossiers si necessaire
    for name, path in OUTPUT_DIRS.items():
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created directory: {path}")

    # Generer les donnees IoT
    print("\n[1/4] Generating IoT telemetry data...")
    iot_records = generate_batch(count=50)
    iot_files = save_records(iot_records, OUTPUT_DIRS["iot_telemetry"], "iot_telemetry")
    print(f"  Created {len(iot_files)} IoT telemetry files")

    # Generer les donnees LED
    print("\n[2/4] Generating LED spectrum data...")
    led_records = generate_batch(count=20)
    for r in led_records:
        r["data_source_type"] = "IoT"
        r["sensor_hardware_id"] = f"LED-{r['rack_id']}-{r['level_index']}"
    led_files = save_records(led_records, OUTPUT_DIRS["led_spectrum"], "led_spectrum")
    print(f"  Created {len(led_files)} LED spectrum files")

    # Generer les donnees nutriments
    print("\n[3/4] Generating nutrient data...")
    nutrient_records = generate_batch(count=15)
    for r in nutrient_records:
        r["data_source_type"] = "IoT"
        r["sensor_hardware_id"] = f"NUT-{r['zone_id'][:8]}"
    nutrient_files = save_records(nutrient_records, OUTPUT_DIRS["nutrient_data"], "nutrient")
    print(f"  Created {len(nutrient_files)} nutrient data files")

    # Generer les donnees meteo (simulation API)
    print("\n[4/4] Generating weather API data...")
    weather_records = []
    for _ in range(5):
        weather = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "farm_id": FARM_CONFIG["farm_id"],
            "data_source_type": "API",
            "api_source": "OPEN_METEO",
            "ext_temp_openmeteo": round(random.gauss(18, 3), 1),
            "ext_humidity_openmeteo": round(random.gauss(65, 8), 1),
            "ext_uv_index": round(random.uniform(3, 8), 1),
            "ext_solar_radiation": round(random.gauss(450, 80), 1),
            "ext_wind_speed": round(random.uniform(5, 20), 1),
            "ext_evapotranspiration": round(random.uniform(3, 6), 2),
            "ext_pressure": round(random.gauss(1015, 5), 1),
            "location_latitude": FARM_CONFIG["latitude"],
            "location_longitude": FARM_CONFIG["longitude"],
            "data_integrity_flag": 0,
            "lineage_uuid": generate_uuid()
        }
        weather_records.append(weather)
    weather_files = save_records(weather_records, OUTPUT_DIRS["weather_api"], "weather_api")
    print(f"  Created {len(weather_files)} weather API files")

    # Resume
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_files = len(iot_files) + len(led_files) + len(nutrient_files) + len(weather_files)
    print(f"Total files generated: {total_files}")
    print(f"\nFiles ready for NiFi ingestion in:")
    for name, path in OUTPUT_DIRS.items():
        file_count = len([f for f in os.listdir(path) if f.endswith('.json')]) if os.path.exists(path) else 0
        print(f"  {name}: {file_count} files")
    print("=" * 70)


if __name__ == "__main__":
    main()
