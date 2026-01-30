#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VertiFlow - Script de Preparation des Datasets
Execute le pipeline complet pour generer les fichiers JSON pour NiFi.
"""

import pandas as pd
import numpy as np
import json
import zipfile
import os
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATASETS_DIR = PROJECT_DIR / 'datasets'
OUTPUT_DIR = PROJECT_DIR / 'nifi_exchange' / 'input'

# Creer le dossier output s'il n'existe pas
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("VERTIFLOW - PREPARATION DES DATASETS")
print("=" * 60)
print(f"Datasets: {DATASETS_DIR}")
print(f"Output:   {OUTPUT_DIR}")
print()


# === FONCTIONS UTILITAIRES ===

def calculate_vpd(temp_c, humidity_pct):
    """Calcul du Vapor Pressure Deficit (VPD)."""
    if pd.isna(temp_c) or pd.isna(humidity_pct):
        return None
    es = 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea = es * (humidity_pct / 100.0)
    vpd = es - ea
    return round(vpd, 4)


def generate_farm_id(container='FS2', prefix='VERT-MIT'):
    return f"{prefix}-{container}"


def generate_rack_id(bay):
    return f"R{int(bay) % 100:02d}"


def placement_to_level(placement):
    mapping = {'bottom': 1, 'mid': 2, 'top': 3}
    return mapping.get(placement, 1)


def parse_openag_datetime(date_int, time_str):
    try:
        date_str = str(int(date_int))
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H:%M:%S")
        return dt.isoformat() + 'Z'
    except:
        return datetime.now().isoformat() + 'Z'


# === 1. TRAITEMENT OPENAG ENVIRONMENTAL (328K lignes) ===

def process_openag_environmental(chunk_size=10000, max_chunks=None):
    """Traite le dataset OpenAg Environmental par chunks."""
    zip_path = DATASETS_DIR / 'openag-basil-viability-experiment-foodserver-2-master.zip'
    csv_path = 'openag-basil-viability-experiment-foodserver-2-master/ENVIRONMENTAL_data_BV_FS2.csv'

    if not zip_path.exists():
        print(f"  SKIP: {zip_path} non trouve")
        return 0

    print(f"[OpenAg Environmental] Traitement de {zip_path.name}...")

    total_records = 0
    file_index = 0

    with zipfile.ZipFile(zip_path, 'r') as zf:
        with zf.open(csv_path) as f:
            for chunk_num, chunk in enumerate(pd.read_csv(f, chunksize=chunk_size)):
                if max_chunks and chunk_num >= max_chunks:
                    break

                records = []

                for _, row in chunk.iterrows():
                    # Filtrer les temperatures aberrantes (>50C = erreur capteur)
                    temp = row['temp_c'] if row['temp_c'] < 50 else None

                    record = {
                        'timestamp': parse_openag_datetime(row['date'], row['time']),
                        'farm_id': generate_farm_id(row['container']),
                        'rack_id': generate_rack_id(row['bay']),
                        'level_index': placement_to_level(row['placement']),
                        'module_id': f"BAY-{row['bay']}-{row['placement'].upper()}",
                        'batch_id': f"REP-{row['rep']}",
                        'species_variety': row['crop'].capitalize(),
                        'air_temp_internal': round(temp, 2) if temp else None,
                        'air_humidity': round(row['relative_humidity_%'], 2),
                        'dew_point': round(row['dewpoint'], 2),
                        'data_source_type': 'IoT',
                        'sensor_hardware_id': f"OPENAG-FS2-{row['bay']}",
                        'data_integrity_flag': 0,
                        'lineage_uuid': str(uuid.uuid4())
                    }

                    if record['air_temp_internal']:
                        record['vapor_pressure_deficit'] = calculate_vpd(
                            record['air_temp_internal'],
                            record['air_humidity']
                        )

                    records.append(record)

                # Ecrire le chunk
                output_file = OUTPUT_DIR / f'openag_environmental_{file_index:04d}.json'
                with open(output_file, 'w') as out:
                    for rec in records:
                        out.write(json.dumps(rec) + '\n')

                total_records += len(records)
                file_index += 1

                print(f"  Chunk {chunk_num}: {total_records:,} records -> {output_file.name}")

    print(f"  TOTAL: {total_records:,} records en {file_index} fichiers")
    return total_records


# === 2. TRAITEMENT BASIL SENSORY (150 lignes) ===

def process_basil_sensory():
    """Traite le dataset Basil Sensory."""
    zip_path = DATASETS_DIR / 'Basil Data.zip'

    if not zip_path.exists():
        print(f"  SKIP: {zip_path} non trouve")
        return 0

    print(f"[Basil Sensory] Traitement de {zip_path.name}...")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        with zf.open('Basil_sensory_R.csv') as f:
            df = pd.read_csv(f)

    records = []
    base_date = datetime(2025, 6, 1)

    aroma_cols = ['Anise_Aroma', 'Clove_Aroma', 'Black_Pepper_Aroma',
                  'Sweet_Aroma', 'Green_Aroma', 'Mint_Aroma',
                  'Floral_Aroma', 'Lemon_Aroma']

    for idx, row in df.iterrows():
        aroma_score = row[aroma_cols].mean() / 100

        record = {
            'timestamp': (base_date + timedelta(hours=idx)).isoformat() + 'Z',
            'farm_id': 'VERT-LAB-SENSORY',
            'module_id': f"SAMPLE-{row['Sample_Name']}-{idx}",
            'batch_id': row['Sample_Name'],
            'species_variety': 'Genovese',
            'aroma_compounds_ratio': round(aroma_score, 4),
            'essential_oil_yield': round(row[aroma_cols].max() / 100 * 0.8, 4),
            'health_score': round(row['Leaf_Thickness'] / 100, 4),
            'data_source_type': 'Lab',
            'sensor_hardware_id': 'SENSORY-PANEL',
            'data_integrity_flag': 0,
            'lineage_uuid': str(uuid.uuid4())
        }
        records.append(record)

    output_file = OUTPUT_DIR / 'basil_sensory_data.json'
    with open(output_file, 'w') as out:
        for rec in records:
            out.write(json.dumps(rec) + '\n')

    print(f"  Output: {output_file.name} ({len(records)} records)")
    return len(records)


# === 3. TRAITEMENT CHILLING INJURY ===

def process_chilling_injury():
    """Genere des donnees de stress thermique basees sur le protocole Wageningen."""
    print("[Chilling Injury] Generation des donnees de stress thermique...")

    records = []
    base_date = datetime(2025, 1, 15)

    temperatures = [4, 12]
    storage_days = [0, 3, 6, 9, 12]
    replicates = 3

    for temp in temperatures:
        for day in storage_days:
            for rep in range(1, replicates + 1):
                degradation_factor = day / 12
                temp_stress = 1.0 if temp == 12 else 0.7

                fv_fm_base = 0.83
                fv_fm = fv_fm_base * temp_stress * (1 - degradation_factor * 0.3)
                health = fv_fm / fv_fm_base

                record = {
                    'timestamp': (base_date + timedelta(days=day, hours=rep)).isoformat() + 'Z',
                    'farm_id': 'VERT-WAG-CHILL',
                    'module_id': f"CHILL-T{temp}-D{day}-R{rep}",
                    'batch_id': f"STORAGE-{temp}C",
                    'species_variety': 'Dolly',
                    'air_temp_internal': float(temp),
                    'air_humidity': 90.0,
                    'quantum_yield_psii': round(fv_fm, 4),
                    'health_score': round(health, 4),
                    'tip_burn_risk': round(degradation_factor * (1 - temp_stress), 4),
                    'days_since_planting': 20 + day,
                    'data_source_type': 'Lab',
                    'sensor_hardware_id': 'WAG-FLUOROMETER',
                    'data_integrity_flag': 0,
                    'lineage_uuid': str(uuid.uuid4())
                }
                records.append(record)

    output_file = OUTPUT_DIR / 'basil_chilling_injury.json'
    with open(output_file, 'w') as out:
        for rec in records:
            out.write(json.dumps(rec) + '\n')

    print(f"  Output: {output_file.name} ({len(records)} records)")
    return len(records)


# === 4. TRAITEMENT MARTIN WUE ===

def process_martin_wue():
    """Traite le dataset Martin et al. (WUE, photosynthese)."""
    zip_path = DATASETS_DIR / 'basil_research' / '7072502.zip'

    if not zip_path.exists():
        print(f"  SKIP: {zip_path} non trouve")
        return 0

    print(f"[Martin WUE] Traitement de {zip_path.name}...")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        with zf.open('Martin_et_al._Dryad_submission.csv') as f:
            df = pd.read_csv(f)

    records = []
    base_date = datetime(2025, 3, 1)

    for idx, row in df.iterrows():
        record = {
            'timestamp': (base_date + timedelta(hours=idx)).isoformat() + 'Z',
            'farm_id': 'VERT-LAB-MARTIN',
            'module_id': f"MARTIN-{row['sample']}",
            'batch_id': row['treatment'],
            'species_variety': 'Genovese',
            'fresh_biomass_est': round(row['amass'] * 1000, 2),
            'dry_biomass_est': round(row['rmass'] * 1000, 2),
            'leaf_area_index_lai': round(row['area'] / 10, 3),
            'wue_current': round(row['wue'], 4),
            'nutrient_n_total': round(row['leafn'] * 100, 2),
            'light_compensation_point': round(row['llcp'], 2),
            'chlorophyll_index_spad': round(row['leafc'] * 1.2, 2),
            'data_source_type': 'Lab',
            'sensor_hardware_id': 'LICOR-6400',
            'data_integrity_flag': 0,
            'lineage_uuid': str(uuid.uuid4())
        }
        records.append(record)

    output_file = OUTPUT_DIR / 'basil_martin_wue.json'
    with open(output_file, 'w') as out:
        for rec in records:
            out.write(json.dumps(rec) + '\n')

    print(f"  Output: {output_file.name} ({len(records)} records)")
    return len(records)


# === 5. GENERATION RECETTES MONGODB ===

def generate_plant_recipes():
    """Genere les recettes agronomiques pour MongoDB."""
    print("[Plant Recipes] Generation des recettes...")

    recipes = [
        {
            "recipe_id": "BASIL-GERM-001",
            "crop_type": "basil",
            "variety": "Genovese",
            "growth_stage": "germination",
            "environment": {
                "temperature_c": {"min": 20, "max": 25, "optimal": 22},
                "humidity_pct": {"min": 70, "max": 85, "optimal": 80},
                "vpd_kpa": {"min": 0.4, "max": 0.8, "optimal": 0.6}
            },
            "lighting": {
                "ppfd_umol": {"min": 100, "max": 200, "optimal": 150},
                "dli_mol": {"min": 6, "max": 10, "optimal": 8},
                "photoperiod_h": 18
            },
            "nutrition": {
                "ec_ms": {"min": 0.8, "max": 1.2, "optimal": 1.0},
                "ph": {"min": 5.5, "max": 6.0, "optimal": 5.8}
            },
            "source": "Cornell CEA",
            "validated": True
        },
        {
            "recipe_id": "BASIL-VEG-001",
            "crop_type": "basil",
            "variety": "Genovese",
            "growth_stage": "vegetative",
            "environment": {
                "temperature_c": {"min": 22, "max": 28, "optimal": 25},
                "humidity_pct": {"min": 55, "max": 70, "optimal": 62},
                "vpd_kpa": {"min": 0.7, "max": 1.1, "optimal": 0.9}
            },
            "lighting": {
                "ppfd_umol": {"min": 300, "max": 450, "optimal": 380},
                "dli_mol": {"min": 15, "max": 22, "optimal": 18},
                "photoperiod_h": 16
            },
            "nutrition": {
                "ec_ms": {"min": 1.4, "max": 1.8, "optimal": 1.6},
                "ph": {"min": 5.8, "max": 6.4, "optimal": 6.0}
            },
            "source": "Cornell CEA + Wageningen",
            "validated": True
        },
        {
            "recipe_id": "BASIL-FIN-001",
            "crop_type": "basil",
            "variety": "Genovese",
            "growth_stage": "finishing",
            "environment": {
                "temperature_c": {"min": 20, "max": 24, "optimal": 22},
                "humidity_pct": {"min": 50, "max": 65, "optimal": 58},
                "vpd_kpa": {"min": 0.9, "max": 1.3, "optimal": 1.1}
            },
            "lighting": {
                "ppfd_umol": {"min": 400, "max": 550, "optimal": 480},
                "dli_mol": {"min": 18, "max": 26, "optimal": 22},
                "photoperiod_h": 14
            },
            "nutrition": {
                "ec_ms": {"min": 1.0, "max": 1.4, "optimal": 1.2},
                "ph": {"min": 5.6, "max": 6.0, "optimal": 5.8}
            },
            "source": "Cornell CEA + Fluence",
            "validated": True
        }
    ]

    output_file = OUTPUT_DIR / 'plant_recipes.json'
    with open(output_file, 'w') as out:
        for rec in recipes:
            out.write(json.dumps(rec) + '\n')

    print(f"  Output: {output_file.name} ({len(recipes)} recettes)")
    return len(recipes)


# === MAIN ===

if __name__ == "__main__":
    stats = {}

    # 1. Basil Sensory
    print()
    stats['sensory'] = process_basil_sensory()

    # 2. Chilling Injury
    print()
    stats['chilling'] = process_chilling_injury()

    # 3. Martin WUE
    print()
    stats['martin'] = process_martin_wue()

    # 4. Plant Recipes
    print()
    stats['recipes'] = generate_plant_recipes()

    # 5. OpenAg (gros dataset - limite a 5 chunks pour demo)
    print()
    print("[OpenAg] Traitement limite a 50,000 lignes pour demo...")
    print("         Pour tout traiter: modifier max_chunks=None")
    stats['openag'] = process_openag_environmental(chunk_size=10000, max_chunks=5)

    # Resume
    print()
    print("=" * 60)
    print("RESUME")
    print("=" * 60)
    total = sum(stats.values())
    for name, count in stats.items():
        print(f"  {name}: {count:,} records")
    print(f"\n  TOTAL: {total:,} records")
    print()
    print(f"Fichiers generes dans: {OUTPUT_DIR}")
    print()

    # Lister les fichiers
    print("Fichiers:")
    for f in sorted(OUTPUT_DIR.glob('*.json')):
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
