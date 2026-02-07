#!/usr/bin/env python3
"""
Créer table iot_sensors pour dashboard 09_iot_health_map.json
Génère données fictives basées sur capteurs existants
"""

import clickhouse_connect
from datetime import datetime
import random

CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = 'default'
CLICKHOUSE_PASSWORD = 'default'

# Coordonnées Casablanca (base dashboard)
BASE_LAT = 33.574
BASE_LON = -7.590

def create_iot_sensors_table(client):
    """Créer table iot_sensors"""
    print("🔨 Création de la table iot_sensors...")
    
    create_sql = """
    CREATE TABLE IF NOT EXISTS vertiflow.iot_sensors (
        sensor_id String,
        sensor_type String,
        status Enum8('online' = 1, 'offline' = 2, 'warning' = 3, 'error' = 4, 'maintenance' = 5),
        health_score Float64,
        battery_level Float64,
        latitude Float64,
        longitude Float64,
        zone_id String,
        rack_id String,
        last_seen DateTime,
        firmware_version String DEFAULT 'v1.0',
        signal_strength Int32 DEFAULT 0
    ) ENGINE = MergeTree()
    ORDER BY (zone_id, sensor_id);
    """
    
    client.command(create_sql)
    print("✅ Table créée avec succès")

def generate_sensor_data(client):
    """Générer données capteurs depuis tables existantes"""
    print("📊 Génération de données capteurs...")
    
    # Récupérer zones et racks depuis basil_ultimate_realtime
    zones_racks = client.query("""
        SELECT DISTINCT 
            zone_id,
            rack_id
        FROM vertiflow.basil_ultimate_realtime
        LIMIT 50
    """).result_rows
    
    print(f"  🏢 {len(zones_racks)} zones/racks détectés")
    
    sensors = []
    sensor_types = ['Temperature', 'Humidity', 'CO2', 'pH', 'EC', 'Light_PPFD', 'Nutrient_N', 'Nutrient_P', 'Nutrient_K']
    statuses = ['online', 'online', 'online', 'online', 'warning', 'offline']  # Bias vers online
    
    sensor_id = 1
    for zone_id, rack_id in zones_racks:
        # 3-5 capteurs par zone/rack
        num_sensors = random.randint(3, 5)
        
        for i in range(num_sensors):
            sensor_type = random.choice(sensor_types)
            status = random.choice(statuses)
            
            # Health score selon statut
            if status == 'online':
                health_score = random.uniform(90, 100)
                battery = random.uniform(80, 100)
                signal = random.randint(-50, -30)
            elif status == 'warning':
                health_score = random.uniform(70, 89)
                battery = random.uniform(50, 79)
                signal = random.randint(-70, -51)
            elif status == 'offline':
                health_score = 0
                battery = random.uniform(0, 20)
                signal = random.randint(-100, -80)
            else:  # error, maintenance
                health_score = random.uniform(40, 69)
                battery = random.uniform(30, 70)
                signal = random.randint(-80, -60)
            
            # Géolocalisation autour de Casablanca (variation ±0.001°)
            lat = BASE_LAT + random.uniform(-0.001, 0.001)
            lon = BASE_LON + random.uniform(-0.001, 0.001)
            
            sensor = {
                'sensor_id': f'IOT-{sensor_id:04d}',
                'sensor_type': sensor_type,
                'status': status,
                'health_score': round(health_score, 2),
                'battery_level': round(battery, 2),
                'latitude': round(lat, 6),
                'longitude': round(lon, 6),
                'zone_id': zone_id,
                'rack_id': rack_id,
                'last_seen': datetime.now(),
                'firmware_version': f'v{random.randint(1, 3)}.{random.randint(0, 9)}',
                'signal_strength': signal
            }
            
            sensors.append(sensor)
            sensor_id += 1
    
    print(f"  ✅ {len(sensors)} capteurs générés")
    return sensors

def insert_sensors(client, sensors, batch_size=100):
    """Insérer capteurs dans ClickHouse"""
    print(f"📥 Insertion de {len(sensors)} capteurs...")
    
    for i in range(0, len(sensors), batch_size):
        batch = sensors[i:i+batch_size]
        data_tuples = [tuple(s.values()) for s in batch]
        client.insert('vertiflow.iot_sensors', data_tuples, column_names=list(sensors[0].keys()))
    
    print(f"✅ {len(sensors)} capteurs insérés")

def verify_data(client):
    """Vérifier données"""
    print("\n🔍 Vérification des données...")
    
    # Stats globales
    total = client.query("SELECT count() FROM vertiflow.iot_sensors").first_row[0]
    print(f"  📡 Total capteurs: {total}")
    
    # Par statut
    statuses = client.query("""
        SELECT 
            toString(status) as status_name,
            count() as count
        FROM vertiflow.iot_sensors
        GROUP BY status
        ORDER BY count DESC
    """).result_rows
    
    print("\n  📊 Répartition par statut:")
    for row in statuses:
        print(f"    • {row[0]}: {row[1]} capteurs")
    
    # Par type
    types = client.query("""
        SELECT 
            sensor_type,
            count() as count
        FROM vertiflow.iot_sensors
        GROUP BY sensor_type
        ORDER BY count DESC
        LIMIT 5
    """).result_rows
    
    print("\n  🔧 Top 5 types de capteurs:")
    for row in types:
        print(f"    • {row[0]}: {row[1]} capteurs")
    
    # Santé moyenne
    avg_health = client.query("""
        SELECT round(avg(health_score), 1) as avg_health
        FROM vertiflow.iot_sensors
        WHERE toString(status) != 'offline'
    """).first_row[0]
    
    print(f"\n  💚 Santé globale moyenne: {avg_health}%")
    
    # Zones couvertes
    zones = client.query("""
        SELECT DISTINCT zone_id
        FROM vertiflow.iot_sensors
        ORDER BY zone_id
    """).result_rows
    
    print(f"  🏢 Zones couvertes: {', '.join([z[0] for z in zones])}")
    
    # Échantillon géolocalisation
    print("\n  🗺️  Échantillon géolocalisation:")
    samples = client.query("""
        SELECT 
            sensor_id,
            sensor_type,
            zone_id,
            round(latitude, 4) as lat,
            round(longitude, 4) as lon,
            toString(status) as status
        FROM vertiflow.iot_sensors
        LIMIT 5
    """).result_rows
    
    for row in samples:
        print(f"    {row[0]} ({row[1]}) - Zone:{row[2]} - {row[3]}°N, {row[4]}°W - {row[5]}")

def main():
    print("=" * 80)
    print("🗺️  CRÉATION TABLE IOT_SENSORS POUR DASHBOARD 09")
    print("=" * 80)
    
    # Connexion
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD
    )
    print("✅ Connecté à ClickHouse\n")
    
    # Créer table
    create_iot_sensors_table(client)
    print()
    
    # Générer données
    sensors = generate_sensor_data(client)
    print()
    
    # Insérer
    insert_sensors(client, sensors)
    
    # Vérifier
    verify_data(client)
    
    print("\n" + "=" * 80)
    print("✅ TERMINÉ - Dashboard 09_iot_health_map.json débloqué")
    print("=" * 80)
    print("📍 Carte géographique disponible à Casablanca (33.574°N, -7.590°W)")

if __name__ == '__main__':
    main()
