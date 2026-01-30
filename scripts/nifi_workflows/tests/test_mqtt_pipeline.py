#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import time
import os

# Configuration du test
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/iot/data"
OUTPUT_DIR = "./nifi/publication" # Le dossier configuré dans PutFile

def simulate_sensor_data():
    """Génère une donnée simulée au format JSON attendu par le flux."""
    data = {
        "sensor_id": "SN-9982",
        "timestamp": int(time.time()),
        "value": 24.5,
        "unit": "Celsius",
        "status": "OPERATIONAL"
    }
    return json.dumps(data)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connecté au broker MQTT.")
    else:
        print(f"❌ Erreur de connexion (Code: {rc})")

def run_test():
    client = mqtt.Client()
    client.on_connect = on_connect

    try:
        print(f"--- DÉBUT DU TEST DU PIPELINE ---")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Message 1 : Donnée valide
        payload = simulate_sensor_data()
        print(f"📤 Envoi du message : {payload}")
        client.publish(MQTT_TOPIC, payload)
        
        print("⏳ Attente du traitement par NiFi (3 secondes)...")
        time.sleep(3)
        
        # Vérification du fichier en sortie
        if os.path.exists(OUTPUT_DIR):
            files = os.listdir(OUTPUT_DIR)
            if files:
                print(f"🎉 SUCCÈS : {len(files)} fichier(s) trouvé(s) dans {OUTPUT_DIR}")
                for f in files:
                    print(f"   📄 Fichier : {f}")
            else:
                print(f"⚠️ Le dossier {OUTPUT_DIR} est vide. Vérifiez les logs de NiFi.")
        else:
            print(f"❌ Erreur : Le répertoire de sortie {OUTPUT_DIR} n'existe pas encore.")

    except Exception as e:
        print(f"💥 Erreur lors du test : {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    run_test()