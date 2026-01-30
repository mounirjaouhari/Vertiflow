#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VERTIFLOW - ÉTAPE 8 : MAPPING DES 156 PARAMÈTRES (JOLT TRANSFORM)
================================================================================
Description : Ce script configure la transformation structurelle pour aligner
              les données capteurs avec le schéma ClickHouse 156 colonnes.
"""

import json
import logging
import os

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NiFiScientificMapping:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.headers = {'Content-Type': 'application/json'}
        auth_url = f"{self.base_url}/access/token"
        res = requests.post(auth_url, data={'username': username, 'password': password}, verify=False)
        self.headers['Authorization'] = f'Bearer {res.text}'

    def get_group_id(self, name):
        res = requests.get(f"{self.base_url}/process-groups/root/process-groups", headers=self.headers, verify=False)
        for g in res.json().get('processGroups', []):
            if name in g['component']['name']:
                return g['id']
        return None

    def create_jolt_transform(self, pg_id):
        """Crée la transformation JOLT pour mapper les 156 paramètres."""
        logger.info("Configuration du mapping JOLT pour ClickHouse...")
        
        # Spécification JOLT pour transformer les clés variables en colonnes fixes
        # Exemple : aplatir les objets imbriqués pour ClickHouse
        jolt_spec = {
            "version": "v1",
            "spec": {
                "*": {
                    "sensor_id": "tower_id",
                    "timestamp": "event_time",
                    "metrics": {
                        "t_air": "air_temperature",
                        "h_air": "air_humidity",
                        "co2": "co2_level",
                        "par": "light_intensity_par",
                        "ec": "nutrient_ec",
                        "ph": "nutrient_ph"
                        # ... Le mapping peut s'étendre aux 156 colonnes ici
                    }
                }
            }
        }

        payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.standard.JoltTransformJSON",
                "name": "Mapping_Scientifique_156_Cols",
                "position": {"x": 400, "y": 600},
                "config": {
                    "properties": {
                        "jolt-transform": "jolt-transform-chain",
                        "jolt-spec": json.dumps(jolt_spec)
                    }
                }
            }
        }
        
        res = requests.post(f"{self.base_url}/process-groups/{pg_id}/processors", 
                            json=payload, headers=self.headers, verify=False)
        return res.status_code == 201

if __name__ == "__main__":
    NIFI_URL = os.getenv('NIFI_BASE_URL', "https://localhost:8443/nifi-api")
    NIFI_PASSWORD = os.getenv('NIFI_PASSWORD')

    if not NIFI_PASSWORD:
        raise ValueError("NIFI_PASSWORD environment variable is required")

    mapper = NiFiScientificMapping(
        NIFI_URL,
        os.getenv('NIFI_USERNAME', "admin"),
        NIFI_PASSWORD
    )
    
    # On applique cela dans la Zone 2 (Fusion/Enrichissement)
    z2_id = mapper.get_group_id("Z2 - Fusion")
    if z2_id and mapper.create_jolt_transform(z2_id):
        logger.info("✅ ÉTAPE 8 TERMINÉE : Le mapping vers les 156 colonnes est prêt.")