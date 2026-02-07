#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM                              ║
║              MQTT IoT SENSOR SIMULATOR (INTEGRATION-001)                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-02-07                                                 ║
║ Purpose         : Simulate IoT sensors publishing to MQTT broker             ║
║                   Enables ConsumeMQTT processor in NiFi Zone 1               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import time
import random
import argparse
from datetime import datetime, timezone
from typing import Dict, Any

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Installing paho-mqtt...")
    import subprocess
    subprocess.check_call(["pip", "install", "paho-mqtt"])
    import paho.mqtt.client as mqtt


# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
BASE_TOPIC = "vertiflow/farm/F001"

# Sensor configurations par zone
SENSORS = {
    "zone_0": {
        "sensors": ["TMP001", "HUM001", "CO2001", "LUX001"],
        "types": ["temperature", "humidity", "co2", "light"]
    },
    "zone_1": {
        "sensors": ["TMP002", "HUM002", "CO2002", "LUX002", "PH001", "EC001"],
        "types": ["temperature", "humidity", "co2", "light", "ph", "ec"]
    },
    "zone_2": {
        "sensors": ["TMP003", "HUM003", "CO2003", "LUX003"],
        "types": ["temperature", "humidity", "co2", "light"]
    }
}

# Ranges réalistes pour chaque type de capteur
SENSOR_RANGES = {
    "temperature": {"min": 18.0, "max": 28.0, "unit": "°C", "precision": 1},
    "humidity": {"min": 50.0, "max": 80.0, "unit": "%", "precision": 1},
    "co2": {"min": 400, "max": 1200, "unit": "ppm", "precision": 0},
    "light": {"min": 200, "max": 800, "unit": "µmol/m²/s", "precision": 0},
    "ph": {"min": 5.5, "max": 6.5, "unit": "pH", "precision": 2},
    "ec": {"min": 1.2, "max": 2.5, "unit": "mS/cm", "precision": 2}
}


def generate_sensor_reading(sensor_id: str, sensor_type: str, zone_id: str) -> Dict[str, Any]:
    """Generate a realistic sensor reading."""
    config = SENSOR_RANGES[sensor_type]
    
    # Add some variation based on time of day (simulates day/night cycle)
    hour = datetime.now().hour
    day_factor = 1.0 + 0.1 * (1 if 6 <= hour <= 18 else -1)
    
    base_value = random.uniform(config["min"], config["max"])
    value = round(base_value * day_factor, config["precision"])
    
    # Clamp to valid range
    value = max(config["min"], min(config["max"] * 1.1, value))
    
    return {
        "sensor_id": sensor_id,
        "zone_id": zone_id,
        "measurement_type": sensor_type,
        "value": value,
        "unit": config["unit"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "quality_flag": 0 if random.random() > 0.02 else 1,  # 2% chance of degraded quality
        "farm_id": "F001"
    }


def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker."""
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"❌ Connection failed with code {rc}")


def on_publish(client, userdata, mid):
    """Callback when message is published."""
    pass  # Silent publish


def main():
    parser = argparse.ArgumentParser(description="MQTT IoT Sensor Simulator for VertiFlow")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between readings (default: 5)")
    parser.add_argument("--broker", type=str, default=MQTT_BROKER, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=MQTT_PORT, help="MQTT broker port")
    parser.add_argument("--duration", type=int, default=0, help="Duration in seconds (0 = infinite)")
    args = parser.parse_args()
    
    # Create MQTT client
    client = mqtt.Client(client_id="vertiflow_iot_simulator")
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        client.connect(args.broker, args.port, 60)
        client.loop_start()
        
        print(f"🚀 Starting IoT simulation (interval: {args.interval}s)")
        print(f"📡 Publishing to topics: {BASE_TOPIC}/zone/*/sensor/*/telemetry")
        print("-" * 60)
        
        start_time = time.time()
        message_count = 0
        
        while True:
            for zone_id, zone_config in SENSORS.items():
                for sensor_id, sensor_type in zip(zone_config["sensors"], zone_config["types"]):
                    # Generate reading
                    reading = generate_sensor_reading(sensor_id, sensor_type, zone_id)
                    
                    # Build topic
                    topic = f"{BASE_TOPIC}/zone/{zone_id}/sensor/{sensor_id}/telemetry"
                    
                    # Publish
                    payload = json.dumps(reading)
                    result = client.publish(topic, payload, qos=1)
                    
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        message_count += 1
                    
            # Status update every 10 iterations
            if message_count % 50 == 0:
                elapsed = time.time() - start_time
                rate = message_count / elapsed if elapsed > 0 else 0
                print(f"📊 Published {message_count} messages ({rate:.1f} msg/s)")
            
            # Check duration limit
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                print(f"⏱️ Duration limit reached ({args.duration}s)")
                break
            
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping simulator...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print(f"📈 Total messages published: {message_count}")


if __name__ == "__main__":
    main()
