#!/usr/bin/env python3
"""
Batch import LED spectrum and nutrient data to ClickHouse
With throttling and monitoring
"""
import os
import json
import glob
from datetime import datetime
import subprocess
import time

def create_led_table():
    """Create ClickHouse LED spectrum table"""
    sql = """
    CREATE TABLE IF NOT EXISTS vertiflow.led_spectrum_data (
        timestamp DateTime,
        farm_id String,
        rack_id String,
        level_id String,
        light_intensity_ppfd Float32,
        light_ratio_red_blue Float32,
        spectral_recipe_id String,
        measurement_id String DEFAULT generateUUIDv4()
    ) ENGINE = MergeTree()
    ORDER BY (farm_id, rack_id, timestamp)
    """
    try:
        result = subprocess.run(
            ['docker', 'exec', 'clickhouse', 'clickhouse-client', '--query', sql],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ LED table created")
            return True
        else:
            print(f"⚠️ Table creation: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def batch_import_led_data():
    """Import LED spectrum data in batches"""
    led_dir = '/home/mounirjaouhari/vertiflow_cloud_release/data_ingestion/led_spectrum'
    
    files = sorted(glob.glob(f'{led_dir}/*.json'))[:100]  # Limit to 100 for testing
    
    print(f"📊 Importing {len(files)} LED spectrum files...\n")
    
    insert_sql = "INSERT INTO vertiflow.led_spectrum_data FORMAT JSONEachRow\n"
    batch_count = 0
    
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Normalize if needed
                if isinstance(data, list):
                    for record in data:
                        insert_sql += json.dumps(record) + "\n"
                else:
                    insert_sql += json.dumps(data) + "\n"
                batch_count += 1
        except Exception as e:
            print(f"⚠️ Error reading {os.path.basename(filepath)}: {str(e)[:50]}")
            continue
    
    if batch_count == 0:
        print("❌ No valid LED files found")
        return 0
    
    # Insert batch
    try:
        result = subprocess.run(
            ['docker', 'exec', '-i', 'clickhouse', 'clickhouse-client', '--database=vertiflow'],
            input=insert_sql.encode(),
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {batch_count} LED files processed")
            
            # Verify
            verify = subprocess.run(
                ['docker', 'exec', 'clickhouse', 'clickhouse-client', '--query',
                 'SELECT COUNT(*) FROM vertiflow.led_spectrum_data'],
                capture_output=True, text=True, timeout=10
            )
            if verify.returncode == 0:
                count = int(verify.stdout.strip())
                print(f"✅ ClickHouse LED records: {count}")
            
            return batch_count
        else:
            print(f"❌ Insert error: {result.stderr[:200]}")
            return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

def create_nutrient_table():
    """Create ClickHouse nutrient data table"""
    sql = """
    CREATE TABLE IF NOT EXISTS vertiflow.nutrient_data (
        timestamp DateTime,
        zone_id String,
        tank_id String,
        nutrient_n_total Float32,
        nutrient_p_phosphorus Float32,
        nutrient_k_potassium Float32,
        nutrient_ca Float32,
        nutrient_mg Float32,
        measurement_id String DEFAULT generateUUIDv4()
    ) ENGINE = MergeTree()
    ORDER BY (zone_id, tank_id, timestamp)
    """
    try:
        result = subprocess.run(
            ['docker', 'exec', 'clickhouse', 'clickhouse-client', '--query', sql],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ Nutrient table created")
            return True
        else:
            print(f"⚠️ Table creation: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def batch_import_nutrient_data():
    """Import nutrient data in batches"""
    nutrient_dir = '/home/mounirjaouhari/vertiflow_cloud_release/data_ingestion/nutrient_data'
    
    files = sorted(glob.glob(f'{nutrient_dir}/*.json'))[:50]  # Limit to 50 for testing
    
    print(f"📊 Importing {len(files)} nutrient data files...\n")
    
    insert_sql = "INSERT INTO vertiflow.nutrient_data FORMAT JSONEachRow\n"
    batch_count = 0
    
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for record in data:
                        insert_sql += json.dumps(record) + "\n"
                else:
                    insert_sql += json.dumps(data) + "\n"
                batch_count += 1
        except Exception as e:
            print(f"⚠️ Error reading {os.path.basename(filepath)}: {str(e)[:50]}")
            continue
    
    if batch_count == 0:
        print("❌ No valid nutrient files found")
        return 0
    
    # Insert batch
    try:
        result = subprocess.run(
            ['docker', 'exec', '-i', 'clickhouse', 'clickhouse-client', '--database=vertiflow'],
            input=insert_sql.encode(),
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {batch_count} nutrient files processed")
            
            # Verify
            verify = subprocess.run(
                ['docker', 'exec', 'clickhouse', 'clickhouse-client', '--query',
                 'SELECT COUNT(*) FROM vertiflow.nutrient_data'],
                capture_output=True, text=True, timeout=10
            )
            if verify.returncode == 0:
                count = int(verify.stdout.strip())
                print(f"✅ ClickHouse nutrient records: {count}")
            
            return batch_count
        else:
            print(f"❌ Insert error: {result.stderr[:200]}")
            return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

if __name__ == "__main__":
    print("🚀 IoT Data Import to ClickHouse")
    print("="*60 + "\n")
    
    # LED Spectrum
    print("📍 LED Spectrum Data")
    print("-"*60)
    if create_led_table():
        batch_import_led_data()
    
    print("\n📍 Nutrient Data")
    print("-"*60)
    if create_nutrient_table():
        batch_import_nutrient_data()
    
    print("\n" + "="*60)
    print("✅ IoT data import complete!")
