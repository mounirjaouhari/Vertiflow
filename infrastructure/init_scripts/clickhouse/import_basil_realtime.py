#!/usr/bin/env python3
"""
Import Basil Ultimate Realtime Data to ClickHouse
Débloque dashboards: 02_science_lab.json, 07_realtime_basil.json
"""

import pandas as pd
import clickhouse_connect
from datetime import datetime
import sys

# Configuration ClickHouse
CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = 'default'
CLICKHOUSE_PASSWORD = 'default'
CLICKHOUSE_DB = 'vertiflow'
CSV_FILE = '/home/mounirjaouhari/vertiflow_cloud_release/Basil_Agritech_Consolidated/basil_ultimate_realtime1.csv'

# Mapping colonnes CSV → ClickHouse (basé sur analyse dashboards)
COLUMN_MAPPING = {
    0: 'timestamp',           # DateTime
    1: 'farm_id',            # String
    2: 'greenhouse_id',      # String
    3: 'latitude',           # Float64
    4: 'longitude',          # Float64
    5: 'zone_id',            # String (utilisé par dashboards)
    6: 'rack_id',            # String
    7: 'level',              # Int32
    8: 'sensor_id',          # String
    9: 'batch_id',           # String
    10: 'plant_species',     # String
    11: 'plant_age_days',    # Float64 (contient virgule)
    # Colonnes environnementales (dashboards 02, 07)
    13: 'air_temp_internal',       # Float64 (°C) - DASHBOARD 07
    14: 'water_temp',              # Float64 (°C) - DASHBOARD 07
    15: 'air_humidity',            # Float64 (%) - DASHBOARD 07
    16: 'co2_level_ambient',       # Float64 (ppm) - DASHBOARD 07
    17: 'light_intensity_ppfd',    # Float64 (µmol/m²/s) - DASHBOARDS 02, 07
    18: 'water_ph',                # Float64 - DASHBOARD 07
    19: 'nutrient_solution_ec',    # Float64 (mS/cm) - DASHBOARD 07
    # Nutriments (dashboard 02)
    30: 'nutrient_n_total',        # Float64 (ppm) - DASHBOARD 02
    31: 'nutrient_p_phosphorus',   # Float64 (ppm) - DASHBOARD 02
    32: 'nutrient_k_potassium',    # Float64 (ppm) - DASHBOARD 02
    33: 'nutrient_ca_calcium',     # Float64 - DASHBOARD 02
    34: 'nutrient_mg_magnesium',   # Float64 - DASHBOARD 02
    38: 'nutrient_fe_iron',        # Float64 - DASHBOARD 02
    # Métriques scientifiques (dashboard 02)
    40: 'photosynthetic_rate_max', # Float64 - DASHBOARD 02
    43: 'chlorophyll_index_spad',  # Float64 - DASHBOARD 02
    59: 'light_dli_accumulated',   # Float64 - DASHBOARD 02
    68: 'light_ratio_red_blue',    # Float64 - DASHBOARD 02
    69: 'light_far_red_intensity', # Float64 - DASHBOARD 02
    65: 'leaf_temp_delta',         # Float64 - DASHBOARD 02
    81: 'ext_temp_nasa',           # Float64 - DASHBOARD 02
    70: 'co2_consumption_rate',    # Float64 - DASHBOARD 02
    74: 'light_use_efficiency',    # Float64 - DASHBOARD 02
}

def create_table(client):
    """Créer table basil_ultimate_realtime dans ClickHouse"""
    print("🔨 Création de la table basil_ultimate_realtime...")
    
    create_sql = """
    CREATE TABLE IF NOT EXISTS vertiflow.basil_ultimate_realtime (
        timestamp DateTime,
        farm_id String,
        greenhouse_id String,
        latitude Float64,
        longitude Float64,
        zone_id String,
        rack_id String,
        level Int32,
        sensor_id String,
        batch_id String,
        plant_species String,
        plant_age_days Float64,
        air_temp_internal Float64,
        water_temp Float64,
        air_humidity Float64,
        co2_level_ambient Float64,
        light_intensity_ppfd Float64,
        water_ph Float64,
        nutrient_solution_ec Float64,
        nutrient_n_total Float64,
        nutrient_p_phosphorus Float64,
        nutrient_k_potassium Float64,
        nutrient_ca_calcium Float64,
        nutrient_mg_magnesium Float64,
        nutrient_fe_iron Float64,
        photosynthetic_rate_max Float64,
        chlorophyll_index_spad Float64,
        light_dli_accumulated Float64,
        light_ratio_red_blue Float64,
        light_far_red_intensity Float64,
        leaf_temp_delta Float64,
        ext_temp_nasa Float64,
        co2_consumption_rate Float64,
        light_use_efficiency Float64
    ) ENGINE = MergeTree()
    ORDER BY (zone_id, timestamp)
    PARTITION BY toYYYYMM(timestamp)
    TTL timestamp + INTERVAL 90 DAY;
    """
    
    try:
        client.command(create_sql)
        print("✅ Table créée avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur création table: {e}")
        return False

def load_and_transform_csv():
    """Charger CSV et extraire colonnes nécessaires"""
    print(f"📂 Chargement du CSV: {CSV_FILE}")
    
    try:
        # Charger CSV sans header (utiliser indices)
        df = pd.read_csv(CSV_FILE, header=None, low_memory=False)
        print(f"✅ {len(df)} lignes chargées")
        
        # Extraire colonnes mappées
        data = {}
        for col_idx, col_name in COLUMN_MAPPING.items():
            if col_idx < len(df.columns):
                data[col_name] = df[col_idx]
            else:
                print(f"⚠️  Colonne {col_idx} manquante, rempli avec 0")
                data[col_name] = 0
        
        result_df = pd.DataFrame(data)
        
        # Nettoyer timestamp (supprimer millisecondes si présentes)
        result_df['timestamp'] = pd.to_datetime(result_df['timestamp'], errors='coerce')
        
        # Remplacer NaN par 0 pour Float64
        float_columns = [col for col, dtype in result_df.dtypes.items() if 'float' in str(dtype)]
        result_df[float_columns] = result_df[float_columns].fillna(0)
        
        # Nettoyer strings
        string_columns = ['farm_id', 'greenhouse_id', 'zone_id', 'rack_id', 'sensor_id', 'batch_id', 'plant_species']
        for col in string_columns:
            result_df[col] = result_df[col].astype(str).str.strip()
            result_df[col] = result_df[col].replace('nan', 'UNKNOWN')
        
        # Convertir level en Int32
        result_df['level'] = pd.to_numeric(result_df['level'], errors='coerce').fillna(0).astype(int)
        
        print(f"✅ Transformation réussie: {len(result_df)} lignes, {len(result_df.columns)} colonnes")
        return result_df
    
    except Exception as e:
        print(f"❌ Erreur chargement CSV: {e}")
        return None

def insert_data(client, df, batch_size=100):
    """Insérer données dans ClickHouse par batch"""
    print(f"📥 Insertion de {len(df)} lignes dans ClickHouse (batch_size={batch_size})...")
    
    total_inserted = 0
    errors = 0
    
    for start_idx in range(0, len(df), batch_size):
        end_idx = min(start_idx + batch_size, len(df))
        batch = df.iloc[start_idx:end_idx]
        
        try:
            # Convertir DataFrame en liste de tuples
            data_tuples = [tuple(row) for row in batch.values]
            
            # Insérer batch
            client.insert('vertiflow.basil_ultimate_realtime', data_tuples, column_names=list(df.columns))
            total_inserted += len(batch)
            
            if (start_idx + batch_size) % 500 == 0:
                print(f"  ⏳ {total_inserted}/{len(df)} lignes insérées...")
        
        except Exception as e:
            errors += 1
            print(f"⚠️  Erreur batch {start_idx}-{end_idx}: {e}")
            if errors > 10:
                print("❌ Trop d'erreurs, arrêt de l'import")
                return False
    
    print(f"✅ Import terminé: {total_inserted} lignes insérées ({errors} erreurs)")
    return True

def verify_data(client):
    """Vérifier données importées"""
    print("\n🔍 Vérification des données...")
    
    # Compter lignes
    count = client.query("SELECT count() as total FROM vertiflow.basil_ultimate_realtime").first_row[0]
    print(f"  📊 Total lignes: {count}")
    
    # Vérifier zones
    zones = client.query("SELECT DISTINCT zone_id FROM vertiflow.basil_ultimate_realtime").result_rows
    print(f"  🏢 Zones: {', '.join([z[0] for z in zones])}")
    
    # Échantillon données
    sample = client.query("""
        SELECT 
            timestamp, 
            zone_id, 
            round(air_temp_internal, 2) as temp,
            round(air_humidity, 2) as humidity,
            round(light_intensity_ppfd, 2) as ppfd,
            round(water_ph, 2) as ph
        FROM vertiflow.basil_ultimate_realtime 
        LIMIT 3
    """).result_rows
    
    print("\n  📋 Échantillon données:")
    for row in sample:
        print(f"    {row[0]} | Zone:{row[1]} | Temp:{row[2]}°C | Humid:{row[3]}% | PPFD:{row[4]} | pH:{row[5]}")
    
    return count > 0

def main():
    print("=" * 80)
    print("🌿 IMPORT BASIL ULTIMATE REALTIME → CLICKHOUSE")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Objectif: Débloquer dashboards 02_science_lab.json et 07_realtime_basil.json\n")
    
    # Connexion ClickHouse
    try:
        print("🔌 Connexion à ClickHouse...")
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST, 
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD
        )
        print("✅ Connecté à ClickHouse\n")
    except Exception as e:
        print(f"❌ Erreur connexion ClickHouse: {e}")
        return 1
    
    # Étape 1: Créer table
    if not create_table(client):
        return 1
    
    print()
    
    # Étape 2: Charger CSV
    df = load_and_transform_csv()
    if df is None:
        return 1
    
    print()
    
    # Étape 3: Insérer données
    if not insert_data(client, df):
        return 1
    
    # Étape 4: Vérifier
    if not verify_data(client):
        print("\n❌ Vérification échouée")
        return 1
    
    print("\n" + "=" * 80)
    print("✅ IMPORT TERMINÉ AVEC SUCCÈS")
    print("=" * 80)
    print("📊 Dashboards débloqués:")
    print("  - 02_science_lab.json")
    print("  - 07_realtime_basil.json")
    print("\n💡 Prochaine étape: Créer alias plant_recipes et table iot_sensors")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
