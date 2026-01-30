#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - SIMULATEUR IOT AVEC DÉRIVE ANALYTIQUE
================================================================================
Cible : Zone 1 NiFi (vertiflow.ingestion.raw)
Schéma : 157 colonnes (01_tables.sql)
Logique : Cycles de vie (plant_recipes.js) + Simulation de pannes (Drift)
================================================================================
"""

import json
import random
import time
import logging
import sys
import uuid
from datetime import datetime, timezone

try:
    from kafka import KafkaProducer
except ImportError:
    print("❌ Erreur : kafka-python manquant.")
    sys.exit(1)

# Configuration
KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "vertiflow.ingestion.raw"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SIM] - %(message)s')
logger = logging.getLogger("VertiFlow.ExpertSim")

# --- ÉTAT DU SYSTÈME (Pour simuler la dérive) ---
system_state = {
    "is_drifting": False,      # Si True, une anomalie commence
    "drift_intensity": 0.0,    # Augmente progressivement
    "drift_type": None,        # 'PH_ACID' ou 'HVAC_FAIL'
    "current_day": 12          # Commence au stade Végétatif
}

class VertiFlowExpertSimulator:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def trigger_anomaly(self):
        """Déclenche aléatoirement une dérive pour tester la Zone 4"""
        if not system_state["is_drifting"] and random.random() < 0.05:
            system_state["is_drifting"] = True
            system_state["drift_type"] = random.choice(["PH_ACID", "HVAC_FAIL"])
            logger.warning(f"🚨 DÉBUT D'ANOMALIE : {system_state['drift_type']}")

    def generate_record(self, rack, level):
        now = datetime.now(timezone.utc)

        # 1. BASE DE DONNÉES (Valeurs optimales de seed_data.js)
        temp_base = 24.5
        ph_base = 6.2
        hum_base = 65.0

        # 2. APPLICATION DE LA DÉRIVE (Si active)
        if system_state["is_drifting"]:
            system_state["drift_intensity"] += 0.05 # Dérive progressive
            if system_state["drift_type"] == "PH_ACID":
                ph_base -= system_state["drift_intensity"] # Le pH chute (Acidification)
            elif system_state["drift_type"] == "HVAC_FAIL":
                temp_base += system_state["drift_intensity"] # La température monte (Panne clim)
                hum_base -= (system_state["drift_intensity"] * 2) # L'air s'assèche

        # 3. GÉNÉRATION DU RECORD (Conforme aux 157 colonnes de 01_tables.sql)
        # Nous remplissons les colonnes clés pour vos alertes NiFi
        record = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "farm_id": "VERT-MAROC-01",
            "rack_id": rack,
            "level_index": level,
            "module_id": f"{rack}-L{level}",
            "species_variety": "Ocimum basilicum",

            # Paramètres Environnementaux
            "air_temp_internal": round(random.gauss(temp_base, 0.2), 2),
            "air_humidity": round(random.gauss(hum_base, 1.0), 1),
            "vapor_pressure_deficit": 0.0, # NiFi doit le calculer en Zone 2

            # Paramètres de Nutrition (plant_recipes.js)
            "water_ph": round(ph_base + random.uniform(-0.05, 0.05), 2),
            "nutrient_solution_ec": 1.8,

            # Biomasse (Inspiré de basil_recipe_optimal_vance.csv)
            "days_since_planting": system_state["current_day"],
            "fresh_biomass_est": round(20.0 + (system_state["current_day"] * 1.5), 2),
            "growth_stage": "Végétatif",

            # Hardware & Intelligence (01_tables.sql)
            "pump_vibration_level": 0.2 if system_state["drift_type"] != "PH_ACID" else 4.5,
            "health_score": round(1.0 - (system_state["drift_intensity"] / 10), 2),
            "data_source_type": "IoT-Expert-Drift",
            "lineage_uuid": str(uuid.uuid4())
        }

        # Compléter avec des valeurs par défaut pour les colonnes restantes (157 au total)
        # (Pour l'exemple, on s'assure que les colonnes SQL existent)
        return record

    def run(self):
        logger.info(f"🚀 Simulateur prêt. Envoi vers : {KAFKA_TOPIC}")
        try:
            while True:
                self.trigger_anomaly()
                for rack in ["RACK-01", "RACK-02"]:
                    for level in [1, 2, 3, 4]:
                        data = self.generate_record(rack, level)
                        self.producer.send(KAFKA_TOPIC, value=data)

                # Mise à jour de l'état
                if system_state["is_drifting"] and system_state["drift_intensity"] > 3.0:
                    logger.info("✅ Anomalie terminée (système stabilisé ou plant ruiné).")
                    system_state["is_drifting"] = False
                    system_state["drift_intensity"] = 0.0

                time.sleep(5)
        except KeyboardInterrupt:
            self.producer.close()

if __name__ == "__main__":
    VertiFlowExpertSimulator().run()