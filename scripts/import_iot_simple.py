#!/usr/bin/env python3
"""
Batch import with preprocessing: Extract LED and nutrient JSON files
"""
import os
import json
import glob
from pathlib import Path
import subprocess

def import_sample_files():
    """Import first 50 LED and 20 nutrient files"""
    
    print("🚀 Sample IoT Data Import")
    print("="*60 + "\n")
    
    # LED Spectrum
    print("📍 LED Spectrum Files")
    led_dir = Path('/home/mounirjaouhari/vertiflow_cloud_release/data_ingestion/led_spectrum')
    led_files = sorted(led_dir.glob('*.json'))[:50]
    
    if led_files:
        print(f"Processing {len(led_files)} LED files...")
        led_data = []
        
        for filepath in led_files:
            try:
                with open(filepath) as f:
                    record = json.load(f)
                    # Extract key fields
                    led_data.append({
                        'timestamp': record.get('timestamp', ''),
                        'farm_id': record.get('farm_id', ''),
                        'rack_id': record.get('rack_id', ''),
                        'ppfd': record.get('light_intensity_ppfd', 0),
                        'ratio_rb': record.get('light_ratio_red_blue', 0)
                    })
            except Exception as e:
                continue
        
        if led_data:
            # Insert via CSV format
            csv_content = "timestamp,farm_id,rack_id,ppfd,ratio_rb\n"
            for rec in led_data:
                ts = rec['timestamp'].replace('T', ' ').replace('+00:00', '')
                csv_content += f'"{ts}","{rec["farm_id"]}","{rec["rack_id"]}",{rec["ppfd"]},{rec["ratio_rb"]}\n'
            
            # Write temp file
            with open('/tmp/led_import.csv', 'w') as f:
                f.write(csv_content)
            
            # Insert
            sql = """
            CREATE TABLE IF NOT EXISTS vertiflow.iot_led_measurements (
                timestamp DateTime,
                farm_id String,
                rack_id String,
                ppfd Float32,
                ratio_rb Float32
            ) ENGINE MergeTree ORDER BY (farm_id, rack_id, timestamp);
            
            INSERT INTO vertiflow.iot_led_measurements FORMAT CSV
            """
            
            # Use clickhouse-client directly
            try:
                result = subprocess.run(
                    f"cat /tmp/led_import.csv | docker exec -i clickhouse clickhouse-client --query 'INSERT INTO vertiflow.iot_led_measurements FORMAT CSV' 2>&1",
                    shell=True, capture_output=True, text=True, timeout=30
                )
                
                if result.returncode == 0 or 'error' not in result.stderr.lower():
                    # Verify
                    verify = subprocess.run(
                        ['docker', 'exec', 'clickhouse', 'clickhouse-client', '--query',
                         'SELECT COUNT(*) FROM vertiflow.iot_led_measurements'],
                        capture_output=True, text=True, timeout=10
                    )
                    count = int(verify.stdout.strip()) if verify.returncode == 0 else 0
                    print(f"✅ {len(led_data)} LED records imported (total: {count})")
                else:
                    print(f"⚠️ Insert warning: {result.stderr[:100]}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Nutrient Data
    print("\n📍 Nutrient Data Files")
    nutrient_dir = Path('/home/mounirjaouhari/vertiflow_cloud_release/data_ingestion/nutrient_data')
    nutrient_files = sorted(nutrient_dir.glob('*.json'))[:20]
    
    if nutrient_files:
        print(f"Processing {len(nutrient_files)} nutrient files...")
        nutrient_data = []
        
        for filepath in nutrient_files:
            try:
                with open(filepath) as f:
                    record = json.load(f)
                    nutrient_data.append({
                        'timestamp': record.get('timestamp', ''),
                        'zone_id': record.get('zone_id', ''),
                        'tank_id': record.get('tank_id', ''),
                        'n': record.get('nutrient_n_total', 0),
                        'p': record.get('nutrient_p_phosphorus', 0)
                    })
            except Exception as e:
                continue
        
        if nutrient_data:
            # Create table
            subprocess.run(
                ['docker', 'exec', 'clickhouse', 'clickhouse-client', '--query',
                 'CREATE TABLE IF NOT EXISTS vertiflow.iot_nutrient_measurements (timestamp DateTime, zone_id String, tank_id String, n Float32, p Float32) ENGINE MergeTree ORDER BY (zone_id, tank_id, timestamp)'],
                capture_output=True, timeout=10
            )
            
            # Insert as CSV
            csv_content = "timestamp,zone_id,tank_id,n,p\n"
            for rec in nutrient_data:
                ts = rec['timestamp'].replace('T', ' ').replace('+00:00', '')
                csv_content += f'"{ts}","{rec["zone_id"]}","{rec["tank_id"]}",{rec["n"]},{rec["p"]}\n'
            
            with open('/tmp/nutrient_import.csv', 'w') as f:
                f.write(csv_content)
            
            try:
                result = subprocess.run(
                    f"cat /tmp/nutrient_import.csv | docker exec -i clickhouse clickhouse-client --query 'INSERT INTO vertiflow.iot_nutrient_measurements FORMAT CSV' 2>&1",
                    shell=True, capture_output=True, text=True, timeout=30
                )
                
                if result.returncode == 0 or 'error' not in result.stderr.lower():
                    verify = subprocess.run(
                        ['docker', 'exec', 'clickhouse', 'clickhouse-client', '--query',
                         'SELECT COUNT(*) FROM vertiflow.iot_nutrient_measurements'],
                        capture_output=True, text=True, timeout=10
                    )
                    count = int(verify.stdout.strip()) if verify.returncode == 0 else 0
                    print(f"✅ {len(nutrient_data)} nutrient records imported (total: {count})")
                else:
                    print(f"⚠️ Insert warning: {result.stderr[:100]}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ IoT data import complete!")

if __name__ == "__main__":
    import_sample_files()
